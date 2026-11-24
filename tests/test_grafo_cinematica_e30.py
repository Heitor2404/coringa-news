import unittest
from types import SimpleNamespace as S
import numpy as np
from src.v4.formatos.grafo_cinematica_e30 import extrair


def mont(fechado=True):
    juntas=[S(nome="entrada",corpo=2,tipo="hinge",adr=0),
            S(nome="elo",corpo=3,tipo="hinge",adr=1),
            S(nome="guia",corpo=4,tipo="slide",adr=2)]
    return S(nq=3,corpos=["world","base","a","b","c"],pai=[-1,0,1,2,1],
             juntas=juntas,coords=[S(junta=i) for i in range(3)],
             igualdades=[S(tipo="connect",a=3,b=4)] if fechado else [])


class E30(unittest.TestCase):
    def setUp(self):
        self.q=np.array([[0,0,0],[.5,.2,.01],[1,.3,.02],[2,0,0]])
        self.a={"motor":{0:1.}}

    def test_rotation_and_slide(self):
        r=extrair(mont(),self.q,self.a)
        by={m["junta"]:m for m in r["movimentos"]}
        self.assertEqual(by["entrada"]["tipo"],"rotacao_relativa")
        self.assertEqual(by["guia"]["tipo"],"translacao_relativa")
        self.assertEqual(by["guia"]["amplitude"],20)
        self.assertEqual(by["entrada"]["papel"],"entrada_prescrita")
        rel=next(x for x in r["relacoes"] if x["movimento"]=="guia")
        self.assertEqual([x["tipo"] for x in rel["caminho"]],
                         ["descendente_na_arvore","fechamento_connect"])
        self.assertFalse(rel["prova_forca_ou_dinamica"])

    def test_common_base_not_connection(self):
        r=extrair(mont(False),self.q,self.a)
        self.assertNotIn("guia",[x["movimento"] for x in r["relacoes"]])

    def test_no_false_causal_relation_between_inputs(self):
        r=extrair(mont(),self.q,{"m1":{0:1},"m2":{2:1}})
        self.assertNotIn("guia",[x["movimento"] for x in r["relacoes"]])
        self.assertEqual(r["inferencia_causal"],"NAO_INFERIDA")

    def test_actual_frame_clock(self):
        r=extrair(mont(),self.q,self.a,indices=[0,2,3])
        m=next(x for x in r["movimentos"] if x["junta"]=="guia")
        self.assertEqual(m["frame_max"],1)
        self.assertAlmostEqual(m["tempo_max_s"],1/30)

    def test_non_finite(self):
        q=self.q.copy();q[1,0]=np.nan
        with self.assertRaisesRegex(ValueError,"TRAJETORIA"):
            extrair(mont(),q,self.a)
