"""Optional stock discovery; contextual only, no download or permanent cache."""
import json
import os
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
def pexels(q,*,session=None,key=None):
    q=_query(q);key=key or os.getenv('PEXELS_API_KEY')
    if not key:return {'status':'CHAVE_AUSENTE','candidates':[]}
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
            variants.append(dict(url=url,w=w,h=h))
        c=_candidate('pexels',row,variants,page,author,'https://www.pexels.com/license/',q)
        if c:out.append(c)
        if len(out)>=4:break
    return {'status':'LEADS' if out else 'EMPTY','candidates':out}
def pixabay(q,*,session=None,key=None):
    q=_query(q);key=key or os.getenv('PIXABAY_API_KEY')
    if not key:return {'status':'CHAVE_AUSENTE','candidates':[]}
    data=_get('https://pixabay.com/api/videos/',{'key':key,'q':q[:100],'per_page':12,'safesearch':'true'},UA,session or requests.Session())
    out=[]
    for row in data.get('hits',[])[:12]:
        page=row.get('pageURL');author=row.get('user')
        if not safe(page,PIXABAY_PAGE) or not isinstance(row.get('duration'),(int,float)) or row['duration']<3:continue
        variants=[]
        for v in (row.get('videos') or {}).values():
            w,h=v.get('width'),v.get('height');url=v.get('url')
            if not safe(url,PIXABAY_MEDIA) or not all(type(x) is int and x>=360 for x in (w,h)):continue
            variants.append(dict(url=url,w=w,h=h))
        c=_candidate('pixabay',row,variants,page,author,'https://pixabay.com/service/license-summary/',str(row.get('tags') or q))
        if c:out.append(c)
        if len(out)>=4:break
    return {'status':'LEADS' if out else 'EMPTY','candidates':out}
def pesquisar(q,*,necessidade):
    # Never treat stock search as event-specific evidence or factual action.
    if necessidade.get('evidencia_visual')!='contexto':return {'status':'ESCOPO_NAO_CONTEXTUAL','candidates':[]}
    return {name:fn(q) for name,fn in [('pexels',pexels),('pixabay',pixabay)]}
