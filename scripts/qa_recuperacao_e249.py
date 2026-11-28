"""Private targeted regression of E248 acquisition failures; no vision/TTS."""
import json,sys
from pathlib import Path
from scripts.qa_pesquisa_documental_e246 import sample
from src.v4.aquisicao_documental import Transporte
from src.v4 import acervo_v4 as A

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    originals=out/'originais';originals.mkdir(exist_ok=True)
    t=Transporte(max_http=10,max_bytes=60_000_000,max_wait=20)
    rows=[]
    # IDs observed in the prior E248 report, not new thematic templates.
    for nid in ('PIA06538','PIA12639'):
        c={'source_id':nid,'fonte':'nasa','tipo':'foto'}
        try:
            m,im,p=sample(c,originals,t)
            c['aquisicao']=m
            im.thumbnail((960,960));im.save(out/(nid+'.jpg'),quality=90)
        except Exception as e:c['erro']=str(e)[:300]
        rows.append(c)
    n={'id':'n1','necessidade':'registro','evidencia_visual':'movimento',
       'pesquisa':{'consultas_en':['octopus camouflage color','octopus changing skin']}}
    discovery=A.pesquisar_cobertura(n,max_buscas=4)
    (out/'revisao.json').write_text(json.dumps({'publish':False,'pronto_para_render':False,
        'nasa':rows,'descoberta':discovery,'rede':t.resumo(),'visao_chamadas':0},ensure_ascii=False,indent=2),encoding='utf8')
    print('E249 NASA',sum('aquisicao' in c for c in rows),'candidatos alternativos',len(discovery['candidatos']))
if __name__=='__main__':main()
