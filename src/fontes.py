"""Pesquisa profunda para o Coringa Explica.

Junta material de várias fontes (Wikipédia PT e EN, busca na web, Google News) e um "garimpeiro"
separa os fatos concretos e surpreendentes: nomes, datas, números, cenas, viradas. É o que deixa
o roteiro com cara de quem pesquisou de verdade, em vez de resumo de enciclopédia.
"""
import json

from . import gemini, wiki
from src import cofre

PROMPT_GARIMPO = cofre.prompt('PROMPT_GARIMPO')


def _texto_fatos(r: dict) -> str:
    """Transforma o dossiê em texto para o roteirista, com os fatos mais surpreendentes primeiro."""
    fatos = r.get('fatos') or []
    if isinstance(fatos, str):
        return fatos
    linhas = []
    itens = [f if isinstance(f, dict) else {'fato': str(f)} for f in fatos]
    itens.sort(key=lambda f: -float(f.get('surpresa') or 0))
    for f in itens:
        estrela = '★ ' if float(f.get('surpresa') or 0) >= 8 else ''
        tipo = f" [{f['tipo']}]" if f.get('tipo') else ''
        fonte = f" ({f['fonte']})" if f.get('fonte') else ''
        linhas.append(f"- {estrela}{f.get('fato', '')}{tipo}{fonte}")
    extra = []
    if r.get('angulo'):
        extra.append(f"FIO CONDUTOR SUGERIDO: {r['angulo']}")
    p = r.get('protagonista')
    if isinstance(p, dict) and p.get('nome'):
        extra.append(f"PROTAGONISTA: {p.get('nome')} — {p.get('papel', '')}")
    if r.get('epoca') or r.get('lugares'):
        extra.append(f"ÉPOCA/LUGAR: {r.get('epoca', '')} · {', '.join(r.get('lugares') or [])}")
    return '\n'.join(extra + ['', 'FATOS (★ = mais surpreendentes):'] + linhas)


def coletar(tema: dict, pedido: str = '', parte: int = 1) -> tuple[str, list[str], str, dict]:
    """Devolve (fatos em texto, fontes, link de referência, dossiê). Levanta erro se o material não for sobre o tema."""
    chars = 7000 if parte <= 1 else 9000
    blocos, links = [], []
    pt, tit_pt = wiki.pesquisar(tema.get('termos', []), chars=chars, lang='pt')
    if pt:
        blocos.append(f'=== Wikipédia (português) ===\n{pt}')
        links.append('https://pt.wikipedia.org/wiki/' + tit_pt[0].replace(' ', '_'))
    en, tit_en = wiki.pesquisar(tema.get('termos_en') or tema.get('termos', []), chars=chars, lang='en')
    if en:
        blocos.append(f'=== Wikipedia (inglês) ===\n{en}')
        links.append('https://en.wikipedia.org/wiki/' + tit_en[0].replace(' ', '_'))
    try:   # busca na web pelo Gemini (quando a conta tiver essa função liberada)
        web = gemini.pesquisar(f'Pesquise na web e liste fatos concretos e pouco conhecidos, com nomes, datas, números, '
                               f'detalhes de cena e a fonte de cada um, sobre: {tema["pergunta"]} ({pedido})')
        if web:
            blocos.append(f'=== Busca na web ===\n{web[:8000]}')
    except Exception as e:
        print(f'  [fontes] busca na web indisponível: {str(e)[:80]}')
    try:   # reportagens (Google News)
        from .pautas import cobertura
        cov = cobertura(tema.get('busca') or pedido or tema['pergunta'], n=10)
        if cov:
            blocos.append(f'=== Reportagens (Google News) ===\n{cov}')
    except Exception as e:
        print(f'  [fontes] Google News falhou: {str(e)[:80]}')
    if not blocos:
        raise ValueError('nenhuma fonte trouxe material')
    r = gemini.json_(PROMPT_GARIMPO.format(pergunta=tema['pergunta'], pedido=pedido or tema['pergunta'],
                                           blocos='\n\n'.join(blocos)[:45000]))
    if isinstance(r, list):
        r = r[0]
    texto = _texto_fatos(r)
    n = len(r.get('fatos') or []) if isinstance(r.get('fatos'), list) else 0
    print(f"  [fontes] relevante={r.get('relevante')} sensível={r.get('sensivel')} · {n} fatos · {r.get('motivo', '')[:100]}")
    if r.get('sensivel'):
        raise ValueError('tema sensível (crime/violência): não vou fazer este vídeo')
    if not r.get('relevante') or len(texto) < 300:
        raise ValueError(f"não achei material confiável sobre o tema ({r.get('motivo', '')[:150]})")
    r['_artigos'] = {'pt': tit_pt, 'en': tit_en}      # o acervo de imagens começa pelas fotos destes artigos
    return texto, (r.get('fontes') or ['Wikipédia'])[:3], (links[0] if links else ''), r
