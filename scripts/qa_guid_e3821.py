"""One metadata query, compare E382 exact phrase; no media acquisition."""
import json
from pathlib import Path
from src.v4 import fontes_culturais_e366 as C
from src.v4.aquisicao_documental import Transporte
def main():
    root=Path('stage_documental/e3821');root.mkdir(parents=True,exist_ok=True)
    t=Transporte(max_http=1,max_bytes=4_000_000,max_wait=8)
    d={};q='steam locomotive'
    try:
        cs=C.smithsonian(q,transport=t,diagnostico=d,phrase=True)
        row=dict(status='LEADS' if cs else 'EMPTY',candidates=[dict(title=c['titulo'],page=c['pagina'],type=c['tipo_objeto_declarado'],hint=c['pista_objeto'],page_field=c['recibo_fonte'].get('page_field'),rank=C.object_rank(q,c)) for c in cs])
    except Exception as e:row=dict(status='ERROR',error=type(e).__name__)
    (root/'proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,metadata_only=True,new_ai=0,query=q,diagnostic=d,transport=t.resumo(),row=row),ensure_ascii=False,indent=2))
    print('E3821',row['status'],d.get('guid_fallback',0),d.get('reasons'))
if __name__=='__main__':main()
