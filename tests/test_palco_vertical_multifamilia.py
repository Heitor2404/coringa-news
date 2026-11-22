"""Regressão de palco compartilhado com DOIS mecanismos físicos distintos.

Exercita os SVG verdadeiros (não apenas manifesto) sem Gemini/Claude.
A qualidade estética e as zonas de UI de cada app ainda dependem de revisão.
"""
from __future__ import annotations

import io
import json
import math

import cairosvg
import pytest
from PIL import Image, ImageChops, ImageStat

from src.v4.formatos.palco_vertical import CaixaVisivel, PalcoVertical
from src.v4.formatos import render_compressor_conjunto_2d as C
from src.v4.formatos import render_reconstrucao_causal_2d as O


def _scene():
    m = json.loads((O.Path(__file__).resolve().parents[1] /
        "docs/v4/formatos/reference_first/otto_48f_measured_motion.json").read_text("utf8"))
    s = json.loads((O.Path(__file__).resolve().parents[1] /
        "docs/v4/formatos/reference_first/otto_48f_causal_reviewed_scene.json").read_text("utf8"))
    return m,s


def _png(svg):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as im:
        return im.convert("RGB").copy()


def _delta(a,b,roi):
    return sum(ImageStat.Stat(ImageChops.difference(a.crop(roi), b.crop(roi))).mean) / 3


def test_mecanismos_diferentes_usam_mesmo_solvedor_sem_ajuste_por_tema():
    compressor=C.EditorialHeader().palco()
    motor=O.PALCO_OTTO
    assert isinstance(compressor, PalcoVertical)
    assert isinstance(motor, PalcoVertical)
    assert compressor.deslocar()==100
    assert motor.deslocar()==28
    assert compressor.faixa_resultante()==(242,800)
    assert motor.faixa_resultante()==(245,860)
    assert compressor.deslocar(0)==motor.deslocar(0)==0
    assert compressor.caixa != motor.caixa


def test_subida_do_compressor_mantem_pecas_fisica_e_texto_livre():
    p=json.loads(C.MANIFESTO_PADRAO.read_text("utf8"))
    for t in (.02,.2,.5,.72,.94):
        high=C.frame_svg(t,p)
        low=C.frame_svg(t,p,layout=C.AssemblyLayout(mechanism_lift_px=0))
        assert 'transform="translate(0 -100.0)"' in high
        assert 'id="role-electric_motor"' in high
        assert 'id="role-receiver_horizontal"' in high
        a,b=_png(high),_png(low)
        assert a.size==b.size==(540,960)
        # Marca+cabeçalho NÃO são objetos da máquina.
        assert _delta(a,b,(0,0,540,235))==0
        assert _delta(a,b,(50,250,492,805))>5


def test_motor_otto_usa_mesmo_solvedor_sem_herdar_descricao_de_compressor():
    mov,scene=_scene()
    for t in (.1,.35,.56,.85):
        new=O.svg_frame(mov,scene,t)
        old=O.svg_frame(mov,scene,t,subida_palco_px=0)
        assert 'id="mechanical-stage" transform="translate(0 -28.0)"' in new
        assert 'id="mechanical-stage" transform="translate(0 -0.0)"' in old
        assert "COMPRESSOR DE AR" not in new
        assert "MOTOR DE 4 TEMPOS" in new
        a,b=_png(new),_png(old)
        assert a.size==b.size==(540,960)
        assert _delta(a,b,(0,0,540,240))==0
        assert _delta(a,b,(16,245,524,900))>3


@pytest.mark.parametrize("bad",[-1,101,math.inf,math.nan])
def test_queima_area_do_compressor_bloqueia(bad):
    p=json.loads(C.MANIFESTO_PADRAO.read_text("utf8"))
    with pytest.raises(ValueError,match="LIFT-AREA-SEGURA"):
        C.frame_svg(.33,p,layout=C.AssemblyLayout(mechanism_lift_px=bad))


@pytest.mark.parametrize("bad",[-1,29,math.inf,math.nan])
def test_queima_area_de_motor_bloqueia(bad):
    mov,scene=_scene()
    with pytest.raises(ValueError,match="SUBIDA-FORA-DA-AREA"):
        O.svg_frame(mov,scene,.25,subida_palco_px=bad)


def test_motor_excessivo_nunca_encolhe_ou_corta_automaticamente():
    with pytest.raises(ValueError,match="INTERSECAO"):
        PalcoVertical(540,960,CaixaVisivel(20,400,520,959),
                     editorial_termina_y=230,rodape_comeca_y=650).deslocar(0)
    with pytest.raises(ValueError,match="GEOMETRIA"):
        PalcoVertical(540,960,CaixaVisivel(-5,400,520,850),
                     editorial_termina_y=230,rodape_comeca_y=900).deslocar()
    with pytest.raises(ValueError,match="INVADIRIA"):
        PalcoVertical(540,960,CaixaVisivel(20,200,520,850),
                     editorial_termina_y=230,rodape_comeca_y=900).deslocar()


def test_cada_familia_ciclo_independente_e_publicacao_bloqueada():
    p=json.loads(C.MANIFESTO_PADRAO.read_text("utf8"))
    m,s=_scene()
    assert p["publicar"] is False and s["publicar"] is False
    assert O.validar(m,s) is None
    assert C.validar_plano(p) is None
    assert C.AssemblyLayout().spec().raio==42
    assert O.pose(.1,m)["rod_distance"]==pytest.approx(O.pose(.1,m)["rod_nominal"])
