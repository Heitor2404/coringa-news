"""Duração do PLANO acompanha acontecimento real, nunca zoom decorativo ou meta comercial.

Testes sintéticos de contrato e sincronização. NÃO provam que os quadros
mostram a ação alegada nem substituem a revisão visual do MP4.
"""
import copy
import json
from pathlib import Path

import pytest
from src.v4.formatos import tempo_natural
from src.v4.formatos.filme_editorial import avaliar

ROOT = Path(__file__).resolve().parents[1]
PROVA = ROOT / "docs/v4/formatos/filme_taiwan_prova.json"


def progressao(ini=12.0, sha="c"*64):
    return {
        "tipo":"acao_observada", "sha256_origem":sha,
        "inspecao":"Anotação de quadros reais por curador; ainda exige aprovação humana do filme",
        "eventos":[
            {"at":0.8,"fonte_s":ini+.8,"acao_visivel":"trabalhador abre a máquina"},
            {"at":3.2,"fonte_s":ini+3.2,"acao_visivel":"suporte avança para o interior"},
            {"at":6.4,"fonte_s":ini+6.4,"acao_visivel":"porta da câmara é fechada"},
            {"at":9.0,"fonte_s":ini+9.0,"acao_visivel":"equipamento muda de estado"},
        ],
    }


def montar():
    p=json.loads(PROVA.read_text(encoding="utf8"))
    s=p["shots"][0]
    s.update(type="video",asset="acao-motor",source_in_seconds=12.0,
             progressao_visual=progressao())
    dif=10.0-s["end"]
    s["end"]=10.0
    for e in p["shots"][1:]:
        e["start"]=round(e["start"]+dif,3)
        e["end"]=round(e["end"]+dif,3)
    p["duracao"]=round(p["duracao"]+dif,3)
    p["media"]["acao-motor"]={
        "url":"https://upload.wikimedia.org/wikipedia/commons/a/ab/acao.mp4",
        "page":"https://commons.wikimedia.org/wiki/File:acao.mp4",
        "credit":"Fonte licenciada submetida a revisão",
        "license":"CC BY 4.0",
        "media_type":"video","expected_sha256":"c"*64,
    }
    return p


def codigos(r):
    return {x["codigo"] for x in r["bloqueios"]}


def test_mesmo_montador_aceita_dez_segundos_com_acoes_distintas():
    p=montar()
    r=avaliar(p)
    assert r["pronto"],r["bloqueios"]
    assert "F-VIDEO-SEM-PROGRESSAO-COMPROVADA" not in codigos(r)
    assert p["duracao"]>16  # história se alonga junto com a cena
    assert r["visual_approval"]=="NAO_FOI_AVALIADO"


@pytest.mark.parametrize("tema",["industria", "engenharia", "historia", "geografia"])
def test_contrato_ritmo_e_igual_em_qualquer_assunto(tema):
    p=montar()
    p["titulo"]=tema
    p["shots"][0]["headline"]=f"UM PROCESSO CONTÍNUO · {tema}"
    assert avaliar(p)["pronto"]


def test_video_longo_sem_inspecao_e_bloqueado_antes_de_render():
    p=montar()
    p["shots"][0].pop("progressao_visual")
    r=avaliar(p)
    assert "F-VIDEO-SEM-PROGRESSAO-COMPROVADA" in codigos(r)
    assert not r["pronto"]


def test_uma_panoramica_ou_label_nao_comprovam_acao():
    p=montar()
    p["shots"][0]["progressao_visual"]["tipo"]="camera_pan"
    assert "F-VIDEO-SEM-PROGRESSAO-COMPROVADA" in codigos(avaliar(p))


def test_fonte_trocada_nao_continua_sendo_a_mesma_acao():
    p=montar()
    p["media"]["acao-motor"]["expected_sha256"]="d"*64
    assert "F-VIDEO-SEM-PROGRESSAO-COMPROVADA" in codigos(avaliar(p))


def test_eventos_de_outro_trecho_nao_valem_e_lacuna_sem_progresso_bloqueia():
    p=montar()
    p["shots"][0]["progressao_visual"]["eventos"][1]["fonte_s"]=200
    assert "F-VIDEO-SEM-PROGRESSAO-COMPROVADA" in codigos(avaliar(p))
    p=montar()
    p["shots"][0]["progressao_visual"]["eventos"][1]["at"]=7.0
    assert "F-VIDEO-SEM-PROGRESSAO-COMPROVADA" in codigos(avaliar(p))


def test_video_sem_acao_nao_pode_ter_voz_longa():
    p=montar()
    p["shots"][0].pop("progressao_visual")
    p["shots"]=p["shots"][:1]
    with pytest.raises(ValueError,match="falta progressão"):
        tempo_natural.retemporizar(p,[9.76])


def test_voz_natural_de_mais_de_nove_segundos_preserva_velocidade():
    p=montar()
    p["shots"]=p["shots"][:1]
    r=tempo_natural.retemporizar(p,[9.76])
    assert r["duracao"]==10.0
    assert r["shots"][0]["voice_tempo"]==1
    assert r["shots"][0]["start"]==0
    assert r["sincronia_voz"]["tempo_audio"]==1.0
    assert r["sincronia_voz"]["estetica_aprovada"] is False


def test_foto_nao_ganha_dez_segundos_por_declarar_marcadores():
    p=montar()
    p["shots"][0]["type"]="photo"
    r=avaliar(p)
    assert "F-PLANO-SEM-DIRECAO" in codigos(r)
    p["shots"]=p["shots"][:1]
    with pytest.raises(ValueError,match="somente vídeo real"):
        tempo_natural.retemporizar(p,[9.76])


def test_breve_video_continua_funcionando_sem_burocracia():
    p=json.loads(PROVA.read_text(encoding="utf8"))
    s=p["shots"][0]
    s["type"]="video"
    assert tempo_natural.validar_progressao_video(s,2.6)==[]
