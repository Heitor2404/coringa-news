"""Real bounded metadata-only probes, separate from editorial approval."""
import json
from pathlib import Path
from src.v4 import fontes_publicas_e354 as F
from src.v4.aquisicao_documental import Transporte
from src.v4.acervo_v4 import _candidato_documental
def main():
    cases=[('openverse','foto','hydraulic excavator',F.openverse),('inaturalist','foto','hummingbird',F.inaturalist),
           ('usgs_pagina','video','Kilauea lava',lambda q,transport:F.usgs(q,'video',transport=transport)),
           ('usgs_pagina','foto','Chinook salmon',lambda q,transport:F.usgs(q,'foto',transport=transport))]
    rows=[]
    t=Transporte(max_http=12,max_bytes=12_000_000,max_wait=25)
    for provider,kind,q,fn in cases:
        row=dict(provider=provider,kind=kind,query=q)
        try:
            raw=fn(q,transport=t)
            candidates=[c for item in raw if (c:=_candidato_documental(item,provider,kind))]
            row.update(status='LEADS' if candidates else 'EMPTY',count=len(candidates),candidates=candidates)
        except Exception as exc:row.update(status='ERROR',reason=str(exc)[:160])
        rows.append(row)
    out=Path('stage_documental/e354');out.mkdir(parents=True,exist_ok=True)
    report={'publish':False,'semantic_approval':False,'metadata_only':True,'new_ai':0,'transport':t.resumo(),'rows':rows}
    (out/'source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('E354_SOURCE_AUDIT',[(r['provider'],r['kind'],r['status'],r.get('count')) for r in rows])
if __name__=='__main__':main()
