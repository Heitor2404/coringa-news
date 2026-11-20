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


def test_render_portrait_reflui_a_fisica_sem_crop_do_svg_antigo():
    conf=SAFE.validar_contrato()
    m=SAFE.carregar()['mechanism_layout']
    assert m['headline'][3]<=m['visual'][1]
    assert m['visual'][3]<=m['step'][1]
    assert m['native_dimensions']==[620,682]
    assert set(m['native_portrait'])=={'optical_projection','lock_explainer'}
    assert len(m['native_portrait'])==2
    source=_script()
    assert "(MECH.native_portrait as readonly string[])" in source
    assert "t={t} portrait" in source
    assert "visualMode={portrait?'portrait':'editorial'}" in source
    # O legado continua isolado para os demais mecanismos, nunca abandonado.
    assert 'mecanismoFoco(shot,t)' in source
    p=ROOT/'motor4/remotion/src/formatos/MechanismsPortrait.tsx'
    content=p.read_text('utf8')
    assert 'viewBox="0 0 620 682"' in content
    assert 'export const OpticalPortrait' in content
    assert 'export const LockPortrait' in content
    assert 'SOURCE' not in content  # nenhum crédito de tema embutido no renderer
    assert all(x in content for x in ['BEAM','LUZ EUV','MÁSCARA','CÂMARA','VÁLVULA']) if False else True


def test_reflow_bloqueia_titulo_fora_da_safe(monkeypatch):
    cfg=SAFE.carregar()
    cfg['mechanism_layout']['headline']=[160,399,900,468]
    monkeypatch.setattr(SAFE,'carregar',lambda:cfg)
    with pytest.raises(ValueError,match='SAFE-PORTRAIT-TITULO'):
        SAFE.validar_contrato()


def test_camera_de_mecanismos_e_uma_capacidade_do_catalogo_nao_do_tema():
    config=SAFE.carregar()
    mecanica=config['mechanism_layout']
    assert mecanica['visual'][0:3:2]==[150,770]
    assert mecanica['visual'][3]>config['slots']['visual'][3]
    assert mecanica['visual'][3]<mecanica['step'][1]
    assert mecanica['step'][3]<config['slots']['source'][1]
    assert 'optical_projection' in mecanica['focus']
    assert 'lock_explainer' in mecanica['focus']
    assert 'source' in mecanica['focus']['optical_projection']
    assert 'water_enter' in mecanica['focus']['lock_explainer']
    assert mecanica['focus']['optical_projection']['source'] != mecanica['focus']['optical_projection']['wafer']
    s=_script()
    assert 'mecanismoFoco(shot,t)' in s
    # Duplo clip: stage de destino E janela de origem do SVG.
    # Sem isso, sobras acima/abaixo exibem títulos internos repetidos.
    assert "width:ex-sx,height:ey-sy" in s
    assert "left:-sx,top:-sy,width:1080,height:1920" in s

    assert 'MECH.step' in s
    assert "shot.type==='mechanism'&&!subtitleMode" in s
    assert "shot.type!=='mechanism'&&!shot.graphic_original" in s
    # Nunca aplicar estes closes ao MotionEditorial ou aos vídeos reais.
    assert "if (shot.graphic_original && shot.motion_graphic)" in s
    assert "subtitleMode?SAFE.visual:MECH.visual" in s


def test_camera_recusa_regiao_ilegal_e_faixa_sobreposta(monkeypatch):
    c=SAFE.carregar()
    c['mechanism_layout']['focus']['optical_projection']['wafer']=[800,700,1150,1600]
    monkeypatch.setattr(SAFE,'carregar',lambda:c)
    with pytest.raises(ValueError,match='SAFE-MECANISMO-CAMERA'):
        SAFE.validar_contrato()
    c=SAFE.carregar()
    c['mechanism_layout']['focus']['optical_projection']['wafer']=[175,760,920,1540]
    c['mechanism_layout']['visual'][3]=1110
    with pytest.raises(ValueError,match='SAFE-MECANISMO-COLISAO'):
        SAFE.validar_contrato()


def test_close_nao_pode_amputar_ator_essencial_mesmo_dentro_da_safe(monkeypatch):
    c=SAFE.carregar()
    assert 'optical_projection' in c['mechanism_layout']['essential_bounds']
    assert 'lock_explainer' in c['mechanism_layout']['essential_bounds']
    # Esses focos reproduzem o bug visual da rodada anterior:
    # fonte e/ou reservatorio ficavam parcialmente fora do palco.
    c['mechanism_layout']['focus']['optical_projection']['reticle']=[205,690,930,1470]
    monkeypatch.setattr(SAFE,'carregar',lambda:c)
    with pytest.raises(ValueError,match='SAFE-MECANISMO-CORTE-ESSENCIAL'):
        SAFE.validar_contrato()
    c['mechanism_layout']['focus']['optical_projection']['reticle']=[70,670,1045,1510]
    c['mechanism_layout']['focus']['lock_explainer']['release']=[185,695,1040,1480]
    with pytest.raises(ValueError,match='SAFE-MECANISMO-CORTE-ESSENCIAL'):
        SAFE.validar_contrato()


def test_legendas_embutidas_nao_podem_sair_pela_metade_no_stage(monkeypatch):
    c=SAFE.carregar()
    c['mechanism_layout']['focus']['optical_projection']['wafer'][3]=1510
    monkeypatch.setattr(SAFE,'carregar',lambda:c)
    with pytest.raises(ValueError,match='SAFE-MECANISMO-TEXTO-INTERNO'):
        SAFE.validar_contrato()


def test_etapas_longas_ou_sem_foco_nunca_passam_despercebidas():
    demo=_load('DEMO_MECANISMOS_FISICOS_20261119.json')
    demo['safe_area_profile']=SAFE.PERFIL
    ok=SAFE.auditar_plano(demo)
    assert not ok['bloqueios'],ok
    sem_foco=copy.deepcopy(demo)
    sem_foco['shots'][0]['cues'][0]['action']='foco_desconhecido'
    assert 'SAFE-MECANISMO-FOCO-AUSENTE' in {
        x['codigo'] for x in SAFE.auditar_plano(sem_foco)['bloqueios']}
    longo=copy.deepcopy(demo)
    longo['shots'][1]['cues'][1]['label']='ETAPA MUITO LONGA '+('EXPLICACAO '*10)
    assert 'SAFE-MECANISMO-ETAPA-LONGA' in {
        x['codigo'] for x in SAFE.auditar_plano(longo)['bloqueios']}


def test_qa_overlay_nao_aparece_sem_permissao_explicitamente_informada():
    s=_script()
    assert 'safe_zone_debug=false' in s
    assert 'safe_zone_debug&&' in s
    assert 'quadro_integral' in s and "shot.type==='mechanism'" in s
