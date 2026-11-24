import numpy as np
import pytest
from src.v4.formatos import direcao_cad_e46f as E

def rel():
    return dict(schema="coringa.revelacao.e45.v1",publish=False,vistas=[
        dict(aceita=True,alvo=1,ocultos=[2],protegidos=[0,1],depois=[.9,.8],ganho=.4),
        dict(aceita=False,alvo=0,ocultos=[],protegidos=[0],depois=[.1],ganho=0)])

def test_only_evidenced_views():
    a=E.planos(rel(),3)
    assert a==[dict(alvo=None,ocultos=[],protegidos=[]),dict(alvo=1,ocultos=[2],protegidos=[0,1])]

def test_protected_mesh_cannot_hide():
    r=rel();r["vistas"][0]["ocultos"]=[0]
    with pytest.raises(ValueError,match="VISTA"):
        E.planos(r,3)

def test_hash_detects_change():
    q=np.arange(30).reshape(10,3)
    h=E.hash_poses(q)
    assert h==E.hash_poses(q.copy())
    q[1,1]+=1
    assert h!=E.hash_poses(q)
