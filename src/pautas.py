"""Busca manchetes no Google News Brasil e evita repetir notícias já usadas."""
import json, re, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import feedparser

HIST = Path(__file__).resolve().parents[1] / 'data' / 'historico.json'
BASE = 'https://news.google.com/rss{}?hl=pt-BR&gl=BR&ceid=BR:pt-419'
TOPICOS = {
    'DESTAQUES': '',
    'MUNDO': '/headlines/section/topic/WORLD',
    'BRASIL': '/headlines/section/topic/NATION',
    'ECONOMIA': '/headlines/section/topic/BUSINESS',
    'TECNOLOGIA': '/headlines/section/topic/TECHNOLOGY',
    'CIÊNCIA': '/headlines/section/topic/SCIENCE',
    'SAÚDE': '/headlines/section/topic/HEALTH',
    'ESPORTES': '/headlines/section/topic/SPORTS',
    'ENTRETENIMENTO': '/headlines/section/topic/ENTERTAINMENT',
}


def _chave(titulo: str) -> str:
    t = re.sub(r'\s+-\s+[^-]+$', '', titulo.lower())  # tira " - Fonte"
    return re.sub(r'[^a-z0-9à-ú ]', '', t)[:90]


def carregar_historico() -> dict:
    if HIST.exists():
        return json.loads(HIST.read_text(encoding='utf-8'))
    return {}


def salvar_historico(h: dict):
    limite = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    h = {k: v for k, v in h.items() if v >= limite}
    HIST.parent.mkdir(exist_ok=True)
    HIST.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding='utf-8')


def buscar(por_topico: int = 8) -> list[dict]:
    hist = carregar_historico()
    vistos, itens = set(), []
    for topico, caminho in TOPICOS.items():
        feed = feedparser.parse(BASE.format(caminho))
        for e in feed.entries[:por_topico]:
            k = _chave(e.title)
            if k in vistos or k in hist:
                continue
            vistos.add(k)
            fonte = e.get('source', {}).get('title', '') if isinstance(e.get('source'), dict) else ''
            itens.append({'id': len(itens), 'topico': topico, 'titulo': e.title, 'fonte': fonte,
                          'link': e.link, 'data': e.get('published', ''), 'chave': k})
        time.sleep(0.5)
    return itens


_PARADAS = set('para pelo pela pelos pelas como com sem sobre entre após apos depois antes mais menos muito muita '
               'que qual quais quando onde porque está estão esta este essa esse isso aquele aquela ainda também '
               'uma umas uns dos das nos nas aos num numa seu sua seus suas diz dizem afirma veja entenda saiba '
               'novo nova novos novas pode podem será foram vai vão the and for with from'.split())


def _palavras(t: str) -> set[str]:
    t = re.sub(r'\s+-\s+[^-]+$', '', t.lower())
    return {w for w in re.findall(r'[a-zà-ú0-9]{4,}', t) if w not in _PARADAS}


def cobertura(titulo: str, n: int = 10) -> str:
    """Manchetes e resumos de vários veículos sobre o mesmo assunto (reserva quando não há busca no Gemini)."""
    import html
    q = re.sub(r'\s+-\s+[^-]+$', '', titulo)
    feed = feedparser.parse(BASE.format('/search') .replace('?hl=', f'?q={quote(q)}&hl='))
    chave = _palavras(q)
    linhas = []
    for e in feed.entries[:n * 2]:
        if len(linhas) >= n:
            break
        if len(chave & _palavras(e.title)) < max(1, min(3, len(chave) // 3)):
            continue                                    # manchete de outro assunto

        resumo = re.sub(r'<[^>]+>', ' ', html.unescape(e.get('summary', '')))
        resumo = re.sub(r'\s+', ' ', resumo).strip()
        fonte = e.get('source', {}).get('title', '') if isinstance(e.get('source'), dict) else ''
        linhas.append(f"- {e.title} | {fonte} | {e.get('published', '')}" + (f" | {resumo[:300]}" if resumo and resumo not in e.title else ''))
    return '\n'.join(linhas)


def buscar_tema(tema: str, n: int = 12) -> list[dict]:
    """Manchetes recentes sobre um assunto pedido (ex.: 'derrota do Trump')."""
    feed = feedparser.parse(BASE.format('/search').replace('?hl=', f'?q={quote(tema)}+when:3d&hl='))
    if not feed.entries:
        feed = feedparser.parse(BASE.format('/search').replace('?hl=', f'?q={quote(tema)}&hl='))
    itens = []
    for e in feed.entries[:n]:
        fonte = e.get('source', {}).get('title', '') if isinstance(e.get('source'), dict) else ''
        itens.append({'id': len(itens), 'topico': 'DESTAQUES', 'titulo': e.title, 'fonte': fonte,
                      'link': e.link, 'data': e.get('published', ''), 'chave': _chave(e.title)})
    return itens
