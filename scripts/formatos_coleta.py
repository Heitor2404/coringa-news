"""COLETA (sem IA, sem render): dados cartográficos e mídia histórica licenciada para a direção de arte dos formatos.

Roda no Actions (a sessão local não alcança Commons/NASA/EOX/AWS). Saída (cifrada pelo workflow):
  raster/   mosaicos físico + satélite por região (scripts/formatos_raster.py), com fontes, licenças e sha256
  midia/    arquivos Commons + midia.json (URL de origem, licença e autor LIDOS da própria API do Commons, sha256, tamanho)
Só entra mídia cuja licença, lida da API, é domínio público / CC0 / CC BY / CC BY-SA. Nada é escolhido aqui: a escolha
(e a conferência visual de que a imagem mostra o que diz) é feita depois, e só então o item vai à biblioteca comprovada.
uso: python scripts/formatos_coleta.py <saida>
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import formatos_raster  # noqa: E402

API = 'https://commons.wikimedia.org/w/api.php'
UA = {'User-Agent': 'CoringaExplica/formatos-coleta (pesquisa editorial; https://github.com/Heitor2404)'}
TITULOS = [
    'File:Aktie Canal de Panama 1880.jpg',
    'File:SS Ancon entering west chamber cph.3b17471u.jpg',
    'File:NSRW Panama Canal French Excavator.jpg',
    'File:Panama Canal under construction, 1907.jpg',
]
BUSCAS = [
    'Ancon 1914 Panama Canal opening',
    'French Panama Canal excavation 1880s',
    'Compagnie universelle canal interoceanique Panama',
    'Ferdinand de Lesseps portrait photograph',
    'Gatun locks construction 1913',
    'Culebra Cut 1913 Panama',
]
ACEITAS = re.compile(r'^(public domain|pd|cc0|cc by(-sa)? [0-9.]+|cc-by(-sa)?-[0-9.]+|no restrictions)', re.I)


def api(**kw):
    kw.update(format='json', formatversion=2)
    for k in range(4):
        try:
            r = requests.get(API, params=kw, headers=UA, timeout=60)
            if r.ok:
                return r.json()
        except Exception:
            pass
        time.sleep(2 * (k + 1))
    raise RuntimeError(f'API falhou: {kw}')


def limpo(html: str | None) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html or '')).strip()


def info(titulos: list[str]) -> list[dict]:
    d = api(action='query', titles='|'.join(titulos), prop='imageinfo', iiprop='url|size|sha1|extmetadata|mime', iiurlwidth=1920)
    out = []
    for p in d['query']['pages']:
        ii = (p.get('imageinfo') or [None])[0]
        if not ii:
            out.append({'titulo': p['title'], 'erro': 'inexistente'})
            continue
        em = ii.get('extmetadata') or {}
        g = lambda k: limpo((em.get(k) or {}).get('value'))
        out.append({'titulo': p['title'], 'pagina': ii.get('descriptionurl'), 'original': ii.get('url'), 'url': ii.get('thumburl') or ii.get('url'),
                    'wh_original': [ii.get('width'), ii.get('height')], 'mime': ii.get('mime'), 'sha1_commons': ii.get('sha1'),
                    'licenca': g('LicenseShortName'), 'licenca_url': g('LicenseUrl'), 'autor': g('Artist'), 'credito_linha': g('Credit'),
                    'data': g('DateTimeOriginal') or g('DateTime'), 'descricao': g('ImageDescription')[:600], 'restricoes': g('Restrictions'),
                    'uso_termos': g('UsageTerms')})
    return out


def main(saida: Path):
    if '--so-raster' in sys.argv:
        formatos_raster.main(saida / 'raster')
        return
    midia = saida / 'midia'
    midia.mkdir(parents=True, exist_ok=True)
    titulos = list(TITULOS)
    for q in BUSCAS:
        d = api(action='query', list='search', srsearch=q, srnamespace=6, srlimit=6)
        titulos += [s['title'] for s in d['query']['search'] if re.search(r'\.(jpe?g|png|tiff?)$', s['title'], re.I)]
    vistos, itens = set(), []
    for i in range(0, len(titulos), 20):
        lote = [t for t in titulos[i:i + 20] if not (t in vistos or vistos.add(t))]
        if lote:
            itens += info(lote)
    for k, it in enumerate(itens):
        if it.get('erro'):
            continue
        it['aceita'] = bool(ACEITAS.search(it['licenca'] or '')) and not it['restricoes']
        if not it['aceita']:
            continue
        r = requests.get(it['url'], headers=UA, timeout=120)
        if not r.ok:
            it['erro'] = f'download {r.status_code}'
            continue
        ext = '.png' if it['url'].lower().endswith('.png') else '.jpg'
        nome = f'c{k:02d}_' + hashlib.sha1(it['titulo'].encode()).hexdigest()[:10] + ext
        (midia / nome).write_bytes(r.content)
        it.update(arquivo=nome, sha256=hashlib.sha256(r.content).hexdigest(), bytes=len(r.content))
        time.sleep(.3)
    (midia / 'midia.json').write_text(json.dumps(itens, ensure_ascii=False, indent=1))
    print('mídia:', sum(1 for x in itens if x.get('arquivo')), 'de', len(itens))
    formatos_raster.main(saida / 'raster')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
