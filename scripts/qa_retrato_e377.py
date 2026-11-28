import json
from pathlib import Path
from src import midia
def main():
    out=Path('stage_documental/e377');out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for q in ('waterfall','train arriving'):
        row=dict(query=q)
        try:
            cs=midia.candidatos_arquivo(q,estrito=True,preferir_vertical=True,pesquisa_retrato=True)
            row.update(status='LEADS' if cs else 'EMPTY',count=len(cs),candidates=[dict(title=c['titulo'],page=c['pagina'],w=c['w'],h=c['h']) for c in cs])
        except Exception as e:row.update(status='ERROR',error=type(e).__name__)
        rows.append(row)
    (out/'proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,metadata_only=True,new_ai=0,rows=rows),ensure_ascii=False,indent=2))
    print('E377_PORTRAIT',[(r['query'],r['status'],r.get('count')) for r in rows])
if __name__=='__main__':main()
