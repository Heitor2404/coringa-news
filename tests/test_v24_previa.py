"""V2.4 — composição demonstrativa genérica (mecanismo.estados) + prévia visual antes da narração.

Auditoria do MP4 43730252500 (2/10): mecanismos críticos viraram cartões de texto (frases do contrato jogadas em
processo.etapas/diagrama.explicativo, setas sem objeto em forcas.vetores). Estes testes conferem que:
  · a composição nova mostra objetos, estado inicial, mudança e resultado para temas DIFERENTES (não é da lagartixa);
  · o contrato recusa esquema sem mudança; mecanismo crítico com frases soltas não é aceito como representação;
  · a prévia renderiza no palco real e bloqueia composição que não muda / não desenha nada.
"""
from __future__ import annotations

import pytest

from src.v2 import contrato, previa

pytest.importorskip('playwright')


def _esq(objetos, estados):
    return {'objetos': objetos, 'estados': estados}


# Esquemas de outros temas, só com formas genéricas (superfície, corpo, seta, partículas)
TACOMA = _esq([{'id': 'pil', 'forma': 'superficie', 'rotulo': 'PILARES', 'x': .5, 'y': .9, 'w': 1, 'h': .1},
               {'id': 'pon', 'forma': 'corpo', 'rotulo': 'TABULEIRO', 'x': .5, 'y': .5, 'w': .8, 'h': .08},
               {'id': 'ven', 'forma': 'seta', 'rotulo': 'VENTO', 'x': .12, 'y': .25, 'w': .2, 'angulo': 0}],
              [{'rotulo': 'VENTO CONSTANTE', 'objetos': {}},
               {'rotulo': 'O TABULEIRO TORCE', 'objetos': {'pon': {'rot': 8}}},
               {'rotulo': 'TORÇÃO CRESCE E ROMPE', 'objetos': {'pon': {'rot': -14, 'dy': .12}}}])
EVER_GIVEN = _esq([{'id': 'm1', 'forma': 'superficie', 'rotulo': 'MARGEM', 'x': .5, 'y': .1, 'w': 1, 'h': .1},
                   {'id': 'm2', 'forma': 'superficie', 'x': .5, 'y': .9, 'w': 1, 'h': .1},
                   {'id': 'nav', 'forma': 'corpo', 'rotulo': 'NAVIO', 'x': .5, 'y': .5, 'w': .6, 'h': .12}],
                  [{'rotulo': 'NAVEGA NO CANAL', 'objetos': {}},
                   {'rotulo': 'VENTO EMPURRA A PROA', 'objetos': {'nav': {'rot': 12}}},
                   {'rotulo': 'ENCALHA ATRAVESSADO', 'objetos': {'nav': {'rot': 34, 'escala': 1.15}},
                    'relacoes': [{'de': 'nav', 'para': 'm1', 'tipo': 'contato', 'forca': 1, 'rotulo': 'ENCALHE'}]}])
KATRINA = _esq([{'id': 'diq', 'forma': 'superficie', 'rotulo': 'DIQUE', 'x': .25, 'y': .55, 'w': .08, 'h': .7},
                {'id': 'agu', 'forma': 'corpo', 'rotulo': 'ÁGUA', 'x': .12, 'y': .8, 'w': .22, 'h': .3},
                {'id': 'cid', 'forma': 'corpo', 'rotulo': 'CIDADE', 'x': .7, 'y': .85, 'w': .5, 'h': .2}],
               [{'rotulo': 'NÍVEL NORMAL', 'objetos': {}},
                {'rotulo': 'A ÁGUA SOBE', 'objetos': {'agu': {'dy': -.25, 'escala': 1.3}},
                 'relacoes': [{'de': 'agu', 'para': 'diq', 'tipo': 'empurra', 'forca': .8, 'rotulo': 'PRESSÃO'}]},
                {'rotulo': 'O DIQUE CEDE', 'objetos': {'agu': {'dx': .3, 'dy': -.1, 'escala': 1.3}, 'diq': {'rot': 25, 'opacidade': .4}}}])


@pytest.mark.parametrize('nome,esq', [('tacoma', TACOMA), ('ever_given', EVER_GIVEN), ('katrina', KATRINA)])
def test_esquema_generico_de_outros_temas_renderiza_e_muda(nome, esq, tmp_path):
    assert contrato.esquema_problemas(esq) == []
    r = previa.renderizar('mecanismo.estados', {'titulo': nome, 'esquema': esq}, tmp_path, nome)
    r['params'] = {'esquema': esq}
    assert previa.problemas('mecanismo.estados', r) == [], (nome, r['graves'], r['erros'], r['medidas'])
    assert r['medidas']['dif_ini_fim'] >= previa.DIFERENCA_MIN


def test_contrato_recusa_esquema_sem_mudanca_e_objeto_inexistente():
    parado = _esq(TACOMA['objetos'], [{'rotulo': 'A', 'objetos': {}}, {'rotulo': 'B', 'objetos': {}}])
    assert 'estados iguais: nada muda na tela' in contrato.esquema_problemas(parado)
    fantasma = _esq(TACOMA['objetos'], [{'rotulo': 'A'}, {'rotulo': 'B', 'objetos': {'xx': {'dy': .1}}}])
    assert any('inexistente' in p for p in contrato.esquema_problemas(fantasma))
    assert contrato.esquema_problemas(None) == ['esquema ausente']


def test_mecanismo_critico_com_frases_soltas_nao_e_representacao():
    ac = {'tipo': 'mecanismo', 'importancia': 'critica', 'dados': {}}
    frases = {'etapas': ['deslocamento temporário da nuvem eletrônica em uma molécula', 'cria um dipolo instantâneo']}
    rotulos = {'etapas': ['Pedal', 'Coroa e corrente', 'Catraca', 'Roda']}
    assert not contrato.comp_aceita(ac, 'processo.etapas', frases)
    assert contrato.comp_aceita(ac, 'processo.etapas', rotulos)                     # passos curtos e autorados: valem
    assert contrato.comp_aceita({**ac, 'importancia': 'apoio'}, 'processo.etapas', frases)   # apoio: não é exigido
    assert contrato.comp_aceita({'tipo': 'processo', 'importancia': 'critica'}, 'processo.etapas', frases)


def test_previa_bloqueia_composicao_que_nao_desenha_o_mecanismo(tmp_path):
    # força sem nome reconhecível nem ângulo: o render não desenha seta nenhuma → nada muda entre início e fim
    r = previa.renderizar('forcas.vetores', {'titulo': 'Van der Waals', 'forcas': ['forças de Van der Waals']}, tmp_path, 'fv')
    r['params'] = {}
    assert any('início e fim iguais' in p for p in previa.problemas('forcas.vetores', r))


def test_validar_relata_e_bloqueia_por_evento(tmp_path):
    bom = {'id': 'e1', 'tipo': 'mecanismo', 'importancia': 'critica', 'mostrar': 'Ponte torce',
           'dados': {'esquema': TACOMA}, 'representacao': {'modo': 'composicao', 'comp': 'mecanismo.estados'}}
    ruim = {'id': 'e2', 'tipo': 'mecanismo', 'importancia': 'critica', 'mostrar': 'Força',
            'dados': {'forcas': ['forças de Van der Waals']}, 'representacao': {'modo': 'composicao', 'comp': 'forcas.vetores'}}
    v = {'cenas': [{'acontecimento': bom}, {'acontecimento': ruim}, {'acontecimento': bom}]}
    rel = previa.validar(v, tmp_path)
    assert [e['evento'] for e in rel['eventos']] == ['e1', 'e2']                  # cada acontecimento uma vez
    assert [b['evento'] for b in rel['bloqueios']] == ['e2']
    assert (tmp_path / 'folha.jpg').exists() and (tmp_path / 'previa.json').exists()
