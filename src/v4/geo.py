"""Preparação cartográfica do V4: Natural Earth (domínio público) + rota REAL do OpenStreetMap (ODbL, atribuição
"© colaboradores do OpenStreetMap") via Overpass, recortados e convertidos em TopoJSON (motor4/geo/preparar.mjs,
Turf mede a rota). Cache por consulta. Sem geometria de fonte → mapa sem rota, motivo registrado."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import requests

from src.v4.util import MOTOR4, RAIZ, rodar

NE = RAIZ / 'src' / 'render' / 'v2' / 'dados' / 'ne'
OVERPASS = 'https://overpass-api.de/api/interpreter'
OSM_ATRIB = '© colaboradores do OpenStreetMap (ODbL)'


ESPELHOS = (OVERPASS, 'https://overpass.kumi.systems/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter')


def _consultas(regiao: list, rota_osm: dict) -> list[str]:
    # valor começando com '~' = expressão regular (ex.: "~canal|fairway")
    tags = ''.join(f'["{k}"~"{v[1:]}"]' if str(v).startswith('~') else f'["{k}"="{v}"]' for k, v in (rota_osm.get('tags') or {}).items())
    nome = f'["name"~"{rota_osm["nome"]}",i]' if rota_osm.get('nome') else ''
    o, s, l, n = regiao
    q = [f'[out:json][timeout:90];way{tags}{nome}({s},{o},{n},{l});out geom;']
    if nome:                      # 2ª: as mesmas tags sem o filtro de nome (o nome no OSM varia por idioma)
        q.append(f'[out:json][timeout:90];way{tags}({s},{o},{n},{l});out geom;')
    return q


def osm_rota(regiao: list, rota_osm: dict, cache: Path, registro: Path | None = None) -> Path | None:
    """geometria REAL da rota no OSM. Execução 43972774128: a consulta não voltou e o mapa saiu sem rota (só o rio
    parecia a linha). Agora: cache persistente (CORINGA_OSM_CACHE, guardado pelo Actions), espelhos, 2ª consulta sem
    o filtro de nome e as tentativas gravadas na pasta da cena."""
    import os
    import time
    cache = Path(os.environ.get('CORINGA_OSM_CACHE') or cache)
    cache.mkdir(parents=True, exist_ok=True)
    tent = []
    for q in _consultas(regiao, rota_osm):
        arq = cache / f"osm_{hashlib.sha1(q.encode()).hexdigest()[:12]}.geojson"
        if arq.exists():
            tent.append({'consulta': q, 'resultado': 'cache'})
            _registrar(registro, tent)
            return arq
        for url in ESPELHOS:
            try:
                r = requests.post(url, data={'data': q}, timeout=120, headers={'User-Agent': 'CoringaExplica/4.0'})
                r.raise_for_status()
                els = [e for e in r.json().get('elements', []) if e.get('type') == 'way' and e.get('geometry')]
            except Exception as e:
                tent.append({'consulta': q, 'espelho': url, 'erro': str(e)[:200]})
                time.sleep(3)
                continue
            tent.append({'consulta': q, 'espelho': url, 'vias': len(els)})
            if not els:
                break                                   # resposta válida e vazia: tenta a consulta seguinte
            fc = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'osm_id': e['id'], 'name': (e.get('tags') or {}).get('name')},
                  'geometry': {'type': 'LineString', 'coordinates': [[p['lon'], p['lat']] for p in e['geometry']]}} for e in els],
                  'atribuicao': OSM_ATRIB, 'consulta': q}
            arq.write_text(json.dumps(fc))
            _registrar(registro, tent)
            return arq
    _registrar(registro, tent)
    return None


def _registrar(arq: Path | None, tent: list):
    if arq:
        arq.write_text(json.dumps(tent, ensure_ascii=False, indent=1))


def preparar(params: dict, trab: Path) -> dict:
    trab = Path(trab).resolve()
    trab.mkdir(parents=True, exist_ok=True)
    o, s, l, n = params['regiao']
    margem = max(l - o, n - s) * 0.6 + 1.0                  # o recorte precisa passar da área visível da câmera
    reg = [o - margem, s - margem, l + margem, n + margem]
    ped = {'regiao': reg, 'ne_dir': str(NE)}
    if params.get('rota_osm'):
        g = osm_rota(params['regiao'], params['rota_osm'], trab / 'cache_osm', trab / 'osm_tentativas.json')
        if g:
            ped.update(rota_geojson=str(g), rota_fonte=OSM_ATRIB, salto_max_km=params['rota_osm'].get('salto_max_km', 3))
            if params['rota_osm'].get('inicio'):
                ped['rota_inicio'] = params['rota_osm']['inicio']
    pj, saida = trab / 'geo_pedido.json', trab / 'geo.topo.json'
    pj.write_text(json.dumps(ped))
    rodar(['node', MOTOR4 / 'geo' / 'preparar.mjs', pj, saida], cwd=MOTOR4, log=trab / 'geo.log')
    return json.loads(saida.read_text())
