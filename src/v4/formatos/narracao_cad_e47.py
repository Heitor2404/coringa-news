"""E47: private phrase-level timing from real, individually recorded WAVs.
Preserve all existing CAD shot boundaries and video cadence. No guessed
word timing, no speech time-stretch, no inferred physical fact.
"""
import copy
import json
import math
from pathlib import Path
import subprocess
import wave
import numpy as np
from . import legenda_sync as L
from . import ponte_cad_editorial_e28 as B

SR=48000
GAP=round(.18*SR)

def pcm(path):
    raw=subprocess.check_output([B.ffmpeg(),"-v","error","-i",str(path),"-ac","1","-ar",str(SR),"-f","s16le","-"])
    a=np.frombuffer(raw,dtype="<i2").copy()
    n=len(a)//480
    if n<2:
        raise ValueError("E47-AUDIO_CURTO")
    rms=np.sqrt(np.mean((a[:n*480].reshape(n,480).astype(float)/32768)**2,axis=1))
    active=np.flatnonzero(L.mascara_fala(rms))
    if not len(active):
        raise ValueError("E47-SEM_FALA")
    lo=max(0,int(active[0])*480-1920)
    hi=min(len(a),(int(active[-1])+1)*480+2880)
    return a[lo:hi],int(active[0])*480-lo,min(hi,(int(active[-1])+1)*480)-lo

def montar(props,plan,root):
    if props.get("preview") is not True or props.get("private_review_only") is not True or props.get("subtitle_mode"):
        raise ValueError("E47-PRIVADO")
    p=copy.deepcopy(props); shots=p["shots"]
    if set(plan)!=set(s["id"] for s in shots) or len(plan)!=len(shots):
        raise ValueError("E47-PLANO")
    total=round(p["duracao"]*SR)
    audio=np.zeros(total,dtype="<i2"); report=[]; last=0
    root=Path(root).resolve()
    for s in shots:
        if s.get("type")!="cad_preview" or s.get("cad_reflow",{}).get("schema")!="coringa.cad.hero.balanced.private.v1":
            raise ValueError("E47-CENA")
        ini,fim=round(s["start"]*SR),round(s["end"]*SR)
        if ini!=last or fim<=ini or fim>total:
            raise ValueError("E47-CLOCK")
        last=fim
        pos=ini+round(.10*SR)
        caps=[]
        if not plan[s["id"]]:
            raise ValueError("E47-SEM_TEXTO")
        for phrase in plan[s["id"]]:
            txt=phrase["text"]
            if not isinstance(txt,str) or not 1<=len(txt)<=75 or "\n" in txt:
                raise ValueError("E47-TEXTO")
            path=(root/phrase["wav"]).resolve()
            if not path.is_relative_to(root) or not path.is_file() or B.sha(path)!=phrase["sha256"]:
                raise ValueError("E47-HASH")
            data,a,b=pcm(path)
            if pos+len(data)>fim:
                raise ValueError("E47-FALA_NAO_CABE")
            audio[pos:pos+len(data)]=data
            start=max(0,math.floor((pos+a-ini)/SR*30)/30)
            end=min((fim-ini)/SR,math.ceil((pos+b-ini)/SR*30)/30)
            if end-start<.35:
                raise ValueError("E47-LEITURA")
            caps.append(dict(start=start,end=end,text=txt))
            report.append(dict(shot=s["id"],text=txt,sha256=phrase["sha256"],
                fala_inicio=(pos+a)/SR,fala_fim=(pos+b)/SR,
                legenda_inicio=ini/SR+start,legenda_fim=ini/SR+end))
            pos+=len(data)+GAP
        s["cad_phrase_captions"]=caps
    if last!=total:
        raise ValueError("E47-DURACAO")
    return p,audio,report

def preparar(props_path,plan_path,public,out):
    pth=Path(plan_path)
    p,audio,r=montar(json.loads(Path(props_path).read_text()),json.loads(pth.read_text()),pth.parent)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    wav=out/"voz_e47.wav"
    with wave.open(str(wav),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes(audio.tobytes())
    asset="cad_e47/"+B.sha(wav)+".wav"
    dst=Path(public)/asset;dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(wav.read_bytes())
    p["cad_narration_asset"]=asset
    (out/"props.json").write_text(json.dumps(p,ensure_ascii=False,indent=2))
    (out/"SYNC.json").write_text(json.dumps(dict(frases=r,amostras=len(audio),sample_rate=SR,
        hash_voz=B.sha(wav),metodo="energia_de_frases_gravadas_individualmente",
        palavras_alinhadas=False,publish=False,visual_approved=False),ensure_ascii=False,indent=2))
    return p

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    for k in ("props","plan","public","out"):
        a.add_argument(k)
    v=a.parse_args()
    preparar(v.props,v.plan,v.public,v.out)
