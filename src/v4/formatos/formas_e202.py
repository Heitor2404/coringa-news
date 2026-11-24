"""E202 — resolução de FORMAS para a cena declarativa (sem desenho manual por tema).

Cada ator pedido pelo diretor ganha uma forma de UMA destas origens, sempre registrada:

  icone      Fluent Emoji Flat (Microsoft, MIT) instalado por npm em motor4 (versão exata no package.json).
             Busca por termos em inglês fornecidos pelo diretor; sem correspondência => não resolve.
  geo        contorno REAL de país/território do Natural Earth 1:50m (domínio público) via world-atlas 2.0.2.
             Só localiza/identifica; não desenha limite de placa, rota nem fronteira inventada.
  primitiva  formas genéricas parametrizadas (bloco, camada, recipiente, filtro, particula, fluido, celula, anel).
             Nenhuma é específica de assunto.
  svg_ia     caminho SVG simples escrito pelo modelo (fallback), validado; marcado como desenho gerado por IA.

Nada aqui cria fato: a forma é ilustração identificada; o contorno geo é dado real com crédito.
"""
from __future__ import annotations

import functools
import json
import math
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
ICONES = RAIZ / 'motor4/node_modules/@iconify-json/fluent-emoji-flat/icons.json'
ATLAS = RAIZ / 'motor4/node_modules/world-atlas/countries-50m.json'
CREDITO_ICONE = 'Fluent Emoji Flat © Microsoft (MIT) via @iconify-json/fluent-emoji-flat 1.2.6'
CREDITO_GEO = 'Natural Earth 1:50m (domínio público) via world-atlas 2.0.2'
D_OK = re.compile(r'^[-+0-9., eEMmLlHhVvCcSsQqTtAaZz]+$')
COR = re.compile(r'^#[0-9a-fA-F]{6}$')
STOP = frozenset('a an the of and with for in on to face symbol sign'.split())


def _cor(c: str | None, padrao: str = '#9FB7C8') -> str:
    c = (c or '').strip()
    if re.fullmatch(r'#[0-9a-fA-F]{3}', c):
        c = '#' + ''.join(ch * 2 for ch in c[1:])
    return c.upper() if COR.fullmatch(c) else padrao


# ───────────────────────── ícones ─────────────────────────
@functools.lru_cache(maxsize=1)
def _icones() -> dict:
    if not ICONES.exists():
        raise FileNotFoundError('pacote de ícones ausente: rode npm ci --prefix motor4')
    d = json.loads(ICONES.read_text(encoding='utf8'))
    out = {}
    for nome, v in d['icons'].items():
        corpo = v['body']
        tags = set(re.findall(r'<(\w+)', corpo))
        if not tags <= {'g', 'path'} or 'transform' in corpo or 'url(' in corpo:
            continue                       # só ícones convertíveis sem perda (97%)
        if re.search(r'-(dark|light|medium|medium-dark|medium-light)$', nome):
            continue                       # variações de tom de pele não são conceitos novos
        formas = []
        for m in re.finditer(r'<path([^>]*)/?>', corpo):
            at = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
            dd = at.get('d', '')
            if not dd or not D_OK.match(dd):
                formas = []
                break
            formas.append({'d': dd, 'fill': _cor(at.get('fill'), '#000000')})
        if formas:
            out[nome] = formas
    return out


def _tok(s: str) -> list[str]:
    return [t for t in re.findall(r'[a-z0-9]+', (s or '').lower()) if t not in STOP]


def icone(termos: list[str]) -> dict | None:
    """Melhor ícone para a lista de termos (ordem = preferência do diretor). Exato > todos os tokens > nenhum."""
    ic = _icones()
    for termo in termos or []:
        alvo = '-'.join(_tok(termo))
        if alvo in ic:
            return _icone_res(alvo, termo, 'exato')
    for termo in termos or []:
        tk = set(_tok(termo))
        if not tk:
            continue
        cand = [n for n in ic if tk <= set(n.split('-'))]
        if cand:
            nome = min(cand, key=lambda n: (len(n.split('-')), n))   # o mais curto = conceito mais direto
            return _icone_res(nome, termo, 'tokens')
    return None


def _icone_res(nome: str, termo: str, modo: str) -> dict:
    return {'origem': f'icone:fluent-emoji-flat/{nome}', 'termo': termo, 'casamento': modo,
            'view': [0, 0, 32, 32], 'shapes': _icones()[nome], 'credito': CREDITO_ICONE,
            'licenca': 'MIT', 'natureza': 'ilustracao'}


# ───────────────────────── contorno geográfico real ─────────────────────────
@functools.lru_cache(maxsize=1)
def _atlas() -> dict:
    return json.loads(ATLAS.read_text(encoding='utf8'))


def _arcos() -> list[list[tuple[float, float]]]:
    d = _atlas()
    (sx, sy), (tx, ty) = d['transform']['scale'], d['transform']['translate']
    out = []
    for arc in d['arcs']:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx; y += dy
            pts.append((x * sx + tx, y * sy + ty))
        out.append(pts)
    return out


def _anel(idx: list[int], arcos) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in idx:
        a = arcos[i] if i >= 0 else arcos[~i][::-1]
        pts.extend(a[1:] if pts else a)
    return pts


def _area(p) -> float:
    return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2


def geo(nome: str) -> dict | None:
    """Contorno real (Natural Earth) por nome em inglês do país/território. Ilhas < 0,5% da maior são omitidas e isso
    é registrado; projeção equirretangular com correção de cos(latitude central) — sem escala métrica."""
    alvo = (nome or '').strip().lower()
    if not alvo:
        return None
    geoms = _atlas()['objects']['countries']['geometries']
    g = next((x for x in geoms if str((x.get('properties') or {}).get('name', '')).lower() == alvo), None)
    if not g:
        return None
    arcos = _arcos()
    polis = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]
    aneis = [_anel(p[0], arcos) for p in polis]          # só o anel externo (lagos internos omitidos)
    maior = max(_area(a) for a in aneis)
    mantidos = [a for a in aneis if _area(a) >= 0.005 * maior]
    lat0 = sum(y for a in mantidos for _, y in a) / sum(len(a) for a in mantidos)
    k = math.cos(math.radians(lat0))
    xy = [[(x * k, -y) for x, y in a] for a in mantidos]
    xs = [p[0] for a in xy for p in a]; ys = [p[1] for a in xy for p in a]
    x0, y0, w, h = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    s = 100 / max(w, h)
    d = ' '.join('M' + ' L'.join(f'{(px - x0) * s:.2f} {(py - y0) * s:.2f}' for px, py in a) + ' Z' for a in xy)
    return {'origem': f'geo:natural-earth-50m/{g["properties"]["name"]}', 'termo': nome, 'casamento': 'nome_exato',
            'view': [0, 0, round(w * s, 2), round(h * s, 2)], 'shapes': [{'d': d, 'fill': '#3E7F6B', 'stroke': '#BFE8D4', 'sw': 0.8}],
            'credito': CREDITO_GEO, 'licenca': 'domínio público', 'natureza': 'dado_real',
            'omitidos': len(aneis) - len(mantidos), 'lat_central': round(lat0, 3)}


# ───────────────────────── primitivas genéricas ─────────────────────────
def _clarear(c: str, f: float) -> str:
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    m = (lambda v: max(0, min(255, int(v + (255 - v) * f if f > 0 else v * (1 + f)))))
    return '#%02X%02X%02X' % (m(r), m(g), m(b))


def primitiva(tipo: str, cor: str | None = None) -> dict | None:
    c = _cor(cor)
    claro, escuro = _clarear(c, .35), _clarear(c, -.35)
    P = {
        'bloco': [{'d': 'M6 18 Q6 8 16 8 H84 Q94 8 94 18 V82 Q94 92 84 92 H16 Q6 92 6 82 Z', 'fill': c, 'stroke': claro, 'sw': 2.5},
                  {'d': 'M14 30 H86 M14 50 H86 M14 70 H86', 'fill': 'none', 'stroke': escuro, 'sw': 2}],
        'camada': [{'d': 'M0 30 Q25 22 50 30 T100 30 V70 Q75 78 50 70 T0 70 Z', 'fill': c, 'stroke': claro, 'sw': 2}],
        'recipiente': [{'d': 'M14 10 V84 Q14 94 24 94 H76 Q86 94 86 84 V10', 'fill': 'none', 'stroke': claro, 'sw': 4},
                       {'d': 'M17 40 Q50 34 83 40 V83 Q83 91 75 91 H25 Q17 91 17 83 Z', 'fill': c}],
        'filtro': [{'d': 'M10 10 H90 V90 H10 Z', 'fill': escuro, 'stroke': claro, 'sw': 3},
                   {'d': 'M10 26 H90 M10 42 H90 M10 58 H90 M10 74 H90 M26 10 V90 M42 10 V90 M58 10 V90 M74 10 V90',
                    'fill': 'none', 'stroke': c, 'sw': 2.5}],
        'particula': [{'d': 'M50 14 A36 36 0 1 0 50 86 A36 36 0 1 0 50 14 Z', 'fill': c, 'stroke': claro, 'sw': 5}],
        'fluido': [{'d': 'M50 6 C72 34 88 50 88 66 A38 30 0 0 1 12 66 C12 50 28 34 50 6 Z', 'fill': c, 'stroke': claro, 'sw': 2.5}],
        'celula': [{'d': 'M50 6 C80 6 94 28 94 50 C94 76 76 94 50 94 C22 94 6 74 6 50 C6 24 24 6 50 6 Z', 'fill': c, 'stroke': claro, 'sw': 3},
                   {'d': 'M50 34 A16 16 0 1 0 50 66 A16 16 0 1 0 50 34 Z', 'fill': escuro}],
        'anel': [{'d': 'M50 4 A46 46 0 1 0 50 96 A46 46 0 1 0 50 4 Z', 'fill': 'none', 'stroke': c, 'sw': 6}],
    }
    if tipo not in P:
        return None
    return {'origem': f'primitiva:{tipo}', 'termo': tipo, 'casamento': 'primitiva', 'view': [0, 0, 100, 100],
            'shapes': P[tipo], 'credito': None, 'licenca': 'código do projeto', 'natureza': 'ilustracao'}


PRIMITIVAS = ('bloco', 'camada', 'recipiente', 'filtro', 'particula', 'fluido', 'celula', 'anel')


def svg_ia(d: str, cor: str | None = None) -> dict | None:
    """Caminho único escrito pelo diretor em caixa 0..100. Recusado se fora da caixa ou com sintaxe não-SVG."""
    d = (d or '').strip()
    if not d or len(d) > 3000 or not D_OK.match(d):
        return None
    nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?(?:e-?\d+)?', d)]
    if not nums or min(nums) < -5 or max(nums) > 105:
        return None
    c = _cor(cor)
    return {'origem': 'svg_ia', 'termo': 'desenho gerado', 'casamento': 'gerado', 'view': [0, 0, 100, 100],
            'shapes': [{'d': d, 'fill': c, 'stroke': _clarear(c, .4), 'sw': 2}], 'credito': None,
            'licenca': 'gerado pelo modelo do projeto', 'natureza': 'desenho_gerado_ia'}


def resolver(forma: dict | None) -> tuple[dict | None, str]:
    """forma pedida pelo diretor → (resultado, motivo). Ordem: o que o diretor pediu; nada de troca silenciosa."""
    forma = forma or {}
    tipo = forma.get('tipo')
    if tipo == 'icone':
        r = icone([str(x) for x in (forma.get('termos_en') or [])][:6])
        if r:
            return r, 'ok'
        alt = forma.get('alternativa')
        if alt in PRIMITIVAS:
            return primitiva(alt, forma.get('cor')), 'icone_ausente_usou_primitiva_declarada'
        return None, 'ICONE-NAO-ENCONTRADO: ' + ', '.join(map(str, forma.get('termos_en') or []))
    if tipo == 'geo':
        r = geo(str(forma.get('nome_en') or ''))
        return (r, 'ok') if r else (None, f'GEO-NAO-ENCONTRADO: {forma.get("nome_en")}')
    if tipo == 'primitiva':
        r = primitiva(str(forma.get('nome') or ''), forma.get('cor'))
        return (r, 'ok') if r else (None, f'PRIMITIVA-INEXISTENTE: {forma.get("nome")}')
    if tipo == 'svg_ia':
        r = svg_ia(str(forma.get('d') or ''), forma.get('cor'))
        return (r, 'ok') if r else (None, 'SVG-IA-INVALIDO')
    return None, f'FORMA-DESCONHECIDA: {tipo}'
