"""E286 private composition check using actual versioned image/video fixtures.
Silent caption-lane samples are layout probes, not a narrated documentary.
No acquisition, no external AI, no new rights claims.
"""
import hashlib,json,shutil,subprocess,wave
from pathlib import Path
from PIL import Image

def main():
    root=Path('stage_documental/e286');root.mkdir(parents=True,exist_ok=True)
    pub=Path('motor4/remotion/public');assets=pub/'e286';assets.mkdir(parents=True,exist_ok=True)
    rows=[
        ('video_horizontal_navio','.mp4','video','CANAL DO PANAMÁ','Navio em trânsito'),
        ('foto_vertical_salto_angel','.jpg','photo','SALTO ÁNGEL','Vista vertical'),
        ('foto_horizontal_roraima','.jpg','photo','MONTE RORAIMA','Vista panorâmica'),
        ('video_vertical_nasa','.mp4','video','REGISTRO NASA','Filmagem vertical'),
    ]
    shots=[];captions=[];receipts=[]
    for i,(name,ext,kind,lead,label) in enumerate(rows):
        src=Path('tests/midia')/(name+ext);meta=json.loads(src.with_suffix('.json').read_text())
        sha=hashlib.sha256(src.read_bytes()).hexdigest();dst=assets/(sha+ext);shutil.copyfile(src,dst)
        if kind=='photo':
            with Image.open(src) as im:w,h=im.size
        else:
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height:format=duration','-of','json',str(src)]))
            w,h=probe['streams'][0]['width'],probe['streams'][0]['height']
            assert float(probe['format']['duration'])>=3
        credit=' · '.join(str(meta.get(k)) for k in ('autor','licenca') if meta.get(k))
        s={'id':name,'type':kind,'asset':'e286/'+dst.name,'start':i*3,'end':(i+1)*3,'source_dimensions':[w,h],
            'lead':lead,'headline':label,'subject':label,'source':credit,'source_display':credit,
            'evidence':'representative','focus':[.5,.5]}
        if kind=='photo':s['photo_framing']='integral'
        else:s.update(video_context_layout='cena_integral',source_in_seconds=0,video_zoom=1)
        shots.append(s);captions.append({'start':i*3+.3,'end':(i+1)*3-.2,'words':[{'w':x,'hl':j==0} for j,x in enumerate(label.upper().split())]})
        receipts.append({'id':name,'sha256':sha,'dimensions':[w,h],'source':meta})
    audio=root/'layout-silence.wav'
    with wave.open(str(audio),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(bytes(12*48000*2))
    name='e202/'+hashlib.sha256(audio.read_bytes()).hexdigest()+'.wav'
    (pub/'e202').mkdir(exist_ok=True);shutil.copyfile(audio,pub/name)
    p={'duracao':12,'shots':shots,'preview':True,'private_review_only':True,'documentary_media_preview':True,
       'scene_narration_asset':name,'documentary_captions':captions,'documentary_caption_origin':'FRASES_MEDIDAS_LAB'}
    (root/'props.json').write_text(json.dumps(p,ensure_ascii=False))
    (root/'prova.json').write_text(json.dumps({'publish':False,'visual_approval':'PENDING','kind':'LAYOUT_PROBE','narration':False,
        'caption_timing':'synthetic layout only','duration':12,'source_receipts':receipts},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
