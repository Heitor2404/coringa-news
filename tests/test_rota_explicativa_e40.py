import unittest
from src.v4.formatos.rota_explicativa_e40 import planejar as _planejar

def planejar(c,exige_contorno_industrial=False):
    return _planejar(c,exige_contorno_industrial,alvo="alvo-de-teste")

def base(tipo):
    return dict(tipo=tipo,alvo="alvo-de-teste",identidade_verificada=True,fonte_sha256="a"*64,
                fonte_url="https://example.org/source",licenca_candidata="permissiva",
                juntas_fundamentadas=True,movimento_fundamentado=True)

def cad():
    return dict(base("cad_real"),estado="VALIDADO_TECNICAMENTE_SEM_HOMOLOGACAO_VISUAL",
                verificacao_contato="SEM_INTERFERENCIA_BREP_NA_AMOSTRA",sobreposicao_inicial_fonte=False)

def plano():
    return dict(base("esquema_cinematico_2d"),apenas_principio=True,solver_verificado=True)

class E40(unittest.TestCase):
    def test_valid_cad_preferred(self):
        r=planejar([plano(),cad()])
        self.assertEqual(r["decisao"]["indice"],1)
        self.assertFalse(r["publish"])

    def test_failed_cad_not_laundered(self):
        c=cad();c["estado"]="REPROVADO_INTERFERENCIA_BREP"
        r=planejar([c,plano()])
        self.assertEqual(r["decisao"]["tipo"],"esquema_cinematico_2d")
        self.assertEqual(r["candidatos"][0]["status"],"CAD_SEM_VALIDACAO_TECNICA")
        self.assertIsNone(planejar([c])["decisao"])

    def test_contour_required(self):
        self.assertIsNone(planejar([plano()],True)["decisao"])

    def test_parametric_requires_dimensions(self):
        p=dict(plano(),tipo="parametrico_fundamentado")
        self.assertIsNone(planejar([p])["decisao"])
        p["dimensoes_fundamentadas"]=True
        self.assertEqual(planejar([plano(),p])["decisao"]["indice"],1)

    def test_missing_rights_or_evidence(self):
        p=plano();p["licenca_candidata"]="sem_licenca"
        self.assertIsNone(planejar([p])["decisao"])
        p=plano();p["juntas_fundamentadas"]=False
        self.assertIsNone(planejar([p])["decisao"])

    def test_no_source_hash(self):
        p=plano();p["fonte_sha256"]="not-verified"
        self.assertIsNone(planejar([p])["decisao"])


    def test_different_mechanism_never_fallback(self):
        p=plano();p["alvo"]="outro-mecanismo"
        c=cad();c["estado"]="REPROVADO_INTERFERENCIA_BREP"
        r=planejar([c,p])
        self.assertIsNone(r["decisao"])
        self.assertEqual(r["candidatos"][1]["status"],"ALVO_DIFERENTE_OU_NAO_IDENTIFICADO")
