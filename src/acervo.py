"""Acervo de imagens REAIS do tema — juntado ANTES do roteiro (como um editor de documentário junta o material).

1. Fontes: as imagens dos artigos da Wikipédia (PT e EN) usados na pesquisa + os artigos do protagonista e dos lugares
   + busca no Wikimedia Commons pelos nomes principais. Só arquivos livres (domínio público / Creative Commons).
2. Um "catalogador" (Gemini, modelo principal, olhando as imagens) descreve o que cada uma mostra DE VERDADE e descarta
   o que não serve (logo, ícone, mapa genérico, assinatura, foto fora do tema).
3. O roteirista recebe essa lista e escreve frases que essas fotos conseguem mostrar; no fim, o "casamento" (uma chamada
   com todas as imagens) confere cada frase com a melhor foto do acervo.
"""
import io, json, os, re, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from . import gemini
from .midia import UA, _ano, _legenda, _licenca_ok, _txt, miniatura_jpg
from src import cofre

COMMONS = 'https://commons.wikimedia.org/w/api.php'
WIKI = 'https://{lang}.wikipedia.org/w/api.php'
MIN_LADO = 620          # 11/11: tudo vai em tela cheia; menor que isso fica minúscula ou borrada no vídeo (foto do paleontólogo do vídeo do dinossauro)
MAX_ARQUIVOS = 60       # quantos arquivos olhar
MAX_ACERVO = 42         # quantos baixar e catalogar
MIN_UTEIS = 10          # menos que isso: o tema não tem material visual → pula para o próximo (com 8, repetia foto e tapava com IA)
LIXO = re.compile(r'(logo|icon|ícone|flag of|bandeira|coat of arms|brasão|signature|assinatura|commons-|wiki|symbol|'
                  r'question[_ ]book|ambox|edit-clear|padlock|disambig|stub|red pog|pictogram|location map|locator|'
                  r'blank map|\.svg$|\.gif$|\.webm$|\.ogv$|\.ogg$|\.pdf$|\.djvu$)', re.I)


def _get(url: str, **params):
    params.update(format='json', formatversion=2)
    for espera in (0, 3, 8, 15):
        time.sleep(espera or 0.4)
        try:
            r = requests.get(url, params=params, headers=UA, timeout=40)
            if r.status_code == 429:
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if espera == 15:
                raise
    return {}


# ───────────────────────── fontes do acervo (todas grátis e com imagens de uso livre) ─────────────────────────
# Cada fonte devolve [{titulo, desc, ano, url, w, h, legenda, credito, fonte}]. Falha de uma fonte nunca derruba as outras.
POR_FONTE = 10


def _cand(titulo, desc, ano, url, credito, fonte, w=0, h=0):
    titulo = re.sub(r'\s+', ' ', str(titulo or '')).strip()[:120]
    return {'titulo': titulo, 'desc': re.sub(r'<[^>]+>|\s+', ' ', str(desc or '')).strip()[:220], 'ano': ano, 'url': url,
            'w': w or 0, 'h': h or 0, 'legenda': _legenda(titulo, ano), 'credito': credito, 'fonte': fonte}


def _ano_txt(s) -> int | None:
    m = re.search(r'\b(1[0-9]\d\d|20\d\d)\b', str(s or ''))
    return int(m.group(1)) if m else None


def _imagens_do_artigo(titulo: str, lang: str) -> list[str]:
    """Imagens do artigo NA ORDEM em que aparecem (as primeiras são as que ilustram o assunto; ícones ficam no fim)."""
    try:
        j = _get(WIKI.format(lang=lang), action='parse', page=titulo, prop='images', redirects=1)
        return [f'File:{i}' for i in (j.get('parse') or {}).get('images', [])]
    except Exception as e:
        print(f'  [acervo] artigo {lang}:{titulo[:40]} falhou: {str(e)[:60]}')
        return []


def _artigo(nome: str, lang: str = 'en') -> str | None:
    try:
        j = _get(WIKI.format(lang=lang), action='query', list='search', srsearch=nome, srlimit=1)
        h = j.get('query', {}).get('search', [])
        return h[0]['title'] if h else None
    except Exception:
        return None


def _busca_commons(q: str, n: int = 12) -> list[str]:
    try:
        j = _get(COMMONS, action='query', list='search', srsearch=f'{q} filetype:bitmap', srnamespace=6, srlimit=n)
        return [h['title'] for h in j.get('query', {}).get('search', [])]
    except Exception:
        return []


def _categoria_commons(q: str, n: int = 25) -> list[str]:
    """Categorias do Commons são montadas por pessoas: 'Theft of the Mona Lisa', 'Formicidae', 'Mars'... ouro puro."""
    try:
        j = _get(COMMONS, action='query', list='search', srsearch=q, srnamespace=14, srlimit=2)
        out = []
        for h in j.get('query', {}).get('search', [])[:2]:
            m = _get(COMMONS, action='query', list='categorymembers', cmtitle=h['title'], cmtype='file', cmlimit=n)
            out += [x['title'] for x in m.get('query', {}).get('categorymembers', [])]
        return out
    except Exception:
        return []


def _commons_infos(titulos: list[str], fonte: str) -> list[dict]:
    """Metadados no Commons (arquivo que só existe na Wikipédia — uso justo — não aparece aqui: fica de fora)."""
    out = []
    titulos = [t for t in titulos if not LIXO.search(t)]
    for i in range(0, len(titulos), 40):
        try:
            j = _get(COMMONS, action='query', prop='imageinfo', titles='|'.join(titulos[i:i + 40]),
                     iiprop='url|size|mime|extmetadata', iiurlwidth=1400)
        except Exception:
            continue
        pags = {p['title']: p for p in j.get('query', {}).get('pages', [])}
        for t in titulos[i:i + 40]:          # mantém a ordem original (a 1ª imagem do artigo é a mais importante)
            p = pags.get(t) or pags.get(t.replace('_', ' '))
            info = (p or {}).get('imageinfo', [None])[0] if p else None
            if not info:
                continue
            meta = info.get('extmetadata') or {}
            if info.get('mime') not in ('image/jpeg', 'image/png', 'image/tiff'):
                continue
            if min(info.get('width') or 0, info.get('height') or 0) < MIN_LADO:
                continue
            lic = _txt(meta, 'LicenseShortName')
            if not _licenca_ok(lic):
                continue
            titulo = p['title'].split(':', 1)[-1].rsplit('.', 1)[0]
            autor = re.sub(r'\s+', ' ', _txt(meta, 'Artist'))[:60] or 'autor desconhecido'
            out.append(_cand(titulo, _txt(meta, 'ImageDescription') or _txt(meta, 'ObjectName'), _ano(meta),
                             info.get('thumburl') or info['url'], f'"{titulo[:50]}" — {autor} ({lic}), via Wikimedia Commons',
                             fonte, info.get('width'), info.get('height')))
    return out


def f_wikipedia(arts: dict, nomes: list[str]) -> list[dict]:
    """Imagens dos artigos do evento (PT/EN) e dos artigos do protagonista e dos lugares (as primeiras de cada artigo)."""
    titulos = []
    for nome in nomes[:3]:
        a = _artigo(nome)
        if a:
            titulos += _imagens_do_artigo(a, 'en')[:8]
        a = _artigo(nome, 'pt')                 # tema do Brasil costuma ter mais foto na Wikipédia em português
        if a:
            titulos += _imagens_do_artigo(a, 'pt')[:5]
    for lang in ('en', 'pt'):
        for t in (arts.get(lang) or [])[:3]:
            titulos += _imagens_do_artigo(t, lang)[:8]   # artigo geral grande não engole o limite
    return _commons_infos(list(dict.fromkeys(titulos)), 'Wikipédia')


def f_commons(consultas: list[str]) -> list[dict]:
    titulos = []
    for q in consultas[:2]:
        titulos += _categoria_commons(q)
    for q in consultas[:3]:
        titulos += _busca_commons(q, 8)
    return _commons_infos(list(dict.fromkeys(titulos))[:60], 'Commons')


def f_nasa(consultas: list[str]) -> list[dict]:
    """NASA Image Library: espaço, planetas, Terra vista de cima, foguetes (domínio público, sem chave)."""
    out = []
    for q in consultas[:2]:
        try:
            r = requests.get('https://images-api.nasa.gov/search', params={'q': q, 'media_type': 'image', 'page_size': 12},
                             headers=UA, timeout=30)
            r.raise_for_status()
            for it in r.json().get('collection', {}).get('items', [])[:POR_FONTE]:
                d, link = (it.get('data') or [{}])[0], (it.get('links') or [{}])[0].get('href', '')
                if not link:
                    continue
                url = link.replace('~thumb', '~medium')
                out.append(_cand(d.get('title'), d.get('description'), _ano_txt(d.get('date_created')), url,
                                 f"{d.get('title', 'imagem')[:50]} — NASA ({d.get('center') or 'domínio público'})", 'NASA'))
        except Exception as e:
            print(f'  [acervo/nasa] {q!r}: {str(e)[:60]}')
    return out


def f_inaturalist(consultas: list[str]) -> list[dict]:
    """iNaturalist: fotos de animais, plantas, fungos e insetos (só licenças CC0/CC BY/CC BY-SA), sem chave."""
    out = []
    for q in consultas[:2]:
        try:
            r = requests.get('https://api.inaturalist.org/v1/taxa', params={'q': q, 'per_page': 1}, headers=UA, timeout=30)
            r.raise_for_status()
            res = r.json().get('results') or []
            if not res:
                continue
            t = requests.get(f"https://api.inaturalist.org/v1/taxa/{res[0]['id']}", headers=UA, timeout=30).json()
            taxon = (t.get('results') or [{}])[0]
            nome = taxon.get('preferred_common_name') or taxon.get('name') or q
            for tp in (taxon.get('taxon_photos') or [])[:POR_FONTE]:
                p = tp.get('photo') or {}
                lic = str(p.get('license_code') or '').lower()
                if lic not in ('cc0', 'cc-by', 'cc-by-sa') or not p.get('url'):
                    continue
                dims = p.get('original_dimensions') or {}
                out.append(_cand(f"{nome} ({taxon.get('name', '')})", p.get('attribution'), None,
                                 p['url'].replace('square', 'large'), f"{p.get('attribution') or nome} ({lic.upper()}), via iNaturalist",
                                 'iNaturalist', dims.get('width'), dims.get('height')))
        except Exception as e:
            print(f'  [acervo/inaturalist] {q!r}: {str(e)[:60]}')
    return out


def f_loc(consultas: list[str]) -> list[dict]:
    """Library of Congress: fotos e jornais históricos; só itens marcados como sem restrição/domínio público. Sem chave."""
    out = []
    for q in consultas[:2]:
        try:
            r = requests.get('https://www.loc.gov/photos/', params={'q': q, 'fo': 'json', 'c': 15}, headers=UA, timeout=40)
            r.raise_for_status()
            for it in r.json().get('results', []):
                bruto = json.dumps(it, ensure_ascii=False).lower()
                if 'no known restriction' not in bruto and 'public domain' not in bruto:
                    continue
                urls = [u for u in (it.get('image_url') or []) if isinstance(u, str)]
                if not urls:
                    continue
                url = urls[-1].split('#')[0]
                if url.startswith('//'):
                    url = 'https:' + url
                out.append(_cand(it.get('title'), ' '.join(it.get('description') or []) if isinstance(it.get('description'), list) else it.get('description'),
                                 _ano_txt(it.get('date')), url, f"{str(it.get('title', 'foto'))[:50]} — Library of Congress (sem restrição conhecida)",
                                 'Library of Congress'))
                if len(out) >= POR_FONTE:
                    break
        except Exception as e:
            print(f'  [acervo/loc] {q!r}: {str(e)[:60]}')
    return out


def f_met(consultas: list[str]) -> list[dict]:
    """Metropolitan Museum: obras e objetos em domínio público (arte, história antiga, armas, roupas de época). Sem chave."""
    out = []
    for q in consultas[:1]:
        try:
            r = requests.get('https://collectionapi.metmuseum.org/public/collection/v1/search',
                             params={'q': q, 'hasImages': 'true'}, headers=UA, timeout=30)
            r.raise_for_status()
            for oid in (r.json().get('objectIDs') or [])[:8]:
                o = requests.get(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}', headers=UA, timeout=30).json()
                if not o.get('isPublicDomain') or not (o.get('primaryImage') or o.get('primaryImageSmall')):
                    continue
                out.append(_cand(o.get('title'), f"{o.get('objectName', '')} {o.get('culture', '')} {o.get('artistDisplayName', '')}",
                                 _ano_txt(o.get('objectEndDate')), o.get('primaryImageSmall') or o['primaryImage'],
                                 f"{str(o.get('title', 'obra'))[:50]} — The Met (domínio público)", 'Met Museum'))
        except Exception as e:
            print(f'  [acervo/met] {q!r}: {str(e)[:60]}')
    return out


def f_europeana(consultas: list[str]) -> list[dict]:
    """Europeana: museus, arquivos e bibliotecas da Europa (só itens de reuso aberto). Precisa de EUROPEANA_API_KEY (grátis)."""
    chave = os.getenv('EUROPEANA_API_KEY')
    if not chave:
        return []
    out = []
    for q in consultas[:2]:
        try:
            r = requests.get('https://api.europeana.eu/record/v2/search.json', headers=UA, timeout=40,
                             params={'wskey': chave, 'query': q, 'reusability': 'open', 'media': 'true',
                                     'qf': 'TYPE:IMAGE', 'rows': 12, 'profile': 'rich'})
            r.raise_for_status()
            for it in r.json().get('items', [])[:POR_FONTE]:
                url = (it.get('edmIsShownBy') or it.get('edmPreview') or [None])[0]
                if not url:
                    continue
                prov = (it.get('dataProvider') or ['Europeana'])[0]
                out.append(_cand((it.get('title') or [''])[0], (it.get('dcDescription') or [''])[0],
                                 _ano_txt((it.get('year') or [''])[0]), url, f"{(it.get('title') or ['obra'])[0][:50]} — {prov}, via Europeana",
                                 'Europeana'))
        except Exception as e:
            print(f'  [acervo/europeana] {q!r}: {str(e)[:60]}')
    return out


def f_openverse(consultas: list[str]) -> list[dict]:
    """Openverse: Flickr e outros acervos com licença aberta (uso comercial permitido). Sem chave."""
    out = []
    for q in consultas[:2]:
        try:
            r = requests.get('https://api.openverse.org/v1/images/', headers=UA, timeout=30,
                             params={'q': q[:100], 'license_type': 'commercial', 'page_size': 10, 'mature': 'false'})
            r.raise_for_status()
            for h in r.json().get('results', [])[:POR_FONTE]:
                if not h.get('url'):
                    continue
                lic = f"CC {str(h.get('license', '')).upper()} {h.get('license_version') or ''}".strip()
                c = _cand(h.get('title'), ' '.join(t.get('name', '') for t in (h.get('tags') or [])[:8]), None, h['url'],
                          f"{h.get('title') or 'foto'} — {h.get('creator') or 'autor desconhecido'} ({lic}), via Openverse",
                          'Openverse', h.get('width'), h.get('height'))
                if h.get('thumbnail'):
                    c['alt'] = h['thumbnail']           # cópia servida pelo Openverse (o Flickr recusa download direto)
                out.append(c)
        except Exception as e:
            print(f'  [acervo/openverse] {q!r}: {str(e)[:60]}')
    return out


def f_wikidata(nomes: list[str]) -> list[dict]:
    """Wikidata: a imagem OFICIAL de cada pessoa, lugar, animal ou objeto citado (propriedade P18). Sem chave.
    É a busca mais certeira: 'Thalassodromeus' devolve a foto do próprio fóssil, não um dinossauro qualquer."""
    titulos = []
    for nome in [n for n in nomes if n][:6]:
        try:
            ids = []
            for lang in ('pt', 'en'):
                j = _get('https://www.wikidata.org/w/api.php', action='wbsearchentities', search=nome[:80],
                         language=lang, uselang=lang, limit=2, type='item')
                ids += [h['id'] for h in j.get('search', []) if h.get('id')]
            ids = list(dict.fromkeys(ids))[:3]
            if not ids:
                continue
            j = _get('https://www.wikidata.org/w/api.php', action='wbgetentities', ids='|'.join(ids), props='claims')
            ents = j.get('entities') or {}
            for e in (ents.values() if isinstance(ents, dict) else ents):
                for prop in ('P18', 'P2716'):                          # imagem principal, colagem de imagens
                    for cl in ((e.get('claims') or {}).get(prop) or [])[:2]:
                        val = ((cl.get('mainsnak') or {}).get('datavalue') or {}).get('value')
                        if isinstance(val, str) and val:
                            titulos.append('File:' + val)
        except Exception as e:
            print(f'  [acervo/wikidata] {nome!r}: {str(e)[:60]}')
    return _commons_infos(list(dict.fromkeys(titulos)), 'Wikidata')


def f_artic(consultas: list[str]) -> list[dict]:
    """Art Institute of Chicago: pinturas, gravuras e fotos históricas em domínio público. Sem chave."""
    out = []
    for q in consultas[:2]:
        try:
            r = requests.get('https://api.artic.edu/api/v1/artworks/search', timeout=30,
                             headers={**UA, 'AIC-User-Agent': UA.get('User-Agent', 'coringa-explica')},
                             params={'q': q[:100], 'limit': 12,
                                     'fields': 'id,title,image_id,date_end,is_public_domain,artist_title,thumbnail,medium_display'})
            r.raise_for_status()
            j = r.json()
            base = ((j.get('config') or {}).get('iiif_url') or 'https://www.artic.edu/iiif/2').rstrip('/')
            for o in j.get('data') or []:
                if not o.get('is_public_domain') or not o.get('image_id'):
                    continue
                th = o.get('thumbnail') or {}
                out.append(_cand(o.get('title'), f"{o.get('artist_title') or ''} {o.get('medium_display') or ''} {th.get('alt_text') or ''}",
                                 _ano_txt(o.get('date_end')), f"{base}/{o['image_id']}/full/843,/0/default.jpg",
                                 f"{str(o.get('title', 'obra'))[:50]} — Art Institute of Chicago (domínio público)",
                                 'Art Institute', th.get('width'), th.get('height')))
                if len(out) >= POR_FONTE:
                    break
        except Exception as e:
            print(f'  [acervo/artic] {q!r}: {str(e)[:60]}')
    return out


def f_cleveland(consultas: list[str]) -> list[dict]:
    """Cleveland Museum of Art: obras e objetos com licença CC0 (arte, história antiga, fotografia). Sem chave."""
    out = []
    for q in consultas[:2]:
        try:
            r = requests.get('https://openaccess-api.clevelandart.org/api/artworks/', headers=UA, timeout=30,
                             params={'q': q[:100], 'has_image': 1, 'cc0': 1, 'limit': 12})
            r.raise_for_status()
            for o in r.json().get('data') or []:
                im = o.get('images') or {}
                web = im.get('print') or im.get('web') or {}
                if not web.get('url'):
                    continue
                out.append(_cand(o.get('title'), f"{o.get('type') or ''} {o.get('technique') or ''} {o.get('culture') and ' '.join(o['culture']) or ''}",
                                 _ano_txt(o.get('creation_date')),          # antes de Cristo fica sem ano (etiqueta estranha)
                                 web['url'], f"{str(o.get('title', 'obra'))[:50]} — Cleveland Museum of Art (CC0)", 'Cleveland Museum',
                                 _int(web.get('width')), _int(web.get('height'))))
                if len(out) >= POR_FONTE:
                    break
        except Exception as e:
            print(f'  [acervo/cleveland] {q!r}: {str(e)[:60]}')
    return out


MAX_VIDEOS = 8          # clipes candidatos no acervo (só o miniatura é baixada; o clipe, só se for escolhido)
MIN_ALT_VIDEO = 720     # vídeo deitado com menos de 720 linhas fica borrado mesmo na moldura


def f_videos(consultas: list[str]) -> list[dict]:
    """VÍDEO EM MOVIMENTO: clipes do próprio assunto (Wikimedia Commons) e de ambiente (Pixabay: deserto, mina, mar...).
    Entram no acervo como as fotos: o catalogador olha um quadro, o editor de imagem decide foto ou vídeo por frase."""
    from . import midia
    out, vistos = [], set()
    buscas = list(dict.fromkeys([q for q in consultas if q]))
    for q in buscas[:6]:
        for c in midia.candidatos_pixabay(q) + midia.candidatos_arquivo(q):
            w, h, dur = int(c.get('w') or 0), int(c.get('h') or 0), float(c.get('dur') or 0)
            deitado = w >= h
            if not c.get('thumb') or c['url'] in vistos or (dur and dur < 3):
                continue
            if (deitado and h and h < MIN_ALT_VIDEO) or (not deitado and h < 1280):
                continue                                    # pequeno demais: borrado no celular
            vistos.add(c['url'])
            pix = 'pixabay' in c['url']
            x = _cand(c['descricao'], c['descricao'], c.get('ano'), c['thumb'], c.get('credito', ''),
                      'Pixabay vídeo' if pix else 'Commons vídeo', w, h)
            x['video'] = {'url': c['url'], 'w': w, 'h': h, 'dur': dur}
            out.append(x)
            if len(out) >= MAX_VIDEOS:
                return out
    return out


def _int(x) -> int:
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


def f_gbif(consultas: list[str]) -> list[dict]:
    """GBIF: fotos de animais, plantas e fungos de museus e cientistas (só licenças CC0/CC BY). Sem chave.
    Só entra quando a busca é o nome de um ser vivo (o GBIF reconhece a espécie, o gênero ou a família)."""
    out = []
    for q in consultas[:2]:
        try:
            m = requests.get('https://api.gbif.org/v1/species/match', params={'name': q[:80]}, headers=UA, timeout=30).json()
            if not m.get('usageKey') or m.get('matchType') not in ('EXACT', 'FUZZY') or (m.get('confidence') or 0) < 90:
                continue
            r = requests.get('https://api.gbif.org/v1/occurrence/search', headers=UA, timeout=30,
                             params={'taxonKey': m['usageKey'], 'mediaType': 'StillImage', 'limit': 25})
            r.raise_for_status()
            nome = m.get('scientificName') or q
            for oc in r.json().get('results') or []:
                for md in (oc.get('media') or [])[:1]:
                    lic = str(md.get('license') or oc.get('license') or '').lower()
                    if not md.get('identifier') or any(x in lic for x in ('by-nc', '_nc', 'by-nd', '_nd')):
                        continue                               # sem uso comercial ou sem modificação: fica de fora
                    if not any(x in lic for x in ('zero', 'publicdomain', '/by/', '/by-sa/', 'cc_by', 'cc0')):
                        continue
                    autor = md.get('rightsHolder') or md.get('creator') or oc.get('recordedBy') or 'autor desconhecido'
                    out.append(_cand(f"{nome}", f"{oc.get('species') or ''} {oc.get('country') or ''}", None, md['identifier'],
                                     f"{nome} — {str(autor)[:40]} (CC), via GBIF", 'GBIF'))
                if len(out) >= POR_FONTE:
                    break
        except Exception as e:
            print(f'  [acervo/gbif] {q!r}: {str(e)[:60]}')
    return out


def f_smithsonian(consultas: list[str]) -> list[dict]:
    """Smithsonian (19 museus americanos: história natural, ar e espaço, história): só imagens CC0.
    Precisa de DATA_GOV_API_KEY (grátis, api.data.gov)."""
    chave = os.getenv('DATA_GOV_API_KEY')
    if not chave:
        return []
    out = []
    for q in consultas[:2]:
        try:
            r = requests.get('https://api.si.edu/openaccess/api/v1.0/search', headers=UA, timeout=40,
                             params={'q': q[:100], 'rows': 40, 'api_key': chave})
            r.raise_for_status()
            linhas = (r.json().get('response') or {}).get('rows') or []
            antes = len(out)
            for row in linhas:
                cont = row.get('content') or {}
                dnr = cont.get('descriptiveNonRepeating') or {}
                livre = str((dnr.get('metadata_usage') or {}).get('access') or '').upper() == 'CC0'
                for md in ((dnr.get('online_media') or {}).get('media') or [])[:1]:
                    if str((md.get('usage') or {}).get('access') or '').upper() != 'CC0' and not livre:
                        continue
                    if str(md.get('type', 'Images')).lower() not in ('images', 'image', ''):
                        continue
                    url = md.get('content') or ''
                    for res in md.get('resources') or []:          # versão em JPEG de tamanho bom, quando houver
                        if 'jpeg' in str(res.get('label', '')).lower() and 'thumb' not in str(res.get('label', '')).lower():
                            url = res.get('url') or url
                            break
                    if not url.startswith('http'):
                        continue
                    datas = (cont.get('indexedStructured') or {}).get('date') or []
                    notas = (cont.get('freetext') or {}).get('notes') or []
                    desc = notas[0].get('content', '') if notas and isinstance(notas[0], dict) else ''
                    out.append(_cand(row.get('title'), desc, _ano_txt(datas[0] if datas else ''), url,
                                     f"{str(row.get('title', 'item'))[:50]} — Smithsonian (CC0)", 'Smithsonian'))
                if len(out) >= POR_FONTE:
                    break
            print(f'  [acervo/smithsonian] {q!r}: {len(linhas)} resultados, {len(out) - antes} com imagem livre')
        except Exception as e:
            print(f'  [acervo/smithsonian] {q!r}: {str(e)[:60]}')
    return out


PROMPT_CATALOGO = cofre.prompt('PROMPT_CATALOGO')


def _catalogar(itens: list[dict], tema: str, epoca: str) -> None:
    for ini in range(0, len(itens), 14):
        lote = itens[ini:ini + 14]
        lista = '\n'.join(f"{k}: " + ('[VÍDEO — a imagem é um quadro do clipe] ' if x.get('video') else '') + f"{x['titulo']} — {x['desc'][:160]}" + (f" ({x['ano']})" if x.get('ano') else '')
                          for k, x in enumerate(lote))
        try:
            r = gemini.json_visao(PROMPT_CATALOGO.format(tema=tema, epoca=epoca or '?', n=len(lote), lista=lista),
                                  [x['mini'] for x in lote], leve=True)     # descrever imagem é tarefa simples: modelo lite
            if isinstance(r, list):
                r = {'imagens': r}
            for a in r.get('imagens') or []:
                try:
                    x = lote[int(a.get('i'))]
                except (TypeError, ValueError, IndexError):
                    continue
                util = a.get('util')
                x['util'] = util if isinstance(util, bool) else str(util).lower() in ('true', 'sim', 'yes')
                tpc = a.get('texto_por_cima', False)    # marca d'água / texto de outro canal: nunca vai para o vídeo
                if tpc is True or str(tpc).lower() in ('true', 'sim', 'yes'):
                    x['util'] = False
                    print(f"  [acervo] fora: texto/marca d'água por cima — {x['titulo'][:60]}")
                x['mostra'] = str(a.get('mostra') or '')[:200]
                x['tipo_img'] = str(a.get('tipo') or 'foto').lower()
                esp = a.get('especifica', True)
                x['generica'] = not (esp if isinstance(esp, bool) else str(esp).lower() in ('true', 'sim', 'yes'))
                try:
                    x['nota'] = float(a.get('nota') or 0)
                except (TypeError, ValueError):
                    x['nota'] = 0
        except Exception as e:
            print(f'  [acervo] catalogador falhou ({str(e)[:80]}); uso a descrição do arquivo')
            for x in lote:
                x.setdefault('util', True)
                x.setdefault('mostra', x['desc'] or x['titulo'])
                x.setdefault('nota', 5)


import threading
_LOC = threading.Lock()
NAVEGADOR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}


_LOC_BLOQ: list = []


def _baixar_item(x: dict, arq: Path) -> dict:
    """Baixa a imagem de uma candidata. Library of Congress: um download por vez, com pausa (senão recusa com 429).
    Flickr (via Openverse) recusa programas (403): usa a cópia que o próprio Openverse serve."""
    from PIL import Image
    urls = [x['url']] + ([x['alt']] if x.get('alt') else [])
    for url in urls:
        cab = UA if ('wikimedia' in url or 'wikipedia' in url) else NAVEGADOR
        try:
            if 'loc.gov' in url:
                if _LOC_BLOQ:                        # a Library of Congress já recusou (429): não insiste e não perde tempo
                    raise RuntimeError('Library of Congress recusando downloads (429) nesta execução')
                with _LOC:
                    for espera in (0, 6):
                        time.sleep(espera or 1.5)
                        r = requests.get(url, headers=cab, timeout=40)
                        if r.status_code != 429:
                            break
                    if r.status_code == 429:
                        _LOC_BLOQ.append(1)
            else:
                r = requests.get(url, headers=cab, timeout=60)
                if r.status_code == 404 and '~medium' in url:          # NASA: nem todo item tem a versão média
                    r = requests.get(url.replace('~medium', '~orig'), headers=cab, timeout=90)
            r.raise_for_status()
            im = Image.open(io.BytesIO(r.content)).convert('RGB')
            if min(im.size) < MIN_LADO and not x.get('video'):
                return x
            if max(im.size) > 2000:
                im.thumbnail((2000, 2000))
            im.save(arq, 'JPEG', quality=92)
            x['arq'], x['mini'] = arq, miniatura_jpg(arq.read_bytes(), 384)
            return x
        except Exception as e:
            erro = e
    print(f"  [acervo] não baixei {x['titulo'][:40]}: {str(erro)[:60]}")
    return x


def _seguro(fn):
    try:
        return fn() or []
    except Exception as e:
        print(f'  [acervo] fonte falhou: {str(e)[:80]}')
        return []


def coletar(tema: dict, dossie: dict, pasta: Path) -> list[dict]:
    """Junta e cataloga o acervo. Levanta ValueError('pouco material visual...') se o tema não tiver fotos reais."""
    pasta.mkdir(parents=True, exist_ok=True)
    arts = dossie.get('_artigos') or {}
    prot = dossie.get('protagonista') if isinstance(dossie.get('protagonista'), dict) else {}
    nomes = ([prot['nome']] if prot.get('nome') else []) + [l for l in (dossie.get('lugares') or [])][:2]
    termos = [t for t in (tema.get('termos_en') or tema.get('termos') or []) if t]
    cenas_video = [t for t in (tema.get('busca_video') or []) if isinstance(t, str) and t.strip()]
    consultas = list(dict.fromkeys(([prot['nome']] if prot.get('nome') else []) + termos))[:4] or [tema.get('pergunta', '')]
    # todas as fontes AO MESMO TEMPO; cada uma serve melhor a uma área (história, espaço, natureza, arte, ciência)
    fontes = [('Commons', lambda: f_commons(consultas)), ('Wikipédia', lambda: f_wikipedia(arts, nomes)),
              ('Library of Congress', lambda: f_loc(consultas)), ('Europeana', lambda: f_europeana(consultas)),
              ('NASA', lambda: f_nasa(consultas)), ('iNaturalist', lambda: f_inaturalist(consultas)),
              ('Met Museum', lambda: f_met(consultas)), ('Openverse', lambda: f_openverse(consultas)),
              ('Wikidata', lambda: f_wikidata(nomes + consultas)), ('Art Institute', lambda: f_artic(consultas)),
              ('Cleveland', lambda: f_cleveland(consultas)), ('GBIF', lambda: f_gbif(consultas)),
              ('Smithsonian', lambda: f_smithsonian(consultas)), ('Vídeos', lambda: f_videos(cenas_video + termos + consultas))]
    with ThreadPoolExecutor(len(fontes)) as ex:
        res = list(ex.map(lambda f: (f[0], _seguro(f[1])), fontes))
    print('  [acervo] encontrados: ' + ' · '.join(f'{n} {len(r)}' for n, r in res))
    # intercala as fontes (a 1ª de cada, depois a 2ª de cada...): nenhuma fonte engole o limite sozinha
    itens, vistos = [], set()
    videos = next((list(r) for n, r in res if n == 'Vídeos'), [])     # clipes entram TODOS (não disputam o limite)
    filas = [list(r) for n, r in res if n != 'Vídeos']
    while any(filas) and len(itens) < MAX_ACERVO:
        for fila in filas:
            if fila and len(itens) < MAX_ACERVO:
                x = fila.pop(0)
                k = x['url'].split('?')[0].lower()       # o endereço inteiro (no iNaturalist todo arquivo se chama large.jpg)
                if k not in vistos and not LIXO.search(x['titulo'] + ' ' + x['url'].rsplit('.', 1)[-1][:5]):
                    vistos.add(k)
                    itens.append(x)
    for x in videos:
        if x['url'] not in vistos:
            vistos.add(x['url']); itens.append(x)
    print(f'  [acervo] {len(itens)} candidatas para baixar e catalogar')

    def baixar(par):
        k, x = par
        return _baixar_item(x, pasta / f'a{k}.jpg')

    with ThreadPoolExecutor(4) as ex:
        itens = [x for x in ex.map(baixar, enumerate(itens)) if x.get('arq')]
    epoca = ' · '.join(x for x in [str(dossie.get('epoca') or ''), ', '.join(dossie.get('lugares') or [])] if x)
    _catalogar(itens, tema.get('pergunta', ''), epoca)
    uteis = [x for x in itens if x.get('util') and x.get('nota', 0) >= 4]
    for k, x in enumerate(uteis):
        x['id'] = f'a{k}'
    print(f'  [acervo] {len(uteis)} imagens úteis para a história')
    for x in uteis:
        print(f"     {x['id']}: {x['mostra'][:90]}" + (f" ({x['ano']})" if x.get('ano') else ''))
    if len(uteis) < MIN_UTEIS:
        raise ValueError(f'pouco material visual: só {len(uteis)} fotos/vídeos reais sobre o tema (mínimo {MIN_UTEIS}); pulo para o próximo')
    return uteis


def texto(acervo: list[dict]) -> str:
    return '\n'.join(f"{x['id']}: " + ('[VÍDEO EM MOVIMENTO] ' if x.get('video') else '') + f"{x['mostra']}" + (f" [{x['ano']}]" if x.get('ano') else '')
                     + (' [genérica: só para frase de ambiente]' if x.get('generica') else '') for x in acervo)


PROMPT_CASAR = cofre.prompt('PROMPT_CASAR')


def casar(v: dict, acervo: list[dict]) -> dict:
    """Uma chamada com o acervo inteiro: escolhe a foto de cada ideia (o fiscal agora trabalha ANTES da montagem)."""
    por_id = {x['id']: x for x in acervo}
    ideias = []
    for c in v['cenas']:
        if c['tipo'] in ('fechamento', 'mapa') or c.get('sub'):
            continue
        ideias.append(c)
    if not ideias:
        return v
    linhas = '\n'.join(f"{k}: {(c.get('fala_ideia') or c['fala']).replace('*', '')} [{c.get('visual') or '?'}]"
                       for k, c in enumerate(ideias))
    escolha = {}
    try:
        r = gemini.json_visao(PROMPT_CASAR.format(primeiro=acervo[0]['id'], acervo=texto(acervo), ideias=linhas),
                              [x['mini'] for x in acervo], leve=False)
        if isinstance(r, list):
            r = {'escolhas': r}
        for e in r.get('escolhas') or []:
            try:
                k = int(e.get('ideia'))
            except (TypeError, ValueError):
                continue
            f = e.get('foto')
            if isinstance(f, int) or (isinstance(f, str) and f.isdigit()):
                f = f'a{int(f)}'
            exata = e.get('exata')
            exata = exata if isinstance(exata, bool) else str(exata).lower() in ('true', 'sim', 'yes')
            # 11/11: foto que NÃO mostra o que a frase diz e ainda é genérica (vaso qualquer numa frase sobre múmias,
            # flamingo de zoológico numa frase sobre o lago) sai: melhor outra imagem do que uma 'mais ou menos'
            if 0 <= k < len(ideias) and f in por_id and (exata or not por_id[f].get('generica')):
                escolha[k] = f
    except Exception as e:
        print(f'  [acervo] casamento falhou ({str(e)[:80]}); uso as sugestões do roteirista')
        for k, c in enumerate(ideias):
            if c.get('visual') in por_id:
                escolha[k] = c['visual']
    usos, ant = {}, None
    for k, c in enumerate(ideias):
        f = escolha.get(k)
        if f and (usos.get(f, 0) >= 1 or f == ant):        # 11/11: cada foto/vídeo em UMA ideia só (molécula 3x)
            f = None
        if f:
            usos[f] = usos.get(f, 0) + 1
            c['foto'] = f
        else:
            c.pop('foto', None)
        ant = f
    for c in v['cenas']:                       # os planos da mesma ideia herdam a foto dela
        if c.get('sub'):
            pai = next((x for x in v['cenas'] if x.get('grupo') == c.get('grupo') and not x.get('sub')), None)
            if pai and pai.get('foto'):
                c['foto'] = pai['foto']
            else:
                c.pop('foto', None)
    n = sum(1 for c in ideias if c.get('foto'))
    nv = sum(1 for c in ideias if c.get('foto') and por_id[c['foto']].get('video'))
    print(f'  [acervo] {n} de {len(ideias)} ideias com foto/vídeo real do acervo ({nv} em movimento)')
    return v


def complementar(v: dict, acervo: list[dict], pasta: Path) -> list[dict]:
    """2ª busca: para cada frase que ficou sem foto, procura imagem real do ASSUNTO DA FRASE (campo "busca" do roteiro:
    "Loki Balder painting", "Halifax bomber"...), não só do tema geral. As novas entram no acervo e o casamento é refeito."""
    from .orcamento import sobra
    faltam = [c for c in v['cenas'] if c['tipo'] not in ('mapa', 'fechamento') and not c.get('sub')
              and not c.get('foto') and str(c.get('busca') or '').strip()]
    if not faltam or sobra() < 50:
        return acervo
    consultas = list(dict.fromkeys(str(c['busca']).strip() for c in faltam))[:6]
    print(f"  [acervo] 2ª busca para {len(faltam)} frase(s) sem foto: {', '.join(consultas)}")

    def buscar(q):
        tit = _categoria_commons(q, 8) + _busca_commons(q, 6)
        return (f_wikidata([q])[:2] + _commons_infos(list(dict.fromkeys(tit))[:12], 'Commons')[:5]
                + f_smithsonian([q])[:2] + f_openverse([q])[:2])

    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(lambda q: _seguro(lambda: buscar(q)), consultas))
    vistos = {x['url'].split('?')[0].lower() for x in acervo}
    novos = []
    for lote in res:
        for x in lote:
            k = x['url'].split('?')[0].lower()
            if k not in vistos and not LIXO.search(x['titulo']):
                vistos.add(k)
                novos.append(x)
    novos = novos[:20]
    if not novos:
        return acervo
    base = len(acervo)
    with ThreadPoolExecutor(4) as ex:
        novos = [x for x in ex.map(lambda p: _baixar_item(p[1], pasta / f'b{p[0]}.jpg'), enumerate(novos)) if x.get('arq')]
    _catalogar(novos, v.get('titulo', ''), '')
    uteis = [x for x in novos if x.get('util') and x.get('nota', 0) >= 4]
    for k, x in enumerate(uteis):
        x['id'] = f'a{base + k}'
    print(f'  [acervo] 2ª busca: +{len(uteis)} imagem(ns) útil(eis)')
    for x in uteis:
        print(f"     {x['id']}: {x['mostra'][:90]}")
    return acervo + uteis
