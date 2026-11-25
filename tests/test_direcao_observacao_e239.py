"""Synthetic technical hints, never semantic approval."""
import numpy as np
from PIL import Image, ImageDraw
from src.v4.formatos import direcao_eventos as D

def noisy(w=240,h=136):
    return Image.fromarray(np.random.default_rng(7).integers(35,220,(h,w,3),dtype=np.uint8))

def test_card_penalty_and_no_automatic_crop():
    im=Image.new('RGB',(240,136),(0,0,0))
    ImageDraw.Draw(im).rectangle((92,62,148,74),fill='white')
    a=D.diagnosticar_janela([im,im,noisy()])
    b=D.diagnosticar_janela([noisy(),noisy(),noisy()])
    assert a['quadros_grafismo_suspeito']==2
    assert b['quadros_grafismo_suspeito']==0
    assert not a['recorte_automatico_autorizado']
    assert D.ordenar_janelas_tecnicas([{'inicio_s':2,'diagnostico':a},{'inicio_s':7,'diagnostico':b}])[0]['inicio_s']==7

def test_embedded_bars():
    im=Image.new('RGB',(240,136))
    im.paste(noisy(76,136),(82,0))
    d=D.diagnosticar_janela([im,im,im])
    assert d['barras_candidatas']
    assert np.allclose(d['bbox_conteudo'],[82/240,0,158/240,1])
    assert not d['recorte_automatico_autorizado']
    assert d['quadros_grafismo_suspeito']==0

def test_asymmetric_dark_edge_not_bar():
    im=noisy()
    ImageDraw.Draw(im).rectangle((0,0,50,135),fill='black')
    assert not D.diagnosticar_janela([im,im,im])['barras_candidatas']

def test_uniform_dark_scene_is_not_card():
    im=Image.new('RGB',(240,136),(4,4,4))
    d=D.diagnosticar_janela([im,im,im])
    assert d['quadros_grafismo_suspeito']==0
    assert not d['barras_candidatas']
