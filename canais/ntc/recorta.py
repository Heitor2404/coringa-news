"""Recorta o fundo verde liso das imagens de personagem (gera PNG com transparência, cortado justo)."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

def recorta(src, dst, so_maior=False):
    im = np.asarray(Image.open(src).convert('RGB')).astype(float)
    borda = np.concatenate([im[:10].reshape(-1, 3), im[-10:].reshape(-1, 3), im[:, :10].reshape(-1, 3), im[:, -10:].reshape(-1, 3)])
    bg = np.median(borda, 0)
    d = np.sqrt(((im - bg) ** 2).sum(2))
    a = np.clip((d - 22) / 22, 0, 1)
    lab, n = ndimage.label(a > 0.5)
    tam = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = (lab == int(np.argmax(tam)) + 1) if so_maior else np.isin(lab, [i + 1 for i, s in enumerate(tam) if s > 0.002 * lab.size])
    keep = ndimage.binary_fill_holes(keep)
    a = np.where(keep, np.maximum(a, ndimage.binary_erosion(keep, iterations=2)), 0)
    # tira o verde que vaza na borda
    rgb = im.copy(); g = rgb[..., 1]; lim = np.maximum(rgb[..., 0], rgb[..., 2]); rgb[..., 1] = np.where(a < 1, np.minimum(g, lim + 8), g)
    ys, xs = np.nonzero(keep)
    out = np.dstack([rgb, a * 255]).astype(np.uint8)[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    Image.fromarray(out).save(dst, optimize=True)

if __name__ == '__main__':
    recorta(sys.argv[1], sys.argv[2])
