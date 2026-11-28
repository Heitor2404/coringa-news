"""E323: targeted official evidence acquisition for missing causal beats.
Public source receipts only; private archive; no new AI or editorial approval.
"""
import json,hashlib,concurrent.futures
from pathlib import Path
from PIL import Image,ImageDraw
from scripts.qa_documentario_geografia_e219 import acquire,acquire_photo,frame,STAGE,sha
from scripts.qa_replanejamento_e319 import alternatives

SOURCES=[
 ('video','july-5-2018-collapse-event-kilauea-volcanos-summit','Registro de colapso de 5 de julho','c5-1'),
 ('video','kilauea-summit-0','Timelapse documentado de abril a agosto','c5-2'),
 ('video','kilauea-volcano-uas-mission-aid-rescue','Operação de monitoramento e resgate','c2-3'),
 ('photo','schematic-east-west-cross-section-across-kilauea-caldera-2018-2019','Esquema científico de drenagem do reservatório','c5-3'),
 ('photo','agu-chapman-conference-caldera-forming-eruptions-basaltic-volcanoes','Esquema de relação entre erupção e colapso','c5-3'),
]
def main():
    STAGE.mkdir(parents=True,exist_ok=True)
    root=Path('stage_documental/e323');root.mkdir(parents=True,exist_ok=True)
    def one(item):
        i,(kind,slug,label,target)=item
        try:
            m=acquire((slug,label),min_duration=4.) if kind=='video' else acquire_photo((slug,label,'USGS · Hawaiian Volcano Observatory'))
            p=Path(m['local_source']);assert sha(p)==m['expected_sha256']
            m['rights_status']='REVIEW_PENDING';m['target_obligation']=target
            m['local_source']=str(root/p.name);p.replace(m['local_source'])
            p=Path(m['local_source'])
            row={'status':'BYTES_VERIFIED','media':m,'semantic_review':'PENDING'}
            if kind=='photo':
                with Image.open(p) as im:
                    im.thumbnail((1080,1500));im.convert('RGB').save(root/f'fonte-{i:02d}.jpg',quality=92)
                row['sheet']=f'fonte-{i:02d}.jpg'
            else:
                starts=alternatives(m['duration_s'],3.8,[],limit=7)
                if not starts:raise ValueError('E323-SEM-JANELAS')
                board=Image.new('RGB',(960,205*len(starts)),'#191919');draw=ImageDraw.Draw(board);windows=[]
                for k,t in enumerate(starts):
                    samples=[]
                    for j,f in enumerate((.12,.5,.86)):
                        at=t+3.8*f;im=frame(p,at,width=320)
                        samples.append({'time':at,'size':list(im.size),'pixels_sha256':hashlib.sha256(im.tobytes()).hexdigest()})
                        draw.text((j*320+5,k*205+4),f'{at:.2f}s',fill='white')
                        im.thumbnail((320,180));board.paste(im,(j*320,k*205+22))
                    windows.append({'window_start':t,'window_duration':3.8,'samples':samples,'status':'REVIEW_REQUIRED'})
                name=f'fonte-{i:02d}.jpg';board.save(root/name,quality=90)
                row.update(sheet=name,windows=windows)
            return row
        except Exception as e:return {'status':'ACQUISITION_FAILED','source':slug,'target_obligation':target,'error':str(e)[:400]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(one,enumerate(SOURCES)))
    (root/'evidencias.json').write_text(json.dumps({'publish':False,'new_ai':0,'records':rows},ensure_ascii=False,indent=2))
    print('E323_BYTES_VERIFIED',sum(r['status']=='BYTES_VERIFIED' for r in rows),flush=True)
    assert any(r['status']=='BYTES_VERIFIED' for r in rows)
if __name__=='__main__':main()
