import unittest
from types import SimpleNamespace
import numpy as np
from src.v4.formatos.camera_e24 import evidencia,pontos_foco,movimento_projetado,cabe


class Mont:
    def __init__(self):
        self.visuais=[SimpleNamespace(corpo=0,local=np.eye(4),
            vertices=np.array([[0,0,0],[.1,0,0],[0,.02,0]]))]
    def poses(self,q):
        c,s=np.cos(q),np.sin(q)
        T=np.array([[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]])
        return [T]


class Cam:
    def projetar(self,p):
        return p[:,0]*1000+150,p[:,1]*1000+150,np.ones(len(p)),p


class E24(unittest.TestCase):
    def test_rotacao_sem_deslocar_origem(self):
        b,t=evidencia(Mont(),[0,np.pi/2,np.pi])
        self.assertEqual(set(t),{0})
        self.assertGreater(movimento_projetado(Cam(),t,300),0.05)

    def test_estatico(self):
        _,t=evidencia(Mont(),[0,0,0])
        self.assertEqual(t,{})
        self.assertEqual(movimento_projetado(Cam(),t,300),0)

    def test_caixa_inclui_ponta_entre_amostras(self):
        q=np.zeros(101);q[47]=np.pi/2
        b,t=evidencia(Mont(),q)
        self.assertIn(0,t)
        self.assertAlmostEqual(b[0][:,1].max(),.1)

    def test_foco_preserva_todo_movimento(self):
        b={0:np.array([[-.1,0,0],[.1,0,0]]),
           1:np.array([[-10,0,0],[10,0,0]])}
        p,f=pontos_foco(b,{0:np.zeros((2,2,3))})
        self.assertEqual(f,"pecas_moveis")
        np.testing.assert_allclose([p[:,0].min(),p[:,0].max()],[-.1,.1])

    def test_limite_real(self):
        self.assertTrue(cabe(Cam(),np.array([[0,0,0],[.1,0,0]]),(.1,.1,.9,.9),300,300))
        self.assertFalse(cabe(Cam(),np.array([[0,0,0],[.2,0,0]]),(.1,.1,.9,.9),300,300))
