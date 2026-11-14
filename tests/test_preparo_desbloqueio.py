"""Correções GERAIS do preparo V2.3 vindas do piloto da lagartixa (execução 43643345166), offline:
(1) tipo declarado incompatível com os dados + etapas reais → processo (sem inventar dado; ambíguo fica);
(2) fenômeno sem ano não herda a época geral do vídeo (só história datada herda)."""
import json
from pathlib import Path

import pytest

from src import gemini
from src.v2 import preparo

F = Path(__file__).parent / 'piloto_lagartixa'


def _v():
    v = gemini.extrair_json((F / 'roteiro_bruto.txt').read_text(encoding='utf-8'))
    v['tipo_conteudo'] = 'geral'                       # classificação real da execução ([viabilidade] geral)
    v['fatos'] = 'ÉPOCA/LUGAR: Atual (reportagens de 2026), com aplicações tecnológicas desde 2007-2010\n'
    v['acervo'] = []
    return v


def test_e9_proporcao_com_etapas_vira_processo_e_nao_bloqueia():
    rel = preparo.preparar(_v(), [])
    e9 = next(e for e in rel['eventos'] if e['id'] == 'e9')
    assert e9['tipo_original'] == 'proporcao' and e9['tipo'] == 'processo' and 'etapas' in e9['reclassificacao']
    assert e9['representacao'] == {'modo': 'composicao', 'comp': 'processo.etapas'}
    assert not any(b['evento'] == 'e9' for b in rel['bloqueios'])
    assert e9['dados']['etapas'] == ['moléculas próximas', 'moléculas se afastam', 'atração desaparece']   # nada inventado


@pytest.mark.parametrize('dados', [
    {'pct': 40, 'etapas': ['a1', 'b1', 'c1']},          # tem o dado do próprio tipo: ambíguo, fica
    {'etapas': ['a1', 'b1']},                           # etapas insuficientes
    {'etapas': ['10%', '20%', '30%']},                  # "etapas" que são números
    {}])
def test_reclassificacao_conservadora(dados):
    assert preparo.reclassificar({'tipo': 'proporcao', 'dados': dados}, {})[0] == 'proporcao'


def test_tipo_representavel_por_foto_nao_e_reclassificado():
    assert preparo.reclassificar({'tipo': 'pessoa', 'dados': {'etapas': ['nasce', 'estuda', 'trabalha']}}, {})[0] == 'pessoa'


def test_fenomeno_sem_ano_nao_herda_a_epoca_do_video():
    assert preparo.atemporal({'tipo': 'mecanismo'}, {'quando': 'atual'}, {'tipo_conteudo': 'geral'})
    assert preparo.atemporal({'tipo': 'processo'}, {'quando': ''}, {'tipo_conteudo': 'mecanismo'})


@pytest.mark.parametrize('ac,bruto,v', [
    ({'tipo': 'mecanismo'}, {'quando': 'atual'}, {'tipo_conteudo': 'historico'}),     # história datada: herda
    ({'tipo': 'impacto'}, {'quando': ''}, {'tipo_conteudo': 'geral'}),                # acontecimento, não fenômeno
    ({'tipo': 'mecanismo'}, {'quando': 'março de 2021'}, {'tipo_conteudo': 'geral'}),  # tem data
    ({'tipo': 'mecanismo', 'dados': {'data': '1980'}}, {'quando': ''}, {'tipo_conteudo': 'geral'})])
def test_controle_temporal_preservado_para_fatos_datados(ac, bruto, v):
    assert not preparo.atemporal(ac, bruto, v)


def test_e4_foto_de_2009_nao_e_penalizada_por_2026():
    x = {'id': 'a3', 'arq': 'x', 'mostra': 'Foto em close das cerdas microscópicas na sola da pata de uma lagartixa', 'titulo': 'gecko foot',
         'ano': 2009, 'tipo_img': 'foto'}
    v = _v()
    for c in v['cenas']:
        if (c.get('acontecimento') or {}).get('id') == 'e4':
            c['foto'] = 'a3'
    rel = preparo.preparar(v, [x])
    rev = [r for r in rel['revisoes'] if r['evento'] == 'e4']
    assert not any('2026' in r['evidencia'] for r in rev)
