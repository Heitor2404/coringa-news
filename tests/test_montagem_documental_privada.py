"""Permitir mídia institucional REAL apenas em montagem privada, sem liberar direitos.

O mesmo compositor e ffprobe são usados no filme final. Nenhum destes
testes chama Gemini, publica ou presume licença de material NIST.
"""
import copy
import hashlib
import io
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from src.v4.formatos import filme_editorial as F

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/v4/formatos/filme_taiwan_prova.json"
VIDEO=ROOT/"tests/midia/video_horizontal_navio.mp4"


def plano(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source=Path("stage_documental/nist/testemunho.mp4")
    source.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(VIDEO,source)
    p=json.loads(BASE.read_text(encoding="utf8"))
    p["publicar"]=False
    s=p["shots"][0]
    s["type"]="video"
    s["source_in_seconds"]=0
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    p["media"][s["asset"]]={
        "local_source":str(source),
        "url":"https://www.nist.gov/video/inside-instrument-nist-center-nanoscale-science",
        "page":"https://www.nist.gov/video/inside-instrument-nist-center-nanoscale-science",
        "credit":"NIST · fonte institucional ainda não homologada",
        "license":"REVIEW_PENDING",
        "rights_status":"REVIEW_PENDING",
        "media_type":"video",
        "expected_sha256":sha,
        "width":1280,"height":720,
    }
    return p,source


def fotografo(url):
    im=Image.new("RGB",(820,820),(40,80,120))
    out=io.BytesIO();im.save(out,"JPEG");return out.getvalue()


def test_privado_verifica_bytes_e_marca_direitos_pendentes(tmp_path,monkeypatch):
    p,src=plano(tmp_path,monkeypatch)
    assert F.avaliar(p)["pronto"]
    r=F.preparar(p,Path("saida"),Path("public"),downloader=fotografo)
    assert r["pronto"]
    props=json.loads(Path("saida/props.json").read_text())
    assert props["private_review_only"] is True
    assert props["direitos_pendentes"]==["chip-macro"]
    assert props["shots"][0]["type"]=="video"
    assert Path("public",props["shots"][0]["asset"]).read_bytes()==src.read_bytes()


def test_filme_final_rejeita_candidato_nao_aprovado(tmp_path,monkeypatch):
    p,_=plano(tmp_path,monkeypatch)
    p["tipo"]="FILME_FINAL"
    codes={e["codigo"] for e in F.avaliar(p)["bloqueios"]}
    assert "F-FIXTURE-NAO-AUTORIZADA" in codes
    assert "F-LICENCA" in codes
    assert "F-PORTAO-INTEGRAL-AUSENTE" in codes


def test_previas_sem_publicar_explicito_nao_aceitam_candidatos(tmp_path,monkeypatch):
    p,_=plano(tmp_path,monkeypatch)
    p.pop("publicar")
    codes={e["codigo"] for e in F.avaliar(p)["bloqueios"]}
    assert "F-FIXTURE-NAO-AUTORIZADA" in codes
    assert "F-LICENCA" in codes


def test_original_alterado_nao_entra_no_compositor(tmp_path,monkeypatch):
    p,src=plano(tmp_path,monkeypatch)
    src.write_bytes(src.read_bytes()+b"MODIFICADO")
    with pytest.raises(ValueError,match="hash da origem mudou"):
        F.preparar(p,Path("saida"),Path("public"),downloader=fotografo)


def test_fonte_externa_em_stage_nao_e_homologada_so_por_hash(tmp_path,monkeypatch):
    p,_=plano(tmp_path,monkeypatch)
    p["media"]["chip-macro"]["page"]="https://site-fora.example/video"
    codes={e["codigo"] for e in F.avaliar(p)["bloqueios"]}
    assert "F-FIXTURE-NAO-AUTORIZADA" in codes
    assert "F-LICENCA" in codes


def test_nist_candidato_nao_e_fonte_tsmc_literal(tmp_path,monkeypatch):
    p,_=plano(tmp_path,monkeypatch)
    p["shots"][0]["evidence"]="literal"
    p["shots"][0]["literal_identity"]="TSMC Taiwan gravada no mesmo vídeo"
    # Campo literal_identity é CONTESTÁVEL por curadoria; o contrato de
    # substituição factual será verificado no gate final. O privado não
    # libera a imagem institucional para publicar.
    props=F.avaliar(p)
    assert props["visual_approval"]=="NAO_FOI_AVALIADO"
    assert p["media"]["chip-macro"]["license"]=="REVIEW_PENDING"
