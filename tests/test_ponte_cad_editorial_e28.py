import unittest
from copy import deepcopy
from src.v4.formatos.ponte_cad_editorial_e28 import props


def fixture():
    stage=dict(schema="coringa.palco.cad.v1",publish=False,direitos_publicacao="NAO_AVALIADOS",
               homologacao_visual="NAO_HOMOLOGADO",tipo_evidencia="representacao_tecnica",
               quadros=31,fps=30,dimensoes=[1080,1920],sha256="a"*64,
               credito="Fixture",licenca_informada="fixture",natureza="sintetico",
               fonte={"url":"fixture"},verificacao_video={"quadros":31,"pico_pixels_mudados":301})
    ev=dict(schema="coringa.eventos.trajetoria.v1",interpretacao_causal="NAO_INFERIDA",
            quadros=31,fps=30,duracao_s=31/30,medida={"rotulo":"Abertura"},
            fases=[dict(tipo="aumenta",frame_inicio=0,frame_fim=15,tempo_inicio_s=0,
                        tempo_fim_s=.5,delta_mm=10),
                   dict(tipo="diminui",frame_inicio=15,frame_fim=30,tempo_inicio_s=.5,
                        tempo_fim_s=1,delta_mm=-10)])
    return dict(publish=False,visual_approved=False,palco_cad=stage,eventos_trajetoria=ev)


class E28(unittest.TestCase):
    def setUp(self):
        self.asset="cad_e28/"+"a"*64+".mp4"

    def test_private_and_cues(self):
        p=props(fixture(),self.asset)
        self.assertTrue(p["private_review_only"])
        self.assertTrue(p["preview"])
        self.assertEqual(p["shots"][0]["type"],"cad_preview")
        self.assertEqual(p["shots"][0]["evidence"],"explainer")
        self.assertEqual(p["shots"][0]["cues"][1]["at"],.5)

    def test_reject_publish(self):
        q=fixture(); q["publish"]=True
        with self.assertRaisesRegex(ValueError,"PRIVADO"):
            props(q,self.asset)

    def test_reject_clock(self):
        q=fixture(); q["palco_cad"]["fps"]=24
        with self.assertRaisesRegex(ValueError,"RELOGIO"):
            props(q,self.asset)

    def test_reject_missing_rights_status(self):
        q=fixture(); del q["palco_cad"]["direitos_publicacao"]
        with self.assertRaisesRegex(ValueError,"PRIVADO"):
            props(q,self.asset)

    def test_reject_bad_event(self):
        q=fixture(); q["eventos_trajetoria"]["fases"][1]["frame_inicio"]=16
        with self.assertRaisesRegex(ValueError,"EVENTO"):
            props(q,self.asset)

    def test_reject_asset_hash(self):
        with self.assertRaisesRegex(ValueError,"HASH_ASSET"):
            props(fixture(),"cad_e28/"+"b"*64+".mp4")
