"""E1 — physics oracle, exact closures, shared rendering, no per-target solver."""
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

from src.v4.formatos import solver_restricoes_e1 as SOLVER
from src.v4.formatos import renderer_corpos_e1 as DRAW
from src.v4.formatos import cinematica_biela_manivela as ORACLE
from benchmarks import rodar_baseline_f15_e0 as BASELINE

SPECS=Path(__file__).resolve().parents[1]/"benchmarks/specs_genericas_e1"
NAMES=("oraculo_biela_e1","quatro_barras_e1","scotch_yoke_e1")

def spec(name):
    return json.loads((SPECS/(name+".json")).read_text("utf8"))

def test_baseline_12_probes_frozen_no_guess():
    record=BASELINE.measure()
    assert record["total"]==12 and len(record["cases"])==12
    assert record["score_ge_3"]==0
    assert record["blocked"]==12
    assert record["admitted_not_validated"]==0
    assert record["rendering_attempted"] is False
    assert all(x["reason"].startswith("F15-BLOQUEADO") for x in record["cases"])
    assert len(record["benchmark_sha256"])==64
    assert len(record["probes_sha256"])==64

@pytest.mark.parametrize("name",NAMES)
def test_common_solver_full_cycle_closes_all_joints(name):
    s=spec(name)
    frames=SOLVER.trajectory(s,121)
    assert len(frames)==121
    assert frames[0]["t"]==0
    assert math.isclose(frames[-1]["t"],6)
    assert max(f["max_residual_m"] for f in frames)<1e-8
    assert all(f["jacobian_rank"]==f["jacobian_size"] for f in frames)
    assert all(f["poses"]["ground"]==[0,0,0] for f in frames)
    for frame in frames:
        q=frame["q"]
        assert max(abs(x) for x in SOLVER.residual(
            q,s,frame["t"],SOLVER.validate(s)))<1e-8

def test_biela_matches_independent_f7_closed_form_not_written_for_spike():
    s=spec("oraculo_biela_e1")
    traj=SOLVER.trajectory(s,121)
    for f in traj:
        angle=2*math.pi*f["t"]/6
        reference=ORACLE.calcular(angle,35,120,250,600)
        pin=SOLVER.world(f["poses"]["crank"],[.35,0])
        assert abs(pin[0]-(reference.crank_x-250)/100)<3e-7
        assert abs(pin[1]-(reference.crank_y-600)/100)<3e-7
        assert abs(f["poses"]["slider"][0])<3e-7
        assert abs(f["poses"]["slider"][1]-(reference.piston_y-600)/100)<3e-7
        assert math.isclose(
           np.linalg.norm(SOLVER.world(f["poses"]["rod"],[1.2,0])-
                          SOLVER.world(f["poses"]["rod"],[0,0])),
           1.2,abs_tol=1e-9)

def test_four_bar_full_rotation_continuous_rocker_and_joint_closure():
    s=spec("quatro_barras_e1")
    frames=SOLVER.trajectory(s,121)
    rocker=np.array([f["poses"]["rocker"][2] for f in frames])
    crank=np.array([f["poses"]["crank"][2] for f in frames])
    assert abs((crank[-1]-crank[0])-2*math.pi)<1e-8
    assert rocker.max()-rocker.min()>.35
    assert abs(rocker[-1]-rocker[0])<1e-6
    assert max(np.abs(np.diff(rocker)))<.3
    for f in frames:
        a=SOLVER.world(f["poses"]["coupler"],[2,0])
        b=SOLVER.world(f["poses"]["rocker"],[1.65,0])
        assert np.linalg.norm(a-b)<1e-8

def test_scotch_yoke_is_sinusoidal_from_generic_slot_constraint():
    s=spec("scotch_yoke_e1")
    traj=SOLVER.trajectory(s,121)
    poses=np.array([f["poses"]["yoke"] for f in traj])
    time=np.array([f["t"] for f in traj])
    expect=.65*np.sin(2*math.pi*time/6)
    assert np.max(np.abs(poses[:,0]-expect))<1e-8
    assert np.max(np.abs(poses[:,1]))<1e-8
    assert np.max(np.abs(poses[:,2]))<1e-8
    assert poses[:,0].max()>.64 and poses[:,0].min()<-.64

def test_solver_rejects_new_joints_and_missing_constraint_without_fake_motion():
    base=spec("scotch_yoke_e1")
    altered=copy.deepcopy(base)
    altered["joints"][-1]["kind"]="unmodeled_contact"
    with pytest.raises(ValueError,match="E1-SOLVER-JUNTA_NAO_SUPORTADA"):
        SOLVER.validate(altered)
    altered=copy.deepcopy(base)
    altered["joints"].pop()
    with pytest.raises(ValueError,match="E1-SOLVER-RESTRICOES_CONTAGEM"):
        SOLVER.validate(altered)
    altered=copy.deepcopy(base)
    altered["publish"]=True
    with pytest.raises(ValueError,match="E1-SOLVER-PUBLICACAO"):
        SOLVER.validate(altered)
    altered=copy.deepcopy(base)
    altered["units"]="px"
    with pytest.raises(ValueError,match="E1-SOLVER-CONTRATO"):
        SOLVER.validate(altered)

@pytest.mark.parametrize("name",NAMES)
def test_single_renderer_uses_same_code_fixed_camera_and_separate_pixels(name):
    s=spec(name)
    frames=SOLVER.trajectory(s,13)
    cam=DRAW.geometry_bounds(s,frames)
    assert cam["world_fixed_for_all_frames"] is True
    assert cam["scale_px_per_m"]>30
    scene=DRAW.svg_frame(s,frames[3],cam,title=name)
    assert 'id="generic-machine-stage"' in scene
    assert scene.count('id="body-')==len(s["bodies"])
    assert 'data-layout="E1_SHARED_RENDERER_PRIVATE"' in scene
    assert "NÃO PUBLICAR" in scene
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=scene.encode()))) as img:
        assert img.size==(540,960)

def test_default_no_phone_safe_zone_claim_and_no_3d_claim():
    import inspect
    source=inspect.getsource(SOLVER)
    assert "540" not in source and "960" not in source
    assert "cinematica_biela_manivela" not in source
    assert "quatro_barras_e1" not in source
    assert "scotch_yoke_e1" not in source
    assert not hasattr(SOLVER,"contact_solver")
    assert SOLVER.KINDS=={"pin":2,"slider":2,"slot":1}

def test_closed_form_oracle_makes_f7_regression_stronger_than_green_test_count():
    f=spec("oraculo_biela_e1")
    bad=copy.deepcopy(f)
    bad["bodies"][1]["seed"][1]=100
    with pytest.raises(ValueError,match="E1-SOLVER-FECHAMENTO"):
        SOLVER.solve_one(bad,0)
