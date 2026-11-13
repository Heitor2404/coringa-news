"""PLANO EDITORIAL e FUNÇÃO DOS BLOCOS do Coringa Explica (plano-mestre, etapas B e C — 12/11/2026).

O plano vem DENTRO do mesmo pedido de roteiro (campo "plano" do JSON): nenhuma chamada nova. Este módulo só normaliza,
valida e diagnostica com código — não decide publicação e não muda o fiscal antigo.

Plano (versão 1):
  assunto, intencao (o que o espectador aprende), por_que_agora, promessa (verdadeira e específica), publico, complexidade,
  angulo {tipo, pergunta}, modos [1–2] (estratégias, não categorias exclusivas), estrategia {abertura, progressao, payoff,
  fechamento}, evidencias [{afirmacao, fonte, certeza, natureza}], incertezas [..], visual {precisa_mostrar, disponivel,
  faltando, riscos}, duracao_alvo_s, viabilidade {ok, motivo, alternativa}.
Cada cena pode trazer "bloco" {funcao, avanca, evidencia} (função na explicação, não só fluência).
Roteiro antigo sem plano: plano DERIVADO (origem "derivado"), marcado como tal — nunca inventa evidência.
"""
import re
import unicodedata

VERSAO = 1
MODOS = ('historico_investigativo', 'mecanismo', 'comparacao', 'curiosidade_factual', 'estudo_de_caso', 'descoberta',
         'experimento_mental')
ANGULOS = ('misterio', 'mecanismo', 'contraste', 'experimento_mental', 'causa_consequencia', 'descoberta', 'paradoxo',
           'explicacao')
FUNCOES = ('abertura', 'contexto', 'mecanismo', 'evidencia', 'virada', 'comparacao', 'consequencia', 'payoff', 'ligacao',
           'fechamento')
CERTEZAS = ('alta', 'media', 'baixa')
NATUREZAS = ('fato', 'hipotese', 'analogia', 'estimativa')
COMPLEXIDADES = ('baixa', 'media', 'alta')
DURACAO_PADRAO, DURACAO_MIN, DURACAO_MAX = 55, 35, 70
PALAVRAS_POR_S = 2.75            # narração do Coringa (+10% de velocidade): ~2,7 palavras por segundo
# clickbait que promete o que um vídeo curto não entrega
CLICKBAIT = re.compile(r'voc[eê] n[aã]o vai acreditar|ningu[eé]m (te )?conta|chocante|segredo que|mudar[aá] sua vida|'
                       r'o governo esconde|ci[eê]ncia n[aã]o explica', re.I)
# vocabulário de crime/suspense: em mecanismo de biologia/ciência vira "plot" forçado (o vírus não é "criminoso")
SUSPENSE = re.compile(r'\b(crime|criminos|culpad|v[ií]tima|assassin|golpe|suspeit|investiga[cç][aã]o policial|'
                      r'plot twist|reviravolta)\w*', re.I)
CIENCIA = ('CIÊNCIA', 'CIENCIA', 'BIOLOGIA', 'NATUREZA', 'CORPO', 'ESPAÇO', 'ESPACO', 'SAÚDE', 'SAUDE', 'ANIMAIS')


def _s(x, n: int = 240) -> str:
    return re.sub(r'\s+', ' ', str(x or '')).strip()[:n]


def _lista(x, n: int = 8) -> list:
    if isinstance(x, (list, tuple)):
        return [i for i in x if i not in (None, '', {})][:n]
    return [x] if x not in (None, '', {}) else []


def _chave(s: str) -> str:
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z_]+', '_', s).strip('_')


def _opcao(x, validas, padrao=''):
    k = _chave(x)
    if k in validas:
        return k
    return next((v for v in validas if k and (k.startswith(v) or v.startswith(k))), padrao)


def _palavras(s: str) -> set[str]:
    s = unicodedata.normalize('NFKD', str(s or '').replace('*', '')).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z0-9]{4,}', s)}


PARADAS = {'como', 'para', 'pelo', 'pela', 'pelos', 'pelas', 'mais', 'muito', 'muita', 'esse', 'essa', 'isso', 'este',
           'esta', 'isto', 'quando', 'onde', 'porque', 'sobre', 'entre', 'depois', 'antes', 'ainda', 'tambem', 'cada',
           'todo', 'toda', 'todos', 'todas', 'eles', 'elas', 'mesmo', 'mesma', 'assim', 'pode', 'podem', 'fazer', 'quem',
           'qual', 'quais', 'outro', 'outra', 'nossa', 'nosso', 'voce', 'deles', 'delas', 'dele', 'dela', 'seus', 'suas',
           'numa', 'num', 'nunca', 'sempre', 'tudo', 'nada', 'algo', 'ser', 'sera', 'foram', 'eram', 'tinha', 'tem',
           'esta', 'estao', 'aqui', 'agora', 'entao', 'porem', 'mas', 'apenas', 'so', 'logo', 'bem', 'tao', 'menos',
           'que', 'com', 'por', 'uma', 'uns', 'dos', 'das', 'nos', 'nas', 'ele', 'ela', 'seu', 'sua', 'sem', 'foi', 'sao',
           'era', 'ate', 'aos', 'pra', 'pro', 'tem', 'ter', 'vai', 'nao', 'sim', 'mais', 'dia', 'vez', 'ano', 'anos'}


def raizes(s) -> set[str]:
    """Palavras de conteúdo (3+ letras, sem as vazias: "cor" conta), reduzidas aos 5 primeiros caracteres
    ("muda"/"mudando" casam)."""
    s = unicodedata.normalize('NFKD', str(s or '').replace('*', '')).encode('ascii', 'ignore').decode().lower()
    return {w[:5] for w in re.findall(r'[a-z]{3,}', s) if w not in PARADAS}


ANO = re.compile(r'\b(1[5-9][0-9]{2}|20[0-9]{2})\b')


def _central(v: dict) -> tuple[set[str], set[str], str]:
    p = v.get('plano') or {}
    est = p.get('estrategia') or {}
    txt = ' '.join([str(p.get(k) or '') for k in ('assunto', 'intencao', 'promessa')]
                   + [str((p.get('angulo') or {}).get('pergunta') or ''), str(v.get('titulo') or '')]
                   + [str(est.get(k) or '') for k in ('abertura', 'payoff', 'fechamento')] + [str(x) for x in est.get('progressao') or []]
                   + [str(e.get('afirmacao') or '') for e in p.get('evidencias') or []])
    return raizes(txt), set(ANO.findall(txt)), txt


def desvios(v: dict) -> list[str]:
    """13/11 (polvo: "Em janeiro de 2026, uma pele sintética…" num vídeo sobre como o polvo muda de cor). Assunto lateral:
    2+ ideias SEGUIDAS sem nenhuma palavra do plano (promessa, pergunta, assunto, estratégia, evidências), ou uma ideia
    com um ano que o plano não tem e menos de 40% das palavras ligadas ao plano. Só com plano do roteirista (sem ele não há o que comparar)."""
    p = v.get('plano') or {}
    if not p or p.get('origem') == 'derivado':
        return []
    central, anos, _ = _central(v)
    if not central:
        return []
    ideias = [c for c in v.get('cenas', []) if c.get('tipo') not in ('fechamento',) and not c.get('sub')]
    sem, out = [], []
    for k, c in enumerate(ideias):
        r = raizes(c.get('fala'))
        comum = r & central
        ano_fora = [a for a in ANO.findall(str(c.get('fala') or '')) if a not in anos]
        if ano_fora and len(comum) < 0.4 * max(1, len(r)):     # data nova + quase nada do plano = outro assunto
            out.append(f"desvio: cena {k + 1} traz um fato de {ano_fora[0]} fora do plano (\"{str(c.get('fala'))[:60]}\")")
        sem.append(k if (r and not comum) else None)
    run = []
    for k in sem + [None]:
        if k is not None:
            run.append(k)
            continue
        if len(run) >= 2:
            out.append(f'desvio: cenas {run[0] + 1}–{run[-1] + 1} não falam da pergunta central (assunto lateral?)')
        run = []
    return out


def _numeros(s: str) -> set[str]:
    return {n.replace('.', '').replace(',', '') for n in re.findall(r'\d[\d.,]*\d|\d', str(s or '').replace('*', ''))
            if len(n.replace('.', '').replace(',', '')) >= 2}


# ───────────────────────── plano ─────────────────────────
def normalizar_plano(p) -> dict | None:
    if not isinstance(p, dict) or not (p.get('promessa') or p.get('assunto') or p.get('angulo')):
        return None
    ang = p.get('angulo') if isinstance(p.get('angulo'), dict) else {'tipo': p.get('angulo'), 'pergunta': ''}
    est = p.get('estrategia') if isinstance(p.get('estrategia'), dict) else {}
    vis = p.get('visual') if isinstance(p.get('visual'), dict) else {}
    via = p.get('viabilidade') if isinstance(p.get('viabilidade'), dict) else {}
    evid = []
    for e in _lista(p.get('evidencias'), 12):
        if isinstance(e, str):
            e = {'afirmacao': e}
        if not isinstance(e, dict) or not e.get('afirmacao'):
            continue
        evid.append({'afirmacao': _s(e.get('afirmacao'), 200), 'fonte': _s(e.get('fonte'), 120),
                     'certeza': _opcao(e.get('certeza'), CERTEZAS, 'media'),
                     'natureza': _opcao(e.get('natureza') or e.get('tipo'), NATUREZAS, 'fato')})
    try:
        dur = int(float(p.get('duracao_alvo_s') or DURACAO_PADRAO))
    except (TypeError, ValueError):
        dur = DURACAO_PADRAO
    modos = list(dict.fromkeys(m for m in (_opcao(x, MODOS) for x in _lista(p.get('modos') or p.get('modo'), 3)) if m))
    ok = via.get('ok', True)
    return {
        'versao': VERSAO, 'origem': 'roteirista',
        'assunto': _s(p.get('assunto'), 160), 'intencao': _s(p.get('intencao'), 240),
        'por_que_agora': _s(p.get('por_que_agora'), 200), 'promessa': _s(p.get('promessa'), 200),
        'publico': _s(p.get('publico') or 'leigo', 40), 'complexidade': _opcao(p.get('complexidade'), COMPLEXIDADES, 'media'),
        'angulo': {'tipo': _opcao(ang.get('tipo'), ANGULOS, 'explicacao'), 'pergunta': _s(ang.get('pergunta'), 200)},
        'modos': modos[:2] or ['curiosidade_factual'],
        'estrategia': {'abertura': _s(est.get('abertura'), 200), 'progressao': [_s(x, 160) for x in _lista(est.get('progressao'), 8)],
                       'payoff': _s(est.get('payoff'), 200), 'fechamento': _s(est.get('fechamento'), 160)},
        'evidencias': evid,
        'incertezas': [_s(x, 200) for x in _lista(p.get('incertezas'), 6)],
        'visual': {k: [_s(x, 120) for x in _lista(vis.get(k), 10)] for k in ('precisa_mostrar', 'disponivel', 'faltando', 'riscos')},
        'duracao_alvo_s': max(DURACAO_MIN, min(DURACAO_MAX, dur)),
        'viabilidade': {'ok': ok if isinstance(ok, bool) else str(ok).lower() not in ('false', 'nao', 'não', 'no', '0'),
                        'motivo': _s(via.get('motivo'), 200), 'alternativa': _s(via.get('alternativa'), 200)},
    }


def plano_derivado(v: dict) -> dict:
    """Roteiro antigo (sem plano): o mínimo que dá para tirar do próprio roteiro, sem inventar evidência."""
    cenas = [c for c in v.get('cenas', []) if c.get('tipo') != 'fechamento']
    return normalizar_plano({'assunto': v.get('titulo') or '', 'promessa': (cenas[0].get('fala') if cenas else '') or v.get('titulo', ''),
                             'angulo': {'tipo': 'explicacao'}, 'modos': ['curiosidade_factual']}) | {'origem': 'derivado'}


def preparar(v: dict) -> dict:
    """Garante v['plano'] válido (do roteirista, ou derivado) e v['plano_erros']."""
    p = normalizar_plano(v.get('plano'))
    v['plano'] = p or plano_derivado(v)
    return v


def validar_plano(p: dict, fatos: str = '') -> list[str]:
    """Problemas objetivos do plano (código, sem IA)."""
    erros = []
    if not p:
        return ['sem plano editorial']
    if p.get('origem') == 'derivado':
        return ['plano derivado (o roteirista não mandou o plano): ângulo, evidências e viabilidade não medidos']
    if not p['promessa']:
        erros.append('sem promessa')
    elif CLICKBAIT.search(p['promessa']):
        erros.append(f"promessa com cara de clickbait: \"{p['promessa'][:80]}\"")
    if fatos:
        nf = _numeros(fatos)
        falsos = sorted(n for n in _numeros(p['promessa']) if n not in nf)
        if falsos:
            erros.append(f"promessa com número que não está nos fatos: {', '.join(falsos)}")
    if not p['angulo']['pergunta']:
        erros.append('ângulo sem pergunta central')
    if not p['estrategia']['payoff']:
        erros.append('sem payoff definido')
    if not p['evidencias']:
        erros.append('sem evidências centrais')
    elif fatos:
        sem = [e['afirmacao'][:60] for e in p['evidencias'] if e['natureza'] == 'fato' and not e['fonte']]
        if sem:
            erros.append(f'{len(sem)} evidência(s) sem fonte (ex.: {sem[0]})')
    if not p['viabilidade']['ok']:
        erros.append(f"o próprio plano diz que não é viável: {p['viabilidade']['motivo'] or 'sem motivo'}")
    return erros


def limite_palavras(p: dict | None, padrao: int) -> int:
    """Teto de palavras do roteiro. 12/11 (polvo): o plano pedia 45 s e o teto caía para 134 palavras — a 1ª versão (155)
    foi recusada e pedida de novo (US$ 0,12) e a reescrita da crítica (152) foi jogada fora, embora as duas coubessem nas
    160 de sempre. Agora a duração do plano só AUMENTA o teto (vídeo de até 70 s); nunca o deixa abaixo do padrão. Encurtar
    é pedido ao roteirista no prompt, não cobrado com nova chamada."""
    if not p or p.get('origem') == 'derivado':
        return padrao
    return max(padrao, int(round(p['duracao_alvo_s'] * PALAVRAS_POR_S)) + 10)


FOLGA_PALAVRAS = 1.08      # passou do teto por até 8%: aceita (e avisa) em vez de pagar outra chamada
MIN_IDEIAS_REESCRITA = 10  # reescrita com 10+ ideias é aproveitável (dividir() ainda quebra as frases longas)
MAX_PALAVRAS_FRASE = 20


def formato(cenas: list[dict], limite: int) -> tuple[str, list[str]]:
    """Regra ÚNICA de formato para roteiro e reescrita: ('ok' | 'recuperavel' | 'invalido', motivos).
    Recuperável = o código conserta sem IA (frase longa → dividir(); poucas palavras além do teto → aceita e avisa)."""
    ideias = [c for c in cenas if c.get('tipo') != 'fechamento']
    palavras = sum(len(str(c.get('fala') or '').split()) for c in cenas)
    longas = [c for c in ideias if len(str(c.get('fala') or '').split()) > 16]
    mot = []
    if len(ideias) < MIN_IDEIAS_REESCRITA:
        return 'invalido', [f'{len(ideias)} ideias (mínimo {MIN_IDEIAS_REESCRITA})']
    if palavras > limite * FOLGA_PALAVRAS:
        return 'invalido', [f'{palavras} palavras (teto {limite} + 8%)']
    if any(len(str(c.get('fala') or '').split()) > MAX_PALAVRAS_FRASE for c in ideias):
        return 'invalido', [f'frase com mais de {MAX_PALAVRAS_FRASE} palavras']
    if palavras > limite:
        mot.append(f'{palavras} palavras (teto {limite}): aceito, cabe na folga')
    if longas:
        mot.append(f'{len(longas)} frase(s) longa(s): viram 2 planos no dividir()')
    if len(ideias) < 11:
        mot.append(f'{len(ideias)} ideias')
    return ('recuperavel' if mot else 'ok'), mot


# ───────────────────────── blocos (etapa C) ─────────────────────────
def _funcao(c: dict) -> str:
    b = c.get('bloco') if isinstance(c.get('bloco'), dict) else {}
    return _opcao(b.get('funcao') or c.get('funcao'), FUNCOES)


def avaliar_roteiro(v: dict, fatos: str = '') -> dict:
    """Função de cada bloco + promessa × entrega, só com código. Devolve {'problemas': [...], 'funcoes': [...]}."""
    p = v.get('plano') or {}
    cenas = [c for c in v.get('cenas', []) if c.get('tipo') != 'fechamento' and not c.get('sub')]
    funcoes = [_funcao(c) for c in cenas]
    probs = []
    if p.get('origem') != 'derivado':
        sem = [k + 1 for k, f in enumerate(funcoes) if not f]
        if sem:
            probs.append(f"{len(sem)} bloco(s) sem função declarada (cena {', '.join(map(str, sem[:5]))})")
        if funcoes and 'payoff' not in funcoes:
            probs.append('nenhum bloco entrega o payoff prometido')
        fim = [f for f in funcoes[-3:] if f]
        if fim and not set(fim) & {'payoff', 'consequencia', 'fechamento'}:
            probs.append('o fim não fecha a pergunta central (últimos blocos: ' + ', '.join(fim) + ')')
        prom = _palavras(p.get('promessa')) | _palavras((p.get('angulo') or {}).get('pergunta'))
        entrega = set().union(*(_palavras(c.get('fala')) for c in cenas[len(cenas) // 2:])) if cenas else set()
        if prom and len(prom & entrega) == 0:
            probs.append('a segunda metade não retoma nada da promessa (promessa não cumprida?)')
    probs += desvios(v)                                  # 13/11: assunto lateral (pele sintética no vídeo do polvo)
    # premissa repetida: duas frases seguidas dizendo quase o mesmo
    for k in range(1, len(cenas)):
        a, b = _palavras(cenas[k - 1].get('fala')), _palavras(cenas[k].get('fala'))
        if len(a) >= 3 and len(b) >= 3 and len(a & b) / min(len(a), len(b)) >= 0.75:
            probs.append(f'cenas {k} e {k + 1} repetem a mesma informação')
    # alegação central sem suporte: número/data na fala que não está nos fatos
    if fatos:
        nf = _numeros(fatos)
        for k, c in enumerate(cenas):
            fora = sorted(n for n in _numeros(c.get('fala')) if n not in nf)
            if fora:
                probs.append(f"cena {k + 1}: número/data fora dos fatos ({', '.join(fora)})")
    # suspense criminal forçado em mecanismo de ciência/biologia
    ciencia = str(v.get('categoria') or '').upper() in CIENCIA or 'mecanismo' in (p.get('modos') or [])
    if ciencia and not set(p.get('modos') or []) & {'historico_investigativo', 'estudo_de_caso'}:
        forc = [k + 1 for k, c in enumerate(cenas) if SUSPENSE.search(str(c.get('fala') or ''))]
        if forc:
            probs.append(f"vocabulário de crime/suspense num vídeo de mecanismo (cena {', '.join(map(str, forc[:4]))})")
    return {'problemas': probs, 'funcoes': funcoes}


def para_critica(v: dict, fatos: str = '') -> str:
    """Problemas detectados por código, para a crítica (que já é chamada) corrigir — nenhuma chamada nova."""
    probs = validar_plano(v.get('plano'), fatos) + avaliar_roteiro(v, fatos)['problemas']
    probs = [x for x in probs if not x.startswith('plano derivado')]
    if not probs:
        return ''
    return 'PROBLEMAS DETECTADOS NO ROTEIRO (corrija na reescrita):\n' + '\n'.join(f'- {x}' for x in probs[:10])


def herdar(antigo: dict, novo: dict):
    """A reescrita da crítica que esquecer o plano ou a função dos blocos herda da versão anterior."""
    if antigo.get('plano') and not normalizar_plano(novo.get('plano')):
        novo['plano'] = antigo['plano']
    if len(antigo.get('cenas', [])) == len(novo.get('cenas', [])):
        for a, b in zip(antigo['cenas'], novo['cenas']):
            if 'bloco' in a and 'bloco' not in b:
                b['bloco'] = a['bloco']


def linha_telegram(v: dict, fatos: str = '') -> str:
    p = v.get('plano')
    if not p:
        return ''
    if p.get('origem') == 'derivado':
        return '🧭 Plano editorial: não veio do roteirista (derivado; ângulo/evidências não medidos)'
    av = avaliar_roteiro(v, fatos)
    probs = validar_plano(p, fatos) + av['problemas']
    base = (f"🧭 Plano editorial (só registro): {' + '.join(p['modos'])} · ângulo {p['angulo']['tipo']} · "
            f"{len(p['evidencias'])} evidência(s) · alvo {p['duracao_alvo_s']}s")
    return base + (f" · {len(probs)} problema(s): " + '; '.join(probs[:3]) if probs else ' · sem problemas detectados')
