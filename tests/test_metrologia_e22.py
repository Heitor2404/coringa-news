"""Provas sintéticas: não são resultados dimensionais de equipamento real."""
import unittest
from types import SimpleNamespace
import numpy as np
from src.v4.formatos.metrologia_e22 import medir_planos, resumo_serie, diagnostico


def visual(c, nome):
    return SimpleNamespace(corpo=c, nome=nome, local=np.eye(4),
        vertices=np.array([[0, 0, 0], [0, .01, 0], [0, 0, .01], [0, .01, .01]]),
        faces=np.array([[0, 1, 2], [1, 3, 2]]))


class Mont:
    def __init__(self):
        self.corpos = ["base", "a", "b"]
        self.visuais = [visual(1, "v"), visual(2, "v")]
    def indice_corpo(self, nome):
        return self.corpos.index(nome)
    def poses(self, q):
        t = [np.eye(4) for _ in self.corpos]
        t[2][0, 3] = q
        return t


def spec():
    return dict(tipo="separacao_planos_projetada", unidade="m",
                fonte_datum="fixture sintetica, faces x=0", corpo_referencia="base",
                eixo_local=[1, 0, 0],
                a=dict(corpo="a", visual="v", triangulos=[0, 1]),
                b=dict(corpo="b", visual="v", triangulos=[0, 1]))


class E22(unittest.TestCase):
    def test_gap_e_curso_distintos(self):
        r = medir_planos(Mont(), [.002, .084, .002], spec())
        self.assertAlmostEqual(r["min_mm"], 2)
        self.assertAlmostEqual(r["max_mm"], 84)
        self.assertAlmostEqual(r["curso_mm"], 82)
        self.assertEqual(r["equivalencia_fabricante"], "NAO_DEMONSTRADA")

    def test_sinal_preservado(self):
        self.assertAlmostEqual(medir_planos(Mont(), [-.003], spec())["min_mm"], -3)

    def test_muda_referencial_rigido(self):
        m = Mont()
        old = m.poses
        g = np.array([[0,-1,0,.5],[1,0,0,.2],[0,0,1,.1],[0,0,0,1]])
        m.poses = lambda q: [g @ t for t in old(q)]
        self.assertAlmostEqual(medir_planos(m, [.084], spec())["max_mm"], 84)

    def test_transformacao_visual(self):
        m = Mont()
        m.visuais[0].local[0, 3] = .004
        self.assertAlmostEqual(medir_planos(m, [.084], spec())["max_mm"], 80)

    def test_normal_incompativel(self):
        s = spec()
        s["eixo_local"] = [0,1,0]
        with self.assertRaisesRegex(ValueError, "NORMAL_INCOMPATIVEL"):
            medir_planos(Mont(), [.084], s)

    def test_sem_fonte(self):
        s = spec()
        s["fonte_datum"] = ""
        with self.assertRaisesRegex(ValueError, "SEM_PROCEDENCIA"):
            medir_planos(Mont(), [.084], s)

    def test_indice_invalido(self):
        s = spec()
        s["a"]["triangulos"] = [-1]
        with self.assertRaisesRegex(ValueError, "MALHA_OU_FACE"):
            medir_planos(Mont(), [.084], s)

    def test_visual_ambiguo(self):
        m = Mont()
        m.visuais.append(visual(1, "v"))
        with self.assertRaisesRegex(ValueError, "AMBIGUO"):
            medir_planos(m, [.084], spec())

    def test_degenerado(self):
        m = Mont()
        m.visuais[0].faces[0] = [0,0,1]
        with self.assertRaisesRegex(ValueError, "DEGENERADO"):
            medir_planos(m, [.084], spec())

    def test_nao_planar(self):
        m = Mont()
        m.visuais[0].vertices[3, 0] = .0001
        with self.assertRaisesRegex(ValueError, "PATCH_NAO_PLANAR"):
            medir_planos(m, [.084], spec())

    def test_pose_nao_rigida(self):
        m = Mont()
        old = m.poses
        def bad(q):
            t = old(q)
            t[1][0,0] = 2
            return t
        m.poses = bad
        with self.assertRaisesRegex(ValueError, "POSE_NAO_RIGIDA"):
            medir_planos(m, [.084], spec())

    def test_serie_ruim(self):
        for s in ([], [float("nan")], [[1, 2]]):
            with self.assertRaisesRegex(ValueError, "SERIE"):
                resumo_serie(s)

    def test_diagnostico_nao_escolhe_oraculo(self):
        r = diagnostico(None, [], {"tipo":"folga"}, [.001640031, .088923580])
        self.assertAlmostEqual(r["curso_mm"], 87.283549)
        self.assertAlmostEqual(r["max_mm"], 88.923580)
        self.assertNotIn("dentro_da_tolerancia", r)
        self.assertEqual(r["equivalencia_fabricante"], "NAO_DEMONSTRADA_POR_DATUM")

    def test_datum_opcional_integrado(self):
        r = diagnostico(Mont(), [.084], {"tipo":"folga","datum":spec()}, [.090])
        self.assertAlmostEqual(r["max_mm"], 90)
        self.assertAlmostEqual(r["datum"]["max_mm"], 84)
        self.assertNotIn("dentro_da_tolerancia", r["datum"])
