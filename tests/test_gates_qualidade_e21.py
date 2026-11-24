"""E21 — regressão sem MuJoCo: PASS do solver nunca mascara falha externa."""
import copy
import json
import unittest

from src.v4.formatos.gates_qualidade_e21 import classificar,resumo


def qa_base():
    return {
      "id":"modelo_generico",
      "residuo_max":4.1e-14,
      "verificacao_video":{"quadros":180,"pico_pixels_mudados":1500},
      "interferencias":{"0":[],"60":[],"120":[],"179":[]},
      "sobreposicao_na_referencia_da_fonte":[],
      "publish":False,"visual_approved":False,
    }


class GatesE21(unittest.TestCase):

    def test_xarm_previous_measured_discrepancy_must_not_be_pass(self):
        # Valores observados no CI 45302101314, não uma nova medida CAD.
        qa=qa_base()
        qa["id"]="ufactory_xarm_gripper"
        measured=88.92358047912954
        reference=84.0
        tolerance=4.2
        self.assertGreater(abs(measured-reference),tolerance)
        qa["oraculo_fabricante"]={
          "tipo":"medida_maxima_mm","valor_mm":reference,
          "medido_mm":measured,"tolerancia_mm":tolerance,
          "dentro_da_tolerancia":abs(measured-reference)<=tolerance,
        }
        original=copy.deepcopy(qa)
        r=classificar(qa)
        self.assertEqual(qa,original)
        self.assertEqual(r["estado_execucao"],"PASS")
        self.assertEqual(r["validacao_externa"],"REPROVADO")
        self.assertEqual(r["estado"],"REPROVADO_REFERENCIA_EXTERNA")
        self.assertFalse(r["liberado_para_publicacao"])
        self.assertFalse(r["visual_approved"])
        self.assertFalse(r["publish"])
        self.assertEqual(r["oraculo_fabricante"]["tolerancia_mm"],4.2)

    def test_approved_external_oracle_is_still_not_publication_approval(self):
        qa=qa_base()
        qa["oraculo_fabricante"]={
            "tipo":"medida_maxima_mm","valor_mm":85,
            "medido_mm":85.4,"tolerancia_mm":4.25,
            "dentro_da_tolerancia":True}
        qa["visual_approved"]=True
        qa["publish"]=True
        r=classificar(qa)
        self.assertEqual(r["estado"],"VALIDADO_TECNICAMENTE_SEM_HOMOLOGACAO_VISUAL")
        self.assertEqual(r["validacao_externa"],"APROVADO")
        self.assertFalse(r["liberado_para_publicacao"])
        self.assertEqual(r["homologacao_documental"],"NAO_AVALIADO_60S_NARRACAO")

    def test_model_with_no_manufacturer_oracle_must_be_reported_unverified(self):
        r=classificar(qa_base())
        self.assertEqual(r["validacao_externa"],"SEM_REFERENCIA")
        self.assertEqual(r["estado"],"SEM_REFERENCIA_EXTERNA")
        self.assertFalse(r["liberado_para_publicacao"])

    def test_missing_or_malformed_oracle_boolean_must_never_pass(self):
        for flag in (None,0,1,"true",[],{}):
            qa=qa_base()
            qa["oraculo_fabricante"]={"dentro_da_tolerancia":flag}
            r=classificar(qa)
            self.assertEqual(r["estado"],"BLOQUEADO_ORACULO_INVALIDO")
            self.assertEqual(r["validacao_externa"],"INDETERMINADO")

    def test_new_collisions_override_external_approval(self):
        qa=qa_base()
        qa["oraculo_fabricante"]={"dentro_da_tolerancia":True}
        qa["interferencias"]["60"]=[["corpo_a","corpo_b"]]
        r=classificar(qa)
        self.assertEqual(r["estado"],"REPROVADO_CONTATO_NOVO")
        self.assertEqual(r["verificacao_contato"],"COLISAO_NOVA_DETECTADA")

    def test_reference_overlap_is_not_hidden_as_verified_no_collision(self):
        qa=qa_base()
        qa["sobreposicao_na_referencia_da_fonte"]=[["A","B"]]
        r=classificar(qa)
        self.assertTrue(r["sobreposicao_inicial_fonte"])
        self.assertEqual(r["verificacao_contato"],"SEM_COLISAO_NOVA_NA_AMOSTRA")

    def test_blocked_execution_stays_blocked(self):
        r=classificar({"id":"bad","motivo":"E18-FECHAMENTO"})
        self.assertEqual(r["estado"],"BLOQUEADO_NA_EXECUCAO")
        self.assertEqual(r["estado_execucao"],"BLOCKED")
        self.assertFalse(r["liberado_para_publicacao"])

    def test_indeterminate_motion_validation_stays_blocked(self):
        qa=qa_base()
        del qa["verificacao_video"]
        r=classificar(qa)
        self.assertEqual(r["estado_execucao"],"BLOCKED")

    def test_summary_cannot_claim_100percent_with_xarm_failure(self):
        data=[]
        for flag in (True, False, None):
            qa=qa_base()
            if flag is not None:
                qa["oraculo_fabricante"]={"dentro_da_tolerancia":flag,
                    "valor_mm":84,"medido_mm":89,"tolerancia_mm":4.2}
            data.append(classificar(qa))
        d=resumo(data)
        self.assertEqual(d["total"],3)
        self.assertEqual(d["execucoes_tecnicas_concluidas"],3)
        self.assertEqual(d["oraculos_externos"],
            {"APROVADO":1,"REPROVADO":1,"SEM_REFERENCIA":1,"INDETERMINADO":0})
        self.assertFalse(d["qualidade_externa_100pct"])
        self.assertEqual(len(d["bloqueados_por_oraculo"]),1)
        self.assertFalse(d["todos_visualmente_homologados"])
        self.assertFalse(d["publish"])

    def test_no_machine_name_special_cases_in_gate_source(self):
        from pathlib import Path
        code=Path("src/v4/formatos/gates_qualidade_e21.py").read_text()
        self.assertNotIn("ufactory",code.lower())
        self.assertNotIn("robotiq",code.lower())
        self.assertNotIn("franka",code.lower())


if __name__=="__main__":
    unittest.main()
