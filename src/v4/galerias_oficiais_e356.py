"""Official gallery exploration. Narrow, private, per-page receipts; no guessed API."""
from urllib.parse import urljoin,urlsplit,urlencode
import re,hashlib
from bs4 import BeautifulSoup
from src.v4.aquisicao_documental import Transporte
from src.v4.fontes_publicas_e354 import safe,_query

CONFIG={
 'noaa':{'host':'oceanexplorer.noaa.gov','foto':'/multimedia/','video':'/multimedia/'},
 'nist':{'host':'www.nist.gov','foto':'/image-gallery','video':'/video-gallery'},
}
MEDIA={'noaa':{'oceanexplorer.noaa.gov','archive.oceanexplorer.noaa.gov'},'nist':{'www.nist.gov'}}
def _soup(raw):return BeautifulSoup(raw,'html.parser')
def _path(provider,kind):
    return r'/multimedia/[a-z0-9-]+/' if provider=='noaa' else ('/image/' if kind=='foto' else '/video/')+r'[a-z0-9-]+'
def _page(url,provider,kind):
    return safe(url,{CONFIG[provider]['host']}) and bool(re.fullmatch(_path(provider,kind),urlsplit(url).path)) and not urlsplit(url).query
def _tokens(s):return set(re.findall(r'[a-z0-9]{3,}',str(s).casefold()))-{'the','and','for','with','from','video','image','photo'}
def _search_form(soup,base,provider):
    """Use actual GET form names; no guessed CMS query parameter."""
    for form in soup.find_all('form'):
        if (form.get('method') or 'get').lower()!='get':continue
        target=urljoin(base,form.get('action') or base)
        if not safe(target,{CONFIG[provider]['host']}) or urlsplit(target).path!=urlsplit(base).path:continue
        for field in form.find_all('input'):
            name=field.get('name');fid=field.get('id')
            label=soup.find('label',attrs={'for':fid}) if fid else None
            marker=' '.join([str(field.get('placeholder') or ''),label.get_text(' ',strip=True) if label else '',str(field.get('aria-label') or '')]).lower()
            if name and ('keyword' in marker or 'keyword' in name.lower()):
                return target,name
    return None
def discover(q,provider,kind,*,transport=None):
    q=_query(q);conf=CONFIG[provider];t=transport or Transporte(max_http=4,max_bytes=9_000_000,max_wait=12)
    base='https://'+conf['host']+conf[kind]
    raw=t.get(base,{conf['host']},3_000_000);soup=_soup(raw);initial_raw=raw;initial_soup=soup;form=_search_form(soup,base,provider)
    mode='VISIBLE_GALLERY_ONLY'
    if form:
        target,name=form;sep='&' if urlsplit(target).query else '?'
        raw=t.get(target+sep+urlencode({name:q}),{conf['host']},3_000_000)
        soup=_soup(raw);mode='GET_FORM_QUERY'
    def extract(soup,raw,mode):
        out=[];seen=set();terms=_tokens(q)
        for a in soup.find_all('a',href=True):
            u=urljoin(base,a['href']);title=a.get_text(' ',strip=True)
            if not _page(u,provider,kind) or u in seen or not title:continue
            # A card can have a separate title, caption and action link.
            # Never use an entire listing as context for a single item.
            contexts=[title]
            for node in list(a.parents)[:4]:
                txt=node.get_text(' ',strip=True)
                links={urljoin(base,x['href']) for x in node.find_all('a',href=True)
                       if _page(urljoin(base,x['href']),provider,kind)}
                if len(txt)>1400 or len(links)>1:break
                if txt:contexts.append(txt)
            description=contexts[-1]
            if provider=='noaa':
                label=title.lower()
                if label in ('watch video','view image'):
                    if (label=='watch video')!=(kind=='video'):continue
                else:
                    marker=description.lower()
                    want='video' if kind=='video' else 'image'
                    other='image' if kind=='video' else 'video'
                    if not re.search(r'\b'+want+r'\b',marker) or re.search(r'\b'+other+r'\b',marker):continue
            if not terms.intersection(_tokens(title+' '+description+' '+urlsplit(u).path)):continue
            seen.add(u);out.append(dict(provider=provider,kind=kind,page=u,title=title,description=description[:500],mode=mode,metadata_sha256=hashlib.sha256(raw).hexdigest(),status='PAGE_LEAD',publish=False))
            if len(out)>=4:break
        return out
    out=extract(soup,raw,mode)
    if not out and form:
        # The original page is already available; no extra HTTP retry.
        out=extract(initial_soup,initial_raw,'VISIBLE_GALLERY_FALLBACK')
        if out:mode='VISIBLE_GALLERY_FALLBACK'
    return {'mode':mode,'status':'LEADS' if out else ('PARTIAL_NO_MATCH' if not form else 'EMPTY_QUERY'),'candidates':out}

def candidatos(q,provider,kind,*,transport=None):
    report=discover(q,provider,kind,transport=transport)
    return [{'titulo':x['title'],'descricao':x.get('description') or '',
             'url':x['page'],'pagina':x['page'],'source_id':x['page'],'credito':'','licenca':'',
             'recibo_fonte':{'provider':provider+'_pagina','id':x['page'],'page':x['page'],
                             'metadata_sha256':x['metadata_sha256'],'mode':x['mode']}}
            for x in report['candidates']]
def _credit(soup):
    for node in soup.find_all(string=re.compile(r'^\s*Credit\s*:?\s*$',re.I)):
        p=node.parent
        for x in (p.find_next_sibling(),p.parent.find_next_sibling() if p.parent else None):
            if x:
                s=x.get_text(' ',strip=True)
                if s and len(s)<300:return s
    return None
def receipt(page,provider,kind,*,transport=None):
    if not _page(page,provider,kind):raise ValueError('GALERIA_PAGE')
    t=transport or Transporte(max_http=3,max_bytes=4_000_000,max_wait=10)
    raw=t.get(page,{CONFIG[provider]['host']},3_000_000);soup=_soup(raw)
    credit=_credit(soup);body=soup.get_text(' ',strip=True)
    # Explicit restrictions trump the institutional web-wide policy.
    if re.search(r'stock art.{0,40}requires permission|copyrighted material|all rights reserved|used with permission',body,re.I):raise ValueError('GALERIA_RESTRICAO')
    if provider=='noaa':
        if not credit or not credit.startswith('NOAA Ocean Exploration'):raise ValueError('GALERIA_CREDITO')
        policy='https://oceanexplorer.noaa.gov/faqs/'
    else:
        if credit!='NIST':raise ValueError('GALERIA_CREDITO')
        policy='https://www.nist.gov/copyrights-disclaimers'
    variants=[]
    for a in soup.find_all('a',href=True):
        label=a.get_text(' ',strip=True);url=urljoin(page,a['href'])
        if not safe(url,MEDIA[provider]):continue
        ext=urlsplit(url).path.lower().rsplit('.',1)[-1]
        if provider=='nist' and (kind!='foto' or label.lower()!='download full image'):continue
        if provider=='noaa' and not re.search(r'\b(?:version|download|resolution|original)\b',label,re.I):continue
        if ext not in ({'mp4','mov','webm'} if kind=='video' else {'jpg','jpeg','png','webp'}):continue
        m=re.search(r'([\d.]+)\s*(MB|GB)',label,re.I)
        size=int(float(m[1])*(1_000_000 if m[2].lower()=='mb' else 1_000_000_000)) if m else None
        cap=80_000_000 if kind=='video' else 26_000_000
        if size is not None and size>cap:continue
        variants.append(dict(url=url,size=size,label=label))
    return dict(provider=provider,kind=kind,page=page,credit=credit,policy=policy,page_sha256=hashlib.sha256(raw).hexdigest(),
                variants=variants,status='PRIVATE_RECEIPT_PENDING' if variants else 'NO_DIRECT_VARIANT',rights='REVISAR_PAGINA_INDIVIDUAL',publish=False)
