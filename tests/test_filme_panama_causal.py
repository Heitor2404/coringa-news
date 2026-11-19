"""Prova causal curta de eclusa — estrutura e causalidade, NÃO aprovação estética."""
import copy
import json
from pathlib import Path
from src.v4.formatos.filme_editorial import avaliar

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/v4/formatos/filme_panama_8s_causal.json"

def _plano():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_dois_planos_e_cinco_estados_reais_do_esquema():
    p = _plano()
    r = avaliar(p)
    assert r["pronto"], r["bloqueios"]
    assert r["visual_approval"] == "NAO_FOI_AVALIADO"
    assert len(p["shots"]) == 2
    assert [c["type"] for c in p["shots"]] == ["video", "mechanism"]
    assert [c["action"] for c in p["shots"][1]["cues"]] == [
        "closed", "water_enter", "rise", "equalize", "release"]
    assert r["momentos_visuais"] >= 4
    assert p["media"]["eclusa-hero-hd"]["expected_sha256"] == (
        "3d21204dc0ff2b45298b341b102f0175f32a8c4838dbed7de4efb24cece5b38d")

def test_ordem_causal_nao_pode_ser_invertida():
    p = _plano()
    p["shots"][1]["cues"][3], p["shots"][1]["cues"][4] = (
        p["shots"][1]["cues"][4],p["shots"][1]["cues"][3])
    r = avaliar(p)
    assert "F-MECANISMO-CAUSAL" in {b["codigo"] for b in r["bloqueios"]}

def test_evento_de_agua_ou_de_igualdade_nao_pode_sumir():
    p = _plano()
    del p["shots"][1]["cues"][1]
    assert "F-MECANISMO-CAUSAL" in {b["codigo"] for b in avaliar(p)["bloqueios"]}

def test_simulacao_nao_pode_ser_vendida_como_registro_real():
    p = _plano()
    p["shots"][1]["evidence"] = "literal"
    p["shots"][1]["literal_identity"] = "registro real"
    assert "F-MECANISMO-NÃO-IDENTIFICADO" in {b["codigo"] for b in avaliar(p)["bloqueios"]}

def test_cena_curta_nao_permite_enrolacao_sem_estados():
    p = _plano()
    p["shots"][1]["end"] = 10.4
    p["duracao"] = 10.4
    assert "F-PLANO-SEM-DIRECAO" in {b["codigo"] for b in avaliar(p)["bloqueios"]}

def test_plano_existente_v5_continua_valido():
    p = json.loads((ROOT / "docs/v4/formatos/filme_panama_12s_prova.json").read_text())
    assert avaliar(p)["pronto"]

def test_ponte_visual_exige_mesmo_arquivo_e_tempo_continuo():
    p = _plano()
    assert p["shots"][1]["reference_asset"] == p["shots"][0]["asset"]
    assert abs(p["shots"][1]["reference_from_seconds"] - 6.8) < .001
    p["shots"][1]["reference_from_seconds"] = 2.0
    assert "F-PONTE-REAL" in {b["codigo"] for b in avaliar(p)["bloqueios"]}
