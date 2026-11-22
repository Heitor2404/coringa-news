"""QA que renderiza PIXELS do compressor completo, não só manifesto de peças."""
from __future__ import annotations

import io
import json
import math
from pathlib import Path

import cairosvg
import pytest
from PIL import Image, ImageChops, ImageStat

from src.v4.formatos.compressor_pv_core import (
    CompressorSpec, estado, limites_fases,
)
from src.v4.formatos import render_compressor_conjunto_2d as R


def load():
    return json.loads(R.MANIFESTO_PADRAO.read_text(encoding="utf8"))


def png_at(progress, manifest=None, **kwargs):
    svg = R.frame_svg(progress, manifest or load(), **kwargs)
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as im:
        return im.convert("RGB").copy()


def difference(a, b, crop):
    x = ImageChops.difference(a.crop(crop), b.crop(crop))
    return sum(ImageStat.Stat(x).mean) / 3.0


def shifted_bbox(box, amount=None):
    x1, y1, x2, y2 = box
    shift = R.AssemblyLayout().mechanism_lift_px if amount is None else amount
    return (x1, y1 - shift, x2, y2 - shift)


def dark_fraction(img, box):
    pix = img.crop(box).convert("RGB")
    pixels = list(pix.getdata())
    return sum(max(p) < 150 for p in pixels) / len(pixels)


def test_configuracao_correta_obrigatoria():
    p = load()
    assert R.validar_plano(p) is None
    assert p["configuracao"] == R.CONFIG_ID
    for wrong in ("compressor_parafuso", "motor_otto_4t"):
        bad = dict(p, configuracao=wrong) if "parafuso" in wrong else dict(p, processo=wrong)
        with pytest.raises(ValueError, match="CONFIGURACAO"):
            R.validar_plano(bad)
    with pytest.raises(ValueError, match="CONFIGURACAO"):
        R.validar_plano(dict(p, publicar=True))


def test_nao_finge_que_maquina_foi_inspecionada_por_visao():
    p = load()
    p["validacao_visao"] = "APROVADA"
    with pytest.raises(ValueError, match="VISAO-NAO-AUDITADA"):
        R.validar_plano(p)


def test_todas_as_pecas_requeridas_realmente_geram_elementos_svg():
    p = load()
    required = {x["papel"] for x in p["pecas"]}
    for t in (.03, .28, .7, .93):
        svg = R.frame_svg(t, p)
        for name in required:
            assert f'id="role-{name}"' in svg, name
        assert "COMPRESSOR DE AR" in svg
        assert "RECONSTRUÇÃO DE IMAGEM" not in svg
        assert "IGNIÇÃO" not in svg
        assert 'id="role-piston_cutaway"' in svg


def test_ciclo_pv_independe_da_apresentacao_visual():
    layout = R.AssemblyLayout()
    base = layout.spec()
    assert base.raio == layout.crank_radius
    assert base.biela == layout.connecting_rod
    for i in range(241):
        s = estado(i/240, base)
        distance = math.hypot(s.crank_x - base.eixo_x, s.crank_y - s.pistao_y)
        assert abs(distance-base.biela) < 1e-7
        assert not (s.admissao_aberta and s.descarga_aberta)
        assert 1 <= s.pressao_relativa <= base.pressao_saida_relativa + 1e-9


def test_motor_eletrico_gira_mais_rapido_que_bomba():
    layout=R.AssemblyLayout()
    assert layout.pump_wheel_radius > layout.motor_pulley_radius
    ratio = layout.pump_wheel_radius/layout.motor_pulley_radius
    assert 2 < ratio < 3
    assert abs(ratio*layout.motor_pulley_radius - layout.pump_wheel_radius)<1e-8


def test_janela_do_pistao_muda_de_posicao_em_quadros_reais():
    one = png_at(.05)
    two = png_at(.48)
    assert one.size == two.size == (540,960)
    diff = difference(one, two, shifted_bbox((245,470,342,610)))
    assert diff > 7, f"pistao parado na janela ({diff})"


def test_tanque_e_motor_aparecem_na_imagem_ao_mesmo_tempo():
    im = png_at(.25)
    # Não basta JSON dizer que as peças existem: regiões do quadro precisam
    # conter massa visual. Isso é heurística de pixels, não classificação VLM.
    assert dark_fraction(im, shifted_bbox((58,784,475,875))) > .1
    assert dark_fraction(im, shifted_bbox((70,600,202,735))) > .1
    assert dark_fraction(im, shifted_bbox((223,453,365,630))) > .1


def test_filtro_e_tubo_nao_somem_ao_mudar_fase():
    for t in (.04,.20,.71,.95):
        img = png_at(t)
        # Filtro (parte superior esquerda) e ligação vertical à direita
        assert dark_fraction(img, shifted_bbox((152,370,208,426))) > .15
        assert dark_fraction(img, shifted_bbox((429,421,453,745))) > .15


def test_estado_de_pressao_altera_a_janela_e_os_fluxos():
    reexp = png_at(.02)
    intake = png_at(.27)
    compress = png_at(.71)
    discharge = png_at(.94)
    # O miolo, e não só o texto no topo, deve mudar em cores e movimento.
    assert difference(intake, compress, shifted_bbox((243,415,347,611))) > 10
    assert difference(compress, discharge, shifted_bbox((243,415,347,611))) > 8
    # Os elementos extra-pistão mudam na admissão/descarga.
    assert difference(reexp, intake, shifted_bbox((128,370,220,426))) > .2
    assert difference(compress, discharge, shifted_bbox((410,399,457,748))) > .2


def test_licenca_fonte_nao_autoriza_video_publico():
    p=load()
    assert p["publicar"] is False
    assert p["midia_de_referencia_licenciada"] == "NAO_COPIADA"
    assert p["validacao_visao"] == "PENDENTE"


def test_mudancas_de_pressao_e_representacao_nao_sao_motor_otto():
    p=load()
    for t in (.01,.2,.6,.95):
        svg=R.frame_svg(t,p)
        assert "ignicao" not in svg.lower()
        assert "motor_otto" not in svg.lower()
        assert "MOTOR ELÉTRICO" in svg
    assert len(limites_fases(R.AssemblyLayout().spec())) == 4


def test_layout_nao_permite_maquina_sem_biela_valida():
    p=load()
    with pytest.raises(ValueError,match="PARAMETROS"):
        R.frame_svg(.3,p,layout=R.AssemblyLayout(connecting_rod=65))


def test_texto_editorial_respeita_faixa_superior_sem_deslocar_maquina():
    p=load()
    svg=R.frame_svg(.24,p)
    # Compactação real do cabeçalho, sem sobrepor a etiqueta FILTRO.
    assert 'x="42" y="108"' in svg
    assert 'x="42" y="148"' in svg
    assert 'x="42" y="180"' in svg
    assert '<rect width="540" height="202" fill="#122E43"/>' in svg
    assert '<rect x="42" y="190"' in svg
    assert 'x="56" y="225"' in svg
    assert 'x="258" y="225"' in svg
    assert R.EditorialHeader().max_mechanism_lift_px() == 100
    # A posição dos objetos físicos fica idêntica à prévia anterior.
    assert 'x="56.0" y="774.0"' in svg
    assert 'y="371"' in svg
    assert 'translate(294.00 705.00)' in svg


def test_conjunto_integral_sobe_100_sem_escala_e_texto_parado():
    p = load()
    high = R.frame_svg(.71, p)
    low = R.frame_svg(.71, p, layout=R.AssemblyLayout(mechanism_lift_px=0.))
    assert '<g id="machine-assembly" transform="translate(0 -100.0)">' in high
    assert '<g id="machine-assembly" transform="translate(0 -0.0)">' in low
    # Ninguém pode remover motor/tanque/pressão da translação única.
    start=high.index('<g id="machine-assembly"')
    end=high.index('<path d="M 52 905 H 488"')
    stage=high[start:end]
    for role in ("receiver_horizontal", "electric_motor", "drive_belt",
                 "finned_cylinder", "piston_cutaway", "discharge_pipe",
                 "compressor_head", "pump_flywheel"):
        assert f'id="role-{role}"' in stage, role
    assert 'id="pressure_card"' in stage
    # Elementos editoriais essenciais/rodapé ficam fora da cena móvel.
    assert 'x="42" y="108"' in high[:start]
    assert 'x="42" y="148"' in high[:start]
    assert 'x="42" y="180"' in high[:start]
    assert '<rect x="44" y="205"' in high[:start]
    assert 'PROVA PRIVADA' in high[end:]


def test_subida_conserva_fisica_e_relacoes_visualmente():
    p=load()
    high=png_at(.71)
    low=png_at(.71, layout=R.AssemblyLayout(mechanism_lift_px=0))
    # Região editorial não muda em 540×960.
    assert difference(high, low, (0,0,540,235)) == 0
    # Conjunto é realmente reposicionado, não apenas o texto/label.
    assert difference(high, low, (45,240,495,895)) > 10
    # Pressão/progresso dependem exclusivamente de P-V, não da posição.
    assert R.AssemblyLayout().spec() == R.AssemblyLayout(mechanism_lift_px=0).spec()


def test_nao_subir_alem_da_area_disponivel():
    with pytest.raises(ValueError,match="LIFT-AREA-SEGURA"):
        R.frame_svg(.3,load(),layout=R.AssemblyLayout(mechanism_lift_px=101))
    with pytest.raises(ValueError,match="LIFT-AREA-SEGURA"):
        R.frame_svg(.3,load(),layout=R.AssemblyLayout(mechanism_lift_px=-8))

def test_editorial_compacto_nao_encosta_filtro_e_conserva_rodape():
    e = R.EditorialHeader()
    m = R.AssemblyLayout()
    assert e.header_height < 210
    assert e.progress_y + 6 < e.header_height
    assert e.category_y > e.header_height
    # Fonte FILTRO 12px, baseline geométrica 354, folga >=7px.
    assert 354 - 12 - m.mechanism_lift_px >= e.category_y + e.category_height + 7
    assert 900 - m.mechanism_lift_px < 905
    a, b = png_at(.03), png_at(.95)
    assert difference(a,b,(0,0,540,235)) > 0  # fase e progressão
    assert difference(a,b,(0,28,540,52)) == 0  # marca fica fixa
