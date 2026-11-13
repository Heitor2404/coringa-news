"""IMAGEM POR ACONTECIMENTO (Fase 3, correção 2 — 12/11/2026).

Princípio: quem assiste precisa VER o acontecimento narrado, não só uma foto do tema. Cada ideia do roteiro traz
"acontecimento" (quem, onde, quando, o recurso visual ideal) e "evento" (ideias que narram o MESMO fato têm o mesmo id).

Ordem para mostrar uma ideia (sem inventar nada):
  1. imagem do acervo que mostra o fato, o documento/jornal, ou a pessoa/lugar/objeto DESSE fato (escolha do `casar`);
  2. 2ª busca dirigida pelo acontecimento (documento/jornal primeiro quando é o recurso pedido);
  3. reserva do acervo SÓ se for da mesma pessoa/lugar do fato (comparação de nomes, sem IA) ou se a frase é de ambiente;
  4. a imagem de OUTRA ideia do MESMO evento (reenquadrada);
  5. cartão com as palavras da própria narração (o que o template já desenha quando não há imagem).
Ilustração de IA só quando o roteiro pediu "ia" (mito, microscópico, momento sem registro possível) — nunca para tapar
buraco de fato histórico. Foto vizinha de OUTRO acontecimento (o A-B-A) só no gancho, como antes.

A cobertura por acontecimento é só REGISTRO (diagnóstico): não muda nota de fiscal nem decisão de publicação.
"""
import re
import unicodedata

RECURSOS = ('foto', 'video', 'documento', 'jornal', 'retrato', 'lugar', 'objeto', 'mapa', 'linha_tempo', 'numero', 'ia',
            'ambiente')
RELACOES_DO_FATO = ('fato', 'documento', 'pessoa', 'lugar', 'objeto')    # imagem ligada ao acontecimento da frase
GRAFICOS = ('mapa', 'linha_tempo', 'numero', 'comparacao', 'cards', 'lista', 'escala', 'citacao')
SEM_IDEIA = ('fechamento',)


def _txt(x, n=60) -> str:
    return re.sub(r'\s+', ' ', str(x or '')).strip()[:n]


def _norm(s: str) -> str:
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    return ''.join(ch for ch in s if not unicodedata.combining(ch))


_VAZIAS = {'de', 'da', 'do', 'das', 'dos', 'the', 'of', 'and', 'e', 'em', 'na', 'no', 'a', 'o', 'la', 'le', 'des', 'em'}


def _tokens(s: str) -> set:
    return {t for t in re.findall(r'[a-z0-9]{3,}', _norm(s)) if t not in _VAZIAS}


def ideias(cenas: list[dict]) -> list[dict]:
    """Uma entrada por ideia. Com `grupo` (o roteiro dividido sempre tem), o 1º plano de cada grupo; sem, os que não são
    pedaço (`sub`). Na montagem `sub` também marca reenquadramento, por isso o grupo vem primeiro."""
    validas = [c for c in cenas if c.get('tipo') not in SEM_IDEIA]
    if validas and all('grupo' in c for c in validas):
        vistos, out = set(), []
        for c in validas:
            if c['grupo'] not in vistos:
                vistos.add(c['grupo'])
                out.append(c)
        return out
    return [c for c in validas if not c.get('sub')]


def normalizar(v: dict) -> dict:
    """Garante `acontecimento` e `evento` em toda ideia (o roteiro pode não mandar: aí cada ideia é o seu evento e o
    recurso fica em branco). Pedaços da mesma ideia (sub) herdam da ideia."""
    vistos = {}
    for k, c in enumerate(v.get('cenas') or []):
        if c.get('tipo') in SEM_IDEIA or c.get('sub'):
            continue
        c.setdefault('grupo', f'g{k}')
        ac = c.get('acontecimento') if isinstance(c.get('acontecimento'), dict) else {}
        rec = _norm(ac.get('recurso')).replace(' ', '_').replace('-', '_')
        rec = {'linha_do_tempo': 'linha_tempo', 'foto_do_fato': 'foto', 'jornais': 'jornal', 'mapas': 'mapa'}.get(rec, rec)
        c['acontecimento'] = {'quem': _txt(ac.get('quem')), 'onde': _txt(ac.get('onde')), 'quando': _txt(ac.get('quando'), 20),
                              'recurso': rec if rec in RECURSOS else ''}
        ev = _txt(c.get('evento') or ac.get('evento'), 12)
        c['evento'] = ev or f'i{k}'
        vistos[c.get('grupo', k)] = c
    for c in v.get('cenas') or []:
        if c.get('sub'):
            pai = vistos.get(c.get('grupo'))
            if pai:
                c['acontecimento'], c['evento'] = dict(pai['acontecimento']), pai['evento']
    return v


def linha_casar(c: dict) -> str:
    """O acontecimento da ideia, em uma linha, para o editor de imagem (`casar`)."""
    ac = c.get('acontecimento') or {}
    partes = [f"{k}={ac[k]}" for k in ('quem', 'onde', 'quando', 'recurso') if ac.get(k)]
    return f" {{acontecimento: {', '.join(partes)}}}" if partes else ''


def ligacao(item: dict, c: dict) -> str | None:
    """Sem IA: a imagem do acervo é da MESMA pessoa ou do MESMO lugar do acontecimento? (nomes em comum)"""
    ac = c.get('acontecimento') or {}
    pessoas = _tokens(' '.join(item.get('pessoas') or []))
    descr = _tokens(f"{item.get('mostra', '')} {item.get('titulo', '')}")
    quem, onde = _tokens(ac.get('quem')), _tokens(ac.get('onde'))
    if quem and (quem & pessoas or (len(quem & descr) >= min(2, len(quem)))):
        return 'pessoa'
    lugar = _tokens(item.get('lugar') or '')
    if onde and (onde & lugar or len(onde & descr) >= min(2, len(onde))):
        return 'lugar'
    return None


def ambiente(c: dict) -> bool:
    return (c.get('acontecimento') or {}).get('recurso') == 'ambiente'


# ───────────────────────── cobertura (só registro) ─────────────────────────
ROTULOS = {'mostra_o_fato': 'mostram o fato', 'ligada_ao_fato': 'pessoa/lugar/objeto do fato', 'grafico': 'gráfico',
           'mesmo_acontecimento': 'imagem do mesmo acontecimento', 'ambiente': 'ambiente', 'ilustracao_ia': 'ilustração',
           'tema': 'só do tema', 'cartao': 'cartão (sem imagem)', 'emprestada': 'emprestada de outro acontecimento',
           'sem_classificacao': 'sem classificação'}


def classe(c: dict) -> str:
    if c.get('tipo') in GRAFICOS:
        return 'grafico'
    if c.get('ia'):
        return 'ilustracao_ia'
    if c.get('mesmo_evento'):
        return 'mesmo_acontecimento'
    if c.get('repetida') or c.get('midia') == 'vizinha':
        return 'emprestada'
    if not c.get('img'):
        return 'cartao'
    rel = c.get('relacao')
    if rel in ('fato', 'documento'):
        return 'mostra_o_fato'
    if rel in ('pessoa', 'lugar', 'objeto'):
        return 'ligada_ao_fato'
    if rel == 'ambiente' or c.get('midia') == 'video' or ambiente(c):
        return 'ambiente'
    if rel == 'tema':
        return 'tema'
    return 'sem_classificacao'


def aba(cenas: list[dict]) -> int:
    """Quantas vezes uma imagem volta depois de outra, entre ideias de acontecimentos DIFERENTES (A → B → A)."""
    seq = [(c.get('img'), c.get('evento')) for c in cenas if c.get('img') and c.get('tipo') not in SEM_IDEIA]
    n = 0
    for k in range(2, len(seq)):
        a, b, x = seq[k - 2], seq[k - 1], seq[k]
        if x[0] == a[0] and b[0] != x[0] and x[1] != a[1]:
            n += 1
    return n


def cobertura(cenas: list[dict]) -> dict:
    ids = ideias(cenas)
    por = []
    for c in ids:
        if c.get('fundidas'):                 # cartões seguidos que viraram lista/linha do tempo: cada fato conta
            por += [{'evento': f.get('evento'), 'fala': _txt(f.get('fala'), 70), 'classe': 'grafico',
                     'recurso_pedido': f.get('recurso', '')} for f in c['fundidas']]
        else:
            por.append({'evento': c.get('evento'), 'fala': _txt(c.get('fala'), 70), 'classe': classe(c),
                        'recurso_pedido': (c.get('acontecimento') or {}).get('recurso', '')})
    cont = {k: sum(1 for p in por if p['classe'] == k) for k in ROTULOS}
    return {'ideias': len(por), 'contagem': cont, 'aba': aba(cenas), 'por_ideia': por}


def linha_telegram(cob: dict) -> str:
    if not cob or not cob.get('ideias'):
        return ''
    c = cob['contagem']
    partes = [f"{c[k]} {ROTULOS[k]}" for k in ROTULOS if c.get(k)]
    return (f"🎬 Cobertura visual (só registro, não muda nota): {cob['ideias']} ideias · " + ' · '.join(partes)
            + f" · A-B-A: {cob['aba']}")
