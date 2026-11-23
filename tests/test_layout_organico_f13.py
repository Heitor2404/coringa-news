"""F13 — separa overlay orgânico observado e AD; texto lateral sem escala/camera."""
from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from PIL import Image

from src.v4.formatos import compositor_cinematico_parametrico_2d as M
from src.v4.formatos import qa_ui_organico_f13 as Q
from src.v4.formatos import layout_organico_f13 as H

SCENES=Path(__file__).resolve().parents[1]/"src/v4/formatos/cenas_parametricas"


def scene(name="curto"):
    return M.carregar(SCENES/f"biela_manivela_curso_{name}.json")


def stage(xml):
    nodes=[n for n in ET.fromstring(xml).iter() if n.attrib.get("id")=="machine-stage"]
    assert len(nodes)==1
    return ET.tostring(nodes[0])


@pytest.mark.parametrize("mode",["curto","longo"])
def test_f13_mesma_maquina_f12_sem_zoom_pan_ou_mudanca_de_fisica(mode):
    s=scene(mode)
    for t in (.3,1.1,3.6,6.7,8.6):
        before=M.frame_svg(s,t,transmissao_animada=True,
                           enquadramento_mobile="hero_elevado_f12")
        after=M.frame_svg(s,t,transmissao_animada=True,
                          enquadramento_mobile="hero_lateral_f13")
        assert stage(before)==stage(after)
        assert 'data-layout="hero_lateral_f13"' in after
        assert 'id="f13-essential-pocket"' in after
        assert 'id="f13-essential-title"' in after
        assert 'id="f13-essential-phase"' in after
        assert 'id="f13-essential-detail"' in after
        assert s["publish"] is False and s["visual_approval"] is False
        assert "data-belt-travel" in after
    assert "f13-essential-pocket" not in M.frame_svg(s,3.6)
    assert M.frame_svg(s,3.6)==M.frame_svg(s,3.6,enquadramento_mobile=None)


def test_f13_titulo_real_abaixo_de_topo_observado_sem_colidir_com_cilindro():
    s=scene()
    b=Q.avaliar(s,3.6,"hero_elevado_f12")
    a=Q.avaliar(s,3.6,"hero_lateral_f13")
    for key in ("title","phase"):
        assert a["essential_text"][key]["bbox"][1]>110
        for profile in Q._profiles():
            if profile["placement"]=="organic":
                assert a["essential_text"][key]["ui_risks"][profile["id"]]==0,profile
    assert b["essential_text"]["title"]["ui_risks"]["reels_organic_android_oct2026"]>.85
    assert a["essential_text"]["title"]["ui_risks"]["reels_organic_android_oct2026"]==0
    title=a["essential_text"]["title"]["bbox"]
    cyl=Q.Q.medir(M.frame_svg(s,3.6,transmissao_animada=True,
                              enquadramento_mobile="hero_lateral_f13"),
                  roles=("cylinder",))["cylinder"]["pixel_bbox"]
    assert title[2]<cyl[0]
    assert a["roles"]["flywheel"]["bbox"]==b["roles"]["flywheel"]["bbox"]


def test_perfis_organicos_nao_herdam_area_ads_ou_citados_sem_prova():
    p=Q._profiles()
    assert len(p)==5
    assert len([x for x in p if x["placement"]=="organic"])==4
    reels=next(x for x in p if x["id"]=="reels_organic_android_oct2026")
    ads=next(x for x in p if x["id"]=="reels_ads_guide_conservative")
    assert reels["bottom"]==280 and ads["bottom"]==672
    assert reels["top"]==150 and ads["top"]==269
    assert Q.mask(reels).size==(540,960)
    assert Q.mask(ads).size==(540,960)
    assert Q.mask(reels).getpixel((270,720))==0
    assert Q.mask(ads).getpixel((270,720))==255
    assert Q.mask(reels).getpixel((490,460))==255
    assert Q.mask(reels).getpixel((270,150))==0
    with pytest.raises(ValueError,match="F13-UI-PERFIL_INVALIDO"):
        Q.mask({"placement":"ads"})


def test_bloqueia_texto_que_nao_cabe_ou_layout_invalido():
    with pytest.raises(ValueError,match="F13-HOOK-"):
        H._wrap("ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ",169,21,True,2)
    s=scene()
    f12=M.frame_svg(s,3.6,transmissao_animada=True,
                    enquadramento_mobile="hero_elevado_f12")
    f13,meta=H.aplicar(f12)
    assert meta["scale_reduced"] is False
    assert meta["publish"] is False
    with pytest.raises(ValueError,match="F13-HOOK-EXIGE_F12"):
        H.aplicar(f13)
    with pytest.raises(ValueError,match="F13-HOOK-EXIGE_F12"):
        H.aplicar(M.frame_svg(s,3.6))


def test_qa_dispositivo_ausente_publicacao_fechada_e_prancha_real(tmp_path):
    s=scene()
    r=Q.analisar(s,tmp_path)
    assert r["screenshot_user_device"] is False
    assert r["publisher_certification"] is False
    assert r["publish"] is False
    assert r["no_auto_shrink"] is True
    assert set(r["samples"])=={"1.1","3.6","6.7"}
    assert r["samples"]["3.6"]["organic_f13"]["essential_text"]["title"]["pixels"]>100
    output=tmp_path/(s["id"]+"_F13_FONTES_UI_CONTATO.jpg")
    assert output.is_file()
    with Image.open(output) as im:
        assert im.size==(1620,510)
    output2=tmp_path/(s["id"]+"_F13_UI_RISCOS.json")
    assert output2.is_file()
    assert json.loads(output2.read_text("utf8"))["visual_approval"] is False
