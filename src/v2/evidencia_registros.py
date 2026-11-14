"""REGISTROS E REFERÊNCIAS REAIS para a Evidência V1 (experimental, só modo sombra).

O acervo da produção guarda só título, 220 caracteres de descrição e o ano (`registro_legado`). Aqui, SEM mexer no
acervo da produção, os metadados completos são buscados de novo nas APIs públicas e gratuitas, a partir do próprio
endereço da imagem:
  - Commons (Commons, Wikipédia e Wikidata usam arquivos do Commons): nome do arquivo tirado da URL → consulta em LOTE
    (até 40 títulos por pedido, pausa entre lotes) → `registro_commons` (categorias, data com origem, autor, licença);
  - NASA: nasa_id tirado da URL → `registro_nasa` (palavras-chave, data declarada);
  - qualquer outra fonte, ou falha: `registro_legado` (desconhecido nunca vira confirmação).
Referências: nomes do contrato (sujeito/quem/onde) → Wikidata (rótulo, apelidos, categoria do Commons P373).
Nada é inventado: o que a API não devolve fica ausente. Uma tentativa por consulta; erro → legado.
"""
from __future__ import annotations

import re
import time
from urllib.parse import unquote

from src.v2 import evidencia as E

UA = {'User-Agent': 'coringa-evidencia-sombra/1.0 (pesquisa; github.com/Heitor2404)'}
COMMONS = 'https://commons.wikimedia.org/w/api.php'
WIKIDATA = 'https://www.wikidata.org/w/api.php'
PAUSA = 2.0
MAX_NASA = 10
MAX_NOMES = 6


def _get_real(url, params):
    import requests
    r = requests.get(url, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    return r.json()


def arquivo_commons(url: str) -> str | None:
    m = re.search(r'/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/?#]+)', str(url or ''))
    return 'File:' + unquote(m.group(1)).replace('_', ' ') if m else None


def nasa_id(url: str) -> str | None:
    m = re.search(r'images-assets\.nasa\.gov/image/([^/]+)/', str(url or ''))
    return unquote(m.group(1)) if m else None


def registros(acervo: list[dict], get=None, pausa: float = PAUSA) -> tuple[dict, dict]:
    """{id: registro} para todo o acervo + resumo {real_commons, real_nasa, legado, erros}."""
    get = get or _get_real
    out, resumo = {}, {'real_commons': 0, 'real_nasa': 0, 'legado': 0, 'erros': []}
    titulos = {x['id']: arquivo_commons(x.get('url')) for x in acervo if x.get('id')}
    pedidos = list(dict.fromkeys(t for t in titulos.values() if t))
    paginas = {}
    for i in range(0, len(pedidos), 40):
        if i:
            time.sleep(pausa)
        try:
            j = get(COMMONS, {'action': 'query', 'titles': '|'.join(pedidos[i:i + 40]), 'prop': 'imageinfo|categories',
                              'iiprop': 'extmetadata|timestamp', 'cllimit': 'max', 'format': 'json', 'formatversion': 2})
            norm = {n['to']: n['from'] for n in j.get('query', {}).get('normalized', [])}
            for p in j.get('query', {}).get('pages', []):
                if p.get('imageinfo'):
                    paginas[p['title']] = p
                    if p['title'] in norm:
                        paginas[norm[p['title']]] = p
        except Exception as e:
            resumo['erros'].append(f'commons lote {i // 40}: {str(e)[:100]}')
    nasas = 0
    for x in acervo:
        if not x.get('id'):
            continue
        t = titulos.get(x['id'])
        p = paginas.get(t) if t else None
        if p:
            out[x['id']] = {**E.registro_commons(p), 'pagina': t}
            resumo['real_commons'] += 1
            continue
        nid = nasa_id(x.get('url'))
        if nid and nasas < MAX_NASA:
            nasas += 1
            try:
                time.sleep(pausa / 2)
                it = (get('https://images-api.nasa.gov/search', {'nasa_id': nid}).get('collection', {}).get('items') or [None])[0]
                if it:
                    out[x['id']] = {**E.registro_nasa((it.get('data') or [{}])[0]), 'pagina': nid}
                    resumo['real_nasa'] += 1
                    continue
            except Exception as e:
                resumo['erros'].append(f'nasa {nid}: {str(e)[:80]}')
        out[x['id']] = E.registro_legado(x)
        resumo['legado'] += 1
    return out, resumo


def _nomes(v: dict) -> list[str]:
    nomes = []
    for c in v.get('cenas') or []:
        ac = c.get('acontecimento') or {}
        for k in ('sujeito', 'quem', 'onde'):
            t = re.sub(r'\s+', ' ', str(ac.get(k) or '')).strip()
            if 3 <= len(t) <= 60:
                nomes.append(t)
    return list(dict.fromkeys(nomes))[:MAX_NOMES]


def referencias(v: dict, get=None, pausa: float = PAUSA) -> tuple[dict, dict]:
    """Entidades do contrato → Wikidata: rótulo, apelidos (pt/en) e categoria do Commons (P373). Sem resultado → só o nome."""
    get = get or _get_real
    base = E.referencias_basicas(v)
    entidades, resumo = list(base['entidades']), {'wikidata': 0, 'erros': []}
    evento = dict(base.get('evento') or {})
    tema = re.sub(r'[*?]', '', str(v.get('titulo') or '')).strip()
    if tema:                    # o acontecimento central: o artigo da Wikipédia que a busca pelo tema devolve (como a pesquisa faz)
        r = _item_do_artigo(tema, get, pausa, resumo) or _item(tema, get, pausa, resumo)
        if r:
            evento = {'nomes': r['apelidos'], 'categorias': r['categorias'], 'ids': r['ids']}
    for nome in _nomes(v):
        r = _item(nome, get, pausa, resumo)
        if r:
            entidades.append({'nome': nome, **r})
    return {'evento': evento, 'entidades': entidades}, resumo


def _item_do_artigo(tema: str, get, pausa: float, resumo: dict) -> dict | None:
    try:
        time.sleep(pausa / 2)
        h = (get('https://pt.wikipedia.org/w/api.php', {'action': 'query', 'list': 'search', 'srsearch': tema, 'srlimit': 1,
                                                        'format': 'json'}).get('query', {}).get('search') or [None])[0]
        if not h:
            return None
        pp = get('https://pt.wikipedia.org/w/api.php', {'action': 'query', 'titles': h['title'], 'prop': 'pageprops', 'format': 'json',
                                                       'formatversion': 2})
        q = ((pp.get('query', {}).get('pages') or [{}])[0].get('pageprops') or {}).get('wikibase_item')
        return _item(q, get, pausa, resumo, por_id=True) if q else None
    except Exception as ex:
        resumo['erros'].append(f'wikipédia {tema!r}: {str(ex)[:80]}')
        return None


def _item(nome: str, get, pausa: float, resumo: dict, por_id: bool = False) -> dict | None:
    try:
        time.sleep(pausa / 2)
        h = {'id': nome} if por_id else (get(WIKIDATA, {'action': 'wbsearchentities', 'search': nome, 'language': 'pt', 'uselang': 'pt',
                                                        'limit': 1, 'type': 'item', 'format': 'json'}).get('search') or [None])[0]
        if not h:
            return None
        e = get(WIKIDATA, {'action': 'wbgetentities', 'ids': h['id'], 'props': 'labels|aliases|claims', 'languages': 'pt|en',
                           'format': 'json'})['entities'][h['id']]
        cats = [c['mainsnak']['datavalue']['value'] for c in (e.get('claims') or {}).get('P373', []) if (c.get('mainsnak') or {}).get('datavalue')]
        rot = [l['value'] for l in (e.get('labels') or {}).values()]
        ali = [a['value'] for lst in (e.get('aliases') or {}).values() for a in lst][:8]
        resumo['wikidata'] += 1
        return {'apelidos': list(dict.fromkeys(rot + ali)), 'categorias': cats, 'ids': [h['id']]}
    except Exception as ex:
        resumo['erros'].append(f'wikidata {nome!r}: {str(ex)[:80]}')
        return None
