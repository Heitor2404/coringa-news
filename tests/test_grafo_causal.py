"""Grafo de cena causal, integrado ao diretor EXISTENTE, em três físicas.

Não confundir promessas estruturais com prova por visão ou aprovação humana.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.v4.formatos import grafo_causal as G
from src.v4.formatos import catalogo_mecanismos as C
from src.v4.formatos import diretor_processos as D
from src.v4.formatos import filme_editorial as F

ROOT=Path(__file__).resolve().parents[1]
DEMO=ROOT/'docs/v4/formatos/DEMO_DIRETOR_EVENTOS_20261120.json'


def plan():
    return json.loads(DEMO.read_text('utf8'))


def issues(p):
    return {x['codigo'] for x in F.avaliar(p)['bloqueios']}


def test_planejador_cria_grafos_sem_cenas_manuais_em_optica_e_hidraulica():
    raw=plan()
    result=D.expandir(raw)
    assert len(result['shots'])==2
    assert raw.get('shots') is None
    assert result['diretor_automatico']['planejamento_causal'].startswith('ATORES_')
    for scene,cap_id in zip(result['shots'],('optical_projection','lock_cycle_standalone')):
        assert scene['mechanism']=='auto'
        assert scene['processo_visual']['grafo_causal_requerido'] is True
        g=scene['plano_causal']
        assert g['capacidade']==cap_id
        assert g['integridade_estrutural']=='VALIDADA_NAO_COMPROVA_PIXELS'
        assert g['revisao_visual']=='PENDENTE' and g['publicar'] is False
        assert len(g['eventos'])==len(scene['cues'])
        assert [e['acao'] for e in g['eventos']]==[x['action'] for x in scene['cues']]
        assert all(e['antes']!=e['depois'] and e['relacoes_em_foco'] for e in g['eventos'])
        assert C.decidir(scene)==(cap_id,[])
    assert len(result['shots'][0]['plano_causal']['atores'])==5
    assert len(result['shots'][1]['plano_causal']['atores'])==9
    assert F.avaliar(raw)['pronto']


def test_tres_fisicas_e_ciclos_independentes_sem_herdar_pecas():
    for id in ('lock_cycle_standalone','lock_explainer','optical_projection'):
        c=C.CAPACIDADES[id]
        g=G.montar(id,c.acoes,momentos=c.tempos_referencia)
        assert g['capacidade']==id
        assert len(g['eventos'])==len(c.acoes)
        assert set(x['operador'] for x in g['eventos']).issubset(G.OPERADORES)
        assert all(x['precondicoes'] and x['depois'] for x in g['eventos'])
    graph=G.montar('optical_projection',C.CAPACIDADES['optical_projection'].acoes)
    assert 'ship' not in {x['id'] for x in graph['atores']}
    assert 'resist.exposure' in graph['estado_final']
    lock=G.montar('lock_cycle_standalone',C.CAPACIDADES['lock_cycle_standalone'].acoes)
    assert lock['estado_final']['ship.location']=='upper_channel'
    assert lock['estado_final']['outlet_gate.closed']=='false'


def test_evento_agua_sobe_e_navio_segue_uma_relacao_unica():
    c=C.CAPACIDADES['lock_cycle_standalone']
    g=G.montar(c.id,c.acoes)
    assert {'from':'ship','type':'floats_on','to':'water'} in g['relacoes']
    rise=next(x for x in g['eventos'] if x['acao']=='rise')
    assert {'ship','water','chamber'}<=set(rise['camera']['alvos'])
    assert any(r['type']=='floats_on' for r in rise['relacoes_em_foco'])
    assert rise['depois']=={'water.level':'rising'}
    # "Ship rises" é INVARIANTE DE RELAÇÃO, não um segundo motor temporal.
    assert rise['operador']=='fill'


def test_fluxo_otico_realca_relacoes_e_consequencia():
    c=C.CAPACIDADES['optical_projection']
    g=G.montar(c.id,c.acoes)
    assert [x['operador'] for x in g['eventos']]==['emit','reflect','project','expose']
    assert {'from':'projection_optics','type':'projects_to','to':'resist'} in g['relacoes']
    last=g['eventos'][-1]
    assert last['depois']=={'resist.exposure':'exposed'}
    assert last['camera']['intencao']=='show_consequence'


def test_atores_essenciais_e_relacoes_faltantes_bloqueiam_sem_render():
    p=plan()
    p['eventos_diretor'][0]['direcao_evento']['atores_essenciais']=['ship']
    assert 'F-GRAFO-ATOR-INDISPONIVEL' in issues(p)
    p=plan()
    p['eventos_diretor'][1]['direcao_evento']['relacoes_essenciais']=[
        {'from':'ship','type':'rotates_with','to':'water'}]
    assert 'F-GRAFO-RELACAO-INDISPONIVEL' in issues(p)
    p=plan()
    p['eventos_diretor'][1]['direcao_evento']['atores_essenciais']=['ship','chamber']
    p['eventos_diretor'][1]['direcao_evento']['relacoes_essenciais']=[
        {'from':'ship','type':'floats_on','to':'water'}]
    assert F.avaliar(p)['pronto']


def test_grafo_adulterado_e_grafo_ausente_sao_rejeitados_no_catalogo():
    p=D.expandir(plan())
    s=copy.deepcopy(p['shots'][1])
    s['plano_causal']['estado_final']['ship.location']='lower_channel'
    assert C.decidir(s)[1][0]['codigo']=='F-GRAFO-DIVERGENTE'
    s=copy.deepcopy(p['shots'][1])
    del s['plano_causal']
    assert C.decidir(s)[1][0]['codigo']=='F-GRAFO-AUSENTE'
    s=copy.deepcopy(p['shots'][0])
    s['plano_causal']['eventos'][-1]['camera']['alvos']=['light_source']
    assert C.decidir(s)[1][0]['codigo']=='F-GRAFO-DIVERGENTE'


def test_ficha_impossivel_precondicao_ou_ator_escondido_bloqueados(monkeypatch):
    c=C.CAPACIDADES['lock_cycle_standalone']
    original=copy.deepcopy(G.GRAFOS[c.id])
    wrong=copy.deepcopy(original)
    wrong['eventos'][4]['requer']['water.level']='dry'
    monkeypatch.setitem(G.GRAFOS,c.id,wrong)
    with pytest.raises(G.GrafoInvalido,match='F-GRAFO-PRECONDICAO'):
        G.montar(c.id,c.acoes)
    wrong=copy.deepcopy(original)
    wrong['eventos'][3]['foco']=['chamber']
    monkeypatch.setitem(G.GRAFOS,c.id,wrong)
    with pytest.raises(G.GrafoInvalido,match='F-GRAFO-FOCO'):
        G.montar(c.id,c.acoes)
    monkeypatch.setitem(G.GRAFOS,c.id,original)


def test_familia_nao_implementada_nunca_ganha_atores_genéricos():
    with pytest.raises(G.GrafoInvalido,match='F-GRAFO-SEM-FICHA'):
        G.montar('turbina_desconhecida',('rotate',))
    c=C.CAPACIDADES['optical_projection']
    with pytest.raises(G.GrafoInvalido,match='F-GRAFO-EVENTO'):
        G.montar(c.id,('source','wafer'))
    p=plan()
    p['eventos_diretor'][0]['direcao_evento']['acoes_necessarias']=[
        'source','reticle','projection','turbine']
    assert 'F-DIRETOR-SEM-CAPACIDADE' in issues(p)


def test_planejador_nao_finge_inspecao_de_pixels_ou_producao():
    p=D.expandir(plan())
    assert all(not s['plano_causal']['publicar'] for s in p['shots'])
    assert all(s['plano_causal']['revisao_visual']=='PENDENTE' for s in p['shots'])
    assert p['diretor_automatico']['fatos_verificados_externamente'] is False
    assert p['diretor_automatico']['revisao_visual']=='REPROVADO_ESTILO_LEGADO'
    assert F.avaliar(plan())['visual_approval']=='REPROVADO_ESTILO_LEGADO'
    legacy=json.loads((ROOT/'docs/v4/formatos/filme_panama_ciclo_19s.json').read_text('utf8'))
    assert D.expandir(legacy) is legacy
    assert F.avaliar(legacy)['pronto']


def test_requisito_falso_nao_burla_grafo_causal():
    p=D.expandir(plan())
    shot=copy.deepcopy(p['shots'][0])
    shot['processo_visual']['grafo_causal_requerido']=True
    shot['plano_causal']['publicar']=True
    resolved,errors=C.decidir(shot)
    assert resolved is None
    assert any(x['codigo']=='F-GRAFO-DIVERGENTE' for x in errors)
