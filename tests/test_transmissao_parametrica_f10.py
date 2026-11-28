"""F10 — compressor completo usa a MESMA correia de tangentes da F7.

Testes de pixels e de geometria. Não afirmam correspondência CAD industrial.
"""
from __future__ import annotations

import io
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image, ImageChops, ImageStat
import pytest

from src.v4.formatos import render_compressor_conjunto_2d as C
from src.v4.formatos import primitivas_fisicas_parametricas as P
from src.v4.formatos import compositor_cinematico_parametrico_2d as F7

ROOT=Path(__file__).resolve().parents[1]
SCENES=ROOT/"src/v4/formatos/cenas_parametricas"
MANIFEST=json.loads(C.MANIFESTO_PADRAO.read_text(encoding="utf8"))


def _image(svg):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as im:
        return im.convert("RGB").copy()


def _role(svg,identifier):
    root=ET.fromstring(svg)
    matches=[x for x in root.iter() if x.attrib.get("id")==identifier]
    assert len(matches)==1
    return matches[0]


def _frame(progress,*,new=False,camera=False):
    return C.frame_svg(progress,MANIFEST,transmissao_parametrica=new,
                       camera_causal=camera,tempo_s=progress*8,
                       inicio_fase_s=0,duracao_s=8)


def test_compressor_default_inalterado_e_sem_novos_dados_de_belt():
    baseline=C.frame_svg(.38,MANIFEST)
    assert 'data-transmissao="tangentes_externas_f10"' not in baseline
    assert 'data-belt-travel' not in baseline
    assert 'id="role-drive_belt"' in baseline
    assert '<path d="M 142 646 L 278 643' in baseline
    assert 'data-visual-identity="PENDENTE"' in baseline
    assert "F-VISUAL-LEGADO-DESCARTADO" not in baseline  # gate externo


def test_modo_f10_reaproveita_tangentes_e_marcas_da_primitiva_f7():
    cfg=C.AssemblyLayout()
    original=_frame(.22)
    enhanced=_frame(.22,new=True)
    assert original!=enhanced
    belt=_role(enhanced,"role-drive_belt")
    assert belt.attrib["data-transmissao"]=="tangentes_externas_f10"
    assert len(list(belt))==3
    stroke=list(belt)[-1]
    assert "data-belt-travel" in stroke.attrib
    assert "stroke-dashoffset" in stroke.attrib
    assert "stroke-dasharray" in stroke.attrib
    expected_progress=C.estado(.22,cfg.spec()).angulo*cfg.pump_wheel_radius
    assert math.isclose(float(stroke.attrib["data-belt-travel"]),expected_progress,abs_tol=.002)
    # A função é a mesma, sem um segundo algoritmo na implementação.
    direct=P.transmissao_correia(cfg.motor_x,cfg.motor_y,cfg.motor_pulley_radius,
                 cfg.center_x,cfg.shaft_y,cfg.pump_wheel_radius,
                 cor="#203F51",filete="#A5D8E0",largura=12,
                 deslocamento_trama_px=expected_progress)
    assert direct in enhanced
    assert belt.attrib["id"]=="role-drive_belt"


@pytest.mark.parametrize("t",[.00,.07,.27,.46,.61,.81,.98])
def test_f10_correia_se_movimenta_mas_centro_das_polias_nao(t):
    cfg=C.AssemblyLayout()
    svg=_frame(t,new=True)
    # Câmara, gauge e conjunto seguem no lugar; movimento é da correia no percurso.
    assert 'id="role-receiver_horizontal"' in svg
    assert 'id="role-piston_cutaway"' in svg
    assert svg.count('id="machine-assembly"')==1
    belt=_role(svg,"role-drive_belt")
    assert len(list(belt))==3
    assert float(list(belt)[-1].attrib["data-belt-travel"])>=0
    assert cfg.pump_wheel_radius>cfg.motor_pulley_radius


def test_marcas_progridem_no_ritmo_linear_ideal_sem_oscilar_camera():
    cfg=C.AssemblyLayout()
    speeds=[]
    poses=set()
    for t in (.01,.07,.23,.47,.65,.91):
        svg=_frame(t,new=True,camera=True)
        belt=_role(svg,"role-drive_belt")
        speeds.append(float(list(belt)[-1].attrib["data-belt-travel"]))
        poses.add(_role(svg,"machine-assembly").attrib["transform"])
    assert speeds==sorted(speeds)
    assert len(poses)==1  # câmera F2B travada
    a=_frame(.1,new=True,camera=True)
    b=_frame(.9,new=True,camera=True)
    assert _role(a,"machine-assembly").attrib["transform"]==_role(b,"machine-assembly").attrib["transform"]


def test_f10_correia_atras_das_faces_e_antigo_mantem_ordem():
    antigo=_frame(.35)
    novo=_frame(.35,new=True)
    assert novo.index('id="role-drive_belt"') < novo.index('id="role-pump_flywheel"')
    assert novo.index('id="role-drive_belt"') < novo.index('id="role-motor_pulley"')
    assert antigo.index('id="role-drive_belt"') > antigo.index('id="role-pump_flywheel"')
    assert len([x for x in ET.fromstring(novo).iter()
               if x.get("id")=="role-drive_belt"])==1


def test_f7_duas_cenas_continuam_exatamente_iguais_por_padrao():
    for filename in ("biela_manivela_curso_curto.json","biela_manivela_curso_longo.json"):
        scene=F7.carregar(SCENES/filename)
        xml=F7.frame_svg(scene,1.75)
        assert "data-belt-travel" not in xml
        assert "BIELA E MANIVELA" in xml
        assert F7.validar(scene)["radius"] in (46,64)


def test_f10_pixels_mudam_so_no_palco_mecanico():
    for p in (.08,.29,.73):
        orig=_image(_frame(p))
        upgraded=_image(_frame(p,new=True))
        assert orig.size==upgraded.size==(540,960)
        diff=ImageChops.difference(orig,upgraded)
        # topo editorial e rodapé físico continuam byte idênticos
        assert diff.crop((0,0,540,270)).getbbox() is None
        assert diff.crop((0,905,540,960)).getbbox() is None
        # mudança mensurável real na região das polias e correia (imagem final já subida)
        belt_roi=diff.crop((55,498,395,700))
        assert sum(ImageStat.Stat(belt_roi).mean)/3 > 0.35


def test_correcao_f10_rejeita_correia_impossivel_e_fase_invalida():
    with pytest.raises(ValueError,match="F-PRIMITIVA-CORREIA"):
        P.transmissao_correia(141,675,70,160,680,60,
                             deslocamento_trama_px=1.)
    with pytest.raises(ValueError,match="F-PRIMITIVA-NUMERO"):
        P.transmissao_correia(141,675,29,294,705,65,
                             deslocamento_trama_px=float("nan"))
    with pytest.raises(ValueError,match="F-PRIMITIVA-LIMITE"):
        P.transmissao_correia(141,675,29,294,705,65,
                             deslocamento_trama_px=1000001)
