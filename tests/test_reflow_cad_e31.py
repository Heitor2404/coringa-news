import unittest
import numpy as np
from src.v4.formatos.reflow_cad_e31 import planejar,limites,LEGACY_SCALE


class E31(unittest.TestCase):
    def test_wide_top_narrow_bottom(self):
        f=np.zeros((480,270),bool);m=f.copy()
        f[100:285,40:225]=True
        m[100:190,45:220]=True
        r=planejar(f,m)
        self.assertGreater(r["scale"],LEGACY_SCALE)
        self.assertIsNotNone(limites(f,m,r["scale"],r["ty"]))
        self.assertFalse(r["publish"])

    def test_narrow_lower_motion(self):
        f=np.zeros((480,270),bool)
        f[90:300,30:240]=True
        r=planejar(f,f)
        self.assertIsNotNone(limites(f,f,r["scale"],r["ty"]))
        self.assertLessEqual(r["scale"],.8)

    def test_empty(self):
        z=np.zeros((480,270),bool)
        with self.assertRaises(ValueError):
            planejar(z,z)
