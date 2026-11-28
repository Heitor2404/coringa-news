"""Bounded public metadata waves: independent sessions, deterministic merge.

No shared Transporte, no concurrent download, no increased logical search
budget. At most two independent origins per wave. Byte ceilings concern
accepted metadata; an interrupted HTTP response may consume a final chunk.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from time import monotonic
from src.v4.aquisicao_documental import Transporte

@dataclass(frozen=True)
class RotaPublica:
    origem:str
    buscar:object
    max_http:int=3
    max_bytes:int=5_000_000
    max_wait:int=12

    def executar(self,q,*,factory=Transporte):
        t=factory(max_http=self.max_http,max_bytes=self.max_bytes,max_wait=self.max_wait)
        start=monotonic()
        try:
            raw=self.buscar(q,transport=t) or []
            if not isinstance(raw,list):raise ValueError('RESULTADO_NAO_LISTA')
            result=dict(raw=raw,error=None)
        except Exception as exc:
            result=dict(raw=[],error=type(exc).__name__)
        finally:
            session=getattr(t,'session',None)
            if session is not None:session.close()
        return {**result,'rede':t.resumo(),'inicio_monotonic':start,'fim_monotonic':monotonic()}

    def __call__(self,q):
        result=self.executar(q)
        if result['error']:raise ValueError('FONTE_PUBLICA_'+result['error'])
        return result['raw']

def onda(tasks):
    tasks=list(tasks)
    if not 1<=len(tasks)<=2 or any(not isinstance(r,RotaPublica) for r,q in tasks):
        raise ValueError('ONDA_LIMITE')
    if len({r.origem for r,q in tasks})!=len(tasks):raise ValueError('ONDA_ORIGEM_REPETIDA')
    if sum(r.max_http for r,q in tasks)>8 or sum(r.max_bytes for r,q in tasks)>18_000_000:
        raise ValueError('ONDA_ORCAMENTO')
    def run(task):return task[0].executar(task[1])
    if len(tasks)==1:return [run(tasks[0])]
    with ThreadPoolExecutor(max_workers=2,thread_name_prefix='documental-meta') as executor:
        return list(executor.map(run,tasks))

def rotas_publicas(tipo):
    import os
    from src.v4 import fontes_publicas_e354 as F,galerias_oficiais_e356 as G,fontes_culturais_e366 as C
    if tipo=='video':
        return [('usgs_pagina',RotaPublica('www.usgs.gov',lambda q,transport:F.usgs(q,'video',transport=transport))),
                ('noaa_pagina',RotaPublica('oceanexplorer.noaa.gov',lambda q,transport:G.candidatos(q,'noaa','video',transport=transport),4,9_000_000))]
    if tipo=='foto':
        return [('usgs_pagina',RotaPublica('www.usgs.gov',lambda q,transport:F.usgs(q,'foto',transport=transport))),
                ('openverse',RotaPublica('api.openverse.org',F.openverse)),
                ('inaturalist',RotaPublica('api.inaturalist.org',F.inaturalist_identidade,3,8_000_000)),
                ('nist_pagina',RotaPublica('www.nist.gov',lambda q,transport:G.candidatos(q,'nist','foto',transport=transport),4,9_000_000))]+([('smithsonian',RotaPublica('api.si.edu',C.smithsonian_identidade,3,8_000_000))] if os.getenv('DATA_GOV_API_KEY') else [])
    raise ValueError('TIPO_PUBLICO')
