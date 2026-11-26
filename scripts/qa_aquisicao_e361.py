"""Private real byte/decoder proof for known gallery controls, not topic approval."""
import json
from pathlib import Path
from src.v4.aquisicao_documental import Transporte
from scripts.qa_pesquisa_documental_e246 import sample
def main():
    out=Path('stage_documental/e361');out.mkdir(parents=True,exist_ok=True)
    originals=out/'originais';originals.mkdir(exist_ok=True)
    t=Transporte(max_http=9,max_bytes=85_000_000,max_wait=25)
    rows=[]
    for provider,kind,page in [('noaa_pagina','video','https://oceanexplorer.noaa.gov/multimedia/okeanos-explorations-seascape-alaska-ex2306-gallery-media-dive08-changingcolors/'),
        ('nist_pagina','foto','https://www.nist.gov/image/18ctl003ctlantenna-beam-exp2-jelena-senicinstagramjpg')]:
        c=dict(fonte=provider,tipo=kind,pagina=page,url=page,source_id=page,titulo=page.rsplit('/',1)[-1],direitos='REVISAR_PAGINA_INDIVIDUAL',publicar=False)
        row=dict(provider=provider,kind=kind,page=page)
        try:
            meta,visual,path=sample(c,originals,t,progressivo=True,max_variantes=1,min_video_px=360)
            visual.thumbnail((640,640))
            preview=out/(provider+'.jpg');visual.convert('RGB').save(preview,quality=88)
            row.update(status='BYTES_VERIFIED_SEMANTICS_PENDING',meta=meta,receipt=c.get('recibo_galeria'),preview=preview.name)
        except Exception as e:row.update(status='ERROR',reason=str(e)[:180])
        rows.append(row)
    (out/'acquisition.json').write_text(json.dumps({'publish':False,'semantic_approval':False,'new_ai':0,'transport':t.resumo(),'rows':rows},ensure_ascii=False,indent=2))
    print('E361_ACQUISITION',[(r['provider'],r['status'],r.get('meta',{}).get('bytes')) for r in rows])
if __name__=='__main__':main()
