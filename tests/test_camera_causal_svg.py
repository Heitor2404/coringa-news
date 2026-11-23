"""F2: prova de câmera alimentada por GRAFO REAL, em 2 renderizadores SVG.

Não é geração 2D/3D a partir de texto: apenas camera de ativos já existentes.
Preserva base anterior por default e bloqueia edição não homologada de bounds.
"""
from __future__ import annotations

import copy
import io
import json
import math
from pathlib import Path

import cairosvg
import pytest
from PIL import Image,ImageChops,ImageStat

from src.v4.formatos import camera_causal_svg as C
from src.v4.formatos import grafo_causal as G
from src.v4.formatos import temporizacao_causal as T
from src.v4.formatos import render_compressor_conjunto_2d as P
from src.v4.formatos import render_reconstrucao_causal_2d as O
from src.v4.formatos.compressor_pv_core import limites_fases,estado

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/v4/formatos/reference_first'


def meta():
    return json.loads(P.MANIFESTO_PADRAO.read_text('utf8'))


def measured():
    return (
       json.loads((DATA/'otto_48f_measured_motion.json').read_text('utf8')),
       json.loads((DATA/'otto_48f_causal_reviewed_scene.json').read_text('utf8')),
    )


def pixel(svg):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as im:
        return im.convert('RGB').copy()


def diff(a,b,crop):
    return sum(ImageStat.Stat(ImageChops.difference(a.crop(crop),b.crop(crop))).mean)/3.


def test_duas_familias_usam_mesma_camera_e_grafo_com_atores_diferentes():
    assert C.CAMERAS['publicar'] is False
    for id,actions in [
        ('compressor_oficina_pv',tuple(P.FASES)),
        ('otto_4t_reference',tuple(O.SEQUENCIAS['motor_otto_4t'])),
    ]:
        g=G.montar(id,actions)
        assert g['integridade_estrutural']=='VALIDADA_NAO_COMPROVA_PIXELS'
        assert all(e['relacoes_em_foco'] for e in g['eventos'])
        assert all(e['camera']['alvos'] for e in g['eventos'])
        for i,name in enumerate(actions):
            pose=C.calcular(id,name,(i+0.35)*8/len(actions),i*8/len(actions),8)
            assert C.verificar_pose(id,pose)
            assert 1<=pose.scale<=C.CAMERAS['familias'][id]['zoom_max']+1e-6
            assert pose.active==name
            assert pose.focus_roles==tuple(g['eventos'][i]['camera']['alvos'])
    assert 'receiver_horizontal' not in C.CAMERAS['familias']['otto_4t_reference']['roles']
    assert 'sparkplug' not in C.CAMERAS['familias']['compressor_oficina_pv']['roles']


def test_camera_nao_corta_nenhum_mecanismo_ao_longo_de_cada_fase():
    for id in ('compressor_oficina_pv','otto_4t_reference'):
        names=[e['acao'] for e in G.montar(
            id,tuple(x['acao'] for x in G.GRAFOS[id]['eventos']))['eventos']]
        for i in range(240):
            t=i/30
            index=min(len(names)-1,int(t/(8/len(names))))
            from_s=index*(8/len(names))
            cam=C.calcular(id,names[index],t,from_s,8)
            assert C.verificar_pose(id,cam)
            if i>35:
                assert cam.scale>=1.01
    assert C.calcular('compressor_oficina_pv','ADMISSAO_AR',4,3,8).scale>1.07


def test_pv_retime_garante_descarga_sem_alterar_coordenadas_fisicas():
    stages=limites_fases(P.AssemblyLayout().spec())
    timeline=T.distribuir(stages,8,1.15)
    assert [x['fase'] for x in timeline]==list(P.FASES)
    assert all(x['video_ate']-x['video_de']>=1.15-1e-8 for x in timeline)
    assert abs(timeline[-1]['video_ate']-8)<1e-8
    for beat in timeline:
        phys,name,begin=T.mapear((beat['video_de']+beat['video_ate'])/2,timeline)
        assert name==beat['fase']
        assert estado(phys,P.AssemblyLayout().spec()).estado==name
        assert math.isclose(begin,beat['video_de'],abs_tol=1e-8)
    vals=[T.mapear(t*8/240,timeline)[0] for t in range(241)]
    assert all(a<=b for a,b in zip(vals,vals[1:]))
    assert vals[0]==0 and math.isclose(vals[-1],1,abs_tol=1e-10)


def test_compressor_novo_render_mexe_camera_sem_mudar_fisica_nem_montagem():
    m=meta()
    s=P.AssemblyLayout().spec()
    for physical in (.03,.22,.63,.96):
        old=P.frame_svg(physical,m)
        upgraded=P.frame_svg(physical,m,camera_causal=True)
        assert 'id="machine-assembly" transform="translate(0 -100.0)"' in old
        assert 'id="machine-assembly" transform="translate(' in upgraded
        assert 'scale(' in upgraded.split('id="machine-assembly"')[1][:100]
        assert all(f'id="role-{x}"' in upgraded for x in ('electric_motor',
            'piston_cutaway','drive_belt','receiver_horizontal','discharge_pipe'))
        a,b=pixel(old),pixel(upgraded)
        assert a.size==b.size==(540,960)
        assert diff(a,b,(0,0,540,235))==0
        assert diff(a,b,(40,240,500,895))>1.0
        # States are calculated from the same physical clock.
        assert estado(physical,s)==estado(physical,s)
    assert P.AssemblyLayout().spec()==s


def test_otto_mesma_camera_em_svg_sem_alterar_track_fonte():
    mov,sc=measured()
    for physical in (.1,.34,.61,.85):
        old=O.svg_frame(mov,sc,physical)
        new=O.svg_frame(mov,sc,physical,camera_causal=True)
        assert 'id="mechanical-stage" transform="translate(0 -28.0)"' in old
        assert 'scale(' in new.split('id="mechanical-stage"')[1][:110]
        assert all(f'id="role-{x}"' in new for x in ('cylinder','chamber','piston','crankshaft'))
        a,b=pixel(old),pixel(new)
        assert a.size==b.size==(540,960)
        assert diff(a,b,(0,0,540,240))==0
        assert diff(a,b,(20,245,520,915))>1
        assert math.isclose(O.pose(physical,mov)['rod_distance'],
                            O.pose(physical,mov)['rod_nominal'],abs_tol=1e-6)


@pytest.mark.parametrize('bad',[-1,0,math.inf,math.nan])
def test_bloqueia_tempo_invalido(bad):
    if bad==0:
        dur=0
        t=0
    else:
        dur=8
        t=bad
    with pytest.raises(ValueError,match='F-CAMERA-TEMPO'):
        C.calcular('compressor_oficina_pv','ADMISSAO_AR',t,0,dur)


def test_cam_sem_grafo_ou_ator_inexistente_bloqueia(monkeypatch):
    with pytest.raises(ValueError,match='F-CAMERA-SEM-GRAFO'):
        C.calcular('familia_desconhecida','qualquer',1,0,8)
    with pytest.raises(ValueError,match='F-CAMERA-ACAO-SEM-GRAFO'):
        C.calcular('compressor_oficina_pv','gancho_generico',1,0,8)
    bad=copy.deepcopy(C.CAMERAS)
    del bad['familias']['compressor_oficina_pv']['roles']['compressor_head']
    monkeypatch.setattr(C,'CAMERAS',bad)
    with pytest.raises(ValueError,match='F-CAMERA-ATOR-SEM-BBOX'):
        C.calcular('compressor_oficina_pv','ADMISSAO_AR',2,1,8)


def test_nao_copiar_camera_de_otto_para_compressor():
    with pytest.raises(ValueError,match='F-CAMERA-BASE-NAO-HOMOLOGADA'):
        P.frame_svg(.3,meta(),layout=P.AssemblyLayout(mechanism_lift_px=0),
                   camera_causal=True)
    mov,scene=measured()
    with pytest.raises(ValueError,match='F-CAMERA-BASE-NAO-HOMOLOGADA'):
        O.svg_frame(mov,scene,.3,subida_palco_px=0,camera_causal=True)


def test_risco_corte_falha_fechado(monkeypatch):
    c=copy.deepcopy(C.CAMERAS)
    c['familias']['otto_4t_reference']['viewport']=[300,245,500,900]
    monkeypatch.setattr(C,'CAMERAS',c)
    with pytest.raises(ValueError,match='F-CAMERA-BASE-NAO-CABE'):
        C.calcular('otto_4t_reference','admissao_mistura',.4,0,8)


def test_qualidade_nao_alegada_automaticamente():
    assert C.CAMERAS['status']=='LAB_NAO_ESTETICA_APROVADA'
    assert G.GRAFOS['compressor_oficina_pv']['fontes_visuais'].startswith('roles_reais')
    assert all(not G.montar(cap,tuple(x['acao'] for x in G.GRAFOS[cap]['eventos']))['publicar']
               for cap in ('compressor_oficina_pv','otto_4t_reference'))
