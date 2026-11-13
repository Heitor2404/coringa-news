"""CLAUDE como escritor principal (roteiro, revisão, ganchos, plano de imagens, fatos, tema).

Usa a assinatura Claude Pro do Heitor pelo Claude Code (`claude -p`), que tem um crédito mensal próprio para uso
automático (GitHub Actions) — separado do limite do chat. Autenticação: secret CLAUDE_CODE_OAUTH_TOKEN, gerado uma vez
com `claude setup-token` (vale ~1 ano). NUNCA usar ANTHROPIC_API_KEY junto (ela teria prioridade e cobraria à parte).

Tarefa de qualidade → Sonnet; tarefa simples (leve=True) → Haiku. Se o Claude falhar, quem chamou segue para o Gemini.
"""
import contextvars
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from . import custo

MODELO = os.getenv('CLAUDE_MODELO') or 'sonnet'
MODELO_LEVE = os.getenv('CLAUDE_MODELO_LEVE') or 'haiku'
TEMPO_MAX = 300                      # segundos por pedido
FALHAS_PARA_DESLIGAR = 2             # falhou 2x seguidas nesta execução: para de tentar (sem crédito, fora do ar...)
SISTEMA = ('Você é um redator de roteiros de vídeos curtos em português do Brasil. Responda SOMENTE ao pedido, '
           'no formato pedido (JSON quando pedirem JSON), sem comentários antes ou depois. Não use ferramentas.')
SEM_FERRAMENTAS = 'Bash,Edit,Write,Read,Glob,Grep,WebFetch,WebSearch,Task,NotebookEdit,TodoWrite'

_falhas = 0
GASTO = {'usd': 0.0, 'pedidos': 0}

# ───────── Fase 1 · M1 e M2 (12/11): interruptores, DESLIGADOS por padrão ─────────
# M1: DESCARTADA em 12/11 (ver m1_ligado); o código do `--system-prompt` fica só para referência.
# M2 (FATOS_NO_SISTEMA=1): os fatos que vão no pedido saem do meio do pedido e vão, IDÊNTICOS, para o prompt de sistema,
#   onde o cache do Claude é reaproveitado entre roteiro, crítica e ganchos (quando o trecho de fatos é o mesmo). O lugar
#   onde estavam vira um aviso de onde estão. Só acontece se o trecho aparece UMA vez no pedido; senão nada muda. O
#   Gemini (quando o Claude falha) recebe o pedido original, com os fatos no lugar de sempre. Sem M1, M2 liga
#   `--exclude-dynamic-system-prompt-sections` (tira pasta/ambiente, que mudam a cada chamada, do sistema).
MARCA_FATOS = '[os FATOS PESQUISADOS estão nas instruções do sistema, no bloco "FATOS PESQUISADOS"; use-os aqui]'
_fatos_ctx = contextvars.ContextVar('fatos_compartilhados', default=None)


def _no_coringa() -> bool:
    """M1 e M2 só valem dentro do orçamento de um vídeo do Coringa: o NTC (sem orçamento aberto) nunca muda."""
    try:
        from . import orcamento_video
        return orcamento_video.aberto()
    except Exception:
        return False


def m1_ligado() -> bool:
    """M1 DESCARTADA (12/11, Torre Eiffel 3): o Claude Code continua mandando ~6,4 mil tokens de base mesmo com
    --system-prompt próprio, então ela quase não economiza e muda o prompt-base. Ignora CLAUDE_SISTEMA_PROPRIO."""
    return False


def m2_ligado() -> bool:
    return os.getenv('FATOS_NO_SISTEMA', '0') == '1' and _no_coringa()


@contextmanager
def fatos_compartilhados(texto: str | None):
    """`with claude.fatos_compartilhados(trecho):` declara o trecho EXATO de fatos que o próximo pedido leva."""
    tok = _fatos_ctx.set(str(texto) if texto else None)
    try:
        yield
    finally:
        _fatos_ctx.reset(tok)


def montar(prompt: str, modelo: str) -> tuple[list, str, str]:
    """Comando, pedido e sistema que vão ao `claude -p`. Com M1 e M2 desligados: exatamente como antes da Fase 1."""
    sistema = SISTEMA
    trecho = _fatos_ctx.get()
    if m2_ligado() and trecho and trecho.strip() and prompt.count(trecho) == 1:
        prompt = prompt.replace(trecho, MARCA_FATOS, 1)
        sistema = SISTEMA + '\n\nFATOS PESQUISADOS (a única fonte de fatos do pedido):\n' + trecho
    if m1_ligado():
        flags = ['--system-prompt', sistema]
    else:
        flags = ['--append-system-prompt', sistema] + (['--exclude-dynamic-system-prompt-sections'] if sistema != SISTEMA else [])
    cmd = ['claude', '-p', '--model', modelo, '--output-format', 'json', '--max-turns', '1', *flags,
           '--disallowedTools', SEM_FERRAMENTAS]
    return cmd, prompt, sistema


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
    cmd, prompt, sistema = montar(prompt, modelo)
    # Fase 1 (12/11): o orçamento do vídeo só CALCULA o pior caso e o que faria; o comando acima não muda
    from . import orcamento_video
    dec = orcamento_video.antes(prompt, modelo, sistema=sistema)
    try:
        return _executar(cmd, prompt, modelo)
    finally:
        orcamento_video.depois(dec)


def _executar(cmd: list, prompt: str, modelo: str) -> str:
    global _falhas
    t0 = time.time()
    with tempfile.TemporaryDirectory() as vazio:   # pasta vazia: o Claude Code não enxerga o repositório
        try:
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=TEMPO_MAX,
                               cwd=vazio, env=_ambiente())
        except subprocess.TimeoutExpired:
            _falhas += 1
            custo.registrar('claude', modelo, 0, None, time.time() - t0, ok=False)
            raise RuntimeError(f'Claude ({modelo}) não respondeu em {TEMPO_MAX}s')
    try:
        saida = json.loads(r.stdout)
    except (json.JSONDecodeError, TypeError):
        _falhas += 1
        custo.registrar('claude', modelo, 0, None, time.time() - t0, ok=False)
        raise RuntimeError(f'Claude ({modelo}) saiu com código {r.returncode}: {(r.stderr or r.stdout)[:200]}')
    if isinstance(saida, list):                   # algumas versões devolvem a lista de eventos
        saida = next((x for x in reversed(saida) if isinstance(x, dict) and x.get('type') == 'result'), {})
    usd = float(saida.get('total_cost_usd') or 0)
    if saida.get('is_error') or not str(saida.get('result') or '').strip():
        _falhas += 1
        custo.registrar('claude', modelo, usd, saida.get('usage'), time.time() - t0, ok=False)   # falha também gasta
        GASTO['usd'] += usd
        raise RuntimeError(f"Claude ({modelo}): {str(saida.get('result') or saida.get('subtype') or saida)[:200]}")
    _falhas = 0
    GASTO['usd'] += usd
    GASTO['pedidos'] += 1
    custo.registrar('claude', modelo, usd, saida.get('usage'), time.time() - t0)
    guardar_bruta(str(saida['result']))
    return str(saida['result'])


PASTA_BRUTAS = Path(__file__).resolve().parents[1] / 'saida' / 'respostas_ia'


def guardar_bruta(texto: str):
    """13/11 (polvo): a resposta paga que dá erro de leitura era perdida e não dava para saber o que veio. Guarda o texto
    bruto de cada pedido do Coringa (vai para o pacote PRIVADO da rodada, nunca para o repositório). NTC: não guarda."""
    try:
        if not _no_coringa():
            return
        PASTA_BRUTAS.mkdir(parents=True, exist_ok=True)
        n = len(list(PASTA_BRUTAS.glob('*.txt'))) + 1
        etapa = re.sub(r'[^a-z0-9]+', '-', str((custo.LIVRO[-1] if custo.LIVRO else {}).get('etapa') or 'pedido').lower())
        (PASTA_BRUTAS / f'{n:02d}-{etapa}.txt').write_text(texto, encoding='utf-8')
    except Exception as e:
        print(f'  [claude] não guardei a resposta bruta ({str(e)[:60]})')


def resumo_gasto() -> str:
    return f"{GASTO['pedidos']} pedido(s) ao Claude · ~US$ {GASTO['usd']:.2f} do crédito mensal"
