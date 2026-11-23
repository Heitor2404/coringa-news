"""Independent E7 adapter tests: external licensed geometry is not a video template."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from src.v4.formatos import importador_geometria_e7 as E7
from src.v4.formatos import solver_restricoes_e1 as S
from src.v4.formatos import renderer_corpos_e1 as R

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/"benchmarks/e7_open_geometry_sources_v1.json").read_text("utf8"))
# A tiny synthetic fixture is used only for parser adversarial testing.
# Real source proofs and dynamics are run separately with HTTPS in CI.
SYNTHETIC="""LinkageDesign,1
[project]
key,value
name,Renamed anonymous mechanism
length_unit,mm
angle_unit,deg
[points]
id,x,y,fixed,label
P1,0,0,1,
P2,0,150,0,
P3,51.9615242271,180,0,
P4,83.2050294338,288.230676849,0,
[lines]
id,p1,p2,construction
L1,P1,P2,1
L2,P2,P3,0
L3,P1,P4,0
[constraints]
id,type,a,b,c,value,reference,label_dx,label_dy
C1,vertical,L1,,,,0,,
C2,distance,L1,,,150,0,,
C3,distance,L2,,,60,0,,
C4,angle,L2,,,30,0,,
C5,point_on_line,P3,L3,,,0,,
C6,distance,L3,,,300,0,,
[bodies]
id,name,lines,ground,color,mass,com_x,com_y,inertia
B1,Unspecified A,L2,0,,,,,
B2,Unspecified B,L3,0,,,,,
[joints]
id,type,point,line,body_a,body_b
J1,revolute,P2,,ground,B1
J2,revolute,P1,,ground,B2
J3,pin_in_slot,P3,L3,B2,B1
[driver]
key,value
type,rotary
line,L2
line_ref,
speed,30
return,0
"""

def test_manifest_tamper_and_fake_liveness_blocked():
    entries=E7.source_manifest(MANIFEST)
    assert len(entries)==5
    assert MANIFEST["upstream_license"]=="MIT"
    damaged=copy.deepcopy(MANIFEST)
    damaged["upstream_commit"]="main"
    with pytest.raises(ValueError,match="E7-FONTE-FONTE_LICENCA"):
        E7.source_manifest(damaged)
    damaged=copy.deepcopy(MANIFEST)
    damaged["files"][0]["path"]="../../.git/config"
    with pytest.raises(ValueError,match="E7-FONTE-CAMINHO_OU_HASH"):
        E7.source_manifest(damaged)
    with pytest.raises(ValueError,match="E7-FONTE-FAKE_LIVE"):
        E7.validate_source_run(MANIFEST,entries[0],source_bytes=b"fake",live=True)
    with pytest.raises(ValueError,match="E7-FONTE-CAMINHO"):
        E7.fetch_pinned("../../remote_script")

def test_parser_builds_source_driven_joints_not_a_named_template():
    spec,details=E7.source_geometry(SYNTHETIC.encode())
    S.validate(spec)
    assert spec["schema"]==S.SCHEMA
    assert set(x["kind"] for x in spec["joints"])=={"pin","slot"}
    assert [x["kind"] for x in spec["joints"]]==["pin","pin","slot"]
    assert len(spec["bodies"])==2
    assert spec["driver"]["body"]=="b1"
    assert math.isclose(spec["driver"]["speed"],math.pi)
    assert spec["duration_s"]==2
    assert details["source_geometry_satisfied_constraints"]==6
    assert details["converted_joint_count"]==3
    assert details["no_mechanism_name_dispatch"]
    assert not spec["publish"]
    frames=S.trajectory(spec,91)
    assert max(x["max_residual_m"] for x in frames)<1e-8
    contact=E7.finite_slots(spec,frames,details)
    assert contact["finite_slot_proof"]
    assert 0<=contact["finite_slot_projections_min"]
    assert contact["finite_slot_projections_max"]<=1

def test_renaming_unrelated_document_title_does_not_change_solver():
    a=E7.source_geometry(SYNTHETIC.encode())[0]
    b=E7.source_geometry(SYNTHETIC.replace(
        "Renamed anonymous mechanism","Widget Z23").encode())[0]
    assert a==b

@pytest.mark.parametrize(("from_text","to_text","code"),(
    ("C3,distance,L2,,,60,0,,","C3,distance,L2,,,70,0,,","DESENHO_NAO_SATISFAZ_CONSTRAINT"),
    ("C4,angle,L2,,,30,0,,","C4,angle,L2,,,80,0,,","DESENHO_NAO_SATISFAZ_CONSTRAINT"),
    ("J3,pin_in_slot,P3,L3,B2,B1","J3,pin_in_slot,P3,L2,B2,B1","RASGO_SEM_CORPO"),
    ("J3,pin_in_slot,P3,L3,B2,B1","J3,slider,P3,L3,B2,B1","TIPO_JUNTA_NAO_SUPORTADO"),
    ("line,L2","line,L9","DRIVER_SEM_CORPO"),
))
def test_tampered_geometry_or_joint_cannot_pass(from_text,to_text,code):
    altered=SYNTHETIC.replace(from_text,to_text)
    assert altered!=SYNTHETIC
    with pytest.raises(ValueError,match="E7-FONTE-"+code):
        E7.source_geometry(altered.encode())

def test_no_fake_license_and_bytes_are_allowed():
    a=MANIFEST["files"][0]
    payload=SYNTHETIC.encode()
    with pytest.raises(ValueError,match="E7-FONTE-LICENCA_DIVERGIU"):
        E7.validate_source_run(MANIFEST,a,source_bytes=payload,
                               license_bytes=b"Fake license\n",live=False)
    assert len(E7.git_blob_sha1(payload))==40
    assert E7.git_blob_sha1(payload)!=a["blob_sha1"]

def test_slot_segment_not_infinite_preventing_escaped_pin():
    spec,details=E7.source_geometry(SYNTHETIC.encode())
    frames=S.trajectory(spec,21)
    tampered=copy.deepcopy(details)
    idx=next(i for i,x in enumerate(tampered["joint_provenance"])
             if x["source_type"]=="pin_in_slot")
    tampered["joint_provenance"][idx]["finite_slot_length_m"]=.001
    with pytest.raises(ValueError,match="E7-FONTE-CONTATO_FORA_DO_SEGMENTO"):
        E7.finite_slots(spec,frames,tampered)

def test_non_supported_pair_and_source_unit_are_blocked():
    with pytest.raises(ValueError,match="E7-FONTE-UNIDADE"):
        E7.source_geometry(SYNTHETIC.replace("length_unit,mm","length_unit,px").encode())
    with pytest.raises(ValueError,match="E7-FONTE-CONTATO_COMPOSTO_NAO_SUPORTADO"):
        E7.source_geometry((SYNTHETIC+"\n[pairs]\nid,type\nG1,gear\n").encode())


def test_shared_camera_uses_source_dimensions_and_prevents_clipping():
    """Regression: the old 1.0-m minimum span shrunk a 0.3-m machine."""
    spec,_=E7.source_geometry(SYNTHETIC.encode())
    frames=S.trajectory(spec,91)
    camera=R.geometry_bounds(spec,frames)
    assert camera["world_fixed_for_all_frames"]
    assert camera["scale_px_per_m"]>800, camera
    assert max(camera["span_m"])<.9, camera
    cx,cy=camera["center"];scale=camera["scale_px_per_m"]
    for f in frames:
        for body in spec["bodies"]:
            p=f["poses"][body["id"]]
            for sh in body["shapes"]:
                for key in ("a","b"):
                    x,y=S.world(p,sh[key])
                    screen_x=270+(x-cx)*scale
                    screen_y=461-(y-cy)*scale
                    assert 25<=screen_x<=515,(screen_x,screen_y)
                    assert 170<=screen_y<=750,(screen_x,screen_y)
    svg=R.svg_frame(spec,frames[30],camera,title="DADOS GENERICOS")
    assert svg.count('id="body-')==2
    assert 'id="generic-machine-stage"' in svg
    assert "NÃO PUBLICAR" in svg
