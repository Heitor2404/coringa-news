"""F14 — regressões físicas e visuais de uma família NOVA: par de engrenagens."""
from __future__ import annotations

import copy
import io
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
import pytest
from PIL import Image,ImageChops,ImageStat,ImageDraw

from src.v4.formatos import engrenagens_parametricas_f14 as G
from src.v4.formatos import compositor_engrenagens_f14 as M
from src.v4.formatos import compositor_cinematico_parametrico_2d as F7
from src.v4.formatos import qa_ui_organico_f13 as UI
from src.v4.formatos import qa_svg_mobile_f11 as Q

DIR=Path(__file__).resolve().parents[1]/"src/v4/formatos/cenas_parametricas"
SAMPLES=[DIR/"redutor_engrenagens_18x36.json",
         DIR/"redutor_engrenagens_24x36.json"]

def scenes():
    return [M.load(f) for f in SAMPLES]

def _img(svg):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode("utf8")))) as im:
        return im.convert("RGB").copy()

@pytest.mark.parametrize("index,expected",[ (0,2.),(1,1.5) ])
def test_duas_cenas_mesmo_kernel_com_proporcao_exata(index,expected):
    scene=scenes()[index]
    pair=M.validate(scene)
    assert math.isclose(pair.ratio,expected,rel_tol=1e-12)
    assert math.isclose(pair.center_distance,scene["gears"]["module"]*(scene["gears"]["z1"]+scene["gears"]["z2"])/2,abs_tol=1e-10)
    assert math.isclose(pair.cx2-pair.cx1,pair.center_distance,abs_tol=1e-10)
    assert math.isclose(pair.driving.pitch/pair.driven.pitch,1/expected)
    assert math.isclose(pair.driving.base/pair.driving.pitch,math.cos(math.radians(20)))
    assert scene["publish"] is False and scene["industrial_approval"] is False

@pytest.mark.parametrize("index",[0,1])
def test_movimento_inverso_sem_slip_angular(index):
    scene=scenes()[index]
    p=M.validate(scene)
    phase=math.pi+math.pi/p.driven.z
    for t in (0,.31,2.4,4.49,4.5,6.7,9):
        st=M.state(scene,t)
        assert math.isclose(st["driver_angle_rad"],4*math.pi*t/9,abs_tol=1e-12)
        assert math.isclose(st["driven_angle_rad"],phase-st["driver_angle_rad"]*p.driving.z/p.driven.z,abs_tol=1e-12)
        assert st["opposite_rotation"] is True
        assert st["pitch_tangential_error"]<1e-8
        assert st["driver_teeth"]==p.driving.z
        assert st["driven_teeth"]==p.driven.z
    assert (M.state(scene,9)["driven_angle_rad"]-M.state(scene,0)["driven_angle_rad"])<0
    assert scene["driver_revolutions"]==2

def test_dentes_involutos_forma_continua_com_raiz_gerada():
    for scene in scenes():
        p=M.validate(scene)
        for gear in (p.driving,p.driven):
            pts=G.outline(gear)
            assert len(pts)==gear.z*22
            for x,y in pts:
                r=math.hypot(x,y)
                assert gear.root-1e-8<=r<=gear.tip+1e-8
            one=G.gear_svg(gear,110,500,22,role="input_gear",color="silver")
            assert one.count('data-profile="involute_no_root_fillet_lab"')==1
            assert one.count("<path")>=2
            ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">'+one+'</svg>')

@pytest.mark.parametrize("index",[0,1])
def test_enquadramento_gera_atores_reais_e_camera_estatica(index):
    scene=scenes()[index]
    frames=[]
    for t in (.3,2.2,4.7,6.8):
        svg=M.frame(scene,t)
        G.svg_actors_check(svg)
        root=ET.fromstring(svg)
        assert root.get("data-family")==M.FAMILY
        roles=[node for node in root.iter() if (node.get("id") or "").startswith("role-")]
        assert len(roles)==2
        assert [x.get("data-teeth") for x in roles]==[
           str(scene["gears"]["z1"]),str(scene["gears"]["z2"])]
        stage=[node for node in root.iter() if node.get("id")=="machine-stage"]
        assert len(stage)==1 and stage[0].get("transform")=="translate(0 0)"
        im=_img(svg)
        assert im.size==(540,960)
        frames.append(im)
    diff=ImageChops.difference(frames[0].crop((93,379,450,647)),
                               frames[1].crop((93,379,450,647)))
    assert sum(ImageStat.Stat(diff).mean)/3 > .3

@pytest.mark.parametrize("invalid,code",[
    ({"z1":0},"DENTES"),
    ({"z1":3.2},"DENTES"),
    ({"z2":999},"DENTES"),
    ({"module":0},"PARAMETRO"),
    ({"module":float("nan")},"PARAMETRO"),
    ({"input_x":0},"PARAMETRO"),
    ({"center_y":900},"PARAMETRO"),
])
def test_nao_aceita_geometria_alucinada(invalid,code):
    scene=scenes()[0]
    scene["gears"].update(invalid)
    with pytest.raises(ValueError,match="F14-GEAR-"+code):
        M.validate(scene)


@pytest.mark.parametrize("index",[0,1])
def test_dentes_nao_se_penetraram_na_rasterizacao_2d(index):
    """40 poses/ciclo, tolerância de 30 pixels discretos no contato.

    Não certifica folga industrial, mas captura interpenetração
    grosseira por fase/centros incorretos.
    """
    p=M.validate(scenes()[index])
    points=[G.outline(p.driving),G.outline(p.driven)]
    max_overlap=0
    for k in range(40):
        st=M.state(scenes()[index],9*k/40)
        polys=[]
        for pts,x,ang in zip(points,(p.cx1,p.cx2),
                             (st["driver_angle_rad"],st["driven_angle_rad"])):
            c,sn=math.cos(ang),math.sin(ang)
            xy=[(x+c*u-sn*v,p.cy+sn*u+c*v) for u,v in pts]
            layer=Image.new("L",(540,960),0)
            ImageDraw.Draw(layer).polygon(xy,fill=255)
            polys.append(layer)
        collision=ImageChops.multiply(*polys).histogram()[-1]
        max_overlap=max(max_overlap,collision)
    assert max_overlap<=30,max_overlap


@pytest.mark.parametrize("index",[0,1])
def test_titulo_essencial_fica_fora_das_mascaras_ui_de_terceiros(index):
    scene=scenes()[index]
    xml=M.frame(scene,2.8)
    root=ET.fromstring(xml)
    title=[n for n in root if n.get("data-essential")=="machine_title"]
    assert len(title)==1 and title[0].get("y")=="162"
    original=Q._raster(xml)
    root.remove(title[0])
    removed=Q._raster(ET.tostring(root,encoding="unicode"))
    pixels=Q._threshold_difference(original,removed)
    assert Q._count(pixels)>100
    for profile in UI._profiles():
        overlap=ImageChops.multiply(pixels,UI.mask(profile))
        assert Q._count(overlap)/Q._count(pixels)<.035,profile["id"]

def test_nao_habilita_publicacao_e_nao_confunde_fonte_tecnica_com_imagem():
    scene=scenes()[0]
    for field,value in [
        ("publish",True),("visual_approval",True),("industrial_approval",True),
    ]:
        changed=copy.deepcopy(scene)
        changed[field]=value
        with pytest.raises(ValueError,match="F14-COMPOSITOR-CONTRATO"):
            M.validate(changed)
    for field,value in [
        ("url","https://fake.example.com/manual"),
        ("source_is_license",True),
        ("external_pixels_copied",True),
        ("scope","LICENCA_APROVADA"),
    ]:
        changed=copy.deepcopy(scene)
        changed["source"][field]=value
        with pytest.raises(ValueError,match="F14-COMPOSITOR-PROVENIENCIA"):
            M.validate(changed)

def test_nao_aceita_corpo_cena_sem_apresentacao_fisica_ou_atores():
    scene=scenes()[0]
    scene["phases"][0]["action"]="fingir_maquina"
    with pytest.raises(ValueError,match="F14-COMPOSITOR-FASES"):
        M.validate(scene)
    scene=scenes()[0]
    scene["gears"]["z1"]=48
    with pytest.raises(ValueError,match="F14-GEAR-MAQUINA_FORA_PALCO|F14-COMPOSITOR-PALCO_MECANICO|F14-COMPOSITOR-REDEMOINHO_SEM_REDUCAO"):
        M.validate(scene)

def test_f14_nao_muda_f7_ou_o_catalogo_de_producao():
    p=DIR/"biela_manivela_curso_curto.json"
    before=F7.load(p) if hasattr(F7,"load") else F7.carregar(p)
    svg=F7.frame_svg(before,1.7)
    assert "role-input_gear" not in svg
    assert 'data-family="external_spur_gear_reduction"' not in svg
    assert "data-visual-identity" in svg
    assert G.SOURCE.startswith("https://khkgears.net/")
    assert G.RIGHTS=="PRINCIPIO_MECANICO_NAO_LICENCA_IMAGEM"
