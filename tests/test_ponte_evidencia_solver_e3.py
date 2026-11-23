"""E3 source-to-joint proof gate: no source-based numeric hallucination.

Tests with fixture text are NOT proof of an external HTTP retrieval.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.v4.formatos import ingestao_evidencias_f16 as F16
from src.v4.formatos import relacoes_com_evidencia_f17 as F17
from src.v4.formatos import ponte_evidencia_solver_e3 as E3

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"src/v4/formatos/evidencias_f16"
SPEC=ROOT/"benchmarks/specs_genericas_e1/oraculo_biela_e1.json"
BIND=ROOT/"benchmarks/bindings_e3/biela_parcial_f17_e3.json"


def fixture(name="biela_cinematica_parcial"):
    doc=F16.load_document(EVIDENCE/(name+".json"))
    html="<html><body>"+" . ".join(x["text"] for x in doc["quoted_spans"])+"</body></html>"
    ledger=F17.audit_verified_source(doc,html)
    return doc,ledger


def inputs():
    d,ledger=fixture()
    spec=json.loads(SPEC.read_text("utf8"))
    binding=json.loads(BIND.read_text("utf8"))
    return d,spec,binding,ledger


def test_offline_fixture_proposes_joint_relation_but_never_claims_live_source():
    d,s,b,ledger=inputs()
    a=E3.analyze(d,s,b,ledger)
    assert a["status"]=="BLOCKED_SOURCE_NOT_LIVE"
    assert a["joint_claims_supported"]==1
    assert a["joint_claims_total"]==4
    assert a["unproven_joint_indices"]==[0,1,2]
    assert a["source_supported_joint_claims"][0]["supported_span_ids"]==["b3"]
    assert a["source_supported_joint_claims"][0]["relation"]=="slides_in"
    assert a["candidate_joints_from_source"][0]["solver_joint_kind"]=="slider"
    assert a["candidate_joints_from_source"][0]["required_manual_geometry"]==[
        "pa","pb","axis_a","angle_offset"]
    assert a["geometry_values_source_verified"] is False
    assert a["geometry_preflight"]["status"]=="PASS_MANUAL_GEOMETRY_ONLY"
    assert a["geometry_preflight"]["max_residual_m"]<1e-8
    assert a["source_sha256"] is None
    assert not a["source_live_verified"] and not a["render_allowed"]
    assert not a["source_to_complete_spec_automatic"] and not a["publish"]


def test_unreferenced_solver_joints_cannot_be_turned_into_verified_claims():
    d,s,b,ledger=inputs()
    forged=copy.deepcopy(b)
    forged["joint_claims"].append({"joint_index":1,"edge_id":"crank_rod_hinge_b2"})
    with pytest.raises(ValueError,match="E3-EVIDENCIA-ARESTA_INVENTADA"):
        E3.analyze(d,s,forged,ledger)
    forged=copy.deepcopy(b)
    forged["joint_claims"][0]["edge_id"]="piston_slide_b2"
    with pytest.raises(ValueError,match="E3-EVIDENCIA-ARESTA_INVENTADA"):
        E3.analyze(d,s,forged,ledger)


def test_wrong_joint_type_and_endpoints_never_pass_citation_binding():
    d,s,b,ledger=inputs()
    wrong=copy.deepcopy(b)
    wrong["joint_claims"]=[{"joint_index":0,"edge_id":"piston_slide_b3"}]
    with pytest.raises(ValueError,match="E3-EVIDENCIA-TIPO_DE_JUNTA_SEM_PROVA"):
        E3.analyze(d,s,wrong,ledger)
    wrong=copy.deepcopy(b)
    wrong["body_roles"]["chamber"]="rod"
    with pytest.raises(ValueError,match="E3-EVIDENCIA-EXTREMIDADES_INCOMPATIVEIS"):
        E3.analyze(d,s,wrong,ledger)


def test_repeated_claims_and_source_body_ids_are_rejected():
    d,s,b,ledger=inputs()
    bad=copy.deepcopy(b)
    bad["joint_claims"].append(bad["joint_claims"][0].copy())
    with pytest.raises(ValueError,match="E3-EVIDENCIA-CITACAO_DUPLICADA"):
        E3.validate_binding(d,s,bad)
    bad=copy.deepcopy(b)
    bad["body_roles"]["made_up_node"]="crank"
    with pytest.raises(ValueError,match="E3-EVIDENCIA-PAPEL_SEM_PROVA"):
        E3.analyze(d,s,bad,ledger)
    bad=copy.deepcopy(b)
    bad["joint_claims"][0]["joint_index"]=True
    with pytest.raises(ValueError,match="E3-EVIDENCIA-INDICE"):
        E3.validate_binding(d,s,bad)


def test_wrong_document_or_copied_excerpt_not_accepted():
    d,s,b,ledger=inputs()
    other,_=fixture("par_engrenagens_educacional")
    with pytest.raises(ValueError,match="E3-EVIDENCIA-PROCEDENCIA"):
        E3.validate_binding(other,s,b)
    bad=copy.deepcopy(ledger);bad["source_url"]="https://example.org/unrelated"
    with pytest.raises(ValueError,match="E3-EVIDENCIA-FONTE_DIFERENTE"):
        E3.analyze(d,s,b,bad)


def test_fake_live_flag_without_sha_rejected_and_offline_mode_stays_blocked(tmp_path):
    d,s,b,ledger=inputs()
    with pytest.raises(ValueError,match="E3-EVIDENCIA-LIVE_NAO_COMPROVADO"):
        E3.analyze(d,s,b,ledger,live_proof=True)
    result=E3.run(EVIDENCE/"biela_cinematica_parcial.json",SPEC,BIND,tmp_path)
    assert result["status"]=="BLOCKED_NO_LIVE_SOURCE"
    assert not result["source_live_verified"]
    assert not result["render_allowed"]
    assert not result["publish"]
    stored=json.loads((tmp_path/"biela_cinematica_parcial_E3_AUDIT.json").read_text("utf8"))
    assert stored==result


def test_mocked_https_path_only_tests_transport_not_real_web(monkeypatch,tmp_path):
    d,s,b,ledger=inputs()
    text=" . ".join(x["text"] for x in d["quoted_spans"])
    def mocked_fetch(url):
        assert url==d["url"]
        return {"text":text,"raw_sha256":hashlib.sha256(text.encode()).hexdigest(),
                "final_url":url,"mime":"text/html"}
    monkeypatch.setattr(F16,"fetch_html",mocked_fetch)
    result=E3.run(EVIDENCE/"biela_cinematica_parcial.json",SPEC,BIND,tmp_path,live=True)
    # This branch is MOCKED: not a proof that the public page was fetched.
    assert result["status"]=="BLOCKED_UNPROVEN_JOINTS"
    assert result["joint_claims_supported"]==1
    assert result["unproven_joint_indices"]==[0,1,2]
    assert result["human_review_required"]
    assert not result["render_allowed"]
    assert not result["source_to_complete_spec_automatic"]


def test_redirect_and_missing_anchor_fail_closed(monkeypatch,tmp_path):
    d,s,b,ledger=inputs()
    def redirect(url):
        return {"text":" . ".join(x["text"] for x in d["quoted_spans"]),
                "raw_sha256":"a"*64,"final_url":"https://evil.example.invalid",
                "mime":"text/html"}
    monkeypatch.setattr(F16,"fetch_html",redirect)
    result=E3.run(EVIDENCE/"biela_cinematica_parcial.json",SPEC,BIND,tmp_path,live=True)
    assert result["status"]=="BLOCKED_SOURCE_OR_CONTRACT_ValueError"
    assert not result["source_live_verified"]
    monkeypatch.setattr(F16,"fetch_html",lambda url:{
        "text":"This unrelated page claims nothing.","raw_sha256":"b"*64,
        "final_url":url,"mime":"text/html"})
    result=E3.run(EVIDENCE/"biela_cinematica_parcial.json",SPEC,BIND,tmp_path,live=True)
    assert result["status"]=="BLOCKED_SOURCE_OR_CONTRACT_ValueError"
    assert not result["source_live_verified"]


def test_strictly_unsupported_gear_mesh_and_hydraulic_edges_do_not_fake_solver():
    for name in ("par_engrenagens_educacional",
                 "plataforma_tesoura_fonte_alternativa"):
        d,record=fixture(name)
        suggestions=E3.joint_candidates(record["graph"])
        assert suggestions
        assert all(x["solver_joint_kind"] is None for x in suggestions)
        assert all(x["status"]=="UNSUPPORTED_BY_CURRENT_PLANAR_SOLVER"
                   for x in suggestions)
        assert all(x["source_edge_id"] and x["supported_span_ids"]
                   for x in suggestions)


def test_no_source_numeric_provenance_injected_by_binding():
    d,s,b,ledger=inputs()
    b["numbers_from_source"]=True
    with pytest.raises(ValueError,match="E3-EVIDENCIA-PROCEDENCIA"):
        E3.validate_binding(d,s,b)
    b["numbers_from_source"]=False
    b["spec_authorship"]="LLM_generated_autonomous"
    with pytest.raises(ValueError,match="E3-EVIDENCIA-PROCEDENCIA"):
        E3.validate_binding(d,s,b)


def test_source_relation_without_dimensions_never_reaches_publish_or_automatic_render():
    d,s,b,ledger=inputs()
    for row in E3.joint_candidates(ledger["graph"]):
        assert "seed" not in row
        assert "length" not in row
        assert row["status"]=="RELATION_ONLY_REQUIRES_DIMENSIONS"
    report=E3.analyze(d,s,b,ledger)
    assert report["human_review_required"] is True
    assert report["render_allowed"] is False
    assert report["source_to_complete_spec_automatic"] is False
    assert report["geometry_preflight"]["samples"]==33
