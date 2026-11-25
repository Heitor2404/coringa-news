"""Verificação geográfica automática por DUAS fontes independentes (E284).

Consolida mecanismos já usados no projeto — Nominatim/OpenStreetMap (`src/roteiro.py`) e Wikidata
(`src/acervo.py`, `src/v2/evidencia_registros.py`) — para que uma necessidade `territorio` chegue ao ATLAS sem
curadoria manual em todos os assuntos, mas também sem coordenadas inventadas:

- Wikidata: entidade com coordenada P625 (e rótulo) encontrada pelo nome + contexto;
- OpenStreetMap/Nominatim: ponto e caixa delimitadora do mesmo nome + contexto;
- aceita somente se as duas fontes concordarem (distância <= max(5 km, metade da diagonal da caixa OSM)) e o ponto
  Wikidata cair dentro da caixa OSM expandida; caso contrário devolve PENDENTE com o motivo (curadoria continua
  possível). Não há fallback para coordenadas de modelo.
A ROI do ATLAS é a caixa OSM com margem e tamanho mínimo, o marcador é o ponto Wikidata.
"""
from __future__ import annotations

import math
import re
import time

UA = {'User-Agent': 'CoringaExplicaBot/1.0 (https://github.com/Heitor2404/coringa-news; educational short videos)'}
WIKIDATA = 'https://www.wikidata.org/w/api.php'
NOMINATIM = 'https://nominatim.openstreetmap.org/search'
ORIGEM = 'VERIFICACAO_GEOGRAFICA_AUTOMATICA'


def _km(a, b):
    (lat1, lon1), (lat2, lon2) = a, b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def _get(sessao, url, params):
    r = sessao.get(url, params=params, headers=UA, timeout=25)
    r.raise_for_status()
    return r.json()


def wikidata(nome, contexto, sessao):
    busca = _get(sessao, WIKIDATA, {'action': 'wbsearchentities', 'search': nome, 'language': 'en', 'limit': 5, 'format': 'json'})
    ids = [h['id'] for h in busca.get('search', [])]
    if not ids:
        return None
    ents = _get(sessao, WIKIDATA, {'action': 'wbgetentities', 'ids': '|'.join(ids), 'props': 'labels|descriptions|claims',
                                   'languages': 'en|pt', 'format': 'json'}).get('entities', {})
    ctx = {w for w in re.findall(r'[a-z]{3,}', (contexto or '').lower())}
    melhores = []
    for i, qid in enumerate(ids):
        e = ents.get(qid) or {}
        c = ((e.get('claims') or {}).get('P625') or [{}])[0].get('mainsnak', {}).get('datavalue', {}).get('value')
        if not c:
            continue
        desc = ' '.join(str((e.get(k) or {}).get(l, {}).get('value', '')) for k in ('labels', 'descriptions') for l in ('en', 'pt')).lower()
        melhores.append((-len(ctx & set(re.findall(r'[a-z]{3,}', desc))), i, qid, c, desc))
    if not melhores:
        return None
    _, _, qid, c, desc = min(melhores)
    return {'qid': qid, 'lat': float(c['latitude']), 'lon': float(c['longitude']), 'descricao': desc[:200],
            'url': f'https://www.wikidata.org/wiki/{qid}'}


def osm(nome, contexto, sessao):
    j = _get(sessao, NOMINATIM, {'q': f'{nome}, {contexto}' if contexto else nome, 'format': 'json', 'limit': 1,
                                 'accept-language': 'en'})
    if not j:
        return None
    x = j[0]
    s, n, w, e = map(float, x['boundingbox'])
    return {'lat': float(x['lat']), 'lon': float(x['lon']), 'bbox': [w, s, e, n], 'nome': x.get('display_name', '')[:200],
            'url': f"https://www.openstreetmap.org/{x.get('osm_type', 'node')}/{x.get('osm_id')}"}


def roi_atlas(bbox, ponto, *, margem=.35, minimo_graus=.12):
    """Caixa OSM com margem e tamanho mínimo (o lugar não fica colado na borda nem minúsculo)."""
    w, s, e, n = bbox
    lat0 = ponto[0]
    dx, dy = max(e - w, minimo_graus / max(.2, math.cos(math.radians(lat0)))), max(n - s, minimo_graus)
    cx, cy = (w + e) / 2, (s + n) / 2
    dx, dy = dx * (1 + 2 * margem), dy * (1 + 2 * margem)
    return [round(cx - dx / 2, 5), round(max(-84, cy - dy / 2), 5), round(cx + dx / 2, 5), round(min(84, cy + dy / 2), 5)]


def verificar(nome, contexto='', *, sessao=None, rotulo=None, caso_id=None):
    import requests
    sessao = sessao or requests.Session()
    base = {'nome': nome, 'contexto': contexto, 'publicar': False}
    try:
        wd = wikidata(nome, contexto, sessao)
        time.sleep(1.1)  # política de uso do Nominatim
        om = osm(nome, contexto, sessao)
    except Exception as e:
        return {**base, 'estado': 'PENDENTE', 'motivo': 'FONTE_INDISPONIVEL:' + type(e).__name__}
    if not wd or not om:
        return {**base, 'estado': 'PENDENTE', 'motivo': 'SEM_DUAS_FONTES', 'wikidata': wd, 'osm': om}
    w, s, e, n = om['bbox']
    diag = _km((s, w), (n, e))
    dist = _km((wd['lat'], wd['lon']), (om['lat'], om['lon']))
    tol = max(5.0, diag / 2)
    folga = max(.02, .25 * max(e - w, n - s))
    dentro = w - folga <= wd['lon'] <= e + folga and s - folga <= wd['lat'] <= n + folga
    if dist > tol or not dentro:
        return {**base, 'estado': 'PENDENTE', 'motivo': 'FONTES_DIVERGEM', 'distancia_km': round(dist, 2), 'tolerancia_km': round(tol, 2),
                'wikidata': wd, 'osm': om}
    ponto = (wd['lat'], wd['lon'])
    return {**base, 'estado': 'VERIFICADA', 'origem': ORIGEM, 'distancia_km': round(dist, 3), 'tolerancia_km': round(tol, 2),
            'wikidata': wd, 'osm': om,
            'caso_atlas': {'id': caso_id or re.sub(r'[^a-z0-9]+', '_', nome.lower()).strip('_')[:40],
                           'title': rotulo or nome, 'fonte_localizacao': wd['url'], 'fontes': [wd['url'], om['url']],
                           'delta': 1.6, 'atlas': {'roi': roi_atlas(om['bbox'], ponto), 'label': rotulo or nome,
                                                   'lonlat': [round(wd['lon'], 5), round(wd['lat'], 5)]}},
            'escopo': 'localização atual; não comprova limites históricos, rotas ou relevo'}


def validar_verificacao(v):
    """Contrato aceito pela ponte ATLAS→filme em lugar da curadoria manual."""
    if not isinstance(v, dict) or v.get('estado') != 'VERIFICADA' or v.get('origem') != ORIGEM:
        return ['GEO-VERIFICACAO-AUSENTE']
    erros = []
    for k in ('wikidata', 'osm'):
        src = v.get(k) or {}
        if not str(src.get('url', '')).startswith('https://'):
            erros.append('GEO-FONTE-' + k.upper())
    if not isinstance(v.get('distancia_km'), (int, float)) or v['distancia_km'] > v.get('tolerancia_km', 0):
        erros.append('GEO-FONTES-DIVERGEM')
    return erros
