"""LIVRO-CAIXA do vídeo (Fase 0 da auditoria do Coringa, 12/11/2026): registra cada chamada de IA por ETAPA e por TENTATIVA.

Um "vídeo" = tudo da pauta até a entrega, contando temas descartados, novas tentativas e refações. Só MEDE: nada aqui
bloqueia ou troca chamadas (o teto de USD 0,30 entra na Fase 1).

- Claude: custo que o próprio Claude Code devolve (`total_cost_usd`, crédito da assinatura) + tokens do `usage`.
- Gemini: grátis — conta só pedidos e modelo, separado do Claude.
A etapa é descoberta pelo nome da função que pediu (roteiro, crítica, ganchos…); dá para forçar com `with etapa('x')`.
"""
import contextvars
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

# função que pediu → nome da etapa (o que não estiver aqui aparece com o nome da função)
ETAPAS = {
    'cacar': 'pauta', 'escolher': 'pauta', 'temas_explica': 'pauta',
    'tema_livre': 'tema', 'decidir_partes': 'partes', '_fatos': 'pesquisa',
    'coletar': 'garimpo', '_melhor_de_dois': 'roteiro', 'revisar': 'crítica',
    'escolher_gancho': 'ganchos', 'dirigir': 'diretor',
    'fiscal': 'fiscal de imagem', 'conferir_ia': 'fiscal de IA', 'fiscal_final': 'fiscal final',
    'sombra': 'fiscal sombra', '_gemini_direto': 'fiscal sombra',
}
_PULAR = {'custo.py', 'claude.py', 'gemini.py', 'orcamento_video.py', 'contextlib.py', 'threading.py', 'thread.py',
          'concurrent'}

_etapa = contextvars.ContextVar('etapa', default=None)
LIVRO: list[dict] = []
_tent = {'n': 0, 'rotulo': 'antes do tema'}


def zerar():
    LIVRO.clear()
    _tent.update(n=0, rotulo='antes do tema')


def tentativa(rotulo: str):
    """Começa a tentativa de um tema (o tema descartado continua no livro, com o número dele)."""
    _tent['n'] += 1
    _tent['rotulo'] = str(rotulo)[:80]


@contextmanager
def etapa(nome: str):
    tok = _etapa.set(nome)
    try:
        yield
    finally:
        _etapa.reset(tok)


def _quem_chamou() -> str:
    if _etapa.get():
        return _etapa.get()
    f = sys._getframe(1)
    while f:
        arq = f.f_code.co_filename.replace('\\', '/').rsplit('/', 1)[-1]
        if arq not in _PULAR and 'concurrent' not in f.f_code.co_filename:
            return ETAPAS.get(f.f_code.co_name, f.f_code.co_name)
        f = f.f_back
    return '?'


def registrar(ia: str, modelo: str, usd: float = 0.0, uso: dict | None = None, segundos: float = 0.0,
              ok: bool = True, etapa_: str | None = None):
    """Uma linha por chamada REAL (o Claude registra uma vez por `claude -p`, com sucesso ou falha; o Gemini uma vez por
    pedido respondido). Nunca levanta erro: o livro-caixa não pode atrapalhar a produção."""
    try:
        _registrar(ia, modelo, usd, uso, segundos, ok, etapa_)
    except Exception as e:
        print(f'  [custo] não registrei uma chamada ({str(e)[:80]})')


def _registrar(ia, modelo, usd, uso, segundos, ok, etapa_):
    uso = uso if isinstance(uso, dict) else {}
    LIVRO.append({
        'ia': ia, 'modelo': modelo, 'etapa': etapa_ or _quem_chamou(), 'tentativa': _tent['n'], 'tema': _tent['rotulo'],
        'usd': round(float(usd or 0), 5), 'ok': ok, 'segundos': round(segundos, 1),
        'entrada': int(uso.get('input_tokens') or 0), 'cache_escrita': int(uso.get('cache_creation_input_tokens') or 0),
        'cache_lida': int(uso.get('cache_read_input_tokens') or 0), 'saida': int(uso.get('output_tokens') or 0),
        'quando': time.strftime('%H:%M:%S'),
    })


def claude_usd() -> float:
    return round(sum(x['usd'] for x in LIVRO if x['ia'] == 'claude'), 4)


def por_etapa(ia: str = 'claude') -> dict:
    out: dict = {}
    for x in LIVRO:
        if x['ia'] != ia:
            continue
        e = out.setdefault(x['etapa'], {'usd': 0.0, 'chamadas': 0, 'tokens': 0})
        e['usd'] = round(e['usd'] + x['usd'], 4)
        e['chamadas'] += 1
        e['tokens'] += x['entrada'] + x['cache_escrita'] + x['cache_lida'] + x['saida']
    return dict(sorted(out.items(), key=lambda kv: -kv[1]['usd']))


def linha_telegram() -> str:
    """Uma linha para o resumo do Telegram (Claude separado do Gemini; o que foi gasto com temas descartados à parte)."""
    cl = [x for x in LIVRO if x['ia'] == 'claude']
    ge = [x for x in LIVRO if x['ia'] == 'gemini']
    if not cl and not ge:
        return ''
    partes = [f"💰 Claude ≈USD {claude_usd():.2f} estimado (crédito da assinatura; cobrança em dinheiro: USD 0) · {len(cl)} chamada(s)"]
    ultima = max([x['tentativa'] for x in cl] or [0])
    perdido = sum(x['usd'] for x in cl if 0 < x['tentativa'] < ultima)
    if perdido:
        partes.append(f'tema(s) descartado(s) USD {perdido:.2f}')
    pe = por_etapa()
    if pe:
        nome, d = next(iter(pe.items()))
        partes.append(f"maior etapa: {nome} USD {d['usd']:.2f}")
    if ge:
        partes.append(f'Gemini (grátis) {len(ge)} chamada(s)')
    return ' · '.join(partes)


def tabela() -> str:
    """Tabela completa para o registro da execução (vai para o Telegram como arquivo)."""
    if not LIVRO:
        return '  [custo] nenhuma chamada de IA registrada'
    linhas = ['  [custo] chamada a chamada (t = tentativa de tema; tokens: entrada / cache escrito / cache lido / saída)']
    for x in LIVRO:
        linhas.append(f"  [custo] t{x['tentativa']} {x['ia']:<6} {x['modelo'][:22]:<22} {x['etapa'][:18]:<18} "
                      f"USD {x['usd']:.4f}  {x['entrada']}/{x['cache_escrita']}/{x['cache_lida']}/{x['saida']}  "
                      f"{x['segundos']:.0f}s{'' if x['ok'] else '  FALHOU'}")
    for nome, d in por_etapa().items():
        linhas.append(f"  [custo] etapa {nome}: USD {d['usd']:.4f} em {d['chamadas']} chamada(s), {d['tokens']} tokens")
    linhas.append(f'  [custo] TOTAL Claude USD {claude_usd():.4f} ESTIMADO pelo Claude Code (descontado do crédito da assinatura; '
                  'cobrança efetiva em dinheiro: USD 0). Gemini: plano grátis.')
    return '\n'.join(linhas)


def salvar(arq: Path):
    try:                                          # Fase 1 (monitorar): o que o orçamento do vídeo calculou
        from . import orcamento_video
        orc = orcamento_video.resumo()
    except Exception:
        orc = None
    arq.write_text(json.dumps({'claude_usd_estimado': claude_usd(), 'cobranca_efetiva_usd': 0.0,
                               'observacao': 'estimativa total_cost_usd do Claude Code, descontada do crédito da assinatura',
                               'por_etapa': por_etapa(), 'chamadas': LIVRO, 'orcamento': orc},
                              ensure_ascii=False, indent=1), encoding='utf-8')
