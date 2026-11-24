import pytest
from src.v4.formatos.palco_vertical import CaixaVisivel, ajustar_envelope, extrair_grupo_svg
from src.v4.formatos.palco_editorial_render import PROFILE

def test_fit_maximizes_uniformly_and_centers():
    box=CaixaVisivel(40,100,440,600)
    v=CaixaVisivel(*PROFILE['stage'])
    f=ajustar_envelope(box,v)
    assert f.escala==min(516/400,600/500,1.35)
    assert f.x>=v.esquerda and f.x+f.largura<=v.direita
    assert f.y>=v.topo and f.y+f.altura<=v.base
    assert abs(f.largura/f.altura-.8)<.002

def test_art_is_not_restricted_to_text_box():
    f=ajustar_envelope(CaixaVisivel(0,0,500,300),CaixaVisivel(*PROFILE['stage']))
    assert f.largura>500 and f.largura>PROFILE['text'][2]-PROFILE['text'][0]

def test_extract_preserves_transform_and_defs_but_not_lab_header():
    s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 960"><defs><linearGradient id="a"/></defs><text>LAB HEADER</text><g id="stage" transform="translate(3 4)"><rect width="500" height="300" fill="url(#a)"/></g></svg>'
    x=extrair_grupo_svg(s,'stage')
    assert 'LAB HEADER' not in x and 'translate(3 4)' in x and 'linearGradient' in x
    with pytest.raises(ValueError,match='E215-GRUPO'):
        extrair_grupo_svg(s,'unknown')

def test_invalid_envelope_refused():
    with pytest.raises(ValueError,match='E215-ENVELOPE'):
        ajustar_envelope(CaixaVisivel(0,0,0,50),CaixaVisivel(*PROFILE['stage']))
