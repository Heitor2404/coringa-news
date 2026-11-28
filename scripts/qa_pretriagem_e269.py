"""Private low-byte contact sheets. Provider-declared thumbnails only; never coverage."""
import hashlib,io,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
from src.v4 import acervo_v4 as A
from src import acervo
from src.v4.aquisicao_documental import Transporte
from src.v4.formatos import diretor_visual_e202 as D,revisao_documental as R

from src.v4.pretriagem_documental import candidatos,coletar_fila

def main():
    spec=json.loads(Path(sys.argv[1]).read_text());previous=json.loads(Path(sys.argv[2]).read_text());root=Path(sys.argv[3]);root.mkdir(parents=True,exist_ok=False)
    if spec.get('publish') is not False or previous.get('publicar') is not False:raise ValueError('E269-PRIVADO')
    case=next(c for c in spec['cases'] if c['id']==sys.argv[4]);tri={n['id']:n for n in D.triagem_documental(case['necessidades'],case['fatos'],progressivo=True)}
    history=json.loads(Path(sys.argv[5]).read_text()) if len(sys.argv)>5 else {'necessidades':[],'publicar':False}
    if history.get('publicar') is not False:raise ValueError('E270-HISTORICO')
    previous_previews={x['id']:x for x in history['necessidades']}
    t=Transporte(max_http=12,max_bytes=9_000_000,max_wait=20);queues=[];discoveries={}
    for gap in previous['necessidades']:
        n=tri[gap['id']]
        prior=previous_previews.get(n['id'],{})
        old={x['pagina'] for x in gap['amostras']+prior.get('amostras',[])}
        attempted={(q['tipo'],q['fonte'],q['consulta'].casefold()) for q in prior.get('buscas',[]) if q.get('estado') in ('OK','SEM_NOVOS_CANDIDATOS')}
        discovery=A.pesquisar_cobertura(n,fontes=lambda typ:[('commons',lambda q:acervo.f_commons_documental(q,preview_width=640))] if typ=='foto' else [],max_buscas=4,max_candidatos=64,progressivo=True,buscas_vistas=attempted)
        choices=[(c,v) for c,v in candidatos(n,discovery['candidatos'],old) if not R.contexto_de_busca(n,c)[0]]
        queues.append((n,choices));discoveries[n['id']]=discovery['buscas']
    def board(n,c,v,im,digest,index):
        im.thumbnail((900,620))
        canvas=Image.new('RGB',(960,680),'#101c28');ImageDraw.Draw(canvas).text((12,8),n['id']+' '+digest[:12]+' MINIATURA - NAO APROVADA',fill='white')
        canvas.paste(im,((960-im.width)//2,35));name=n['id']+'-'+str(index)+'.jpg';canvas.save(root/name,quality=90)
        return {'pagina':c['pagina'],'titulo':c['titulo'],'source_id':c['source_id'],'consulta_origem':c.get('consulta_origem'),'preview_url':v['url'],'preview_sha256':digest,'folha':name,'componentes':R.cobertura_componentes(n,c),'componentes_declarados':bool(n.get('pesquisa',{}).get('componentes_busca')),'estado':'PRETRIAGEM_PENDENTE','publicar':False}
    report=coletar_fila(queues,t,board)
    for row in report:row['buscas']=discoveries[row['id']]
    out={'publicar':False,'direitos_aprovados':False,'visao':0,'cobertura_nova':0,'rede':t.resumo(),'necessidades':report}
    (root/'pretriagem.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print('E269 PRETRIAGEM',[(r['id'],len(r['amostras'])) for r in report],t.http,t.bytes,flush=True)
if __name__=='__main__':main()
