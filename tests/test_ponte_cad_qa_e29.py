import unittest
from src.v4.formatos.ponte_cad_qa_e29 import selecionar


def item(id="a"):
    return dict(id=id,estado_execucao="PASS",validacao_externa="APROVADO",
                estado="VALIDADO_TECNICAMENTE_SEM_HOMOLOGACAO_VISUAL",
                liberado_para_publicacao=False,publish=False,visual_approved=False,
                palco_cad={})


class E29(unittest.TestCase):
    def test_selects_by_data_not_machine(self):
        self.assertEqual(selecionar({"modelos":[item("a"),item("b")]},"b")["id"],"b")

    def test_duplicate(self):
        with self.assertRaisesRegex(ValueError,"AMBIGUO"):
            selecionar({"modelos":[item(),item()]},"a")

    def test_failed_oracle(self):
        m=item();m["validacao_externa"]="REPROVADO"
        with self.assertRaisesRegex(ValueError,"VALIDACAO"):
            selecionar({"modelos":[m]},"a")

    def test_no_publish_permission(self):
        m=item();m["liberado_para_publicacao"]=True
        with self.assertRaisesRegex(ValueError,"VALIDACAO"):
            selecionar({"modelos":[m]},"a")
