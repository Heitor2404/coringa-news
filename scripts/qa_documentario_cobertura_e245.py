"""Private source coverage probe; no vision calls or motion claims from photographs."""
import sys
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_documentario_geografia_e219 as E

def main():
    spec=E.read(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    if spec.get('publish') is not False:raise ValueError('PRIVATE_ONLY')
    E.STAGE=out/'originais';E.STAGE.mkdir(exist_ok=True)
    records=[];images=[]
    for c in spec['candidates']:
        r={'candidate':c,'status':'PENDING','semantic_review':'PENDING'}
        try:
            if c['type']=='photo':
                m=E.acquire_photo((c['slug'],c['label'],c['credit']))
                with Image.open(m['local_source']) as im:images.append((c,im.convert('RGB')))
            elif c['type']=='video':
                m=E.acquire((c['slug'],c['label']));m['credit']=c['credit']
                # Do not mistake a successful download for correct species.
                r['window_candidates']=[t for t,_ in E.windows(m,3.8,review_technical=True)]
            else:raise ValueError('E245-TIPO')
            if E.sha(Path(m['local_source']))!=m['expected_sha256']:raise ValueError('E245-SHA')
            r.update(status='BYTES_VERIFIED',media=m)
        except Exception as e:r.update(status='REJECTED',error=str(e)[:250])
        records.append(r)
        print('E245 COVERAGE',c['slug'],r['status'],flush=True)
    E.write(out/'coverage.json',{'publish':False,'records':records,'approval':'PENDING'})
    if images:
        board=Image.new('RGB',(1080,len(images)*420),'#101c28');draw=ImageDraw.Draw(board)
        for i,(c,im) in enumerate(images):
            y=i*420;im.thumbnail((1040,370))
            board.paste(im,((1080-im.width)//2,y+30))
            draw.text((12,y+5),c['label']+' | FOTO, NAO PROVA MOVIMENTO',fill='white')
        board.save(out/'fotos.jpg',quality=94)
if __name__=='__main__':main()
