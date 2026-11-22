"""Compressor Pv one revolution: automatic valves, never Otto ignition."""
from __future__ import annotations

import io
import json
import math
import shutil
import subprocess

import cairosvg
import pytest
from PIL import Image

from src.v4.formatos.compressor_pv_core import (
    CompressorSpec, estado, limites_fases, ESTADOS,
)
from src.v4.formatos.render_compressor_pv_2d import draw_svg, renderizar


def test_um_giro_quatro_etapas_automaticas():
    stages = {}
    samples = [estado(i/240) for i in range(241)]
    for item in samples:
        stages.setdefault(item.estado, []).append(item.progresso)
    assert list(stages)==list(ESTADOS)
    assert len(stages["REEXPANSAO_RESIDUAL"]) >= 10
    assert len(stages["ADMISSAO_AR"]) >= 70
    assert len(stages["COMPRESSAO_AR"]) >= 65
    assert len(stages["DESCARGA_PRESSURIZADA"]) >= 10
    bounds=limites_fases()
    assert .07 < bounds["ADMISSAO_AR"]["de"] < .16
    assert .81 < bounds["DESCARGA_PRESSURIZADA"]["de"] < .94


def test_pistao_e_biela_nao_se_desconectam_241_quadros():
    g=CompressorSpec()
    for i in range(241):
        s=estado(i/240,g)
        dist=math.hypot(s.crank_x-g.eixo_x,s.crank_y-s.pistao_y)
        assert abs(dist-g.biela)<1e-8
        assert .0 <= s.fracao_curso<=1.0
        assert .059<=s.volume_relativo<=1.061
        assert 1-1e-6 <= s.pressao_relativa<=g.pressao_saida_relativa+1e-6


def test_valvulas_nunca_abrem_juntas_e_tem_sentidos_corretos():
    for i in range(241):
        s=estado(i/240)
        assert not (s.admissao_aberta and s.descarga_aberta)
        if s.admissao_aberta:
            assert s.sentido_pistao=="DESCENDO"
            assert abs(s.pressao_relativa-1)<1e-6
        if s.descarga_aberta:
            assert s.sentido_pistao=="SUBINDO"
            assert abs(s.pressao_relativa-5)<1e-6


def test_ciclo_de_pressao_respeita_reexpansao_e_compressao():
    data=[estado(i/240) for i in range(241)]
    pre=[x.pressao_relativa for x in data if x.estado=="REEXPANSAO_RESIDUAL"]
    comp=[x.pressao_relativa for x in data if x.estado=="COMPRESSAO_AR"]
    assert pre[0]>pre[-1] and pre[0]>=4.99
    assert comp[0]<comp[-1] and comp[-1]>4.7
    assert all(a >= b-1e-7 for a,b in zip(pre,pre[1:]))
    assert all(a <= b+1e-7 for a,b in zip(comp,comp[1:]))


def test_compressor_nao_tem_ignicao_ou_valvulas_com_came_de_otto():
    for t in (.02,.23,.63,.92):
        frame=draw_svg(t)
        assert "COMPRESSOR DE AR" in frame
        assert "IGNIÇÃO" not in frame
        assert "RECONSTRUÇÃO VETORIAL" not in frame
        assert "P–V" in frame and "TANQUE" in frame
        assert "pistao" not in frame.lower()  # geometria, nao título de motor
    assert "O AR ENTRA" in draw_svg(.25)
    assert "O VOLUME DIMINUI" in draw_svg(.7)
    assert "AR SOB PRESSÃO SAI" in draw_svg(.92)
    assert "AR RESIDUAL EXPANDE" in draw_svg(.03)


def test_visuais_valvulas_tem_elementos_moveis_e_fluxo_visivel():
    a=draw_svg(.25)
    b=draw_svg(.68)
    c=draw_svg(.95)
    assert '<circle cx="' in a and 'fill="#168EA6"' in a
    assert 'fill="#D97936"' in c
    assert 'fill="#168EA6"' not in b
    assert 'fill="#D97936"' not in b
    # Posição de válvula muda apenas por diferença de pressão.
    assert 'M 208 384' in a
    assert 'M 329 360' in c
    assert 'M 329 372' in b
    assert 'M 208 372' in b


def test_render_de_quatro_fases_em_png_9x16():
    for t in (.03,.25,.70,.94):
        raw=cairosvg.svg2png(bytestring=draw_svg(t).encode())
        with Image.open(io.BytesIO(raw)) as im:
            assert im.size==(540,960)
            assert im.mode in ("RGB","RGBA")


def test_parametros_fora_de_faixa_sao_bloqueados():
    with pytest.raises(ValueError,match="PARAMETROS"):
        estado(.5,CompressorSpec(biela=70))
    with pytest.raises(ValueError,match="PROGRESSO"):
        estado(-.1)
    with pytest.raises(ValueError,match="PROGRESSO"):
        estado(float("nan"))


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg indisponivel")
def test_video_fisico_real_sem_voz_e_sem_publicacao(tmp_path):
    path=tmp_path/"compressor.mp4"
    result=renderizar(path,fps=24,duracao=6)
    assert result["publicar"] is False
    assert result["referencia_compressor_animada_medida"] is False
    assert "NAO_REFERENCE_RECONSTRUCTED" in result["estado"]
    assert path.exists() and path.stat().st_size>50_000
    meta=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_entries",
        "format=duration:stream=codec_type,width,height",
        "-of","json",str(path)]))
    stream=next(x for x in meta["streams"] if x["codec_type"]=="video")
    assert (stream["width"],stream["height"])==(540,960)
    assert not any(x["codec_type"]=="audio" for x in meta["streams"])
    assert abs(float(meta["format"]["duration"])-6)<.1

def test_duto_continuo_ate_tanque_e_legenda_em_area_util():
    frame=draw_svg(.93)
    assert 'M 499 338 V 625 H 467 V 656' in frame
    assert 'M 467 656 V 680' in frame
    assert 'cx="498.0"' in frame
    # Marca pode estar no topo; texto explicativo fica abaixo da interface.
    assert 'x="44" y="155"' in frame
    assert 'x="44" y="197"' in frame
    assert 'x="44" y="233"' in frame
