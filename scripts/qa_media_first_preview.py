"""Short visual-only comparison of real USGS footage, no TTS or new documentary.
The same native footage is deliberately repeated for crop vs full-context review.
"""
import hashlib,json,shutil,subprocess,wave
from pathlib import Path
from scripts import qa_documentario_geografia_e219 as E

def main():
    out=Path('qa_media_first');out.mkdir(exist_ok=True)
    E.STAGE=out/'originais';E.STAGE.mkdir(exist_ok=True)
    spec=E.read('benchmarks/e219/kilauea_2018.json')
    media=[]
    for chapter in (spec['chapters'][0],spec['chapters'][2]):
        # A failed original must not end the whole sample while another
        # licensed candidate for the SAME chapter can satisfy the same gate.
        for row in chapter['videos']:
            try:
                m=E.acquire(row)
                cuts=E.windows(m,3.1)
                if not cuts:raise RuntimeError('sem trecho de teste')
                print('AMOSTRA FONTE OK',row[0],flush=True)
                break
            except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as exc:
                print('AMOSTRA FONTE RECUSADA',row[0],type(exc).__name__,str(exc)[:120],flush=True)
        else:
            raise RuntimeError('Sem registro elegível para a amostra: '+chapter['title'])
        asset='e219_visual/'+m['expected_sha256']+'.mp4'
        dest=E.PUBLIC/asset;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(m['local_source'],dest)
        if E.sha(dest)!=m['expected_sha256']:raise RuntimeError('hash')
        media.append((m,asset,cuts[0][0]))
    shots=[]
    captions=[]
    for i,(j,integral,words) in enumerate([(0,False,['LAVA','NO','OCEANO']),(0,True,['CONTEXTO','DA','COSTA']),(1,False,['FISSURAS','EM','ATIVIDADE'])]):
        m,asset,offset=media[j];start=i*3
        shot={'id':str(i),'type':'video','asset':asset,'start':start,'end':start+3,'source_in_seconds':offset,
              'headline':m['label'],'lead':'Enquadramento integral' if integral else 'Enquadramento imersivo',
              'subject':m['subject'],'source':m['page'],'source_display':m['credit'],'evidence':'literal','video_zoom':1,'focus':[.5,.5]}
        if integral:shot['video_context_layout']='cena_integral'
        shots.append(shot)
        captions.append({'start':start,'end':start+3,'words':[{'w':w,'hl':k==0} for k,w in enumerate(words)]})
    # Silent laboratory asset only: captions demonstrate typography, not sync.
    wav=out/'silencio_lab.wav'
    with wave.open(str(wav),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(bytes(9*48000*2))
    h=E.sha(wav);audio='e202/'+h+'.wav'
    (E.PUBLIC/'e202').mkdir(exist_ok=True);shutil.copyfile(wav,E.PUBLIC/audio)
    props={'duracao':9,'shots':shots,'preview':True,'private_review_only':True,'scene_narration_asset':audio,
           'documentary_captions':captions,'documentary_caption_origin':'FRASES_MEDIDAS_LAB'}
    E.write(out/'props.json',props)
    E.write(out/'fontes.json',{'publish':False,'laboratory_silent':True,'semantic_approval':'PENDING','sources':[m for m,_,_ in media]})
if __name__=='__main__':main()
