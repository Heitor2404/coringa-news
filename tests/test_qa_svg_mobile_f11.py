"""F11 — reuso de correia em dois rigs e auditoria por pixels de area de UI."""
from __future__ import annotations

import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from PIL import Image

from src.v4.formatos import compositor_cinematico_parametrico_2d as M
from src.v4.formatos import qa_svg_mobile_f11 as Q
from src.v4.formatos import layout as L
from src.v4.formatos import primitivas_fisicas_parametricas as P
from src.v4.formatos import render_compressor_conjunto_2d as C

DIR=Path(__file__).resolve().parents[1]/"src/v4/formatos/cenas_parametricas"


def scenes():
    return (M.carregar(DIR/"biela_manivela_curso_curto.json"),
            M.carregar(DIR/"biela_manivela_curso_longo.json"))


def belt_mark(xml):
    tree=ET.fromstring(xml)
    nodes=[n for n in tree.iter() if n.get("data-belt-travel") is not None]
    assert len(nodes)==1
    return nodes[0]


@pytest.mark.parametrize("idx",[0,1])
def test_reuso_motor_anima_correa_com_geometria_da_f10(idx):
    scene=scenes()[idx]
    for t in (.0,.9,2.6,4.5,7.8):
        baseline=M.frame_svg(scene,t)
        assert "data-belt-travel" not in baseline
        new=M.frame_svg(scene,t,transmissao_animada=True)
        assert "data-belt-travel" in new
        state=M.estado(scene,t)
        band=belt_mark(new)
        expected=state["theta"]*scene["crank"]["wheel"]
        assert math.isclose(float(band.attrib["data-belt-travel"]),expected,abs_tol=.001)
        # O operador matematico/ilustrativo usado na F10 e mesmo da F7.
        belt=P.transmissao_correia(
            scene["motor"]["cx"],scene["motor"]["cy"],scene["motor"]["pulley"],
            scene["crank"]["cx"],scene["crank"]["cy"],scene["crank"]["wheel"],
            largura=11,deslocamento_trama_px=expected)
        assert belt in new
        assert new.index('id="role-drive_belt"')<new.index('id="role-flywheel"')
        assert 'id="role-piston"' in new


def test_default_antes_conservado_byte_a_byte_na_chamada_publica():
    for s in scenes():
        t=2.7
        assert M.frame_svg(s,t)==M.frame_svg(s,t,transmissao_animada=False)
        assert M.estado(s,t)==M.estado(s,t)
        assert s["publish"] is False and s["visual_approval"] is False


def test_modo_animado_nao_desloca_a_camera():
    for s in scenes():
        original=[]
        animated=[]
        for t in (.1,2.2,4.7,7.9):
            b=M.frame_svg(s,t)
            a=M.frame_svg(s,t,transmissao_animada=True)
            find=lambda xml:re.search(r'id="machine-stage" transform="([^"]+)"',xml).group(1)
            original.append(find(b))
            animated.append(find(a))
        assert len(set(original))==1
        assert original==animated


def test_mascaras_herdadas_dos_perfis_conservadores_e_nao_chutadas():
    assert Q.PROFILE_NAMES==tuple(L.CFG["ativos_seguros"])
    for name in Q.PROFILE_NAMES:
        mask=Q.mascara(name)
        assert mask.size==(540,960)
        assert mask.getpixel((2,2))==255
        assert mask.getpixel((538,950))==255
        assert mask.getpixel((270,250))==0
        assert len(Q._rects(name))==4
    with pytest.raises(ValueError,match="F11-ZONA-PERFIL_DESCONHECIDO"):
        Q.mascara("instagram_reels")


def test_medicao_real_do_pistao_por_pixels_nao_envelope_da_camera():
    scene=scenes()[0]
    frame=M.frame_svg(scene,3.6,transmissao_animada=True)
    result=Q.medir(frame)
    assert set(result)==set(Q.CRITICAL)
    for role,entry in result.items():
        assert entry["visible_pixel_area"]>25,role
        assert len(entry["pixel_bbox"])==4
        assert 0<=entry["max_overlap_fraction"]<=1
        assert set(entry["overlap_fraction_per_platform"])==set(Q.PROFILE_NAMES)
    # Caixa REAL da peça do pistão é menor do que envelope de movimento
    # conservador da câmera e muda de posição com o curso.
    piston=result["piston"]["pixel_bbox"]
    envelope=__import__("src.v4.formatos.camera_causal_svg",fromlist=["CAMERAS"]).CAMERAS["familias"][M.FAMILY]["roles"]["piston"]
    assert (piston[2]-piston[0])*(piston[3]-piston[1]) < (envelope[2]-envelope[0])*(envelope[3]-envelope[1])


def test_medidor_rejeita_ator_inexistente_svg_invalido_e_formato_falso():
    frame=M.frame_svg(scenes()[0],.2)
    with pytest.raises(ValueError,match="F11-ZONA-ATOR_AUSENTE_OU_DUPLICADO"):
        Q.medir(frame,roles=("unknown_actor",))
    with pytest.raises(ValueError,match="F11-ZONA-SVG-INVALIDO"):
        Q.medir("<svg>")
    wrong=frame.replace('width="540"','width="300"',1)
    with pytest.raises(ValueError,match="F11-ZONA-FORMATO"):
        Q.medir(wrong)


def test_qa_nao_encolhe_automaticamente_e_exige_revisao(tmp_path):
    r=Q.analisar(scenes()[0],tmp_path,animation=True)
    assert r["status"]=="INSPECAO_UI_HUMANA_PENDENTE"
    assert r["publish"] is False
    assert r["automatically_shrink_machine"] is False
    assert r["masks_are_conservative_estimates"] is True
    assert 0<=r["worst_observed_overlap_fraction"]<=1
    assert len(r["windows"])==3
    sheet=tmp_path/(scenes()[0]["id"]+"_F11_MASCARAS_PERFIL_SIMULADO.jpg")
    with Image.open(sheet) as im:
        assert im.size==(2160,1002)


def test_compressores_podem_seguir_opt_in_independentes():
    manifest=__import__("json").loads(C.MANIFESTO_PADRAO.read_text("utf8"))
    old=C.frame_svg(.23,manifest)
    improved=C.frame_svg(.23,manifest,transmissao_parametrica=True)
    assert "data-belt-travel" not in old
    assert "data-belt-travel" in improved
    assert "PROVA PRIVADA" in improved
