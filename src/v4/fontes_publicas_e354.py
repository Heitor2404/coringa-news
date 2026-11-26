"""Bounded discovery adapters. Metadata is a lead, never a publication permit."""
import hashlib
import json
import re
from urllib.parse import urlencode, urljoin, urlsplit
from src.v4.aquisicao_documental import Transporte

OPENVERSE_HOSTS={'live.staticflickr.com','farm1.staticflickr.com','farm2.staticflickr.com','farm3.staticflickr.com','farm4.staticflickr.com','farm5.staticflickr.com','farm6.staticflickr.com','farm7.staticflickr.com','farm8.staticflickr.com','farm9.staticflickr.com','upload.wikimedia.org','images.pexels.com'}
INAT_HOSTS={'inaturalist-open-data.s3.amazonaws.com','inaturalist-open-data.s3.us-west-2.amazonaws.com'}
LICENSES={'by':'CC BY','by-sa':'CC BY-SA','cc0':'CC0','pdm':'Public domain mark'}
def safe(url, hosts):
    try:
        u=urlsplit(url)
        return isinstance(url,str) and u.scheme=='https' and bool(u.hostname) and u.hostname in hosts and not u.username and not u.password and u.port in (None,443) and not u.fragment
    except (TypeError,ValueError,AttributeError):return False

def _query(q):
    if not isinstance(q,str) or not 2<=len(q.strip())<=180:raise ValueError('QUERY')
    return q.strip()
def _json(t,base,params):
    raw=t.get(base+'?'+urlencode(params),{urlsplit(base).hostname},2_000_000)
    return json.loads(raw),hashlib.sha256(raw).hexdigest()
def _transport(t):
    return t if t is not None else Transporte(max_http=3,max_bytes=5_000_000,max_wait=12)
def _lic(code,version,url):
    if code not in LICENSES:return None
    if code in ('by','by-sa'):
        if version not in ('1.0','2.0','2.5','3.0','4.0'):return None
        expected='https://creativecommons.org/licenses/'+code+'/'+version+'/'
    elif code=='cc0':
        expected='https://creativecommons.org/publicdomain/zero/1.0/'
    else:
        # Public Domain Mark is not itself a licence; retain only as a lead.
        return None
    if not isinstance(url,str) or url.replace('http://','https://',1).rstrip('/')!=expected.rstrip('/'):return None
    return LICENSES[code]+' '+(version if code in ('by','by-sa') else '1.0'),expected

def openverse(q,*,transport=None):
    q=_query(q);t=_transport(transport)
    data,digest=_json(t,'https://api.openverse.org/v1/images/',{'q':q,'license':'by,by-sa,cc0','page_size':12,'mature':'false'})
    out=[]
    for row in data.get('results',[])[:12]:
        if not isinstance(row,dict):continue
        lic=_lic(row.get('license'),row.get('license_version'),row.get('license_url'))
        url=row.get('url');page=row.get('foreign_landing_url');author=row.get('creator');sid=row.get('id')
        # Restrict download origins, preserve the upstream landing page, not a thumbnail.
        if not lic or not safe(url,OPENVERSE_HOSTS) or not isinstance(page,str) or not author or not sid:continue
        try:
            if not safe(page,{urlsplit(page).hostname}):continue
        except ValueError:continue
        out.append({'titulo':row.get('title') or str(sid),'descricao':' '.join(str(x.get('name','')) for x in (row.get('tags') or [])[:8] if isinstance(x,dict)),
            'url':url,'pagina':page,'source_id':str(sid),'credito':str(author)+' ('+lic[0]+')','licenca':lic[0],'licenca_url':lic[1],
            'w':row.get('width'),'h':row.get('height'),'recibo_fonte':{'provider':'openverse','id':str(sid),'url':url,'page':page,'license_url':lic[1],'metadata_sha256':digest,'author':str(author)}})
        if len(out)>=4:break
    return out

def inaturalist(q,*,transport=None):
    q=_query(q);t=_transport(transport)
    data,digest=_json(t,'https://api.inaturalist.org/v1/observations',{'q':q,'quality_grade':'research','photos':'true','photo_license':'cc0,cc-by,cc-by-sa','per_page':12})
    out=[];seen_photos=set()
    from src.v4.formatos.revisao_documental import termos_consulta
    wanted=set(termos_consulta(q))
    for obs in data.get('results',[])[:12]:
        if not isinstance(obs,dict) or type(obs.get('id')) is not int or obs.get('quality_grade')!='research':continue
        tax=obs.get('taxon') or {}
        for p in (obs.get('photos') or [])[:3]:
            if not isinstance(p,dict):continue
            code=p.get('license_code');author=p.get('attribution');pid=p.get('id');u=p.get('url')
            # The photo licence, not the observation's licence, controls use.
            if code not in ('cc0','cc-by','cc-by-sa') or not author or type(pid) is not int or pid in seen_photos or not safe(u,INAT_HOSTS):continue
            # iNaturalist documents size tokens; preserve exact host and photo ID.
            path=urlsplit(u).path
            if not re.fullmatch(r'/photos/'+str(pid)+r'/(?:square|small|medium|large|original)\.(?:jpg|jpeg|png|webp)',path,re.I):continue
            original=re.sub(r'/(?:square|small|medium|large)\.', '/original.',u, count=1)
            if not safe(original,INAT_HOSTS):continue
            # Do not invent the CC version when API supplies only a code.
            # Attribution string and original observation are retained for manual audit.
            page='https://www.inaturalist.org/observations/'+str(obs['id']);sid=str(pid)
            dims=p.get('original_dimensions') or {};seen_photos.add(pid)
            out.append({'titulo':tax.get('preferred_common_name') or tax.get('name') or 'Observation '+str(obs['id']),'descricao':tax.get('name') or '',
                'url':original,'pagina':page,'source_id':sid,'credito':str(author),'licenca':code.upper(),
                'w':dims.get('width'),'h':dims.get('height'),'recibo_fonte':{'provider':'inaturalist','id':sid,'url':original,'page':page,'license_code':code,'metadata_sha256':digest,'author':str(author)}})
    # Rank all bounded response rows before truncation. Distinct observations
    # precede extra photos of the same subject; no metadata veto.
    def rank(c):
        terms=set(termos_consulta(c['titulo']+' '+c['descricao']))
        match=len(wanted&terms)
        w,h=c.get('w'),c.get('h')
        px=min(w,h) if type(w) is int and type(h) is int and min(w,h)>0 else 0
        return (-match,-int(px>=600),-int(px>0 and h>w),-px)
    ordered=sorted(out,key=rank);first=[];extra=[];pages=set()
    # Diversity within a relevance tier, not at the expense of a better taxon.
    for c in ordered:
        key=(rank(c)[0],c['pagina'])
        if key in pages:extra.append(c)
        else:pages.add(key);first.append(c)
    return sorted(first+extra,key=lambda c:rank(c)[0])[:4]

def usgs(q,kind,*,transport=None):
    q=_query(q);t=_transport(transport)
    from bs4 import BeautifulSoup
    role={'video':'videos','foto':'images'}[kind]
    bundle='video' if kind=='video' else 'image'
    # The public multimedia gallery exposes both filters in its GET URL.
    base='https://www.usgs.gov/products/multimedia-gallery/all-multimedia?'+urlencode({'media_bundle['+bundle+']':bundle,'search_api_fulltext':q})
    raw=t.get(base,{'www.usgs.gov'},3_000_000)
    soup=BeautifulSoup(raw,'html.parser');out=[];seen=set()
    import unicodedata
    def terms(s):
        norm=''.join(x for x in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(x))
        return set(re.findall(r'[a-z0-9]{3,}',norm))-{'the','and','for','video','photo','image'}
    wanted=terms(q)
    for a in soup.find_all('a',href=True):
        u=urljoin(base,a['href'])
        if not re.fullmatch(r'https://www\.usgs\.gov/media/'+role+r'/[a-z0-9-]+',u) or u in seen:continue
        title=a.get_text(' ',strip=True)
        if not title or not wanted.intersection(terms(title+' '+u.rsplit('/',1)[-1])):continue
        seen.add(u)
        # Gallery link often names the thumbnail, not the source video. Keep
        # the label and the observed URL slug separately as discovery hints.
        slug=u.rsplit('/',1)[-1].replace('-',' ')
        alt_label=title
        if kind=='video' and re.match(r'^(?:color |black and white )?(?:photo(?:graph)?|image)\b',title,re.I):title=slug
        out.append({'titulo':title,'descricao':alt_label if title!=alt_label else slug,'url':u,'pagina':u,'source_id':u,'credito':'','licenca':'',
            'recibo_fonte':{'provider':'usgs_pagina','id':u,'page':u,'metadata_sha256':hashlib.sha256(raw).hexdigest(),'credit_pending':True,'title_origin':'PAGE_SLUG_NOT_OFFICIAL_TITLE' if title!=alt_label else 'LINK_TEXT'}})
        if len(out)>=4:break
    return out

def receipt_choices(c):
    """Only fetch bytes from a retained provider-declared receipt. Rights stay pending."""
    p=c.get('fonte');r=c.get('recibo_fonte') or {}
    hosts={'openverse':OPENVERSE_HOSTS,'inaturalist':INAT_HOSTS}.get(p)
    if not hosts or r.get('provider')!=p or r.get('id')!=c.get('source_id') or r.get('url')!=c.get('url') or r.get('page')!=c.get('pagina') or not r.get('author') or not re.fullmatch(r'[0-9a-f]{64}',str(r.get('metadata_sha256',''))) or not safe(c.get('url'),hosts):raise ValueError('FONTE_RECIBO')
    if p=='openverse' and r.get('license_url')!=c.get('licenca_url'):raise ValueError('FONTE_LICENCA')
    if p=='inaturalist' and r.get('license_code') not in ('cc0','cc-by','cc-by-sa'):raise ValueError('FONTE_LICENCA')
    return [{'url':c['url']}],hosts
