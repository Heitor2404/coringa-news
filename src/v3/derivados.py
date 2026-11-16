"""Imagens DERIVADAS reutilizáveis (V3.1-resgate). Uma derivada é sempre do mesmo arquivo do acervo e aparece com o
crédito do original + 'derivado'."""
from __future__ import annotations

from pathlib import Path


def apagar_cor(img: Path, rgb: tuple[int, int, int], destino: Path, tol: int = 60, cinza: float = .35,
               preservar: list[list[float]] | None = None) -> Path:
    """Copia a imagem com os pixels próximos de `rgb` (a cor da legenda de um mapa, ex.: área queimada) trocados pelo
    cinza equivalente. Serve de BASE para `avanco` em doc.plano: a área aparece em cor só onde/quando a etapa chega,
    e nada além da área marcada no próprio mapa ganha cor."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(img).convert('RGB')).astype(np.int16)
    d = np.abs(a - np.array(rgb, dtype=np.int16)).sum(axis=2)
    m = d <= tol
    h, w = m.shape
    for x, y, bw, bh in preservar or []:               # ex.: a legenda do mapa continua na cor original
        m[int(y * h):int((y + bh) * h), int(x * w):int((x + bw) * w)] = False
    g = (a.mean(axis=2, keepdims=True) * cinza + 205 * (1 - cinza)).clip(0, 255)     # cinza claro, como o fundo do mapa
    out = np.where(m[..., None], np.repeat(g, 3, axis=2), a).astype(np.uint8)
    Image.fromarray(out).save(destino, quality=92)
    return destino
