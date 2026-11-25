"""E251: opt-in rehydrated originals for private documentary inspection.
A catalogue hit is not a semantic verdict. No network fallback inside this adapter.
"""
import re
from pathlib import Path
from PIL import Image
from src.v3.pacote_biblioteca import sha

def escopo(n):
    return {k:n.get(k) for k in ('id','sujeito','mostrar','fatos','necessidade','evidencia_visual')}

def historicos(n):
    """Explicit historical leads, never semantic approvals or a cache."""
    out=[]
    for h in n.get('candidatos_historicos') or []:
        if not isinstance(h,dict) or h.get('escopo')!=escopo(n) or h.get('publicar') is not False or h.get('direitos_aprovados') is not False or h.get('estado')!='PISTA_HISTORICA_PENDENTE':continue
        if not re.fullmatch('[0-9a-f]{64}',str(h.get('sha256',''))) or not h.get('pagina') or not h.get('relatorio') or not h.get('necessidade_anterior'):continue
        if h.get('tipo') not in ('foto','video') or (n.get('evidencia_visual')=='movimento' and h['tipo']!='video'):continue
        if n.get('necessidade') not in ('registro','lacuna_explicativa'):continue
        out.append(h)
    return out

def vinculo_historico(n,row):
    return next((h for h in historicos(n) if h['sha256']==row.get('sha256') and h['pagina']==row.get('url_pagina') and h['tipo']==row.get('tipo')),None)

def candidatos(bib,necessidade,limite=4):
    if necessidade.get('necessidade') not in ('registro','lacuna_explicativa'):return []
    ev=necessidade.get('evidencia_visual')
    tipos=('video',) if ev=='movimento' else ('foto','video')
    search=necessidade.get('pesquisa') or {}
    queries=(search.get('consultas_en') or [])+(search.get('consultas') or [])
    out=[];seen=set();ranked={}
    for h in historicos(necessidade):
        d=bib.obter('cm-'+h['sha256'][:12])
        if d and not d.get('ia') and vinculo_historico(necessidade,d):
            ranked[h['sha256']]=(2,d['tipo'],d)
    for q in queries:
        for tipo in tipos:
            # Rank metadata first, but only count verified local files against the review quota.
            for d in bib.buscar(q,tipo=tipo,so_comercial=False,limite=None):
                h=d['sha256'];score=d.get('pontos',0)
                if h not in ranked or score>ranked[h][0]:ranked[h]=(score,tipo,d)
    for _,tipo,d in sorted(ranked.values(),key=lambda x:-x[0]):
        h=d['sha256']
        if h in seen or d['uso_comercial']=='nao':continue
        if tipo=='video' and d['ext'] not in ('.mp4','.webm','.mov'):continue
        if tipo=='foto' and d['ext'] not in ('.jpg','.jpeg','.png','.webp'):continue
        p=bib.caminho(h,d['ext'])
        if not p.is_file() or sha(p)!=h:continue
        seen.add(h)
        out.append({'fonte':'biblioteca_v3','source_id':d['id'],'tipo':tipo,
            'titulo':d['titulo'],'descricao':d['descricao'],'url':d['url_original'],
            'pagina':d['url_pagina'],'credito':d['atribuicao'],'licenca':d['licenca'],
            'direitos':'QUARENTENA_REVISAO_PRIVADA','sha_catalogo':h,
            'natureza_preliminar':'NATUREZA_PENDENTE_INSPECAO','publicar':False,
            **({'pista_historica':vinculo_historico(necessidade,d)} if vinculo_historico(necessidade,d) else {})})
        if len(out)>=limite:return out
    return out

def amostra(bib,c,*,probe=None,frame=None):
    if c.get('fonte')!='biblioteca_v3' or c.get('publicar') is not False:raise ValueError('E251-PRIVADO')
    d=bib.obter(c['source_id'])
    if not d or d['sha256']!=c['sha_catalogo'] or d['tipo']!=c['tipo'] or d['uso_comercial']=='nao':raise ValueError('E251-VINCULO')
    p=bib.caminho(d['sha256'],d['ext'])
    if not p.is_file() or sha(p)!=d['sha256']:raise ValueError('E251-BYTES')
    if c['tipo']=='foto':
        if d['ext'] not in ('.jpg','.jpeg','.png','.webp'):raise ValueError('E251-TIPO')
        with Image.open(p) as im:
            if im.format not in ('JPEG','PNG','WEBP') or min(im.size)<600:raise ValueError('E251-PIXELS')
            w,h=im.size;visual=im.convert('RGB')
        dur=None
    elif c['tipo']=='video':
        if d['ext'] not in ('.mp4','.webm','.mov') or probe is None or frame is None:raise ValueError('E251-TIPO')
        w,h,dur=probe(p)
        if min(w,h)<360 or dur<3:raise ValueError('E251-VIDEO')
        visual=frame(p,min(2,dur*.3),width=640)
    else:raise ValueError('E251-TIPO')
    return {'width':w,'height':h,'duration_s':dur,'sha256':d['sha256'],'bytes':p.stat().st_size,
        'url_adquirida':d['url_original'],'status':'BYTES_VERIFIED_SEMANTICS_PENDING',
        'reuso_biblioteca':True,'direitos_aprovados':False},visual,p
