import numpy as np
import pytest
from src.v4.formatos import raster_e18 as R
from src.v4.formatos import revelacao_e45 as E

def quad(k,z,x=0):
    v=np.array([[-.5+x,-.5,z],[.5+x,-.5,z],[.5+x,.5,z],[-.5+x,.5,z]])
    return k,v,np.array([[0,1,2],[0,2,3]])

def camera():
    return R.Camera([0,0,0],[0,0,1],[0,1,0],55,180,320)

def test_revela_oclusor_real_e_preserva_parceiro():
    cenas=[[quad(1,3),quad(2,2),quad(3,3,2)] for _ in range(3)]
    r=E.planejar(camera(),cenas,{1:[3]})["vistas"][0]
    assert r["aceita"] and r["ocultos"]==[2]
    assert min(r["depois"])>.95 and r["protegidos"]==[1,3]
    assert [m[0] for m in cenas[0]]==[1,2,3]

def test_oclusor_protegido_nao_pode_sumir():
    r=E.planejar(camera(),[[quad(1,3),quad(2,2)]],{1:[2]})["vistas"][0]
    assert not r["aceita"] and r["ocultos"]==[]

def test_nao_oculta_objetos_que_nao_bloqueiam():
    r=E.planejar(camera(),[[quad(1,3),quad(2,2,2)]],{1:[]})["vistas"][0]
    assert not r["aceita"] and min(r["antes"])>.95

def test_recusa_identidade_instavel_e_protecao_inexistente():
    with pytest.raises(ValueError,match="IDENTIDADE"):
        E.planejar(camera(),[[quad(1,3)],[quad(2,3)]],{1:[]})
    with pytest.raises(ValueError,match="PROTEGIDOS"):
        E.planejar(camera(),[[quad(1,3)]],{1:[7]})
