"""Optional stock discovery; contextual only, 24h metadata cache, no media cache."""
import json
import os
import re
from src.v4.cache_stock_e365 import CacheStock
from urllib.parse import urlsplit
import requests
from src.v4.aquisicao_documental import UA
from src.v4.fontes_publicas_e354 import safe,_query
PEXELS_PAGE={'www.pexels.com','pexels.com'}
PIXABAY_PAGE={'pixabay.com','www.pixabay.com'}
PEXELS_MEDIA={'videos.pexels.com','player.vimeo.com'}
PIXABAY_MEDIA={'cdn.pixabay.com','videos.pexels.com'}
def _get(url,params,headers,session):
    # Never propagate HTTP errors with credential-bearing query URLs.
    try:
        with session.get(url,params=params,headers=headers,timeout=(10,25),stream=True,allow_redirects=False) as r:
            if r.status_code!=200:raise ValueError('STOCK_HTTP_'+str(r.status_code))
            data=bytearray()
            for chunk in r.iter_content(65536):
                data.extend(chunk)
                if len(data)>2_000_000:raise ValueError('STOCK_METADATA_LIMIT')
        return json.loads(data)
    except requests.RequestException:
        raise ValueError('STOCK_NETWORK') from None
def _candidate(provider,row,variants,page,author,license_url,title):
    if not author or not variants or not row.get('id'):return None
    # Portrait priority only after valid format, dimensions and source URL.
    v=sorted(variants,key=lambda x:(x['h']<=x['w'],-min(x['w'],x['h'])))[0]
    return dict(provider=provider,id=str(row['id']),page=page,author=author,license_url=license_url,
                title=title,variant=v,variants=variants,kind='video',editorial_scope='CONTEXTO_APENAS',
                rights='REVISAR_PAGINA_INDIVIDUAL',publish=False,semantic_approval=False,permanent_cache=False)
def _pexels(q,session,key):
    data=_get('https://api.pexels.com/v1/videos/search',{'query':q,'orientation':'portrait','per_page':12},
              {**UA,'Authorization':key},session or requests.Session())
    out=[]
    for row in data.get('videos',[])[:12]:
        page=row.get('url');author=(row.get('user') or {}).get('name')
        if not safe(page,PEXELS_PAGE) or not isinstance(row.get('duration'),(int,float)) or row['duration']<3:continue
        variants=[]
        for v in row.get('video_files',[])[:20]:
            w,h=v.get('width'),v.get('height');url=v.get('link')
            if v.get('file_type')!='video/mp4' or not safe(url,PEXELS_MEDIA) or not all(type(x) is int and x>=360 for x in (w,h)):continue
            variants.append(dict(url=url,w=w,h=h,size=v.get('size') if type(v.get('size')) is int and v['size']>0 else None))
        c=_candidate('pexels',row,variants,page,author,'https://www.pexels.com/license/',q)
        if c:out.append(c)
    out.sort(key=lambda c:(c['variant']['h']<=c['variant']['w'],-min(c['variant']['w'],c['variant']['h'])))
    return {'status':'LEADS' if out else 'EMPTY','candidates':out[:4]}
def pertinencia_stock(q,c):
    """Only provider tags; ignore format hints, never infer factual coverage."""
    from src.v4.formatos.revisao_documental import termos_consulta
    words=set(termos_consulta(q))-{'vertical','portrait','horizontal','landscape','video','footage','clip','film','4k','hd'}
    tags=set(termos_consulta(c.get('title')))
    if not words:return 0.
    return len(words&tags)/len(words)

def ordenar_stock(q,candidates):
    def rank(c):
        score=pertinencia_stock(q,c)
        v=c['variant']
        # A relevant portrait beats a similarly relevant landscape, but an
        # unrelated portrait cannot beat a highly relevant landscape.
        tier=2 if score>=.6 else 1 if score>0 else 0
        return (-tier,v['h']<=v['w'],-score,-min(v['w'],v['h']))
    return sorted(candidates,key=rank)

def _pixabay(q,session,key):
    data=_get('https://pixabay.com/api/videos/',{'key':key,'q':q[:100],'per_page':20,'safesearch':'true','video_type':'film'},UA,session or requests.Session())
    out=[]
    for row in data.get('hits',[])[:20]:
        if row.get('type') not in (None,'film') or re.search(r'\b(green screen|chroma|template|intro|overlay|countdown)\b',str(row.get('tags','')),re.I):continue
        page=row.get('pageURL');author=row.get('user')
        if not safe(page,PIXABAY_PAGE) or not isinstance(row.get('duration'),(int,float)) or row['duration']<3:continue
        variants=[]
        for v in (row.get('videos') or {}).values():
            w,h=v.get('width'),v.get('height');url=v.get('url')
            if not safe(url,PIXABAY_MEDIA) or not all(type(x) is int and x>=360 for x in (w,h)):continue
            variants.append(dict(url=url,w=w,h=h,size=v.get('size') if type(v.get('size')) is int and v['size']>0 else None))
        c=_candidate('pixabay',row,variants,page,author,'https://pixabay.com/service/license-summary/',str(row.get('tags') or q))
        if c:out.append(c)
    out=ordenar_stock(q,out)
    return {'status':'LEADS' if out else 'EMPTY','candidates':out[:4]}

def _cached(provider,q,session,key,cache,load,params):
    q=_query(q);key=key or os.getenv(provider.upper()+'_API_KEY')
    if not key:return {'status':'CHAVE_AUSENTE','candidates':[]}
    if cache is None:
        path=os.getenv('CORINGA_STOCK_CACHE_DB')
        if not path:return {'status':'CACHE_24H_AUSENTE','candidates':[]}
        cache=CacheStock(path)
    return cache.fetch(provider,{'q':q if provider=='pexels' else q[:100],**params},lambda:load(q,session,key))

def pexels(q,*,session=None,key=None,cache=None):
    return _cached('pexels',q,session,key,cache,_pexels,{'orientation':'portrait','per_page':12,'version':1})

def pixabay(q,*,session=None,key=None,cache=None):
    result=_cached('pixabay',q,session,key,cache,_pixabay,{'video_type':'film','per_page':20,'safesearch':True,'version':1})
    # Re-rank cached rows locally; don't reset the 24h cache version.
    return {**result,'candidates':ordenar_stock(q,result.get('candidates') or [])}

def pixabay_retrato(q,*,session=None,key=None,cache=None):
    """At most one alternate text query, never an invented orientation filter."""
    q=_query(q);first=pixabay(q,session=session,key=key,cache=cache)
    if first['status'] not in ('LEADS','EMPTY'):return first
    original=first.get('candidates') or []
    if any(c['variant']['h']>c['variant']['w'] and pertinencia_stock(q,c)>=.6 for c in original) or re.search(r'\b(?:vertical|portrait)\b',q,re.I):
        return {**first,'consultas':[q],'retrato_pista':False}
    alt=('vertical '+q)[:100].strip()
    second=pixabay(alt,session=session,key=key,cache=cache)
    if second['status'] not in ('LEADS','EMPTY'):
        return {**first,'consultas':[q,alt],'alternativa_status':second['status'],'retrato_pista':True}
    unique={}
    for c in original+(second.get('candidates') or []):unique.setdefault(c['id'],c)
    candidates=ordenar_stock(q,unique.values())[:4]
    return {'status':'LEADS' if candidates else 'EMPTY','candidates':candidates,'consultas':[q,alt],
            'cache_hits':[first.get('cache_hit'),second.get('cache_hit')],'retrato_pista':True}

def pesquisar(q,*,necessidade):
    # Never treat stock search as event-specific evidence or factual action.
    if necessidade.get('evidencia_visual')!='contexto':return {'status':'ESCOPO_NAO_CONTEXTUAL','candidates':[]}
    if os.getenv('CORINGA_STOCK_CONTEXT_ENABLED')!='1':return {'status':'STOCK_OPT_IN_DESATIVADO','candidates':[]}
    return {name:fn(q) for name,fn in [('pexels',pexels),('pixabay',pixabay_retrato)]}
