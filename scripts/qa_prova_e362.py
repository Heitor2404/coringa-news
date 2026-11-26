"""Replay actual E354 leads; prove bytes privately without a new broad search."""
import base64,json,subprocess
from pathlib import Path
from scripts.qa_pesquisa_documental_e246 import sample
from src.v4.aquisicao_documental import Transporte
from src.v4 import fontes_publicas_e354 as F
from src.v4.acervo_v4 import _candidato_documental
def main():
    out=Path('stage_documental/e362');out.mkdir(parents=True,exist_ok=True)
    originals=out/'originais';originals.mkdir(exist_ok=True)
    # Exact immutable private report of the successful original probe.
    api='repos/Heitor2404/coringa-cofre/contents/revisoes/e354-45901292833-1/source-audit.json?ref=b124f00900732c39121afff22cef0b024179328d'
    response=json.loads(subprocess.check_output(['gh','api',api],text=True))
    report=json.loads(base64.b64decode(response['content']))
    t=Transporte(max_http=10,max_bytes=92_000_000,max_wait=25)
    rows=[]
    def probe(provider,kind,candidates):
        r=dict(provider=provider,kind=kind,found=len(candidates),status='NO_CANDIDATE')
        # One original per source; no uncontrolled retries on other items.
        if candidates:
            c=candidates[0]
            r['page']=c['pagina'];r['declared_license']=c.get('licenca');r['declared_credit']=c.get('credito')
            try:
                meta,visual,path=sample(c,originals,t,progressivo=True,max_variantes=1,min_video_px=360)
                visual.thumbnail((640,640));preview=out/(provider+'-'+kind+'.jpg');visual.convert('RGB').save(preview,quality=88)
                r.update(status='BYTES_VERIFIED_SEMANTICS_PENDING',meta=meta,preview=preview.name,rights=c.get('direitos'),source_receipt=c.get('recibo_fonte'),usgs_receipt=c.get('recibo_usgs'))
            except Exception as exc:r.update(status='ERROR',reason=str(exc)[:180])
        rows.append(r)
    for row in report['rows']:
        if row['provider'] in ('openverse','inaturalist'):
            eligible=[c for c in row.get('candidates',[]) if min(c.get('largura_declarada') or 0,c.get('altura_declarada') or 0)>=600]
            probe(row['provider'],row['kind'],eligible)
    try:
        raw=F.usgs('Kilauea lava','video',transport=t)
        candidates=[c for x in raw if (c:=_candidato_documental(x,'usgs_pagina','video'))]
        probe('usgs_pagina','video',candidates)
    except Exception as exc:rows.append(dict(provider='usgs_pagina',kind='video',status='ERROR',reason=str(exc)[:180]))
    (out/'proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,new_ai=0,source_report='e354-45901292833-1',transport=t.resumo(),rows=rows),ensure_ascii=False,indent=2))
    print('E362_PROOF',[(r['provider'],r['status'],r.get('meta',{}).get('bytes')) for r in rows])
if __name__=='__main__':main()
