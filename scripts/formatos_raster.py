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
# Blue Marble com relevo sombreado e BATIMETRIA (oceano com plataforma continental visível, como a imagem da referência)
BMNG_BATI = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg'
# 2016 = camada 's2cloudless_3857' (a ÚNICA edição CC BY 4.0; 2018+ são CC BY-NC-SA → proibidas em vídeo monetizado)
S2 = 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg'
ATRIB = {
    'relevo': 'Relevo: Terrain Tiles (AWS Open Data/Mapzen; SRTM, GMTED2010, ETOPO1)',
    'bmng': 'Imagem: NASA Blue Marble Next Generation (domínio público)',
    'bmng_bati': 'Imagem: NASA Blue Marble (relevo sombreado + batimetria), via GIBS (domínio público)',
    's2': 'Sentinel-2 cloudless - https://s2maps.eu by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2016 & 2017) · CC BY 4.0',
}
REGIOES = {
    # nome: (oeste, sul, leste, norte), zoom dos tiles, fonte de satélite
    # o plano largo (istmo, z ≤ 7,5) vem do Natural Earth II local (scripts/formatos_ne2.py); aqui só o que exige rede
    'panama_canal': ((-80.45, 8.55, -79.15, 9.75), 11, 's2'),
    'gatun_eclusas': ((-79.97, 9.24, -79.88, 9.31), 14, 's2'),
    'miraflores_eclusas': ((-79.63, 8.98, -79.56, 9.04), 14, 's2'),
    # escala continental (calibração com a referência A: China e entorno)
    'asia_continente': ((52.0, -22.0, 168.0, 76.0), 6, 'bmng_bati'),
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
    falta = 0
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            im = baixar(modelo.format(z=z, x=x, y=y))
            if im is None:
                falta += 1
                continue
            out.paste(im.convert(modo).resize((256, 256)), (i * 256, j * 256))
    if falta:   # mosaico com buraco NUNCA vira palco (a coleta 44097219552 gerou satélite preto sem avisar)
        raise RuntimeError(f'{falta}/{len(xs) * len(ys)} tiles ausentes em {modelo.split("/")[2]} z{z}')
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


def main(saida: Path, so: list[str] | None = None):
    saida.mkdir(parents=True, exist_ok=True)
    for nome, (bbox, z, fonte) in REGIOES.items():
        if so and nome not in so:
            continue
        dem, cantos = mosaico(DEM, bbox, z, 'RGB')
        elev = elevacao(dem)
        lat = (bbox[1] + bbox[3]) / 2
        hs = sombra(elev, z, lat)
        Image.fromarray(fisico(elev, hs)).filter(ImageFilter.SMOOTH).save(saida / f'{nome}_fisico.jpg', quality=88, optimize=True)
        img, cantos2 = mosaico({'bmng': BMNG, 'bmng_bati': BMNG_BATI}.get(fonte, S2), bbox, z if fonte == 's2' else min(z, 8), 'RGB')
        img = img.resize(dem.size, Image.LANCZOS)
        img.save(saida / f'{nome}_bruto.jpg', quality=92)          # sem grade: a grade final é calibrada contra a referência
        Image.fromarray(satelite(img, elev, hs)).save(saida / f'{nome}_satelite.jpg', quality=88, optimize=True)
        meta = {'nome': nome, 'bbox_pedido': bbox, 'zoom_tiles': z, 'cantos': cantos, 'px': list(dem.size),
                'fontes': {'fisico': [ATRIB['relevo']], 'satelite': [ATRIB[fonte], ATRIB['relevo']]},
                'sha256': {f'{nome}_{k}.jpg': hashlib.sha256((saida / f'{nome}_{k}.jpg').read_bytes()).hexdigest() for k in ('fisico', 'satelite')},
                'gerado': time.strftime('%Y-%m-%d')}
        (saida / f'{nome}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(nome, dem.size, cantos[0], cantos[2])


if __name__ == '__main__':
    main(Path(sys.argv[1]))


def acabamento(jpg: Path, gama: float = .78, sat: float = 1.18, borda: float = .07) -> Path:
    """grade final do satélite para o palco (mais luz nos médios, cor um pouco mais viva) e BORDA SUAVE em alfa:
    o recorte detalhado se funde ao relevo largo por baixo, sem a aresta do retângulo aparecer (WebP com alfa)"""
    a = np.asarray(Image.open(jpg).convert('RGB'), dtype=np.float32) / 255
    a = a ** gama
    m = a.mean(axis=2, keepdims=True)
    a = np.clip(m + (a - m) * sat, 0, 1)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum.reduce([xx / w, (w - 1 - xx) / w, yy / h, (h - 1 - yy) / h])
    alfa = np.clip(d / borda, 0, 1) ** 1.5
    rgba = np.dstack([a * 255, alfa * 255]).astype(np.uint8)
    out = jpg.with_suffix('.webp')
    Image.fromarray(rgba, 'RGBA').save(out, 'WEBP', quality=86, method=6)
    return out


NE_LAND = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_10m_land.geojson'


def _terras_ne(bbox, cache_dir):
    """Natural Earth 10 m land polygons (public domain) intersecting bbox; cached file outside Git."""
    cache = Path(cache_dir) / '_ne_10m_land.geojson'
    if not cache.is_file():
        r = requests.get(NE_LAND, headers=UA, timeout=120); r.raise_for_status(); cache.write_bytes(r.content)
    o, s, l, n = bbox
    out = []
    for f in json.loads(cache.read_text())['features']:
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            ring = poly[0]
            xs = [c[0] for c in ring]; ys = [c[1] for c in ring]
            if max(xs) >= o and min(xs) <= l and max(ys) >= s and min(ys) <= n:
                out.append(ring)
    return out


def compor_oceano(s2, tile0, z, aneis, oceano, *, lat_ref, buffer_m=1500.):
    """Keep Sentinel-2 over land + a coastal buffer; elsewhere use the bathymetric ocean base.

    E284 diagnosis (Kilauea, raw EOX tiles): s2cloudless only images a coastal strip of ocean; beyond it EOX
    composites a different dark ocean, which shows as a CURVED border (and swath seams) in the raw tiles themselves.
    The bathymetric Blue Marble base already used at lower ATLAS zooms is the geographically consistent ocean.
    `tile0` = (x0, y0) integer tile origin of the mosaic; rings are lon/lat land polygons (Natural Earth 10 m).
    """
    from PIL import ImageDraw
    w, h = s2.size
    mask = Image.new('L', (w, h), 0); d = ImageDraw.Draw(mask)
    for ring in aneis:
        pts = []
        for lon, lat in ring:
            lat = max(-85.0, min(85.0, lat))
            x, y = tile_xy(lon, lat, z)
            pts.append(((x - tile0[0]) * 256, (y - tile0[1]) * 256))
        if len(pts) >= 3:
            d.polygon(pts, fill=255)
    mpp = 156543.03392 * math.cos(math.radians(lat_ref)) / 2 ** z
    raio = max(1.0, buffer_m / mpp)
    dil = np.asarray(mask.filter(ImageFilter.GaussianBlur(raio)), np.float32) > 4      # coastal buffer
    alfa = Image.fromarray((dil * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(1.0, raio / 2)))
    a = (np.asarray(alfa, np.float32) / 255)[..., None]
    out = np.asarray(s2.convert('RGB'), np.float32) * a + np.asarray(oceano.convert('RGB').resize((w, h), Image.BICUBIC), np.float32) * (1 - a)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), float((np.asarray(mask) > 0).mean())


def _oceano_bmng(bbox_tiles, z):
    """Bathymetric Blue Marble (max z8) covering exactly the S2 mosaic extent."""
    zb = min(8, z)
    nw, se = bbox_tiles
    img, cantos = mosaico(BMNG_BATI, [nw[0], se[1], se[0], nw[1]], zb, 'RGB')
    bx0, by0 = tile_xy(cantos[0][0], cantos[0][1], zb)
    ax, ay = tile_xy(nw[0], nw[1], zb); bx, by = tile_xy(se[0], se[1], zb)
    box = ((ax - bx0) * 256, (ay - by0) * 256, (bx - bx0) * 256, (by - by0) * 256)
    return img.crop(tuple(int(round(v)) for v in box))


def registrar_base_regional(nome, bbox, z, dataset, *, saida=None, max_tiles=100, oceano=None):
    """Acquire a parameterized native raster, not an episode-specific template.

    No upsampled resolution claims. Only sources already in the ATLAS
    attribution manifest; the returned metadata remains a technical candidate.
    DEM shading is deliberately separate: regional DEM provenance must be
    checked before combining additional elevation sources.
    """
    import re
    from src.v4.formatos import plano as A, atlas_ref
    if not isinstance(nome,str) or not re.fullmatch(r'[a-z0-9_]{1,80}',nome):
        raise ValueError('GEO-NOME')
    if not isinstance(bbox,(tuple,list)) or len(bbox)!=4 or not all(
        isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in bbox):
        raise ValueError('GEO-BBOX')
    o,s,l,n=bbox
    if not -180<=o<l<180 or not -85<=s<n<=85:
        raise ValueError('GEO-BBOX: dividir antimeridiano explicitamente')
    fontes={'bmng':(BMNG_BATI,4,8),'s2_2016':(S2,4,14)}
    if dataset not in fontes:
        raise ValueError('GEO-DATASET')
    modelo,zmin,zmax=fontes[dataset]
    lic=atlas_ref.datasets().get(dataset,{})
    if not lic.get('uso_comercial') or not lic.get('atribuicao_exigida') or atlas_ref.proibido(modelo):
        raise ValueError('GEO-LICENCA')
    if type(z) is not int or not zmin<=z<=zmax:
        raise ValueError('GEO-ZOOM')
    if type(max_tiles) is not int or not 1<=max_tiles<=100:
        raise ValueError('GEO-ORCAMENTO')
    x0,y0=tile_xy(o,n,z);x1,y1=tile_xy(l,s,z)
    count=(int(x1)-int(x0)+1)*(int(y1)-int(y0)+1)
    if count>max_tiles:raise ValueError('GEO-ORCAMENTO: reduzir região ou zoom')
    out = Path(saida) if saida is not None else A.RASTER_DIR
    out.mkdir(parents=True, exist_ok=True)
    img = out / (nome + '.jpg')
    receipt = out / (nome + '.json')
    px = [256 * (int(x1) - int(x0) + 1), 256 * (int(y1) - int(y0) + 1)]
    nw = tile_lonlat(int(x0), int(y0), z)
    se = tile_lonlat(int(x1) + 1, int(y1) + 1, z)
    corners = [list(nw), [se[0], nw[1]], list(se), [nw[0], se[1]]]
    composicao = (oceano == 'batimetria' and dataset == 's2_2016')
    meta = {'nome': nome, 'tipo': 'satelite', 'cantos': corners, 'px': px,
            **({'oceano': 'bmng_batimetria+ne_10m_land', 'buffer_costeiro_m': 1500} if composicao else {}),
            'px_por_grau_fonte': 256*2**z/360, 'arquivo': img.name, 'dataset': dataset,
            'atribuicao': lic['atribuicao_exigida'] + (' · ' + atlas_ref.datasets()['bmng']['atribuicao_exigida'] + ' · Natural Earth' if composicao else ''),
            'fonte': {'url': modelo, 'licenca': lic['licenca'], 'zoom_tiles': z,
                      'bbox_pedido': list(bbox), 'tiles': count,
                      'escopo': 'base de referência; não comprova estado histórico'}}
    try:
        saved = json.loads(receipt.read_text(encoding='utf8'))
        if isinstance(saved, dict) and all(saved.get(k) == v for k, v in meta.items()):
            digest = hashlib.sha256(img.read_bytes()).hexdigest()
            if digest == saved.get('sha256'):
                with Image.open(img) as existing:
                    if existing.format == 'JPEG' and list(existing.size) == px:
                        existing.load()
                        return saved
    except (OSError, ValueError):
        pass
    im, observed = mosaico(modelo, bbox, z, 'RGB')
    if list(im.size) != px or [list(point) for point in observed] != corners:
        raise ValueError('GEO-MOSAICO')
    if composicao:
        aneis = _terras_ne(bbox, out)
        mar = _oceano_bmng((nw, se), z)
        im, fracao_terra = compor_oceano(im, (int(x0), int(y0)), z, aneis, mar, lat_ref=(nw[1] + se[1]) / 2)
        meta['fracao_terra'] = round(fracao_terra, 4)
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(dir=out, suffix='.jpg', delete=False) as temp:
        pending = Path(temp.name)
    try:
        im.save(pending, quality=94)
        meta['sha256'] = hashlib.sha256(pending.read_bytes()).hexdigest()
        pending.replace(img)
    finally:
        pending.unlink(missing_ok=True)
    with NamedTemporaryFile('w', dir=out, encoding='utf8', delete=False) as temp:
        json.dump(meta, temp, ensure_ascii=False, indent=2)
    Path(temp.name).replace(receipt)
    return meta
