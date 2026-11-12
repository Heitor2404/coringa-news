"""Fase 1, etapa 2 (12/11/2026): M1 e M2 (interruptores, desligados por padrão), escolha das notícias no orçamento do
LOTE (rateada, sem contar duas vezes) e versão fixa do Claude Code. Tudo com respostas simuladas: nenhuma chamada real.
Cache · compatibilidade · contabilização · isolamento do NTC."""
import json
import sys
import types
from pathlib import Path

import pytest
import yaml

import main
from src import claude, custo, gemini, orcamento_video as orc, roteiro

RAIZ = Path(__file__).resolve().parent.parent
FATOS_CURTOS = 'FATOS (★ = mais surpreendentes):\n' + '\n'.join(f'- ★ fato {k}: Lustig vendeu a torre em 1925' for k in range(80))
FATOS_LONGOS = FATOS_CURTOS + '\n' + '\n'.join(f'- fato extra {k}: ' + 'x' * 120 for k in range(80))   # > 14 mil


@pytest.fixture(autouse=True)
def limpo(monkeypatch):
    custo.zerar()
    orc._ORC.clear(); orc._ORC['aberto'] = False
    orc._LOTE.clear(); orc._LOTE['aberto'] = False
    for k in ('ORCAMENTO_MODO', 'CLAUDE_SISTEMA_PROPRIO', 'FATOS_NO_SISTEMA'):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(claude, '_falhas', 0)
    yield
    custo.zerar()
    orc._ORC.clear(); orc._ORC['aberto'] = False
    orc._LOTE.clear(); orc._LOTE['aberto'] = False


def _falso(monkeypatch, respostas=None, resultado='{"ok": true}'):
    chamadas = []
    fila = list(respostas or [])

    def run(cmd, input=None, capture_output=None, text=None, timeout=None, cwd=None, env=None):
        chamadas.append({'cmd': list(cmd), 'input': input, 'env': dict(env or {})})
        usd, lido, escrito = fila.pop(0) if fila else (0.05, 7025, 10000)
        r = {'type': 'result', 'result': resultado, 'total_cost_usd': usd,
             'usage': {'input_tokens': 2, 'cache_creation_input_tokens': escrito, 'cache_read_input_tokens': lido,
                       'output_tokens': 800}}
        return types.SimpleNamespace(stdout=json.dumps(r), stderr='', returncode=0)
    monkeypatch.setattr(claude.subprocess, 'run', run)
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_TOKEN', 'tok')
    return chamadas


def _sistema(cmd):
    for f in ('--system-prompt', '--append-system-prompt'):
        if f in cmd:
            return f, cmd[cmd.index(f) + 1]
    return None, None


ANTES = lambda modelo: ['claude', '-p', '--model', modelo, '--output-format', 'json', '--max-turns', '1',
                        '--append-system-prompt', claude.SISTEMA, '--disallowedTools', claude.SEM_FERRAMENTAS]


# ───────── compatibilidade ─────────
def test_desligadas_por_padrao_o_comando_e_o_de_antes(monkeypatch):
    ch = _falso(monkeypatch)
    orc.abrir('v')
    with claude.fatos_compartilhados(FATOS_CURTOS):
        claude.pedir(f'REGRAS\n{FATOS_CURTOS}\nESCREVA')
    assert ch[0]['cmd'] == ANTES(claude.MODELO) and ch[0]['input'] == f'REGRAS\n{FATOS_CURTOS}\nESCREVA'


def test_m1_troca_so_o_prompt_de_sistema(monkeypatch):
    monkeypatch.setenv('CLAUDE_SISTEMA_PROPRIO', '1')
    ch = _falso(monkeypatch)
    orc.abrir('v')
    claude.pedir('PEDIDO')
    c = ch[0]['cmd']
    assert _sistema(c) == ('--system-prompt', claude.SISTEMA) and '--append-system-prompt' not in c
    assert '--exclude-dynamic-system-prompt-sections' not in c and ch[0]['input'] == 'PEDIDO'
    assert c[:8] == ANTES(claude.MODELO)[:8] and c[-2:] == ANTES(claude.MODELO)[-2:]


@pytest.mark.parametrize('m1', ['0', '1'])
def test_m2_move_os_fatos_identicos_para_o_sistema(monkeypatch, m1):
    monkeypatch.setenv('CLAUDE_SISTEMA_PROPRIO', m1)
    monkeypatch.setenv('FATOS_NO_SISTEMA', '1')
    ch = _falso(monkeypatch)
    orc.abrir('v')
    original = f'REGRAS DO ROTEIRO\nFATOS:\n{FATOS_CURTOS}\n\nESCREVA O JSON'
    with claude.fatos_compartilhados(FATOS_CURTOS):
        claude.pedir(original)
    c, pedido = ch[0]['cmd'], ch[0]['input']
    flag, sistema = _sistema(c)
    assert sistema.startswith(claude.SISTEMA) and sistema.endswith(FATOS_CURTOS)       # fatos idênticos, no sistema
    assert FATOS_CURTOS not in pedido and pedido.replace(claude.MARCA_FATOS, FATOS_CURTOS) == original
    assert flag == ('--system-prompt' if m1 == '1' else '--append-system-prompt')
    assert ('--exclude-dynamic-system-prompt-sections' in c) == (m1 == '0')


@pytest.mark.parametrize('pedido', ['SEM OS FATOS AQUI', f'{FATOS_CURTOS}\n---\n{FATOS_CURTOS}'])
def test_m2_nao_mexe_se_o_trecho_nao_aparece_uma_vez(monkeypatch, pedido):
    monkeypatch.setenv('FATOS_NO_SISTEMA', '1')
    ch = _falso(monkeypatch)
    orc.abrir('v')
    with claude.fatos_compartilhados(FATOS_CURTOS):
        claude.pedir(pedido)
    assert ch[0]['input'] == pedido and ch[0]['cmd'] == ANTES(claude.MODELO)


def test_gemini_reserva_recebe_o_pedido_original(monkeypatch):
    """Claude falhou: o Gemini recebe o pedido com os fatos no lugar de sempre (a M2 só existe no comando do Claude)."""
    monkeypatch.setenv('CLAUDE_SISTEMA_PROPRIO', '1')
    monkeypatch.setenv('FATOS_NO_SISTEMA', '1')
    monkeypatch.setattr(claude, 'disponivel', lambda: True)
    monkeypatch.setattr(claude.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(stdout='quebrado', stderr='', returncode=1))
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_TOKEN', 'tok')
    vistos = []
    class Modelos:
        def generate_content(self, model, contents, config=None):
            vistos.append(contents)
            return types.SimpleNamespace(text='{"ok": 1}')
    monkeypatch.setattr(gemini, 'cliente', lambda *a, **k: types.SimpleNamespace(models=Modelos()))
    monkeypatch.setattr(gemini, '_tentar', lambda f, modelos=None: f('g'))
    orc.abrir('v')
    original = f'X\n{FATOS_CURTOS}\nY'
    with claude.fatos_compartilhados(FATOS_CURTOS):
        assert gemini.json_(original) == {'ok': 1}
    assert vistos and vistos[0] == original


# ───────── os quatro pontos do roteiro declaram o MESMO trecho que já mandavam ─────────
def _capturar(monkeypatch):
    vistos = []
    def json_(prompt, leve=False):
        vistos.append((claude._fatos_ctx.get(), prompt))
        return {}
    monkeypatch.setattr(gemini, 'json_', json_)
    return vistos


@pytest.mark.parametrize('fatos', [FATOS_CURTOS, FATOS_LONGOS])
def test_critica_e_ganchos_declaram_o_trecho_que_ja_usavam(monkeypatch, fatos):
    vistos = _capturar(monkeypatch)
    v = {'titulo': 'T', 'cenas': [{'tipo': 'gancho', 'fala': 'Ele vendeu a torre'}, {'tipo': 'historia', 'fala': 'Lustig'}]}
    roteiro.revisar(v, fatos)
    roteiro.escolher_gancho(v, fatos)
    (ctx_c, p_c), (ctx_g, p_g) = vistos
    assert ctx_c == fatos[:14000] and p_c.count(ctx_c) == 1
    assert ctx_g == fatos[:9000] and p_g.count(ctx_g) == 1


def test_roteiro_noticia_declara_os_fatos(monkeypatch):
    vistos = []
    monkeypatch.setattr(roteiro, '_fatos', lambda pauta: FATOS_CURTOS)
    monkeypatch.setattr(roteiro, 'PROMPT_ROTEIRO', 'R {fatos} {produtos} {titulo}')
    monkeypatch.setattr(roteiro, '_melhor_de_dois', lambda prompt, **k: vistos.append((claude._fatos_ctx.get(), prompt))
                        or {'titulo': 't', 'cenas': [{'tipo': 'gancho', 'fala': 'a'}]})
    for f in ('revisar', 'escolher_gancho', 'arrumar_final', 'dividir', 'geocodificar'):
        monkeypatch.setattr(roteiro, f, lambda v, *a, **k: v)
    from src import orcamento
    monkeypatch.setattr(orcamento, 'marca', lambda *a, **k: None)
    roteiro.escrever({'titulo': 'P', 'resumo': '', 'fonte': '', 'link': ''}, [])
    assert vistos[0][0] == FATOS_CURTOS and vistos[0][1].count(FATOS_CURTOS) == 1


def test_sistema_identico_entre_chamadas_quando_o_trecho_e_o_mesmo(monkeypatch):
    """O que deixa o cache ser reaproveitado: roteiro, crítica e ganchos com o MESMO sistema (fatos curtos)."""
    monkeypatch.setenv('CLAUDE_SISTEMA_PROPRIO', '1')
    monkeypatch.setenv('FATOS_NO_SISTEMA', '1')
    ch = _falso(monkeypatch)
    orc.abrir('v')
    for fatos in (FATOS_CURTOS, FATOS_CURTOS[:14000], FATOS_CURTOS[:9000]):       # fatos < 9 mil: os 3 iguais
        with claude.fatos_compartilhados(fatos):
            claude.pedir(f'PEDIDO {len(ch)}\n{fatos}\nFIM')
    sis = [_sistema(c['cmd'])[1] for c in ch]
    assert len(FATOS_CURTOS) < 9000 and sis[0] == sis[1] == sis[2]
    ch.clear()
    for fatos in (FATOS_LONGOS, FATOS_LONGOS[:14000], FATOS_LONGOS[:9000]):       # fatos longos: trechos diferentes
        with claude.fatos_compartilhados(fatos):
            claude.pedir(f'PEDIDO\n{fatos}\nFIM')
    sis = [_sistema(c['cmd'])[1] for c in ch]
    assert len({sis[0], sis[1], sis[2]}) == 3                                    # sem cache, mas conteúdo intacto


# ───────── contabilização ─────────
def test_cache_lido_e_economias_aparecem_no_orcamento(monkeypatch):
    monkeypatch.setenv('CLAUDE_SISTEMA_PROPRIO', '1')
    monkeypatch.setenv('FATOS_NO_SISTEMA', '1')
    _falso(monkeypatch, [(0.09, 0, 13000), (0.06, 3500, 8000), (0.03, 3500, 6000)])  # 2ª e 3ª leem os fatos do cache
    orc.abrir('v')
    for et in ('roteiro', 'crítica', 'ganchos'):
        with custo.etapa(et), claude.fatos_compartilhados(FATOS_CURTOS):
            claude.pedir(f'PEDIDO\n{FATOS_CURTOS}\nFIM')
    r = orc.resumo()
    assert r['m1'] and r['m2'] and r['cache_lido_tokens'] == 7000 and r['gasto_usd'] == pytest.approx(0.18)
    assert [e['cache_lido_tokens'] for e in r['eventos']] == [0, 3500, 3500]
    assert 'economias ligadas: M1, M2 · cache lido 7000 tokens' in orc.linha_telegram()
    assert custo.claude_usd() == pytest.approx(0.18)                                # o livro-caixa conta o mesmo


def test_pior_caso_com_m1_nao_conta_o_prompt_base():
    com, sem = orc.pior_caso(10000, 'roteiro', 'sonnet', base_claude_code=True), orc.pior_caso(10000, 'roteiro', 'sonnet', base_claude_code=False)
    assert com - sem == pytest.approx(7025 * 0.30 / 1e6, abs=1e-4)


def test_pior_caso_nunca_conta_com_o_cache(monkeypatch):
    """Mesmo com M2, a estimativa cobra toda a entrada (sistema com fatos + pedido) como escrita: continua pior caso."""
    monkeypatch.setenv('FATOS_NO_SISTEMA', '1')
    _falso(monkeypatch)
    orc.abrir('v')
    with custo.etapa('roteiro'), claude.fatos_compartilhados(FATOS_CURTOS):
        claude.pedir(f'P\n{FATOS_CURTOS}\nF')
    e = orc.resumo()['eventos'][0]
    assert e['entrada_tokens_est'] >= orc.tokens(FATOS_CURTOS) + orc.tokens(claude.SISTEMA)


# ───────── lote de notícias ─────────
def test_escolha_rateada_entre_os_videos_sem_contar_duas_vezes(monkeypatch):
    _falso(monkeypatch, [(0.04, 7025, 5000), (0.10, 7025, 9000), (0.12, 7025, 9000)])
    orc.abrir_lote('notícias')
    with custo.etapa('pauta'):
        claude.pedir('escolha as notícias')
    orc.definir_rateio(2)
    gastos = []
    for k, et in enumerate(('roteiro', 'roteiro')):
        with orc.video(f'n{k}'):
            with custo.etapa(et):
                claude.pedir('roteiro')
            gastos.append(orc.gasto())
            assert orc.resumo()['rateio_lote_usd'] == pytest.approx(0.02)
    r = orc.fechar_lote()
    assert gastos == pytest.approx([0.12, 0.14])                                   # 0,10 + 0,02 e 0,12 + 0,02
    assert r['total_usd'] == pytest.approx(0.26) == pytest.approx(custo.claude_usd())
    assert sum(gastos) == pytest.approx(r['total_usd'])                            # nada contado duas vezes
    assert [v['proprio_usd'] for v in r['videos']] == pytest.approx([0.10, 0.12]) and r['escolha_sem_video_usd'] == pytest.approx(0)


def test_lote_sem_video_ou_com_noticia_que_falhou(monkeypatch):
    _falso(monkeypatch, [(0.04, 7025, 5000)])
    orc.abrir_lote('notícias')
    with custo.etapa('pauta'):
        claude.pedir('escolha')
    orc.definir_rateio(0)                                                          # nenhuma notícia passou do filtro
    r = orc.fechar_lote()
    assert r['total_usd'] == pytest.approx(0.04) and r['escolha_sem_video_usd'] == pytest.approx(0.04)
    _falso(monkeypatch, [(0.04, 7025, 5000), (0.03, 7025, 5000)])
    orc.abrir_lote('notícias')
    with custo.etapa('pauta'):
        claude.pedir('escolha')
    orc.definir_rateio(2)
    with pytest.raises(RuntimeError):
        with orc.video('n1'):
            with custo.etapa('roteiro'):
                claude.pedir('roteiro')
            raise RuntimeError('notícia falhou depois de gastar')
    r = orc.fechar_lote()                                                          # a 2ª notícia nem começou
    assert r['total_usd'] == pytest.approx(0.07) and r['escolha_sem_video_usd'] == pytest.approx(0.02)


def test_main_noticias_rateia_a_escolha_e_preserva_a_saida_antecipada(monkeypatch, tmp_path):
    _falso(monkeypatch, [(0.06, 7025, 5000)] + [(0.10, 7025, 9000)] * 3)
    from src import pautas
    monkeypatch.setattr(pautas, 'buscar', lambda: [{'titulo': f'N{k}', 'link': 'l', 'chave': f'c{k}'} for k in range(5)])
    monkeypatch.setattr(roteiro, 'escolher', lambda lista, n: claude.pedir('escolha') and lista[:n])
    monkeypatch.setattr(roteiro, 'escrever', lambda p, prods: {'titulo': p['titulo'], 'roteiro': claude.pedir('r')})
    monkeypatch.setattr(pautas, 'carregar_historico', lambda: {})
    monkeypatch.setattr(pautas, 'salvar_historico', lambda h: None)
    monkeypatch.setattr(main, 'produtos', lambda: [])
    monkeypatch.setattr(main, 'montar_video', lambda v, pasta, nome, teste=False: (pasta / f'{nome}.txt').write_text('t') or pasta / f'{nome}.mp4')
    monkeypatch.setattr(main, 'telegram', lambda *a, **k: None)
    monkeypatch.setattr(main, 'RAIZ', tmp_path)                                    # saída do teste fica no tmp
    monkeypatch.setattr(sys, 'argv', ['main.py', '--qtd', '3'])
    main.main()
    r = orc._LOTE['resumo']
    assert r['escolha_usd'] == pytest.approx(0.06) and r['n_videos_previstos'] == 3 and r['rateio_usd'] == pytest.approx(0.02)
    assert len(r['videos']) == 3 and r['total_usd'] == pytest.approx(0.36) == pytest.approx(custo.claude_usd())
    # --tema sem notícia: sai antes, como antes (não roda as curiosidades extras)
    chamou = []
    monkeypatch.setattr(pautas, 'buscar_tema', lambda t: [])
    monkeypatch.setattr(main, 'fazer_curiosidade', lambda *a, **k: chamou.append(a))
    monkeypatch.setattr(sys, 'argv', ['main.py', '--tema', 'nada', '--explica', '1'])
    main.main()
    assert chamou == [] and not orc._LOTE['aberto']


# ───────── NTC isolado ─────────
def test_fora_do_coringa_m1_m2_nao_valem(monkeypatch, capsys):
    monkeypatch.setenv('CLAUDE_SISTEMA_PROPRIO', '1')
    monkeypatch.setenv('FATOS_NO_SISTEMA', '1')
    ch = _falso(monkeypatch)
    with claude.fatos_compartilhados(FATOS_CURTOS):                                # nem com fatos declarados
        claude.pedir(f'cena da Valdirene\n{FATOS_CURTOS}')
    assert ch[0]['cmd'] == ANTES(claude.MODELO) and FATOS_CURTOS in ch[0]['input']
    assert '[orçamento]' not in capsys.readouterr().out and not orc._ORC.get('eventos')


def test_ramo_do_ntc_no_main_nao_abre_orcamento_nem_lote(monkeypatch, tmp_path):
    monkeypatch.setenv('CLAUDE_SISTEMA_PROPRIO', '1')
    monkeypatch.setenv('FATOS_NO_SISTEMA', '1')
    ch = _falso(monkeypatch)
    from src import fabula
    monkeypatch.setattr(fabula, 'fazer', lambda tema: claude.pedir('fábula'))
    monkeypatch.setattr(main, 'RAIZ', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['main.py', '--fabula', 'tema'])
    main.main()
    assert ch[0]['cmd'] == ANTES(claude.MODELO) and not orc.aberto() and not orc._LOTE.get('aberto')
    for p in (RAIZ / 'src').glob('*.py'):
        if p.name.startswith(('fabula', 'ntc')):
            t = p.read_text(encoding='utf-8')
            assert 'orcamento_video' not in t and 'fatos_compartilhados' not in t, p.name


# ───────── versão fixa do Claude Code ─────────
def test_versao_do_claude_code_fixa_nos_workflows():
    for nome in ('gerar-videos.yml', 'testar-claude.yml'):
        t = (RAIZ / '.github/workflows' / nome).read_text(encoding='utf-8')
        assert '@anthropic-ai/claude-code@2.1.322' in t
        assert 'npm install -g @anthropic-ai/claude-code ' not in t                 # nenhuma instalação sem versão
    wf = yaml.safe_load((RAIZ / '.github/workflows/gerar-videos.yml').read_text(encoding='utf-8'))
    env = next(p for p in wf['jobs']['gerar']['steps'] if p.get('name') == 'Gerar vídeos')['env']
    assert {'CLAUDE_SISTEMA_PROPRIO', 'FATOS_NO_SISTEMA', 'ORCAMENTO_MODO'} <= set(env)
