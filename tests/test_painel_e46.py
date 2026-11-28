import math
import numpy as np
import pytest
from src.v4.formatos import editorial_e42 as E
from src.v4.formatos import reflow_cad_e31 as R

def test_painel_totais_observados():
    a=np.linspace(0,6*math.pi,240)
    t=E.transmissao(a,-a/11,-1/11,30)
    d=E.painel(t,240)
    assert d["razao"]=="11,0:1"
    assert d["entrada"]=="3,0 voltas" and d["saida"]=="-98,2°"
    assert d["publish"] is False
    with pytest.raises(ValueError):
        E.painel(t,239)

def test_painel_reserva_area_sem_colidir():
    fg=np.zeros((R.SH,R.SW),bool)
    fg[90:260,70:190]=True
    p=R.planejar(fg,fg,R.VIEW_E46)
    assert p["viewport"]==[50,400,1030,962]
    assert p["scale"]*p["foreground_bbox"][3]+p["ty"]<=962+1e-7
