"""F9 — testes offline do ingestor de evidência de referência externa."""
from __future__ import annotations
import copy
import hashlib
import io
import json
from pathlib import Path

import pytest
from PIL import Image

from src.v4.formatos import referencia_evidencia_f9 as F

@pytest.fixture
def ref():
    return F.carregar()

@pytest.fixture
def jpeg():
    image=Image.new("RGB",(2100,1500),"#789eaf")
    out=io.BytesIO()
    image.save(out,format="JPEG",quality=87)
    return out.getvalue()


def test_referencia_registra_fonte_licenca_escopo_sem_engano(ref):
    got=F.validar(ref)
    assert got["visible_parts"]==8
    assert got["hidden_parts"]==4
    assert got["published"] is False
    assert "belt_guard" in [x["role"] for x in ref["claims"]["visible_parts"]]
    assert "drive_belt" in ref["claims"]["hidden_parts"]
    assert ref["reference_type"]=="ilustracao_tecnica_estatica_nao_fotografia"
    assert ref["rights_and_gates"]["publication_allowed"] is False


@pytest.mark.parametrize("field,value,code",[
    ("license","CC0","PROVENIENCIA"),
    ("license_url","https://creativecommons.org/publicdomain/zero/1.0/","PROVENIENCIA"),
    ("file_url","https://example.com/evil.jpg","PROVENIENCIA"),
    ("file_url","http://upload.wikimedia.org/wikipedia/commons/1/19/x.jpg","PROVENIENCIA"),
    ("file_url","https://upload.wikimedia.org/wikipedia/commons/1/19/x.jpg?next=evil","PROVENIENCIA"),
    ("file_url","https://upload.wikimedia.org.evil.com/wikipedia/commons/1/19/x.jpg","PROVENIENCIA"),
    ("page","https://fake-commons.wikimedia.org/wiki/File:evil.jpg","PROVENIENCIA"),
])
def test_fonte_e_licenca_nao_sao_inferidas(ref,field,value,code):
    candidate=copy.deepcopy(ref)
    candidate["source"][field]=value
    with pytest.raises(ValueError,match="F9-REFERENCIA-"+code):
        F.validar(candidate)


def test_manifesto_rejeita_publicacao_mascarada(ref):
    for key,val in [
        ("publication_allowed",True),
        ("automatic_geometry_extraction",True),
        ("commercial_use_review_pending",False),
        ("visual_approval",True),
        ("derivative_obligations_review_pending",False),
    ]:
        candidate=copy.deepcopy(ref)
        candidate["rights_and_gates"][key]=val
        with pytest.raises(ValueError,match="F9-REFERENCIA-PUBLICACAO"):
            F.validar(candidate)


def test_rejeita_bboxes_impossiveis_ou_atores_ocultos(ref):
    changed=copy.deepcopy(ref)
    changed["claims"]["visible_parts"][0]["bbox"]=[.8,.2,.5,.4]
    with pytest.raises(ValueError,match="F9-REFERENCIA-BBOX"):
        F.validar(changed)
    changed=copy.deepcopy(ref)
    changed["claims"]["hidden_parts"].append("receiver_horizontal")
    with pytest.raises(ValueError,match="F9-REFERENCIA-"):
        F.validar(changed)


def test_bytes_jpeg_sem_pin_sao_candidatos_e_pin_correto_e_obrigatorio(ref,jpeg):
    res=F.conferir_bytes(ref,jpeg)
    assert len(res["original_sha256"])==64
    assert res["sha_pinned_and_verified"] is False
    with pytest.raises(ValueError,match="F9-REFERENCIA-SHA-NAO-FIXADO"):
        F.conferir_bytes(ref,jpeg,exigir_pin=True)
    candidate=copy.deepcopy(ref)
    candidate["file"]["expected_sha256"]=hashlib.sha256(jpeg).hexdigest()
    assert F.conferir_bytes(candidate,jpeg,exigir_pin=True)["sha_pinned_and_verified"] is True
    with pytest.raises(ValueError,match="F9-REFERENCIA-SHA-DIVERGENTE"):
        F.conferir_bytes(candidate,jpeg+b"changed bytes",exigir_pin=True)
    with pytest.raises(ValueError,match="F9-REFERENCIA-JPEG"):
        F.conferir_bytes(candidate,b"hello world"*3000)


def test_sem_fallback_em_redirect_ou_content_type(ref,jpeg):
    class Resp:
        status_code=200
        is_redirect=False
        headers={"Content-Type":"image/jpeg"}
        content=jpeg
        def raise_for_status(self):
            return None
    assert F.adquirir(ref,get=lambda *a,**kw: Resp())==jpeg
    class Wrong(Resp):
        headers={"Content-Type":"text/html"}
    with pytest.raises(ValueError,match="F9-REFERENCIA-CONTENT-TYPE"):
        F.adquirir(ref,get=lambda *a,**kw: Wrong())
    class Redirect(Resp):
        status_code=302
        is_redirect=True
    with pytest.raises(ValueError,match="F9-REFERENCIA-HTTP-REDIRECT"):
        F.adquirir(ref,get=lambda *a,**kw: Redirect())


def test_prancha_com_desenho_do_compressor_real_e_atribuicao(ref,jpeg,tmp_path):
    report=F.gerar(ref,jpeg,tmp_path,animar=False)
    assert report["physics_simulated_from_external_image"] is False
    assert report["identity_homologated"] is False
    assert report["publication_allowed"] is False
    assert report["hidden_unverified_roles"]==ref["claims"]["hidden_parts"]
    assert "Brian S. Elliott" in report["credit"]
    assert "CC BY-SA 4.0" in report["license"]
    path=tmp_path/"CONTATO_REFERENCIA_VS_COMPRESSOR_REAL_F9.jpg"
    assert path.is_file()
    with Image.open(path) as image:
        assert image.size==(1530,1050)
    assert (tmp_path/"BBOX_CANDIDATAS_MANUAIS_NAO_VLM.jpg").is_file()
    assert (tmp_path/"RELATORIO_REFERENCIA_F9.json").is_file()
    assert not list(tmp_path.glob("*.mp4"))


def test_sem_sha_vetado_video_animado(ref,jpeg,tmp_path):
    with pytest.raises(ValueError,match="F9-REFERENCIA-SHA-NAO-FIXADO"):
        F.gerar(ref,jpeg,tmp_path,animar=True)
