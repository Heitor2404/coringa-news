"""LIVRO-CAIXA COM TRAVA (Plano Mestre §5). Protege dinheiro real; não é o antigo `orcamento_video` (que só monitora o
equivalente do Claude Code e "não bloqueia").

Três métricas separadas, nunca somadas entre si:
  cobrado_usd  — cobrança efetiva em dinheiro (provedor pago);
  credito_usd  — consumo equivalente de assinatura/créditos (ex.: Claude Code com OAuth: cobrança 0);
  cota         — unidades de cota gratuita (pedidos ao Gemini grátis, Groq...).

Regras (valem só com um caixa ABERTO; fora dele, `antes()` devolve None e nada muda):
  * provedor desconhecido ou de faturamento não confirmado → NEGADO;
  * provedor pago sem ratificação humana do teto (CAIXA_RATIFICADO=humano:<nome>:<AAAA-MM-DD>) → NEGADO;
  * estimativa de pior caso desconhecida (None) numa operação paga → NEGADO;
  * cobrado + reservado + pior caso + futuros obrigatórios > teto → NEGADO (pede autorização; não degrada);
  * limites de tentativas por etapa, de chamadas no total e de tempo de execução → NEGADO;
  * duas execuções do mesmo vídeo ao mesmo tempo → a segunda não abre (trava de arquivo).
Tudo é persistido a cada operação (falha também conta), então um retry/job novo continua do total já gasto.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path

TETO_USD = float(os.getenv('CAIXA_TETO_USD') or 0.80)        # proposta provisória (não ratificada pelo proprietário)
ALERTA_USD = float(os.getenv('CAIXA_ALERTA_USD') or 0.60)
MAX_POR_ETAPA = int(os.getenv('CAIXA_MAX_POR_ETAPA') or 4)    # tentativas PAGAS por etapa
MAX_CHAMADAS = int(os.getenv('CAIXA_MAX_CHAMADAS') or 200)    # todas as chamadas (inclusive grátis)
MAX_SEGUNDOS = float(os.getenv('CAIXA_MAX_SEGUNDOS') or 5400)

# Faturamento declarado de cada provedor usado hoje. 'assinatura' e 'cota' não geram cobrança em dinheiro pelo que está
# configurado (OAuth da assinatura; chaves do plano grátis). 'confirmar' = pode cobrar dependendo do plano da conta:
# tratado como pago até alguém confirmar. Qualquer provedor fora daqui é desconhecido → negado.
PROVEDORES = {
    'claude_code': {'faturamento': 'assinatura', 'nota': 'CLI com CLAUDE_CODE_OAUTH_TOKEN; ANTHROPIC_API_KEY removida do ambiente'},
    'gemini': {'faturamento': 'cota', 'nota': 'chaves do plano grátis (texto, visão e TTS); se a conta ganhar faturamento, mudar para pago'},
    'groq': {'faturamento': 'cota', 'nota': 'plano grátis'},
    'pollinations': {'faturamento': 'cota', 'nota': 'serviço grátis sem conta'},
    'gemini_imagem': {'faturamento': 'confirmar', 'nota': 'geração de imagem do Gemini: em geral fora do plano grátis'},
    'cloudflare': {'faturamento': 'confirmar', 'nota': 'Workers AI: alocação diária grátis; conta paga cobra além dela'},
}
_HUMANO = re.compile(r'^humano:[^:]+:\d{4}-\d{2}-\d{2}$')


class OperacaoNegada(RuntimeError):
    """A trava recusou a operação. A mensagem diz o motivo e o que precisa de autorização."""


class CaixaOcupado(RuntimeError):
    """Outra execução já está com o caixa deste vídeo aberto."""


_ATUAL: dict = {}


def _provedores() -> dict:
    extra = os.getenv('CAIXA_PROVEDORES')            # ex.: '{"cloudflare": {"faturamento": "pago"}}'
    p = {k: dict(v) for k, v in PROVEDORES.items()}
    if extra:
        for k, v in json.loads(extra).items():
            p.setdefault(k, {}).update(v)
    return p


def faturamento(provedor: str) -> str:
    return (_provedores().get(provedor) or {}).get('faturamento', 'desconhecido')


def ratificado() -> bool:
    return bool(_HUMANO.match(os.getenv('CAIXA_RATIFICADO') or ''))


def _salvar(c: dict) -> None:
    tmp = c['arq'].with_suffix('.tmp')
    tmp.write_text(json.dumps({k: v for k, v in c.items() if k not in ('arq', '_fd')}, ensure_ascii=False, indent=1),
                   encoding='utf-8')
    tmp.replace(c['arq'])


def abrir(video: str, pasta: Path, teto: float | None = None, alerta: float | None = None) -> dict:
    """Abre (ou retoma) o caixa do vídeo. Retoma o total persistido de execuções anteriores do mesmo vídeo."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = re.sub(r'[^a-z0-9_-]+', '-', video.lower())[:60] or 'video'
    arq = pasta / f'caixa_{nome}.json'
    fd = os.open(str(arq.with_suffix('.lock')), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise CaixaOcupado(f'outra execução está gastando o orçamento de "{video}"')
    c = json.loads(arq.read_text(encoding='utf-8')) if arq.exists() else {
        'video': video, 'cobrado_usd': 0.0, 'credito_usd': 0.0, 'cota': {}, 'operacoes': [], 'negadas': [],
        'por_etapa': {}, 'chamadas': 0, 'segundos': 0.0, 'execucoes': 0}
    c.update(arq=arq, _fd=fd, teto=TETO_USD if teto is None else teto, alerta=ALERTA_USD if alerta is None else alerta,
             reservado=0.0, inicio=time.time(), ratificado=ratificado())
    c['execucoes'] += 1
    _ATUAL.clear()
    _ATUAL.update(c)
    _salvar(_ATUAL)
    return _ATUAL


def fechar() -> dict | None:
    if not _ATUAL:
        return None
    c = _ATUAL
    c['segundos'] = round(c['segundos'] + time.time() - c.pop('inicio'), 1)
    c['reservado'] = 0.0
    _salvar(c)
    fcntl.flock(c['_fd'], fcntl.LOCK_UN)
    os.close(c['_fd'])
    out = {k: v for k, v in c.items() if k not in ('arq', '_fd')}
    _ATUAL.clear()
    return out


@contextmanager
def video(rotulo: str, pasta: Path, **kw):
    abrir(rotulo, pasta, **kw)
    try:
        yield _ATUAL
    finally:
        fechar()


def aberto() -> bool:
    return bool(_ATUAL)


def _negar(motivo: str, **info) -> None:
    _ATUAL['negadas'].append({'motivo': motivo, **info, 'quando': time.strftime('%Y-%m-%dT%H:%M:%S')})
    _salvar(_ATUAL)
    raise OperacaoNegada(motivo)


def antes(provedor: str, etapa: str, pior_usd: float | None = 0.0, futuros_usd: float = 0.0) -> dict | None:
    """Preflight. Devolve um bilhete para `depois()` ou levanta OperacaoNegada. Sem caixa aberto: None (não interfere)."""
    if not _ATUAL:
        return None
    c = _ATUAL
    fat = faturamento(provedor)
    info = {'provedor': provedor, 'etapa': etapa, 'faturamento': fat, 'pior_usd': pior_usd}
    decorrido = c['segundos'] + time.time() - c['inicio']
    if decorrido > MAX_SEGUNDOS:
        _negar(f'tempo de execução esgotado ({decorrido:.0f}s > {MAX_SEGUNDOS:.0f}s)', **info)
    if c['chamadas'] >= MAX_CHAMADAS:
        _negar(f'limite de chamadas do vídeo atingido ({MAX_CHAMADAS})', **info)
    if fat == 'desconhecido':
        _negar(f'provedor "{provedor}" sem faturamento declarado: não chamo', **info)
    pago = fat in ('pago', 'confirmar')
    if pago:
        if not c['ratificado']:
            _negar(f'"{provedor}" pode cobrar e o teto não foi ratificado (CAIXA_RATIFICADO): peço autorização', **info)
        if c['por_etapa'].get(etapa, 0) >= MAX_POR_ETAPA:
            _negar(f'limite de tentativas pagas da etapa "{etapa}" atingido ({MAX_POR_ETAPA})', **info)
        if pior_usd is None:
            _negar(f'custo de "{provedor}" ({etapa}) desconhecido: não chamo', **info)
        total = c['cobrado_usd'] + c['reservado'] + pior_usd + futuros_usd
        if total > c['teto']:
            _negar(f'cobrança prevista US$ {total:.2f} > teto US$ {c["teto"]:.2f}: preciso de autorização explícita', **info)
        c['reservado'] += pior_usd
    c['chamadas'] += 1
    if pago:
        c['por_etapa'][etapa] = c['por_etapa'].get(etapa, 0) + 1
    _salvar(c)
    return {**info, 'pago': pago, 't0': time.time()}


def depois(bilhete: dict | None, ok: bool = True, cobrado_usd: float = 0.0, credito_usd: float = 0.0, cota: int = 1,
           erro: str = '') -> None:
    """Registra a operação (sucesso ou falha: falha também gasta). Libera a reserva."""
    if not bilhete or not _ATUAL:
        return
    c = _ATUAL
    if bilhete['pago']:
        c['reservado'] = max(0.0, c['reservado'] - (bilhete['pior_usd'] or 0))
        c['cobrado_usd'] = round(c['cobrado_usd'] + cobrado_usd, 6)
    else:
        cobrado_usd = 0.0
    c['credito_usd'] = round(c['credito_usd'] + credito_usd, 6)
    if bilhete['faturamento'] == 'cota':
        c['cota'][bilhete['provedor']] = c['cota'].get(bilhete['provedor'], 0) + cota
    c['operacoes'].append({k: bilhete[k] for k in ('provedor', 'etapa', 'faturamento')} | {
        'ok': ok, 'cobrado_usd': cobrado_usd, 'credito_usd': credito_usd, 'segundos': round(time.time() - bilhete['t0'], 1),
        **({'erro': erro[:200]} if erro else {})})
    if c['cobrado_usd'] >= c['alerta'] and not c.get('alertou'):
        c['alertou'] = True
        print(f"  [caixa] ALERTA: cobrança do vídeo em US$ {c['cobrado_usd']:.2f} (alerta {c['alerta']:.2f}, teto {c['teto']:.2f})")
    _salvar(c)


def resumo() -> dict:
    c = _ATUAL
    if not c:
        return {}
    return {'cobrado_usd': c['cobrado_usd'], 'credito_usd': c['credito_usd'], 'cota': c['cota'], 'chamadas': c['chamadas'],
            'negadas': len(c['negadas']), 'teto': c['teto'], 'alerta': c['alerta'], 'ratificado': c['ratificado']}


def operar(provedor: str, etapa: str, fn, pior_usd: float | None = 0.0, futuros_usd: float = 0.0, credito=None):
    """antes() → fn() → depois(). `credito`: função sem argumento que devolve o crédito consumido (assinatura).
    OperacaoNegada propaga (quem chama decide: parar, ou pular algo opcional)."""
    b = antes(provedor, etapa, pior_usd, futuros_usd)
    try:
        r = fn()
    except Exception as e:
        depois(b, ok=False, credito_usd=(credito() if credito else 0.0), erro=str(e))
        raise
    depois(b, ok=True, credito_usd=(credito() if credito else 0.0))
    return r
