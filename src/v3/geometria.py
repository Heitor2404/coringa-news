"""Geometria da câmera do doc.plano (Plano Mestre §4) — espelho em Python da matemática de src/render/v2/comp/doc.js.

Serve para três coisas, sem render: (1) o diretor escolher o layout ('cobrir' × 'integral') antes de montar;
(2) auditar a trajetória CONTÍNUA de cada plano (cobertura, escala, velocidade, aceleração, parada-e-arranque),
amostrada quadro a quadro, e não só nas pontas; (3) os testes compararem o espelho com o palco real (window.geometria).

Estado de um enquadramento-chave: escala (log) + ponto da imagem no centro de composição (W/2, 760). Entre chaves o
centro anda em linha reta e a posição é limitada, quadro a quadro, ao que o layout permite; em 'cobrir' s ≥ escala de
cobertura, então não aparece borda nem a foto encolhe.
"""
from __future__ import annotations

import math

W, H = 1080, 1920
FIT_H, CY = 1540, 760                 # a caixa cabe em 1080×1540 centrada em y 760 (assunto acima da legenda)
SMAX = 1.8                            # ampliação máxima sobre os pixels da foto (acima disso: macia)
FPS = 30
# limites da trajetória (por segundo); valores iniciais conservadores, para revisão humana — não são estética aprovada
ZOOM_MAX_S = math.log(1.45)           # no máximo ~45% de mudança de escala por segundo
PAN_MAX_S = 700.0                     # px de tela por segundo
SALTO_PX = 40.0                       # deslocamento num único quadro que já é salto
ACEL_MAX = 9000.0                     # px/s² — mudança brusca de velocidade (arranque/freada seca)


def _clamp(x, a=0.0, b=1.0):
    return min(b, max(a, x))


def _eio(x):
    """Seno in-out (igual ao doc.js): pico de velocidade 1,57× a média."""
    return (1 - math.cos(math.pi * _clamp(x))) / 2


def nat(wh) -> float:
    return max(W / wh[0], H / wh[1])


BARRA = 1140                          # linha de cima da legenda: no 'integral', sobra só pode ficar abaixo dela


def faixa_y(s, ih, layout='cobrir'):
    if layout != 'integral':
        return min(0.0, H - ih * s), max(0.0, H - ih * s)
    return BARRA - ih * s, max(0.0, H - ih * s)


def estado(caixa, wh, layout='cobrir') -> dict:
    iw, ih = wh
    bx, by, bw, bh = caixa[0] * iw, caixa[1] * ih, caixa[2] * iw, caixa[3] * ih
    bcx, bcy = bx + bw / 2, by + bh / 2
    n = nat(wh)
    teto = max(n, SMAX)
    sb = min(W / bw, FIT_H / bh)
    s = min(sb, SMAX) if layout == 'integral' else _clamp(sb, n, teto)
    if layout == 'integral' and n * .82 <= s < n and n <= SMAX * 1.12 \
            and abs(_clamp(CY - bcy * n, H - ih * n, 0) + bcy * n - CY) < 250:
        s = n                                   # margem pequena parece acidente: cobre, se o assunto fica no lugar
    tx, ty = W / 2 - bcx * s, CY - bcy * s
    if layout == 'integral':                     # prefere a composição limpa se o assunto andar < 250 px por isso
        tc = _clamp(ty, min(0.0, H - ih * s), max(0.0, H - ih * s))
        if abs(tc - ty) < 250:
            ty = tc
    s_, tx, ty = limitar(s, (W / 2 - tx) / s, (CY - ty) / s, wh, layout)
    return {'s': s, 'sb': sb, 'cx': (W / 2 - tx) / s, 'cy': (CY - ty) / s}


def limitar(s, cx, cy, wh, layout='cobrir'):
    """(s, tx, ty) com o ponto (cx, cy) da imagem no centro de composição, limitado ao que o layout permite."""
    iw, ih = wh
    dx = W - iw * s
    lo, hi = faixa_y(s, ih, layout)
    if layout == 'integral' and iw * s < W and ih * s < H:     # foto pequena: cartão parado (não é câmera)
        return s, dx / 2, _clamp(0.0, lo, hi)
    return s, _clamp(W / 2 - cx * s, min(0.0, dx), max(0.0, dx)), _clamp(CY - cy * s, lo, hi)


def transform(cam, tl, wh, layout='cobrir') -> tuple[float, float, float]:
    """(s, tx, ty) no tempo local tl — mesma conta do camEm de doc.js."""
    ks = cam or [{'t': 0, 'caixa': [0, 0, 1, 1]}]
    es = [{**estado(k['caixa'], wh, layout), 't': float(k.get('t') or 0), 'ease': k.get('ease')} for k in ks]
    a = b = es[0]
    k = 1.0
    for i in range(len(es) - 1):
        if tl >= es[i]['t']:
            a, b = es[i], es[i + 1]
            k = _clamp((tl - a['t']) / max(.01, b['t'] - a['t']))
    if tl >= es[-1]['t']:
        a = b = es[-1]
        k = 1.0
    e = k if b.get('ease') == 'linear' else _eio(k)
    s = math.exp(math.log(a['s']) + (math.log(b['s']) - math.log(a['s'])) * e)
    return limitar(s, a['cx'] + (b['cx'] - a['cx']) * e, a['cy'] + (b['cy'] - a['cy']) * e, wh, layout)


def duracao_minima(c0, c1, wh) -> float:
    """Menor duração de um movimento entre duas caixas para que o PICO (seno in-out: π/2 × a média) respeite os limites
    de zoom e de pan. Aproximação pela escala de 'cobrir'."""
    e0, e1 = estado(c0, wh), estado(c1, wh)
    dz = abs(math.log(e1['s']) - math.log(e0['s']))
    s = math.sqrt(e0['s'] * e1['s'])
    iw, ih = wh
    dp = math.hypot((c1[0] + c1[2] / 2 - c0[0] - c0[2] / 2) * iw, (c1[1] + c1[3] / 2 - c0[1] - c0[3] / 2) * ih) * s
    return round(max(dz / ZOOM_MAX_S, dp / PAN_MAX_S) * math.pi / 2 * 1.05, 2)


def visivel(caixa, wh, layout='cobrir') -> float:
    """Fração da caixa (área) que fica dentro do quadro nesse enquadramento-chave (1.0 = inteira)."""
    iw, ih = wh
    s, tx, ty = transform([{'t': 0, 'caixa': caixa}], 0, wh, layout)
    x0, y0 = tx + caixa[0] * iw * s, ty + caixa[1] * ih * s
    x1, y1 = x0 + caixa[2] * iw * s, y0 + caixa[3] * ih * s
    a = max(1e-9, (x1 - x0) * (y1 - y0))
    return max(0.0, min(x1, W) - max(x0, 0)) * max(0.0, min(y1, H) - max(y0, 0)) / a


def escolher_layout(caixas: list, wh, pedido: str | None = None, documento: bool = False) -> tuple[str, float]:
    """→ (layout, pior fração visível em 'cobrir'). Pedido explícito é respeitado. Sem pedido: 'cobrir' quando toda
    caixa cabe (≥ 90% visível) e a foto tem resolução para cobrir o quadro; senão 'integral' (a caixa inteira e a
    nitidez importam mais do que cobrir o quadro)."""
    pior = min(visivel(c, wh, 'cobrir') for c in caixas) if caixas else 1.0
    if pedido in ('cobrir', 'integral'):
        return pedido, pior
    if nat(wh) > SMAX * 1.12:
        return 'integral', pior
    return ('cobrir' if pior >= .9 and not (documento and pior < .97) else 'integral'), pior


def auditar(cam, dur: float, wh, layout='cobrir', fps: int = FPS) -> list[dict]:
    """Amostra a trajetória quadro a quadro. → achados {codigo, t, texto} (vazio = sem defeito geométrico)."""
    iw, ih = wh
    n = nat(wh)
    out = []
    amostras = [transform(cam, i / fps, wh, layout) for i in range(int(dur * fps) + 1)]

    def ach(codigo, t, texto):
        if not any(a['codigo'] == codigo for a in out):        # um achado por tipo e plano (o primeiro quadro)
            out.append({'codigo': codigo, 't': round(t, 2), 'texto': texto})
    vel = []
    for i, (s, tx, ty) in enumerate(amostras):
        t = i / fps
        if layout == 'cobrir':
            if s < n - 1e-6:
                ach('G-ENCOLHE', t, f'escala {s:.3f} abaixo da que cobre o quadro ({n:.3f})')
            if tx > .5 or ty > .5 or tx + iw * s < W - .5 or ty + ih * s < H - .5:
                ach('G-BORDA', t, f'borda aparecendo (tx {tx:.0f}, ty {ty:.0f}, {iw * s:.0f}×{ih * s:.0f})')
        else:
            f = 1.0
            if iw * s >= W and (tx > f or tx + iw * s < W - f):
                ach('G-BORDA', t, 'imagem descobre a borda lateral num eixo que ela cobre')
            if iw * s < W and (tx < -f or tx + iw * s > W + f):
                ach('G-BORDA', t, 'imagem estreita cortada na lateral')
            if (ty > f and ty + ih * s > H + f) or ty + ih * s < BARRA - f:
                ach('G-BORDA', t, f'vão fora da barra da legenda (topo {ty:.0f}, base {ty + ih * s:.0f})')
        if s > SMAX + 1e-6:
            ach('G-RESOLUCAO', t, f'ampliação {s:.2f}× sobre os pixels da foto (> {SMAX}): imagem macia')
        if i:
            s0, tx0, ty0 = amostras[i - 1]
            # deslocamento do centro da tela em coordenadas da foto, convertido para px de tela
            cx0, cy0 = (W / 2 - tx0) / s0, (H / 2 - ty0) / s0
            cx1, cy1 = (W / 2 - tx) / s, (H / 2 - ty) / s
            d = math.hypot(cx1 - cx0, cy1 - cy0) * s
            dz = abs(math.log(s) - math.log(s0))
            vel.append(d * fps)
            if d > SALTO_PX:
                ach('G-SALTO', t, f'salto de {d:.0f} px num quadro')
            if d * fps > PAN_MAX_S:
                ach('G-PAN-RAPIDO', t, f'pan a {d * fps:.0f} px/s (limite {PAN_MAX_S:.0f})')
            if dz * fps > ZOOM_MAX_S:
                ach('G-ZOOM-RAPIDO', t, f'zoom a {math.exp(dz * fps) - 1:.0%}/s (limite {math.exp(ZOOM_MAX_S) - 1:.0%})')
    for i in range(1, len(vel)):
        if abs(vel[i] - vel[i - 1]) * fps > ACEL_MAX:
            ach('G-ACELERACAO', (i + 1) / fps, f'velocidade muda {abs(vel[i] - vel[i - 1]):.0f} px/s em um quadro')
    # parada-e-arranque: o movimento para (≈0) e volta a andar em menos de 0,3 s, sem estar numa pausa planejada
    parado = [v < 8 for v in vel]
    i = 0
    while i < len(parado):
        if parado[i] and 0 < i and not parado[i - 1]:
            j = i
            while j < len(parado) and parado[j]:
                j += 1
            if j < len(parado) and (j - i) / fps < .3:
                ach('G-PARA-E-ANDA', i / fps, f'câmera para e volta a andar em {(j - i) / fps:.2f}s')
            i = j
        i += 1
    return out


def auditar_dados(dados: dict) -> list[dict]:
    """Todos os doc.plano de um v2_dados.json → achados com plano e tempo absoluto."""
    out = []
    for k, sc in enumerate(dados.get('scenes') or []):
        p = sc.get('params') or {}
        if sc.get('comp') != 'doc.plano' or not p.get('wh'):
            continue
        if p.get('layout') == 'editorial':
            e = editorial(p['wh'], p.get('visao_geral'), (p.get('cam') or [{'caixa': None}])[0].get('caixa'))
            if not e['resolucao_ok']:
                out.append({'codigo': 'G-RESOLUCAO', 't': 0, 'texto': f"detalhe editorial ampliado {e['detalhe']['s']:.2f}× sobre os pixels da fonte",
                            'plano': k, 'inicio': round(sc['start'], 2)})
            continue
        for a in auditar(p.get('cam'), sc['end'] - sc['start'], p['wh'], p.get('layout') or 'cobrir'):
            out.append({**a, 'plano': k, 'inicio': round(sc['start'] + a['t'], 2)})
    return out


def auditar_palco(pg, dados: dict, fps: int = 10) -> list[dict]:
    """Mede o PALCO REAL (Chromium, window.geometria): onde a imagem principal está em cada amostra. Confere cobertura
    em 'cobrir' e compara com o espelho (diferença > 2 px = o JS e a conta divergiram). Ignora o instante de transição
    da própria cena (o chicote/íris movem a cena de propósito)."""
    out = []
    cenas = dados['scenes']
    t, fim = 0.0, dados['duration']
    while t < fim:
        for g in pg.evaluate(f'geometria({t:.4f})'):
            sc = cenas[g['cena']]
            p = sc.get('params') or {}
            if sc.get('comp') != 'doc.plano' or g['em_transicao'] or g['opacidade'] < .99:
                continue
            if g['layout'] == 'cobrir' and (g['x0'] > .5 or g['y0'] > .5 or g['x1'] < W - .5 or g['y1'] < H - .5):
                out.append({'codigo': 'G-BORDA', 'plano': g['cena'], 'inicio': round(t, 2),
                            'texto': f"borda no palco: imagem em ({g['x0']:.0f},{g['y0']:.0f})–({g['x1']:.0f},{g['y1']:.0f})"})
            # ocupação medida no palco (união dos painéis de imagem, recortada ao quadro) × espelho
            pain = g.get('paineis') or [[g['x0'], g['y0'], g['x1'], g['y1']]]
            oc_palco = sum(max(0, min(W, x1) - max(0, x0)) * max(0, min(H, y1) - max(0, y0)) for x0, y0, x1, y1 in pain) / (W * H)
            oc_esp = ocupacao(p, t - sc['start'])['ocupacao']
            if abs(min(1.0, oc_palco) - oc_esp) > .01:
                out.append({'codigo': 'G-ESPELHO', 'plano': g['cena'], 'inicio': round(t, 2),
                            'texto': f"ocupação no palco {oc_palco:.3f} × espelho {oc_esp:.3f}"})
            if g['layout'] == 'editorial':
                continue
            s, tx, ty = transform(p.get('cam'), t - sc['start'], p['wh'], p.get('layout') or 'cobrir')
            esp = (tx, ty, tx + p['wh'][0] * s, ty + p['wh'][1] * s)
            if max(abs(a - b) for a, b in zip(esp, (g['x0'], g['y0'], g['x1'], g['y1']))) > 2:
                out.append({'codigo': 'G-ESPELHO', 'plano': g['cena'], 'inicio': round(t, 2),
                            'texto': f"palco ≠ espelho: {tuple(round(x) for x in esp)} × {(round(g['x0']), round(g['y0']), round(g['x1']), round(g['y1']))}"})
        t += 1 / fps
    return out


# ---------------------------------------------------------------- composição EDITORIAL (16/11)
# Para documento, mapa, gravura ou pintura horizontal que precisa ser vista inteira: em cima, a VISÃO GERAL na largura
# do quadro (a fonte inteira, sem cortar); embaixo, o DETALHE da informação principal ampliado, cobrindo o painel até o
# pé do quadro (a legenda fica sobre ele). Um marcador na visão geral mostra de onde vem o detalhe. Sem fundo vazio:
# os dois painéis ocupam o quadro todo, menos o filete entre eles. Mesmas contas em doc.js.
GAP_EDITORIAL = 16
VISAO_MAX = 0.55                       # a visão geral ocupa no máximo 55% da altura


def editorial(wh, visao=None, detalhe=None) -> dict:
    iw, ih = wh
    vx, vy, vw, vh = [v * d for v, d in zip(visao or [0, 0, 1, 1], (iw, ih, iw, ih))]
    s1 = min(W / vw, VISAO_MAX * H / vh)
    h1 = vh * s1
    ox = (W - vw * s1) / 2                              # se a fonte for alta demais, centraliza (filetes laterais)
    t1 = (ox - vx * s1, -vy * s1)
    y0 = h1 + GAP_EDITORIAL
    hd = H - y0
    dx, dy, dw, dh = [v * d for v, d in zip(detalhe or visao or [0, 0, 1, 1], (iw, ih, iw, ih))]
    cobre = max(W / iw, hd / ih)
    util = max(1.0, BARRA - y0)                         # parte do painel acima da legenda
    sd = min(W / dw, util / dh)
    sd = min(max(sd, cobre), max(cobre, SMAX))
    cx, cy = dx + dw / 2, dy + dh / 2
    tx = min(0.0, max(W - iw * sd, W / 2 - cx * sd))
    ty = min(y0, max(y0 + hd - ih * sd, (y0 + min(BARRA, H)) / 2 - cy * sd))
    janela = [(-tx) / sd / iw, (y0 - ty) / sd / ih, W / sd / iw, hd / sd / ih]
    return {'visao': {'s': s1, 'tx': t1[0], 'ty': t1[1], 'rect': [ox, 0.0, vw * s1, h1]},
            'detalhe': {'s': sd, 'tx': tx, 'ty': ty, 'rect': [0.0, y0, float(W), hd], 'janela': janela},
            'escala_util': max(s1, sd), 'resolucao_ok': sd <= SMAX * 1.12 or sd <= cobre * 1.001 and cobre <= SMAX * 1.12}


def ocupacao(params: dict, t: float) -> dict:
    """Fração do quadro coberta pela(s) imagem(ns) do plano em t, e a escala útil (px de tela por px da fonte, no
    painel mais ampliado: é a que decide se rótulos e texto são legíveis)."""
    wh, lay = params['wh'], params.get('layout') or 'cobrir'
    iw, ih = wh
    if lay == 'editorial':
        e = editorial(wh, params.get('visao_geral'), (params.get('cam') or [{'caixa': None}])[0].get('caixa'))
        area = sum(r[2] * r[3] for r in (e['visao']['rect'], e['detalhe']['rect']))
        return {'ocupacao': min(1.0, area / (W * H)), 'escala_util': e['escala_util'], 's': e['detalhe']['s'],
                'tx': e['detalhe']['tx'], 'ty': e['detalhe']['ty']}
    s, tx, ty = transform(params.get('cam'), t, wh, lay)
    area = max(0.0, min(W, tx + iw * s) - max(0.0, tx)) * max(0.0, min(H, ty + ih * s) - max(0.0, ty))
    return {'ocupacao': area / (W * H), 'escala_util': s, 's': s, 'tx': tx, 'ty': ty}


def visivel_em(caixa, o: dict, wh) -> float:
    """Fração da caixa (0–1 da imagem) que aparece no quadro com a transformação `o` (de ocupacao)."""
    iw, ih = wh
    s, tx, ty = o['s'], o['tx'], o['ty']
    x0, y0 = tx + caixa[0] * iw * s, ty + caixa[1] * ih * s
    x1, y1 = x0 + caixa[2] * iw * s, y0 + caixa[3] * ih * s
    a = max(1e-9, (x1 - x0) * (y1 - y0))
    return max(0.0, min(x1, W) - max(x0, 0)) * max(0.0, min(y1, H) - max(y0, 0)) / a
