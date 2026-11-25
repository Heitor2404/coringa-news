"""E246 resilient private discovery. Evidence acquisition is not rights or semantic approval."""
import hashlib,io,re,sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
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

def nasa_receipt(c,t):
    # The provider returns the collection of actual file variants. No guessed URL.
    import json
    nid=c.get('source_id')
    if not isinstance(nid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',nid):raise ValueError('NASA_ID')
    raw=t.get('https://images-api.nasa.gov/asset/'+nid,{'images-api.nasa.gov'},2_000_000)
    items=json.loads(raw)['collection']['items']
    urls=[];variants_receipt=[]
    for x in items:
        if not isinstance(x,dict) or not isinstance(x.get('href'),str):continue
        u=x['href']
        try:
            p=urlsplit(u)
            if p.hostname!='images-assets.nasa.gov' or p.username or p.password or p.port not in (None,443) or p.scheme not in ('http','https') or not re.search(r'\.(jpg|jpeg|png)$',p.path,re.I):continue
        except ValueError:continue
        # Upgrade legacy provider URLs to HTTPS only for the exact NASA host.
        safe=urlunsplit(('https','images-assets.nasa.gov',p.path,p.query,''))
        variants_receipt.append({'href_declarado':u,'href_https':safe})
        if safe not in urls:urls.append(safe)
    urls.sort(key=lambda u: (0 if '~medium' in u else 1 if '~large' in u else 2 if '~orig' in u else 3,u))
    if not urls:raise ValueError('NASA_SEM_VARIANTE')
    c['recibo_nasa']={'nasa_id':nid,'asset_response_sha256':hashlib.sha256(raw).hexdigest(),'variantes_declaradas':variants_receipt[:30],'credit_declared':c.get('nasa_credit'),'secondary_credit':c.get('nasa_secondary_credit'),'direitos':'PENDENTE_AUDITORIA_INDIVIDUAL'}
    return [{'url':u} for u in urls[:3]]

def sample(c,out,t):
    if c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA':raise ValueError('REPRESENTACAO_NAO_E_REGISTRO')
    if c['fonte']=='nasa' and c['tipo']=='foto':
        choices=nasa_receipt(c,t);hosts={'images-assets.nasa.gov'}
    elif c.get('fonte')=='figshare':
        from src.v4.fontes_cientificas import HOSTS,safe_url
        rec=c.get('recibo_cientifico') or {}
        if c.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or rec.get('provedor')!='figshare' or not safe_url(c['url'],HOSTS):raise ValueError('FIGSHARE_RECIBO')
        choices=[{'url':c['url']}];hosts=HOSTS
    elif c['direitos']=='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA':
        choices=list(variants(c));hosts={'upload.wikimedia.org'}
    else:raise ValueError('PAGINA_PENDENTE')
    cap=26_000_000 if c['tipo']=='foto' else 80_000_000
    failures=[]
    for v in choices[:3]:
        try:
            raw=t.get(v['url'],hosts,cap)
            if c.get('fonte')=='figshare':
                rec=c['recibo_cientifico']
                if len(raw)!=rec.get('bytes') or hashlib.md5(raw).hexdigest()!=rec.get('md5_declarado'):raise ValueError('FIGSHARE_INTEGRIDADE')
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
                if min(w,h)<360 or dur<3:raise ValueError('VIDEO_QUALIDADE')
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
