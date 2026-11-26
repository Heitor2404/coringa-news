"""Corrective probes: one new portrait text search, filtered museum search."""
import hashlib,json,os
from pathlib import Path
from src.v4.fontes_contextuais_e359 import pixabay,PIXABAY_MEDIA
from src.v4.fontes_culturais_e366 import smithsonian
from src.v4.cache_stock_e365 import CacheStock
from src.v4.acervo_v4 import _candidato_documental
from src.v4.aquisicao_documental import Transporte
from scripts.qa_pesquisa_documental_e246 import sample
from scripts import qa_documentario_geografia_e219 as E
def main():
    out=Path('stage_documental/e368');out.mkdir(parents=True,exist_ok=True)
    originals=out/'originais';originals.mkdir(exist_ok=True)
    cache=CacheStock(os.environ['CORINGA_STOCK_CACHE_DB'])
    t=Transporte(max_http=7,max_bytes=48_000_000,max_wait=18);rows=[]
    try:
        q='vertical city street pedestrian'
        r=pixabay(q,cache=cache)
        cs=r.get('candidates') or [];portraits=[c for c in cs if c['variant']['h']>c['variant']['w']]
        row=dict(provider='pixabay',query=q,status=r['status'],count=len(cs),portrait_leads=len(portraits),
                 candidates=[dict(id=c['id'],page=c['page'],author=c['author'],title=c['title'],width=c['variant']['w'],height=c['variant']['h']) for c in cs],cache_hit=r.get('cache_hit'))
        # Prove only a native portrait if one is actually returned.
        pick=None
        for c in portraits:
            v=next((v for v in sorted(c['variants'],key=lambda x:-min(x['w'],x['h'])) if v['h']>v['w'] and type(v.get('size')) is int and v['size']<=24_000_000),None)
            if v:pick=(c,v);break
        if pick:
            c,v=pick;raw=t.get(v['url'],PIXABAY_MEDIA,24_000_000)
            p=originals/'portrait.mp4';p.write_bytes(raw)
            w,h,d=E.probe(p)
            if not h>w or min(w,h)<360 or d<3:raise ValueError('PORTRAIT_DECODE')
            E.frame(p,min(3,d/2),width=640).convert('RGB').save(out/'pixabay-portrait.jpg',quality=87)
            row.update(status='PORTRAIT_CONTEXT_BYTES_VERIFIED',meta=dict(width=w,height=h,duration_s=d,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),
                       source=dict(id=c['id'],page=c['page'],author=c['author'],scope='CONTEXTO_APENAS',license_url=c['license_url']),preview='pixabay-portrait.jpg')
            p.unlink()
        rows.append(row)
    except Exception as e:rows.append(dict(provider='pixabay',status='ERROR',reason=type(e).__name__))
    for q in ('steam locomotive','Wright Flyer'):
        try:
            diag={};raw=smithsonian(q,transport=t,diagnostico=diag)
            candidates=[c for x in raw if (c:=_candidato_documental(x,'smithsonian','foto'))]
            row=dict(provider='smithsonian',query=q,status='LEADS' if candidates else 'EMPTY',count=len(candidates),diagnostico=diag,
                     candidates=[dict(title=c['titulo'],page=c['pagina'],credit=c['credito']) for c in candidates])
            if candidates:
                c=candidates[0];m,im,p=sample(c,originals,t,progressivo=True,max_variantes=1)
                im.thumbnail((640,640));im.convert('RGB').save(out/'smithsonian-photo.jpg',quality=87)
                row.update(status='BYTES_VERIFIED_SEMANTICS_PENDING',meta=m,receipt=c['recibo_fonte'],preview='smithsonian-photo.jpg')
            rows.append(row)
            if candidates:break
        except Exception as e:rows.append(dict(provider='smithsonian',query=q,status='ERROR',reason=type(e).__name__))
    (out/'proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,new_ai=0,transport=t.resumo(),rows=rows),ensure_ascii=False,indent=2))
    print('E368_PROOF',[(r['provider'],r['status'],r.get('count'),r.get('portrait_leads')) for r in rows])
if __name__=='__main__':main()
