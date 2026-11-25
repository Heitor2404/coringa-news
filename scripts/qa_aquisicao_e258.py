"""Private E258 probe of the two formerly disconnected video sources."""
import json,sys
from pathlib import Path
from src.v4 import acervo_v4 as A
from src.v4.aquisicao_documental import Transporte
from scripts.qa_pesquisa_documental_e246 import sample

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    originals=out/'originais';originals.mkdir(exist_ok=True)
    t=Transporte(max_http=20,max_bytes=100_000_000,max_wait=30)
    # Contrast the previously failing query with a known domain of the NASA catalog.
    # These are transport probes, not approved editorial footage.
    cases=[('nasa_video','volcano eruption lava','nasa_volcano'),
           ('nasa_video','Earth rotating','nasa_short_control'),
           ('nasa_video','Apollo 11','nasa_control'),
           ('archive_video','Apollo 11 NASA','archive_apollo')]
    rows=[]
    global_http=t.max_http;global_bytes=t.max_bytes
    for index,(provider,q,case_id) in enumerate(cases):
        n={'id':case_id,'necessidade':'registro','evidencia_visual':'movimento',
           'pesquisa':{'consultas_en':[q]}}
        def sources(kind):return [(name,fn) for name,fn in A.fontes_documentais(kind) if name==provider]
        r=A.pesquisar_cobertura(n,fontes=sources,max_buscas=1,max_candidatos=64,progressivo=True)
        # This probe must leave every provider a chance; otherwise the first
        # large item consumes all HTTP before later sources can be diagnosed.
        remaining_cases=len(cases)-index
        t.max_http=t.http+(global_http-t.http)//remaining_cases
        t.max_bytes=t.bytes+(global_bytes-t.bytes)//remaining_cases
        before=t.resumo()
        try:
            for c in r['candidatos']:
                if t.http>=t.max_http or t.bytes>=t.max_bytes:break
                try:
                    m,im,p=sample(c,originals,t,progressivo=True,max_variantes=2)
                    c['aquisicao']=m
                    im.thumbnail((960,960));im.save(out/(case_id+'.jpg'),quality=90)
                    break
                except Exception as e:c['falha_aquisicao']=str(e)[:300]
        finally:
            r['prova_orcamento']={'http':t.http-before['http'],'bytes':t.bytes-before['bytes'],
                'limite_http_local':t.max_http-before['http'],'limite_bytes_local':t.max_bytes-before['bytes'],
                'candidatos_nao_tentados':sum('aquisicao' not in c and 'falha_aquisicao' not in c for c in r['candidatos'])}
            t.max_http=global_http;t.max_bytes=global_bytes
        rows.append(r)
    (out/'revisao.json').write_text(json.dumps({'publicar':False,'direitos_aprovados':False,'visao_chamadas':0,
        'rede':t.resumo(),'pesquisas':rows},ensure_ascii=False,indent=2),encoding='utf8')
    print('E258 ACQUISITION',[(r['id'],len(r['candidatos']),sum('aquisicao' in c for c in r['candidatos'])) for r in rows],flush=True)
if __name__=='__main__':main()
