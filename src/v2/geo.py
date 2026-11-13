"""Recorte das camadas do Natural Earth (domínio público) para um mapa V2.

O MapLibre recebe só o que cai no enquadramento (com folga): uma página com 20 MB de GeoJSON demoraria segundos por
quadro. Camadas em src/render/v2/dados/ne (scripts/v2_natural_earth.py).
"""
import json
from functools import lru_cache
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1] / 'render' / 'v2' / 'dados' / 'ne'


@lru_cache(maxsize=None)
def camada(nome: str) -> list[dict]:
    arq = PASTA / f'{nome}.json'
    if not arq.exists():
        raise FileNotFoundError(f"{arq} não existe: rode  python scripts/v2_natural_earth.py")
    feats = json.loads(arq.read_text(encoding='utf-8'))['features']
    for f in feats:
        f['_bb'] = _bbox(f['geometry']['coordinates'])
    return feats


def _bbox(c):
    xs, ys = [], []

    def anda(v):
        if not v:
            return
        if isinstance(v[0], (int, float)):
            xs.append(v[0]); ys.append(v[1])
        else:
            for x in v:
                anda(x)
    anda(c)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (999, 999, 999, 999)


def _cruza(a, b) -> bool:
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def caixa_de(pontos: list[tuple[float, float]], folga: float = 0.35, minimo: float = 1.0) -> tuple:
    xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
    w, h = max(max(xs) - min(xs), minimo), max(max(ys) - min(ys), minimo)
    # limita ao mundo projetável (Web Mercator corta em ±85°): folga grande não pode virar caixa além dos polos
    return (max(-180.0, min(xs) - w * folga), max(-80.0, min(ys) - h * folga), min(180.0, max(xs) + w * folga), min(84.0, max(ys) + h * folga))


def pais(nome: str) -> dict | None:
    """Acha um país pelo nome (português ou inglês) ou código ISO A3."""
    n = (nome or '').strip().lower()
    for f in camada('paises'):
        p = f['properties']
        if n in {str(p.get('name', '')).lower(), str(p.get('name_pt', '')).lower(), str(p.get('adm0_a3', '')).lower()}:
            return f
    return None


def recorte(bb: tuple, extra: float = 1.0) -> dict:
    """FeatureCollections das camadas que cruzam a caixa (lon0, lat0, lon1, lat1) ampliada por `extra`."""
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    big = (bb[0] - w * extra, max(-85, bb[1] - h * extra), bb[2] + w * extra, min(85, bb[3] + h * extra))
    regional = w < 40
    def fc(nome, filtro=None):
        out = []
        for f in camada(nome):
            if _cruza(f['_bb'], big) and (not filtro or filtro(f['properties'])):
                out.append({'type': 'Feature', 'properties': f['properties'], 'geometry': f['geometry']})
        return {'type': 'FeatureCollection', 'features': out}
    zoom_aprox = 0 if w <= 0 else max(0.0, min(12.0, __import__('math').log2(360 / max(w, 1e-3))))
    rank_max = 3 + int(zoom_aprox)                    # mais detalhe quanto mais perto
    return {
        'paises': fc('paises10' if regional else 'paises'),
        'lagos': fc('lagos', lambda p: (p.get('scalerank') or 0) <= rank_max + 2) if regional else fc('lagos', lambda p: (p.get('scalerank') or 0) <= 2),
        'rios': fc('rios', lambda p: (p.get('scalerank') or 0) <= rank_max + 1),
        'cidades': fc('cidades', lambda p: (p.get('scalerank') or 0) <= rank_max),
        'mares': fc('mares', lambda p: (p.get('scalerank') or 0) <= (rank_max if regional else 2)),
        'regioes': fc('regioes', lambda p: (p.get('scalerank') or 0) <= 2) if not regional else {'type': 'FeatureCollection', 'features': []},
    }


# ---------------- validação geográfica (V2.1) ----------------
def _no_poligono(lon: float, lat: float, geom: dict) -> bool:
    polis = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    for pol in polis:
        dentro = False
        anel = pol[0]
        j = len(anel) - 1
        for i in range(len(anel)):
            xi, yi = anel[i][0], anel[i][1]
            xj, yj = anel[j][0], anel[j][1]
            if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi:
                dentro = not dentro
            j = i
        if dentro:
            return True
    return False


def em_terra(lon: float, lat: float) -> str | None:
    """Nome do país (Natural Earth 1:50m) que contém o ponto, ou None (mar)."""
    for f in camada('paises'):
        b = f['_bb']
        if b[0] <= lon <= b[2] and b[1] <= lat <= b[3] and _no_poligono(lon, lat, f['geometry']):
            return f['properties'].get('name_pt') or f['properties'].get('name')
    return None


def mares_em(lon: float, lat: float) -> list[str]:
    """Nomes (inglês, Natural Earth) dos polígonos marinhos que contêm o ponto. Teste plano (par-ímpar), que não depende
    do sentido dos anéis: serve de verificação independente do d3 esférico usado no palco."""
    return [f['properties'].get('name') for f in camada('mares')
            if f['_bb'][0] <= lon <= f['_bb'][2] and f['_bb'][1] <= lat <= f['_bb'][3] and _no_poligono(lon, lat, f['geometry'])]


def coordenadas_validas(pontos: list[dict]) -> list[str]:
    erros = []
    for p in pontos:
        try:
            lon, lat = float(p['lon']), float(p['lat'])
        except (KeyError, TypeError, ValueError):
            erros.append(f"{p.get('nome', '?')}: coordenada ausente ou não numérica")
            continue
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            erros.append(f"{p.get('nome', '?')}: coordenada fora do globo ({lon}, {lat})")
        elif p.get('pais'):
            alvo = pais(p['pais'])
            if alvo and not _no_poligono(lon, lat, alvo['geometry']):
                # tolera ponto costeiro: 0,15° de folga
                if not any(_no_poligono(lon + dx, lat + dy, alvo['geometry']) for dx in (-.15, 0, .15) for dy in (-.15, 0, .15)):
                    erros.append(f"{p.get('nome', '?')}: ({lon}, {lat}) não fica em {p['pais']}")
    return erros


def validar_rota(rota: list, tipo: str = 'maritima', passo_km: float = 60) -> dict:
    """Amostra a rota (círculo máximo entre os vértices) e mede quanto passa sobre terra. Rota marítima com mais de 3%
    do comprimento sobre terra (fora das pontas) é incoerente. 'canal' e 'terrestre'/'aerea' não são checadas assim."""
    import math
    def hav(a, b):
        r = math.pi / 180
        h = math.sin((b[1] - a[1]) * r / 2) ** 2 + math.cos(a[1] * r) * math.cos(b[1] * r) * math.sin((b[0] - a[0]) * r / 2) ** 2
        return 2 * 6371 * math.asin(math.sqrt(h))
    amostras, total = [], 0.0
    for a, b in zip(rota, rota[1:]):
        d = hav(a, b)
        total += d
        n = max(1, int(d / passo_km))
        for k in range(n):
            amostras.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    if tipo != 'maritima' or len(amostras) < 4:
        return {'ok': True, 'km': round(total), 'em_terra': 0.0, 'paises': []}
    miolo = amostras[2:-2]
    terra = [(x, em_terra(*x)) for x in miolo]
    sobre = [t for t in terra if t[1]]
    frac = len(sobre) / max(1, len(miolo))
    return {'ok': frac <= .03, 'km': round(total), 'em_terra': round(frac, 3), 'paises': sorted({t[1] for t in sobre})}
