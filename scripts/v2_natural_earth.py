"""Baixa e compacta as camadas do Natural Earth usadas pelos mapas V2 (domínio público, naturalearthdata.com).

Fonte: github.com/nvkelso/natural-earth-vector (GeoJSON oficial, v5.x). Saída: src/render/v2/dados/ne/*.json
(fora do Git: .gitignore). Coordenadas arredondadas e só os campos que o mapa usa (nomes em português quando existem).
Uso: python scripts/v2_natural_earth.py   (idempotente; o CI roda antes dos testes de mapa)
"""
import json, sys
from pathlib import Path
import requests

BASE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/'
SAIDA = Path(__file__).resolve().parents[1] / 'src' / 'render' / 'v2' / 'dados' / 'ne'
# camada: (arquivo, casas decimais, campos mantidos, filtro)
CAMADAS = {
    'paises': ('ne_50m_admin_0_countries.geojson', 3, ['NAME', 'NAME_PT', 'ADM0_A3', 'CONTINENT', 'LABEL_X', 'LABEL_Y'], None),
    'paises10': ('ne_10m_admin_0_countries.geojson', 3, ['NAME', 'NAME_PT', 'ADM0_A3'], None),
    'lagos': ('ne_10m_lakes.geojson', 4, ['name', 'name_pt', 'scalerank'], lambda p: (p.get('scalerank') or 9) <= 9),
    'rios': ('ne_10m_rivers_lake_centerlines.geojson', 3, ['name', 'name_pt', 'scalerank'], lambda p: (p.get('scalerank') or 9) <= 9),
    'cidades': ('ne_10m_populated_places_simple.geojson', 3, ['name', 'nameascii', 'adm0name', 'pop_max', 'scalerank', 'featurecla'], None),
    'mares': ('ne_10m_geography_marine_polys.geojson', 2, ['name', 'name_pt', 'featurecla', 'scalerank', 'label'], None),
    'regioes': ('ne_50m_geography_regions_points.geojson', 2, ['name', 'name_pt', 'featurecla', 'scalerank'], None),
}


def _arred(c, n):
    if isinstance(c, (int, float)):
        return round(c, n)
    return [_arred(x, n) for x in c]


def baixar(nome: str, forcar: bool = False) -> Path:
    arq, casas, campos, filtro = CAMADAS[nome]
    dest = SAIDA / f'{nome}.json'
    if dest.exists() and not forcar:
        return dest
    r = requests.get(BASE + arq, timeout=300)
    r.raise_for_status()
    gj = r.json()
    feats = []
    for f in gj['features']:
        p = {k.lower(): v for k, v in (f.get('properties') or {}).items()}
        if filtro and not filtro(p):
            continue
        if not f.get('geometry'):
            continue
        feats.append({'type': 'Feature', 'properties': {k.lower(): p.get(k.lower()) for k in campos},
                      'geometry': {'type': f['geometry']['type'], 'coordinates': _arred(f['geometry']['coordinates'], casas)}})
    SAIDA.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, separators=(',', ':')),
                    encoding='utf-8')
    return dest


if __name__ == '__main__':
    for n in CAMADAS:
        p = baixar(n, '--forcar' in sys.argv)
        print(f'{n:9s} {p.stat().st_size/1e6:6.2f} MB  {p}')
