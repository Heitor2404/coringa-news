"""Private low-byte contact sheets. Provider-declared thumbnails only; never coverage."""
import hashlib,io,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
from src.v4 import acervo_v4 as A
from src.v4.aquisicao_documental import Transporte
from src.v4.formatos import diretor_visual_e202 as D,revisao_documental as R

def candidatos(n,rows,previous_pages=()):
    seen=set(previous_pages);out=[]
    for c in R.ordenar_candidatos(n,rows):
        page=c.get('pagina')
        if not page or page in seen or c.get('tipo')!='foto' or c.get('fonte')!='commons' or c.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA':continue
        seen.add(page)
        if R.incompatibilidade_metadados(n,c):continue
        v=next((v for v in c.get('variantes') or [] if v.get('url') and v['url']!=c.get('url') and all(type(v.get(k)) is int and 240<=v[k]<=2400 for k in ('width','height'))),None)
        if v:out.append((c,v))
    return out

def main():
    spec=json.loads(Path(sys.argv[1]).read_text());previous=json.loads(Path(sys.argv[2]).read_text());root=Path(sys.argv[3]);root.mkdir(parents=True,exist_ok=False)
    if spec.get('publish') is not False or previous.get('publicar') is not False:raise ValueError('E269-PRIVADO')
    case=next(c for c in spec['cases'] if c['id']==sys.argv[4]);tri={n['id']:n for n in D.triagem_documental(case['necessidades'],case['fatos'],progressivo=True)}
    history=json.loads(Path(sys.argv[5]).read_text()) if len(sys.argv)>5 else {'necessidades':[],'publicar':False}
    if history.get('publicar') is not False:raise ValueError('E270-HISTORICO')
    previous_previews={x['id']:x for x in history['necessidades']}
    t=Transporte(max_http=12,max_bytes=9_000_000,max_wait=20);report=[]
    for gap in previous['necessidades']:
        n=tri[gap['id']]
        prior=previous_previews.get(n['id'],{})
        old={x['pagina'] for x in gap['amostras']+prior.get('amostras',[])}
        attempted={(q['tipo'],q['fonte'],q['consulta'].casefold()) for q in prior.get('buscas',[]) if q.get('estado') in ('OK','SEM_NOVOS_CANDIDATOS')}
        discovery=A.pesquisar_cobertura(n,fontes=lambda typ:[x for x in A.fontes_documentais(typ) if x[0]=='commons'],max_buscas=4,max_candidatos=64,progressivo=True,buscas_vistas=attempted)
        choices=candidatos(n,discovery['candidatos'],old);samples=[];errors=[]
        for c,v in choices:
            if R.contexto_de_busca(n,c)[0]:continue
            if len(samples)>=3 or t.http>=t.max_http or t.bytes>=t.max_bytes:break
            try:
                raw=t.get(v['url'],{'upload.wikimedia.org','thumb.wikimedia.org'},1_000_000)
                with Image.open(io.BytesIO(raw)) as img:
                    if img.format not in ('JPEG','PNG','WEBP') or min(img.size)<240:raise ValueError('PREVIEW_PIXELS')
                    im=img.convert('RGB')
                digest=hashlib.sha256(raw).hexdigest();im.thumbnail((900,620))
                board=Image.new('RGB',(960,680),'#101c28');ImageDraw.Draw(board).text((12,8),n['id']+' '+digest[:12]+' MINIATURA - NAO APROVADA',fill='white')
                board.paste(im,((960-im.width)//2,35));name=n['id']+'-'+str(len(samples)+1)+'.jpg';board.save(root/name,quality=90)
                samples.append({'pagina':c['pagina'],'titulo':c['titulo'],'source_id':c['source_id'],'preview_url':v['url'],'preview_sha256':digest,'folha':name,'componentes':R.cobertura_componentes(n,c),'estado':'PRETRIAGEM_PENDENTE','publicar':False})
            except Exception as e:errors.append({'pagina':c['pagina'],'motivo':str(e)[:180]})
        report.append({'id':n['id'],'buscas':discovery['buscas'],'amostras':samples,'erros':errors})
    out={'publicar':False,'direitos_aprovados':False,'visao':0,'cobertura_nova':0,'rede':t.resumo(),'necessidades':report}
    (root/'pretriagem.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print('E269 PRETRIAGEM',[(r['id'],len(r['amostras'])) for r in report],t.http,t.bytes,flush=True)
if __name__=='__main__':main()
