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
    tech={'title':'Tecnologia de campo','credit':'USGS · ciência e tecnologia',
          'videos':[['using-drones-study-rivers-above','Pesquisa de rios com drones'],
                    ['usgs-road-remotely-sampling-a-stream-contaminants','Amostragem remota'],
                    ['usgs-sediment-core-laboratory-ad','Laboratório de sedimentos']]}
    history={'title':'Acervo histórico','credit':'USGS · EROS',
             'videos':[['outreach-eros-overview','Acervo e observação terrestre']]}
    for chapter in (spec['chapters'][0],spec['chapters'][2],tech,history):
        # A failed original must not end the whole sample while another
        # licensed candidate for the SAME chapter can satisfy the same gate.
        for row in chapter['videos']:
            try:
                m=E.acquire(row)
                if chapter.get('credit'):m['credit']=chapter['credit']
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
    variants=[
        (0,'imersivo',['LAVA','NO','OCEANO']),
        (0,'4:5',['RECORTE','INTERMEDIÁRIO']),
        (0,'integral',['CONTEXTO','DA','COSTA']),
        (1,'imersivo',['FISSURAS','EM','ATIVIDADE']),
        (2,'1:1',['TECNOLOGIA','DE','CAMPO']),
        (3,'integral',['ACERVO','EROS']),
    ]
    for i,(j,mode,words) in enumerate(variants):
        m,asset,offset=media[j];start=i*3
        shot={'id':str(i),'type':'video','asset':asset,'start':start,'end':start+3,'source_in_seconds':offset,
              'headline':m['label'],'lead':{'integral':'Enquadramento integral','imersivo':'Enquadramento imersivo','4:5':'Recorte de teste 4:5','1:1':'Recorte de teste 1:1'}[mode],
              'subject':m['subject'],'source':m['page'],'source_display':m['credit'],'evidence':'literal','video_zoom':1,'focus':[.5,.5]}
        if mode=='integral':shot['video_context_layout']='cena_integral'
        elif mode in ('4:5','1:1'):
            # Explicit laboratory comparison, NOT measured ROI or automatic semantic decision.
            shot['video_context_layout']='recorte_relacional_seguro'
            shot['documentary_viewport']=mode
        shots.append(shot)
        captions.append({'start':start,'end':start+3,'words':[{'w':w,'hl':k==0} for k,w in enumerate(words)]})
    dur=3*len(variants)
    # Silent laboratory asset only: captions demonstrate typography, not sync.
    wav=out/'silencio_lab.wav'
    with wave.open(str(wav),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(bytes(dur*48000*2))
    h=E.sha(wav);audio='e202/'+h+'.wav'
    (E.PUBLIC/'e202').mkdir(exist_ok=True);shutil.copyfile(wav,E.PUBLIC/audio)
    props={'duracao':dur,'shots':shots,'preview':True,'private_review_only':True,'scene_narration_asset':audio,
           'documentary_captions':captions,'documentary_caption_origin':'FRASES_MEDIDAS_LAB'}
    E.write(out/'props.json',props)
    E.write(out/'fontes.json',{'publish':False,'laboratory_silent':True,'semantic_approval':'PENDING','framing':'LAB_MANUAL_COMPARISON_NOT_ROI','history_scope':'modern archive overview; historical footage not verified','sources':[m for m,_,_ in media]})
if __name__=='__main__':main()
