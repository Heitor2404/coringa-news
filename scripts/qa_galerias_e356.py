import json
from pathlib import Path
from src.v4 import galerias_oficiais_e356 as G
from src.v4.aquisicao_documental import Transporte
def main():
    t=Transporte(max_http=14,max_bytes=20_000_000,max_wait=25)
    rows=[]
    for provider,kind,q in [('noaa','video','octopus'),('nist','foto','antenna'),('nist','video','wildfire')]:
        try:r=G.discover(q,provider,kind,transport=t)
        except Exception as e:r={'status':'ERROR','reason':str(e)[:160]}
        rows.append(dict(provider=provider,kind=kind,query=q,**r))
    # Directed controls independently test the known published item pages.
    for provider,kind,page in [('noaa','video','https://oceanexplorer.noaa.gov/multimedia/okeanos-explorations-seascape-alaska-ex2306-gallery-media-dive08-changingcolors/'),
       ('nist','foto','https://www.nist.gov/image/18ctl003ctlantenna-beam-exp2-jelena-senicinstagramjpg')]:
        try:r=G.receipt(page,provider,kind,transport=t)
        except Exception as e:r={'status':'ERROR','reason':str(e)[:160]}
        rows.append(dict(proof='DIRECTED_CONTROL',**{'provider':provider,'kind':kind,'page':page,**r}))
    out=Path('stage_documental/e356');out.mkdir(parents=True,exist_ok=True)
    (out/'gallery-audit.json').write_text(json.dumps({'publish':False,'semantic_approval':False,'metadata_only':True,'transport':t.resumo(),'rows':rows},indent=2,ensure_ascii=False))
    print('E356_GALLERY_AUDIT',[(r['provider'],r['kind'],r['status']) for r in rows])
if __name__=='__main__':main()
