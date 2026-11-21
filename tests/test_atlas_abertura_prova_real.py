"""ATLAS V2: gancho fisico opcional com foto/video real, preservando V1 map-first.

Testes de contrato, sem IA/Telegram/URLs externas e sem alterar o plano aprovado.
"""
import copy
import json
from pathlib import Path

from src.v4.formatos import plano as P


ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "tests/dados/formatos_atlas_resolvido.json").read_text())


def _regras(pl, imgs=None):
    resolvido = P.resolver_tempos(copy.deepcopy(pl), [])
    return {x["regra"] for x in P.validar(resolvido, imgs) if x["gravidade"] == "erro"}


def _foto():
    pl = copy.deepcopy(BASE)
    pl["abertura_tipo"] = "prova_real"
    pl["beats"][0]["composicao"] = "atlas.prova"
    pl["beats"][0]["camadas"] = [{
        "id": "foto-corroborada", "componente": "atlas.provaVisual", "slot": "prova",
        "t0": 0, "t1": 2.9,
        "p": {"asset": "teste:foto", "meta": "Crédito factual · CC BY 4.0",
              "rotulo": "Instalação real"}
    }]
    # Fotografia narrativa abre e o próximo beat mostra a consequência geográfica.
    pl["beats"][1]["t"] = 2.9
    return pl


def _video():
    pl = copy.deepcopy(BASE)
    pl["abertura_tipo"] = "prova_real"
    pl["beats"][0]["camadas"] = []  # MP4 substitui totalmente o palco no gancho
    pl["clipes"].insert(0, {
        "t0": 0, "t1": 2.9, "componente": "registro.video",
        "params": {"asset": "teste:video", "inicio": 0}
    })
    return pl


def _imagens(tipo="foto", conferido=True):
    return {
        "teste:foto": {"tipo": tipo, "origem_conferida": conferido, "sha256_origem": "a" * 64,
                       "credito": "Autor · CC BY 4.0", "licenca": "CC BY 4.0",
                       "w": 1920, "h": 1080},
        "teste:video": {"tipo": "video", "origem_conferida": conferido,
                        "sha256_origem": "b" * 64,
                        "credito": "Autor · CC BY 4.0", "licenca": "CC BY 4.0",
                        "w": 1080, "h": 1920, "duracao": 10}
    }


def test_v1_sem_flag_permanece_map_first():
    assert "F-GANCHO-MAPA-PRIMEIRO" not in _regras(BASE)
    pl = copy.deepcopy(BASE)
    pl["clipes"].append({"t0": 0, "t1": 2.9, "componente": "registro.video",
                         "params": {"asset": "teste:video", "inicio": 0}})
    assert "F-GANCHO-MAPA-PRIMEIRO" in _regras(pl)


def test_prova_fotografica_permitida_quando_verificada():
    regras = _regras(_foto(), _imagens())
    assert "F-GANCHO-PROVA-REAL" not in regras
    assert "F-GANCHO-ORIGEM" not in regras
    assert "F-GANCHO-MAPA-PRIMEIRO" not in regras


def test_prova_video_permitida_quando_verificada():
    regras = _regras(_video(), _imagens())
    assert "F-GANCHO-PROVA-REAL" not in regras
    assert "F-GANCHO-ORIGEM" not in regras
    assert "F-GANCHO-MAPA-PRIMEIRO" not in regras
    assert "F-VIDEO-SOBREPOE-CAMADA" not in regras


def test_video_ou_foto_sem_sha_e_credito_bloqueia():
    for pl in (_foto(), _video()):
        for corretos in (False, True):
            im = _imagens(conferido=corretos)
            if corretos:
                chave = "teste:foto" if pl["beats"][0]["composicao"] == "atlas.prova" else "teste:video"
                im[chave]["sha256_origem"] = ""
            assert "F-GANCHO-ORIGEM" in _regras(pl, im)


def test_gancho_nao_aceita_animacao_fingindo_filmagem():
    pl = _video()
    pl["clipes"][0]["componente"] = "mecanismo.eclusa"
    assert "F-GANCHO-PROVA-REAL" in _regras(pl, _imagens())


def test_primeira_prova_incompleta_bloqueia():
    pl = _foto()
    pl["beats"][0]["camadas"][0]["t1"] = 1.0
    assert "F-GANCHO-PROVA-REAL" in _regras(pl, _imagens())
    pl = _video()
    pl["clipes"][0]["t0"] = 1
    assert "F-GANCHO-PROVA-REAL" in _regras(pl, _imagens())


def test_modo_invalido_nao_desliga_protecao():
    pl = copy.deepcopy(BASE)
    pl["abertura_tipo"] = "qualquer_coisa"
    assert "F-GANCHO-TIPO" in _regras(pl)
