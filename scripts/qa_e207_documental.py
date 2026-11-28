"""E207: regression with original Panama footage, authenticated ATLAS and archive photo.
Uses existing scene data, renderer and gates. Laboratory voice, never publish.
"""
import json
import copy
import hashlib
import subprocess
import wave
from pathlib import Path
import numpy as np
from src.v4.formatos import filme_editorial as FILME, ponte_mapa_atlas as ATLAS
from src.v4.formatos import diretor_visual_e202 as D
from src.v4.formatos.narracao_cad_e47 import pcm, SR, GAP

def read(p):
    return json.loads(Path(p).read_text(encoding='utf8'))

def main():
    out=Path('qa_e207');out.mkdir(exist_ok=True)
    public=Path('motor4/remotion/public')
    p=read('docs/v4/formatos/filme_panama_12s_prova.json')
    p['publicar']=False
    # Exact original media windows from the previously reviewed QA.
    src=Path('stage_atlas/e207/mapa.mp4')
    proof=src.parent/'comprovante_atlas.json'
    ATLAS.confirmar(read(src.parent/'preparo_atlas.json'),src,src.parent)
    m={'id':'atlas','type':'atlas_map','start':3,'end':7.4,'headline':'Canal do Panamá',
       'subject':'Localização do canal','lead':'GEOGRAFIA','evidence':'explainer',
       'cues':[{'at':.3,'label':'CANAL DO PANAMÁ'}]}
    for s in p['shots'][1:]:
        s['start']=round(s['start']+4.4,4);s['end']=round(s['end']+4.4,4)
    p['shots'].insert(1,m);p['duracao']=16.4
    p=ATLAS.inserir_no_filme(p,'atlas',src,proof)
    result=FILME.preparar(p,out/'documental',public)
    props=read(result['props']);props.update(preview=True,private_review_only=True)
    props.pop('safe_area_profile',None)
    # Fixed windows; speak individual short phrases. No time stretching,
    # no made-up word timestamps. Reuse the E47 measured waveform primitive.
    frases={
      '01-camara-real':['Como esse navio sobe?'],
      'atlas':['O Canal do Panamá','liga dois oceanos.'],
      '02-principio-hidraulico':['A água entra.','O navio sobe junto.'],
      '03-segue-passagem-real':['No novo nível, segue.'],
      '04-gatun-historico':['Obras de Gatún, 1913.'],
    }
    audio=np.zeros(round(props['duracao']*SR),dtype='<i2')
    grupos=[];report=[]
    for s in props['shots']:
        lo,hi=round(s['start']*SR),round(s['end']*SR)
        pos=lo+round(.08*SR)
        for j,txt in enumerate(frases[s['id']]):
            wav=out/f"{s['id']}-{j}.wav"
            subprocess.run(['espeak-ng','-v','pt-br','-s','185','-w',str(wav),txt],check=True)
            data,a,b=pcm(wav)
            if pos+len(data)>hi:
                raise ValueError(f"E207-FALA-NAO-CABE {s['id']} {txt}: {(pos+len(data)-hi)/SR:.3f}s")
            audio[pos:pos+len(data)]=data
            start,end=(pos+a)/SR,(pos+b)/SR
            words=txt.split()
            best=max(range(len(words)),key=lambda i:len(words[i]))
            grupos.append({'start':round(start,5),'end':round(end,5),
                           'words':[{'w':w,'hl':i==best} for i,w in enumerate(words)]})
            report.append({'id':s['id'],'texto':txt,'fala_inicio':start,'fala_fim':end,
                           'legenda_inicio':round(start,5),'legenda_fim':round(end,5)})
            pos+=len(data)+GAP
    wav=out/'voz.wav'
    with wave.open(str(wav),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes(audio.tobytes())
    sha=hashlib.sha256(wav.read_bytes()).hexdigest()
    asset='e202/'+sha+'.wav'
    (public/'e202').mkdir(parents=True,exist_ok=True)
    (public/asset).write_bytes(wav.read_bytes())
    props=D.anexar_audio_documental(props,asset,grupos,public,'FRASES_MEDIDAS_LAB')
    (out/'props.json').write_text(json.dumps(props,ensure_ascii=False))
    (out/'sync.json').write_text(json.dumps({'metodo':'eSpeak laboratório, frases medidas por energia',
        'palavras_alinhadas':False,'publicar':False,'voz_sha256':sha,'frases':report},ensure_ascii=False,indent=2))
    print('E207-PREPARADO',props['duracao'],[s['type'] for s in props['shots']])

if __name__=='__main__':
    main()
