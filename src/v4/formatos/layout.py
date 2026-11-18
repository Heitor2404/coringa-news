"""Layout responsivo às áreas seguras das plataformas (TikTok, Reels, Shorts — plataformas.json).

- `uniao()`: margens mais restritivas dos perfis ativos (topo, base, esquerda) + coluna de ícones à direita por faixa de y.
- `faixa_inferior()`: faixas PRÓPRIAS e separadas para conteúdo, legenda e créditos cartográficos (de baixo para cima:
  créditos colados no limite visível, legenda acima, conteúdo acima da legenda) — nunca uma sobre a outra.
- `slot(spec)`: qualquer slot de composição vira retângulo CENTRALIZADO na faixa livre da sua altura (encolhe se a coluna de
  ícones invade), e é empurrado para dentro do limite de conteúdo. A composição declara a intenção; o perfil decide o pixel.
- `mascaras(perfil)`: retângulos da interface simulada (para folhas de conferência e validação nos quadros).
"""
from __future__ import annotations

import json
from pathlib import Path

W, H = 1080, 1920
CFG = json.loads((Path(__file__).resolve().parent / 'plataformas.json').read_text(encoding='utf-8'))


def perfis(nomes: list[str] | None = None) -> dict:
    return {k: CFG['perfis'][k] for k in (nomes or CFG['ativos'])}


def uniao(nomes: list[str] | None = None) -> dict:
    ps = perfis(nomes)
    return {'topo': max(p['topo'] for p in ps.values()), 'base': max(p['base'] for p in ps.values()),
            'esquerda': max(p['esquerda'] for p in ps.values()), 'direita': [p['direita'] for p in ps.values()]}


def limite_direito(y0: float, y1: float, nomes: list[str] | None = None) -> float:
    """maior x utilizável numa faixa vertical (desconta a coluna de ícones que cruza a faixa)"""
    u = uniao(nomes)
    larg = [d['largura'] for d in u['direita'] if y1 > d['de_y'] and y0 < d.get('ate_y', H)]
    return W - max(larg + [u['esquerda']])


def faixa_inferior(nomes: list[str] | None = None) -> dict:
    u, F = uniao(nomes), CFG['faixa_inferior']
    base = H - u['base']                                          # último y visível em TODAS as plataformas
    cy = base - F['creditos_altura']
    ly = cy - F['folga'] - F['legenda_altura']
    xd = limite_direito(ly, base, nomes)
    xe = max(u['esquerda'], F['margem_minima'])
    meia_leg = min(540 - xe, xd - 540)
    return {'creditos': [xe, cy, xd - xe, F['creditos_altura']],
            'legenda': [round(540 - meia_leg), ly, round(2 * meia_leg), F['legenda_altura']],
            'conteudo_base': ly - F['folga'], 'conteudo_topo': F.get('conteudo_topo', 340), 'marca_y': F.get('marca_y'), 'base_visivel': base}


def slot(spec, nomes: list[str] | None = None) -> list[int]:
    """[x, y, w, h] ou {"y", "h", "w_max"} → retângulo centralizado na faixa livre, dentro do limite de conteúdo"""
    fi = faixa_inferior(nomes)
    if isinstance(spec, dict):
        y, h, wmax = spec['y'], spec['h'], spec.get('w_max', 936)
    else:
        x, y, w, h = spec
        wmax = w
    if y + h > fi['conteudo_base']:                               # empurra para cima (e encolhe só se não couber)
        y = max(fi['conteudo_topo'], fi['conteudo_base'] - h)
        h = min(h, fi['conteudo_base'] - y)
    xe = max(uniao(nomes)['esquerda'], CFG['faixa_inferior']['margem_minima'])
    meia = min(540 - xe, limite_direito(y, y + h, nomes) - 540, wmax / 2)
    return [round(540 - meia), round(y), round(2 * meia), round(h)]


def quadro(q: list[int] | None, nomes: list[str] | None = None) -> list[int] | None:
    """quadro do território: recorta a parte sob a coluna de ícones e abaixo do limite de conteúdo (não precisa centralizar)"""
    if not q:
        return q
    x, y, w, h = q
    fi = faixa_inferior(nomes)
    h = min(h, fi['conteudo_base'] - y)
    xd = limite_direito(y, y + h, nomes)
    return [x, y, round(min(w, xd - x)), round(h)]


def mascaras(nome: str) -> list[dict]:
    p = CFG['perfis'][nome]
    m = [{'tipo': 'topo', 'caixa': [0, 0, W, p['topo']]}, {'tipo': 'base', 'caixa': [0, H - p['base'], W, p['base']]},
         {'tipo': 'esquerda', 'caixa': [0, 0, p['esquerda'], H]},
         {'tipo': 'icones', 'caixa': [W - p['direita']['largura'], p['direita']['de_y'], p['direita']['largura'], p['direita'].get('ate_y', H) - p['direita']['de_y']]}]
    if p.get('recorte_feed'):
        m.append({'tipo': 'recorte_feed', 'caixa': [0, 0, W, p['recorte_feed']['topo']], 'aviso': True})
        m.append({'tipo': 'recorte_feed', 'caixa': [0, H - p['recorte_feed']['base'], W, p['recorte_feed']['base']], 'aviso': True})
    return m
