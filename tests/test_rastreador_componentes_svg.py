"""F5: o envelope da câmera não é a caixa real do objeto num quadro."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from src.v4.formatos import rastreador_componentes_svg as T
from src.v4.formatos import camera_causal_svg as C
from src.v4.formatos import render_compressor_conjunto_2d as P
from src.v4.formatos import render_reconstrucao_causal_2d as O
from src.v4.formatos import render_eclusa_hidraulica_2d as L

D=Path(__file__).resolve().parents[1]/'docs/v4/formatos/reference_first'

def _samples():
    m=json.loads(P.MANIFESTO_PADRAO.read_text('utf8'))
    move=json.loads((D/'otto_48f_measured_motion.json').read_text('utf8'))
    scene=json.loads((D/'otto_48f_causal_reviewed_scene.json').read_text('utf8'))
    return {
      ('compressor_oficina_pv','piston_cutaway'):
          [P.frame_svg(t,m,camera_causal=True) for t in (.13,.63)],
      ('otto_4t_reference','piston'):
          [O.svg_frame(move,scene,t,camera_causal=True) for t in (.12,.54)],
      ('lock_cycle_standalone','ship'):
          [L.frame_svg(t) for t in (.12,11.6)],
    }


def test_peca_visivel_muda_posicao_sem_ser_envelope_total():
    for (family,role),svgs in _samples().items():
        a,b=[T.bbox_instante(family,role,s) for s in svgs]
        assert a['pixel_bbox']!=b['pixel_bbox'],(family,role)
        assert a['source']=='SVG_PRIMITIVA_JA_RENDERIZADA'
        assert a['visual_identity_approved'] is False
        assert a['detected_from_external_image'] is False
        for info in (a,b):
            x1,y1,x2,y2=info['pixel_bbox']
            assert 0<x1<x2<540 and 0<y1<y2<960
        env=C.CAMERAS['familias'][family]['roles'][role]
        bbox=a['pixel_bbox']
        observed=(bbox[2]-bbox[0])*(bbox[3]-bbox[1])
        swept=(env[2]-env[0])*(env[3]-env[1])
        assert observed < swept*.78,(family,role,observed,swept)


def test_embarcacao_inteira_no_inicio_e_final_da_eclusa():
    for t in (0,L.DURATION):
        bbox=T.bbox_instante('lock_cycle_standalone','ship',L.frame_svg(t))['pixel_bbox']
        assert 0<bbox[0]<bbox[2]<540
        assert 270<bbox[1]<bbox[3]<900
    a=T.bbox_instante('lock_cycle_standalone','ship',L.frame_svg(0))['pixel_bbox']
    b=T.bbox_instante('lock_cycle_standalone','ship',L.frame_svg(L.DURATION))['pixel_bbox']
    assert b[0]>a[0]+300 and b[1]<a[1]-150


def test_sem_transformacao_ou_ator_real_nao_passa():
    svg=_samples()[('otto_4t_reference','piston')][0]
    with pytest.raises(ValueError,match='F-BBOX-SEM-RASTREADOR'):
        T.bbox_instante('otto_4t_reference','imaginary',svg)
    with pytest.raises(ValueError,match='F-BBOX-SVG-INVALIDO'):
        T.bbox_instante('otto_4t_reference','piston','not svg')
    bad=svg.replace('id="role-piston"','id="role-piston-inexistente"')
    with pytest.raises(ValueError,match='F-BBOX-ATOR-SVG'):
        T.bbox_instante('otto_4t_reference','piston',bad)
    bad=svg.replace('id="mechanical-stage"','id="stage-fake"')
    with pytest.raises(ValueError,match='F-BBOX-ATOR-SVG'):
        T.bbox_instante('otto_4t_reference','piston',bad)


def test_head_pistao_nao_finge_abranger_biela():
    x=_samples()[('compressor_oficina_pv','piston_cutaway')][0]
    q=T.bbox_instante('compressor_oficina_pv','piston_cutaway',x)
    assert q['scope']=='CABECOTE_VISUAL_APENAS_NAO_BIELA'
    assert q['pixel_bbox'][2]-q['pixel_bbox'][0]<120
