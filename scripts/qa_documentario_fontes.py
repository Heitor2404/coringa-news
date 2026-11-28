"""Preflight of source candidates using the existing USGS acquisition and cut scanner.
No TTS, rendering or claim that a candidate shows the required action.
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
from scripts import qa_documentario_geografia_e219 as E

def main():
    spec=json.loads(Path(sys.argv[1]).read_text())
    out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    if spec.get('publish') is not False:raise ValueError('PRIVATE_ONLY')
    E.STAGE=out/'originais';E.STAGE.mkdir(exist_ok=True)
    records=[];thumbs=[]
    for need in spec['needs']:
        for item in need['sources']:
            row={'need':need['id'],'slug':item['slug'],'role':item['role'],'credit':item['credit'],'note':item['note']}
            try:
                m=E.acquire((item['slug'],item['label']))
                m['credit']=item['credit']
                cuts=E.windows(m,3.8)
                row.update({'status':'BYTES_VERIFIED','media':m,'candidate_offsets':[t for t,_ in cuts],'semantic_review':'PENDING'})
                thumbs.extend((item['slug'],t,im) for t,im in cuts)
            except Exception as e:
                row.update({'status':'REJECTED','error':str(e)[:300]})
            records.append(row)
            print('PREFLIGHT',row['slug'],row['status'],len(row.get('candidate_offsets',[])),flush=True)
    E.write(out/'coverage.json',{'publish':False,'records':records,'needs':{n['id']:sum(r['need']==n['id'] and bool(r.get('candidate_offsets')) for r in records) for n in spec['needs']}})
    if thumbs:
        board=Image.new('RGB',(960,((len(thumbs)+3)//4)*174),'#101c28');draw=ImageDraw.Draw(board)
        for i,(slug,t,im) in enumerate(thumbs):
            im.thumbnail((236,140));x=i%4*240;y=i//4*174
            board.paste(im,(x,y));draw.text((x+3,y+141),slug[:27],fill='white');draw.text((x+3,y+156),str(t)+'s',fill='white')
        board.save(out/'contato.jpg')
if __name__=='__main__':main()
