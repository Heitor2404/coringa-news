import json
from pathlib import Path
from src.v4.fontes_culturais_e366 import smithsonian
from src.v4.acervo_v4 import _candidato_documental
from src.v4.aquisicao_documental import Transporte
from scripts.qa_pesquisa_documental_e246 import sample
def main():
    out=Path('stage_documental/e369');out.mkdir(parents=True,exist_ok=True)
    t=Transporte(max_http=5,max_bytes=30_000_000,max_wait=12);diag={};row={}
    try:
        raw=smithsonian('steam locomotive',transport=t,diagnostico=diag)
        cs=[c for x in raw if (c:=_candidato_documental(x,'smithsonian','foto'))]
        row=dict(status='LEADS' if cs else 'EMPTY',count=len(cs),diagnostic=diag,
                 candidates=[dict(title=c['titulo'],page=c['pagina'],credit=c['credito']) for c in cs])
        if cs:
            c=cs[0]
            try:
                m,im,p=sample(c,out,t,progressivo=True,max_variantes=1)
                im.thumbnail((640,640));im.convert('RGB').save(out/'smithsonian.jpg',quality=88)
                row.update(status='BYTES_VERIFIED_SEMANTICS_PENDING',meta=m,receipt=c['recibo_fonte'])
                p.unlink()
            except Exception as e:row.update(status='ACQUISITION_FAILED',error=type(e).__name__)
    except Exception as e:row=dict(status='SEARCH_FAILED',error=type(e).__name__,diagnostic=diag)
    proof=dict(publish=False,semantic_approval=False,new_ai=0,transport=t.resumo(),row=row)
    (out/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
    print('E369_SMITHSONIAN',row['status'],row.get('count'),[(e['status'],e.get('redirect_host')) for e in proof['transport']['eventos']])
if __name__=='__main__':main()
