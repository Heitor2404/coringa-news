"""F17: relation-level provenance, paraphrases, missing hydraulic kernel."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import pytest

from src.v4.formatos import ingestao_evidencias_f16 as F16
from src.v4.formatos import relacoes_com_evidencia_f17 as F17
from src.v4.formatos import compilador_topologia_f15 as F15

DOCS=Path(__file__).resolve().parents[1]/"src/v4/formatos/evidencias_f16"

def doc(name):
    return F16.load_document(DOCS/(name+".json"))

def page(manifest):
    # Test fixture ONLY. Cannot be called live evidence by a test.
    return "<html><body>"+". ".join(x["text"] for x in manifest["quoted_spans"])+".</body></html>"

def extracted(name):
    d=doc(name)
    return F17.audit_verified_source(d,page(d))

def _joints(result):
    return {e["joint"] for e in result["graph"]["edges"]}

def test_hydraulics_each_relation_has_own_evidence_not_all_spans():
    record=extracted("plataforma_tesoura_fonte_alternativa")
    graph=record["graph"]
    assert graph["family_candidate"]=="hydraulic_scissor_lift"
    assert [(e["joint"],e["supported_span_ids"]) for e in graph["edges"]]==[
        ("drives",["h1"]),("fluid_to",["h2"]),("pushes",["h3"])]
    assert all(e["evidence_kind"]=="direct_lexical_relation" for e in graph["edges"])
    assert record["all_claims_have_span_id"] is True
    assert record["source_live_verified"] is False
    assert record["render_allowed"] is False
    assert record["publication_allowed"] is False

def test_hydraulic_original_wording_uses_same_lexicon_not_url_selection():
    a=extracted("plataforma_tesoura_hidraulica")
    b=extracted("plataforma_tesoura_fonte_alternativa")
    assert a["graph"]["family_candidate"]==b["graph"]["family_candidate"]
    assert _joints(a)==_joints(b)=={"drives","fluid_to","pushes"}
    assert a["capability_gap"]["status"]=="BLOCKED_NO_KERNEL"
    assert b["capability_gap"]["status"]=="BLOCKED_NO_KERNEL"
    for r in (a,b):
        kinds={n["kind"] for n in r["graph"]["nodes"]}
        assert kinds=={"electric_motor","hydraulic_pump","hydraulic_cylinder","scissor_arms"}
        assert r["capability_gap"]["new_edge_kinds"]==["fluid_to","pushes"]
        assert len(r["capability_gap"]["required_subsystems"])==4

def test_gear_pair_does_not_infer_driver_and_numeric_values_from_text():
    r=extracted("par_engrenagens_educacional")
    assert r["graph"]["family_candidate"]=="external_spur_pair"
    assert len(r["graph"]["edges"])==1
    edge=r["graph"]["edges"][0]
    assert edge["joint"]=="meshes_with"
    assert edge["supported_span_ids"]==["g2"]
    assert edge["direction_confirmed"] is False
    assert all(n["kind"]=="spur_gear" for n in r["graph"]["nodes"])
    assert r["capability_gap"]["unknown_input_output_orientation"] is True
    assert r["capability_gap"]["tooth_counts_observed"] is False
    assert r["full_f15_compile_allowed"] is False
    assert r["render_allowed"] is False

def test_slider_crank_names_dont_imply_unproved_hinges_or_belt():
    r=extracted("biela_cinematica_parcial")
    assert r["graph"]["family_candidate"]=="partial_slider_crank"
    assert _joints(r)=={"slides_in"}
    edge=r["graph"]["edges"][0]
    assert edge["supported_span_ids"]==["b3"]
    assert "crank" in {n["id"] for n in r["graph"]["nodes"]}
    assert "rod" in {n["id"] for n in r["graph"]["nodes"]}
    assert all(n["kind"]!="belt" for n in r["graph"]["nodes"])
    assert r["capability_gap"]["status"]=="BLOCKED_MISSING_JOINTS_AND_COMPONENTS"
    assert len(r["capability_gap"]["unproven_required_connections"])==4

def test_synonyms_independent_of_page_identity_and_order():
    spans=[
       {"id":"t3","text":"The hydraulic ram pushes the scissor arms upward.","supported":True},
       {"id":"t1","text":"An electric motor powers the hydraulic pump.","supported":True},
       {"id":"t2","text":"Hydraulic fluid flows from the pump to the cylinder.","supported":True},
    ]
    result=F17.extract(spans)
    assert result["family_candidate"]=="hydraulic_scissor_lift"
    assert {e["joint"]:e["supported_span_ids"] for e in result["edges"]}=={
       "drives":["t1"],"fluid_to":["t2"],"pushes":["t3"]
    }
    assert {e["id"] for e in result["edges"]}=={
       "motor_pump_t1","pump_actuator_t2","actuator_scissors_t3"
    }

def test_unsupported_relation_or_negation_must_not_look_confirmed():
    r=F17.extract([
       {"id":"a1","text":"The motor does not drive the pump.","supported":True},
       {"id":"a2","text":"The ram never pushes the scissor arms.","supported":True},
    ])
    assert r["family_candidate"]=="insufficient_explicit_relations"
    assert r["edges"]==[]
    assert len(r["warnings"])==2
    r2=F17.extract([{"id":"a3","text":"A motor powers a brake.","supported":True}])
    assert r2["edges"]==[]
    with pytest.raises(ValueError,match="F17-PROVA-TRECHO_NAO_VERIFICADO"):
        F17.extract([{"id":"a4","text":"Two gears in mesh","supported":False}])
    with pytest.raises(ValueError,match="F17-PROVA-TRECHO_NAO_VERIFICADO"):
        F17.extract([{"id":"dup","text":"Two gears in mesh","supported":True},
                     {"id":"dup","text":"Two gears in mesh","supported":True}])

def test_no_external_html_no_automated_fake_evidence(tmp_path):
    d=doc("plataforma_tesoura_fonte_alternativa")
    report=F17.run(DOCS/(d["id"]+".json"),tmp_path,live=False)
    assert report["status"]=="BLOCKED_NO_LIVE_SOURCE"
    assert "graph" not in report
    assert report["source_live_verified"] is False
    assert report["publication_allowed"] is False
    assert json.loads((tmp_path/(d["id"]+"_F17_RELATIONS.json")).read_text("utf8"))==report

def test_mocked_live_transport_not_citable_as_real_production_proof(monkeypatch,tmp_path):
    d=doc("plataforma_tesoura_fonte_alternativa")
    def fake(url):
        assert url==d["url"]
        return {"text":page(d),"raw_sha256":"a"*64,"mime":"text/html","final_url":url}
    monkeypatch.setattr(F16,"fetch_html",fake)
    # Proves only the deterministic network branch in tests, not a live GET.
    r=F17.run(DOCS/(d["id"]+".json"),tmp_path,live=True)
    assert r["source_live_verified"] is True
    assert r["source_sha256"]=="a"*64
    assert r["status"]=="BLOCKED_NO_KERNEL"
    assert r["render_allowed"] is False
    assert r["publication_allowed"] is False
    assert len(r["graph"]["edges"])==3
    assert "hydraulic_cylinder" not in F15.NODE_KINDS

def test_source_mismatch_and_url_redirect_are_fail_closed(monkeypatch,tmp_path):
    d=doc("plataforma_tesoura_fonte_alternativa")
    monkeypatch.setattr(F16,"fetch_html",lambda url:{
       "text":"None of the required technical spans.","raw_sha256":"a"*64,
       "mime":"text/html","final_url":url})
    r=F17.run(DOCS/(d["id"]+".json"),tmp_path,live=True)
    assert r["status"].startswith("BLOCKED_SOURCE_")
    assert r["source_live_verified"] is False
    assert "graph" not in r
    monkeypatch.setattr(F16,"fetch_html",lambda url:{
       "text":page(d),"raw_sha256":"a"*64,"mime":"text/html",
       "final_url":"https://example.com/redirected"})
    r=F17.run(DOCS/(d["id"]+".json"),tmp_path,live=True)
    assert r["source_live_verified"] is False
    assert "graph" not in r

def test_no_visual_rights_or_kernels_promoted():
    r=extracted("plataforma_tesoura_fonte_alternativa")
    assert r["visual_reference_rights_verified"] is False
    assert r["source_does_not_establish_kinematic_dimensions"] is True
    assert r["third_party_media_copied"] is False
    assert r["full_f15_compile_allowed"] is False
    assert "scissor_arms" not in F15.NODE_KINDS
    assert r["capability_gap"]["is_machine_design_complete"] is False
    assert r["capability_gap"]["industrial_drawings_imported"] is False
    assert r["capability_gap"]["required_subsystems"][0]["capability"]=="scissor_linkage_kinematics_2d"

def test_spur_quote_disappears_does_not_claim_spur_geometry():
    source=doc("par_engrenagens_educacional")
    spans=F16.verified_spans(source,page(source))
    without_kind=[s for s in spans if s["id"]!="g1"]
    graph=F17.extract(without_kind)
    assert graph["family_candidate"]=="mixed_or_unclassified" or graph["family_candidate"]=="insufficient_explicit_relations"
    assert graph["nodes"][0]["kind"]=="gear"
    assert graph["nodes"][1]["kind"]=="gear"
    with pytest.raises(ValueError,match="F16-FONTE-ANCORA_AUSENTE_g1"):
        F17.audit_verified_source(source,"two gears in mesh turn in opposite directions")

def test_source_digest_only_with_source_proof():
    source=doc("par_engrenagens_educacional")
    r=F17.audit_verified_source(source,page(source),source_sha256="b"*64)
    assert r["source_live_verified"] is False
    assert r["source_sha256"] is None
    with pytest.raises(ValueError,match="F17-PROVA-SHA_AUSENTE"):
        F17.audit_verified_source(source,page(source),source_sha256="xx",proof_from_https=True)
