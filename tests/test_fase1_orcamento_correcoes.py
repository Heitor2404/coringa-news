"""Correções do orçamento depois da Torre Eiffel 3 (12/11/2026), só modo monitorar, sem chamadas reais:
etapa `_gerar_roteiro` reconhecida · reserva pelo custo médio · pior caso com a base e a sobrecarga que sempre vão ·
M1 descartada e M2 desligada · falhas, tentativas e regressão."""
import json
import types

import pytest

from src import claude, custo, orcamento_video as orc

# Torre Eiffel 3 (run 43323322779): tokens de pedido que o monitor estimou e o custo real de cada chamada
TORRE3 = [('garimpo', 4107, 0.0893), ('roteiro', 4533, 0.0975), ('crítica', 5147, 0.0694), ('ganchos', 3493, 0.0299)]


@pytest.fixture(autouse=True)
def limpo(monkeypatch):
    custo.zerar()
    orc._ORC.clear(); orc._ORC['aberto'] = False
    orc._LOTE.clear(); orc._LOTE['aberto'] = False
    # estes testes conferem a MECÂNICA do monitor com os limites antigos (0,30/0,24); a política nova (0,50/0,40/0,35)
    # tem teste próprio em test_valores_aprovados
    monkeypatch.setattr(orc, 'TETO_USD', 0.30); monkeypatch.setattr(orc, 'ALVO_USD', 0.24)
    monkeypatch.setattr(orc, 'ALERTA_USD', 0.30)
    for k in ('ORCAMENTO_MODO', 'CLAUDE_SISTEMA_PROPRIO', 'FATOS_NO_SISTEMA'):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(claude, '_falhas', 0)
    yield
    custo.zerar()
    orc._ORC.clear(); orc._ORC['aberto'] = False


def _falso(monkeypatch, respostas):
    chamadas, fila = [], list(respostas)

    def run(cmd, input=None, capture_output=None, text=None, timeout=None, cwd=None, env=None):
        chamadas.append({'cmd': list(cmd), 'input': input})
        usd, ok = fila.pop(0) if fila else (0.05, True)
        r = {'type': 'result', 'is_error': not ok, 'result': 'OK' if ok else 'erro', 'total_cost_usd': usd,
             'usage': {'input_tokens': 2, 'cache_creation_input_tokens': 10000, 'cache_read_input_tokens': 6397,
                       'output_tokens': 900}}
        return types.SimpleNamespace(stdout=json.dumps(r), stderr='', returncode=0)
    monkeypatch.setattr(claude.subprocess, 'run', run)
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_TOKEN', 'tok')
    return chamadas


def _pedido(tokens):
    """Um pedido que o monitor estima com ~`tokens` tokens (descontado o SISTEMA, que também conta)."""
    return 'x' * int(max(0, tokens - orc.tokens(claude.SISTEMA)) * orc.CHARS_POR_TOKEN)


# ───────── 1. etapa _gerar_roteiro ─────────
def _gerar_roteiro(prompt):           # mesmo nome da função de src/roteiro.py: é o nome que o livro-caixa enxerga
    return claude.pedir(prompt)


def test_gerar_roteiro_e_reconhecido_como_roteiro_essencial(monkeypatch):
    _falso(monkeypatch, [(0.10, True)])
    orc.abrir('v')
    custo.tentativa('t')
    _gerar_roteiro('escreva')
    e = orc.resumo()['eventos'][0]
    assert e['etapa'] == 'roteiro' and e['classe'] == 'essencial'
    assert custo.LIVRO[-1]['etapa'] == 'roteiro'                       # o livro-caixa também passa a chamar de roteiro
    assert 'roteiro' in orc._feitas_na_tentativa(custo._tent['n'])


def test_etapa_normalizada_usa_a_tabela_do_livro_caixa():
    assert orc.etapa_normalizada('_gerar_roteiro') == 'roteiro' and orc.etapa_normalizada('revisar') == 'crítica'
    assert orc.etapa_normalizada('escolher_gancho') == 'ganchos' and orc.etapa_normalizada('qualquer') == 'qualquer'


# ───────── 2. reserva ─────────
def test_reserva_pelo_custo_medio_nao_estoura_o_teto_no_comeco():
    custo.tentativa('t')
    orc.abrir('v')
    r = orc.reserva('garimpo')
    assert r == pytest.approx(orc.CUSTO_MEDIO['roteiro'] + orc.CUSTO_MEDIO['crítica'])
    pior = orc.pior_caso(4107, 'garimpo', 'sonnet', base_em_cache=False)
    assert orc.decidir('garimpo', pior, 0.0, r, 0.30, 0.24) != 'pedir autorização'    # antes: pedia, com gasto zero


# ───────── 3. pior caso com base e sobrecarga ─────────
@pytest.mark.parametrize('k', range(4))
def test_pior_caso_cobre_cada_chamada_da_torre_3(k):
    etapa, est, real = TORRE3[k]
    assert orc.pior_caso(est, etapa, 'sonnet', base_em_cache=k > 0) >= real          # garimpo: 0,0654 < 0,0893 antes


def test_pior_caso_conta_base_e_sobrecarga():
    p = orc.PRECOS['sonnet']
    sem_nada = (orc.SAIDA_MAX['roteiro'] * p['saida']) / 1e6 + orc.MARGEM_USD
    esperado = sem_nada + (orc.SOBRECARGA_POR_CHAMADA * p['entrada'] + orc.BASE_CLAUDE_CODE * p['cache_lido']) / 1e6
    assert orc.pior_caso(0, 'roteiro', 'sonnet') == pytest.approx(esperado, abs=1e-4)
    assert orc.pior_caso(0, 'roteiro', 'sonnet', base_em_cache=False) > orc.pior_caso(0, 'roteiro', 'sonnet')


def test_replay_da_torre_3_pelo_claude_falso(monkeypatch):
    """A rodada real, chamada a chamada: o que o monitor registraria agora."""
    _falso(monkeypatch, [(real, True) for _, _, real in TORRE3])
    orc.abrir('torre 3')
    custo.tentativa('torre')
    for etapa, est, _ in TORRE3:
        with custo.etapa(etapa):
            claude.pedir(_pedido(est))
    r = orc.resumo()
    dec = [e['decisao'] for e in r['eventos']]
    assert dec == ['chamar (acima do alvo)'] * 3 + ['pular']          # antes: pedir autorização (2×) e pular
    assert r['estimativa_baixa'] == [] and not r['estourou_teto'] and r['gasto_usd'] == pytest.approx(0.2861, abs=1e-3)
    assert [e['classe'] for e in r['eventos']] == ['essencial', 'essencial', 'essencial', 'opcional']


# ───────── 4. M1 descartada, M2 desligada ─────────
def test_m1_e_m2_desligadas_por_padrao(monkeypatch):
    ch = _falso(monkeypatch, [(0.05, True)] * 2)
    orc.abrir('v')
    with claude.fatos_compartilhados('FATOS ' * 300):
        claude.pedir('A\n' + 'FATOS ' * 300 + '\nB')
    monkeypatch.setenv('CLAUDE_SISTEMA_PROPRIO', '1')                   # variável do repositório que sobrou: ignorada
    claude.pedir('C')
    for c in ch:
        assert '--system-prompt' not in c['cmd'] and '--append-system-prompt' in c['cmd']
        assert c['cmd'][c['cmd'].index('--append-system-prompt') + 1] == claude.SISTEMA
    assert 'FATOS ' * 300 in ch[0]['input'] and not orc.resumo()['m2']
    assert 'M2: desligada' in orc.linha_telegram()


# ───────── 5. falhas e tentativas ─────────
def test_falhas_dentro_do_gerar_roteiro_e_tentativas(monkeypatch):
    _falso(monkeypatch, [(0.08, True), (0.03, False), (0.10, True), (0.07, True), (0.09, True)])
    orc.abrir('v')
    custo.tentativa('A')
    with custo.etapa('garimpo'):
        claude.pedir('g')
    with pytest.raises(RuntimeError):
        _gerar_roteiro('r1')                                            # 1ª tentativa do roteiro falha (custou 0,03)
    _gerar_roteiro('r2')                                                # 2ª dá certo
    custo.tentativa('B')                                                # tema descartado: reserva volta, gasto soma
    assert orc.reserva('garimpo') == pytest.approx(orc.CUSTO_MEDIO['roteiro'] + orc.CUSTO_MEDIO['crítica'])
    with custo.etapa('garimpo'):
        claude.pedir('g')
    _gerar_roteiro('r3')
    r = orc.resumo()
    assert [e['etapa'] for e in r['eventos']] == ['garimpo', 'roteiro', 'roteiro', 'garimpo', 'roteiro']
    assert [e['ok'] for e in r['eventos']] == [True, False, True, True, True]
    assert r['gasto_usd'] == pytest.approx(0.37) and r['estourou_teto']   # o monitor aponta, mas não bloqueia


# ───────── 6. regressão: monitorar não muda nada ─────────
@pytest.mark.parametrize('modo', [None, 'monitorar', 'aplicar'])
def test_regressao_comando_identico_e_sem_bloqueio(monkeypatch, modo):
    if modo:
        monkeypatch.setenv('ORCAMENTO_MODO', modo)
    sem = _falso(monkeypatch, [(0.25, True)] * 3)
    for e in ('garimpo', 'roteiro', 'ganchos'):
        with custo.etapa(e):
            claude.pedir(f'pedido {e}')
    custo.zerar()
    com = _falso(monkeypatch, [(0.25, True)] * 3)                        # 0,75: muito acima do teto
    orc.abrir('v')
    for e in ('garimpo', 'roteiro', 'ganchos'):
        with custo.etapa(e):
            assert claude.pedir(f'pedido {e}') == 'OK'                   # nenhuma chamada barrada nem pulada
    assert [c['cmd'] for c in com] == [c['cmd'] for c in sem] and [c['input'] for c in com] == [c['input'] for c in sem]
    assert orc.modo() == 'monitorar' and 'pedir autorização' in [e['decisao'] for e in orc.resumo()['eventos']]
