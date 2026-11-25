"""Private E258 probe of the two formerly disconnected video sources."""
import json,sys
from pathlib import Path
from src.v4 import acervo_v4 as A
from src.v4.aquisicao_documental import Transporte
from scripts.qa_pesquisa_documental_e246 import sample

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    originals=out/'originais';originals.mkdir(exist_ok=True)
    t=Transporte(max_http=20,max_bytes=100_000_000,max_wait=30)
    cases=[('nasa_video','volcano eruption lava'),('archive_video','Apollo 11')]
    rows=[]
    for provider,q in cases:
        n={'id':provider,'necessidade':'registro','evidencia_visual':'movimento',
           'pesquisa':{'consultas_en':[q]}}
        def sources(kind):return [(name,fn) for name,fn in A.fontes_documentais(kind) if name==provider]
        r=A.pesquisar_cobertura(n,fontes=sources,max_buscas=1,max_candidatos=64,progressivo=True)
        for c in r['candidatos']:
            if t.http>=t.max_http or t.bytes>=t.max_bytes:break
            try:
                m,im,p=sample(c,originals,t)
                c['aquisicao']=m
                im.thumbnail((960,960));im.save(out/(provider+'.jpg'),quality=90)
                break
            except Exception as e:c['falha_aquisicao']=str(e)[:300]
        rows.append(r)
    (out/'revisao.json').write_text(json.dumps({'publicar':False,'direitos_aprovados':False,'visao_chamadas':0,
        'rede':t.resumo(),'pesquisas':rows},ensure_ascii=False,indent=2),encoding='utf8')
    print('E258 ACQUISITION',[(r['id'],len(r['candidatos']),sum('aquisicao' in c for c in r['candidatos'])) for r in rows],flush=True)
if __name__=='__main__':main()
