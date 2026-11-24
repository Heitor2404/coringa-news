"""E202 — compilador CENA SEMÂNTICA → grafo declarativo (SceneGraph v2) sem coordenadas escritas à mão.

O diretor (IA) descreve O QUE acontece: atores (com papel e forma pedida), relações espaciais e AÇÕES de um
vocabulário genérico (fluxo, tingir, afastar, filtrar, acumular, transformar, mover, aparecer, sair, destacar,
revelar_interior). Este módulo decide COMO aparece, de forma determinística:

  1. resolve formas (formas_e202: ícone MIT, contorno Natural Earth, primitiva, svg_ia) e registra a origem;
  2. diagrama o mundo por camadas a partir do grafo de relações/ações (origem acima do destino; pares lado a lado);
  3. compila cada ação em trilhas por propriedade (x, y, escala, sx, sy, opacidade, saturação) com easing;
  4. dirige a câmera por beat: enquadra os atores envolvidos na ação para ocupar a área segura (mundo → tela);
  5. gera legendas a partir das palavras medidas da narração (ou estimadas, marcado como estimativa).

Nada é específico de tema. Toda forma é ilustração identificada, exceto o contorno geo (dado real com crédito).
Técnicas reaproveitadas da Lemo-Opuscar (MIT/CC BY-NC docs, reimplementadas, sem cópia): render f(t) determinístico,
função única mundo→tela, tempo de leitura mínimo de textos, sujeito ≥ 1/3 da altura em momentos-chave.
"""
from __future__ import annotations

import math
import re

from src.v4.formatos import formas_e202 as F

SCHEMA = 'coringa.scene_graph.private.v2'
W, H = 1080, 1920
# área essencial: largura do perfil MULTIPLATAFORMA_CONSERVADOR_V1 (x 150..770); altura no arranjo equilibrado
# da E46E (palco centrado, aprovado após a reprovação do palco alto da E46D): y 430..1170. A legenda vai a
# y 1185..1320 — 80 px abaixo do limite universal conservador (1240); registrado como desvio medido, não ignorado.
CAIXA = (150, 430, 770, 1170)
LEGENDA = (150, 1185, 770, 1320)
VERBOS = ('aparecer', 'sair', 'mover', 'fluxo', 'tingir', 'afastar', 'filtrar', 'acumular', 'transformar',
          'destacar', 'revelar_interior')
RELACOES = ('sobre', 'dentro', 'ao_lado')
PAPEIS = ('protagonista', 'origem', 'destino', 'meio', 'produto', 'contexto')
BASE = {'protagonista': 380, 'origem': 230, 'destino': 260, 'meio': 230, 'produto': 210, 'contexto': 520}
TAM_PARTICULA = 46
MAX_PARTICULAS = 14


class CenaInvalida(ValueError):
    def __init__(self, problemas: list[dict]):
        self.problemas = problemas
        super().__init__('; '.join(f"[{p['regra']}] {p['texto']}" for p in problemas)[:900])


def _p(regra: str, texto: str, cena: str = '') -> dict:
    return {'regra': regra, 'texto': texto, 'cena': cena}


def _ease(p: float) -> float:
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


# ───────────────────────── normalização (variações de formato, registradas) ─────────────────────────
def _item(x) -> dict:
    """item de partícula: aceita {'rotulo','cor','forma'}, {'item':{...}} e forma como nome de primitiva."""
    if isinstance(x, dict) and isinstance(x.get('item'), dict) and not x.get('rotulo'):
        x = {**x['item'], **{k: v for k, v in x.items() if k != 'item'}}
    x = dict(x) if isinstance(x, dict) else {'rotulo': str(x or '')}
    f = x.get('forma')
    if isinstance(f, str):
        x['forma'] = {'tipo': 'primitiva', 'nome': f if f in F.PRIMITIVAS else 'particula', 'cor': x.get('cor')}
    return x


def normalizar(cena: dict) -> tuple[dict, list[str]]:
    """Corrige VARIAÇÕES DE FORMATO sem mudar o significado e registra cada ajuste (nunca inventa ator ou fato).
    Ator com papel 'contexto' que é alvo de ação física deixa de ser fundo: vira 'meio' (só papel visual)."""
    import copy
    c = copy.deepcopy(cena)
    ajustes = []
    for b in c.get('beats') or []:
        for a in b.get('acoes') or []:
            for k in ('item', 'passa', 'retido', 'preencher_com'):
                if k in a and a[k] is not None:
                    antes = a[k]
                    a[k] = _item(a[k])
                    if a[k] != antes:
                        ajustes.append(f"{a.get('verbo')}.{k}: formato normalizado")
    ativos = set()
    for b in c.get('beats') or []:
        for a in b.get('acoes') or []:
            if a.get('verbo') not in ('aparecer', 'destacar'):
                ativos |= {a[x] for x in ('alvo', 'de', 'para', 'a', 'b', 'filtro', 'interior') if isinstance(a.get(x), str)}
    for at in c.get('atores') or []:
        if at.get('papel') == 'contexto' and at.get('id') in ativos:
            at['papel'] = 'meio'
            ajustes.append(f"{at['id']}: papel contexto→meio (participa de ação)")
    return c, ajustes


# ───────────────────────── validação semântica (antes de qualquer forma) ─────────────────────────
def validar(cena: dict, fatos_ids: set[str]) -> list[dict]:
    cid = str(cena.get('id') or '?')
    out = []
    atores = cena.get('atores') or []
    ids = [a.get('id') for a in atores if isinstance(a, dict)]
    if not atores or len(set(ids)) != len(ids) or not all(isinstance(i, str) and re.fullmatch(r'[a-z0-9_]{1,30}', i) for i in ids):
        out.append(_p('C-ATORES', 'atores ausentes ou ids não únicos [a-z0-9_]', cid))
    for a in atores:
        if a.get('papel') not in PAPEIS:
            out.append(_p('C-PAPEL', f"ator {a.get('id')}: papel fora de {PAPEIS}", cid))
        if not str(a.get('rotulo') or '').strip() or len(str(a.get('rotulo'))) > 26:
            out.append(_p('C-ROTULO', f"ator {a.get('id')}: rótulo vazio ou > 26 caracteres", cid))
    for r in cena.get('relacoes') or []:
        if r.get('tipo') not in RELACOES or r.get('a') not in ids or r.get('b') not in ids:
            out.append(_p('C-RELACAO', f'relação inválida {r}', cid))
    beats = cena.get('beats') or []
    if not beats:
        out.append(_p('C-BEATS', 'cena sem beats', cid))
    for i, b in enumerate(beats):
        bid = f'{cid}.b{i + 1}'
        fala = str(b.get('fala') or '')
        if not 3 <= len(fala.split()) <= 34:
            out.append(_p('C-FALA', f'{bid}: fala com {len(fala.split())} palavras (3–34)', cid))
        fts = b.get('fatos') or []
        if not fts or not set(fts) <= fatos_ids:
            out.append(_p('C-FATO', f'{bid}: fatos {fts} ausentes da lista verificada', cid))
        acoes = b.get('acoes') or []
        if not acoes:
            out.append(_p('C-SEM-ACAO', f'{bid}: beat sem ação visível', cid))
        if cena.get('verbo') in ('DEMONSTRAR', 'CONECTAR', 'REVELAR') and acoes and all(
                a.get('verbo') in ('aparecer', 'destacar') for a in acoes):
            out.append(_p('C-ACAO-FRACA', f'{bid}: demonstração só com aparecer/destacar (sem mudança causal)', cid))
        for a in acoes:
            v = a.get('verbo')
            if v not in VERBOS:
                out.append(_p('C-VERBO', f'{bid}: verbo {v} fora do vocabulário', cid)); continue
            for k in ('alvo', 'de', 'para', 'a', 'b', 'filtro', 'interior'):
                if k in a and isinstance(a[k], str) and a[k] not in ids and not (v == 'mover' and k == 'para' and a[k] in ('esquerda', 'direita', 'cima', 'baixo', 'centro')):
                    out.append(_p('C-REF', f'{bid}: ação {v} referencia ator inexistente {k}={a[k]}', cid))
            try:
                i0, i1 = float(a.get('inicio', 0)), float(a.get('fim', 1))
                if not 0 <= i0 < i1 <= 1:
                    raise ValueError
            except (TypeError, ValueError):
                out.append(_p('C-TEMPO', f'{bid}: ação {v} com início/fim fora de 0..1', cid))
        # números falados precisam existir nos fatos (não inventar quantidades)
    return out


def numeros_inventados(fala: str, textos_fatos: str) -> list[str]:
    fatos = set(re.findall(r'\d+(?:[.,]\d+)?', textos_fatos))
    return [n for n in re.findall(r'\d+(?:[.,]\d+)?', fala) if n not in fatos]


# ───────────────────────── diagramação ─────────────────────────
def _arestas(cena: dict) -> list[tuple[str, str]]:
    e = []
    for b in cena.get('beats') or []:
        for a in b.get('acoes') or []:
            v = a.get('verbo')
            if v in ('fluxo', 'acumular') and a.get('de') and a.get('para'):
                e.append((a['de'], a['para']))
            elif v == 'filtrar':
                if a.get('de') and a.get('filtro'):
                    e.append((a['de'], a['filtro']))
                if a.get('filtro') and a.get('para'):
                    e.append((a['filtro'], a['para']))
            elif v == 'mover' and a.get('para') and a.get('alvo') and a['para'] not in ('esquerda', 'direita', 'cima', 'baixo', 'centro'):
                e.append((a['alvo'], a['para']))
    return [x for x in e if x[0] != x[1]]


def _dependencias(cena: dict) -> dict:
    """quem é desenhado DENTRO/NO LUGAR de outro: relação explícita > transformar > revelar_interior;
    atores com posição explícita (sobre/ao_lado/afastar) nunca viram dependentes; ciclos são quebrados."""
    atores = {a['id'] for a in cena['atores']}
    rel = cena.get('relacoes') or []
    acoes = [a for b in cena.get('beats') or [] for a in b.get('acoes') or []]
    ancorados = {x for r in rel if r['tipo'] in ('sobre', 'ao_lado') for x in (r['a'], r['b'])}
    ancorados |= {x for a in acoes if a.get('verbo') == 'afastar' for x in (a.get('a'), a.get('b'))}
    dep = {}
    for r in rel:
        if r['tipo'] == 'dentro' and r['a'] not in ancorados:
            dep[r['a']] = ('dentro', r['b'])
    for a in acoes:
        if a.get('verbo') == 'transformar' and a.get('de') in atores and a.get('para') in atores and a['para'] not in ancorados:
            dep.setdefault(a['para'], ('mesmo', a['de']))
        if a.get('verbo') == 'revelar_interior' and a.get('interior') in atores and a.get('alvo') in atores and a['interior'] not in ancorados:
            dep.setdefault(a['interior'], ('dentro', a['alvo']))
    for i in list(dep):
        visto, x = {i}, dep[i][1]
        while x in dep:
            if x in visto:
                dep.pop(i, None); break
            visto.add(x); x = dep[x][1]
    return dep


ROTULO = 58                      # altura reservada ao rótulo abaixo de cada ator
PADROES = {1: [[1]], 2: [[1, 1], [2]], 3: [[2, 1], [1, 2], [1, 1, 1]], 4: [[2, 2]], 5: [[2, 2, 1], [3, 2]],
           6: [[2, 2, 2], [3, 3]]}


def _arranjar(ids: list[str], cena: dict, formas: dict) -> dict:
    """Arranjo de UM beat na área segura: unidades (ator; par lado a lado; pilha 'sobre') em linhas, na ordem do
    fluxo (origem antes do destino). Escolhe o padrão de linhas que MAXIMIZA o menor ator. → {id: (x, y, tamanho)}"""
    if not ids:
        return {}
    atores = {a['id']: a for a in cena['atores']}
    rel = cena.get('relacoes') or []
    acoes = [a for b in cena.get('beats') or [] for a in b.get('acoes') or []]
    arestas = [(u, v) for u, v in _arestas(cena) if u in ids and v in ids]
    nivel = {i: 0 for i in ids}
    for _ in range(len(ids)):
        for u, v in arestas:
            if nivel[v] < nivel[u] + 1 < len(ids) + 1:
                nivel[v] = nivel[u] + 1
    ordem = sorted(ids, key=lambda i: (nivel[i], list(atores).index(i)))
    pares = [(a['a'], a['b']) for a in acoes if a.get('verbo') == 'afastar' and a.get('a') in ids and a.get('b') in ids]
    pares += [(r['a'], r['b']) for r in rel if r['tipo'] == 'ao_lado' and r['a'] in ids and r['b'] in ids]
    pilhas = [(r['a'], r['b']) for r in rel if r['tipo'] == 'sobre' and r['a'] in ids and r['b'] in ids]
    usado, unidades = set(), []
    for i in ordem:
        if i in usado:
            continue
        pil = next((p for p in pilhas if i in p and not (set(p) & usado)), None)
        par = next((p for p in pares if i in p and not (set(p) & usado)), None)
        if pil:
            cima, baixo = pil
            ext = next((p for p in pares if baixo in p and cima not in p and not (set(p) & usado)), None)
            linha = list(ext) if ext else [baixo]
            unidades.append(('pilha', [cima], linha)); usado |= {cima, *linha}
        elif par:
            unidades.append(('par', list(par))); usado |= set(par)
        else:
            unidades.append(('um', [i])); usado.add(i)
    asp = {i: _aspecto(formas[i]) for i in ids}
    X0, Y0, X1, Y1 = CAIXA
    W, Hh = X1 - X0, Y1 - Y0

    def caber(u, cw, ch):
        """maior tamanho s (maior lado de cada ator) para a unidade caber na célula; e posições relativas."""
        if u[0] == 'pilha':
            cima, linha = u[1][0], u[2]
            larg = max(asp[cima][0], sum(asp[i][0] for i in linha))
            alt = asp[cima][1] + max(asp[i][1] for i in linha)
            s = min(cw * .9 / larg, (ch - 2 * ROTULO) * .9 / alt, 520.0)
            out, y = {}, -(alt * s + 2 * ROTULO) / 2
            out[cima] = (0.0, y + asp[cima][1] * s / 2, s); y += asp[cima][1] * s + ROTULO
            x = -sum(asp[i][0] for i in linha) * s / 2
            hl = max(asp[i][1] for i in linha) * s
            for i in linha:
                w = asp[i][0] * s; out[i] = (x + w / 2, y + hl / 2, s); x += w
            return s, out
        membros = u[1]
        larg = sum(asp[i][0] for i in membros) + (0 if u[0] == 'par' else 0)
        alt = max(asp[i][1] for i in membros)
        s = min(cw * .88 / larg, (ch - ROTULO) * .88 / alt, 520.0)
        out, x = {}, -larg * s / 2
        for i in membros:
            w = asp[i][0] * s; out[i] = (x + w / 2, -ROTULO / 2, s); x += w
        return s, out
    n = len(unidades)
    padroes = PADROES.get(n) or [[3] * (n // 3) + ([n % 3] if n % 3 else [])]
    melhor = None
    for pad in padroes:
        linhas, k = [], 0
        for c in pad:
            linhas.append(unidades[k:k + c]); k += c
        ch = Hh / len(linhas)
        res, menor = {}, 1e9
        for r, ln in enumerate(linhas):
            cw = W / len(ln)
            for c, u in enumerate(ln):
                s, rel_pos = caber(u, cw, ch)
                menor = min(menor, s)
                ux, uy = X0 + cw * (c + .5), Y0 + ch * (r + .5)
                for i, (dx, dy, ss) in rel_pos.items():
                    res[i] = (ux + dx, uy + dy, ss)
        if melhor is None or menor > melhor[0] + 1:
            melhor = (menor, res)
    return melhor[1]


def _aspecto(forma: dict) -> tuple[float, float]:
    _, _, w, h = forma['view']
    m = max(w, h)
    return w / m, h / m


# ───────────────────────── trilhas por propriedade ─────────────────────────
PROPS = ('x', 'y', 'scale', 'sx', 'sy', 'opacity', 'sat', 'draw', 'tint')


class Trilha:
    """trechos (t0, t1, v0, v1) por propriedade; valor fora dos trechos = último alvo atingido."""
    def __init__(self, base: dict):
        self.base = dict(base)
        self.seg = {p: [] for p in PROPS}

    def ir(self, prop: str, t0: float, t1: float, v1: float, v0: float | None = None):
        if v0 is None:
            v0 = self.valor(prop, t0)
        self.seg[prop].append((t0, max(t1, t0 + 1e-3), v0, v1))
        self.seg[prop].sort()

    def valor(self, prop: str, t: float) -> float:
        v = self.base[prop]
        for t0, t1, a, b in self.seg[prop]:
            if t >= t1:
                v = b
            elif t >= t0:
                return a + (b - a) * _ease((t - t0) / (t1 - t0))
        return v

    def chaves(self, dur: float, passo: float = 1 / 6) -> list[float]:
        ts = {0.0, dur}
        for p in PROPS:
            for t0, t1, _, _ in self.seg[p]:
                n = max(1, int((t1 - t0) / passo))
                ts.update(t0 + (t1 - t0) * k / n for k in range(n + 1))
        return sorted(t for t in ts if 0 <= t <= dur)


def _estados(tr: Trilha, dur: float) -> list[dict]:
    out = []
    for t in tr.chaves(dur):
        st = {'t': round(t, 4), 'angle': 0}
        for p in PROPS:
            st[p] = round(tr.valor(p, t), 4)
        st['scale'] = max(st['scale'], 1e-3); st['sx'] = max(st['sx'], 1e-3); st['sy'] = max(st['sy'], 1e-3)
        st['opacity'] = min(1, max(0, st['opacity'])); st['sat'] = min(1.5, max(0, st['sat'])); st['draw'] = min(1, max(0, st['draw'])); st['tint'] = min(1, max(0, st['tint']))
        if out and st['t'] <= out[-1]['t']:
            continue
        out.append(st)
    # remove chaves redundantes (interpolação linear entre vizinhas reproduz) para caber no contrato
    enx = [out[0]]
    for k in range(1, len(out) - 1):
        a, b, c = enx[-1], out[k], out[k + 1]
        f = (b['t'] - a['t']) / (c['t'] - a['t'])
        if any(abs(a[p] + (c[p] - a[p]) * f - b[p]) > (0.6 if p in ('x', 'y') else 0.004) for p in PROPS):
            enx.append(b)
    enx.append(out[-1])
    return enx


def _curva(p0, p1, curv: float, n: int = 1):
    """ponto na bézier quadrática com controle deslocado perpendicularmente."""
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / L * curv * L, my + dx / L * curv * L
    def f(u):
        return ((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1)
    return f


def _seed(*xs) -> float:
    h = 2166136261
    for ch in '|'.join(map(str, xs)):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


# ───────────────────────── compilação ─────────────────────────
def compilar(cena: dict, duracoes: list[float], fatos: list[dict], palavras: list[dict] | None = None,
             titulo: str = '') -> dict:
    """cena semântica + duração de cada beat (medida da narração ou estimada) → SceneGraph v2 + proveniência."""
    cena, ajustes = normalizar(cena)
    fatos_ids = {f['id'] for f in fatos}
    problemas = validar(cena, fatos_ids)
    texto_fatos = ' '.join(f['texto'] for f in fatos)
    for i, b in enumerate(cena.get('beats') or []):
        inv = numeros_inventados(str(b.get('fala') or ''), texto_fatos)
        if inv:
            problemas.append(_p('C-NUMERO', f"b{i + 1}: números {inv} não constam dos fatos", cena.get('id', '?')))
    formas, origem = {}, {}
    for a in cena.get('atores') or []:
        r, motivo = F.resolver(a.get('forma'))
        if not r:
            problemas.append(_p('C-FORMA', f"ator {a.get('id')}: {motivo}", cena.get('id', '?')))
        else:
            formas[a['id']] = r
            origem[a['id']] = {k: r.get(k) for k in ('origem', 'termo', 'casamento', 'credito', 'licenca', 'natureza', 'omitidos')}
    if len(duracoes) != len(cena.get('beats') or []) or any(d <= 0.5 for d in duracoes):
        problemas.append(_p('C-DURACAO', 'durações de beat ausentes ou < 0,5 s', cena.get('id', '?')))
    if problemas:
        raise CenaInvalida(problemas)

    atores = {a['id']: a for a in cena['atores']}
    inicio = [sum(duracoes[:k]) for k in range(len(duracoes))]
    dur = sum(duracoes)
    nb = len(cena['beats'])
    # participantes por beat (ação + foco); "geral" = todos os essenciais
    envolvidos = []
    for k, b in enumerate(cena['beats']):
        env = set()
        for a in b['acoes']:
            env |= {a[x] for x in ('alvo', 'de', 'para', 'a', 'b', 'filtro', 'interior') if isinstance(a.get(x), str) and a[x] in atores}
        foco = (b.get('camera') or {}).get('foco')
        if foco in atores:
            env.add(foco)
        if (b.get('camera') or {}).get('enquadramento') == 'geral' or not env:
            env = {i for i in atores if atores[i]['papel'] != 'contexto'}
        envolvidos.append({i for i in env if atores[i]['papel'] != 'contexto'})
    dep = _dependencias(cena)
    for k in range(nb):                              # dependente acompanha o pai em cena
        for i, (_, ref) in dep.items():
            if i in envolvidos[k]:
                envolvidos[k].add(ref)
    # ENCENAÇÃO por beat: só os participantes, grandes, em arranjo limpo; o mundo é a própria área segura
    palcos = []
    for k in range(nb):
        livres = [i for i in atores if i in envolvidos[k] and i not in dep]
        st = _arranjar(livres, cena, formas)
        for _ in range(len(dep) + 1):
            for i, (tipo, ref) in dep.items():
                if i in envolvidos[k] and ref in st and i not in st:
                    x, y, s = st[ref]
                    st[i] = (x, y, s * (0.55 if tipo == 'dentro' else 1.0))
        palcos.append(st)
    S = {i: max([p[i][2] for p in palcos if i in p] or [BASE[atores[i]['papel']]]) for i in atores}
    cx, cy = (CAIXA[0] + CAIXA[2]) / 2, (CAIXA[1] + CAIXA[3]) / 2
    trilhas = {}
    for i in atores:
        k0 = next((k for k in range(nb) if i in palcos[k]), None)
        x, y, s = palcos[k0][i] if k0 is not None else (cx, cy, S[i])
        trilhas[i] = Trilha({'x': x, 'y': y, 'scale': s / S[i], 'sx': 1, 'sy': 1, 'opacity': 0, 'sat': 1, 'draw': 1, 'tint': 0})
    for i, a in atores.items():                      # contexto: fundo fixo, translúcido, do início ao fim
        if a['papel'] == 'contexto':
            S[i] = 640.0
            trilhas[i] = Trilha({'x': cx, 'y': cy, 'scale': 1, 'sx': 1, 'sy': 1, 'opacity': 0, 'sat': 1, 'draw': 1, 'tint': 0})
            trilhas[i].ir('opacity', 0, .5, .3, 0)
    explicito = {(k, a['alvo']) for k, b in enumerate(cena['beats']) for a in b['acoes'] if a.get('verbo') == 'aparecer' and isinstance(a.get('alvo'), str)}
    TRANS = 0.55
    visivel = set()
    for k in range(nb):
        T = inicio[k]
        for i in sorted(visivel - set(palcos[k])):           # sai de cena
            trilhas[i].ir('opacity', T, T + .35, 0)
        n = 0
        for i in atores:
            if i not in palcos[k]:
                continue
            x, y, s = palcos[k][i]
            tr = trilhas[i]
            if i in visivel:                                  # continuidade: desliza para o novo lugar
                tr.ir('x', T, T + TRANS, x); tr.ir('y', T, T + TRANS, y); tr.ir('scale', T, T + TRANS, s / S[i])
            else:
                tr.ir('x', T, T + .001, x); tr.ir('y', T, T + .001, y)
                if (k, i) not in explicito:
                    t0 = T + (0.05 + 0.12 * n if k == 0 else 0.08 * n)
                    tr.ir('opacity', t0, t0 + .35, 1.0, 0)
                    tr.ir('scale', t0, t0 + .45, s / S[i], .82 * s / S[i])
                n += 1
        visivel = set(palcos[k])
    tintas = {}
    for b in cena['beats']:                                   # estado inicial visível antes da mudança
        for a in b['acoes']:
            if a.get('verbo') == 'tingir' and a.get('alvo') in trilhas:
                tr = trilhas[a['alvo']]
                if not tr.seg['sat'] and 'de_saturacao' in a or (not tr.seg['sat'] and not a.get('para_cor')):
                    tr.base['sat'] = float(a.get('de_saturacao', 0.15))
                if F.COR.fullmatch(str(a.get('para_cor') or '')):
                    tintas[a['alvo']] = a['para_cor'].upper()
    acoes_planas = []
    for k, b in enumerate(cena['beats']):
        for a in b['acoes']:
            t0 = inicio[k] + float(a.get('inicio', 0)) * duracoes[k]
            t1 = inicio[k] + float(a.get('fim', 1)) * duracoes[k]
            if k > 0 and a.get('verbo') != 'aparecer':        # a ação começa depois que a encenação assentou
                t0 = max(t0, inicio[k] + TRANS)
                t1 = max(t1, t0 + .4)
            acoes_planas.append((t0, min(t1, dur), k, a))
    acoes_planas.sort(key=lambda x: x[0])

    def P(i, tt):
        tr = trilhas[i]
        return {'x': tr.valor('x', tt), 'y': tr.valor('y', tt), 's': S[i] * tr.valor('scale', tt)}
    extras: list[dict] = []                     # partículas, anéis, trilhas de rota e preenchimentos
    for t0, t1, k, a in acoes_planas:
        n0 = len(extras)
        _acao(a, t0, t1, k, atores, P, formas, trilhas, extras)
        if k + 1 < nb:                          # efeitos pertencem ao beat: saem quando a encenação muda
            for e in extras[n0:]:
                e['trilha'].ir('opacity', inicio[k + 1], inicio[k + 1] + .3, 0)
    camera = [{'t': 0.0, 'x': cx, 'y': cy, 'zoom': 1.0}, {'t': round(dur, 4), 'x': cx, 'y': cy, 'zoom': 1.0}]
    focos = []
    for k, b in enumerate(cena['beats']):
        f = (b.get('camera') or {}).get('foco')
        if f not in palcos[k]:
            f = max(palcos[k], key=lambda i: palcos[k][i][2]) if palcos[k] else None
        focos.append(f)
    pos = {i: {'x': trilhas[i].base['x'], 'y': trilhas[i].base['y'], 's': S[i]} for i in atores}

    graf_atores = []
    for i, a in atores.items():
        f = formas[i]
        graf_atores.append({'id': i, 'label': a['rotulo'], 'layer': 'contexto' if a['papel'] == 'contexto' else 'essencial',
                            'view': f['view'], 'size': S[i], 'shapes': f['shapes'], 'states': _estados(trilhas[i], dur),
                            'curve': 'linear', 'origem': f['origem'], **({'tint_color': tintas[i]} if i in tintas else {})})
    for e in extras:
        graf_atores.append({**{k: v for k, v in e.items() if k != 'trilha'}, 'states': _estados(e['trilha'], dur)})
    graf_atores.sort(key=lambda a: {'contexto': 0, 'essencial': 1, 'efeito': 2, 'particula': 3}[a['layer']])
    fontes = sorted({f['fonte'] for f in fatos if any(f['id'] in (b.get('fatos') or []) for b in cena['beats'])})
    creditos = sorted({o['credito'] for o in origem.values() if o.get('credito')})
    natureza = 'esquema_com_dado_real' if any(o['natureza'] == 'dado_real' for o in origem.values()) else 'esquema_sem_escala'
    legendas = _legendas(cena['beats'], inicio, duracoes, palavras)
    data = {'schema': SCHEMA, 'nature': natureza, 'publish': False, 'source': fontes[0] if fontes else '',
            'sources': fontes, 'credits': creditos, 'headline': titulo[:44],
            'actors': graf_atores, 'camera': camera,
            'beats': [{'t': round(inicio[k], 4), 'text': str(b.get('etapa') or b['fala'])[:60], 'foco_ids': sorted(envolvidos[k]),
                       'foco_principal': focos[k],
                       'enquadramento': (b.get('camera') or {}).get('enquadramento', 'medio')} for k, b in enumerate(cena['beats'])],
            'captions': legendas['grupos'], 'captions_origin': legendas['origem']}
    prov = {'atores': origem, 'normalizacao': ajustes, 'encenacao': [{i: [round(v, 1) for v in p[i]] for i in p} for p in palcos],
            'acoes': len(acoes_planas),
            'particulas_e_efeitos': len(extras), 'duracao_s': round(dur, 3), 'beats_s': [round(d, 3) for d in duracoes],
            'fatos_por_beat': [b.get('fatos') for b in cena['beats']], 'legendas': legendas['origem']}
    return {'scene_graph': data, 'proveniencia': prov, 'duracao': dur}


def _cam_monotona(cam: list[dict], dur: float) -> list[dict]:
    out = []
    for c in cam:
        if out and c['t'] <= out[-1]['t']:
            out[-1] = c if c['t'] == out[-1]['t'] else out[-1]
            continue
        out.append(c)
    if out[-1]['t'] < dur:
        out.append({**out[-1], 't': round(dur, 4)})
    return out


def _bbox(itens, t, ta, tb, extras) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for _, tr, s, f in itens:
        ax, ay = _aspecto(f)
        for tt in (ta + .01, t, tb - .01):
            x, y, sc = tr.valor('x', tt), tr.valor('y', tt), tr.valor('scale', tt)
            hw, hh = s * ax * sc * tr.valor('sx', tt) / 2, s * ay * sc * tr.valor('sy', tt) / 2
            xs += [x - hw, x + hw]; ys += [y - hh, y + hh + 58]   # rótulo abaixo
    return min(xs), min(ys), max(xs), max(ys)


MIN_FOCO = {'detalhe': 0.55, 'medio': 0.40}   # fração da altura da área segura (regra ≥ 1/3 com folga); geral não força


def _enquadrar(caixa, caixa_foco=None, minimo: float = 0.40) -> dict:
    """Câmera que mostra os envolvidos; se o ator em foco ficar menor que o mínimo, aproxima até o mínimo e
    desloca o centro só o necessário para o foco caber inteiro (os demais podem ser cortados nas bordas)."""
    x0, y0, x1, y1 = caixa
    bw, bh = CAIXA[2] - CAIXA[0], CAIXA[3] - CAIXA[1] - 40      # 20 px de respiro em cima e embaixo
    w, h = max(40, x1 - x0) * 1.08, max(40, y1 - y0) * 1.08
    zoom = max(0.35, min(2.2, bw / w, bh / h))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if caixa_foco:
        # o foco só cresce enquanto TODOS os participantes ainda cabem: aproximar mais cortaria a ação.
        # Se ainda ficar pequeno, o alerta G-SUJEITO-PEQUENO fica registrado (defeito de diagramação, não do modelo).
        fx0, fy0, fx1, fy1 = caixa_foco
        hf = max(1.0, (fy1 - 58) - fy0)               # sem o espaço do rótulo
        if hf * zoom < minimo * bh:
            zoom = min(zoom, 2.2)
        hw, hh = bw / 2 / zoom, bh / 2 / zoom
        lo_x, hi_x = fx1 - hw, fx0 + hw
        lo_y, hi_y = fy1 - hh, fy0 + hh
        cx = min(max(cx, lo_x), hi_x) if lo_x <= hi_x else (fx0 + fx1) / 2
        cy = min(max(cy, lo_y), hi_y) if lo_y <= hi_y else (fy0 + fy1) / 2
    return {'x': round(cx, 2), 'y': round(cy, 2), 'zoom': round(zoom, 4)}


def _ponto_borda(c, s, alvo):
    dx, dy = alvo[0] - c[0], alvo[1] - c[1]
    L = math.hypot(dx, dy) or 1
    return c[0] + dx / L * s * .32, c[1] + dy / L * s * .32


def _particula(eid: str, item: dict, rotulo: str | None) -> tuple[dict, dict]:
    forma = item.get('forma') or {'tipo': 'primitiva', 'nome': 'particula', 'cor': item.get('cor')}
    if forma.get('tipo') == 'primitiva' and not forma.get('cor'):
        forma = {**forma, 'cor': item.get('cor')}
    r, motivo = F.resolver(forma)
    if not r:
        r = F.primitiva('particula', item.get('cor'))
        motivo = 'particula_padrao:' + motivo
    return r, {'origem': r['origem'], 'motivo': motivo, 'rotulo': rotulo}


class _Posicoes(dict):
    """pos[id] avaliado no instante da ação (mesma interface do mapa estático anterior)."""
    def __init__(self, P, t):
        super().__init__()
        self._P, self._t = P, t

    def __missing__(self, k):
        v = self._P(k, self._t)
        self[k] = v
        return v

    def __contains__(self, k):
        try:
            self._P(k, self._t)
            return True
        except KeyError:
            return False


def _acao(a: dict, t0: float, t1: float, k: int, atores, P, formas, trilhas, extras):
    """P(id, t) → posição/tamanho ATUAIS (a encenação move os atores entre beats)."""
    pos = _Posicoes(P, t0)
    v = a['verbo']
    eid = f"{v}{len(extras)}"
    if v == 'aparecer':
        tr = trilhas[a['alvo']]
        tr.ir('opacity', t0, t0 + min(.4, t1 - t0), 1.0, 0)
        tr.ir('scale', t0, t1, 1.0, .6)
    elif v == 'sair':
        trilhas[a['alvo']].ir('opacity', t0, t1, 0)
    elif v == 'tingir':
        if F.COR.fullmatch(str(a.get('para_cor') or '')):
            # muda para uma COR (camada da mesma forma por cima); a cor é escolha de ilustração, não medida
            trilhas[a['alvo']].ir('tint', t0, t1, float(a.get('intensidade', 0.8)))
        else:
            trilhas[a['alvo']].ir('sat', t0, t1, float(a.get('para_saturacao', 1.0)))
    elif v == 'mover':
        tr = trilhas[a['alvo']]
        alvo = a.get('para')
        if alvo in pos:
            x, y = pos[alvo]['x'], pos[alvo]['y'] - pos[alvo]['s'] * .1
        else:
            d = pos[a['alvo']]['s'] * float(a.get('distancia', 0.35))
            dx, dy = {'esquerda': (-d, 0), 'direita': (d, 0), 'cima': (0, -d), 'baixo': (0, d), 'centro': (0, 0)}.get(alvo, (0, 0))
            x, y = tr.valor('x', t0) + dx, tr.valor('y', t0) + dy
        tr.ir('x', t0, t1, x); tr.ir('y', t0, t1, y)
        if alvo in pos and a.get('absorver', False):
            tr.ir('scale', t1 - (t1 - t0) * .2, t1, .05); tr.ir('opacity', t1 - (t1 - t0) * .2, t1, 0)
    elif v == 'afastar':
        A, B = trilhas[a['a']], trilhas[a['b']]
        ax, bx = A.valor('x', t0), B.valor('x', t0)
        ay, by = A.valor('y', t0), B.valor('y', t0)
        L = math.hypot(bx - ax, by - ay) or 1
        ux, uy = (bx - ax) / L, (by - ay) / L
        d = (pos[a['a']]['s'] + pos[a['b']]['s']) / 2 * float(a.get('distancia', 0.28))
        A.ir('x', t0, t1, ax - ux * d); A.ir('y', t0, t1, ay - uy * d)
        B.ir('x', t0, t1, bx + ux * d); B.ir('y', t0, t1, by + uy * d)
        item = a.get('preencher_com')
        if item:
            r, info = _particula(eid, item, item.get('rotulo'))
            # preenchimento cresce no vão; largura acompanha a separação (sx), altura das placas
            hA = pos[a['a']]['s'] * _aspecto(formas[a['a']])[1]
            tr = Trilha({'x': (ax + bx) / 2, 'y': (ay + by) / 2, 'scale': 1, 'sx': .02, 'sy': 1, 'opacity': 0, 'sat': 1, 'draw': 1, 'tint': 0})
            tr.ir('opacity', t0, t0 + .3, 1, 0)
            tr.ir('sx', t0, t1, (2 * d) / (hA * .9) * 1.0)
            extras.append({'id': eid, 'label': item.get('rotulo'), 'layer': 'efeito', 'view': r['view'], 'size': hA * .9,
                           'shapes': r['shapes'], 'curve': 'linear', 'origem': r['origem'], 'trilha': tr,
                           'label_t': [round(t0 + (t1 - t0) * .4, 3), round(t1 + 1.5, 3)]})
            if item.get('subir', True):
                for j in range(5):         # material novo sobe pelo vão
                    pid = f'{eid}p{j}'
                    tp = Trilha({'x': (ax + bx) / 2, 'y': (ay + by) / 2 + hA * .45, 'scale': 1, 'sx': 1, 'sy': 1, 'opacity': 0, 'sat': 1, 'draw': 1, 'tint': 0})
                    s0 = t0 + (t1 - t0) * (j / 6)
                    tp.ir('opacity', s0, s0 + .2, 1, 0)
                    tp.ir('y', s0, s0 + (t1 - t0) * .5, (ay + by) / 2 - hA * .25)
                    tp.ir('opacity', s0 + (t1 - t0) * .4, s0 + (t1 - t0) * .5, 0)
                    extras.append({'id': pid, 'label': None, 'layer': 'particula', 'view': r['view'], 'size': TAM_PARTICULA * .8,
                                   'shapes': r['shapes'], 'curve': 'linear', 'origem': r['origem'], 'trilha': tp})
    elif v in ('fluxo', 'acumular', 'filtrar'):
        de, para = a.get('de'), a.get('para')
        filtro = a.get('filtro') if v == 'filtrar' else None
        grupos = []
        if v == 'filtrar':
            if a.get('passa'):
                grupos.append(('passa', a['passa']))
            if a.get('retido'):
                grupos.append(('retido', a['retido']))
        else:
            grupos.append(('fluxo', a.get('item') or {'cor': '#FFD21F'}))
        n = max(1, min(MAX_PARTICULAS, int(a.get('quantidade', 8))))
        pc = (pos[de]['x'], pos[de]['y'])
        dest = (pos[para]['x'], pos[para]['y']) if para in pos else (pc[0], pc[1] + 200)
        meio = (pos[filtro]['x'], pos[filtro]['y']) if filtro else None
        # trilha do caminho (desenhada progressivamente): mostra a rota causal, não só pontos soltos
        rota = [_ponto_borda(pc, pos[de]['s'], meio or dest)] + ([meio] if meio else []) + [dest]
        for s_i in range(len(rota) - 1):
            (x0, y0), (x1, y1) = rota[s_i], rota[s_i + 1]
            cor = (grupos[0][1].get('cor') or '#FFD21F')
            x_min, y_min = min(x0, x1) - 20, min(y0, y1) - 20
            w_, h_ = abs(x1 - x0) + 40, abs(y1 - y0) + 40
            tr = Trilha({'x': x_min + w_ / 2, 'y': y_min + h_ / 2, 'scale': 1, 'sx': 1, 'sy': 1, 'opacity': 0, 'sat': 1, 'draw': 0, 'tint': 0})
            a0 = t0 + (t1 - t0) * .25 * s_i
            tr.ir('opacity', a0, a0 + .2, .55, 0)
            tr.ir('draw', a0, a0 + (t1 - t0) * .45, 1, 0)
            tr.ir('opacity', t1 + .4, t1 + 1.0, .22)
            extras.append({'id': f'{eid}rota{s_i}', 'label': None, 'layer': 'efeito', 'view': [x_min, y_min, w_, h_],
                           'size': max(w_, h_), 'shapes': [{'d': f'M{x0:.1f} {y0:.1f} L{x1:.1f} {y1:.1f}', 'fill': 'none',
                                                           'stroke': F._cor(cor), 'sw': 7}],
                           'curve': 'linear', 'origem': 'efeito:rota', 'trilha': tr, 'tracado': True})
        for gi, (modo, item) in enumerate(grupos):
            r, info = _particula(eid, item, item.get('rotulo'))
            m = n if len(grupos) == 1 else max(2, n // len(grupos))
            for j in range(m):
                pid = f'{eid}{modo[0]}{j}'
                u0 = t0 + (t1 - t0) * .6 * (j + gi * .5) / m
                u1 = min(t1, u0 + (t1 - t0) * .45)
                jx = (_seed(pid, 'x') - .5) * pos[de]['s'] * .35
                start = _ponto_borda(pc, pos[de]['s'], meio or dest)
                start = (start[0] + jx, start[1])
                if v == 'acumular':
                    ang = _seed(pid, 'a') * 2 * math.pi
                    rad = pos[para]['s'] * .22 * math.sqrt(_seed(pid, 'r'))
                    fim = (dest[0] + rad * math.cos(ang), dest[1] + rad * math.sin(ang))
                elif modo == 'retido':
                    fim = (meio[0] + (_seed(pid, 'x2') - .5) * pos[filtro]['s'] * .6,
                           meio[1] - pos[filtro]['s'] * .1 + (_seed(pid, 'y2') - .5) * pos[filtro]['s'] * .3)
                else:
                    fim = (dest[0] + (_seed(pid, 'x3') - .5) * pos[para]['s'] * .25, dest[1])
                tp = Trilha({'x': start[0], 'y': start[1], 'scale': 1, 'sx': 1, 'sy': 1, 'opacity': 0, 'sat': 1, 'draw': 1, 'tint': 0})
                tp.ir('opacity', u0, u0 + .15, 1, 0)
                curva = .18 * (1 if j % 2 else -1)
                pts = [start, meio, fim] if (meio and modo != 'retido') else [start, fim]
                if meio and modo == 'retido':
                    pts = [start, fim]
                seg = len(pts) - 1
                for s_i in range(seg):
                    f = _curva(pts[s_i], pts[s_i + 1], curva)
                    a0 = u0 + (u1 - u0) * s_i / seg
                    a1 = u0 + (u1 - u0) * (s_i + 1) / seg
                    for q in range(1, 5):
                        x, y = f(q / 4)
                        tq0 = a0 + (a1 - a0) * (q - 1) / 4
                        tq1 = a0 + (a1 - a0) * q / 4
                        tp.ir('x', tq0, tq1, x); tp.ir('y', tq0, tq1, y)
                if v == 'fluxo' and modo != 'retido':           # absorvido pelo destino
                    tp.ir('scale', u1 - .15, u1, .2); tp.ir('opacity', u1 - .12, u1, 0)
                extras.append({'id': pid, 'label': (info['rotulo'] if j == 0 else None), 'layer': 'particula', 'view': r['view'],
                               'size': TAM_PARTICULA, 'shapes': r['shapes'], 'curve': 'linear', 'origem': r['origem'], 'trilha': tp,
                               'label_t': [round(u0, 3), round(min(u1, u0 + 2.2), 3)]})
        if v == 'fluxo' and a.get('efeito_no_destino') == 'pulsar' and para in trilhas:
            trilhas[para].ir('scale', t1 - .3, t1 - .15, 1.08); trilhas[para].ir('scale', t1 - .15, t1, 1.0)
    elif v == 'transformar':
        A, B = trilhas[a['de']], trilhas[a['para']]
        A.ir('opacity', t0, t0 + (t1 - t0) * .6, 0); A.ir('scale', t0, t1, .6)
        B.ir('opacity', t0 + (t1 - t0) * .3, t1, 1, 0); B.ir('scale', t0 + (t1 - t0) * .3, t1, 1.0, .7)
    elif v == 'revelar_interior':
        trilhas[a['alvo']].ir('opacity', t0, t1, .28)
        B = trilhas[a['interior']]
        B.ir('opacity', t0 + (t1 - t0) * .3, t1, 1, 0); B.ir('scale', t0 + (t1 - t0) * .3, t1, 1.0, .5)
    elif v == 'destacar':
        alvo = a['alvo']
        r = F.primitiva('anel', '#FFD21F')
        tr = Trilha({'x': pos[alvo]['x'], 'y': pos[alvo]['y'], 'scale': .9, 'sx': 1, 'sy': 1, 'opacity': 0, 'sat': 1, 'draw': 1, 'tint': 0})
        tr.ir('opacity', t0, t0 + .2, 1, 0); tr.ir('scale', t0, t1, 1.25); tr.ir('opacity', t1 - .25, t1, 0)
        extras.append({'id': eid, 'label': None, 'layer': 'efeito', 'view': r['view'], 'size': pos[alvo]['s'] * 1.15,
                       'shapes': r['shapes'], 'curve': 'linear', 'origem': r['origem'], 'trilha': tr})


# ───────────────────────── legendas ─────────────────────────
def _legendas(beats, inicio, duracoes, palavras):
    if palavras:
        ws = [{'w': p['w'], 's': float(p['s']), 'e': float(p['e'])} for p in palavras]
        origem = 'palavras_medidas_da_narracao'
    else:
        ws = []
        for k, b in enumerate(beats):
            toks = str(b['fala']).split()
            d = duracoes[k] * .92 / max(1, len(toks))
            ws += [{'w': w, 's': inicio[k] + j * d, 'e': inicio[k] + (j + 1) * d} for j, w in enumerate(toks)]
        origem = 'ESTIMADA_SEM_AUDIO'
    grupos, atual = [], []
    for w in ws:
        atual.append(w)
        fim_frase = w['w'][-1:] in '.!?,;:'
        if len(atual) >= 4 or fim_frase or len(' '.join(x['w'] for x in atual)) > 24:
            grupos.append(atual); atual = []
    if atual:
        grupos.append(atual)
    out = []
    for g in grupos:
        out.append({'start': round(g[0]['s'], 3), 'end': round(g[-1]['e'], 3),
                    'words': [{'w': x['w'], 's': round(x['s'], 3), 'e': round(x['e'], 3)} for x in g]})
    for i in range(len(out) - 1):           # segura a legenda até a próxima (sem tela vazia entre palavras)
        out[i]['end'] = max(out[i]['end'], min(out[i + 1]['start'], out[i]['end'] + .6))
    return {'grupos': out, 'origem': origem}
