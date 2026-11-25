"""Bounded real acquisition proof; no semantic review or narration."""
import json,sys
from pathlib import Path
from src.v4.aquisicao_documental import Transporte
from src.v4.formatos import ponte_cobertura_filme as P
from scripts.qa_pesquisa_documental_e246 import candidato_pagina_usgs,sample

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    rows=[
        {'necessidade_id':'geologia','tipo':'video','pagina':'https://www.usgs.gov/media/videos/kilauea-volcano-overflight-fissure-20-complex','credito':'USGS · Hawaiian Volcano Observatory'},
        {'necessidade_id':'biologia','tipo':'foto','pagina':'https://www.usgs.gov/media/images/chinook-salmon-fry','credito':'Roger Tabor · U.S. Fish and Wildlife Service'}]
    t=Transporte(max_http=8,max_bytes=100_000_000,max_wait=20)
    results=[]
    for row in rows:
        n={'id':row['necessidade_id'],'evidencia_visual':'movimento' if row['tipo']=='video' else 'estatica'}
        c=candidato_pagina_usgs(row,n)
        try:
            a,im,p=sample(c,out,t,progressivo=True,min_video_px=700)
            c['aquisicao']=a
            c['compatibilidade_ponte']=P.licenca_documental(c,a) is not None
            if not c['compatibilidade_ponte']:raise ValueError('E263-RECIBO-PONTE')
            im.thumbnail((960,960));im.save(out/(n['id']+'.jpg'),quality=90)
        except Exception as e:c['falha']=str(e)[:300]
        results.append(c)
    (out/'prova.json').write_text(json.dumps({'publicar':False,'direitos_aprovados':False,'visao':0,
        'resultados':results,'rede':t.resumo()},ensure_ascii=False,indent=2))
    print('E263 PAGES',[(c['source_id'],c.get('compatibilidade_ponte'),c.get('falha')) for c in results],flush=True)
if __name__=='__main__':main()
