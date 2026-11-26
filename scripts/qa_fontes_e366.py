"""One live request to each existing keyed source, private bounded proof."""
import json,os
from pathlib import Path
from src.v4.fontes_contextuais_e359 import pixabay
from src.v4.fontes_culturais_e366 import smithsonian
from src.v4.cache_stock_e365 import CacheStock
from src.v4.aquisicao_documental import Transporte
from src.v4.acervo_v4 import _candidato_documental
from scripts.qa_pesquisa_documental_e246 import sample
from scripts import qa_documentario_geografia_e219 as E
def main():
    out=Path('stage_documental/e366');out.mkdir(parents=True,exist_ok=True)
    originals=out/'originais';originals.mkdir(exist_ok=True)
    cache=CacheStock(os.environ['CORINGA_STOCK_CACHE_DB'])
    t=Transporte(max_http=7,max_bytes=48_000_000,max_wait=18)
    rows=[]
    q='vertical city street'
    try:
        r=pixabay(q,cache=cache);replay=pixabay(q,cache=cache)
        cands=r.get('candidates') or []
        row=dict(provider='pixabay',query=q,status=r['status'],count=len(cands),cache_hit=r.get('cache_hit'),
                 replay_cache_hit=replay.get('cache_hit'),portrait_leads=sum(c['variant']['h']>c['variant']['w'] for c in cands),
                 candidates=[dict(id=c['id'],page=c['page'],author=c['author'],width=c['variant']['w'],height=c['variant']['h']) for c in cands])
        if cands:
            if replay.get('cache_hit') is not True or replay['candidates']!=cands:raise ValueError('STOCK_CACHE_REPLAY')
            # One context clip only; no bulk download, no evidence or permanent media archive.
            pick=None
            for c in cands:
                vs=sorted(c['variants'],key=lambda v:(v['h']<=v['w'],-min(v['w'],v['h'])))
                v=next((v for v in vs if type(v.get('size')) is int and v['size']<=24_000_000),None)
                if v:pick=(c,v);break
            if pick and not r.get('cache_hit') and pick[1]['h']>pick[1]['w']:
                import hashlib
                from src.v4.fontes_contextuais_e359 import PIXABAY_MEDIA
                c,v=pick;raw=t.get(v['url'],PIXABAY_MEDIA,24_000_000)
                p=originals/'pixabay-context.mp4';p.write_bytes(raw)
                w,h,d=E.probe(p)
                if min(w,h)<360 or d<3:raise ValueError('STOCK_DECODE')
                frame=E.frame(p,min(d/2,3),width=640);frame.convert('RGB').save(out/'pixabay-context.jpg',quality=87)
                row.update(status='CONTEXT_BYTES_VERIFIED',source=dict(id=c['id'],page=c['page'],author=c['author'],license_url=c['license_url'],scope='CONTEXTO_APENAS'),
                           meta=dict(width=w,height=h,duration_s=d,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),preview='pixabay-context.jpg')
                p.unlink()
        rows.append(row)
    except Exception as e:rows.append(dict(provider='pixabay',status='ERROR',reason=type(e).__name__))
    try:
        diag={}
        raw=smithsonian('steam locomotive',transport=t,diagnostico=diag)
        cands=[c for x in raw if (c:=_candidato_documental(x,'smithsonian','foto'))]
        row=dict(provider='smithsonian',status='LEADS' if cands else 'EMPTY',count=len(cands),diagnostic=diag,
                 candidates=[dict(title=c['titulo'],page=c['pagina'],credit=c['credito']) for c in cands])
        if cands:
            c=cands[0]
            m,im,p=sample(c,originals,t,progressivo=True,max_variantes=1)
            im.thumbnail((640,640));im.convert('RGB').save(out/'smithsonian-photo.jpg',quality=87)
            row.update(status='BYTES_VERIFIED_SEMANTICS_PENDING',meta=m,receipt=c['recibo_fonte'],preview='smithsonian-photo.jpg')
        rows.append(row)
    except Exception as e:rows.append(dict(provider='smithsonian',status='ERROR',reason=str(e)[:160] if isinstance(e,ValueError) else type(e).__name__))
    (out/'proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,new_ai=0,transport=t.resumo(),rows=rows),ensure_ascii=False,indent=2))
    print('E366_PROOF',[(r['provider'],r['status'],r.get('count'),r.get('portrait_leads')) for r in rows])
if __name__=='__main__':main()
