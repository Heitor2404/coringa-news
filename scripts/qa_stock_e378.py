"""Replay cached request only; one distinct non-synthetic portrait if eligible."""
import json,tempfile,hashlib,os
from pathlib import Path
from src.v4 import fontes_contextuais_e359 as S
from src.v4.aquisicao_documental import Transporte
from scripts.qa_documentario_geografia_e219 import probe,frame
def main():
    out=Path('stage_documental/e378');out.mkdir(parents=True,exist_ok=True)
    q='rain falling window';row={'status':'CACHE_NOT_AVAILABLE','query':q}
    t=Transporte(max_http=2,max_bytes=18_000_000,max_wait=8)
    # Never refresh an expired/missing query in this replay.
    from src.v4.cache_stock_e365 import CacheStock
    class Replay(CacheStock):
        def fetch(self,provider,request,load):
            def unavailable():raise ValueError('CACHE_MISS_NO_REQUEST')
            return super().fetch(provider,request,unavailable)
    try:
        r=S.pixabay(q,cache=Replay(os.environ['CORINGA_STOCK_CACHE_DB']))
        cs=r['candidates'];row.update(status=r['status'],cache_hit=r['cache_hit'],filtered=r.get('declared_synthetic_filtered'),candidates=[dict(id=c['id'],title=c['title'],page=c['page'],w=c['variant']['w'],h=c['variant']['h']) for c in cs])
        pick=next(((c,v) for c in cs if c['id']!='281793' and S.pertinencia_stock(q,c)>=.6 for v in c['variants'] if v['h']>v['w'] and type(v.get('size')) is int and v['size']<=18_000_000),None)
        if pick:
            c,v=pick;raw=t.get(v['url'],S.PIXABAY_MEDIA,18_000_000)
            with tempfile.TemporaryDirectory() as td:
                p=Path(td)/'clip.mp4';p.write_bytes(raw);w,h,dur=probe(p)
                if h<=w or min(w,h)<360 or dur<3:raise ValueError('PORTRAIT_DECODE')
                frame(p,min(dur/2,3),width=480).convert('RGB').save(out/'portrait.jpg',quality=87)
                row.update(status='PORTRAIT_BYTES_VERIFIED_CONTEXT_ONLY',meta=dict(w=w,h=h,duration=dur,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),source=dict(id=c['id'],page=c['page'],author=c['author'],license_url=c['license_url']))
    except Exception as e:row.update(error=type(e).__name__)
    (out/'proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,new_ai=0,row=row,transport=t.resumo()),ensure_ascii=False,indent=2))
    print('E378_STOCK',row['status'],row.get('filtered'),row.get('error'))
if __name__=='__main__':main()
