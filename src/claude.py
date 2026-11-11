"""CLAUDE como escritor principal (roteiro, revisão, ganchos, plano de imagens, fatos, tema).

Usa a assinatura Claude Pro do Heitor pelo Claude Code (`claude -p`), que tem um crédito mensal próprio para uso
automático (GitHub Actions) — separado do limite do chat. Autenticação: secret CLAUDE_CODE_OAUTH_TOKEN, gerado uma vez
com `claude setup-token` (vale ~1 ano). NUNCA usar ANTHROPIC_API_KEY junto (ela teria prioridade e cobraria à parte).

Tarefa de qualidade → Sonnet; tarefa simples (leve=True) → Haiku. Se o Claude falhar, quem chamou segue para o Gemini.
"""
import json
import os
import shutil
import subprocess
import tempfile

MODELO = os.getenv('CLAUDE_MODELO') or 'sonnet'
MODELO_LEVE = os.getenv('CLAUDE_MODELO_LEVE') or 'haiku'
TEMPO_MAX = 300                      # segundos por pedido
FALHAS_PARA_DESLIGAR = 2             # falhou 2x seguidas nesta execução: para de tentar (sem crédito, fora do ar...)
SISTEMA = ('Você é um redator de roteiros de vídeos curtos em português do Brasil. Responda SOMENTE ao pedido, '
           'no formato pedido (JSON quando pedirem JSON), sem comentários antes ou depois. Não use ferramentas.')
SEM_FERRAMENTAS = 'Bash,Edit,Write,Read,Glob,Grep,WebFetch,WebSearch,Task,NotebookEdit,TodoWrite'

_falhas = 0
GASTO = {'usd': 0.0, 'pedidos': 0}


def disponivel() -> bool:
    if os.getenv('USAR_CLAUDE', '1') == '0' or _falhas >= FALHAS_PARA_DESLIGAR:
        return False
    return bool(os.getenv('CLAUDE_CODE_OAUTH_TOKEN')) and bool(shutil.which('claude'))


def _ambiente() -> dict:
    env = dict(os.environ)
    env.pop('ANTHROPIC_API_KEY', None)            # garante que a conta é a da assinatura, não cobrança por token
    # o PowerShell quebra o token em 2 linhas ao copiar; com a quebra o Claude recusa ("contains a line break", 10/11)
    env['CLAUDE_CODE_OAUTH_TOKEN'] = ''.join(str(env.get('CLAUDE_CODE_OAUTH_TOKEN') or '').split())
    env['DISABLE_AUTOUPDATER'] = '1'
    return env


def pedir(prompt: str, leve: bool = False) -> str:
    """Manda o pedido ao Claude e devolve o texto da resposta. Levanta RuntimeError se não deu certo."""
    global _falhas
    modelo = MODELO_LEVE if leve else MODELO
    cmd = ['claude', '-p', '--model', modelo, '--output-format', 'json', '--max-turns', '1',
           '--append-system-prompt', SISTEMA, '--disallowedTools', SEM_FERRAMENTAS]
    with tempfile.TemporaryDirectory() as vazio:   # pasta vazia: o Claude Code não enxerga o repositório
        try:
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=TEMPO_MAX,
                               cwd=vazio, env=_ambiente())
        except subprocess.TimeoutExpired:
            _falhas += 1
            raise RuntimeError(f'Claude ({modelo}) não respondeu em {TEMPO_MAX}s')
    try:
        saida = json.loads(r.stdout)
    except (json.JSONDecodeError, TypeError):
        _falhas += 1
        raise RuntimeError(f'Claude ({modelo}) saiu com código {r.returncode}: {(r.stderr or r.stdout)[:200]}')
    if isinstance(saida, list):                   # algumas versões devolvem a lista de eventos
        saida = next((x for x in reversed(saida) if isinstance(x, dict) and x.get('type') == 'result'), {})
    if saida.get('is_error') or not str(saida.get('result') or '').strip():
        _falhas += 1
        raise RuntimeError(f"Claude ({modelo}): {str(saida.get('result') or saida.get('subtype') or saida)[:200]}")
    _falhas = 0
    GASTO['usd'] += float(saida.get('total_cost_usd') or 0)
    GASTO['pedidos'] += 1
    return str(saida['result'])


def resumo_gasto() -> str:
    return f"{GASTO['pedidos']} pedido(s) ao Claude · ~US$ {GASTO['usd']:.2f} do crédito mensal"
