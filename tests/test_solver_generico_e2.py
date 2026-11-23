"""E2 independent checks for reusable ideal pitch rolling and common visual parts.

No target-named branch in the solver or renderer. This is 2D kinematics,
not tooth contact, dynamics, industrial CAD, or AI source-to-spec generation.
"""
from __future__ import annotations

import copy
import io
import json
import math
from pathlib import Path

import cairosvg
import numpy as np
import pytest
from PIL import Image

from src.v4.formatos import solver_restricoes_e1 as S
from src.v4.formatos import renderer_corpos_e1 as R

SPEC_PATH=(Path(__file__).resolve().parents[1]/
           "benchmarks/specs_genericas_e2/pinhao_cremalheira_e2.json")


def scene():
    return json.loads(SPEC_PATH.read_text(encoding="utf8"))


def test_rack_pinion_uses_same_joint_solver_and_exact_rolling():
    s=scene()
    frames=S.trajectory(s,121)
    r=s["joints"][-1]["pitch_radius_m"]
    assert r==.4
    assert len(frames)==121
    assert all(f["jacobian_rank"]==f["jacobian_size"] for f in frames)
    assert max(f["max_residual_m"] for f in frames)<1e-8
    for f in frames:
        a=f["poses"]["pinion"]
        b=f["poses"]["rack"]
        assert abs(b[0]-r*a[2])<1e-8
        assert abs(b[1]+r)<1e-8
        assert abs(b[2])<1e-8
        assert abs(a[0])+abs(a[1])<1e-8
    assert abs(frames[-1]["poses"]["pinion"][2]-
               frames[0]["poses"]["pinion"][2]-math.pi)<1e-8
    assert abs(frames[-1]["poses"]["rack"][0]-
               frames[0]["poses"]["rack"][0]-r*math.pi)<1e-8


def test_rolling_holds_for_other_radius_and_opposite_contact_side():
    base=scene()
    for r,side,phase in ((.63,-1,.11),(.52,1,-.12)):
        s=copy.deepcopy(base)
        joint=s["joints"][-1]
        joint.update(pitch_radius_m=r,pitch_side=side,phase_m=phase)
        s["joints"][1]["pa"]=[0,side*r]
        s["bodies"][0]["seed"][2]=-math.pi/2
        s["bodies"][0]["shapes"][0]["pitch_radius_m"]=r
        s["bodies"][1]["seed"]=[-side*r*(-math.pi/2)+phase,side*r,0]
        s["bodies"][1]["shapes"][0]["tooth_side"]=-side
        s["bodies"][1]["shapes"][0]["tooth_pitch_m"]=2*math.pi*r/20
        frames=S.trajectory(s,121)
        assert max(f["max_residual_m"] for f in frames)<1e-8
        for f in frames:
            pin=f["poses"]["pinion"];rack=f["poses"]["rack"]
            expected=-side*r*pin[2]+phase
            assert abs(rack[0]-expected)<1e-8
            assert abs(rack[1]-side*r)<1e-8


def test_wrong_pitch_distance_blocks_without_fake_contact():
    s=scene()
    s["joints"][1]["pa"]=[0,-.67]  # slider stays shifted below gear
    with pytest.raises(ValueError,match="E1-SOLVER-RACK_SEM_TANGENCIA"):
        S.solve_one(s,0)


def test_redundant_constraints_of_same_count_do_not_pass_rank_gate():
    s=scene()
    # Replace rolling equation by a second constraint on vertical rack axis.
    # The count still matches but the rack is free in X -> Jacobian rank low.
    s["joints"][2]={"kind":"slot","a":"ground","b":"rack",
                    "pa":[0,-.4],"pb":[0,0],"axis_b":[1,0]}
    with pytest.raises(ValueError,match="E1-SOLVER-SINGULAR_OU_SUBDETERMINADO"):
        S.solve_one(s,0)


@pytest.mark.parametrize("field,value,reason",(
    ("pitch_radius_m",0,"RAIO_PRIMITIVO"),
    ("pitch_radius_m",float("nan"),"RAIO_PRIMITIVO"),
    ("pitch_side",0,"LADO_CONTATO"),
    ("pitch_side",True,"LADO_CONTATO"),
    ("phase_m",float("inf"),"FASE"),
    ("axis_b",[2,0],"EIXO_UNITARIO"),
))
def test_malformed_rolling_is_rejected(field,value,reason):
    s=scene()
    s["joints"][-1][field]=value
    with pytest.raises(ValueError,match="E1-SOLVER-"+reason):
        S.validate(s)


def test_no_routing_by_mechanism_name_or_extra_dedicated_compositor():
    s=scene()
    rename={"pinion":"alpha","rack":"beta"}
    for b in s["bodies"]:b["id"]=rename[b["id"]]
    for j in s["joints"]:
        j["a"]=rename.get(j["a"],j["a"])
        j["b"]=rename.get(j["b"],j["b"])
    s["driver"]["body"]="alpha"
    frames=S.trajectory(s,33)
    assert max(f["max_residual_m"] for f in frames)<1e-8
    cam=R.geometry_bounds(s,frames)
    assert cam["world_fixed_for_all_frames"]
    svg=R.svg_frame(s,frames[6],cam,title="NOMES ALEATORIOS")
    assert 'id="body-alpha"' in svg and 'id="body-beta"' in svg


def test_common_visual_shapes_have_real_teeth_and_are_not_cut():
    s=scene()
    gear=s["bodies"][0]["shapes"][0]
    rack=s["bodies"][1]["shapes"][0]
    j=s["joints"][-1]
    assert gear["pitch_radius_m"]==j["pitch_radius_m"]
    assert abs(rack["tooth_pitch_m"]-(2*math.pi*j["pitch_radius_m"]/gear["teeth"]))<1e-12
    frames=S.trajectory(s,121)
    cam=R.geometry_bounds(s,frames)
    assert cam["scale_px_per_m"]>80
    assert cam["world_fixed_for_all_frames"]
    for f in (frames[0],frames[30],frames[60],frames[90],frames[-1]):
        svg=R.svg_frame(s,f,cam,title="ROLAMENTO IDEAL")
        assert svg.count("<polygon")>=30
        assert 'id="generic-machine-stage"' in svg
        assert "NÃO PUBLICAR" in svg
        with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as im:
            assert im.size==(540,960)
        # Envelope of every graphic, including teeth, under the shared fixed camera.
        cx,cy=cam["center"];k=cam["scale_px_per_m"]
        for b in s["bodies"]:
            p=f["poses"][b["id"]]
            for shape in b["shapes"]:
                if shape["kind"]=="gear":
                    pts=[S.world(p,shape["center"])]
                    rad=shape["pitch_radius_m"]+shape["tooth_height_m"]
                    pts.extend([pts[0]+[-rad,-rad],pts[0]+[rad,rad]])
                else:
                    rad=shape["tooth_height_m"]+shape["thickness"]
                    pts=[]
                    for end in (shape["a"],shape["b"]):
                        center=S.world(p,end)
                        pts.extend([center+[-rad,-rad],center+[rad,rad]])
                for u,v in pts:
                    x=270+(u-cx)*k
                    y=461-(v-cy)*k
                    assert 18<x<522 and 157<y<765


def test_overconstraint_and_publication_still_block():
    s=scene()
    s["joints"].append(copy.deepcopy(s["joints"][0]))
    with pytest.raises(ValueError,match="E1-SOLVER-RESTRICOES_CONTAGEM"):
        S.validate(s)
    s=scene()
    s["visual_approved"]=True
    with pytest.raises(ValueError,match="E1-SOLVER-PUBLICACAO"):
        S.validate(s)
