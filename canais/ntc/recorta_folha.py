"""Recorta uma FOLHA de objetos do Flow (vários adesivos em fundo verde liso) em PNGs separados, sem o verde e sem a
borda branca de adesivo (objeto no chão do cenário não pode parecer adesivo).

Uso: python canais/ntc/recorta_folha.py folha.jpg pasta_saida nome1 nome2 ...   (nomes na ordem de leitura: linha a linha)
     python canais/ntc/recorta_folha.py --limpa adesivo.png saida.png   (só tira a borda de um PNG já recortado)
     --com-borda  mantém a borda branca
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage


def _alfa_verde(im):
    borda = np.concatenate([im[:10].reshape(-1, 3), im[-10:].reshape(-1, 3), im[:, :10].reshape(-1, 3), im[:, -10:].reshape(-1, 3)])
    bg = np.median(borda, 0)
    d = np.sqrt(((im - bg) ** 2).sum(2))
    return np.clip((d - 22) / 22, 0, 1)


def sem_borda(rgb, al):
    """Tira a borda branca de adesivo, o branco preso por dentro e o halo claro. rgb float HxWx3, al 0..1."""
    branco = (rgb.min(2) > 195) & (rgb.max(2) - rgb.min(2) < 35)
    fora = al < 0.5
    lb, _ = ndimage.label(fora | branco)
    ids = np.unique(lb[fora])
    tira = np.isin(lb, ids[ids > 0]) & branco
    lw, nw = ndimage.label(branco & ~tira)
    if nw:
        tw = ndimage.sum(np.ones_like(lw), lw, range(1, nw + 1))
        tira |= np.isin(lw, [k + 1 for k, t in enumerate(tw) if t > 150])
    tira = ndimage.binary_dilation(tira, iterations=2) & (rgb.min(2) > 140)
    al = np.where(tira, 0, al)
    T = al < 0.5
    claro = (rgb.min(2) > 110) & (rgb.max(2) - rgb.min(2) < 45)
    for _ in range(3):
        T = T | (ndimage.binary_dilation(T, iterations=1) & claro)
    al = np.where(T, 0, al)
    return ndimage.gaussian_filter(al, 0.6)


def limpa_png(src, dst):
    """PNG já recortado mas com borda de adesivo → sem borda, cortado justo."""
    a = np.asarray(Image.open(src).convert('RGBA')).astype(float)
    rgb, al = a[..., :3], a[..., 3] / 255
    al = sem_borda(rgb, al)
    out = np.dstack([rgb, np.clip(al, 0, 1) * 255]).astype(np.uint8)
    yy, xx = np.nonzero(out[..., 3] > 8)
    Image.fromarray(out[yy.min():yy.max() + 1, xx.min():xx.max() + 1]).save(dst, optimize=True)


def recorta_folha(src, saida, nomes, com_borda=False):
    im = np.asarray(Image.open(src).convert('RGB')).astype(float)
    a = _alfa_verde(im)
    lab, n = ndimage.label(ndimage.binary_closing(a > 0.5, iterations=3))
    tam = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    grandes = [i + 1 for i, s in enumerate(tam) if s > 0.004 * lab.size]
    fo = ndimage.find_objects(lab); caixas = {i: fo[i - 1] for i in grandes}
    # ordem de leitura: agrupa por linha (centro y) e depois x
    alt_med = np.median([c[0].stop - c[0].start for c in caixas.values()])
    ordem = sorted(grandes, key=lambda i: (round(((caixas[i][0].start + caixas[i][0].stop) / 2) / alt_med), caixas[i][1].start))
    if len(nomes) != len(ordem):
        raise SystemExit(f'achei {len(ordem)} objetos e recebi {len(nomes)} nomes')
    branco = (im.min(2) > 195) & (im.max(2) - im.min(2) < 35)   # branco/cinza claro sem cor
    saida = Path(saida); saida.mkdir(parents=True, exist_ok=True)
    for i, nome in zip(ordem, nomes):
        ys, xs = caixas[i]
        m = (lab[ys, xs] == i)
        al = a[ys, xs] * ndimage.binary_dilation(m, iterations=2)
        rgb = im[ys, xs].copy()
        if not com_borda:
            al = sem_borda(rgb, al)
        # tira o verde que vaza na borda
        g = rgb[..., 1]; lim = np.maximum(rgb[..., 0], rgb[..., 2]); rgb[..., 1] = np.where(al < 1, np.minimum(g, lim + 8), g)
        out = np.dstack([rgb, np.clip(al, 0, 1) * 255]).astype(np.uint8)
        yy, xx = np.nonzero(out[..., 3] > 8)
        out = out[yy.min():yy.max() + 1, xx.min():xx.max() + 1]
        Image.fromarray(out).save(saida / f'{nome}.png', optimize=True)
        print(nome, out.shape[1], 'x', out.shape[0])


if __name__ == '__main__':
    if sys.argv[1] == '--limpa':          # python recorta_folha.py --limpa entrada.png saida.png
        limpa_png(sys.argv[2], sys.argv[3]); sys.exit()
    args = [x for x in sys.argv[1:] if x != '--com-borda']
    recorta_folha(args[0], args[1], args[2:], com_borda='--com-borda' in sys.argv)
