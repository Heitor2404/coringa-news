"""Smithsonian discovery-only follow-up; no source downloads."""
import json
from pathlib import Path
from src.v4 import fontes_culturais_e366 as C
from src.v4.aquisicao_documental import Transporte
def main():
    out=Path('stage_documental/e382');out.mkdir(parents=True,exist_ok=True)
    t=Transporte(max_http=6,max_bytes=16_000_000,max_wait=20)
    rows=[]
    for q in ('steam locomotive photograph','steam engine photograph'):
        d={};row=dict(query=q)
        try:
            cs=C.smithsonian_identidade(q,transport=t,diagnostico=d)
            prom=[c for c in cs if C.object_rank(q,c)[0]==-2 and not C.object_rank(q,c)[1]]
            row.update(status='PROMISING_METADATA_ONLY' if prom else 'GAP_NO_PROMISING_METADATA',count=len(cs),promising=len(prom),candidates=[dict(title=c['titulo'],page=c['pagina'],type=c['tipo_objeto_declarado'],hint=c['pista_objeto'],rank=C.object_rank(q,c)) for c in cs])
        except Exception as e:row.update(status='ERROR',error=type(e).__name__)
        row['diagnostic']=d;rows.append(row)
    (out/'proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,metadata_only=True,new_ai=0,transport=t.resumo(),rows=rows),ensure_ascii=False,indent=2))
    print('E382',[(r['query'],r['status']) for r in rows])
if __name__=='__main__':main()
