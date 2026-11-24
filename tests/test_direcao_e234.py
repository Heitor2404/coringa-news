import numpy as np
import pytest
from PIL import Image
from src.v4.formatos import direcao_eventos as D
from src.v4.formatos import plano as A

def pattern(reverse=False):
    v=np.tile(np.arange(96,dtype=np.uint8)*2,(64,1))
    if reverse:v=v[:,::-1]
    return Image.fromarray(v).convert('RGB')

def test_rank_distinct_window_first_without_rejecting_eligible_repeat():
    old=D.assinatura_janela([pattern(),pattern()])
    other=D.assinatura_janela([pattern(True),pattern(True)])
    same={'ordem':0,'assinatura':old}
    fresh={'ordem':1,'assinatura':other}
    assert D.similaridade_janelas(old,old)==pytest.approx(1)
    assert D.ordenar_janelas([same,fresh],[old])==[fresh,same]
    assert D.ordenar_janelas([same], [old])==[same]

def test_observations_bound_to_source():
    with pytest.raises(ValueError,match='D-OBS-SHA'):
        D.enquadrar_observacoes({}, {'expected_sha256':'a'*64}, {'sha256_origem':'b'*64})

def test_native_approach_preserves_final_roi_and_samples_coverage(monkeypatch):
    p={'formato':'atlas','_resolvido':True,'duracao':5.5,
        'palco':[{'tipo':'mapa','t':0,'camera':{'foco':[0,0],'ancora':[540,960],'zoom':7},
            'roi':[-1,-1,1,1],'movimento':'fixo'}],
        'beats':[{'roi':[-1,-1,1,1]}],'rasters':[{'nome':'fixture'}]}
    monkeypatch.setattr(A,'raster_info',lambda name:{'bbox':[-50,-50,50,50],'nitido_ate':7})
    monkeypatch.setattr(A,'validar',lambda p:[])
    result,proof=D.aproximacao_geografica(p)
    assert p['palco'][0]['camera']['zoom']==7
    assert A.camera_em(result['palco'],0)['zoom']<7
    assert A.camera_em(result['palco'],5.5)['zoom']==pytest.approx(7)
    assert proof['amostras_camera']==61 and not proof['continuidade_optica']
    monkeypatch.setattr(A,'raster_info',lambda name:{'bbox':[-1,-1,1,1],'nitido_ate':7})
    with pytest.raises(ValueError,match='D-IMERSAO-SEM-BASE'):
        D.aproximacao_geografica(p)


def test_stronger_native_approach_within_coverage(monkeypatch):
    p={'formato':'atlas','_resolvido':True,'duracao':5.5,
        'palco':[{'tipo':'mapa','t':0,'camera':{'foco':[0,0],'ancora':[540,960],'zoom':8},
            'roi':[-.3,-.3,.3,.3],'movimento':'fixo'}],
        'beats':[{'roi':[-.3,-.3,.3,.3]}],'rasters':[{'nome':'fixture'}]}
    monkeypatch.setattr(A,'raster_info',lambda name:{'bbox':[-50,-50,50,50],'nitido_ate':8})
    monkeypatch.setattr(A,'validar',lambda p:[])
    result,proof=D.aproximacao_geografica(p,zoom_desejado=1.6)
    assert proof['escala']==pytest.approx(2**1.6)
    assert A.camera_em(result['palco'],0)['zoom']==pytest.approx(6.4)
    assert A.camera_em(result['palco'],5.5)['zoom']==pytest.approx(8)

def test_entrance_rejects_pin_outside_destination():
    with pytest.raises(ValueError,match='D-ENTRADA-ROI'):
        D.plano_entrada_geografica({},roi_destino=[-1,-1,1,1],bases=[{'nome':'x'}],
            rotulo='região',lonlat=[2,0],fonte_localizacao='https://example.org/source')
