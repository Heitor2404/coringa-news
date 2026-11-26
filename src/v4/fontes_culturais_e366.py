"""Credential-optional cultural discovery with per-media, not metadata, rights."""
import hashlib,json,os
from urllib.parse import urlencode,urlsplit
from src.v4.aquisicao_documental import Transporte
from src.v4.fontes_publicas_e354 import safe,_query

SMITH_MEDIA={'ids.si.edu'}
# Registry of Open Data on AWS and Smithsonian/OpenAccess confirm this exact bucket.
SMITH_DELIVERY_HOSTS=SMITH_MEDIA|{'smithsonian-open-access.s3-us-west-2.amazonaws.com'}
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
def object_types(content):
    """Only object-level classifications from Smithsonian structured metadata."""
    indexed=content.get('indexedStructured') or {}
    freetext=content.get('freetext') or {}
    values=[]
    for x in indexed.get('object_type') or []:
        if isinstance(x,str):values.append(x)
    for x in freetext.get('objectType') or []:
        if isinstance(x,dict) and isinstance(x.get('content'),str):values.append(x['content'])
    return list(dict.fromkeys(x.strip()[:160] for x in values if x.strip()))[:12]

def object_hint(query,title,types):
    """A photograph of an illustration is still a record of that object.
    This is a soft mismatch hint, never a license or semantic decision."""
    from src.v4.formatos.revisao_documental import termos_consulta
    import re
    wanted=set(termos_consulta(query))
    text=' '.join(types+[title]).casefold()
    typed=' '.join(types).casefold()
    forms={
        'stamp':r'\b(stamp|stamps|philatelic|postage|selos?)\b',
        'drawing':r'\b(drawing|drawings|engraving|engravings|illustration|illustrations|print|prints|painting|paintings)\b',
        'model':r'\b(model|models|miniature|miniatures|scale model)\b',
        'coin':r'\b(coin|coins|medal|medals)\b',
    }
    intended={'stamp':{'stamp','stamps','postage','philatelic','selo','selos'},'drawing':{'drawing','drawings','engraving','illustration','print','prints','painting','paintings'},'model':{'model','models','miniature','miniatures'},'coin':{'coin','coins','medal','medals'}}
    # Do not infer physical size, authenticity, or referent from an absent type.
    for key,pattern in forms.items():
        matched=(bool(re.search(pattern,typed)) or bool(re.search(r'\b(scale model|miniature|miniatures)\b',title,re.I))) if key=='model' else bool(re.search(pattern,text))
        if matched and not (wanted&intended[key]):
            return 'POSSIVEL_REPRESENTACAO_DE_OUTRO_REFERENTE'
    return 'SEM_INCOMPATIBILIDADE_DECLARADA'

def object_rank(query,c):
    from src.v4.formatos.revisao_documental import termos_consulta
    # Requested format is a separate clue, not the subject itself.
    forms={'photograph','photographs','photography','photo','photos','image','images','picture','pictures','record','archive','historical'}
    wanted=set(termos_consulta(query))-forms
    title=set(termos_consulta(c.get('titulo')))
    desc=set(termos_consulta(c.get('descricao')))
    coverage=len(wanted&(title|desc))/max(1,len(wanted))
    tier=2 if coverage>=.6 else 1 if coverage>0 else 0
    mismatch=c.get('pista_objeto')=='POSSIVEL_REPRESENTACAO_DE_OUTRO_REFERENTE'
    return (-tier,mismatch,-coverage,-len(wanted&title))

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
        content=row.get('content') or {};dnr=content.get('descriptiveNonRepeating') or {}
        rid=_txt(row.get('id') or dnr.get('record_ID'));page=_smith_page(dnr.get('record_link'))
        institution=_txt(dnr.get('data_source') or dnr.get('unit_code') or row.get('unitCode'))
        if not rid:reject('NO_RECORD_ID');continue
        if not page:reject('PAGE_UNSUPPORTED');continue
        if not institution:reject('NO_INSTITUTION');continue
        types=object_types(content)
        title=_txt(row.get('title')) or rid
        hint=object_hint(q,title,types)
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
            out.append(dict(titulo=title,descricao=' · '.join(filter(None,[_txt(dnr.get('title')),*types])),url=url,pagina=page,
                tipo_objeto_declarado=types,pista_objeto=hint,
                source_id=sid,credito=credit,licenca='CC0 1.0',licenca_url='https://creativecommons.org/publicdomain/zero/1.0/',
                recibo_fonte=dict(provider='smithsonian',id=sid,record_id=rid,media_id=mid,url=url,page=page,media_access='CC0',
                    metadata_sha256=digest,institution=institution,object_types=types,object_hint=hint,media_sha256=hashlib.sha256(json.dumps(media,sort_keys=True).encode()).hexdigest())))
    from src.v4.formatos.revisao_documental import termos_consulta
    def rank(c):return object_rank(q,c)
    ordered=sorted(out,key=rank);first=[];extra=[];seen=set()
    for c in ordered:
        rid=c['recibo_fonte']['record_id']
        if rid in seen:extra.append(c)
        else:seen.add(rid);first.append(c)
    result=sorted(first+extra,key=rank)[:4]
    diag['eligible_media']=len(out);diag['retained']=len(result)
    diag['retained_possible_mismatch']=sum(c['pista_objeto']=='POSSIVEL_REPRESENTACAO_DE_OUTRO_REFERENTE' for c in result)
    return result

def smithsonian_redirect(source,target):
    """Permit only delivery-service paths at the original institutional host."""
    from urllib.parse import unquote
    a,b=urlsplit(source),urlsplit(target)
    def path_ok(u):
        path=unquote(u.path)
        return (u.scheme=='https' and u.hostname=='ids.si.edu' and not u.username and not u.password
                and u.port in (None,443) and not u.fragment and '..' not in path.split('/')
                and '\\' not in path and (path=='/ids/deliveryService' or
                path.startswith('/ids/deliveryService/') or path=='/ids/download' or path.startswith('/ids/download/')))
    if not path_ok(a) or source==target:return False
    if path_ok(b):return True
    # Accept only the observed public Open Access bucket from the institutional
    # delivery endpoint; no arbitrary S3 buckets, listing, or private paths.
    path=unquote(b.path)
    return (b.scheme=='https' and b.hostname=='smithsonian-open-access.s3-us-west-2.amazonaws.com'
            and not b.username and not b.password and b.port in (None,443)
            and not b.fragment and not b.query and path.startswith('/media/')
            and '..' not in path.split('/') and '\\' not in path
            and path.lower().endswith(('.jpg','.jpeg','.png','.webp','.tif','.tiff')))

def smithsonian_choices(c):
    r=c.get('recibo_fonte') or {}
    if r.get('provider')!='smithsonian' or r.get('id')!=c.get('source_id') or r.get('url')!=c.get('url') or r.get('page')!=c.get('pagina') or r.get('media_access')!='CC0' or not r.get('record_id') or not r.get('media_id') or not r.get('institution') or c.get('licenca')!='CC0 1.0' or not safe(c.get('url'),SMITH_MEDIA):raise ValueError('SMITHSONIAN_RECIBO')
    return [{'url':c['url']}],SMITH_DELIVERY_HOSTS

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
