import unittest
from src.v4.formatos.gates_qualidade_e21 import classificar

def qa(n=120,bad=101,vol=156.23):
    return dict(residuo_max=1e-10,verificacao_video=dict(quadros=240,pico_pixels_mudados=9577),
                interferencia_brep=dict(quadros_auditados=n,quadros_com_interferencia=bad,
                    pior=dict(volume_mm3=vol)))

class E36(unittest.TestCase):
    def test_interference_overrides_success(self):
        r=classificar(qa())
        self.assertEqual(r["estado_execucao"],"PASS")
        self.assertEqual(r["estado"],"REPROVADO_INTERFERENCIA_BREP")
        self.assertEqual(r["validacao_externa"],"SEM_REFERENCIA")
        self.assertFalse(r["liberado_para_publicacao"])

    def test_no_interference_is_sample_only(self):
        r=classificar(qa(bad=0,vol=0))
        self.assertEqual(r["verificacao_contato"],"SEM_INTERFERENCIA_BREP_NA_AMOSTRA")
        self.assertEqual(r["estado"],"SEM_REFERENCIA_EXTERNA")

    def test_inconsistent_audit_blocked(self):
        for q in (qa(n=0),qa(bad=0),qa(bad=121),qa(vol=float("nan"))):
            self.assertEqual(classificar(q)["estado"],"BLOQUEADO_AUDITORIA_CONTATO")
