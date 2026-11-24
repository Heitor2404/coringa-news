import wave
import numpy as np
import pytest
from src.v4.formatos import narracao_cad_e47 as E
from src.v4.formatos import ponte_cad_editorial_e28 as B

def fixture(tmp_path,d=1):
    sr=48000
    x=(np.sin(np.arange(int(sr*d))*2*np.pi*220/sr)*5000).astype("<i2")
    path=tmp_path/"a.wav"
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes(np.r_[np.zeros(4800,dtype="<i2"),x,np.zeros(4800,dtype="<i2")].astype("<i2").tobytes())
    props=dict(preview=True,private_review_only=True,duracao=2,shots=[
      dict(id="x",type="cad_preview",start=0,end=2,cad_reflow={"schema":"coringa.cad.hero.balanced.private.v1"})])
    return props,{"x":[dict(text="Frase de teste.",wav="a.wav",sha256=B.sha(path))]}

def test_preserves_clock_and_actual_onset(tmp_path):
    p,q=fixture(tmp_path)
    a,pcm,r=E.montar(p,q,tmp_path)
    assert len(pcm)==96000 and a["shots"][0]["end"]==2
    assert "cad_phrase_captions" not in p["shots"][0]
    assert 0<=r[0]["fala_inicio"]-r[0]["legenda_inicio"]<=1/30+1e-8
    assert 0<=r[0]["legenda_fim"]-r[0]["fala_fim"]<=1/30+1e-8

def test_refuses_overlong(tmp_path):
    p,q=fixture(tmp_path,3)
    with pytest.raises(ValueError,match="NAO_CABE"):
        E.montar(p,q,tmp_path)

def test_refuses_hash(tmp_path):
    p,q=fixture(tmp_path)
    q["x"][0]["sha256"]="0"*64
    with pytest.raises(ValueError,match="HASH"):
        E.montar(p,q,tmp_path)
