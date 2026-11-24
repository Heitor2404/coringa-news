import unittest
from types import SimpleNamespace as S
import numpy as np
from src.v4.formatos import editorial_e42 as E

class E42Tests(unittest.TestCase):
    def test_reuse_exact_objects(self):
        x=object(); y=object()
        leitura={"corpos":[S(indice=0,forma=x),S(indice=1,forma=y)]}
        self.assertIs(E.formas(leitura,[1])[1],y)
        self.assertIs(E.formas(leitura,[0])[0],x)
        with self.assertRaises(ValueError):
            E.formas(leitura,[2])
    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            E.formas({"corpos":[S(indice=1,forma=object())]},[0])
    def test_ratio_and_totals(self):
        a=np.linspace(0,6*np.pi,240)
        r=E.transmissao(a,-a/11,-1/11,30)
        c=E.cues(r,240)
        self.assertIn("11,0:1",c[0]["label"])
        self.assertIn("-98,2°",c[1]["label"])
        self.assertIn("Totais",c[1]["label"])
    def test_nonconjugate(self):
        a=np.linspace(0,6*np.pi,240);b=-a/11;b[50]+=.1
        with self.assertRaises(ValueError):
            E.transmissao(a,b,-1/11,30)
    def test_invalid_contract(self):
        a=np.linspace(0,6*np.pi,240)
        r=E.transmissao(a,-a/11,-1/11,30);r["publish"]=True
        with self.assertRaises(ValueError):
            E.cues(r,240)
