"""E9/E10 tests: one style for arbitrary solved specs, not equipment CAD."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.v4.formatos import solver_restricoes_e1 as S
from src.v4.formatos import renderer_corpos_e1 as R
from src.v4.formatos import renderer_mecanico_e9 as E9
from src.v4.formatos import auditoria_visual_e10 as E10

ROOT=Path(__file__).resolve().parents[1]

def get_spec():
    p=ROOT/"benchmarks/specs_genericas_e1/oraculo_biela_e1.json"
    return json.loads(p.read_text("utf8"))

def test_e9_shared_renderer_has_no_specific_machine_dispatch():
    spec=get_spec()
    S.validate(spec)
    trajectory=S.trajectory(spec,61)
    camera=R.geometry_bounds(spec,trajectory)
    svg=E9.svg_frame(spec,trajectory[19],camera,trajectory,title="FONTE MECANICA 01")
    assert 'id="e9-industrial-grid"' in svg
    assert 'id="e9-source-ground-guides"' in svg
    assert 'id="e9-pivots-source-anchored"' in svg
    assert svg.count('class="e9-machine-body"')==len(spec["bodies"])
    assert 'data-source-geometry="centerlines-only"' in svg
    assert 'GEOMETRIA E MOVIMENTO VERIFICADOS' in svg
    assert "PEÇAS ILUSTRATIVAS" in svg
    assert "NÃO PUBLICAR" in svg
    assert "<script" not in svg and "href=" not in svg
    assert "shaper" not in svg.lower()

def test_renamed_visual_document_title_changes_no_geometry_and_is_escaped():
    spec=get_spec()
    trajectory=S.trajectory(spec,51)
    camera=R.geometry_bounds(spec,trajectory)
    image1=E9.svg_frame(spec,trajectory[11],camera,trajectory,
                        title="A < & \"SAFE\"")
    image2=E9.svg_frame(spec,trajectory[11],camera,trajectory,
                        title="B > TEST")
    assert "A &lt; &amp;" in image1
    assert "B &gt; TEST" in image2
    import xml.etree.ElementTree as ET
    ET.fromstring(image1)
    assert image1.count('class="e9-machine-body"')==image2.count(
        'class="e9-machine-body"')
    assert image1.count('id="e9-pivots-source-anchored"')==1

def test_differs_from_old_stick_figure_in_body_geometry():
    spec=get_spec()
    trajectory=S.trajectory(spec,61)
    cam=R.geometry_bounds(spec,trajectory)
    old=R.svg_frame(spec,trajectory[30],cam,title="SOURCE")
    new=E9.svg_frame(spec,trajectory[30],cam,trajectory,title="SOURCE")
    assert 'class="e9-machine-body"' not in old
    assert new.count('class="e9-machine-body"')==len(spec["bodies"])
    assert old!=new
    assert "fill=\"#061927\"" in new
    assert 'id="generic-machine-stage"' in new

def test_bad_camera_frame_count_and_publish_never_accepted():
    spec=get_spec()
    poses=S.trajectory(spec,31)
    cam=R.geometry_bounds(spec,poses)
    with pytest.raises(ValueError,match="E9-VISUAL-FRAMES_INSUFICIENTES"):
        E9.svg_frame(spec,poses[0],cam,poses[:8])
    corrupt=copy.deepcopy(cam);corrupt["world_fixed_for_all_frames"]=False
    with pytest.raises(ValueError,match="E9-VISUAL-CAMERA_NAO_FIXA"):
        E9.svg_frame(spec,poses[0],corrupt,poses)
    publish=copy.deepcopy(spec);publish["publish"]=True
    with pytest.raises(ValueError,match="E1-SOLVER-PUBLICACAO"):
        E9.svg_frame(publish,poses[0],cam,poses)

def test_e10_reports_true_source_provenance_and_no_fake_cad_approval():
    spec=get_spec()
    report,images=E10.evaluate(spec,sample_frames=61)
    assert report["status"]=="TECHNICAL_VISUAL_GATES_PASSED"
    assert report["stage_safezone_pass"]
    assert report["fixed_camera"]
    assert report["svg_no_scripts_no_urls"]
    assert report["joint_error_max_m"]<1e-6
    assert report["max_solver_residual_m"]<1e-7
    assert report["motion_rgb_mean_max"]>.15
    assert report["mechanical_body_graphics_derived_from_source_centerlines"]
    assert report["industrial_part_contours_sourced"] is False
    assert report["illustrative_link_widths_not_from_source"] is True
    assert report["housing_dimensions_verified"] is False
    assert report["industrial_machine_recognizability_reviewed"] is False
    assert report["aesthetic_approved"] is False
    assert report["publish"] is False
    assert len(images)==4
    assert images[0].size==(540,960)

def test_e10_rejects_too_few_or_too_many_frames():
    spec=get_spec()
    with pytest.raises(ValueError,match="E10-VALIDACAO-AMOSTRAS"):
        E10.evaluate(spec,sample_frames=9)
    with pytest.raises(ValueError,match="E10-VALIDACAO-AMOSTRAS"):
        E10.evaluate(spec,sample_frames=999)

def test_e9_svg_uses_existing_e1_camera_and_never_changes_poses():
    spec=get_spec()
    before=json.dumps(spec,sort_keys=True)
    frames=S.trajectory(spec,61)
    camera=R.geometry_bounds(spec,frames)
    for idx in (0,15,30,45):
        svg=E9.svg_frame(spec,frames[idx],camera,frames)
        assert svg.count('id="body-')==len(spec["bodies"])
        assert "data-pose-x" in svg
        assert "data-pose-angle" in svg
    assert json.dumps(spec,sort_keys=True)==before

def test_e9_never_claims_real_machine_identity_from_arbitrary_shapes():
    spec=get_spec()
    images=S.trajectory(spec,51)
    cam=R.geometry_bounds(spec,images)
    svg=E9.svg_frame(spec,images[10],cam,images)
    # End-caps and guiding rails are drawing conventions; source did not
    # provide an industrial housing shape or licensed CAD shell.
    assert "CAD ORIGINAL" not in svg
    assert "PEÇAS ILUSTRATIVAS" in svg
    assert 'id="e9-industrial-grid"' in svg
