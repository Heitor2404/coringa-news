import numpy as np
import pytest
from src.v4.formatos import hero_cad_e46d as H
from src.v4.formatos import reflow_cad_e31 as R

def masks():
    y,x=np.mgrid[:R.SH,:R.SW]
    fg=(x-135)**2+(y-190)**2<90**2
    motion=(x-135)**2+(y-190)**2<32**2
    return fg,motion

def test_wide_hero_separates_silhouette_and_text():
    fg,m=masks()
    p=H.planejar(fg,m,m)
    assert p["width_fraction"]>=.85
    assert p["scale"]>p["previous_scale"]
    assert p["essential_status"]=="MASK_CHECKED"
    assert max(p["motion_ui_fraction"].values())==0
    x,y,X,Y=p["output_bbox"]
    assert x>=H.VIEW[0]-1e-7 and y>=H.VIEW[1]-1e-7
    assert X<=H.VIEW[2]+1e-7 and Y<=H.VIEW[3]+1e-7

def test_missing_semantic_mask_never_certified():
    fg,m=masks()
    p=H.planejar(fg,m)
    assert p["essential_status"]=="SEM_MASCARA_SEMANTICA" and p["publish"] is False
    assert max(p["motion_ui_fraction"].values())<=H.BUDGET

def test_invalid_essential_mask():
    fg,m=masks()
    with pytest.raises(ValueError):
        H.planejar(fg,m,~fg)
