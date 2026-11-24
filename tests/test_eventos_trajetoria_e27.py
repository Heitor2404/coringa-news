import unittest
import numpy as np
from src.v4.formatos.eventos_trajetoria_e27 import extrair


class E27(unittest.TestCase):
    def test_reversoes_e_tempo(self):
        q=[0,.002,.01,.01,.009,0,-.01,-.009,0]
        r=extrair(q,30,"distancia","Medida")
        self.assertEqual([f["tipo"] for f in r["fases"]],["aumenta","diminui","aumenta"])
        self.assertEqual(r["extremos"][0]["frame"],6)
        self.assertEqual(r["extremos"][1]["frame"],2)
        self.assertAlmostEqual(r["fases"][0]["tempo_fim_s"],2/30)
        self.assertEqual(r["interpretacao_causal"],"NAO_INFERIDA")

    def test_indices_correspondem_ao_video(self):
        r=extrair([0,.1,.2,.1,0],24,"folga","Folga",indices=[0,2,4])
        self.assertEqual(r["quadros"],3)
        self.assertEqual(r["extremos"][1]["pose"],2)
        self.assertEqual(r["extremos"][1]["frame"],1)
        self.assertAlmostEqual(r["extremos"][1]["tempo_s"],1/24)

    def test_sem_movimento(self):
        r=extrair([.02]*10,30,"folga","Folga")
        self.assertEqual(r["fases"][0]["tipo"],"variacao_pequena")
        self.assertEqual(r["curso_amostrado_mm"],0)

    def test_ruido_nao_vira_reversao(self):
        q=np.array([0,1,2,1.99,3,4,3.99,5])*1e-3
        r=extrair(q,30,"folga","Folga")
        self.assertEqual(len(r["fases"]),1)

    def test_invalido(self):
        for seq,idx in [([1,float("nan")],None),([1,2],[1,0]),([1,2],[0,2])]:
            with self.assertRaises(ValueError):
                extrair(seq,30,"folga","Folga",idx)
