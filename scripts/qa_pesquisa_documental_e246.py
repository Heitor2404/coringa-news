"""E246 private live discovery. Inputs are editorial needs, not selected assets."""
import hashlib,io,sys
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image,ImageDraw
from scripts.qa_documentario_curado_e218 import get,write
from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import diretor_visual_e202 as D
from src.v3.biblioteca import Biblioteca, DB_PADRAO

def sample(c,out):
    # Only individual Commons metadata candidates are eligible for this
    # bounded byte probe. Other legacy providers need source-page receipts.
    if c['direitos']!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA':
        raise ValueError('E246-PAGINA-PENDENTE')
    if urlsplit(c['url']).hostname!='upload.wikimedia.org':
        raise ValueError('E246-HOST')
    cap=26_000_000 if c['tipo']=='foto' else 80_000_000
    if (c.get('tamanho_declarado') or 0)>cap:raise ValueError('E246-LIMITE')
    raw=get(c['url'],{'upload.wikimedia.org'},cap)
    sha=hashlib.sha256(raw).hexdigest()
    if c['tipo']=='foto':
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in ('JPEG','PNG','WEBP') or min(im.size)<600:raise ValueError('E246-PIXELS')
            w,h=im.size;ext={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[im.format]
            visual=im.convert('RGB')
        path=out/(sha+ext);path.write_bytes(raw)
        meta={'width':w,'height':h,'duration_s':None}
    else:
        path=out/(sha+('.webm' if urlsplit(c['url']).path.lower().endswith('.webm') else '.mp4'))
        path.write_bytes(raw)
        w,h,dur=E.probe(path)
        if min(w,h)<360 or dur<3:raise ValueError('E246-VIDEO-QUALIDADE')
        visual=E.frame(path,min(2,dur*.3),width=640)
        meta={'width':w,'height':h,'duration_s':dur}
    return {**meta,'sha256':sha,'bytes':len(raw),'status':'BYTES_VERIFIED_SEMANTICS_PENDING'},visual

def main():
    spec=E.read(sys.argv[1]);out=Path(sys.argv[2]);caseid=sys.argv[3]
    if spec.get('publish') is not False:raise ValueError('PRIVATE_ONLY')
    case=next(c for c in spec['cases'] if c['id']==caseid)
    out.mkdir(parents=True,exist_ok=True);assets=out/'originais';assets.mkdir(exist_ok=True)
    tri=D.triagem_documental(case['necessidades'],case['fatos'])
    lib=Biblioteca() if DB_PADRAO.is_file() else None
    try:reports=D.pesquisar_triagem(tri,biblioteca_global=lib,max_buscas=6)
    finally:
        if lib:lib.fechar()
    samples=[]
    for row in reports:
        attempts=0
        for c in row['candidatos']:
            if c['direitos']!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA':continue
            if attempts>=2:break
            attempts+=1
            try:
                meta,im=sample(c,assets);c['aquisicao']=meta;samples.append((c,im))
            except Exception as e:c['aquisicao']={'status':'REJECTED','tipo':type(e).__name__,'motivo':str(e)[:140]}
    write(out/'pesquisa.json',{'case':case,'triagem':tri,'pesquisa':reports,'biblioteca_global_disponivel':bool(lib),
        'publish':False,'semantic_review':'PENDING','pronto_para_render':False})
    if samples:
        board=Image.new('RGB',(1080,len(samples)*370),'#101c28');d=ImageDraw.Draw(board)
        for i,(c,im) in enumerate(samples):
            y=i*370;im.thumbnail((1040,310));board.paste(im,((1080-im.width)//2,y+30))
            d.text((12,y+5),c['tipo']+' | '+c['titulo'][:100],fill='white')
            d.text((12,y+345),'Candidato - '+c['aquisicao']['sha256'][:12]+' - revisao pendente',fill='white')
        board.save(out/'candidatos.jpg',quality=93)
    print('E246 DISCOVERY',caseid,'buscas',sum(len(r['buscas']) for r in reports),
          'candidatos',sum(len(r['candidatos']) for r in reports),'bytes',len(samples),flush=True)
if __name__=='__main__':main()
