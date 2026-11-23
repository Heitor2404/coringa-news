"""E12 tests: source-anchored second-author JSON with bounded oscillating actuator."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from src.v4.formatos import importador_juntas_json_e12 as E12
from src.v4.formatos import solver_restricoes_e1 as S
from src.v4.formatos import renderer_mecanico_e9 as V

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/"benchmarks/e12_independent_planar_json_v1.json").read_text("utf8"))

def fourbar():
    return {
      "name":"renamable_source_document",
      "bodies":[
        {"name":"ground","is_ground":True},
        {"name":"input","is_ground":False},
        {"name":"coupler","is_ground":False},
        {"name":"output","is_ground":False}
      ],
      "joints":{
        "A":{"bodies":["ground","input"],"xy_mm":[0.,0.],"kind":"revolute"},
        "B":{"bodies":["input","coupler"],"xy_mm":[9.,15.588457268119894],"kind":"revolute"},
        "C":{"bodies":["coupler","output"],"xy_mm":[48.0507693297486,37.94997364681761],"kind":"revolute"},
        "D":{"bodies":["output","ground"],"xy_mm":[50.,0.],"kind":"revolute"}
      },
      "outputs":{"P":{"body":"coupler","xy_mm":[30.,40.]}},
      "input_joint":"A",
      "input_range_deg":[40.,100.],
      "meta":{"reference_input_deg":60.,"assembly_branch":1}
    }

def test_independent_mit_manifest_has_immutable_source_ids_and_license():
    records=E12.validate_manifest(MANIFEST)
    assert len(records)==4
    assert len({x["path"] for x in records})==4
    assert "compliant" in MANIFEST["source_repository"]
    assert MANIFEST["excluded_mesh_example"]["reason"].startswith("compliant_single_mesh")
    assert MANIFEST["publish"] is False

def test_structured_json_converts_without_mechanism_title_dispatch():
    doc=fourbar()
    spec,proof=E12.build_spec(doc)
    S.validate(spec)
    assert len(spec["bodies"])==3
    assert len(spec["joints"])==4
    assert all(j["kind"]=="pin" for j in spec["joints"])
    assert spec["ground"]["id"]=="ground"
    assert spec["driver"]["body"]=="input"
    assert spec["driver"]["profile"]["kind"]=="oscillating"
    assert proof["source_joint_count"]==4
    assert proof["real_CAD_part_contours_imported"] is False
    assert proof["compliant_flexure_mesh_rigid_animation_disallowed"]
    assert spec["visual_approved"] is False and spec["publish"] is False
    frames=S.trajectory(spec,81)
    assert max(x["max_residual_m"] for x in frames)<1e-7
    assert all(x["jacobian_rank"]==x["jacobian_size"] for x in frames)
    assert max(abs(x["poses"]["input"][2]) for x in frames)<math.radians(41)
    assert frames[0]["poses"]["input"][2]==pytest.approx(0,abs=1e-7)
    assert frames[-1]["poses"]["input"][2]==pytest.approx(0,abs=1e-6)
    svg=V.svg_frame(spec,frames[16],
                    __import__("src.v4.formatos.renderer_corpos_e1",fromlist=["geometry_bounds"]).geometry_bounds(spec,frames),
                    frames)
    assert svg.count('class="e9-machine-body"')==3
    assert "NÃO PUBLICAR" in svg

def test_source_title_change_does_not_alter_machine_motion():
    doc=fourbar()
    spec_a,_=E12.build_spec(doc)
    doc["name"]="a totally different uninvolved title"
    spec_b,_=E12.build_spec(doc)
    assert spec_a==spec_b

@pytest.mark.parametrize("change,error",[
    (lambda d: d["joints"]["B"].update({"kind":"slider"}),"UNSUPPORTED_JOINT"),
    (lambda d: d["joints"]["D"].update({"bodies":["ground","ground"]}),"JOINT_REFERENCES"),
    (lambda d: d["joints"]["B"].update({"xy_mm":["x",0]}),"POINT"),
    (lambda d: d["joints"]["A"].update({"xy_mm":[5000000,0]}),"POINT_RANGE"),
    (lambda d: d.update({"input_joint":"NONE"}),"INPUT_JOINT_UNKNOWN"),
    (lambda d: d["meta"].update({"reference_input_deg":15.}),"SOURCE_REFERENCE_ANGLE_MISMATCH"),
    (lambda d: d.update({"input_range_deg":[0.,20.]}),"SOURCE_RANGE_NOT_OSCILLATORY"),
    (lambda d: d["bodies"][0].update({"name":"../../escape"}),"BODY"),
])
def test_adversarial_incorrect_geometry_is_rejected(change,error):
    d=fourbar();change(d)
    with pytest.raises(ValueError,match="E12-SOURCE-"+error):
        E12.build_spec(d)

def test_no_third_party_license_or_revision_forgery():
    bad=copy.deepcopy(MANIFEST)
    bad["source_commit"]="main"
    with pytest.raises(ValueError,match="E12-SOURCE-MANIFEST"):
        E12.validate_manifest(bad)
    bad=copy.deepcopy(MANIFEST)
    bad["files"][0]["path"]="../pwn.json"
    with pytest.raises(ValueError,match="E12-SOURCE-FILE_ID_OR_HASH"):
        E12.validate_manifest(bad)
    with pytest.raises(ValueError,match="E12-SOURCE-UNSAFE_PATH"):
        E12.fetch("../../README.md")

def test_mock_must_not_report_live_source():
    with pytest.raises(ValueError,match="E12-SOURCE-FAKE_LIVE"):
        E12.audit_manifest(MANIFEST,downloader=lambda p:b"x",network_verified=True)

def test_oscillator_generic_contract_blocks_undocumented_ranges():
    spec,_=E12.build_spec(fourbar())
    p=copy.deepcopy(spec)
    p["driver"]["profile"]["range_max_rad"]=3.9
    with pytest.raises(ValueError,match="E1-SOLVER-PERFIL_INTERVALO"):
        S.validate(p)
    p=copy.deepcopy(spec)
    p["driver"]["profile"]["phase_rad"]=0
    with pytest.raises(ValueError,match="E1-SOLVER-PERFIL_POSE_INICIAL_DIVERGE"):
        S.validate(p)
    p=copy.deepcopy(spec)
    p["driver"]["profile"]["kind"]="manual_family_template"
    with pytest.raises(ValueError,match="E1-SOLVER-PERFIL_ACIONADOR"):
        S.validate(p)

def test_old_constant_speed_driver_contract_remains_unchanged():
    spec,_=E12.build_spec(fourbar())
    spec["driver"]={"body":"input","theta0":0.,"speed":1.0}
    assert S.validate(spec)
    assert len(S.residual([v for b in spec["bodies"] for v in b["seed"]],
                          spec,0.,tuple(["ground"]+[b["id"] for b in spec["bodies"]])))==9
