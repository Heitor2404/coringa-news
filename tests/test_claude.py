"""Claude como escritor principal — com um `claude` FALSO no PATH (nenhum pedido real, nenhum crédito gasto)."""
import json
import os
import stat
from pathlib import Path

import pytest


def _claude_falso(tmp_path: Path, monkeypatch, resposta: dict | None = None, codigo: int = 0, saida_txt: str | None = None):
    """Cria um executável `claude` que grava os argumentos/ambiente e responde como o Claude Code em --output-format json."""
    log = tmp_path / 'chamadas.jsonl'
    corpo = saida_txt if saida_txt is not None else json.dumps(resposta or {})
    script = tmp_path / 'bin' / 'claude'
    script.parent.mkdir()
    script.write_text(f'''#!/usr/bin/env python3
import json, os, sys
entrada = sys.stdin.read()
with open({str(log)!r}, 'a') as f:
    f.write(json.dumps({{'args': sys.argv[1:], 'entrada': entrada, 'api_key': os.getenv('ANTHROPIC_API_KEY'),
                        'cwd': os.getcwd()}}) + '\\n')
sys.stdout.write({corpo!r})
sys.exit({codigo})
''')
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv('PATH', f"{script.parent}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_TOKEN', 'sk-ant-oat01-teste')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'nao-deve-ir')
    from src import claude
    monkeypatch.setattr(claude, '_falhas', 0)
    claude.GASTO.update(usd=0.0, pedidos=0)
    return claude, log


def _chamadas(log: Path) -> list[dict]:
    return [json.loads(l) for l in log.read_text().splitlines()]


def test_roteiro_vai_para_o_sonnet_e_tarefa_simples_para_o_haiku(tmp_path, monkeypatch):
    claude, log = _claude_falso(tmp_path, monkeypatch, {'type': 'result', 'result': 'olá', 'total_cost_usd': 0.02})
    assert claude.pedir('escreva o roteiro') == 'olá'
    assert claude.pedir('escolha o tema', leve=True) == 'olá'
    a, b = _chamadas(log)
    assert a['args'][a['args'].index('--model') + 1] == 'sonnet' and b['args'][b['args'].index('--model') + 1] == 'haiku'
    assert a['entrada'] == 'escreva o roteiro'                    # prompt vai pela entrada (sem limite de tamanho)
    assert claude.GASTO == {'usd': pytest.approx(0.04), 'pedidos': 2}


def test_cobranca_vai_para_a_assinatura_nao_para_api(tmp_path, monkeypatch):
    claude, log = _claude_falso(tmp_path, monkeypatch, {'type': 'result', 'result': 'ok'})
    claude.pedir('x')
    c = _chamadas(log)[0]
    assert c['api_key'] is None                                   # ANTHROPIC_API_KEY teria prioridade e cobraria à parte
    raiz = Path(__file__).resolve().parents[1]
    assert raiz not in Path(c['cwd']).resolve().parents and Path(c['cwd']).resolve() != raiz   # não roda no repositório


def test_erro_do_claude_vira_excecao_e_desliga_depois_de_2(tmp_path, monkeypatch):
    claude, _ = _claude_falso(tmp_path, monkeypatch, {'type': 'result', 'is_error': True, 'result': 'Credit balance too low'})
    for _ in range(2):
        with pytest.raises(RuntimeError, match='Credit balance'):
            claude.pedir('x')
    assert not claude.disponivel()


def test_saida_que_nao_e_json(tmp_path, monkeypatch):
    claude, _ = _claude_falso(tmp_path, monkeypatch, codigo=1, saida_txt='Invalid API key · Please run /login')
    with pytest.raises(RuntimeError, match='login'):
        claude.pedir('x')


def test_sem_token_nao_usa_claude(monkeypatch):
    from src import claude
    monkeypatch.delenv('CLAUDE_CODE_OAUTH_TOKEN', raising=False)
    assert not claude.disponivel()


def test_cascata_usa_o_claude_antes_do_gemini(tmp_path, monkeypatch):
    claude, _ = _claude_falso(tmp_path, monkeypatch, {'type': 'result', 'result': '```json\n{"cenas": [1, 2]}\n```'})
    from src import gemini
    def gemini_nao(*a, **k):
        raise AssertionError('não devia chamar o Gemini')
    monkeypatch.setattr(gemini, '_tentar', gemini_nao)
    assert gemini._em_cascata(lambda m: None, 'p', True, leve=False) == {'cenas': [1, 2]}


def test_claude_falhou_segue_com_o_gemini(tmp_path, monkeypatch):
    claude, _ = _claude_falso(tmp_path, monkeypatch, codigo=1, saida_txt='erro')
    from src import gemini
    gemini.RESERVAS_USADAS.clear()
    monkeypatch.setattr(gemini, '_tentar', lambda f, modelos=None: {'veio': 'gemini'})
    assert gemini._em_cascata(lambda m: None, 'p', True, leve=False) == {'veio': 'gemini'}
    assert gemini.RESERVAS_USADAS == []                           # Gemini principal não é "modelo reserva"


def test_token_colado_com_quebra_de_linha_funciona(tmp_path, monkeypatch):
    claude, log = _claude_falso(tmp_path, monkeypatch, {'type': 'result', 'result': 'ok'})
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_TOKEN', 'sk-ant-oat01-abc\r\ndef  ')
    env = claude._ambiente()
    assert env['CLAUDE_CODE_OAUTH_TOKEN'] == 'sk-ant-oat01-abcdef'
