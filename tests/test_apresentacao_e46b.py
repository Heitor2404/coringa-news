import numpy as np
import pytest
from src.v4.formatos import apresentacao_e46b as P
from src.v4.formatos import raster_e18 as R

def test_papeis_distintos_e_limites():
    a,b=P.material("entrada",1)
    c,d=P.material("acoplado",1)
    assert a[0]>a[2] and c[2]>c[0]
    assert np.linalg.norm(a-c)>.5
    with pytest.raises(ValueError):
        P.material("desconhecido",0)
    with pytest.raises(ValueError):
        P.material("entrada",float("nan"))

def test_borda_sem_halo():
    ids=np.array([[-1,0,0,1]])
    z=np.array([[np.inf,1.,1.,2.]])
    n=np.zeros((1,4,3)); n[:,:,2]=1
    np.testing.assert_array_equal(P.bordas(ids,z,n),[[False,True,True,False]])

def test_render_mesma_cobertura():
    cam=R.Camera([0,0,0],[0,0,1],[0,1,0],55,90,160)
    v=np.array([[-.5,-.5,3],[.5,-.5,3],[.5,.5,3],[-.5,.5,3]])
    f=np.array([[0,1,2],[0,2,3]])
    fundo=R.fundo_gradiente(90,160)
    x,qa=R.renderizar(cam,[(v,f,np.array([.7,.7,.7]),0.)],fundo,ss=1,estilo="e33")
    c,b=P.material("entrada",1)
    y,qb=R.renderizar(cam,[(v,f,c,b)],fundo,ss=1,estilo="e46b")
    assert qa==qb and np.any(x!=y)
