"""Acquire candidates for explicit visual obligations; review remains pending."""
import sys,shutil
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_documentario_geografia_e219 as E

def main():
    if not all(shutil.which(b) for b in ('ffmpeg','ffprobe')):raise RuntimeError('E300-INFRA-MEDIA-TOOLS')
    spec=E.read(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
    if spec.get('publish') is not False or not 1<=len(spec['candidates'])<=3:raise ValueError('E300-SCOPE')
    E.STAGE=out/'originais';E.STAGE.mkdir()
    records=[]
    for i,c in enumerate(spec['candidates']):
        r={'candidate':c,'status':'REJECTED','semantic_review':'PENDING','publish':False}
        try:
            m=E.acquire((c['slug'],c['label']),min_duration=3.9)
            m['credit']=c['credit']
            r['media']=m
            ww=E.windows(m,3.8,review_technical=True,allow_short=True)[:3]
            r['windows']=[]
            if not ww:raise ValueError('E300-SEM-JANELAS')
            board=Image.new('RGB',(960,220*len(ww)),'#161719')
            d=ImageDraw.Draw(board)
            for row,(t,_) in enumerate(ww):
                samples=[]
                for col,f in enumerate((.12,.5,.86)):
                    time=t+3.8*f
                    im=E.frame(m['local_source'],time,width=320);im.thumbnail((310,175))
                    board.paste(im,(col*320,row*220+25))
                    samples.append(time)
                d.text((8,row*220+5),f'{c["need"]} | {t:.1f}s | CANDIDATO',fill='white')
                r['windows'].append({'start':t,'duration':3.8,'samples_s':samples})
            name=f'candidato-{i}.jpg';board.save(out/name,quality=90)
            r.update(status='BYTES_AND_WINDOWS_VERIFIED',sheet=name)
        except Exception as exc:r['error']=str(exc)[:250]
        records.append(r)
        E.write(out/'coverage.json',{'publish':False,'records':records,'semantic_review':'PENDING'})
    print('E300 ACQUISITION',[(r['candidate']['need'],r['status']) for r in records],flush=True)

if __name__=='__main__':main()
