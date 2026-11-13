"""Plano-mestre, etapa F (12/11/2026): identidade visual única, componentes com função e dado verdadeiro.
Capturas de cada componente, colisão (fiscal da tela de f4796c9), legibilidade e zonas dos botões. Sem IA, sem vídeo."""
import re
import shutil

import pytest

from src import recursos
from src.render import identidade, render
from tests.caso_tela import RAIZ, _foto, _inserir, coober_pedy
from tests.test_tela import precisa_navegador

TEMPLATE = (RAIZ / 'src/render/template.html').read_text(encoding='utf-8')


def test_template_declara_os_mesmos_tokens_da_identidade():
    raiz = re.search(r':root\{(.*?)\}', TEMPLATE, re.S).group(1)
    decl = dict(re.findall(r'(--[\w-]+):([^;]+);?', raiz))
    for k, v in identidade.css_vars().items():
        assert decl.get(k, '').strip() == v, k
    for sel, var in (('.title', '--fs-titulo'), ('.sec', '--fs-secao'), ('#cap', '--fs-legenda'), ('.lbl', '--fs-rotulo'),
                     ('#tag', '--fs-aviso')):
        regra = re.search(re.escape(sel) + r'\{([^}]*)\}', TEMPLATE).group(1)
        assert f'font-size:var({var})' in regra, sel                         # o tamanho vem do token, não de número solto


def test_cada_componente_tem_funcao_declarada():
    for t in recursos.GRAFICOS:
        assert t in identidade.FUNCAO and identidade.FUNCAO[t]
    assert 'cartao' not in identidade.FUNCAO                                  # cartão de palavra solta não é componente


# ───────── dado verdadeiro e função ─────────
FATOS = '- A torre tem 330 metros (Wikipédia)\n- Foi inaugurada em 1889 e reformada em 1925 (Wikipédia)\n' \
        '- Recebe 7 milhões de visitantes por ano (site oficial)\n- Eiffel disse: "Eu deveria ter inveja da torre" (biografia)'


def _v(*cenas):
    return {'plano': {'origem': 'roteirista'}, 'cenas': [dict(c, bloco={'funcao': 'evidencia'}) for c in cenas]}


def test_dado_dos_fatos_passa_e_dado_inventado_sai_da_tela():
    v = _v({'tipo': 'numero', 'valor': 330, 'fala': 'a torre tem 330 metros'},
           {'tipo': 'numero', 'valor': 7000000, 'fala': '7 milhões de visitantes'},
           {'tipo': 'numero', 'valor': 512, 'fala': 'tem 512 degraus'},
           {'tipo': 'linha_tempo', 'itens': [{'ano': '1889', 'texto': 'abre'}, {'ano': '1925', 'texto': 'reforma'}], 'fala': 'datas'},
           {'tipo': 'linha_tempo', 'itens': [{'ano': '1889'}, {'ano': '1944'}], 'fala': 'datas'},
           {'tipo': 'comparacao', 'itens': [{'rotulo': 'Torre', 'valor': 330}, {'rotulo': 'Prédio', 'valor': 150}], 'fala': 'compara'},
           {'tipo': 'citacao', 'texto': 'Eu deveria ter inveja da torre', 'autor': 'Eiffel', 'fala': 'citação'},
           {'tipo': 'citacao', 'texto': 'A torre é minha filha', 'autor': 'Eiffel', 'fala': 'citação'})
    probs = {p['cena']: p for p in recursos.conferir(v, FATOS)}
    assert set(probs) == {2, 4, 5, 7} and all(p['inventado'] for p in probs.values())
    feitos = recursos.rebaixar(v, FATOS)
    assert len(feitos) == 4 and [c['tipo'] for c in v['cenas']][:2] == ['numero', 'numero']
    assert v['cenas'][2]['tipo'] == 'historia' and v['cenas'][2]['fala'] == 'tem 512 degraus'   # a fala não muda
    assert 'rebaixado' in recursos.linha_telegram(v, FATOS)


def test_mapa_decorativo_datas_fora_de_ordem_e_recurso_sem_funcao_sao_avisados():
    v = _v({'tipo': 'mapa', 'fala': 'A torre é linda.', 'pontos': [{'nome': 'Paris'}]},
           {'tipo': 'mapa', 'fala': 'Ele fugiu de Paris para Viena.', 'pontos': [{'nome': 'Paris'}, {'nome': 'Viena'}]},
           {'tipo': 'linha_tempo', 'itens': [{'ano': '1925'}, {'ano': '1889'}], 'fala': 'x'})
    v['cenas'].append({'tipo': 'lista', 'itens': ['a', 'b'], 'fala': 'y'})          # sem bloco.funcao
    probs = [p['problema'] for p in recursos.conferir(v, FATOS)]
    assert any('mapa sem função' in p for p in probs) and sum('mapa sem função' in p for p in probs) == 1
    assert any('fora de ordem' in p for p in probs) and any('sem função declarada' in p for p in probs)
    assert recursos.rebaixar(v, FATOS) == []                                     # aviso, não remoção


# ───────── capturas e tela ─────────
def _catalogo(pasta):
    d = coober_pedy(pasta)                       # gancho, história com lugar, número, destaque, mapa, linha do tempo, revelação, fim
    f = _foto(pasta, 'extra', 1400, 1000, (90, 110, 140))
    d = _inserir(d, 'revelacao', {'tipo': 'comparacao', 'img': f, 'titulo': 'Altura', 'unidade': 'm',
                                  'itens': [{'rotulo': 'Torre', 'valor': 330, 'cor': 'amarelo'}, {'rotulo': 'Prédio', 'valor': 150}]},
                 4.5, 'A torre tem *330* metros')
    d = _inserir(d, 'revelacao', {'tipo': 'citacao', 'img': f, 'autor': 'Gustave Eiffel', 'texto': 'Eu deveria ter inveja da torre',
                                  'cor': 'amarelo'}, 4.5, 'Eiffel brincou com a *inveja*')
    d = _inserir(d, 'revelacao', {'tipo': 'lista', 'img': f, 'titulo': 'Três usos', 'itens': ['*rádio*', 'meteorologia', 'turismo']},
                 4.5, 'Ela serviu para *rádio* e mais')
    d = _inserir(d, 'revelacao', {'tipo': 'cards', 'img': f, 'titulo': 'Números',
                                  'itens': [{'rotulo': 'Altura', 'valor': '330 m', 'icone': '📏'}, {'rotulo': 'Ano', 'valor': '1889', 'icone': '📅'}]},
                 4.5, 'Dois números para *guardar*')
    d = _inserir(d, 'revelacao', {'tipo': 'escala', 'img': f, 'titulo': 'Altura', 'unidade': 'm', 'min': 0, 'max': 400,
                                  'marcas': [{'valor': 150, 'rotulo': 'Prédio'}], 'destaque': {'valor': 330, 'rotulo': 'Torre'}},
                 4.5, 'Na escala, *330* metros')
    return d


@precisa_navegador
def test_catalogo_de_componentes_sem_colisao_legivel_e_fora_das_zonas_dos_botoes(tmp_path):
    dados = render.preparar(_catalogo(tmp_path / 'fotos'))
    trab = tmp_path / 'trab'
    trab.mkdir()
    assert render.fiscal_tela(dados, trab) == []                                 # nenhum texto sobre texto, em todas as combinações
    assert render.legibilidade(dados, trab) == []                                # nada pequeno demais nem na área dos botões
    tipos = {sc['tipo'] for sc in dados['scenes']}
    assert {'gancho', 'historia', 'numero', 'mapa', 'linha_tempo', 'comparacao', 'citacao', 'lista', 'cards', 'escala',
            'revelacao', 'fechamento'} <= tipos or 'mapa' not in tipos


@precisa_navegador
def test_capturas_de_cada_componente(tmp_path):
    from playwright.sync_api import sync_playwright
    dados = render.preparar(_catalogo(tmp_path / 'fotos'))
    pagina = render._escrever_pagina(dados, tmp_path)
    saida = RAIZ / 'tmp' / 'capturas-identidade'
    shutil.rmtree(saida, ignore_errors=True)
    saida.mkdir(parents=True)
    with sync_playwright() as p:
        nav = p.chromium.launch(args=render.NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(pagina.as_uri())
        pg.wait_for_function('window.READY===true', timeout=60000)
        for k, sc in enumerate(dados['scenes']):
            t = sc['start'] + min(1.6, (sc['end'] - sc['start']) * 0.6)
            pg.evaluate(f'seek({t:.3f})')
            pg.screenshot(path=str(saida / f"{k:02d}-{sc['tipo']}.png"))
        nav.close()
    fotos = sorted(saida.glob('*.png'))
    assert len(fotos) == len(dados['scenes']) and all(f.stat().st_size > 20000 for f in fotos)   # quadro desenhado, não vazio


@precisa_navegador
def test_aviso_de_ia_legivel(tmp_path):
    d = coober_pedy(tmp_path / 'fotos')
    d['scenes'][1]['ia'] = True
    dados = render.preparar(d)
    trab = tmp_path / 'trab'
    trab.mkdir()
    assert not [x for x in render.legibilidade(dados, trab) if 'GERADAS' in x]
