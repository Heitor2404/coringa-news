from PIL import Image
import numpy as np,cv2
from src.v4.formatos import diagnostico_movimento_e334 as D

def test_camera_pan_with_fixed_texture_does_not_become_semantic_proof():
    rng=np.random.default_rng(2026);x=rng.integers(0,256,(320,480),dtype=np.uint8)
    y=cv2.warpAffine(x,np.float32([[1,0,18],[0,1,9]]),(480,320))
    b=[.35,.35,.60,.60]
    q=D.par(Image.fromarray(x),Image.fromarray(y),[b],[b])
    assert q['status']=='REGISTRO_TECNICO_ESTIMADO'
    assert .02<q['camera_deslocamento_relativo']<.08
    assert not q['prova_semantica']

def test_moving_region_with_static_background_reports_residual_not_identity():
    rng=np.random.default_rng(7);x=rng.integers(0,256,(320,480),dtype=np.uint8)
    y=x.copy();y[110:190,170:270]=0
    b=[.35,.34,.57,.60]
    q=D.par(Image.fromarray(x),Image.fromarray(y),[b],[b])
    assert q['status']=='REGISTRO_TECNICO_ESTIMADO'
    assert q['camera_deslocamento_relativo']<.01
    assert q['diferenca_regiao']>q['diferenca_fundo']+20
    assert not q['prova_semantica']

def test_missing_region_or_flat_image_does_not_claim_registration():
    x=Image.new('RGB',(480,320))
    assert D.par(x,x)['status']=='REFERENCIA_INSUFICIENTE'
    assert D.par(x,x,[[.2,.2,.5,.5]],[[.2,.2,.5,.5]])['status']=='REFERENCIA_INSUFICIENTE'
    assert not D.diagnosticar([x,x,x],[0,1,2],None)['prova_continua']
