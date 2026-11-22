"""Reference-first: prova de render original a partir de medição REAL do Otto.

Não confundir com extração automática de válvulas (fases ainda revisadas
manualmente). Teste não depende de Gemini nem de vídeos da internet.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path

import cairosvg
import pytest
from PIL import Image, ImageChops, ImageStat

from src.v4.formatos import render_reconstrucao_causal_2d as R
from src.v4.formatos import rastrear_movimento_referencia as TRACK


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/v4/formatos/reference_first"


def load():
    m = json.loads((DATA/"otto_48f_measured_motion.json").read_text("utf8"))
    s = json.loads((DATA/"otto_48f_causal_reviewed_scene.json").read_text("utf8"))
    c = json.loads((DATA/"otto_48f_tracker_config.json").read_text("utf8"))
    return m, s, c


def test_fonte_de_48_frames_rastreada_sem_inventar_termodinamica():
    m, s, c = load()
    assert len(m["posicoes_y_px"]) == m["quadros"] == 48
    assert len(m["origem_sha256"]) == 64
    assert c["sha256"] == s["origem_sha256"] == m["origem_sha256"]
    assert c["processo"] == s["processo"] == "motor_otto_4t"
    assert m["revolucoes"] == 2
    assert m["ajuste_geometrico"]["erro_medio_px"] < .25
    assert m["qualidade_correlacao"]["min"] > .79
    assert m["valvulas_validadas"] is False
    assert m["reconstrucao_original"] is False
    assert s["revisao_humana"] == "REVISADA_NA_FONTE"
    assert s["publicar"] is False
    assert R.validar(m, s) is None


def test_biela_conservada_ao_longo_de_ciclo_192_frames():
    m, s, _ = load()
    R.validar(m, s)
    poses = [R.pose(i/192, m) for i in range(192)]
    for state in poses:
        assert abs(state["rod_distance"]-state["rod_nominal"]) < 1e-8
        assert state["piston_min_y"]-.01 <= state["piston_y"] <= state["piston_max_y"]+.01
        assert 386 <= state["piston_y"]-54 <= 560
        assert state["crank_x"]-92 >= 97
        assert state["crank_x"]+92 <= 443
    # Dois giros, quatro tempos. Em cada volta, há um ciclo sobe/desce.
    for offset in (0, 96):
        assert poses[offset+24]["piston_y"] > poses[offset]["piston_y"]+60
        assert poses[offset+48]["piston_y"] > poses[offset+24]["piston_y"]+30
        assert poses[offset+72]["piston_y"] < poses[offset+48]["piston_y"]-40


def test_otro_reconstrucao_tem_fases_visuais_diferentes():
    m, s, _ = load()
    times=[.125,.375,.625,.875]
    svg=[R.svg_frame(m,s,t) for t in times]
    assert len(set(svg)) == 4
    assert "ADMISSÃO" in svg[0]
    assert "COMPRESSÃO" in svg[1]
    assert "IGNIÇÃO E EXPANSÃO" in svg[2]
    assert "ESCAPE" in svg[3]
    assert 'stroke="#1CA6B6"' in svg[0]
    assert 'stroke="#C77D25"' in svg[1]
    assert 'fill="#FF6C32"' in R.svg_frame(m,s,.53)
    assert 'stroke="#D77F4B"' in svg[3]
    assert all("MOTOR DE 4 TEMPOS" in x for x in svg)
    assert all("RECONSTRUÇÃO VETORIAL" in x for x in svg)


def test_png_em_quatro_fases_legivel_no_formato_celular(tmp_path):
    m,s,_=load()
    frames=[]
    for i,t in enumerate((.10,.35,.56,.85)):
        raw=cairosvg.svg2png(bytestring=R.svg_frame(m,s,t).encode())
        with Image.open(io.BytesIO(raw)) as image:
            assert image.size == (540,960)
            image.convert("RGB").save(tmp_path / f"phase_{i}.png")
            frames.append(image.convert("RGB").copy())
    pairs=[ImageChops.difference(frames[0],p) for p in frames[1:]]
    assert all(sum(ImageStat.Stat(x).mean)/3 > 2.5 for x in pairs)


def test_compressor_nao_pode_herdar_grafo_otto():
    m,s,_=load()
    changed=dict(s,processo="compressor_alternativo")
    with pytest.raises(ValueError, match="PROCESSO-INVALIDO"):
        R.validar(m,changed)
    changed=dict(s, processo="compressor_alternativo",
                 ciclo=[
                     {"tipo":"admissao_ar","quadro_inicio":0},
                     {"tipo":"compressao_ar","quadro_inicio":16},
                     {"tipo":"descarga_ar","quadro_inicio":32},
                 ])
    changed_motion=dict(m,processo_declarado="compressor_alternativo")
    with pytest.raises(ValueError, match="COMPRESSOR-UM-GIRO"):
        R.validar(changed_motion,changed)


def test_fonte_ou_sem_revisao_reprova():
    m,s,_=load()
    with pytest.raises(ValueError, match="REFERENCIA-DIVERGENTE"):
        R.validar(dict(m,origem_sha256="0"*64),s)
    with pytest.raises(ValueError, match="CENA-NAO-REVISADA"):
        R.validar(m,dict(s,revisao_humana="PENDENTE"))
    with pytest.raises(ValueError, match="CENA-NAO-REVISADA"):
        R.validar(m,dict(s,publicar=True))


def test_evento_faltando_ou_troca_de_ordem_bloqueiam():
    m,s,_=load()
    with pytest.raises(ValueError, match="CICLO-DIFERENTE-DO-PROCESSO"):
        R.validar(m,dict(s,ciclo=s["ciclo"][:-1]))
    swapped=s["ciclo"].copy()
    swapped[0],swapped[1]=swapped[1],swapped[0]
    with pytest.raises(ValueError, match="CICLO-DIFERENTE-DO-PROCESSO"):
        R.validar(m,dict(s,ciclo=swapped))


def test_tracker_config_e_modelo_geometrico_independentes_do_assunto():
    m, s, c=load()
    fit=m["ajuste_geometrico"]
    result=TRACK.modelo(
        (fit["raio_px"],fit["biela_px"],fit["eixo_y_px"],fit["fase_rad"]),
        list(range(48)),48,2)
    y=m["posicoes_y_px"]
    mae=sum(abs(a-b) for a,b in zip(result,y))/len(y)
    assert mae < .24
    assert c["template_bbox"] == [116,154,138,175]
    assert 0 <= c["keyframe"] < m["quadros"]


def test_tracker_bloqueia_origem_errada_antes_de_analisar(tmp_path):
    m,s,c=load()
    fake=tmp_path/"wrong.gif"
    fake.write_bytes(b"GIF89a not real")
    with pytest.raises(ValueError, match="ORIGEM-NAO-CONFERE"):
        TRACK.extrair(fake,c)


def test_scene_com_movimento_simulado_nao_gera_referencia_real():
    m,s,_=load()
    invalid=dict(m,ajuste_geometrico=dict(m["ajuste_geometrico"],
        erro_medio_px=9.))
    with pytest.raises(ValueError,match="MEDICAO-INADEQUADA"):
        R.validar(invalid,s)
