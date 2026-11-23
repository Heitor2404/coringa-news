"""F12 — composicao HERO sem reduzir maquina nem inventar safe zone homologada."""
from __future__ import annotations

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
import pytest
from PIL import Image,ImageChops
from io import BytesIO

from src.v4.formatos import compositor_cinematico_parametrico_2d as M
from src.v4.formatos import layout_hero_mecanico_f12 as H
from src.v4.formatos import qa_svg_mobile_f11 as Q
from src.v4.formatos import camera_causal_svg as C

SCENES=Path(__file__).resolve().parents[1]/"src/v4/formatos/cenas_parametricas"
PATHS=["biela_manivela_curso_curto.json","biela_manivela_curso_longo.json"]
NS="{http://www.w3.org/2000/svg}"


def _scene(idx):
    return M.carregar(SCENES/PATHS[idx])


def _render(xml):
    with Image.open(BytesIO(cairosvg.svg2png(bytestring=xml.encode("utf8")))) as im:
        return im.convert("RGB").copy()


def _tag(root,name):
    elems=[n for n in root.iter() if n.get("id")==name]
    assert len(elems)==1
    return elems[0]


@pytest.mark.parametrize("idx",[0,1])
def test_hero_preserva_juntas_pecas_e_mesma_escala_no_layout(idx):
    scene=_scene(idx)
    for t in (.08,1.1,3.6,6.7,8.8):
        before=M.frame_svg(scene,t,transmissao_animada=True)
        after=M.frame_svg(scene,t,transmissao_animada=True,
                          enquadramento_mobile="hero_elevado_f12")
        original=ET.fromstring(before)
        changed=ET.fromstring(after)
        assert changed.get("data-layout")=="hero_elevado_f12"
        assert original.get("data-layout") is None
        a,b=_tag(original,"machine-stage"),_tag(changed,"machine-stage")
        assert b.get("transform").endswith(a.get("transform"))
        lift=float(b.get("data-layout-lift-px"))
        assert 90<=lift<=165
        assert b.get("transform").startswith("translate(0 -")
        # Svg dos elementos fisicos (geometria, data-travel, dimensoes e joins)
        assert ET.tostring(list(a)[0])==ET.tostring(list(b)[0])
        for key in M.ACTORS:
            assert ET.tostring(_tag(a,"role-"+key))==ET.tostring(_tag(b,"role-"+key))
        assert "data-belt-travel" in after
        assert "PENDENTE" in after
        assert scene["publish"] is False
    assert M.frame_svg(scene,2.6)==M.frame_svg(scene,2.6,enquadramento_mobile=None)


@pytest.mark.parametrize("idx",[0,1])
def test_hero_tem_distancia_real_do_header_e_footer_sem_corte(idx):
    scene=_scene(idx)
    frame=M.frame_svg(scene,3.6,transmissao_animada=True,
                      enquadramento_mobile="hero_elevado_f12")
    root=ET.fromstring(frame)
    stage=_tag(root,"machine-stage")
    lift=float(stage.get("data-layout-lift-px"))
    phase=scene["phases"][0]["title"]
    assert phase in frame
    assert root.get("width")=="540" and root.get("height")=="960"
    assert lift>100
    camera=C.CAMERAS["familias"][M.FAMILY]
    pose=C.calcular(M.FAMILY,scene["phases"][0]["action"],3.6,0,9.0)
    expected=pose.scale*camera["bounds"][1]+pose.ty-lift
    assert expected>=H.TOP_GOAL-.15
    assert expected<160
    assert ET.fromstring(frame).find(f"./{NS}g[@id='machine-stage']") is not None
    img=_render(frame)
    assert img.size==(540,960)


def test_hero_prova_reducao_de_sobreposicao_simulada_sem_miniaturizar():
    for scene in (_scene(0),_scene(1)):
        old=Q.medir(M.frame_svg(scene,3.6,transmissao_animada=True))
        new=Q.medir(M.frame_svg(scene,3.6,transmissao_animada=True,
                               enquadramento_mobile="hero_elevado_f12"))
        # Volante e correia antes integralmente sob mascara conservadora.
        assert old["flywheel"]["max_overlap_fraction"]==1.0
        assert old["drive_belt"]["max_overlap_fraction"]==1.0
        assert new["flywheel"]["max_overlap_fraction"]<.95
        assert new["drive_belt"]["max_overlap_fraction"]<.95
        # Mesma area de pixels de rolamento, ignorando bordas da tela.
        for role in ("flywheel","drive_belt","piston"):
            a,b=old[role]["visible_pixel_area"],new[role]["visible_pixel_area"]
            assert .96<=b/a<=1.04,(role,a,b)
        assert min(new["flywheel"]["pixel_bbox"][1],
                   new["drive_belt"]["pixel_bbox"][1]) < old["flywheel"]["pixel_bbox"][1]


def test_hero_bloqueia_modo_arbitrario_ou_pose_invalida():
    scene=_scene(0)
    with pytest.raises(ValueError,match="F-COMP-MEC-LAYOUT-NAO-CADASTRADO"):
        M.frame_svg(scene,1.0,enquadramento_mobile="pulo_aleatorio")
    orig=M.frame_svg(scene,1.0)
    pose=C.calcular(M.FAMILY,"curso_descendente",1.0,0.0,9.0)
    with pytest.raises(ValueError,match="F12-HERO-DUPLO_LAYOUT"):
        new,_=H.aplicar(orig,family=M.FAMILY,pose=pose)
        H.aplicar(new,family=M.FAMILY,pose=pose)
    with pytest.raises(ValueError,match="F12-HERO-FAMILIA_OU_CAMERA"):
        H.aplicar(orig,family="inventado",pose=pose)


def test_hero_qa_reutiliza_as_mesmas_mascaras_conservadoras(tmp_path):
    scene=_scene(0)
    old=Q.analisar(scene,tmp_path,animation=True)
    new=Q.analisar(scene,tmp_path,animation=True,
                   enquadramento_mobile="hero_elevado_f12")
    assert old["mobile_layout_mode"]=="original_f11"
    assert new["mobile_layout_mode"]=="hero_elevado_f12"
    assert new["publish"] is False and new["visual_approval"] is False
    assert new["automatically_shrink_machine"] is False
    assert new["masks_are_conservative_estimates"] is True
    assert new["worst_observed_overlap_fraction"] < old["worst_observed_overlap_fraction"]
    assert (tmp_path/(scene["id"]+"_F12_MASCARAS_PERFIL_SIMULADO.jpg")).is_file()
    assert (tmp_path/(scene["id"]+"_F11_MASCARAS_PERFIL_SIMULADO.jpg")).is_file()
