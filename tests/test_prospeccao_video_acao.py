"""Fontes reais independentes; segurança do pipeline sem rede ou bytes inventados."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from src.v4.formatos import prospeccao_video_acao as A

BASE=Path(__file__).resolve().parents[1]/"docs/v4/formatos"


def fontes():
    return json.loads((BASE/"CANDIDATOS_VIDEO_ACAO_REAL_20261120.json").read_text())


def test_dois_processos_sem_empresa_ou_renderer_escolhidos():
    x=fontes()
    assert x["publicar"] is False
    assert {it["dominio"] for it in x["video_fontes"]}=={"usinagem","encadernacao"}
    assert {it["original_licenca"] for it in x["video_fontes"]}=={"CC BY 3.0","CC BY-SA 4.0"}
    for it in x["video_fontes"]:
        A.validar_fonte(it)
        assert "asset" not in it and "renderer" not in it


def test_sha_declarado_nao_equivale_a_arquivo_verificado():
    f=fontes()["video_fontes"][0]
    with pytest.raises(ValueError,match="TAMANHO"):
        A.verificar_bytes(b"short",f)
    fabricated=b"x"*f["expected_bytes"]
    with pytest.raises(ValueError,match="SHA"):
        A.verificar_bytes(fabricated,f)


def test_hash_e_bytes_so_se_promovem_depois_de_lidos(tmp_path):
    f=copy.deepcopy(fontes()["video_fontes"][0])
    b=b"a"*67_000
    f["expected_bytes"]=len(b)
    f["expected_sha1"]=hashlib.sha1(b).hexdigest()
    got=A.baixar_original(f,tmp_path/"stage/verified.webm",
                         reader=lambda _url:b)
    assert got["sha256"]==hashlib.sha256(b).hexdigest()
    assert (tmp_path/"stage/verified.webm").read_bytes()==b
    assert "ORIGINAL" in got["integridade"]


def test_redirecionamentos_e_sites_forjados_bloqueados():
    f=fontes()["video_fontes"][0]
    for url in ("http://upload.wikimedia.org/wikipedia/commons/x.webm",
                "https://upload.wikimedia.org.attacker.net/wikipedia/commons/x.webm",
                "https://upload.wikimedia.org/wikipedia/commons/a.webm?redirect=1",
                "https://evil.org/x.webm"):
        x=copy.deepcopy(f);x["uri"]=url
        with pytest.raises(ValueError,match="URL"):
            A.validar_fonte(x)


def test_status_de_licenca_comercial_nunca_pode_ser_inventado():
    f=copy.deepcopy(fontes()["video_fontes"][0])
    f["status_licenca"]="APROVADA_PUBLICACAO"
    with pytest.raises(ValueError,match="DIREITOS"):
        A.validar_fonte(f)
    f=copy.deepcopy(fontes()["video_fontes"][0]);f["original_licenca"]="All rights reserved"
    with pytest.raises(ValueError,match="LICENCA"):
        A.validar_fonte(f)


def test_janela_que_ultrapassa_original_falha_antes_da_imagem(tmp_path):
    f=copy.deepcopy(fontes()["video_fontes"][0])
    f["janela_candidata"]={"inicio_s":9,"duracao_s":6}
    with pytest.raises(ValueError,match="FIM"):
        A.contato(tmp_path/"inexistente",f,tmp_path/"contato.jpg",
                  {"largura":1280,"altura":720,"duracao_s":10.269})


def test_processo_nao_e_comprovado_so_porque_pixels_mudaram():
    f=fontes()["video_fontes"][0]
    assert f["processo_declarado"]=="usinagem de peça em torno CNC"
    assert f.get("acao_comprovada") is not True
    assert f.get("publicar") is not True
