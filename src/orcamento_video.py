"""ORÇAMENTO POR VÍDEO do Coringa (Fase 1, etapa 1 — 12/11/2026): teto USD 0,30, alvo USD 0,24.

MODO MONITORAR (o único ligado nesta etapa): antes de cada chamada ao Claude calcula o PIOR CASO dela, a reserva das
etapas essenciais que ainda faltam e o que o modo "aplicar" FARIA (chamar, pular, pedir autorização). Depois da chamada
compara o pior caso com o custo real e aponta estouros. NÃO bloqueia, NÃO pula, NÃO muda parâmetros do Claude Code:
o comportamento do vídeo é exatamente o de antes. Qualquer erro aqui só vai para o registro.

Escopo: só existe orçamento entre `abrir()` e `fechar()`, chamados no caminho do Coringa (curiosidade, diário, notícia).
Fora disso (o NTC, por exemplo) nada acontece: `antes()` devolve None e não imprime nada.

Valores em USD = a estimativa do Claude Code (`total_cost_usd`), descontada do crédito da assinatura (cobrança: USD 0).
"""
import os
from contextlib import contextmanager

from . import custo

TETO_USD = float(os.getenv('ORCAMENTO_TETO_USD') or 0.30)
ALVO_USD = float(os.getenv('ORCAMENTO_ALVO_USD') or 0.24)

# preço efetivo por milhão de tokens. Sonnet: medido na Torre Eiffel 2 (4 chamadas, erro ≤ 2%): toda a entrada é cobrada
# como ESCRITA de cache (3,75), o prompt-base do Claude Code é LIDO do cache (0,30), saída 10. Haiku: proporção de
# preço da família (a calibrar quando houver chamada medida). Modelo desconhecido: o mais caro (pior caso).
PRECOS = {'sonnet': {'entrada': 3.75, 'cache_lido': 0.30, 'saida': 10.0},
          'haiku': {'entrada': 1.25, 'cache_lido': 0.10, 'saida': 5.0},
          'opus': {'entrada': 6.25, 'cache_lido': 0.50, 'saida': 25.0}}
# 12/11 (Torre Eiffel 3, M1 e M2 ligadas): o que vai em TODA chamada além do pedido, e continua indo mesmo com
# --system-prompt próprio (por isso a M1 foi descartada): ~6,4 a 7 mil tokens de base (prompt e ferramentas do Claude
# Code) lidos do cache, e mais ~4,3 a 6,4 mil tokens ESCRITOS por chamada que a conta de caracteres não vê (seções
# dinâmicas e afins). O pior caso conta os dois.
BASE_CLAUDE_CODE = 7025          # base lida do cache (maior medida: 7.025 na Torre 2; 6.397 na Torre 3)
SOBRECARGA_POR_CHAMADA = 6500    # escrita por chamada além do pedido (maior medida na Torre 3: 6.389)
CHARS_POR_TOKEN = 3.0            # português + JSON
MARGEM_USD = 0.003

# saída máxima por etapa (tokens) = 1,5 × a maior saída já vista (Torre Eiffel 2; 1ª calibração, 1 rodada só).
# É o valor que o modo "aplicar" passará em CLAUDE_CODE_MAX_OUTPUT_TOKENS. Etapa sem medida: valor conservador.
SAIDA_MAX = {'tema': 3000, 'partes': 800, 'pesquisa': 4500, 'garimpo': 4700, 'roteiro': 8400, 'crítica': 6200,
             'ganchos': 1500}
SAIDA_PADRAO = 8000
# RESERVA das etapas essenciais que ainda faltam = o custo MÉDIO medido delas (não o pior caso: somar o pior caso de
# todas dava mais que o teto já no começo, com gasto zero). Médias da Torre Eiffel 2 e 3 (12/11); tema e pesquisa ainda
# sem medida: estimativa.
CUSTO_MEDIO = {'garimpo': 0.0807, 'roteiro': 0.1018, 'crítica': 0.0788, 'ganchos': 0.0374,
               'tema': 0.05, 'pesquisa': 0.08, 'partes': 0.01}

# Heitor (12/11, 16h45): pesquisa, roteiro e crítica são essenciais; ganchos pode ser opcional.
ESSENCIAIS = {'tema', 'partes', 'pesquisa', 'garimpo', 'roteiro', 'crítica'}
OPCIONAIS = {'ganchos'}
# ordem das etapas essenciais de cada caminho (para saber o que ainda falta reservar). "partes" é condicional e pequena:
# não entra na reserva.
FLUXO_EXPLICA = ['tema', 'garimpo', 'roteiro', 'crítica']
FLUXO_NOTICIA = ['pesquisa', 'roteiro', 'crítica']

_ORC: dict = {'aberto': False}
# LOTE de notícias: a escolha das notícias (uma chamada para o lote todo) é rateada entre os vídeos do lote, para cada
# centavo contar uma vez só: vídeo = o que ele gastou + a sua parte da escolha; lote = escolha + vídeos.
_LOTE: dict = {'aberto': False}


def modo() -> str:
    m = (os.getenv('ORCAMENTO_MODO') or 'monitorar').strip().lower()
    if m == 'aplicar':
        if not _ORC.get('_avisou'):
            print('  [orçamento] ORCAMENTO_MODO=aplicar ainda NÃO foi autorizado: sigo em modo monitorar')
            _ORC['_avisou'] = True
        return 'monitorar'
    return 'desligado' if m in ('0', 'desligado', 'off') else 'monitorar'


def _preco(modelo: str) -> dict:
    m = str(modelo or '').lower()
    for k in ('haiku', 'sonnet', 'opus'):
        if k in m:
            return PRECOS[k]
    return PRECOS['opus']


def tokens(texto: str) -> int:
    return int(len(str(texto or '')) / CHARS_POR_TOKEN) + 1


def pior_caso(entrada_tokens: int, etapa: str, modelo: str, base_em_cache: bool = True) -> float:
    """Pior caso de UMA chamada: pedido + sobrecarga por chamada, tudo cobrado como escrita de cache (sem contar com
    cache nenhum, nem o da M2) + base do Claude Code (lida do cache; na 1ª chamada do vídeo, como escrita) + a saída
    máxima da etapa + margem."""
    p = _preco(modelo)
    base = BASE_CLAUDE_CODE * (p['cache_lido'] if base_em_cache else p['entrada'])
    saida = SAIDA_MAX.get(etapa, SAIDA_PADRAO) * p['saida']
    return round(((entrada_tokens + SOBRECARGA_POR_CHAMADA) * p['entrada'] + base + saida) / 1e6 + MARGEM_USD, 4)


def etapa_normalizada(etapa: str) -> str:
    """Nome de função → etapa (ex.: _gerar_roteiro → roteiro), pela mesma tabela do livro-caixa."""
    return custo.ETAPAS.get(etapa, etapa)


def classe(etapa: str) -> str:
    return 'opcional' if etapa in OPCIONAIS else 'essencial' if etapa in ESSENCIAIS else 'outra'


# ───────────────────────── escopo do vídeo ─────────────────────────
def abrir(rotulo: str = ''):
    """Abre o orçamento do vídeo. Tudo o que o Claude gastar daqui até fechar() conta (todas as tentativas), mais a sua
    parte da escolha do lote, se o vídeo for de um lote de notícias."""
    rateio = _LOTE.get('rateio', 0.0) if _LOTE.get('aberto') else 0.0
    _ORC.clear()
    _ORC.update(aberto=modo() != 'desligado', rotulo=str(rotulo)[:80], inicio=len(custo.LIVRO), eventos=[],
                teto=TETO_USD, alvo=ALVO_USD, rateio=round(rateio, 6))


def fechar():
    if _ORC.get('aberto') and _LOTE.get('aberto'):
        _LOTE['videos'].append({'rotulo': _ORC.get('rotulo'), 'proprio_usd': gasto_proprio(), 'rateio_usd': _ORC['rateio']})
    _ORC['aberto'] = False


def abrir_lote(rotulo: str = 'notícias'):
    """Antes da escolha das notícias: o que o Claude gastar até definir_rateio() é custo do LOTE."""
    _LOTE.clear()
    _LOTE.update(aberto=modo() != 'desligado', rotulo=rotulo, inicio=len(custo.LIVRO), escolha_usd=0.0, n=0,
                 rateio=0.0, videos=[])


def definir_rateio(n_videos: int):
    """Depois da escolha: fecha o custo da escolha e divide igual entre os vídeos que vão ser feitos."""
    if not _LOTE.get('aberto'):
        return
    _LOTE['escolha_usd'] = round(sum(x['usd'] for x in custo.LIVRO[_LOTE['inicio']:] if x['ia'] == 'claude'), 6)
    _LOTE['n'] = max(0, int(n_videos))
    _LOTE['rateio'] = round(_LOTE['escolha_usd'] / _LOTE['n'], 6) if _LOTE['n'] else 0.0


def fechar_lote() -> dict:
    """Fecha o lote e imprime a conta: escolha + vídeos = total, sem contar nada duas vezes."""
    if not _LOTE.get('aberto'):
        return {}
    _LOTE['aberto'] = False
    vids = _LOTE['videos']
    total = round(_LOTE['escolha_usd'] + sum(v['proprio_usd'] for v in vids), 6)
    r = {'rotulo': _LOTE['rotulo'], 'escolha_usd': _LOTE['escolha_usd'], 'n_videos_previstos': _LOTE['n'],
         'rateio_usd': _LOTE['rateio'], 'videos': vids, 'total_usd': total,
         'escolha_sem_video_usd': round(_LOTE['escolha_usd'] - _LOTE['rateio'] * len(vids), 6)}
    try:
        print(f"  [orçamento] lote {r['rotulo']}: escolha USD {r['escolha_usd']:.4f} rateada entre {r['n_videos_previstos']} "
              f"vídeo(s) (USD {r['rateio_usd']:.4f} cada) · {len(vids)} vídeo(s) feito(s) · total do lote USD {total:.4f}"
              + (f" · escolha sem vídeo USD {r['escolha_sem_video_usd']:.4f}" if r['escolha_sem_video_usd'] > 1e-6 else ''))
    except Exception:
        pass
    _LOTE['resumo'] = r
    return r


def aberto() -> bool:
    return bool(_ORC.get('aberto'))


@contextmanager
def video(rotulo: str = ''):
    """`with orcamento_video.video('tema'):` abre se ainda não houver orçamento aberto e fecha só se foi quem abriu."""
    dono = not aberto()
    if dono:
        abrir(rotulo)
    try:
        yield
    finally:
        if dono:
            fechar()


def _livro() -> list[dict]:
    return custo.LIVRO[_ORC.get('inicio', 0):]


def gasto_proprio() -> float:
    return round(sum(x['usd'] for x in _livro() if x['ia'] == 'claude'), 6)


def gasto() -> float:
    """O que conta para o vídeo: o que ele gastou + a sua parte da escolha do lote (zero fora de lote)."""
    return round(gasto_proprio() + _ORC.get('rateio', 0.0), 4)


def _feitas_na_tentativa(tent: int) -> set:
    return {etapa_normalizada(x['etapa']) for x in _livro() if x['ia'] == 'claude' and x['tentativa'] == tent}


def reserva(etapa: str, tent: int | None = None) -> float:
    """Pior caso típico das etapas ESSENCIAIS que ainda faltam depois desta, na tentativa atual."""
    tent = custo._tent['n'] if tent is None else tent
    feitas = _feitas_na_tentativa(tent)
    fluxo = FLUXO_NOTICIA if ('pesquisa' in feitas or etapa == 'pesquisa') else FLUXO_EXPLICA
    if etapa in fluxo:
        depois = fluxo[fluxo.index(etapa) + 1:]
    else:                                    # etapa fora do fluxo (ganchos, partes…): o que vem depois da última feita
        ultima = max([fluxo.index(e) for e in feitas if e in fluxo] or [-1])
        depois = fluxo[ultima + 1:]
    return round(sum(CUSTO_MEDIO.get(e, 0.10) for e in depois if e not in feitas), 4)


def parametros(etapa: str, gasto_atual: float | None = None, teto: float | None = None) -> dict:
    """O que o modo "aplicar" passará ao Claude Code. Em monitorar só é CALCULADO e registrado, nunca passado."""
    teto = _ORC.get('teto', TETO_USD) if teto is None else teto
    g = gasto() if gasto_atual is None else gasto_atual
    return {'max_budget_usd': round(max(0.01, teto - g), 4),
            'max_output_tokens': SAIDA_MAX.get(etapa, SAIDA_PADRAO)}


def decidir(etapa: str, pior: float, g: float, res: float, teto: float, alvo: float) -> str:
    """O que o modo "aplicar" faria. Essencial: chama se o pior caso cabe no teto descontada a reserva; senão pede
    autorização (supervisionado) ou abandona. Opcional: só chama se tudo couber no alvo; senão pula."""
    if classe(etapa) == 'opcional':
        return 'chamar' if g + pior + res <= alvo else 'pular'
    if g + pior + res <= teto:
        return 'chamar' if g + pior + res <= alvo else 'chamar (acima do alvo)'
    return 'pedir autorização'


def opcional_excedida(etapa: str) -> bool:
    """12/11 (polvo, autorizado pelo Heitor): chamada OPCIONAL (ganchos) não sai quando o vídeo JÁ passou do teto. Única
    regra que age de verdade; as essenciais continuam só monitoradas (o modo aplicar segue sem autorização)."""
    try:
        return modo() != 'desligado' and aberto() and classe(etapa) == 'opcional' and gasto() >= TETO_USD
    except Exception:
        return False


def antes(prompt: str, modelo: str, etapa: str | None = None, sistema: str = '') -> dict | None:
    """Chamado pelo claude.py ANTES de cada `claude -p`. Só calcula e registra. Nunca levanta erro."""
    try:
        if not aberto():
            return None
        et = etapa_normalizada(etapa or custo._quem_chamou())
        primeira = not any(x['ia'] == 'claude' for x in _livro())
        ent = tokens(prompt) + tokens(sistema)
        pior = pior_caso(ent, et, modelo, base_em_cache=not primeira)
        g, res = gasto(), reserva(et)
        teto, alvo = _ORC['teto'], _ORC['alvo']
        from . import claude as _cl
        d = {'etapa': et, 'classe': classe(et), 'tentativa': custo._tent['n'], 'modelo': modelo,
             'm2': _cl.m2_ligado() and sistema != _cl.SISTEMA,
             'entrada_tokens_est': ent, 'pior_caso': pior, 'gasto_antes': g, 'reserva': res,
             'decisao': decidir(et, pior, g, res, teto, alvo), 'parametros': parametros(et, g, teto),
             'idx_livro': len(custo.LIVRO)}
        _ORC['eventos'].append(d)
        print(f"  [orçamento] (monitorando, não bloqueia) t{d['tentativa']} {et} [{d['classe']}]: pior caso USD {pior:.4f}"
              f" · gasto USD {g:.4f} · reserva essenciais USD {res:.4f} · aplicar faria: {d['decisao']}")
        return d
    except Exception as e:
        print(f'  [orçamento] não calculei ({str(e)[:80]})')
        return None


def depois(d: dict | None):
    """Chamado pelo claude.py DEPOIS da chamada (com sucesso ou falha): compara o pior caso com o real."""
    try:
        if not d:
            return
        novas = [x for x in custo.LIVRO[d['idx_livro']:] if x['ia'] == 'claude']
        real = round(sum(x['usd'] for x in novas), 4)
        d['real'] = real
        d['cache_lido_tokens'] = sum(x['cache_lida'] for x in novas)
        d['cache_escrito_tokens'] = sum(x['cache_escrita'] for x in novas)
        d['ok'] = all(x['ok'] for x in novas) if novas else False
        d['gasto_depois'] = gasto()
        d['estimativa_baixa'] = real > d['pior_caso']
        d['estourou_alvo'] = d['gasto_depois'] > _ORC['alvo']
        d['estourou_teto'] = d['gasto_depois'] > _ORC['teto']
        avisos = [s for x, s in ((d['estimativa_baixa'], 'REAL ACIMA DO PIOR CASO'),
                                 (d['estourou_teto'], 'PASSOU DO TETO'),
                                 (d['estourou_alvo'] and not d['estourou_teto'], 'passou do alvo')) if x]
        print(f"  [orçamento] {d['etapa']}: real USD {real:.4f} (pior caso {d['pior_caso']:.4f}) · gasto do vídeo "
              f"USD {d['gasto_depois']:.4f}" + ''.join(f' · {s}' for s in avisos))
    except Exception as e:
        print(f'  [orçamento] não comparei ({str(e)[:80]})')


# ───────────────────────── relatório ─────────────────────────
def resumo() -> dict:
    ev = _ORC.get('eventos') or []
    return {'modo': 'monitorar', 'teto_usd': _ORC.get('teto', TETO_USD), 'alvo_usd': _ORC.get('alvo', ALVO_USD),
            'gasto_usd': gasto() if 'inicio' in _ORC else 0.0, 'rateio_lote_usd': _ORC.get('rateio', 0.0),
            'eventos': ev, 'm2': any(e.get('m2') for e in ev),
            'cache_lido_tokens': sum(e.get('cache_lido_tokens') or 0 for e in ev),
            'teria_pulado': [e['etapa'] for e in ev if e['decisao'] == 'pular'],
            'teria_pedido_autorizacao': [e['etapa'] for e in ev if e['decisao'] == 'pedir autorização'],
            'estimativa_baixa': [e['etapa'] for e in ev if e.get('estimativa_baixa')],
            'estourou_teto': any(e.get('estourou_teto') for e in ev),
            'estourou_alvo': any(e.get('estourou_alvo') for e in ev)}


def linha_telegram() -> str:
    """Só com o orçamento do vídeo aberto (nunca mostra o de um vídeo anterior)."""
    if not aberto():
        return ''
    r = resumo()
    if not r['eventos']:
        return ''
    f = lambda x: f'{x:.2f}'.replace('.', ',')
    estado = 'PASSOU DO TETO' if r['estourou_teto'] else 'passou do alvo' if r['estourou_alvo'] else 'dentro do alvo'
    partes = [f"🛡 Orçamento (MONITORANDO, não bloqueia): USD {f(r['gasto_usd'])} de {f(r['teto_usd'])} "
              f"(alvo {f(r['alvo_usd'])}) — {estado}"]
    partes.append('teria pulado: ' + (', '.join(r['teria_pulado']) or 'nada'))
    partes.append('teria pedido autorização: ' + (', '.join(r['teria_pedido_autorizacao']) or 'nada'))
    partes.append('pior caso abaixo do real: ' + (', '.join(r['estimativa_baixa']) or 'nunca'))
    if r['rateio_lote_usd']:
        partes.append(f"inclui USD {r['rateio_lote_usd']:.3f} da escolha do lote".replace('.', ','))
    partes.append(f"M2: {'ligada' if r['m2'] else 'desligada'} · cache lido {r['cache_lido_tokens']} tokens")
    return ' · '.join(partes)
