"""Fase 1, etapa 1 (12/11/2026): orçamento por vídeo em MODO MONITORAR. Nenhuma chamada real (o `claude -p` é falso).
1 monitorar não muda comando, resposta, roteiro nem publicação · 2 contabilização (custos, falhas, tentativas)
3 pior caso e estouros · 4 reserva das essenciais (ganchos opcional) · 5 parâmetros (só calculados) · 6 NTC isolado."""
import copy
import json
import re
import subprocess
import types
from pathlib import Path

import pytest

import main
from src import claude, custo, fiscal, gemini, orcamento_video as orc

RAIZ = Path(__file__).resolve().parent.parent
SOMBRA_REAL = fiscal.sombra


@pytest.fixture(autouse=True)
def limpo(monkeypatch):
    custo.zerar()
    orc._ORC.clear()
    orc._ORC['aberto'] = False
    monkeypatch.delenv('ORCAMENTO_MODO', raising=False)
    monkeypatch.setattr(claude, '_falhas', 0)
    yield
    custo.zerar()
    orc.fechar()


def _falso(monkeypatch, respostas):
    """`claude -p` falso: cada chamada devolve a próxima resposta (usd, ok, saída) e guarda o que recebeu."""
    chamadas = []
    fila = list(respostas)

    def run(cmd, input=None, capture_output=None, text=None, timeout=None, cwd=None, env=None):
        chamadas.append({'cmd': list(cmd), 'input': input, 'env': dict(env or {})})
        usd, ok, saida = fila.pop(0) if fila else (0.05, True, 1000)
        if ok == 'timeout':
            raise subprocess.TimeoutExpired(cmd, timeout)
        r = {'type': 'result', 'is_error': not ok, 'result': 'RESPOSTA OK' if ok else 'erro', 'total_cost_usd': usd,
             'usage': {'input_tokens': 2, 'cache_creation_input_tokens': 10000, 'cache_read_input_tokens': 7025,
                       'output_tokens': saida}}
        return types.SimpleNamespace(stdout=json.dumps(r), stderr='', returncode=0)
    monkeypatch.setattr(claude.subprocess, 'run', run)
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_TOKEN', 'tok')
    return chamadas


def _pedir(etapa, prompt='x' * 30000, leve=False):
    with custo.etapa(etapa):
        return claude.pedir(prompt, leve)


def test_valores_aprovados():
    assert orc.TETO_USD == 0.30 and orc.ALVO_USD == 0.24
    assert {'garimpo', 'pesquisa', 'roteiro', 'crítica'} <= orc.ESSENCIAIS and orc.OPCIONAIS == {'ganchos'}


# ───────── 1. monitorar preserva comando, resposta, roteiro e publicação ─────────
def test_monitorar_nao_muda_o_comando_nem_a_resposta(monkeypatch):
    sem = _falso(monkeypatch, [(0.05, True, 900)] * 4)
    r_sem = [_pedir(e) for e in ('garimpo', 'roteiro', 'crítica', 'ganchos')]
    custo.zerar()
    com = _falso(monkeypatch, [(0.20, True, 900)] * 4)          # caro: o "aplicar" pularia/pediria autorização
    orc.abrir('teste')
    r_com = [_pedir(e) for e in ('garimpo', 'roteiro', 'crítica', 'ganchos')]
    assert r_com == r_sem == ['RESPOSTA OK'] * 4
    assert len(com) == len(sem) == 4                              # nenhuma chamada a menos (nada pulado de verdade)
    for a, b in zip(sem, com):
        assert a['cmd'] == b['cmd'] and a['input'] == b['input'] and a['env'] == b['env']
    decisoes = [e['decisao'] for e in orc.resumo()['eventos']]
    assert 'pular' in decisoes and 'pedir autorização' in decisoes   # o que FARIA, só registrado


def test_monitorar_preserva_o_roteiro_pela_cascata(monkeypatch):
    """O caminho real dos roteiros (gemini.json_ → Claude primeiro) devolve o mesmo JSON com e sem orçamento."""
    monkeypatch.setattr(claude, 'disponivel', lambda: True)
    def run_json(cmd, input=None, **k):
        return types.SimpleNamespace(stdout=json.dumps({'type': 'result', 'result': '{"titulo": "T", "cenas": [1, 2]}',
                                                        'total_cost_usd': 0.29, 'usage': {}}), stderr='', returncode=0)
    monkeypatch.setattr(claude.subprocess, 'run', run_json)
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_TOKEN', 'tok')
    sem = gemini.json_('escreva o roteiro')
    orc.abrir('teste')
    com = [gemini.json_('escreva o roteiro') for _ in range(3)]  # 3 × 0,29: passa do teto já na 2ª
    assert all(c == sem for c in com) and orc.resumo()['estourou_teto']


def _montar(monkeypatch, tmp, nota, aberto_caro):
    cenas = [{'tipo': 'gancho', 'fala': 'a', 'imagem': 'a', 'img': 'a.jpg', 'start': 0, 'end': 3},
             {'tipo': 'historia', 'fala': 'b', 'imagem': 'b', 'img': 'b.jpg', 'start': 3, 'end': 58},
             {'tipo': 'fechamento', 'fala': 'c', 'start': 58, 'end': 60}]
    monkeypatch.setattr(main.voz, 'narrar', lambda *a, **k: (tmp / 'a.wav', [], [], 60.0))
    monkeypatch.setattr(main, 'escolher_musica', lambda *a, **k: None)
    monkeypatch.setattr(main, '_montar_cenas', lambda *a, **k: copy.deepcopy(cenas))
    monkeypatch.setattr(main, 'renderizar', lambda dados, audio, saida, trab, musica=None: saida.write_bytes(b''))
    monkeypatch.setattr(main, 'renderizar_capa', lambda *a, **k: None)
    monkeypatch.setattr(main, 'fiscal_final', lambda *a, **k: (nota, []))
    monkeypatch.setattr(main, 'pacote_diagnostico', lambda *a, **k: None)
    monkeypatch.setattr(main, 'erros_basicos', lambda *a, **k: [])
    monkeypatch.setattr(fiscal, 'sombra', lambda v, c, s, n, t: SOMBRA_REAL(v, c, None, n, t, pedir=lambda p: {},
                                                                          prompt_base='{fatos}{frases}{titulo}'))
    custo.zerar()
    orc._ORC.clear()
    orc._ORC['aberto'] = False
    if aberto_caro:                                   # vídeo que já passou do teto (o "aplicar" teria barrado)
        orc.abrir('teste')
        _falso(monkeypatch, [(0.35, True, 9000)])
        _pedir('roteiro')
    v = {'titulo': 'T', 'fatos': 'F', 'cenas': [{'tipo': 'gancho', 'fala': 'a'}, {'tipo': 'historia', 'fala': 'b'},
                                                {'tipo': 'fechamento', 'fala': 'c'}]}
    tmp.mkdir(exist_ok=True)
    main.montar_video(v, tmp, 'v')
    return v


@pytest.mark.parametrize('nota', [8.0, 4.0])
def test_monitorar_nao_muda_a_decisao_de_publicacao(monkeypatch, tmp_path, nota):
    sem = _montar(monkeypatch, tmp_path / 'sem', nota, False)
    com = _montar(monkeypatch, tmp_path / 'com', nota, True)
    assert com['_telegram']['resumo'] == sem['_telegram']['resumo'] and com['_bloqueado'] == sem['_bloqueado']
    assert '🛡 Orçamento (MONITORANDO, não bloqueia)' in com['_telegram']['diagnostico']
    assert 'PASSOU DO TETO' in com['_telegram']['diagnostico'] and '🛡' not in sem['_telegram']['diagnostico']


def test_curiosidade_abre_e_fecha_o_orcamento_sem_mudar_o_retorno(monkeypatch, tmp_path):
    vistos = []
    for r in (True, False, 'pular'):
        monkeypatch.setattr(main, '_fazer_curiosidade', lambda *a, **k: vistos.append(orc.aberto()) or r)
        assert main.fazer_curiosidade('tema', 1, tmp_path) == r
        assert not orc.aberto()
    assert vistos == [True, True, True]


def test_diario_usa_um_orcamento_so_para_todas_as_tentativas(monkeypatch, tmp_path):
    rotulos = []
    def inner(pasta):
        rotulos.append(orc._ORC['rotulo'])
        main.fazer_curiosidade('tema 1', 1, pasta)                # tentativa dentro do diário: não reabre
        rotulos.append(orc._ORC['rotulo'])
    monkeypatch.setattr(main, '_diario', inner)
    monkeypatch.setattr(main, '_fazer_curiosidade', lambda *a, **k: True)
    main.diario(tmp_path)
    assert rotulos == ['diário', 'diário'] and not orc.aberto()


# ───────── 2. contabilização ─────────
def test_conta_custos_falhas_e_tentativas(monkeypatch):
    _falso(monkeypatch, [(0.03, True, 500)])
    _pedir('pauta')                                              # antes de abrir: fica fora do orçamento
    _falso(monkeypatch, [(0.07, True, 3000), (0.02, False, 100), (0.0, 'timeout', 0), (0.10, True, 5000),
                         (0.04, True, 600)])
    orc.abrir('teste')
    custo.tentativa('tema A')
    _pedir('garimpo')
    with pytest.raises(RuntimeError):
        _pedir('roteiro')                                        # falhou mas gastou 0,02
    with pytest.raises(RuntimeError):
        _pedir('roteiro')                                        # não respondeu: 0
    custo.tentativa('tema B')                                    # tema descartado: o gasto continua somando
    _pedir('roteiro')
    _pedir('ganchos')
    r = orc.resumo()
    assert r['gasto_usd'] == pytest.approx(0.23) and custo.claude_usd() == pytest.approx(0.26)
    ev = r['eventos']
    assert [e['etapa'] for e in ev] == ['garimpo', 'roteiro', 'roteiro', 'roteiro', 'ganchos']
    assert [e['tentativa'] for e in ev] == [1, 1, 1, 2, 2]
    assert [e['real'] for e in ev] == pytest.approx([0.07, 0.02, 0.0, 0.10, 0.04])
    assert [e['ok'] for e in ev] == [True, False, False, True, True]
    assert ev[3]['gasto_antes'] == pytest.approx(0.09)


def test_custos_json_traz_o_orcamento(monkeypatch, tmp_path):
    _falso(monkeypatch, [(0.07, True, 3000)])
    orc.abrir('teste')
    _pedir('garimpo')
    custo.salvar(tmp_path / 'c.json')
    d = json.loads((tmp_path / 'c.json').read_text())
    assert d['orcamento']['modo'] == 'monitorar' and d['orcamento']['gasto_usd'] == pytest.approx(0.07)


# ───────── 3. pior caso e estouros ─────────
TORRE = [('garimpo', 10032, 3122, 0.0721), ('roteiro', 12374, 5591, 0.1061), ('crítica', 11614, 4098, 0.0881),
         ('ganchos', 9423, 647, 0.0449)]


@pytest.mark.parametrize('etapa,entrada,saida,real', TORRE)
def test_pior_caso_cobre_as_chamadas_medidas_da_torre(etapa, entrada, saida, real):
    assert orc.SAIDA_MAX[etapa] >= 1.5 * saida - 1
    assert orc.pior_caso(entrada, etapa, 'sonnet') >= real
    # a fórmula com a saída REAL reproduz o custo medido (erro ≤ 3%): os preços estão certos
    p = orc.PRECOS['sonnet']
    assert (entrada * p['entrada'] + 7025 * p['cache_lido'] + saida * p['saida']) / 1e6 == pytest.approx(real, rel=0.03)


def test_estimativa_de_entrada_e_conservadora():
    assert orc.tokens('a' * 3000) >= 1000                        # 3 caracteres por token: superestima o português
    assert orc.pior_caso(10000, 'x', 'modelo-desconhecido') > orc.pior_caso(10000, 'x', 'sonnet')   # desconhecido = caro
    assert orc.pior_caso(10000, 'roteiro', 'sonnet', base_em_cache=False) > orc.pior_caso(10000, 'roteiro', 'sonnet')


def test_identifica_estouros(monkeypatch):
    _falso(monkeypatch, [(0.09, True, 1000), (0.08, True, 1000), (0.90, True, 1000)])
    orc.abrir('teste')
    _pedir('garimpo')
    _pedir('roteiro', prompt='x' * 300)                          # 0,17 no total: ainda dentro do alvo
    ev = orc.resumo()['eventos']
    assert not ev[1]['estourou_alvo']
    _pedir('crítica', prompt='x' * 300)                          # real 0,90: acima do pior caso e do teto
    r = orc.resumo()
    assert r['estimativa_baixa'] == ['crítica'] and r['estourou_teto'] and r['eventos'][2]['estourou_alvo']
    assert 'PASSOU DO TETO' in orc.linha_telegram() and 'pior caso abaixo do real: crítica' in orc.linha_telegram()


# ───────── 4. reserva das essenciais ─────────
def _tipico(e):
    return orc.pior_caso(orc.ENTRADA_TIPICA[e], e, 'sonnet')


def test_reserva_das_essenciais_que_faltam():
    custo.tentativa('t')
    orc.abrir('teste')
    assert orc.reserva('tema') == pytest.approx(_tipico('garimpo') + _tipico('roteiro') + _tipico('crítica'), abs=1e-3)
    assert orc.reserva('garimpo') == pytest.approx(_tipico('roteiro') + _tipico('crítica'), abs=1e-3)
    assert orc.reserva('roteiro') == pytest.approx(_tipico('crítica'), abs=1e-3)
    assert orc.reserva('crítica') == 0 and orc.reserva('pesquisa') == pytest.approx(_tipico('roteiro') + _tipico('crítica'), abs=1e-3)
    assert orc.reserva('ganchos') == pytest.approx(_tipico('tema') + _tipico('garimpo') + _tipico('roteiro') + _tipico('crítica'), abs=1e-3)


def test_reserva_desconta_o_que_ja_rodou_na_tentativa(monkeypatch):
    _falso(monkeypatch, [(0.05, True, 900)] * 3)
    orc.abrir('teste')
    custo.tentativa('A')
    _pedir('garimpo')
    _pedir('roteiro')
    _pedir('crítica')
    assert orc.reserva('ganchos') == 0                           # todas as essenciais já rodaram nesta tentativa
    custo.tentativa('B')                                         # tema novo: as essenciais voltam para a reserva
    assert orc.reserva('ganchos') > 0.2


def test_decisoes_com_reserva():
    # essencial: chama se pior + reserva cabem no teto; senão pediria autorização
    assert orc.decidir('roteiro', 0.10, 0.05, 0.10, 0.30, 0.24) == 'chamar (acima do alvo)'
    assert orc.decidir('roteiro', 0.08, 0.05, 0.10, 0.30, 0.24) == 'chamar'
    assert orc.decidir('roteiro', 0.10, 0.15, 0.10, 0.30, 0.24) == 'pedir autorização'   # reserva não caberia
    assert orc.decidir('crítica', 0.10, 0.25, 0.0, 0.30, 0.24) == 'pedir autorização'
    # ganchos é opcional: só se tudo couber no alvo
    assert orc.decidir('ganchos', 0.03, 0.10, 0.0, 0.30, 0.24) == 'chamar'
    assert orc.decidir('ganchos', 0.03, 0.22, 0.0, 0.30, 0.24) == 'pular'
    assert orc.decidir('ganchos', 0.03, 0.10, 0.12, 0.30, 0.24) == 'pular'               # reservando as essenciais


# ───────── 5. parâmetros (só calculados, nunca passados) ─────────
def test_parametros_de_limite():
    assert orc.parametros('roteiro', 0.10, 0.30) == {'max_budget_usd': 0.2, 'max_output_tokens': 8400}
    assert orc.parametros('ganchos', 0.0, 0.30)['max_output_tokens'] == 1500
    assert orc.parametros('etapa-nova', 0.0, 0.30)['max_output_tokens'] == orc.SAIDA_PADRAO
    assert orc.parametros('roteiro', 0.45, 0.30)['max_budget_usd'] == 0.01               # nunca zero nem negativo


@pytest.mark.parametrize('modo', [None, 'monitorar', 'aplicar'])
def test_parametros_nao_sao_passados_ao_claude(monkeypatch, modo):
    if modo:
        monkeypatch.setenv('ORCAMENTO_MODO', modo)
    ch = _falso(monkeypatch, [(0.05, True, 900)])
    orc.abrir('teste')
    _pedir('roteiro')
    c = ch[0]
    assert '--max-budget-usd' not in c['cmd'] and 'CLAUDE_CODE_MAX_OUTPUT_TOKENS' not in c['env']
    assert c['cmd'] == ['claude', '-p', '--model', claude.MODELO, '--output-format', 'json', '--max-turns', '1',
                        '--append-system-prompt', claude.SISTEMA, '--disallowedTools', claude.SEM_FERRAMENTAS]
    ev = orc.resumo()['eventos'][0]
    assert ev['parametros'] == {'max_budget_usd': 0.3, 'max_output_tokens': 8400}         # calculado e registrado
    assert orc.modo() == 'monitorar'                                                      # "aplicar" não liga


# ───────── 6. NTC isolado ─────────
def test_sem_orcamento_aberto_nada_acontece(monkeypatch, capsys):
    ch = _falso(monkeypatch, [(0.05, True, 900)])
    assert claude.pedir('fábula da Valdirene') == 'RESPOSTA OK'
    assert '[orçamento]' not in capsys.readouterr().out and orc.resumo()['eventos'] == []
    assert len(custo.LIVRO) == 1 and len(ch) == 1                # o livro-caixa da Fase 0 continua contando


def test_video_do_coringa_nao_vaza_para_o_ntc(monkeypatch, capsys, tmp_path):
    _falso(monkeypatch, [(0.05, True, 900)] * 2)
    monkeypatch.setattr(main, '_fazer_curiosidade', lambda *a, **k: _pedir('roteiro') and True)
    main.fazer_curiosidade('tema', 1, tmp_path)
    assert '[orçamento]' in capsys.readouterr().out
    claude.pedir('cena do NTC')                                   # depois do vídeo: orçamento já fechado
    assert '[orçamento]' not in capsys.readouterr().out


def test_codigo_do_ntc_nao_usa_o_orcamento():
    arquivos = [p for p in (RAIZ / 'src').glob('*.py') if re.match(r'(fabula|ntc)', p.name)]
    assert arquivos
    for p in arquivos:
        assert 'orcamento_video' not in p.read_text(encoding='utf-8'), p.name
    fonte = (RAIZ / 'main.py').read_text(encoding='utf-8')
    ramo_ntc = fonte[fonte.index('if a.fabula is not None:'):fonte.index('if a.diario:')]
    assert 'orcamento_video' not in ramo_ntc


def test_erro_no_orcamento_nunca_derruba_a_chamada(monkeypatch):
    _falso(monkeypatch, [(0.05, True, 900)])
    orc.abrir('teste')
    monkeypatch.setattr(orc, 'pior_caso', lambda *a, **k: 1 / 0)
    assert _pedir('roteiro') == 'RESPOSTA OK'
