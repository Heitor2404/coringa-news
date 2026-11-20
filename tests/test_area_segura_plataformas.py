"""Contrato 9:16 para Reels, TikTok, Shorts no motor documental.

As margens são conservadoras; UI orgânica não é fixa. O CI mede layout
calculável, e contato visual para revisão humana do conteúdo e telemetria.
"""
import copy
import json
from pathlib import Path

import pytest
from PIL import Image

from src.v4.formatos import qa_area_segura as SAFE
from src.v4.formatos import filme_editorial as FILME
from src.v4.formatos import diretor_hibrido as H
from src.v4.formatos import video_acao_real as ACTION
from src.v4.formatos import ponte_biblioteca as BIB

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/v4/formatos'


def _script():
    return (ROOT/'motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text('utf8')


def _load(name):
    return json.loads((DOC/name).read_text('utf8'))


def _curiosity():
    lib=ACTION.catalogo_com_acoes(BIB.catalogo(),
        _load('VIDEO_ACAO_OBSERVADA_NASA_20261120.json'),bytes_obrigatorios=False)
    return H.planejar(_load('QA_ROTEIRO_V2_ACAO_CURIOSITY_20261120.json'),lib)['plano']


def test_fonte_unica_todos_slots_dentro_das_tres_plataformas():
    result=SAFE.validar_contrato()
    assert result['area_universal']==[150,300,770,1240]
    assert set(result['plataformas'])=={'instagram_reels_multiplataforma','tiktok_multiplataforma','youtube_shorts_multiplataforma'}
    assert set(result['slots'])=={
        'brand','section','visual','cue','headline','subject','source','subtitle'}
    assert 'safe-zones-vertical.json' in _script()
    assert SAFE.carregar()['source_of_truth']=='src/v4/formatos/plataformas.json'
    # O editor de legendas já usa essas mesmas máscaras, não há perfis duplicados.
    from src.v4.formatos import layout
    assert layout.uniao()['base']==480  # arquivo legado
    assert layout.uniao(layout.CFG['ativos_seguros'])['base']==672  # novas produções
    assert 1030<=layout.faixa_inferior(layout.CFG['ativos_seguros'])['legenda'][1]<=1060
    assert layout.faixa_inferior(layout.CFG['ativos_seguros'])['creditos'][1]>=SAFE.carregar()['slots']['subtitle'][3]
    # Legendas do Camada usam a faixa distinta de créditos, sem conflito.

    assert 'safeSlot(' in _script()
    assert 'data-safe-role="source"' in _script()


def test_validador_recusa_slot_fora_do_perimetro(monkeypatch):
    c=SAFE.carregar()
    c['slots']['headline']=[112,1062,760,1150]
    monkeypatch.setattr(SAFE,'carregar',lambda:c)
    with pytest.raises(ValueError,match='SAFE-SLOT'):
        SAFE.validar_contrato()


def test_validador_recusa_colisao_titulo_e_credito(monkeypatch):
    c=SAFE.carregar()
    c['slots']['headline']=[160,1062,760,1172]
    monkeypatch.setattr(SAFE,'carregar',lambda:c)
    with pytest.raises(ValueError,match='SAFE-SLOTS-SOBREPOSTOS'):
        SAFE.validar_contrato()


def test_cenas_de_acoes_reais_usam_area_segura_e_preservam_original():
    p=_curiosity()
    assert p['safe_area_profile']==SAFE.PERFIL
    report=SAFE.auditar_plano(p)
    assert not report['bloqueios'],report
    assert report['pixels_inspecionados'] is False
    assert report['publicar_aprovado'] is False
    assert FILME.avaliar(p)['pronto']
    assert p['shots'][0]['video_framing']['modo']=='fonte_integral'


def test_producao_nao_passa_sem_esse_contrato():
    p=_curiosity()
    p['tipo']='FILME_FINAL'
    del p['safe_area_profile']
    codes={x['codigo'] for x in FILME.avaliar(p)['bloqueios']}
    assert 'F-SAFE-SEM-PERFIL' in codes


def test_titulos_cues_e_fontes_longas_nao_sao_silenciosamente_truncados():
    p=_curiosity()
    for key,text_value in [
        ('headline','UMA EXPLICAÇÃO MUITO COMPRIDA SEM PAUSAS '+('PALAVRAS '*12)),
        ('source','AUTOR '+('ORIGINAL '*18)),
        ('lead','UM LEAD LITERAL COM TEXTO DEMAIS '+('GRANDE '*10)),
    ]:
        c=copy.deepcopy(p)
        c['shots'][0][key]=text_value
        assert 'SAFE-TEXTO-COMPRIDO' in {
            x['codigo'] for x in SAFE.auditar_plano(c)['bloqueios']}
    c=copy.deepcopy(p)
    c['shots'][0]['cues'][0]['label']='INSTRUÇÃO MUITO LONGA '+('NÃO CABE '*8)
    assert 'SAFE-CUE-COMPRIDA' in {
        x['codigo'] for x in SAFE.auditar_plano(c)['bloqueios']}


def test_raster_legado_e_mapa_nao_podem_ser_declarados_seguros_sem_revisao():
    p=_curiosity()
    p['shots'][0]['type']='atlas_map'
    r=SAFE.auditar_plano(p)
    assert 'SAFE-MAPA-SEM-CERTIFICACAO' in {x['codigo'] for x in r['bloqueios']}
    p=_curiosity()
    p['shots'][0].update(type='photo',graphic_original=True)
    r=SAFE.auditar_plano(p)
    assert 'SAFE-GRAFICO-RASTER' in {x['codigo'] for x in r['bloqueios']}


def test_mecanismos_entram_em_palco_protegido_sem_afirmar_aprovacao_dos_pixels():
    from src.v4.formatos import diretor_roteiro
    p=_load('QA_ROTEIRO_V2_EUV_20261120.json')
    expanded=diretor_roteiro.expandir_preview(p)
    report=SAFE.auditar_plano(expanded)
    assert not report['bloqueios'],report
    assert 'SAFE-MECANISMO-PIXELS-PENDENTES' in {
        x['codigo'] for x in report['avisos']}
    assert FILME.avaliar(p)['pronto']


def test_prova_de_overlay_com_imagem_real_9x16(tmp_path):
    frame=tmp_path/'frame.png'
    Image.new('RGB',(540,960),(17,35,50)).save(frame)
    target=tmp_path/'4plataformas.jpg'
    SAFE.overlay(frame,target)
    assert target.exists()
    with Image.open(target) as im:
        assert im.size==(4*540,960)


def test_qa_overlay_nao_aparece_sem_permissao_explicitamente_informada():
    s=_script()
    assert 'safe_zone_debug=false' in s
    assert 'safe_zone_debug&&' in s
    assert 'quadro_integral' in s and "shot.type==='mechanism'" in s
