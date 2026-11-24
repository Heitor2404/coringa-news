"""E234 private geographic entrance; real raster and real footage.
No TTS, no fake aerial flight or optical match. Existing native renderers.
"""
import shutil,wave
from pathlib import Path
from scripts import qa_documentario_geografia_e219 as E
from scripts.qa_atlas_regional import regional_base
from src.v4.formatos import direcao_eventos as DE

def main():
    out=Path('qa_immersao');out.mkdir(exist_ok=True)
    E.STAGE=out/'originais';E.STAGE.mkdir(exist_ok=True)
    E.MAP=Path('stage_atlas/e234-immersao')
    spec=E.read('benchmarks/e219/kilauea_review_e232.json')
    ch=next(c for c in spec['chapters'] if 'atlas' in c)
    q=ch['atlas']
    meta=regional_base(q['raster'],[-166,9,-144,30],7)
    duration=5.5
    p,approach=DE.aproximacao_geografica(E.mapplan(ch,duration))
    clip,proof=E.mapclip(ch,duration,plano_resolvido=p)
    proof_data=E.read(proof)
    assert proof_data['video_sha256']==E.sha(clip)
    map_asset='e234/'+E.sha(clip)+'.mp4'
    (E.PUBLIC/'e234').mkdir(exist_ok=True)
    shutil.copyfile(clip,E.PUBLIC/map_asset)
    # These sources were reviewed in E230.1. Same island, different places;
    # the cut is editorial rather than an assertion of identical camera pose.
    rows=[spec['chapters'][0]['videos'][0],spec['chapters'][2]['videos'][1]]
    clips=[];signatures=[]
    for row in rows:
        m=E.acquire(row)
        wins=E.windows(m,4.6)
        if not wins:raise ValueError('E234-SEM-JANELA')
        t=wins[0][0]
        sig=DE.assinatura_janela([E.frame(m['local_source'],t+3.5*f) for f in (.12,.5,.86)])
        signatures.append(sig)
        a='e234/'+m['expected_sha256']+'.mp4'
        shutil.copyfile(m['local_source'],E.PUBLIC/a)
        if E.sha(E.PUBLIC/a)!=m['expected_sha256']:raise ValueError('E234-SHA')
        clips.append((m,a,t))
    shots=[];captions=[]
    def film(i,start,mode,lead,words):
        m,a,t=clips[i]
        shot={'id':'registro-'+str(i),'type':'video','asset':a,'start':start,'end':start+3.5,
              'source_in_seconds':t,'headline':m['label'],'lead':lead,'subject':m['subject'],
              'source':m['page'],'source_display':m['credit'],'evidence':'literal','video_zoom':1,'focus':[.5,.5]}
        if mode=='4:5':
            shot.update(video_context_layout='recorte_relacional_seguro',documentary_viewport=mode)
        shots.append(shot)
        captions.append({'start':start,'end':start+3.5,'words':[{'w':w,'hl':k==len(words)-1} for k,w in enumerate(words)]})
    film(0,0,'4:5','Registro de 2018',['LAVA','E','OCEANO'])
    shots.append({'id':'mapa','type':'atlas_map','asset':map_asset,'start':3.5,'end':9,
        'headline':q['label'],'lead':'Onde aconteceu','subject':'Mapa regional contemporâneo',
        'source':'NASA Blue Marble','evidence':'explainer'})
    film(1,9,'imersivo','Registro na ilha',['A','LAVA','AVANÇA'])
    total=12.5
    wav=out/'silencio.wav'
    with wave.open(str(wav),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(bytes(round(total*48000)*2))
    audio='e202/'+E.sha(wav)+'.wav'
    (E.PUBLIC/'e202').mkdir(exist_ok=True);shutil.copyfile(wav,E.PUBLIC/audio)
    props={'duracao':total,'shots':shots,'preview':True,'private_review_only':True,
           'scene_narration_asset':audio,'documentary_captions':captions,
           'documentary_caption_origin':'FRASES_MEDIDAS_LAB'}
    E.write(out/'props.json',props)
    E.write(out/'prova.json',{'publish':False,'visual_review':'PENDING','laboratory_silent':True,
        'camera':approach,'map_sha256':E.sha(clip),'map_proof':proof_data,'raster':meta,
        'sources':[m for m,_,_ in clips],'geographic_scope':'ilha; não continuidade óptica',
        'similarity_two_sources':DE.similaridade_janelas(*signatures),
        'framing':'previously reviewed source windows, candidate crops only'})
    print('E234 APROXIMACAO',approach,flush=True)
if __name__=='__main__':main()
