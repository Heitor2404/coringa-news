"""Fatos de referência da Wikipedia em português (para os vídeos 'Coringa Explica')."""
import requests

API = 'https://{lang}.wikipedia.org/w/api.php'
CABECALHO = {'User-Agent': 'CoringaExplicaBot/1.1 (https://github.com/Heitor2404/coringa-news; educational short videos) python-requests'}


def _get(lang='pt', **params):
    import time
    params.update(format='json', formatversion=2, maxlag=5)
    for espera in (0, 3, 8, 15):            # a Wikipédia pede calma quando recebe muitos pedidos (erro 429)
        time.sleep(espera or 0.6)
        r = requests.get(API.format(lang=lang), params=params, headers=CABECALHO, timeout=30)
        if r.status_code != 429:
            r.raise_for_status()
            return r.json()
    r.raise_for_status()


def pesquisar(termos: list[str], max_artigos: int = 3, chars: int = 2500, lang: str = 'pt') -> tuple[str, list[str]]:
    """Busca os artigos mais relevantes e devolve (texto de referência, títulos usados)."""
    titulos = []
    for t in termos[:4]:
        try:
            res = _get(lang, action='query', list='search', srsearch=t, srlimit=2)
            for h in res.get('query', {}).get('search', []):
                if h['title'] not in titulos:
                    titulos.append(h['title'])
        except Exception as e:
            print(f'  [wiki] busca falhou ({t}): {str(e)[:100]}')
        if len(titulos) >= max_artigos:
            break
    titulos = titulos[:max_artigos]
    if not titulos:
        return '', []
    blocos = []
    for t in titulos:
        try:
            res = _get(lang, action='query', prop='extracts', explaintext=1, exsectionformat='plain',
                       exchars=chars, titles=t, redirects=1)
            for p in res.get('query', {}).get('pages', []):
                if p.get('extract'):
                    blocos.append(f"### {p['title']}\n{p['extract']}")
        except Exception as e:
            print(f'  [wiki] artigo falhou ({t}): {str(e)[:100]}')
    return '\n\n'.join(blocos), titulos
