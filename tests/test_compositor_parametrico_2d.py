"""F6: prova de DOIS vídeos montados por dados, sem renderer por assunto.

Inclui eclusa preexistente: mesmo conduto, válvula e barreira paramétricos.
"""
from __future__ import annotations
import copy
import io
import json
import math
import re
from pathlib import Path
import cairosvg
import pytest
from PIL import Image,ImageChops,ImageStat
from src.v4.formatos import compositor_mecanismo_parametrico_2d as C
from src.v4.formatos import fisica_reservatorios_parametricos as F
from src.v4.formatos import primitivas_fisicas_parametricas as P
from src.v4.formatos import camera_causal_svg as CAM
from src.v4.formatos import grafo_causal as G
from src.v4.formatos import render_eclusa_hidraulica_2d as E

DIR=Path(__file__).resolve().parents[1]/"src/v4/formatos/cenas_parametricas"


def configs():
    return (C.carregar(DIR/"vasos_comunicantes_iguais.json"),
            C.carregar(DIR/"vasos_comunicantes_assimetricos.json"))


def rgb(svg):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as im:
        return im.convert("RGB").copy()


def diff(a,b,roi):
    d=ImageChops.difference(a.crop(roi),b.crop(roi))
    return sum(ImageStat.Stat(d).mean)/3


def test_primitivas_reais_sao_utilizadas_sem_modelos_novos():
    assert P.verificar_reuso()==["conduit","fluid_body","gate","piston","reservoir","rotor","transmission","valve"]
    assert "stroke-width" in P.conduto("M 211 714 H 331")
    assert 'opacity="0.000"' in P.conduto("M 211 714 H 331")
    assert 'opacity="0.000"' in P.barreira(396,414,777,1.)
    assert "rotate(90.00" in P.valvula(270,714,1.)
    assert "<rect" in P.reservatorio(34,337,190,427)
    assert "<rect" in P.agua_no_tanque(47,425,164,751)
    old=E.frame_svg(5.2)
    assert 'id="role-conduit"' in old and 'id="role-valve"' in old
    assert 'M 461 566 V 809 H 314 V 754' in old
    assert 'data-primitive="conduit"' in old


def test_duas_cenas_de_uma_mesma_arquitetura_com_geometrias_distintas():
    a,b=configs()
    assert a["id"]!=b["id"]
    assert a["family"]==b["family"]=="vasos_comunicantes"
    assert a["duration_s"]==b["duration_s"]==12
    assert a["physics"]==b["physics"]
    assert a["components"]!=b["components"]
    assert [p["primitive"] for p in a["components"]]==[
       p["primitive"] for p in b["components"]]
    assert C.validar(a)["causal"]["integridade_estrutural"]=="VALIDADA_NAO_COMPROVA_PIXELS"
    assert C.validar(b)["causal"]["estado_final"]["left_water.level"]=="equal"
    assert len(G.GRAFOS["vasos_comunicantes"]["atores"])==6


@pytest.mark.parametrize("index",[0,1])
def test_conservacao_agua_e_niveis_sem_fluxo_antes_de_abrir(index):
    c=configs()[index]
    left=next(p for p in c["components"] if p["id"]=="left_tank")
    right=next(p for p in c["components"] if p["id"]=="right_tank")
    v0=C.simular(c,0)
    vl=left["width"]-26
    vr=right["width"]-26
    for i in range(241):
        t=12*i/240
        s=C.simular(c,t)
        assert math.isclose(s.volume_total,v0.volume_total,abs_tol=1e-6)
        assert s.nivel_esquerdo_y>=v0.nivel_esquerdo_y-1e-8
        assert s.nivel_direito_y<=v0.nivel_direito_y+1e-8
        assert 0<=s.valvula_aberta<=1
        assert 0<=s.fluxo<=1
        if t<4.2:
            assert s.nivel_esquerdo_y==v0.nivel_esquerdo_y
            assert s.nivel_direito_y==v0.nivel_direito_y
            assert s.fluxo==0
    end=C.simular(c,12)
    assert math.isclose(end.nivel_esquerdo_y,end.nivel_direito_y,abs_tol=1e-8)
    expected=(vl*v0.nivel_esquerdo_y+vr*v0.nivel_direito_y)/(vl+vr)
    assert math.isclose(end.nivel_esquerdo_y,expected,abs_tol=1e-8)


def test_areas_diferentes_mudam_altura_final_corretamente():
    a,b=configs()
    ea=C.simular(a,12)
    eb=C.simular(b,12)
    assert not math.isclose(ea.nivel_final_y,eb.nivel_final_y,abs_tol=.1)
    assert eb.nivel_final_y<ea.nivel_final_y
    assert ea.fluxo==eb.fluxo==0


def test_camera_uma_unica_pose_e_partes_mudam():
    for scene in configs():
        poses=set()
        for i in range(240):
            t=i/20
            svg=C.frame_svg(scene,t)
            assert svg.count('data-visual-identity="PENDENTE"')==6
            assert 'role-left_water' in svg and 'role-right_water' in svg
            assert "source_pixel" not in svg
            stage=re.search(r'id="machine-stage" transform="([^"]+)"',svg)
            assert stage
            poses.add(stage.group(1))
        assert len(poses)==1
        for action in [x["acao"] for x in G.GRAFOS["vasos_comunicantes"]["eventos"]]:
            cam=CAM.calcular("vasos_comunicantes",action,9.0,0,12.)
            assert CAM.verificar_pose("vasos_comunicantes",cam)


@pytest.mark.parametrize("index",[0,1])
def test_antes_depois_pelo_deslocamento_da_agua_e_nao_por_cards(index):
    c=configs()[index]
    a=rgb(C.frame_svg(c,4.22))
    b=rgb(C.frame_svg(c,9.79))
    assert a.size==b.size==(540,960)
    assert diff(a,b,(25,315,515,788))>9
    assert diff(a,b,(0,0,540,75))==0
    assert diff(a,b,(0,901,540,960))==0
    assert len(set(a.getpixel((x,600)) for x in range(40,503,10)))>4


def test_falha_fechada_sem_tubo_valvula_papeis_ou_fonte():
    a,_=configs()
    edits=[
      (lambda x:x.update({"publish":True}),"F-COMP-CENA-NAO-HOMOLOGADA"),
      (lambda x:x["rights"].update({"external_pixels_copied":True}),"F-COMP-FONTE"),
      (lambda x:x["components"].pop(),"F-COMP-PECAS"),
      (lambda x:next(p for p in x["components"] if p["id"]=="link_pipe").update(
        {"path":"M 250 710 H 330"}),"F-COMP-TUBO"),
      (lambda x:next(p for p in x["components"] if p["id"]=="control_valve").update(
        {"x":15}),"F-COMP-PARAMETRO"),
      (lambda x:x["physics"].update({"flow_to_s":7.0}),"F-COMP-PARAMETRO"),
      (lambda x:x["timeline"][2].update({"acao":"inventado"}),"F-COMP-EVENTOS"),
    ]
    for change,code in edits:
        c=copy.deepcopy(a)
        change(c)
        with pytest.raises(ValueError,match=code):
            C.validar(c)


def test_numeros_maliciosos_ou_polaridade_trocada_nao_passam():
    c=configs()[0]
    for bad in (math.nan,math.inf,-1):
        with pytest.raises(ValueError):
            F.simular(bad,duracao=12,area_esquerda=164,
                      area_direita=164,fundo_y=751,topo_y=350,
                      esquerda_y=425,direita_y=637,
                      abertura_de=3,abertura_ate=4.1,
                      vazao_de=4.2,vazao_ate=9.8)
    with pytest.raises(ValueError,match="F-PRIMITIVA-TRACADO"):
        P.conduto('M 10 20 <script>')
    with pytest.raises(ValueError,match="F-PRIMITIVA-COR"):
        P.reservatorio(34,337,190,427,borda="url(https://attacker)")
