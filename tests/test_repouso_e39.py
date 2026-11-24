import unittest
import numpy as np
from src.v4.formatos.repouso_e39 import extrair
from src.v4.formatos.eventos_trajetoria_e27 import extrair as eventos

class E39(unittest.TestCase):
    def test_dwell_before_and_after(self):
        q=np.r_[np.zeros(61),np.linspace(0,1,61)[1:],np.ones(120)]
        r=extrair(q,30,"rad")
        self.assertEqual([p["tipo"] for p in r["fases"]],
                         ["repouso_amostrado","variacao_observada","repouso_amostrado"])
        self.assertEqual(r["fases"][0]["frame_fim"],60)
        self.assertEqual(r["fases"][1]["frame_fim"],120)
        self.assertAlmostEqual(r["fracao_intervalos_repouso"],179/239)
    def test_continuous_movement(self):
        r=extrair(np.linspace(0,1,240),30,"rad")
        self.assertEqual(r["fracao_intervalos_repouso"],0)
    def test_constant(self):
        r=extrair(np.ones(30),30,"mm")
        self.assertEqual(r["fracao_intervalos_repouso"],1)
    def test_short_pause_not_claimed(self):
        r=extrair([0,0,0,.5,1],30,"rad")
        self.assertEqual(r["fracao_intervalos_repouso"],0)
    def test_integrated_clock_and_units(self):
        r=eventos([0]*20+[.5]*20,30,"angulo","Rotação",unidade="rad")
        self.assertEqual(r["repouso"]["unidade"],"rad")
        self.assertEqual(r["repouso"]["quadros"],40)
        self.assertEqual(r["repouso"]["interpretacao_causal"],"NAO_INFERIDA")
