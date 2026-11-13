"""Medição horizontal (V2.2). Usa V2.medirCentros() do palco (caixa e glifos por elemento) e, independente do DOM,
o centro dos pixels de texto numa faixa da imagem renderizada (vale para o quadro 1080×1920 e para a prévia 540×960)."""
from __future__ import annotations

import numpy as np
from PIL import Image

TOL_CAIXA = 20.0     # critério da ordem V2.2 (px em 1080): desvio máximo do centro do contêiner
TOL_GLIFOS = 20.0    # idem para o centro da área ocupada pelos glifos


def medir(pg, dur: float, passo: float = .25) -> list[dict]:
    """Amostra a cena inteira; por elemento, guarda o PIOR desvio (inclui quadros de animação)."""
    t, el = passo / 2, {}
    while t < dur:
        pg.evaluate(f'seek({t:.3f})')
        for m in pg.evaluate('V2.medirCentros()'):
            k = (m['comp'], m['g'], m['texto'] if m['g'] == 'legenda' else '')
            d = max(abs(m['desvio_caixa']), abs(m['desvio_glifos']))
            if k not in el or d > el[k]['_d']:
                el[k] = {**m, 't': round(t, 2), '_d': d}
        t += passo
    return list(el.values())


def violacoes(medidas: list[dict]) -> dict:
    """centro_fora: declarado (ou legenda) fora da tolerância; sem_intencao: texto centralizado que não declara se é
    centro de tela (data-centro) ou centro local de um objeto (data-alinhamento='local')."""
    fora = [m for m in medidas if m['declarado'] and (abs(m['desvio_caixa']) > TOL_CAIXA or abs(m['desvio_glifos']) > TOL_GLIFOS)]
    sem = [m for m in medidas if m['alinhamento'] == 'centro' and not m['declarado'] and not m.get('intencao')]
    return {'centro_fora': fora, 'sem_intencao': sem}


def centro_pixels(img: str | Image.Image, y0: int, y1: int, limiar: int = 170) -> dict | None:
    """Centro horizontal dos pixels claros (texto) na faixa [y0, y1) — coordenadas da própria imagem."""
    im = img if isinstance(img, Image.Image) else Image.open(img)
    a = np.asarray(im.convert('RGB'), dtype=np.int16)[y0:y1]
    lum = a.max(axis=2)                       # branco e amarelo contam como texto
    cols = np.where((lum > limiar).sum(axis=0) > 0)[0]
    if not len(cols):
        return None
    w = im.size[0]
    return {'x0': int(cols[0]), 'x1': int(cols[-1]), 'centro': (cols[0] + cols[-1]) / 2, 'alvo': (w - 1) / 2, 'desvio': (cols[0] + cols[-1]) / 2 - (w - 1) / 2}
