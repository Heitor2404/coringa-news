"""Regressões do MOTOR: capacidade = ações FÍSICAS, não nome de tema.

Portão não confunde contrato declarativo com inspeção do vídeo.
Nenhum teste aprova estética, conteúdo factual, direitos ou publicação.
"""
import copy
import json
from pathlib import Path

import pytest

from src.v4.formatos import catalogo_mecanismos as CAT
from src.v4.formatos import filme_editorial as FILME

ROOT=Path(__file__).resolve().parents[1]
RECEITA=ROOT/'docs/v4/formatos/DEMO_DIRETOR_CAPACIDADES_20261120.json'


def plano():
    return json.loads(RECEITA.read_text(encoding='utf-8'))


def codes(p):
    return {e['codigo'] for e in FILME.avaliar(p)['bloqueios']}


def test_um_diretor_escolhe_dois_renderers_diferentes():
    p=plano()
    r=FILME.avaliar(p)
    assert r['pronto'], r['bloqueios']
    assert [CAT.decidir(s)[0] for s in p['shots']]==[
        'optical_projection','lock_cycle_standalone']
    assert r['visual_approval']=='NAO_FOI_AVALIADO'
    assert not p['media'] and p['publicar'] is False


def test_preparo_usa_mecanismo_resolvido_no_render_e_nao_auto(tmp_path):
    p=plano()
    # Contrato histórico: não autoriza o estilo descartado em documentários.
    p.update(perfil_visual='LEGADO_REJEITADO_SOMENTE_QA',publicar=False)
    output=FILME.preparar(p,tmp_path/'run',tmp_path/'public')
    assert output['pronto']
    props=json.loads((tmp_path/'run/props.json').read_text(encoding='utf8'))
    assert [s['mechanism'] for s in props['shots']]==[
        'optical_projection','lock_cycle_standalone']
    assert all(s['type']=='mechanism' and not s.get('reference_asset')
               for s in props['shots'])
    # Bug real da imagem antiga: storyboard = auto, renderer resolvido = EUV.
    # Crédito deve seguir a decisão final, jamais herdar eclusa.
    assert props['shots'][0]['source_display']=='ASML · asml.com'
    assert props['shots'][0]['source'].startswith('ASML · https://')
    assert 'hidráulico' not in props['shots'][0]['source'].lower()
    assert props['shots'][1]['source_display'].startswith('Autoridade do Canal do Panamá')
    assert 'pancanal.com' in props['shots'][1]['source']



def test_nome_de_assunto_nao_escolhe_mecanismo():
    p=plano()
    for s in p['shots']:
        s['lead']='PESQUISA CIENTÍFICA MULTITEMA'
        s['headline']='ASSUNTO DIFERENTE'
        s['subject']='Outro objeto hipotético, não identidade real'
        assert CAT.decidir(s)[0] in ('optical_projection','lock_cycle_standalone')


def test_uma_animacao_de_subida_nao_pode_prometer_entrada_e_saida():
    p=plano()
    c=p['shots'][1]
    c['mechanism']='lock_explainer'
    # Mesmo que uma chamada force explicitamente o antigo renderer, o motor bloqueia.
    assert 'F-CAPACIDADE-INCOMPLETA' in codes(p)


def test_catalogo_recusa_transferencia_sem_renderer_fisico():
    p=plano()
    p['shots'][1]['processo_visual']={
        'acoes_necessarias':['enter','scan','sort','exit'],
        'fases_necessarias':['entrada','mecanismo','saida'],
    }
    assert 'F-CAPACIDADE-INDISPONIVEL' in codes(p)


def test_sem_acao_causal_completa_nao_existe_atalho():
    p=plano()
    p['shots'][1]['cues']=p['shots'][1]['cues'][:4]
    assert 'F-CAPACIDADE-INDISPONIVEL' in codes(p)


def test_legacy_ciclo_com_video_real_nao_pode_ser_substituido_silenciosamente():
    p=json.loads((ROOT/'docs/v4/formatos/filme_panama_ciclo_19s.json').read_text('utf8'))
    assert FILME.avaliar(p)['pronto']
    p['shots'][1]['reference_asset']=None
    assert 'F-PONTE-REAL' in codes(p)


def test_auto_sem_demanda_explicita_e_bloqueado():
    p=plano()
    del p['shots'][0]['processo_visual']
    assert 'F-CAPACIDADE-SEM-OBJETIVO' in codes(p)


def test_fases_sao_requisitos_e_nao_legenda():
    p=plano()
    p['shots'][0]['processo_visual']['fases_necessarias'].append('saida')
    assert 'F-CAPACIDADE-INDISPONIVEL' in codes(p)


def test_nao_publica_nem_finge_aprovacao():
    p=plano()
    p['tipo']='FILME_FINAL'
    assert not FILME.avaliar(p)['pronto']


def test_compositor_nao_esconde_acontecimento_com_titulo_duplicado():
    # Regra transversal: mecanismo possui sua própria hierarquia gráfica.
    source=(ROOT/'motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text('utf8')
    assert source.count('data-safe-role="headline"')==1
    assert "safeSlot('visual')" in source
    # O componente MotionEditorial mantém seu recorte legado, mas mecanismos
    # agora usam camera por etapas da biblioteca, sem depender de assunto.
    assert "if (shot.graphic_original && shot.motion_graphic)" in source
    assert "sourceY=450" in source
    assert "mecanismoFoco(shot,t)" in source
    assert "shot.type!=='mechanism'&&!shot.graphic_original" in source
    # Cabeçalhos internos dos SVG não devem reaparecer sobre o título público.
    assert "const SafeBody:" in source
    assert "['lock_cycle','lock_cycle_standalone'].includes" in source
    assert "duration={shot.end-shot.start}" in source
