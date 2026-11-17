"""Mosaicos cartográficos para o palco do ATLAS (roda no Actions, onde há rede; o resultado é versionado com atribuição).

Para cada região (bbox lon/lat + zoom de tiles) gera, em Web Mercator alinhado aos tiles (encaixe exato no MapLibre):
  <nome>_fisico.jpg   mapa físico do Coringa: cor por altitude (terra) e por profundidade (mar) × sombreamento do relevo
  <nome>_satelite.jpg imagem orbital × sombreamento suave (Blue Marble NG no largo; Sentinel-2 cloudless 2016 no detalhe)
  <nome>.json         limites (cantos lon/lat), zoom, fontes, licenças e sha256 dos arquivos

Fontes (todas com uso comercial permitido; atribuição obrigatória na tela):
- relevo: Terrain Tiles (AWS Open Data / Mapzen; SRTM, GMTED2010, ETOPO1) — terrarium PNG
- satélite largo: NASA Blue Marble Next Generation (GIBS) — domínio público
- satélite detalhe: Sentinel-2 cloudless 2016 by EOX IT Services GmbH — CC BY 4.0 (só a edição 2016 é CC BY)
uso: python scripts/formatos_raster.py <saida_dir>
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageFilter

UA = {'User-Agent': 'CoringaExplica/formatos (render editorial; contato via GitHub Heitor2404)'}
DEM = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
BMNG = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_NextGeneration/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg'
S2 = 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2016_3857/default/g/{z}/{y}/{x}.jpg'
ATRIB = {
    'relevo': 'Relevo: Terrain Tiles (AWS Open Data/Mapzen; SRTM, GMTED2010, ETOPO1)',
    'bmng': 'Imagem: NASA Blue Marble Next Generation (domínio público)',
    's2': 'Sentinel-2 cloudless 2016 © EOX IT Services GmbH (CC BY 4.0; contém dados Copernicus Sentinel modificados 2016)',
}
REGIOES = {
    # nome: (oeste, sul, leste, norte), zoom dos tiles, fonte de satélite
    # o plano largo (istmo, z ≤ 7,5) vem do Natural Earth II local (scripts/formatos_ne2.py); aqui só o que exige rede
    'panama_canal': ((-80.45, 8.55, -79.15, 9.75), 11, 's2'),
    'gatun_eclusas': ((-79.97, 9.24, -79.88, 9.31), 14, 's2'),
    'miraflores_eclusas': ((-79.63, 8.98, -79.56, 9.04), 14, 's2'),
}


def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile_lonlat(x, y, z):
    n = 2 ** z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


def baixar(url, tent=4):
    for k in range(tent):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            if r.status_code == 200:
                return Image.open(io.BytesIO(r.content))
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1.5 * (k + 1))
    raise RuntimeError(f'falhou: {url}')


def mosaico(modelo, bbox, z, modo):
    o, s, l, n = bbox
    x0, y0 = tile_xy(o, n, z)
    x1, y1 = tile_xy(l, s, z)
    xs, ys = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
    out = Image.new(modo, (256 * len(xs), 256 * len(ys)))
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            im = baixar(modelo.format(z=z, x=x, y=y))
            if im is not None:
                out.paste(im.convert(modo).resize((256, 256)), (i * 256, j * 256))
    nw = tile_lonlat(xs.start, ys.start, z)
    se = tile_lonlat(xs.stop, ys.stop, z)
    return out, [[nw[0], nw[1]], [se[0], nw[1]], [se[0], se[1]], [nw[0], se[1]]]


def elevacao(im):
    a = np.asarray(im.convert('RGB'), dtype=np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def sombra(elev, z, lat):
    """hillshade (azimute 315°, altitude 45°) com exagero vertical para leitura em celular"""
    m_px = 156543.03 * math.cos(math.radians(lat)) / 2 ** z
    gy, gx = np.gradient(elev, m_px)
    exag = 2.2 if z >= 10 else 4.0
    slope = np.arctan(exag * np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(45)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    return np.clip(hs, 0, 1)


def rampa(v, pontos):
    xs = [p[0] for p in pontos]
    cs = np.array([p[1] for p in pontos], dtype=np.float32)
    return np.stack([np.interp(v, xs, cs[:, k]) for k in range(3)], axis=-1)


TERRA = [(0, (66, 92, 60)), (80, (78, 104, 66)), (300, (110, 118, 78)), (800, (146, 132, 96)), (1600, (176, 160, 128)), (3000, (214, 206, 188))]
MAR = [(-6000, (8, 20, 42)), (-3000, (12, 30, 58)), (-1000, (18, 44, 76)), (-200, (26, 62, 96)), (0, (40, 86, 120))]


def fisico(elev, hs):
    terra = elev > 0
    cor = np.where(terra[..., None], rampa(elev, TERRA), rampa(elev, MAR))
    luz = np.where(terra, .42 + .78 * hs, .78 + .3 * hs)[..., None]
    return np.clip(cor * luz, 0, 255).astype(np.uint8)


def satelite(img, elev, hs):
    a = np.asarray(img.convert('RGB'), dtype=np.float32)
    terra = (elev > 0)[..., None]
    luz = np.where(terra, .72 + .5 * hs[..., None], 1.0)
    a = a * luz
    # grade editorial: um pouco mais escuro e contido para cartões e destaques amarelos respirarem
    m = a.mean(axis=2, keepdims=True)
    a = m + (a - m) * .9
    return np.clip(a * .9, 0, 255).astype(np.uint8)


def main(saida: Path):
    saida.mkdir(parents=True, exist_ok=True)
    for nome, (bbox, z, fonte) in REGIOES.items():
        dem, cantos = mosaico(DEM, bbox, z, 'RGB')
        elev = elevacao(dem)
        lat = (bbox[1] + bbox[3]) / 2
        hs = sombra(elev, z, lat)
        Image.fromarray(fisico(elev, hs)).filter(ImageFilter.SMOOTH).save(saida / f'{nome}_fisico.jpg', quality=88, optimize=True)
        img, cantos2 = mosaico(BMNG if fonte == 'bmng' else S2, bbox, z if fonte == 's2' else min(z, 8), 'RGB')
        img = img.resize(dem.size, Image.LANCZOS)
        Image.fromarray(satelite(img, elev, hs)).save(saida / f'{nome}_satelite.jpg', quality=88, optimize=True)
        meta = {'nome': nome, 'bbox_pedido': bbox, 'zoom_tiles': z, 'cantos': cantos, 'px': list(dem.size),
                'fontes': {'fisico': [ATRIB['relevo']], 'satelite': [ATRIB[fonte], ATRIB['relevo']]},
                'sha256': {f'{nome}_{k}.jpg': hashlib.sha256((saida / f'{nome}_{k}.jpg').read_bytes()).hexdigest() for k in ('fisico', 'satelite')},
                'gerado': time.strftime('%Y-%m-%d')}
        (saida / f'{nome}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(nome, dem.size, cantos[0], cantos[2])


if __name__ == '__main__':
    main(Path(sys.argv[1]))
