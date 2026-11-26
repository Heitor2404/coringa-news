import pytest
from PIL import Image
from scripts import qa_documentario_geografia_e219 as E

def test_short_native_candidate_does_not_relax_pixel_threshold():
    E.validar_origem_video(1280,720,4.2,min_duration=3.9)
    with pytest.raises(ValueError,match='E219-DURACAO'):
        E.validar_origem_video(1280,720,4.2)
    with pytest.raises(ValueError,match='E219-RESOLUCAO'):
        E.validar_origem_video(854,480,30,min_duration=3.9)
    with pytest.raises(ValueError,match='E219-DURACAO'):
        E.validar_origem_video(1280,720,3.8,min_duration=3.9)

def test_short_windows_only_when_requested_and_within_native_duration(monkeypatch):
    im=Image.new('RGB',(240,140),'black')
    im.paste('white',(0,0,120,140))
    monkeypatch.setattr(E,'frame',lambda *a,**k:im)
    m={'local_source':'fixture','duration_s':4.2}
    assert E.windows(m,3.8)==[]
    windows=E.windows(m,3.8,allow_short=True)
    assert windows and all(0<=t and t+3.8<=4.2 for t,_ in windows)
    assert E.windows({**m,'duration_s':3.7},3.8,allow_short=True)==[]
