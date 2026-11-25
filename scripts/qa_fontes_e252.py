"""E252: real scientific-source discovery and bounded acquisition, no AI."""
import json,sys
from pathlib import Path
from src.v4 import fontes_cientificas as F,acervo_v4 as A
from src.v4.aquisicao_documental import Transporte
from scripts.qa_pesquisa_documental_e246 import sample

def main():
    root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=True)
    originals=root/'originais';originals.mkdir(exist_ok=True)
    t=Transporte(max_http=8,max_bytes=40_000_000,max_wait=20)
    cases=[('biologia','octopus camouflage','video'),
           ('fisica','droplet impact','video'),
           ('geologia','glacier crevasse','foto')]
    rows=[]
    for case,q,kind in cases:
        row={'tema':case,'consulta':q,'tipo':kind,'candidatos':[]}
        try:
            row['candidatos']=[c for x in F.candidatos(q,kind) if (c:=A._candidato_documental(x,'figshare',kind))]
            for c in row['candidatos'][:2]:
                try:
                    m,im,p=sample(c,originals,t);c['aquisicao']=m
                    im.thumbnail((960,960));im.save(root/(case+'.jpg'),quality=90)
                    break
                except Exception as e:c['erro_aquisicao']=str(e)[:250]
        except Exception as e:row['erro']=type(e).__name__+':'+str(e)[:160]
        rows.append(row)
    (root/'revisao.json').write_text(json.dumps({'publicar':False,'direitos_aprovados':False,
        'pronto_para_render':False,'casos':rows,'rede_aquisicao':t.resumo(),'visao_chamadas':0},ensure_ascii=False,indent=2),encoding='utf8')
    print('E252 candidatos',sum(len(r['candidatos']) for r in rows),'adquiridos',sum('aquisicao' in c for r in rows for c in r['candidatos']))
if __name__=='__main__':main()
