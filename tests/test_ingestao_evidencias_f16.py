"""F16 — evidência textual não pode ser confundida com rig recuperado de imagem."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.v4.formatos import ingestao_evidencias_f16 as E
from src.v4.formatos import compilador_topologia_f15 as F15

ROOT=Path(__file__).resolve().parents[1]/"src/v4/formatos/evidencias_f16"

def load(name):
    return E.load_document(ROOT/(name+".json"))

def fixture_page(doc):
    # Cenário de TESTE, não snapshot coletado em tempo real.
    return "Research page: \n" + "  ".join(x["text"] for x in doc["quoted_spans"])+"."

@pytest.mark.parametrize("name,expected",[
    ("par_engrenagens_educacional","known_spur_pair"),
    ("biela_cinematica_parcial","partial_slider_crank"),
    ("plataforma_tesoura_hidraulica","hydraulic_scissor_lift_UNSUPPORTED"),
    ("plataforma_tesoura_fonte_alternativa","hydraulic_scissor_lift_UNSUPPORTED"),
])
def test_extrai_candidatos_de_trechos_presentes_no_html_nao_de_url(name,expected):
    d=load(name)
    report=E.audit(d,fixture_page(d),origin="fixture")
    assert report["candidate_graph"]["kind"]==expected
    assert report["source_live_verified"] is False
    assert report["source_retrieval"]=="TEXT_FIXTURE_NOT_LIVE"
    assert report["status"]=="BLOQUEADO_ORIGEM_NAO_COMPROVADA"
    assert report["f15_preflight_passed"] is False
    assert report["publication_allowed"] is False
    assert report["human_review_required"] is True
    assert len(report["verified_anchors"])==3


def test_dominio_de_origem_e_propriedade_midia_nao_sao_inferidos():
    doc=load("par_engrenagens_educacional")
    for key,value in (
        ("url","https://192.168.0.1/"),
        ("url","http://mechanics.ju.se/MachineElements/spur-gears.html"),
        ("original_media_used",True),("image_license_claimed",True),
        ("publication_allowed",True),("extraction_requires_live_anchor_check",False),
        ("id","../../outro_local"),
    ):
        bad=copy.deepcopy(doc)
        bad[key]=value
        with pytest.raises(ValueError,match="F16-FONTE-CONTRATO"):
            E.validate_document(bad)
    with pytest.raises(ValueError,match="F16-FONTE-URL_NAO_AUTORIZADA"):
        E.fetch_html("https://localhost:8443/private")


def test_nao_aceita_fonte_sem_ancora_ou_modificada_e_nao_monta():
    doc=load("par_engrenagens_educacional")
    with pytest.raises(ValueError,match="F16-FONTE-ANCORA_AUSENTE"):
        E.audit(doc,"Unrelated marketing page about wonderful cars",origin="live")
    tampered=copy.deepcopy(doc)
    tampered["quoted_spans"][1]["text"]="The teeth turn clockwise forever."
    with pytest.raises(ValueError,match="F16-FONTE-ANCORA_AUSENTE_g2"):
        E.audit(tampered,fixture_page(doc),origin="live")
    r=E.audit(doc)
    assert r["candidate_graph"] is None
    assert r["status"]=="BLOQUEADO_SEM_HTML_DA_FONTE"
    assert not r["source_live_verified"]


def test_confirma_lista_de_spans_mas_nao_acha_fisica_oculta_por_alias():
    d=load("biela_cinematica_parcial")
    a=E.audit(d,fixture_page(d),origin="fixture")["candidate_graph"]
    assert len(a["nodes"])==4
    assert len(a["edges"])==3
    assert "belt_not_evidenced" in a["uncertainties"]
    assert not any(x["kind"]=="belt" for x in a["nodes"])
    assert not any(x["id"]=="motor_pulley" for x in a["nodes"])
    with pytest.raises(ValueError,match="F16-FONTE-PREVOO_SEM_PROVA_EXTERNA"):
        E.compile_gear_from_verified(E.audit(d,fixture_page(d),origin="live"),{})


def test_alternativa_hidraulica_mesma_topologia_mas_nunca_eh_kernel():
    d=load("plataforma_tesoura_fonte_alternativa")
    r=E.audit(d,fixture_page(d),origin="fixture")
    assert r["candidate_graph"]["kind"]=="hydraulic_scissor_lift_UNSUPPORTED"
    assert r["source_live_verified"] is False
    assert len(r["candidate_graph"]["edges"])==3
    assert r["publication_allowed"] is False


def test_eleva_tesoura_esta_documentada_mas_terceira_familia_nao_renderiza():
    d=load("plataforma_tesoura_hidraulica")
    r=E.audit(d,fixture_page(d),origin="live")
    assert r["source_live_verified"] is True  # APENAS fixture: esta chamada foi SIMULADA
    assert r["status"]=="BLOQUEADO_TOPOLOGIA_INCOMPLETA_OU_SEM_KERNEL"
    assert r["candidate_graph"]["kind"]=="hydraulic_scissor_lift_UNSUPPORTED"
    assert [x["kind"] for x in r["candidate_graph"]["nodes"]]==[
        "electric_motor","hydraulic_pump","hydraulic_cylinder","scissor_arms"]
    assert not r["f15_preflight_passed"]
    with pytest.raises(ValueError,match="F16-FONTE-PREVOO_SEM_PROVA_EXTERNA"):
        E.compile_gear_from_verified(r,{})


def test_plano_de_engrenagem_f15_so_apos_prova_de_citacao_e_parametros_manuais():
    d=load("par_engrenagens_educacional")
    spec=json.loads((ROOT/"especificacao_engrenagens_f16.json").read_text("utf8"))
    report=E.audit(d,fixture_page(d),origin="live") # Somente fixture, não comprova fonte externa.
    assert report["source_live_verified"]
    result=E.compile_gear_from_verified(report,spec)
    assert result["compiled_family"]=="external_spur_gear_reduction"
    assert result["title_used_for_dispatch"] is False
    assert result["publish"] is False and result["visual_approval"] is False
    assert report["status"]=="PREVOO_F15_OK_REVISAO_HUMANA_PENDENTE"
    assert report["manual_design_parameters_not_from_reference"] is True
    assert result["scene"]["gears"]["z1"]==20 and result["scene"]["gears"]["z2"]==40
    assert result["scene"]["publish"] is False
    with pytest.raises(ValueError,match="F16-FONTE-PREVOO_SEM_PROVA_EXTERNA"):
        E.compile_gear_from_verified(E.audit(d,fixture_page(d)),spec)
    # Alterar número de dentes não pode invocar nova evidência.
    invalid=copy.deepcopy(spec)
    invalid["parameters"]["z_output"]=999
    with pytest.raises(ValueError):
        E.compile_gear_from_verified(E.audit(d,fixture_page(d),origin="live"),invalid)


def test_no_texto_curto_nao_extrai_pressao_rpm_cad_ou_licenca():
    for name in ("par_engrenagens_educacional","biela_cinematica_parcial",
                 "plataforma_tesoura_hidraulica"):
        d=load(name)
        r=E.audit(d,fixture_page(d),origin="fixture")
        claims=r["candidate_graph"]
        assert "industrial_identity_verified" not in r
        assert "source_is_image_license" not in claims
        assert r["image_license_proven"] is False
        assert r["visual_media_used"] is False
        assert r["publication_allowed"] is False


def test_html_realista_parser_ignora_scripts_e_preserva_texto_util():
    doc=load("par_engrenagens_educacional")
    spans=fixture_page(doc)
    document=(
        "<html><head><script>spur gears forever</script></head><body>"
        "<h1>Technical Reference</h1><article><p>"+spans+
        "</p></article></body></html>"
    ).encode("utf8")
    text=E.page_text(document,"text/html")
    assert "spur gears forever" not in text
    assert "Technical Reference" in text
    assert len(E.verified_spans(doc,text))==3
    with pytest.raises(ValueError,match="F16-FONTE-TIPO"):
        E.page_text(b"%PDF-1.4"*10,"application/pdf")


def test_inferencia_depende_da_textualidade_nao_do_nome_do_arquivo():
    d=load("par_engrenagens_educacional")
    d["id"]="nome_que_parece_tesoura"
    result=E.audit(d,fixture_page(d),origin="fixture")
    assert result["candidate_graph"]["kind"]=="known_spur_pair"
    r=E.infer_graph([{"id":"x","text":"An unrelated sentence.", "locator":"none"}])
    assert r["kind"]=="evidence_not_decidable"
