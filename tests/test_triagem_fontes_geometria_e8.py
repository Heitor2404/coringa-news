"""E8 tests distinguish source/license verification from solver support."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from src.v4.formatos import triagem_fontes_geometria_e8 as E8
from src.v4.formatos import importador_geometria_e7 as E7

ROOT=Path(__file__).resolve().parents[1]
REG=json.loads((ROOT/"benchmarks/e8_multi_repo_catalog_v1.json").read_text("utf8"))
UNSEEN=json.loads((ROOT/"benchmarks/e8_unseen_linkage_sources_v1.json").read_text("utf8"))
OLD=json.loads((ROOT/"benchmarks/e7_open_geometry_sources_v1.json").read_text("utf8"))

def mock_source():
    # Fake data is for parser/unit tests only, never a public HTTPS claim.
    license=b"MIT License\n\nCopyright test stub, not a real source.\n"
    preset=b"# Example\n\n"+(chr(96)*3+"mechanism\n").encode()+b"type: fourbar\nground: 4\n"+(chr(96)*3).encode()
    oracle=b'{"phases":[0.0,0.5],"slidercrank_B":[[1.0,0.0],[0.0,0.0]]}'
    geometry=b"LinkageDesign,1\n[project]\nkey,value\nname,Incomplete\n"
    blobs={
      ("repoone/example","LICENSE"):license,
      ("repoone/example","examples/example.csv"):geometry,
      ("repotwo/example","LICENSE"):license,
      ("repotwo/example","README.md"):preset,
      ("repotwo/example","reference.json"):oracle,
    }
    sources=[
      {"id":"repo_one","repository":"repoone/example","commit":"a"*40,
       "license_path":"LICENSE","license_blob_sha1":E7.git_blob_sha1(license),
       "samples":[{"path":"examples/example.csv",
                   "blob_sha1":E7.git_blob_sha1(geometry)}]},
      {"id":"repo_two","repository":"repotwo/example","commit":"b"*40,
       "license_path":"LICENSE","license_blob_sha1":E7.git_blob_sha1(license),
       "samples":[{"path":"README.md","blob_sha1":E7.git_blob_sha1(preset)},
                  {"path":"reference.json","blob_sha1":E7.git_blob_sha1(oracle)}]}
    ]
    def getter(repo,commit,path):
        assert commit=="a"*40 if repo=="repoone/example" else commit=="b"*40
        return blobs[(repo,path)]
    return {"schema":E8.SCHEMA,
      "scope":"bounded_catalog_not_open_world_github_discovery",
      "publish":False,"sources":sources},getter

def test_real_registry_has_two_independently_pinned_repositories():
    assert E8.validate_registry(REG) is True
    assert {s["repository"] for s in REG["sources"]}=={
        "jackhale98/linkage_design","MasoudMiM/sketch-mechanisms"}
    assert all(len(s["commit"])==40 for s in REG["sources"])
    assert UNSEEN["eval_files_not_seen_in_e7"] is True
    assert {p["path"] for p in UNSEEN["files"]}.isdisjoint(
        {p["path"] for p in OLD["files"]})
    assert len(UNSEEN["files"])==6
    assert E7.source_manifest(UNSEEN)

def test_fake_network_is_blocked_from_live_claim():
    reg,get=mock_source()
    with pytest.raises(ValueError,match="E8-FONTE-MOCK_NAO_E_LIVE"):
        E8.audit(reg,getter=get,network_verified=True)

def test_mocked_catalog_cannot_claim_external_source_proof():
    reg,get=mock_source()
    result=E8.audit(reg,getter=get)
    assert result["status"]=="MOCKED_SOURCE_TRIAGE_NOT_LIVE"
    assert result["source_count"]==2
    assert result["source_sample_files"]==3
    assert not result["open_internet_topic_discovery"]
    assert result["source_files_with_complete_anchor_geometry"]==0
    caps={a["capability"] for r in result["source_checks"] for a in r["source_files"]}
    assert caps=={"STRUCTURED_SOURCE_REJECTED_BY_GEOMETRY_GATE",
                  "PARAMETRIC_PRESET_NO_EXPLICIT_JOINT_ANCHORS",
                  "INDEPENDENT_KINEMATIC_ORACLE_ONLY"}
    assert result["auto_publish"] is False and result["visual_approved"] is False

def test_independent_reference_is_not_mechanism_spec():
    record=E8.classify(
      b'{"phases":[0,0.5,1],"slidercrank_B":[[4,0],[2,0],[4,0]]}',
      "reference.json")
    assert record["capability"]=="INDEPENDENT_KINEMATIC_ORACLE_ONLY"
    assert record["numeric_samples_are_not_joint_anchors"]
    assert not record["can_build_mechanism_spec_without_named_template"]

def test_csv_schema_is_checked_and_not_blindly_trusted():
    bad=b"LinkageDesign,1\n[project]\nkey,value\nname,Not a machine\n"
    r=E8.classify(bad,"examples/foo.csv")
    assert r["capability"]=="STRUCTURED_SOURCE_REJECTED_BY_GEOMETRY_GATE"
    assert not r["can_build_mechanism_spec_without_named_template"]

def test_full_geometry_still_subject_to_generic_adapter(monkeypatch):
    called=[]
    def controlled_import(payload):
        called.append(payload)
        return (None,{"converted_body_count":3,
                      "converted_joint_count":4,
                      "source_geometry_satisfied_constraints":7})
    monkeypatch.setattr(E8,"source_geometry",controlled_import)
    data=b"LinkageDesign,1\n[points]\n"
    row=E8.classify(data,"from_unknown_source.csv")
    assert called==[data]
    assert row["capability"]=="STRUCTURED_PLANAR_SOURCE"
    assert row["joint_count"]==4
    assert row["kinematic_trajectory_not_yet_tested"] is True

def test_license_hash_and_sample_hash_mismatch_reject_everything():
    reg,get=mock_source()
    bad=copy.deepcopy(reg);bad["sources"][0]["license_blob_sha1"]="0"*40
    with pytest.raises(ValueError,match="E8-FONTE-LICENCA_HASH"):
        E8.audit(bad,getter=get)
    bad=copy.deepcopy(reg);bad["sources"][1]["samples"][0]["blob_sha1"]="0"*40
    with pytest.raises(ValueError,match="E8-FONTE-ARQUIVO_HASH"):
        E8.audit(bad,getter=get)

@pytest.mark.parametrize("field,value,reason",[
    ("repository","evil.com/../../../secrets","IDENTIDADE"),
    ("commit","main","IDENTIDADE"),
    ("license_path","../../LICENSE","LICENCA"),
])
def test_registry_rejects_identity_and_license_tampering(field,value,reason):
    bad=copy.deepcopy(REG)
    bad["sources"][0][field]=value
    with pytest.raises(ValueError,match="E8-FONTE-"+reason):
        E8.validate_registry(bad)

def test_traversal_and_extra_untrusted_sample_rejected():
    bad=copy.deepcopy(REG)
    bad["sources"][0]["samples"].append({
        "path":"../../private.env","blob_sha1":"f"*40})
    with pytest.raises(ValueError,match="E8-FONTE-ARQUIVO"):
        E8.validate_registry(bad)
    with pytest.raises(ValueError,match="E8-FONTE-CAMINHO"):
        E8.fetch("owner/repo","main","README.md")
    with pytest.raises(ValueError,match="E8-FONTE-CAMINHO"):
        E8.fetch("owner/repo","a"*40,"../../other")

def test_duplicate_sources_and_duplicate_paths_rejected():
    bad=copy.deepcopy(REG)
    bad["sources"].append(copy.deepcopy(bad["sources"][0]))
    with pytest.raises(ValueError,match="E8-FONTE-DUPLICADO"):
        E8.validate_registry(bad)
    bad=copy.deepcopy(REG)
    bad["sources"][0]["samples"].append(copy.deepcopy(bad["sources"][0]["samples"][0]))
    with pytest.raises(ValueError,match="E8-FONTE-DUPLICADO"):
        E8.validate_registry(bad)

def test_no_premature_claim_about_visual_assets_or_completeness():
    reg,get=mock_source()
    result=E8.audit(reg,getter=get)
    for source in result["source_checks"]:
        assert source["media_reuse_proven"] is False
        for item in source["source_files"]:
            assert not item["industrial_machine_identity_verified"]
            assert not item["media_asset_reused"]
            assert item["license_inheritance_review_required"]
            assert item["publish"] is False
