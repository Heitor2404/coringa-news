"""E388.2: deliver only changed diagnostic frames, never duplicate prior videos."""
import hashlib,json
from pathlib import Path
from src.v3 import previa_telegram as T
ROOT=Path('stage_documental/e3882')
PRIOR={
'motion-c3-2-before.png':'017b266029d9cf445afcfd9da907d92ae6f0a3d3a496f28090c05af2f094daef',
'motion-c3-2.png':'2395e32347f1260d8599ef3db6d442a6e71c1a8bba381c3f745e1dbc4d9bbd0c',
'motion-c6-1-before.png':'5512da8fd978a34ac0844af94b167ba7bc40d1544025baca437815064548482a',
'motion-c6-1.png':'1c750f75c191f44fe1681eef6773403abf22109406185c0e46097dedce6ac344'}
def main():
    if not ROOT.exists():raise RuntimeError('E3882 NO OUTPUT')
    out=[];path=ROOT/'delivery.json'
    def save(complete=False):path.write_text(json.dumps(dict(publish=False,prior_run=45920278987,qa_retry_of=45920829388,prior_video_messages=[580,581],items=out,complete=complete),indent=2))
    try:
        for f in sorted(ROOT.glob('motion-*.png')):
            h=hashlib.sha256(f.read_bytes()).hexdigest()
            row=dict(file=f.name,sha256=h)
            if PRIOR.get(f.name)==h:row['status']='ALREADY_DELIVERED_IDENTICAL'
            else:
                chat,_=T.chat_autorizado()
                r=T._api('sendDocument',{'chat_id':chat,'caption':'E388.2 · '+f.stem+' · diagnóstico de medição · revisão privada'},('document',f))
                if not isinstance(r,dict) or not r.get('message_id'):raise RuntimeError('RECEIPT')
                row.update(status='DELIVERED',message_id=r['message_id'])
            out.append(row);save()
        save(len(out)==5)
        if len(out)!=5:raise RuntimeError('MISSING FRAMES')
    except Exception:
        save();raise RuntimeError('E3882 DELIVERY INCOMPLETE') from None
if __name__=='__main__':main()
