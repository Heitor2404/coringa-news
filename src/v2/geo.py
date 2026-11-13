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
    return (min(xs) - w * folga, min(ys) - h * folga, max(xs) + w * folga, max(ys) + h * folga)


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
