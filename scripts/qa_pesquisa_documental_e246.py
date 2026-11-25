"""E246 resilient private discovery. Evidence acquisition is not rights or semantic approval."""
import hashlib,io,re,sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,quote
from PIL import Image,ImageDraw
from scripts.qa_documentario_curado_e218 import write
from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import diretor_visual_e202 as D
from src.v3.biblioteca import restaurar_catalogo
from src.v4.aquisicao_documental import Transporte

def variants(c):
    cap=26_000_000 if c['tipo']=='foto' else 80_000_000
    v=[{'url':c['url'],'size':c.get('tamanho_declarado'),'width':c.get('largura_declarada'),'height':c.get('altura_declarada')}]+c.get('variantes',[])
    seen=set()
    for x in v:
        if not x.get('url') or x['url'] in seen or (x.get('size') or 0)>cap:continue
        seen.add(x['url'])
        yield x

def nasa_receipt(c,t,*,progressivo=False,min_video_px=360):
    # The provider returns the collection of actual file variants. No guessed URL.
    import json
    nid=c.get('source_id')
    if not isinstance(nid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',nid):raise ValueError('NASA_ID')
    raw=t.get('https://images-api.nasa.gov/asset/'+nid,{'images-api.nasa.gov'},2_000_000)
    items=json.loads(raw)['collection']['items']
    urls=[];variants_receipt=[]
    ext=r'\.(mp4|webm|mov)$' if c.get('tipo')=='video' else r'\.(jpg|jpeg|png)$'
    for x in items:
        if not isinstance(x,dict) or not isinstance(x.get('href'),str):continue
        u=x['href']
        try:
            p=urlsplit(u)
            if p.hostname!='images-assets.nasa.gov' or p.username or p.password or p.port not in (None,443) or p.scheme not in ('http','https') or not re.search(ext,p.path,re.I):continue
        except ValueError:continue
        # Upgrade legacy provider URLs to HTTPS only for the exact NASA host.
        safe=urlunsplit(('https','images-assets.nasa.gov',p.path,p.query,''))
        variants_receipt.append({'href_declarado':u,'href_https':safe})
        if safe not in urls:urls.append(safe)
    # Progressive video discovery favors usable smaller derivatives before
    # expensive originals. The actual decoded resolution remains mandatory.
    # Photos and the legacy path retain their established ordering.
    if progressivo and c.get('tipo')=='video':
        ranks=({'medium':0,'large':1,'orig':2,'small':3,'mobile':4,'preview':5} if min_video_px>=700 else
               {'small':0,'medium':1,'mobile':2,'preview':3,'large':4,'orig':5})
        def rank(u):
            suffix=urlsplit(u).path.rsplit('~',1)[-1].split('.')[0].lower()
            return (ranks.get(suffix,4),u)
        urls.sort(key=rank)
    else:
        urls.sort(key=lambda u: (0 if '~medium' in u else 1 if '~large' in u else 2 if '~orig' in u else 3,u))
    if not urls:raise ValueError('NASA_SEM_VARIANTE')
    c['recibo_nasa']={'nasa_id':nid,'asset_response_sha256':hashlib.sha256(raw).hexdigest(),'variantes_declaradas':variants_receipt[:30],'credit_declared':c.get('nasa_credit'),'secondary_credit':c.get('nasa_secondary_credit'),'direitos':'PENDENTE_AUDITORIA_INDIVIDUAL'}
    return [{'url':u} for u in (urls if progressivo else urls[:3])]

def archive_receipt(c,t):
    """Item-specific declaration, actual file identity and storage locations.
    Never infer rights from collection membership. No arbitrary redirects."""
    import json
    ident=c.get('source_id')
    if not isinstance(ident,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,150}',ident) or ident in ('.','..'):raise ValueError('ARCHIVE_ID')
    raw=t.get('https://archive.org/metadata/'+ident+'?extended_err=1',{'archive.org'},4_000_000)
    d=json.loads(raw)
    if d==[]:raise ValueError('ARCHIVE_METADATA_AUSENTE')
    if not isinstance(d,dict):raise ValueError('ARCHIVE_METADATA_INVALIDA')
    if d.get('error'):
        code=d.get('errcode')
        raise ValueError('ARCHIVE_METADATA_ERRO_'+str(code) if type(code) is int else 'ARCHIVE_METADATA_ERRO')
    m=d.get('metadata') or {}
    if m.get('identifier')!=ident or d.get('is_dark') or d.get('nodownload') or m.get('access-restricted-item') in (True,'true','1'):raise ValueError('ARCHIVE_RECIBO_PENDENTE')
    lic=m.get('licenseurl')
    allowed={'https://creativecommons.org/licenses/by/4.0':'CC BY 4.0','https://creativecommons.org/publicdomain/zero/1.0':'CC0 1.0','https://creativecommons.org/publicdomain/mark/1.0':'Public Domain'}
    if not isinstance(lic,str):raise ValueError('ARCHIVE_LICENCA_PENDENTE')
    lic=lic.rstrip('/')
    if lic.startswith('http://creativecommons.org/'):lic='https://'+lic[7:]
    if lic not in allowed:raise ValueError('ARCHIVE_LICENCA_PENDENTE')
    directory=d.get('dir')
    if not isinstance(directory,str) or not re.fullmatch(r'/[0-9]+/items/'+re.escape(ident),directory):raise ValueError('ARCHIVE_DIRETORIO_PENDENTE')
    workable=d.get('workable_servers')
    declared=[d.get('d1'),d.get('d2'),d.get('server')]+(workable if isinstance(workable,list) else [])
    hosts={h for h in declared if isinstance(h,str) and re.fullmatch(r'ia[0-9]+(?:\.us)?\.archive\.org',h)}
    if not hosts:raise ValueError('ARCHIVE_HOST_PENDENTE')
    choices=[]
    for f in d.get('files') or []:
        name=f.get('name');md5=f.get('md5');size=f.get('size')
        if not isinstance(name,str) or '/' in name or '\\' in name or not name.lower().endswith(('.mp4','.webm','.mov')) or f.get('private') in (True,'true','1') or not isinstance(md5,str) or not re.fullmatch('[a-fA-F0-9]{32}',md5):continue
        if not str(size).isdigit() or not 0<int(size)<=80_000_000:continue
        for host in sorted(hosts):
            choices.append({'url':'https://'+host+directory+'/'+quote(name,safe=''),'size':int(size),'md5':md5.lower(),'file_name':name})
    if not choices:raise ValueError('ARCHIVE_SEM_VARIANTE')
    choices.sort(key=lambda v:v['size'])
    c['recibo_archive']={'identifier':ident,'metadata_sha256':hashlib.sha256(raw).hexdigest(),'licenca_url':lic,'direitos':'PENDENTE_AUDITORIA_INDIVIDUAL','variantes':choices}
    c['licenca']=allowed[lic];c['credito']=str(m.get('creator') or m.get('title') or ident)+' — Internet Archive'
    return choices,hosts

def progressive_stop(t):
    return getattr(t,'http',0)>=getattr(t,'max_http',float('inf')) or getattr(t,'bytes',0)>=getattr(t,'max_bytes',float('inf'))

USGS_VIDEO_HOSTS=E.HOSTS
USGS_PHOTO_HOSTS={'d9-wret.s3.us-west-2.amazonaws.com','prd-wret.s3.us-west-2.amazonaws.com'}

def candidato_pagina_usgs(row,necessidade):
    """Only explicitly curated individual source pages, not URLs invented by
    the director model. Page verification and visual review are downstream."""
    page=row.get('pagina');kind=row.get('tipo');credit=row.get('credito')
    if row.get('necessidade_id')!=necessidade['id'] or kind not in ('foto','video') or not isinstance(page,str) or not isinstance(credit,str) or not credit.strip():
        raise ValueError('USGS-CURADORIA')
    if necessidade.get('evidencia_visual')=='movimento' and kind!='video':
        raise ValueError('USGS-TIPO-EVIDENCIA')
    role='videos' if kind=='video' else 'images'
    if not re.fullmatch(r'https://www\.usgs\.gov/media/'+role+r'/[a-z0-9-]+',page):
        raise ValueError('USGS-PAGINA')
    return {'fonte':'usgs_pagina','source_id':page,'tipo':kind,'url':page,'pagina':page,
            'titulo':str(row.get('titulo') or page.rsplit('/',1)[-1]),'descricao':str(row.get('escopo') or ''),
            'credito':credit,'licenca':'','direitos':'REVISAR_PAGINA_INDIVIDUAL',
            'natureza_preliminar':'NATUREZA_PENDENTE_INSPECAO','publicar':False}


def usgs_receipt(c,t):
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    page=c.get('pagina');kind=c.get('tipo')
    role='videos' if kind=='video' else 'images' if kind=='foto' else None
    if not role or not isinstance(page,str) or not re.fullmatch(r'https://www\.usgs\.gov/media/'+role+r'/[a-z0-9-]+',page):
        raise ValueError('USGS-PAGINA')
    raw=t.get(page,{'www.usgs.gov'},5_000_000)
    soup=BeautifulSoup(raw,'html.parser')
    txt=soup.get_text(' ',strip=True)
    h=soup.find('h1')
    if not h or not h.get_text(' ',strip=True):raise ValueError('USGS-TITULO')
    if not re.search(r'Sources/Usage\s+Public Domain\b',txt,re.I):
        raise ValueError('USGS-LICENCA')
    hosts=USGS_VIDEO_HOSTS if kind=='video' else USGS_PHOTO_HOSTS
    labels=('download video',) if kind=='video' else ('original','medium')
    choices=[]
    for label in labels:
        for link in soup.find_all('a',href=True):
            text=link.get_text(' ',strip=True).lower()
            if (label not in text if kind=='video' else text!=label):continue
            u=urljoin(page,link['href'])
            try:
                x=urlsplit(u)
                if x.scheme!='https' or x.hostname not in hosts or x.username or x.password or x.port not in (None,443) or x.fragment:continue
            except ValueError:continue
            if not any(v['url']==u for v in choices):choices.append({'url':u,'rotulo':text})
    if not choices:raise ValueError('USGS-SEM-VARIANTE')
    c.update(titulo=h.get_text(' ',strip=True),licenca='Public domain',
             direitos='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA',
             recibo_usgs={'pagina':page,'page_sha256':hashlib.sha256(raw).hexdigest(),
                          'tipo':kind,'licenca_declarada':'Public Domain',
                          'credito_curado':c['credito'],'variantes':choices,
                          'direitos':'PENDENTE_AUDITORIA_INDIVIDUAL'})
    return choices,hosts


def sample(c,out,t,*,progressivo=False,max_variantes=None,min_video_px=360):
    if c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA':raise ValueError('REPRESENTACAO_NAO_E_REGISTRO')
    if c['fonte'] in ('nasa','nasa_video'):
        choices=nasa_receipt(c,t,progressivo=progressivo,min_video_px=min_video_px);hosts={'images-assets.nasa.gov'}
    elif c.get('fonte')=='archive_video':
        choices,hosts=archive_receipt(c,t)
    elif c.get('fonte')=='usgs_pagina':
        choices,hosts=usgs_receipt(c,t)
    elif c.get('fonte')=='figshare':
        from src.v4.fontes_cientificas import HOSTS,safe_url
        rec=c.get('recibo_cientifico') or {}
        if c.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or rec.get('provedor')!='figshare' or not safe_url(c['url'],HOSTS):raise ValueError('FIGSHARE_RECIBO')
        choices=[{'url':c['url']}];hosts=HOSTS
    elif c['direitos']=='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA':
        choices=list(variants(c));hosts={'upload.wikimedia.org'}
        if c['fonte']=='commons' and c['tipo']=='foto':
            # Exact Wikimedia thumbnail host, only URLs already declared by the file API.
            hosts.add('thumb.wikimedia.org')
    else:raise ValueError('PAGINA_PENDENTE')
    cap=26_000_000 if c['tipo']=='foto' else 80_000_000
    failures=[]
    if type(min_video_px) is not int or min_video_px<360:raise ValueError('VIDEO_MIN_PIXELS')
    ordered=choices if progressivo else choices[:3]
    # Optional experimental per-candidate allocation, never a universal
    # editorial limit. Caller can revisit with remaining global budget.
    if max_variantes is not None:
        if type(max_variantes) is not int or max_variantes<1:raise ValueError('LIMITE_PROVA_VARIANTES')
        ordered=ordered[:max_variantes]
    for v in ordered:
        if progressive_stop(t):break
        remaining=getattr(t,'max_bytes',cap)-getattr(t,'bytes',0)
        if (v.get('size') or 0)>min(cap,remaining):
            failures.append('LIMITE_DECLARADO_ANTES_HTTP');continue
        try:
            raw=t.get(v['url'],hosts,cap)
            if c.get('fonte')=='figshare':
                rec=c['recibo_cientifico']
                if len(raw)!=rec.get('bytes') or hashlib.md5(raw).hexdigest()!=rec.get('md5_declarado'):raise ValueError('FIGSHARE_INTEGRIDADE')
            if c.get('fonte')=='archive_video' and (len(raw)!=v['size'] or hashlib.md5(raw).hexdigest()!=v['md5']):raise ValueError('ARCHIVE_INTEGRIDADE')
            sha=hashlib.sha256(raw).hexdigest()
            if c['tipo']=='foto':
                with Image.open(io.BytesIO(raw)) as im:
                    if im.format not in ('JPEG','PNG','WEBP') or min(im.size)<600:raise ValueError('PIXELS')
                    w,h=im.size;ext={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[im.format]
                    visual=im.convert('RGB')
                path=out/(sha+ext);path.write_bytes(raw)
                meta={'width':w,'height':h,'duration_s':None}
            else:
                filename=(c.get('recibo_cientifico') or {}).get('file_name') or urlsplit(v['url']).path
                ext=Path(filename).suffix.lower()
                path=out/(sha+(ext if ext in ('.webm','.mov','.mp4') else '.mp4'))
                path.write_bytes(raw)
                w,h,dur=E.probe(path)
                if min(w,h)<min_video_px or dur<3:
                    c.setdefault('variantes_qualidade_insuficiente',[]).append({
                        'url':v['url'],'width':w,'height':h,'duration_s':dur,
                        'min_video_px':min_video_px,'sha256':sha,'bytes':len(raw)})
                    raise ValueError('VIDEO_QUALIDADE '+str(w)+'x'+str(h)+' minimo='+str(min_video_px))
                visual=E.frame(path,min(2,dur*.3),width=640)
                meta={'width':w,'height':h,'duration_s':dur}
            return {**meta,'sha256':sha,'bytes':len(raw),'url_adquirida':v['url'],'status':'BYTES_VERIFIED_SEMANTICS_PENDING'},visual,path
        except Exception as e:failures.append(str(e)[:120])
    raise ValueError('SEM_VARIANTE '+str(failures)[:250])

def main():
    spec=E.read(sys.argv[1]);out=Path(sys.argv[2]);caseid=sys.argv[3]
    if spec.get('publish') is not False:raise ValueError('PRIVATE_ONLY')
    case=next(c for c in spec['cases'] if c['id']==caseid)
    out.mkdir(parents=True,exist_ok=True);assets=out/'originais';assets.mkdir(exist_ok=True)
    tri=D.triagem_documental(case['necessidades'],case['fatos'])
    lib,rest=restaurar_catalogo(db=out/'biblioteca.sqlite3',armazem=out/'biblioteca')
    t=Transporte(max_http=14,max_bytes=140_000_000,max_wait=30)
    samples=[];reuses=0
    try:
        reports=D.pesquisar_triagem(tri,biblioteca_global=lib,max_buscas=8)
        for row in reports:
            # Restore actual bytes only from approved hosts and verify the original SHA.
            for b in row['biblioteca'][:2]:
                if b['origem']!='biblioteca_v3' or b.get('estado')=='MINIATURA_NAO_E_VIDEO':continue
                item=lib.obter(b['asset_id'])
                def recover(url,dest):
                    dest.write_bytes(t.get(url,{'upload.wikimedia.org','images-assets.nasa.gov','assets.science.nasa.gov','d9-wret.s3.us-west-2.amazonaws.com'},26_000_000))
                p=lib.recuperar(item['id'],baixar=recover)
                b['bytes_recuperados']=bool(p)
                if p:reuses+=1
            # Diversity and preflight: don't spend attempts on oversized originals with no variant.
            ordered=sorted(row['candidatos'],key=lambda c:(c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA',
                c['direitos']!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' and c['fonte']!='nasa',
                (c.get('tamanho_declarado') or 0)>26_000_000))
            attempts=0
            for c in ordered:
                if len(samples)>=2 or attempts>=6 or t.http>=t.max_http:break
                if c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA':
                    c['aquisicao']={'status':'SKIPPED','motivo':'REPRESENTACAO_DECLARADA'};continue
                if c['fonte']!='nasa' and (c['direitos']!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or not list(variants(c))):
                    c['aquisicao']={'status':'SKIPPED','motivo':'PRECHECK'};continue
                if c['fonte']!='nasa' and 'upload.wikimedia.org' in t.blocked:continue
                before=t.http
                try:
                    meta,im,p=sample(c,assets,t);c['aquisicao']=meta;samples.append((c,im))
                    # Record bytes in the existing library, not as semantic approval.
                    if c['direitos']=='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA':
                        saved=lib.ingerir(p,{'titulo':c['titulo'],'desc':c['descricao'],'credito':c['credito'],
                            'licenca':c['licenca'],'licenca_prova':'Declaracao individual pendente auditoria: '+str(c['pagina']),
                            'pagina':c['pagina'],'url':meta['url_adquirida'],'fonte':c['fonte'],'wh':[meta['width'],meta['height']]},
                            tema=case['tema'])
                        c['biblioteca_id']=saved['id']
                except Exception as e:
                    if c.get('aquisicao',{}).get('status')=='BYTES_VERIFIED_SEMANTICS_PENDING':
                        c['biblioteca_erro']=type(e).__name__
                    else:c['aquisicao']={'status':'REJECTED','tipo':type(e).__name__,'motivo':str(e)[:300]}
                if t.http>before:attempts+=1
        lib.exportar_manifesto(out/'manifesto-local.jsonl')
    finally:lib.fechar()
    write(out/'pesquisa.json',{'case':case,'triagem':tri,'pesquisa':reports,'biblioteca_global_disponivel':True,
        'restauracao':rest,'reusos_bytes':reuses,'rede_aquisicao':t.resumo(),'publish':False,
        'semantic_review':'PENDING','pronto_para_render':False})
    if samples:
        board=Image.new('RGB',(1080,len(samples)*370),'#101c28');d=ImageDraw.Draw(board)
        for i,(c,im) in enumerate(samples):
            y=i*370;im.thumbnail((1040,310));board.paste(im,((1080-im.width)//2,y+30))
            d.text((12,y+5),c['tipo']+' | '+c['titulo'][:100],fill='white')
            d.text((12,y+345),'Candidato - '+c['aquisicao']['sha256'][:12]+' - revisao pendente',fill='white')
        board.save(out/'candidatos.jpg',quality=93)
    print('E246 RECOVERY',caseid,'catalogo',rest['registros_db'],'buscas',sum(len(r['buscas']) for r in reports),
          'candidatos',sum(len(r['candidatos']) for r in reports),'bytes',len(samples),'reusos',reuses,'HTTP',t.http,flush=True)
if __name__=='__main__':main()
