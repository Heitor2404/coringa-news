"""Credential-optional cultural discovery with per-media, not metadata, rights."""
import hashlib,json,os
from urllib.parse import urlencode,urlsplit
from src.v4.aquisicao_documental import Transporte
from src.v4.fontes_publicas_e354 import safe,_query

SMITH_MEDIA={'ids.si.edu'}
SMITH_PAGES={'n2t.net','www.si.edu','collections.si.edu','airandspace.si.edu','americanhistory.si.edu','naturalhistory.si.edu','npg.si.edu','americanart.si.edu','www.americanart.si.edu','asia.si.edu','africa.si.edu','nmaahc.si.edu','postalmuseum.si.edu'}
EU_PAGES={'www.europeana.eu','europeana.eu'}
def _metadata(t,url,params):
    raw=t.get(url+'?'+urlencode(params),{urlsplit(url).hostname},4_000_000)
    return json.loads(raw),hashlib.sha256(raw).hexdigest()
def _smith_page(u):
    if not isinstance(u,str):return None
    if u.startswith('http://'):u='https://'+u[7:]
    return u if safe(u,SMITH_PAGES) else None
def _txt(x):
    return x if isinstance(x,str) else ''
def smithsonian(q,*,transport=None,key=None,diagnostico=None):
    q=_query(q);key=key or os.getenv('DATA_GOV_API_KEY')
    if not key:return []
    t=transport or Transporte(max_http=3,max_bytes=6_000_000,max_wait=12)
    query='('+q[:100]+') AND online_media_type:"Images" AND media_usage:CC0'
    data,digest=_metadata(t,'https://api.si.edu/openaccess/api/v1.0/search',{'q':query,'rows':25,'api_key':key})
    response=data.get('response') or {};rows=response.get('rows') or []
    diag=diagnostico if diagnostico is not None else {}
    diag.update(rows=len(rows),reasons={},total=response.get('rowCount'),metadata_sha256=digest)
    def reject(reason):diag['reasons'][reason]=diag['reasons'].get(reason,0)+1
    out=[]
    for row in rows[:25]:
        if not isinstance(row,dict):continue
        counts['rows']+=1
        content=row.get('content') or {};dnr=content.get('descriptiveNonRepeating') or {}
        rid=_txt(row.get('id') or dnr.get('record_ID'));page=_smith_page(dnr.get('record_link'))
        institution=_txt(dnr.get('data_source') or dnr.get('unit_code') or row.get('unitCode'))
        if not rid:reject('NO_RECORD_ID');continue
        if not page:reject('PAGE_UNSUPPORTED');continue
        if not institution:reject('NO_INSTITUTION');continue
        medias=(dnr.get('online_media') or {}).get('media') or []
        if not medias:reject('NO_MEDIA')
        for media in medias[:8]:
            if not isinstance(media,dict):continue
            # Object metadata CC0 alone is explicitly insufficient.
            if (media.get('usage') or {}).get('access')!='CC0':reject('MEDIA_RIGHTS_NOT_CC0');continue
            if str(media.get('type','')).lower() not in ('image','images'):reject('NOT_IMAGE');continue
            url=media.get('content')
            if not safe(url,SMITH_MEDIA):reject('MEDIA_HOST_UNSUPPORTED');continue
            # Prefer explicit full image resource if it is labelled as such.
            for r in media.get('resources') or []:
                label=str(r.get('label') or '').lower()
                if 'jpeg' in label and 'thumb' not in label and safe(r.get('url'),SMITH_MEDIA):
                    url=r['url'];break
            mid=str(media.get('idsId') or media.get('id') or hashlib.sha256(url.encode()).hexdigest())
            sid=rid+':'+mid
            credit=institution+' · Smithsonian Institution (CC0 1.0)'
            if institution=='Smithsonian Institution':credit=institution+' (CC0 1.0)'
            out.append(dict(titulo=_txt(row.get('title')) or rid,descricao=_txt(dnr.get('title')),url=url,pagina=page,
                source_id=sid,credito=credit,licenca='CC0 1.0',licenca_url='https://creativecommons.org/publicdomain/zero/1.0/',
                recibo_fonte=dict(provider='smithsonian',id=sid,record_id=rid,media_id=mid,url=url,page=page,media_access='CC0',
                    metadata_sha256=digest,institution=institution,media_sha256=hashlib.sha256(json.dumps(media,sort_keys=True).encode()).hexdigest())))
            counts['retained']+=1
            if len(out)>=4:return out
    return out

def smithsonian_choices(c):
    r=c.get('recibo_fonte') or {}
    if r.get('provider')!='smithsonian' or r.get('id')!=c.get('source_id') or r.get('url')!=c.get('url') or r.get('page')!=c.get('pagina') or r.get('media_access')!='CC0' or not r.get('record_id') or not r.get('media_id') or not r.get('institution') or c.get('licenca')!='CC0 1.0' or not safe(c.get('url'),SMITH_MEDIA):raise ValueError('SMITHSONIAN_RECIBO')
    return [{'url':c['url']}],SMITH_MEDIA

def europeana(q,kind,*,transport=None,key=None):
    """Search results are page leads only; resource-level rights not inferred."""
    q=_query(q);key=key or os.getenv('EUROPEANA_API_KEY')
    if not key:return []
    t=transport or Transporte(max_http=3,max_bytes=6_000_000,max_wait=12)
    data,digest=_metadata(t,'https://api.europeana.eu/record/v2/search.json',
        {'wskey':key,'query':q,'reusability':'open','media':'true','qf':'TYPE:'+{'foto':'IMAGE','video':'VIDEO'}[kind],'rows':12,'profile':'rich'})
    out=[]
    for row in data.get('items',[])[:12]:
        if not isinstance(row,dict):continue
        rid=row.get('id');page=row.get('guid');media=row.get('edmIsShownBy') or []
        if not isinstance(rid,str) or not safe(page,EU_PAGES) or not isinstance(media,list) or not media:continue
        rights=row.get('rights') or []
        out.append(dict(titulo=str((row.get('title') or [rid])[0]),url=page,pagina=page,source_id=rid,credito='',licenca='',
            recibo_fonte=dict(provider='europeana',id=rid,page=page,metadata_sha256=digest,record_rights=rights,media_urls=media[:4],resource_rights='PENDENTE')))
        if len(out)>=4:break
    return out
