import json
from pathlib import Path
from src.v4.descoberta_paralela_e363 import rotas_publicas,onda
from src.v4.aquisicao_documental import Transporte
from scripts.qa_pesquisa_documental_e246 import usgs_receipt

def main():
    out=Path('stage_documental/e363');out.mkdir(parents=True,exist_ok=True)
    routes=dict(rotas_publicas('video'))
    tasks=[(routes['usgs_pagina'],'volcanic lava fountaining'),(routes['noaa_pagina'],'octopus')]
    results=onda(tasks)
    rows=[]
    for (route,q),r in zip(tasks,results):
        rows.append(dict(origin=route.origem,query=q,count=len(r['raw']),error=r['error'],network=r['rede'],
                         pages=[c.get('pagina') for c in r['raw']]))
    overlap=max(0,min(x['fim_monotonic'] for x in results)-max(x['inicio_monotonic'] for x in results))
    page='https://www.usgs.gov/media/videos/july-15-2026-timelapse-video-kilauea-episode-51-lava-fountaining-v2cam'
    c=dict(pagina=page,tipo='video',credito='',recibo_fonte={'credit_pending':True})
    t=Transporte(max_http=2,max_bytes=5_000_000,max_wait=8)
    try:
        usgs_receipt(c,t)
        byline=dict(status='PAGE_VERIFIED',credit=c['credito'],receipt=c['recibo_usgs'],network=t.resumo())
    except Exception as exc:byline=dict(status='ERROR',reason=str(exc)[:150],network=t.resumo())
    proof=dict(publish=False,semantic_approval=False,metadata_only=True,rows=rows,overlap_s=round(overlap,4),
        http=sum(r['network']['http'] for r in rows),bytes=sum(r['network']['bytes'] for r in rows),byline=byline)
    (out/'wave.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
    print('E363_WAVE',[(r['origin'],r['count'],r['error']) for r in rows],proof['http'],proof['bytes'],proof['overlap_s'],byline['status'])
if __name__=='__main__':main()
