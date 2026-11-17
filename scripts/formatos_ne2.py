"""Base cartográfica do plano largo do ATLAS: Natural Earth II (relevo sombreado + cobertura do solo + fundo do mar),
reprojetada para Web Mercator (encaixe exato numa fonte `image` do MapLibre) e com a grade de cor do canal.

Fonte: NE2_HR_LC_SR_W (1′, 21600×10800), domínio público (naturalearthdata.com/about/terms-of-use). O arquivo bruto
(700 MB) NÃO é versionado: registra-se URL + sha256 de origem no .json, e o recorte gerado vai para o repositório.
uso: python scripts/formatos_ne2.py <NE2_HR_LC_SR_W.tif> <nome> <oeste> <sul> <leste> <norte> [canal]
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

RAIZ = Path(__file__).resolve().parents[1]
DEST = RAIZ / 'motor4' / 'formatos' / 'dados' / 'raster'
ORIGEM = 'https://raw.githubusercontent.com/nvkelso/natural-earth-raster/master/10m_rasters/NE2_HR_LC_SR_W/NE2_HR_LC_SR_W.tif'
PX_GRAU = 60          # resolução da fonte (1 minuto de arco)
SUPER = 2             # superamostragem Lanczos antes do MapLibre (interpolação linear dele fica menos mole)


def merc_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def lat_de(y):
    return math.degrees(2 * math.atan(math.exp(y)) - math.pi / 2)


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def grade(a: np.ndarray, tons: dict) -> np.ndarray:
    """mar: luminância do fundo oceânico do NE2 → rampa escura do canal (o relevo submarino continua visível);
    terra: cor natural do NE2 levemente contida, para cartões e destaques respirarem"""
    a = a.astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # máscara SUAVE do mar (borda da costa sem serrilhado): azul dominante → 1, terra → 0
    mar = np.clip((b - r - 14) / 26, 0, 1) * np.clip((b - g + 6) / 12, 0, 1)
    mar = np.asarray(Image.fromarray((mar * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32) / 255
    lum = (.30 * r + .59 * g + .11 * b) / 255
    # normaliza a luminância do mar (o NE2 varia ~0,45–0,75) e aplica a rampa fundo → raso
    k = np.clip((lum - .38) / .42, 0, 1) ** 1.25
    fundo, raso = hexrgb(tons['mar_fundo']), hexrgb(tons['mar_raso'])
    cor_mar = fundo + (raso - fundo) * k[..., None]
    m = a.mean(axis=2, keepdims=True)
    terra = (m + (a - m) * tons.get('sat_terra', 1.0)) * tons.get('luz_terra', .9)
    terra = 128 + (terra - 128) * tons.get('contraste_terra', 1.0)
    out = cor_mar * mar[..., None] + terra * (1 - mar[..., None])
    return np.clip(out, 0, 255).astype(np.uint8)


def main(tif: Path, nome: str, o: float, s: float, l: float, n: float, canal: str = 'coringa'):
    tons = json.loads((RAIZ / 'src' / 'v4' / 'formatos' / 'canais' / f'{canal}.json').read_text())['palco']['raster']
    Image.MAX_IMAGE_PIXELS = None
    src = Image.open(tif)
    x0, x1 = int((o + 180) * PX_GRAU), int((l + 180) * PX_GRAU)
    y0, y1 = int((90 - n) * PX_GRAU), int((90 - s) * PX_GRAU)
    eq = np.asarray(src.crop((x0, y0, x1, y1)).convert('RGB'))
    lon0, lon1 = x0 / PX_GRAU - 180, x1 / PX_GRAU - 180
    lat_n, lat_s = 90 - y0 / PX_GRAU, 90 - y1 / PX_GRAU
    W = (x1 - x0) * SUPER
    ym_n, ym_s = merc_y(lat_n), merc_y(lat_s)
    H = int(round(W * (ym_n - ym_s) / math.radians(lon1 - lon0)))
    # linha de saída (Mercator) → linha da fonte (equirretangular), interpolação linear entre linhas
    ys = np.array([lat_de(ym_n - (ym_n - ym_s) * (j + .5) / H) for j in range(H)])
    fy = np.clip((lat_n - ys) * PX_GRAU - .5, 0, eq.shape[0] - 1.001)
    j0 = fy.astype(int)
    t = (fy - j0)[:, None, None]
    merc = eq[j0] * (1 - t) + eq[j0 + 1] * t
    im = Image.fromarray(merc.astype(np.uint8)).resize((W, H), Image.LANCZOS)
    im = Image.fromarray(grade(np.asarray(im), tons)).filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    DEST.mkdir(parents=True, exist_ok=True)
    arq = DEST / f'{nome}.jpg'
    im.save(arq, quality=90, optimize=True, progressive=True)
    meta = {'nome': nome, 'tipo': 'fisico', 'cantos': [[lon0, lat_n], [lon1, lat_n], [lon1, lat_s], [lon0, lat_s]], 'px': [W, H],
            'px_por_grau_fonte': PX_GRAU, 'canal': canal,
            'fonte': {'arquivo': 'NE2_HR_LC_SR_W.tif', 'url': ORIGEM, 'sha256': hashlib.sha256(tif.read_bytes()).hexdigest(),
                      'licenca': 'Domínio público (Natural Earth, naturalearthdata.com/about/terms-of-use)'},
            'atribuicao': 'Relevo: Natural Earth II (domínio público)',
            'sha256': hashlib.sha256(arq.read_bytes()).hexdigest(), 'gerado': time.strftime('%Y-%m-%d')}
    (DEST / f'{nome}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(nome, W, H, meta['cantos'][0], meta['cantos'][2])


if __name__ == '__main__':
    a = sys.argv
    main(Path(a[1]), a[2], *map(float, a[3:7]), *(a[7:8] or []))
