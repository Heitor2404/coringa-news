"""Contra-exemplos do fiscal de PROGRESSÃO: sem assuntos hardcoded."""
from src.v4.formatos import fiscal_progressao as F

def _photo(id, start,end,asset, cues):
    return {'id':id,'type':'photo','start':start,'end':end,'asset':asset,
            'cues':[{'at':t,'label':'revela novo ponto'} for t in cues]}

def _src(page,sha):
    return {'page':page,'expected_sha256':sha*64}

def _codes(items):
    return {e['codigo'] for e in items}

def test_uma_imagem_por_2s_com_info_nao_e_bloqueada():
    x=[_photo('a',0,2.5,'um',[.45])]
    assert F.verificar(x,{'um':_src('https://archive.org/first','a')})==[]

def test_foto_presa_3s_apos_unica_informacao_bloqueia():
    x=[_photo('a',0,3.7,'um',[.45])]
    assert 'F-SEM-PROGRESSAO-INFORMACIONAL' in _codes(
       F.verificar(x,{'um':_src('https://archive.org/first','a')}))

def test_novidade_tardia_em_tempo_evitaria_falso_positivo_de_metrica_temporal():
    x=[_photo('a',0,3.7,'um',[.45,2.4])]
    assert 'F-SEM-PROGRESSAO-INFORMACIONAL' not in _codes(
       F.verificar(x,{'um':_src('https://archive.org/first','a')}))

def test_mesma_fonte_nao_vira_duas_provas_ao_trocar_asset_id_e_crop():
    x=[_photo('a',0,2.5,'crop_a',[.45]),
       _photo('b',2.5,5.,'crop_b',[.45])]
    media={'crop_a':_src('https://archive.org/same','a'),
           'crop_b':_src('https://archive.org/same','b')}
    assert 'F-FONTE-VISUAL-REPETIDA' in _codes(F.verificar(x,media))

def test_mesmo_hash_com_paginas_diferentes_tambem_e_repeticao():
    x=[_photo('a',0,2.5,'um',[.45]),
       _photo('b',2.5,5.,'dois',[.45])]
    media={'um':_src('https://archive.org/first','a'),
           'dois':_src('https://archive.org/second','a')}
    assert 'F-FONTE-VISUAL-REPETIDA' in _codes(F.verificar(x,media))

def test_documental_de_video_real_nao_e_foto_parada():
    s=[{'id':'video','type':'video','start':0,'end':3.7,'asset':'a',
        'cues':[{'at':.2,'label':'começa a ação'}]}]
    assert F.verificar(s,{'a':_src('https://archive.org/real','a')})==[]

def test_comparacao_nao_e_automaticamente_tratada_como_duas_fotos_repetidas():
    s=[{'id':'comp','type':'comparison','start':0,'end':3.5,
        'asset':'a','assetB':'b','cues':[{'at':.4,'label':'antes e depois'}]}]
    media={'a':_src('https://archive.org/source','a'),
           'b':_src('https://archive.org/source','a')}
    assert F.verificar(s,media)==[]
