"""Regressão da prova de 19s: um ciclo visível, sem omitir etapas."""
import json
from pathlib import Path
from src.v4.formatos.filme_editorial import avaliar

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"docs/v4/formatos/filme_panama_ciclo_19s.json"
ORDER=("enter","seal","valves","rise","equalize","open","exit")

def plano():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_piloto_19s_cobre_ciclo_completo_e_preserva_filmagem_real():
    p=plano()
    qa=avaliar(p)
    assert qa["pronto"], qa["bloqueios"]
    assert p["tipo"]=="PROVA_VISUAL_PRIVADA"
    assert abs(p["duracao"]-19.0)<1e-9
    assert p["shots"][0]["type"]=="video"
    assert p["shots"][1]["mechanism"]=="lock_cycle"
    assert p["shots"][1]["end"]-p["shots"][1]["start"]>=17
    assert tuple(x["action"] for x in p["shots"][1]["cues"])==ORDER
    assert p["shots"][1]["reference_asset"]==p["shots"][0]["asset"]
    assert abs(p["shots"][1]["reference_from_seconds"]-
               (p["shots"][0]["source_in_seconds"]+p["shots"][0]["end"]))<0.001
    assert qa["visual_approval"]=="NAO_FOI_AVALIADO"

def test_valvulas_nao_podem_abrir_depois_da_subida():
    p=plano()
    p["shots"][1]["cues"][2]["action"]="rise"
    p["shots"][1]["cues"][3]["action"]="valves"
    assert "F-MECANISMO-CAUSAL" in {x["codigo"] for x in avaliar(p)["bloqueios"]}

def test_pulando_entrada_nao_pode_passar():
    p=plano()
    del p["shots"][1]["cues"][0]
    assert "F-MECANISMO-CAUSAL" in {x["codigo"] for x in avaliar(p)["bloqueios"]}

def test_agua_precisa_tempo_para_subir():
    p=plano()
    p["shots"][1]["cues"][4]["at"]=8.0
    assert "F-CICLO-INCOMPLETO" in {x["codigo"] for x in avaliar(p)["bloqueios"]}

def test_saida_precisa_acontecer_depois_da_abertura():
    p=plano()
    p["shots"][1]["cues"][6]["at"]=14.5
    assert "F-CICLO-INCOMPLETO" in {x["codigo"] for x in avaliar(p)["bloqueios"]}

def test_nao_pode_rotular_ilustracao_como_video_real():
    p=plano()
    p["shots"][1]["evidence"]="literal"
    p["shots"][1]["literal_identity"]="Filmagem real da comporta"
    assert "F-MECANISMO-NÃO-IDENTIFICADO" in {x["codigo"] for x in avaliar(p)["bloqueios"]}

def test_7_8s_antigo_continua_compativel():
    p=json.loads((ROOT/"docs/v4/formatos/filme_panama_8s_causal.json").read_text())
    assert avaliar(p)["pronto"]
