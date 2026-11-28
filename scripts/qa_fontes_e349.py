"""Small metadata-only probe of connected sources, no IA or media downloads.
No NASA retry; known origin block is still pending. Counts are leads only."""
import json
from pathlib import Path
from src.v4.acervo_v4 import fontes_documentais
from src.v4.formatos.imersao_documental_e328 import fracao_integral
CASES=[('biology','hummingbird hovering','video','commons_video'),('engineering','hydraulic excavator working','video','commons_video'),('history','early railway steam locomotive','video','archive_video'),('science','cell migration microscopy','video','figshare'),('nature','waterfall','video','commons_video'),('history','industrial revolution steam engine','foto','loc')]
def main():
    rows=[]
    for theme,q,kind,provider in CASES:
        try:
            fn=dict(fontes_documentais(kind,preferir_vertical=True))[provider]
            candidates=fn(q) or []
            dims=[fracao_integral(c.get('w'),c.get('h')) for c in candidates]
            rows.append({'theme':theme,'query':q,'provider':provider,'kind':kind,'status':'LEADS' if candidates else 'EMPTY','count':len(candidates),'portrait_leads':sum(f is not None and f>=.60 and c.get('h',0)>c.get('w',0) for f,c in zip(dims,candidates)),'dimensions_known':sum(f is not None for f in dims),'samples':[{'title':c.get('titulo') or c.get('descricao'),'page':c.get('pagina'),'w':c.get('w'),'h':c.get('h'),'license':c.get('licenca')} for c in candidates[:3]]})
        except Exception as exc:rows.append({'theme':theme,'query':q,'provider':provider,'kind':kind,'status':'ERROR','reason':str(exc)[:200]})
    out=Path('stage_documental/e349');out.mkdir(parents=True,exist_ok=True)
    (out/'source-audit.json').write_text(json.dumps({'publish':False,'metadata_only':True,'semantic_approval':False,'new_ai':0,'records':rows},ensure_ascii=False,indent=2))
    print('E349_SOURCE_AUDIT',[(r['provider'],r['theme'],r['status'],r.get('count'),r.get('portrait_leads')) for r in rows],flush=True)
if __name__=='__main__':main()
