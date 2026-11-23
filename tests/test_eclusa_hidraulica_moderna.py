"""Eclusa moderna: terceiro processo real independente de biela/pistão.

O modelo assume corte lateral esquemático; não faz promessa de CAD ou IA
que detecta peças de vídeos externos. Publicação automática bloqueada.
"""
from __future__ import annotations

import io,json,math,re
from pathlib import Path
import cairosvg,pytest
from PIL import Image,ImageChops,ImageStat

from src.v4.formatos import render_eclusa_hidraulica_2d as L
from src.v4.formatos import camera_causal_svg as C
from src.v4.formatos import realce_causal_svg as R
from src.v4.formatos import grafo_causal as G


def _img(svg):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as img:
        return img.convert("RGB").copy()


def _difference(a,b,box):
    d=ImageChops.difference(a.crop(box),b.crop(box))
    return sum(ImageStat.Stat(d).mean)/3.


def test_sao_sete_acoes_reais_do_grafo_existente():
    actions=tuple(x[0] for x in L.PHASES)
    graph=G.montar('lock_cycle_standalone',actions)
    assert actions==('enter','seal','valves','rise','equalize','open','exit')
    assert len(graph['atores'])==9
    assert len(graph['relacoes'])==9
    assert graph['estado_final']['ship.location']=='upper_channel'
    assert graph['estado_final']['chamber.equalized']=='true'
    assert 'piston' not in {r['id'] for r in graph['atores']}


def test_primeiro_ultimo_quadro_navio_inteiro_com_cotas_correntes():
    start=L.estado(0)
    finish=L.estado(L.DURATION)
    assert start.fase=='enter' and finish.fase=='exit'
    assert start.agua_y==L.LOW and finish.agua_y==L.HIGH
    assert start.navio_y==start.agua_y
    assert finish.navio_y==finish.agua_y
    assert 20<=start.navio_x-62 and finish.navio_x+66<=520
    assert start.navio_x<L.LEFT_GATE<finish.navio_x
    assert finish.navio_x>L.RIGHT_GATE
    assert finish.portao_entrada_fechado==1
    assert finish.portao_saida_aberto==1


def test_enchimento_so_depois_de_fechar_portao_e_abrir_valvula():
    before=L.estado(2.0)
    assert before.portao_entrada_fechado>0
    assert before.valvula_aberta==0 and before.agua_y==L.LOW
    valve=L.estado(3.5)
    assert valve.portao_entrada_fechado>.99
    assert valve.valvula_aberta>.75 and valve.agua_y==L.LOW
    start=L.estado(4.0)
    middle=L.estado(5.85)
    end=L.estado(7.65)
    assert start.agua_y==L.LOW
    assert L.HIGH<middle.agua_y<L.LOW
    assert end.agua_y==L.HIGH
    assert all(x.navio_y==x.agua_y for x in (start,middle,end))
    assert L.estado(8.5).portao_saida_aberto==0
    assert L.estado(10.5).portao_saida_aberto>.99
    assert L.estado(8.5).navio_x==L.CHAMBER_CENTER


def test_camara_flutua_monotonicamente_e_navio_nao_sai_cedo():
    frames=[L.estado(t*L.DURATION/300) for t in range(301)]
    assert all(a.agua_y>=b.agua_y for a,b in zip(frames,frames[1:]))
    assert all(abs(x.navio_y-x.agua_y)<1e-8 for x in frames)
    assert all(x.navio_x<=L.CHAMBER_CENTER+1e-7 for x in frames if x.tempo<10.)
    assert all(x.agua_y==L.HIGH for x in frames if x.tempo>=8.)
    assert all(0<=x.fase_fracao<=1 for x in frames)
    assert len({x.fase for x in frames})==7


def test_mesma_camera_travada_que_piston_e_otto_sem_cortes():
    cfg=C.CAMERAS['familias']['lock_cycle_standalone']
    assert cfg['politica_camera']=='plano_geral_travado'
    assert set(cfg['roles'])=={r['id'] for r in G.GRAFOS['lock_cycle_standalone']['atores']}
    transforms=set()
    for i in range(300):
        t=i*L.DURATION/300
        s=L.estado(t)
        p=C.calcular('lock_cycle_standalone',s.fase,t,s.fase_inicio,L.DURATION)
        assert C.verificar_pose('lock_cycle_standalone',p)
        transforms.add((p.scale,p.tx,p.ty))
    assert len(transforms)==1
    assert C.CAMERAS['familias']['compressor_oficina_pv']['politica_camera']=='plano_geral_travado'
    assert C.CAMERAS['familias']['otto_4t_reference']['politica_camera']=='plano_geral_travado'


def test_sete_fases_rendem_grandes_sem_editorial_vazio():
    for i,(a,lo,hi,*_) in enumerate(L.PHASES):
        t=(lo+hi)/2
        s=L.estado(t)
        svg=L.frame_svg(t)
        assert s.fase==a
        for role in ('ship','chamber','water','conduit','inlet_gate',
                     'outlet_gate','valve','lower_channel','upper_channel'):
            assert f'id="role-{role}"' in svg
        assert 'id="machine-stage"' in svg
        assert 'id="lock-stage"' in svg
        assert 'ECLUSA HIDRÁULICA' in svg
        assert f'{i+1:02d}/07' in svg
        im=_img(svg)
        assert im.size==(540,960)
        # Palco físico expõe água e paredes em mais de 40% da largura.
        colors={im.getpixel((x,720)) for x in range(50,491,8)}
        assert len(colors)>=6
        assert im.getpixel((270,100))!=(im.getpixel((270,600)))


def test_destacar_vazao_apenas_quando_a_valvula_abriu_e_gravidade_age():
    before=L.frame_svg(2.2)
    first=L.frame_svg(2.80)
    valve=L.frame_svg(3.45)
    rise=L.frame_svg(5.3)
    equal=L.frame_svg(8.3)
    assert 'id="causal-emphasis"' not in before
    assert 'id="causal-emphasis"' not in first
    assert 'data-event="valves"' in valve
    assert 'data-event="rise"' in rise
    assert 'id="causal-emphasis"' not in equal
    assert R.REGISTRO['familias']['lock_cycle_standalone']['rise']['edge']==[
        'conduit','feeds','chamber']
    # Um highlight só na ligação, não fundo escuro/painéis/cards.
    base=_img(L.frame_svg(5.3,realce_causal=False))
    enhanced=_img(rise)
    assert _difference(base,enhanced,(0,0,540,258))==0
    assert _difference(base,enhanced,(0,907,540,960))==0
    assert _difference(base,enhanced,(295,540,475,831))>.02


def test_movimento_real_de_navio_e_agua_nao_efeito_de_titulo():
    a=_img(L.frame_svg(4.05))
    b=_img(L.frame_svg(7.40))
    assert _difference(a,b,(153,420,389,760))>7
    assert _difference(a,b,(0,0,540,90))==0
    assert _difference(a,b,(0,904,540,960))>0  # contador de etapa ou barra?
    

def test_controle_bloqueia_inicio_invalido_sem_fallback_generico():
    for val in (-.01,L.DURATION+.1,math.nan,math.inf):
        with pytest.raises(ValueError,match='F-ECLUSA-TEMPO-INVALIDO'):
            L.estado(val)
    with pytest.raises(ValueError,match='F-ECLUSA-VIDEO-INVALIDO'):
        L.renderizar(Path('/tmp/not-created.mp4'),duracao=5)


def test_eclusa_nao_reutiliza_remotion_legado_nem_publica():
    s=L.frame_svg(4.7)
    assert 'LockCausalCycle' not in s
    assert 'FilmeEditorial' not in s
    assert 'PROVA PRIVADA' in s
    assert R.REGISTRO['publicar'] is False
    assert C.CAMERAS['publicar'] is False
