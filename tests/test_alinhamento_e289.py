import numpy as np
from src.v4.formatos import legenda_sync as L

def test_pause_repair_keeps_words_and_audio_acceptance(monkeypatch,tmp_path):
    f=np.zeros(220,dtype=bool);f[5:30]=True;f[90:165]=True
    p=[{'w':'um','s':.05,'e':.25},{'w':'dois','s':.48,'e':.8},{'w':'três','s':1.25,'e':1.6}]
    monkeypatch.setattr(L,'energia',lambda _:f.astype(float))
    out,report=L.alinhar_documental(p,tmp_path/'x.wav')
    assert [x['w'] for x in out]==[x['w'] for x in p]
    assert report['original']['n_palavras_sem_fala']==1
    assert report['final']==L.conferir_palavras(out,f,3)
    assert report['final']['n_palavras_sem_fala']<=report['original']['n_palavras_sem_fala']
    assert all(abs(a['s']-b['s'])<=.85 for a,b in zip(p,out))
