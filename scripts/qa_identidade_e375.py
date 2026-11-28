import json,os
from pathlib import Path
from src.v4 import fontes_culturais_e366 as C,fontes_publicas_e354 as F,acervo_v4 as A
from src.v4.aquisicao_documental import Transporte
from src.v4.fontes_contextuais_e359 import pixabay,PIXABAY_MEDIA,pertinencia_stock
from scripts.qa_documentario_geografia_e219 import probe,frame
def main():
    out=Path('stage_documental/e375');out.mkdir(parents=True,exist_ok=True)
    rows=[];t=Transporte(max_http=10,max_bytes=35_000_000,max_wait=18)
    d={}
    for name,q,fn in [('smithsonian','steam locomotive photograph',lambda q:C.smithsonian_identidade(q,transport=t,diagnostico=d)),
                      ('inaturalist','Calypte anna',lambda q:F.inaturalist_identidade(q,transport=t))]:
        row=dict(provider=name,query=q)
        try:
            cs=fn(q);row.update(status='LEADS' if cs else 'EMPTY',count=len(cs),candidates=[dict(title=c['titulo'],page=c['pagina'],hint=c.get('pista_objeto'),receipt=c.get('recibo_fonte'),rank=C.object_rank(q,c) if name=='smithsonian' else None) for c in cs])
            if name=='smithsonian':row['diagnostic']=d
        except Exception as e:row.update(status='ERROR',error=type(e).__name__)
        rows.append(row)
    # One new real contextual query; cache used by the actual director lane.
    q='rain falling window'
    n=dict(id='context',necessidade='registro',evidencia_visual='contexto',preferencia_midia='video_preferencial',
           preferir_imersao_vertical=True,pesquisa={'consultas_en':[q]})
    try:
        report=A.pesquisar_cobertura(n,progressivo=True,max_buscas=2,max_candidatos=4)
        stock=report.get('stock_contextual') or {}
        cs=stock.get('candidatos') or []
        row=dict(provider='pixabay_contexto',query=q,status=stock.get('estado'),searches=report['buscas'],evidence_count=len(report['candidatos']),
            portrait_leads=sum(c['variant']['h']>c['variant']['w'] for c in cs),candidates=[dict(id=c['id'],title=c['title'],page=c['page'],w=c['variant']['w'],h=c['variant']['h'],relevance=pertinencia_stock(q,c)) for c in cs])
        pick=next(((c,v) for c in cs if pertinencia_stock(q,c)>=.6 for v in c['variants'] if v['h']>v['w'] and type(v.get('size')) is int and v['size']<=18_000_000),None)
        if pick and not stock.get('cache_hit'):
            import hashlib,tempfile
            c,v=pick;raw=t.get(v['url'],PIXABAY_MEDIA,18_000_000)
            with tempfile.TemporaryDirectory() as td:
                p=Path(td)/'clip.mp4';p.write_bytes(raw);w,h,dur=probe(p)
                if h<=w or min(w,h)<360 or dur<3:raise ValueError('STOCK_PORTRAIT_DECODE')
                im=frame(p,min(dur/2,3),width=480);im.convert('RGB').save(out/'portrait.jpg',quality=87)
                row.update(status='PORTRAIT_BYTES_VERIFIED_CONTEXT_ONLY',meta=dict(w=w,h=h,duration=dur,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
        rows.append(row)
    except Exception as e:rows.append(dict(provider='pixabay_contexto',status='ERROR',error=type(e).__name__))
    proof=dict(publish=False,semantic_approval=False,new_ai=0,transport=t.resumo(),rows=rows)
    (out/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
    print('E375_PROOF',[(r['provider'],r['status'],r.get('count'),r.get('portrait_leads')) for r in rows])
if __name__=='__main__':main()
