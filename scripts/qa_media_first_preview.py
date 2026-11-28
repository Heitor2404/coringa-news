"""E230.1: short narrative montage with distinct real sources.
Manual review fixture, not semantic automation or measured narration.
"""
import shutil,subprocess,wave
from pathlib import Path
from scripts import qa_documentario_geografia_e219 as E

def main():
    out=Path('qa_media_first');out.mkdir(exist_ok=True)
    E.STAGE=out/'originais';E.STAGE.mkdir(exist_ok=True)
    spec=E.read('benchmarks/e219/kilauea_2018.json')
    span=4.5
    # Editorial order: hook, fissures, flow, coastline, consequence at summit.
    # One framing for each distinct original, not three views of one take.
    plan=[
        (0,'4:5','O encontro com o mar',['LAVA','E','OCEANO']),
        (2,'imersivo','Fissuras no solo',['O','SOLO','SE','ABRIU']),
        (3,'1:1','Um rio de lava',['UM','RIO','DE','LAVA']),
        (4,'4:5','O litoral mudou',['A','COSTA','MUDOU']),
        (5,'1:1','O topo também mudou',['A','CRATERA','MUDOU']),
    ]
    shots=[];captions=[];media=[];used=set()
    for i,(chapter_index,mode,lead,words) in enumerate(plan):
        chapter=spec['chapters'][chapter_index]
        for row in chapter['videos']:
            try:
                m=E.acquire(row)
                if m['expected_sha256'] in used:raise ValueError('original já usado')
                cuts=E.windows(m,span+.1)
                if not cuts:raise ValueError('sem janela contínua elegível')
                print('AMOSTRA FONTE OK',row[0],flush=True)
                break
            except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as exc:
                print('AMOSTRA FONTE RECUSADA',row[0],type(exc).__name__,str(exc)[:120],flush=True)
        else:
            raise RuntimeError('Sem original distinto elegível: '+chapter['title'])
        used.add(m['expected_sha256'])
        asset='e219_visual/'+m['expected_sha256']+'.mp4'
        dest=E.PUBLIC/asset;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(m['local_source'],dest)
        if E.sha(dest)!=m['expected_sha256']:raise RuntimeError('hash')
        start=i*span;end=start+span
        shot={'id':str(i),'type':'video','asset':asset,'start':start,'end':end,
              'source_in_seconds':cuts[0][0],'headline':m['label'],'lead':lead,
              'subject':m['subject'],'source':m['page'],'source_display':m['credit'],
              'evidence':'literal','video_zoom':1,'focus':[.5,.5]}
        if mode in ('4:5','1:1'):
            # Candidate crops only; no claim of detected/verified ROI.
            shot['video_context_layout']='recorte_relacional_seguro'
            shot['documentary_viewport']=mode
        shots.append(shot)
        captions.append({'start':start,'end':end,'words':[{'w':w,'hl':k==len(words)-1} for k,w in enumerate(words)]})
        media.append({'source':m,'window_s':[cuts[0][0],cuts[0][0]+span],'mode':mode,'review':'PENDING'})
    dur=len(shots)*span
    assert len(used)==len(shots) and 20<=dur<=30
    wav=out/'silencio_lab.wav'
    with wave.open(str(wav),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(bytes(round(dur*48000)*2))
    h=E.sha(wav);audio='e202/'+h+'.wav'
    (E.PUBLIC/'e202').mkdir(exist_ok=True);shutil.copyfile(wav,E.PUBLIC/audio)
    props={'duracao':dur,'shots':shots,'preview':True,'private_review_only':True,'scene_narration_asset':audio,
           'documentary_captions':captions,'documentary_caption_origin':'FRASES_MEDIDAS_LAB'}
    E.write(out/'props.json',props)
    E.write(out/'fontes.json',{'publish':False,'laboratory_silent':True,'semantic_approval':'PENDING',
        'framing':'LAB_MANUAL_NOT_VERIFIED_ROI','sources':media,'distinct_originals':len(used)})
if __name__=='__main__':main()
