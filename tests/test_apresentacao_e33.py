import unittest
from types import SimpleNamespace
import numpy as np
from src.v4.formatos.apresentacao_e33 import focos,intensidade,material,bordas_locais,sombrear


class E33(unittest.TestCase):
    def test_near_side_not_background(self):
        ids=np.array([[-1,0,1,1]])
        z=np.array([[np.inf,1.,2.,2.]])
        n=np.zeros((1,4,3));n[:,:,2]=1
        np.testing.assert_array_equal(bordas_locais(ids,z,n),[[False,True,False,False]])

    def test_same_depth_seam(self):
        ids=np.array([[0,1]])
        z=np.ones((1,2));n=np.zeros((1,2,3));n[:,:,2]=1
        np.testing.assert_array_equal(bordas_locais(ids,z,n),[[True,True]])

    def test_focus_only_real_linked_bodies(self):
        mont=SimpleNamespace(corpos=["base","a","b","c"])
        g=dict(schema="coringa.cinematica.observada.v1",movimentos=[
          dict(junta="j0",corpo="a",papel="entrada_prescrita"),
          dict(junta="j1",corpo="b",papel="movimento_observado"),
          dict(junta="j2",corpo="c",papel="movimento_observado")],
          relacoes=[dict(entrada="j0",movimento="j1")])
        tr=focos(mont,g,list(range(40)))
        self.assertEqual([x["corpos"] for x in tr],[[1],[2]])
        self.assertEqual(tr[-1]["frame_fim_exclusivo"],40)
        self.assertEqual(intensidade(10,3,tr),0)
        self.assertGreater(intensidade(10,1,tr),intensidade(10,2,tr))

    def test_material_and_shading_bounded(self):
        c,b=material("entrada",1)
        r=sombrear(c[None,:],np.array([.5]),np.array([.5]),np.array([.5]))
        self.assertTrue((r>=0).all() and (r<=1).all())
        self.assertEqual(b,0)
