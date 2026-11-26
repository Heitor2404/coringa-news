"""Limited real follow-up, metadata only, no new stock queries or downloads."""
import json
from pathlib import Path
from src.v4.fontes_culturais_e366 import smithsonian,object_rank
from src.v4.fontes_publicas_e354 import inaturalist,usgs
from src.v4.galerias_oficiais_e356 import candidatos
from src.v4.aquisicao_documental import Transporte
def main():
    out=Path('stage_documental/e373');out.mkdir(parents=True,exist_ok=True)
    t=Transporte(max_http=7,max_bytes=15_000_000,max_wait=12);rows=[]
    for name,q,fn in [('smithsonian','steam locomotive photograph',smithsonian),
                      ('inaturalist','hummingbird bird',inaturalist),
                      ('usgs','Kilauea lava',lambda q,transport:usgs(q,'video',transport=transport)),
                      ('noaa','octopus',lambda q,transport:candidatos(q,'noaa','video',transport=transport))]:
        row=dict(provider=name,query=q)
        try:
            cs=fn(q,transport=t)
            row.update(status='LEADS' if cs else 'EMPTY',count=len(cs),candidates=[
                dict(title=c['titulo'],page=c['pagina'],object_types=c.get('tipo_objeto_declarado'),object_hint=c.get('pista_objeto'),
                     title_origin=(c.get('recibo_fonte') or {}).get('title_origin'),object_rank=object_rank(q,c) if name=='smithsonian' else None) for c in cs])
        except Exception as e:row.update(status='ERROR',error=type(e).__name__)
        rows.append(row)
    proof=dict(publish=False,semantic_approval=False,metadata_only=True,new_ai=0,transport=t.resumo(),rows=rows)
    (out/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
    print('E373_RELEVANCE',[(r['provider'],r['status'],r.get('count')) for r in rows])
if __name__=='__main__':main()
