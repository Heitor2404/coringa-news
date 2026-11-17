"""Textura da MESA do DOSSIÊ (madeira escura com veio), gerada uma vez e servida como imagem estática.
O filtro SVG feTurbulence por quadro estourou 30 min de render no Actions (44114805861); a imagem é idêntica a cada
quadro e custa nada. Determinística (semente fixa), sem fonte externa.
uso: python scripts/formatos_mesa.py"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

RAIZ = Path(__file__).resolve().parents[1]
W, H = 1200, 2040


def ruido(rng, w, h, cx, cy):
    """ruído suave anisotrópico: grade pequena aleatória ampliada (veio comprido na horizontal)"""
    g = rng.random((max(2, h // cy), max(2, w // cx))).astype(np.float32)
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255


def main():
    rng = np.random.default_rng(7)
    v = sum(a * ruido(rng, W, H, cx, cy) for a, cx, cy in [(.5, 300, 9), (.25, 120, 4), (.15, 40, 2), (.1, 12, 1)])
    v = (v - v.min()) / (v.max() - v.min())
    anel = .5 + .5 * np.sin(v * 38)                      # anéis/veios
    poro = rng.random((H, W)).astype(np.float32)
    base = np.array([26, 18, 12], np.float32)
    claro = np.array([58, 38, 24], np.float32)
    k = (.55 * v + .35 * anel + .10 * poro)[..., None]
    img = base + (claro - base) * k
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6)).convert('RGBA')
    # objetos de cena FORA DE FOCO (profundidade): pasta embaixo à esquerda, folhas em cima à direita, régua embaixo
    for (x, y, w, h, cor, ang, borr) in [(-60, 1480, 640, 470, (52, 43, 27), -9, 6), (820, 220, 520, 680, (52, 50, 45), 11, 7),
                                          (880, 1560, 520, 70, (63, 54, 37), -22, 5)]:
        cam = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        obj = Image.new('RGBA', (w, h), cor + (255,))
        sombra = Image.new('RGBA', (w, h), (0, 0, 0, 150))
        cam.alpha_composite(sombra.rotate(ang, expand=True), (x + 10, y + 30))
        cam.alpha_composite(obj.rotate(ang, expand=True), (x, y))
        im.alpha_composite(cam.filter(ImageFilter.GaussianBlur(borr)))
    im = im.convert('RGB')
    out = RAIZ / 'motor4' / 'remotion' / 'public' / 'formatos' / 'mesa_madeira.jpg'
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=88)
    print(out, out.stat().st_size)


if __name__ == '__main__':
    main()
