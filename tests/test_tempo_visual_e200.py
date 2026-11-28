import pytest
from src.v4.formatos.tempo_visual_e200 import validar_marcos

@pytest.fixture
def m():
    return [dict(t=0,fracao=0,fonte="fixture"),dict(t=2,fracao=.2,fonte="fixture"),dict(t=5,fracao=1,fonte="fixture")]

@pytest.mark.parametrize("modo",["degrau","linear_ilustrativa"])
def test_valido(m,modo):
    assert validar_marcos(m,modo,0,5)

@pytest.mark.parametrize("campo,valor",[("t",0),("fracao",1.1),("fonte","")])
def test_recusa(m,campo,valor):
    m[1][campo]=valor
    with pytest.raises(ValueError):
        validar_marcos(m,"degrau",0,5)

def test_recusa_modo_inferido(m):
    with pytest.raises(ValueError):
        validar_marcos(m,None,0,5)

def test_recusa_extremo(m):
    with pytest.raises(ValueError):
        validar_marcos(m,"degrau",0,6)
