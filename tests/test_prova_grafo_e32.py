import unittest
from src.v4.formatos.prova_grafo_fontes_e32 import observacoes


def graph():
    a=dict(junta="a",tipo="rotacao_relativa",papel="entrada_prescrita")
    b=dict(junta="b",tipo="translacao_relativa",papel="movimento_observado")
    return dict(schema="coringa.cinematica.observada.v1",inferencia_causal="NAO_INFERIDA",
                publish=False,movimentos=[a,b],relacoes=[dict(entrada="a",movimento="b",
                   caminho=[{"tipo":"fechamento_connect"}],prova_forca_ou_dinamica=False)])


class E32(unittest.TestCase):
    def test_observed_not_force(self):
        r=observacoes(graph())
        self.assertIn("rotação relativa",r[0]["afirmacao"])
        self.assertIn("translação relativa",r[0]["afirmacao"])
        self.assertIn("não é prova",r[0]["limitacao"])

    def test_no_connectivity_no_statement(self):
        g=graph();g["relacoes"]=[]
        self.assertEqual(observacoes(g),[])

    def test_reject_dynamics_claim(self):
        g=graph();g["relacoes"][0]["prova_forca_ou_dinamica"]=True
        with self.assertRaisesRegex(ValueError,"RELACAO"):
            observacoes(g)
