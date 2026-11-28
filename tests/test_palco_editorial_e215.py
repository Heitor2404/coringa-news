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


def test_e216_tipografia_sem_invadiar_arte():
    from PIL import Image,ImageChops
    from src.v4.formatos.palco_editorial_render import cabecalho
    base=Image.new('RGB',(540,960),PROFILE['background'])
    for title,subtitle,source in [
        ('COMPRESSÃO DO AR','Como o pistão comprime o ar.','P–V'),
        ('EQUILÍBRIO DA ÁGUA','Dois níveis, uma ligação.','OpenStax')]:
        for caption in [None,{'words':['A','pressão','aumenta.'],'highlight':2}]:
            img=cabecalho(title,subtitle,source,caption)
            b=ImageChops.difference(img,base).getbbox()
            assert b[0]>=80 and b[2]<=381 and b[1]>=150 and b[3]<=236
    assert PROFILE['stage']==[12,244,528,844]

def test_e216_rejeita_legenda_sem_origem_e_sobreposicao():
    from src.v4.formatos.palco_editorial_render import validar_legendas
    g={'start':1.,'end':2.,'words':['A','água','flui.'],'highlight':2}
    with pytest.raises(ValueError,match='ORIGEM-LEGENDA'):
        validar_legendas([g],3.,None)
    with pytest.raises(ValueError,match='LEGENDA-INVALIDA'):
        validar_legendas([g,{**g,'start':1.5}],3.,'LAB_TEMPOS_DECLARADOS')
    validar_legendas([g],3.,'LAB_TEMPOS_DECLARADOS')
