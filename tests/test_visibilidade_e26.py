import unittest
from types import SimpleNamespace
import numpy as np
from src.v4.formatos import visibilidade_e26 as V
from src.v4.formatos.raster_e18 import Camera


def quad(z,body,size=.6):
    return body,np.array([[-size,-size,z],[size,-size,z],[size,size,z],[-size,size,z]]),np.array([[0,1,2],[0,2,3]],np.int64)


class E26(unittest.TestCase):
    def test_opposite_camera_reveals_hidden_body(self):
        scene=[quad(0.,0),quad(.1,1,.4)]
        a=Camera([0,0,-3],[0,0,0],[0,1,0],45,1080,1920)
        b=Camera([0,0,3],[0,0,0],[0,1,0],45,1080,1920)
        hidden=V.avaliar(a,[scene],{1})
        shown=V.avaliar(b,[scene],{1})
        self.assertEqual(hidden["media"],0)
        self.assertGreater(shown["media"],.99)
        self.assertGreater(V.nota(.8,shown),V.nota(1.,hidden))

    def test_each_body_penalized(self):
        cam=Camera([0,0,3],[0,0,0],[0,1,0],45,1080,1920)
        scene=[quad(0.,0),quad(.1,1,.4),quad(.2,2,.2)]
        r=V.avaliar(cam,[scene],{1,2})
        self.assertGreater(r["corpos"]["2"],.99)
        self.assertLess(r["corpos"]["1"],.9)
        self.assertLess(r["pior_corpo"],.9)

    def test_sector_coverage(self):
        xs=[(1.-i/100,None,{"guinada_graus":i*15}) for i in range(24)]
        picked=V.candidatos_por_setor(xs)
        self.assertEqual(len({x[2]["guinada_graus"]//30 for x in picked}),12)
