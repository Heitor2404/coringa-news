"""Plano-mestre, etapas B e C (12/11/2026): plano editorial adaptativo e função dos blocos do roteiro.
Três assuntos muito diferentes (golpe histórico, resposta imune, cor do céu), respostas de IA simuladas, nenhuma chamada."""
import copy
import json
import os
from pathlib import Path

import pytest

from src import cofre, editorial as ed, gemini, roteiro

RAIZ = Path(__file__).resolve().parent.parent
CASOS = json.loads((RAIZ / 'tests/editorial_casos.json').read_text(encoding='utf-8'))


def _v(nome):
    c = copy.deepcopy(CASOS[nome])
    v = c['roteiro']
    v['categoria'] = c['categoria']
    return ed.preparar(v), c['fatos']


# ───────── B: plano editorial ─────────
@pytest.mark.parametrize('nome', list(CASOS))
def test_tres_assuntos_tem_plano_valido_sem_problemas(nome):
    v, fatos = _v(nome)
    assert v['plano']['origem'] == 'roteirista' and v['plano']['versao'] == ed.VERSAO
    assert ed.validar_plano(v['plano'], fatos) == []
    assert ed.avaliar_roteiro(v, fatos)['problemas'] == []


def test_os_tres_planos_sao_diferentes_e_coerentes_com_o_assunto():
    p = {n: _v(n)[0]['plano'] for n in CASOS}
    assert {p[n]['angulo']['tipo'] for n in p} == {'misterio', 'mecanismo', 'contraste'}
    assert 'historico_investigativo' in p['historia']['modos'] and p['biologia']['modos'] == ['mecanismo']
    assert 'comparacao' in p['ciencia']['modos']
    assert len({p[n]['duracao_alvo_s'] for n in p}) == 3                       # duração por assunto, não fixa
    assert any(e['natureza'] == 'analogia' for e in p['biologia']['evidencias'])     # analogia dita como analogia


def test_normaliza_valores_soltos_e_limita_duracao():
    p = ed.normalizar_plano({'promessa': 'x', 'angulo': 'Mecanismo', 'modos': 'Mecanismo', 'duracao_alvo_s': '300',
                             'complexidade': 'ALTA', 'evidencias': ['fato solto'], 'viabilidade': {'ok': 'não'}})
    assert p['angulo']['tipo'] == 'mecanismo' and p['modos'] == ['mecanismo'] and p['complexidade'] == 'alta'
    assert p['duracao_alvo_s'] == ed.DURACAO_MAX and p['evidencias'][0]['certeza'] == 'media'
    assert p['viabilidade']['ok'] is False


def test_promessa_falsa_clickbait_e_inviavel_sao_apontadas():
    v, fatos = _v('historia')
    p = copy.deepcopy(v['plano'])
    p['promessa'] = 'você não vai acreditar como ele vendeu a torre em 1931'
    p['viabilidade'] = {'ok': False, 'motivo': 'não há imagem do golpe'}
    erros = ed.validar_plano(p, fatos)
    assert any('clickbait' in e for e in erros) and any('1931' in e for e in erros) and any('não é viável' in e for e in erros)


def test_evidencia_de_fato_sem_fonte_e_apontada_mas_analogia_nao():
    v, fatos = _v('biologia')
    assert ed.validar_plano(v['plano'], fatos) == []                            # a analogia sem fonte é aceita
    v['plano']['evidencias'][0]['fonte'] = ''
    assert any('sem fonte' in e for e in ed.validar_plano(v['plano'], fatos))


def test_roteiro_antigo_sem_plano_continua_funcionando():
    v = {'titulo': 'Antigo', 'cenas': [{'tipo': 'gancho', 'fala': 'Algo aconteceu.'}, {'tipo': 'historia', 'fala': 'Depois.'},
                                      {'tipo': 'fechamento', 'fala': 'Segue.'}]}
    ed.preparar(v)
    assert v['plano']['origem'] == 'derivado'
    assert ed.avaliar_roteiro(v)['problemas'] == []                             # não cobra o que não foi pedido
    assert ed.limite_palavras(v['plano'], roteiro.LIMITE_PALAVRAS) == roteiro.LIMITE_PALAVRAS
    assert 'derivado' in ed.linha_telegram(v) and ed.para_critica(v) == ''


# ───────── C: função dos blocos ─────────
def test_roteiro_sem_payoff_e_com_fim_solto_e_apontado():
    v, fatos = _v('ciencia')
    for c in v['cenas']:
        if c.get('bloco', {}).get('funcao') in ('payoff', 'consequencia', 'comparacao'):
            c['bloco']['funcao'] = 'contexto'
    probs = ed.avaliar_roteiro(v, fatos)['problemas']
    assert any('payoff' in p for p in probs) and any('não fecha' in p for p in probs)


def test_bloco_sem_funcao_premissa_repetida_e_numero_inventado():
    v, fatos = _v('historia')
    v['cenas'][2].pop('bloco')
    v['cenas'][4]['fala'] = 'André Poisson pagou o preço e ainda uma propina enorme.'
    v['cenas'][5]['fala'] = 'André Poisson pagou o preço e ainda a propina enorme.'
    v['cenas'][6]['fala'] = 'Lustig fugiu para Viena com 70 mil francos.'
    probs = ed.avaliar_roteiro(v, fatos)['problemas']
    assert any('sem função' in p for p in probs)
    assert any('repetem' in p for p in probs)
    assert any('fora dos fatos (70)' in p for p in probs)


def test_promessa_nao_retomada_na_segunda_metade():
    v, fatos = _v('ciencia')
    for c in v['cenas'][3:-1]:
        c['fala'] = 'Uma frase qualquer sem relação nenhuma.'
    assert any('promessa não cumprida' in p for p in ed.avaliar_roteiro(v, fatos)['problemas'])


def test_suspense_criminal_forcado_em_biologia_e_apontado_mas_nao_no_golpe():
    v, fatos = _v('biologia')
    v['cenas'][1]['fala'] = 'O vírus é o criminoso, e a célula, a vítima.'
    assert any('crime/suspense' in p for p in ed.avaliar_roteiro(v, fatos)['problemas'])
    h, fh = _v('historia')
    h['cenas'][5]['fala'] = 'A vergonha impediu a vítima de denunciar o golpe.'
    assert not any('crime/suspense' in p for p in ed.avaliar_roteiro(h, fh)['problemas'])


def test_duracao_do_plano_muda_o_teto_de_palavras():
    v, _ = _v('ciencia')                                                         # 40 s
    assert ed.limite_palavras(v['plano'], roteiro.LIMITE_PALAVRAS) == round(40 * ed.PALAVRAS_POR_S) + 10
    assert ed.limite_palavras(_v('historia')[0]['plano'], roteiro.LIMITE_PALAVRAS) == round(55 * ed.PALAVRAS_POR_S) + 10


# ───────── integração: mesma quantidade de chamadas, crítica recebe os problemas, reescrita herda ─────────
def _cenas_validas(v, n=13):
    base = v['cenas'][:-1]
    cenas = [dict(base[k % len(base)], fala=f"{base[k % len(base)]['fala'].rstrip('.')} parte {k}.") for k in range(n)]
    return cenas + [v['cenas'][-1]]


def test_critica_recebe_os_problemas_detectados_e_a_reescrita_herda_plano_e_blocos(monkeypatch):
    v, fatos = _v('historia')
    v['cenas'] = _cenas_validas(v)
    v['cenas'][3].pop('bloco')
    enviados = []
    reescrita = {'roteiro': {'titulo': v['titulo'], 'cenas': [{k: x for k, x in c.items() if k != 'bloco'} for c in v['cenas']]},
                 'aprovado': False, 'notas': {}}
    monkeypatch.setattr(gemini, 'json_', lambda p, *a, **k: enviados.append(p) or copy.deepcopy(reescrita))
    monkeypatch.setattr(roteiro, 'PROMPT_CRITICA', '{escopo}|{fatos}|{roteiro}|{problemas}')
    novo = roteiro.revisar(v, fatos, problemas=ed.para_critica(v, fatos))
    assert len(enviados) == 1                                                    # nenhuma chamada nova
    assert 'PROBLEMAS DETECTADOS' in enviados[0] and 'sem função' in enviados[0]
    assert '"plano"' in enviados[0]                                              # a crítica vê o plano
    assert novo['plano']['promessa'] == v['plano']['promessa']
    assert [c.get('bloco') for c in novo['cenas']] == [c.get('bloco') for c in v['cenas']]


def test_gerar_roteiro_usa_o_teto_do_plano(monkeypatch):
    v, _ = _v('ciencia')                                                         # 40 s → teto 120 palavras
    v['cenas'] = _cenas_validas(v, 14)
    for c in v['cenas'][:-1]:
        c['fala'] = 'uma duas tres quatro cinco seis sete oito nove dez'            # 140 palavras
    pedidos = []
    monkeypatch.setattr(gemini, 'json_', lambda p, *a, **k: pedidos.append(p) or copy.deepcopy(v))
    with pytest.raises(ValueError):
        roteiro._gerar_roteiro('PEDIDO', tentativas=1)
    sem_plano = copy.deepcopy(v)
    sem_plano.pop('plano')
    monkeypatch.setattr(gemini, 'json_', lambda p, *a, **k: copy.deepcopy(sem_plano))
    assert roteiro._gerar_roteiro('PEDIDO', tentativas=1)                       # 140 < 160 (o teto de sempre)


# ───────── prompts do cofre ─────────
@pytest.mark.skipif(not (Path(os.environ.get('COFRE_DIR') or RAIZ / 'cofre') / 'prompts').exists(), reason='sem o cofre')
def test_prompts_do_cofre_pedem_plano_e_bloco_e_formatam():
    r = cofre.prompt('PROMPT_ROTEIRO_EXPLICA')
    txt = r.format(pergunta='p', formato='explica', noticia='', fatos='F', partes='', categoria='CIÊNCIA', acervo='')
    assert '"plano"' in txt and '"bloco"' in txt and 'NUNCA force suspense' in txt
    assert 'fio condutor: uma pessoa' not in txt                                  # receita única de história saiu
    c = cofre.prompt('PROMPT_CRITICA').format(escopo='', fatos='F', roteiro='{}', problemas='PROBLEMAS X')
    assert 'PROBLEMAS X' in c and 'não remova "plano", "bloco"' in c
    assert len(r) < 13000                                                         # prompt cresceu ≈ 16% (10,5 → 12,2 kB)
