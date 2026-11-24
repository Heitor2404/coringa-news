import numpy as np
from src.v4.formatos import hero_cad_e46d as H
from src.v4.formatos import reflow_cad_e31 as R

def test_balanced_large_and_centered():
    y,x=np.mgrid[:R.SH,:R.SW]
    fg=(x-135)**2+(y-190)**2<90**2
    m=(x-135)**2+(y-190)**2<32**2
    p=H.planejar(fg,m,balanced=True)
    assert p["schema"]=="coringa.cad.hero.balanced.private.v1"
    assert 900<=p["center_y"]<=1000
    assert p["width_fraction"]>=.85
    assert p["output_bbox"][1]>=H.BALANCED["viewport"][1]-1e-7
    assert p["output_bbox"][3]<=H.BALANCED["viewport"][3]+1e-7
    assert p["publish"] is False
    assert p["essential_status"]=="SEM_MASCARA_SEMANTICA"
