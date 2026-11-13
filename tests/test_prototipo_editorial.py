"""Etapa 3, frente B (13/11/2026): componentes editoriais isolados (prototipos/editorial). Não tocam o template.
Confere: os cinco componentes carregam sem erro, o quadro t não depende do anterior, todo texto visível fica na área
segura com corpo legível, a distância do mapa vem das coordenadas, e componente desconhecido é recusado."""
import json
import math
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
ED = RAIZ / 'prototipos' / 'editorial'
SPECS = sorted((ED / 'specs').glob('*.json'))


def _pronto() -> bool:
    if not (RAIZ / 'node_modules' / 'world-atlas' / 'countries-50m.json').exists():
        return False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


precisa_navegador = pytest.mark.skipif(not _pronto(), reason='sem Chromium/node_modules (o workflow Testes instala)')


@pytest.fixture(scope='module')
def nav():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


def _abrir(nav, spec):
    pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto((ED / 'pagina.html').as_uri())
    pg.evaluate('document.fonts.ready')
    pg.evaluate('m => window.MUNDO = m', json.loads((RAIZ / 'node_modules/world-atlas/countries-50m.json').read_text()))
    pg.evaluate('s => EDITORIAL.carregar(s)', spec)
    pg.wait_for_timeout(100)
    return pg, erros


def test_cinco_componentes_e_nada_alem():
    assert {p.stem for p in SPECS} == {'abertura', 'revelacao', 'mapa', 'etiqueta', 'encerramento'}
    for p in SPECS:
        assert json.loads(p.read_text(encoding='utf-8')).get('fatos'), p.name
    tpl = (RAIZ / 'src' / 'render' / 'template.html').read_text(encoding='utf-8')
    assert 'EDITORIAL' not in tpl and 'prototipos' not in tpl
    assert 'gsap' not in (ED / 'editorial.js').read_text(encoding='utf-8').lower().replace('sem gsap', '')


@precisa_navegador
@pytest.mark.parametrize('nome', [p.stem for p in SPECS])
def test_carrega_e_e_deterministico(nav, nome):
    spec = json.loads((ED / 'specs' / f'{nome}.json').read_text(encoding='utf-8'))
    pg, erros = _abrir(nav, spec)
    t = round(spec['duracao'] * .7, 2)
    pg.evaluate(f'seek({t})'); a = pg.evaluate("document.getElementById('palco').innerHTML")
    pg.evaluate('seek(0.2)'); pg.evaluate(f'seek({t})')
    assert pg.evaluate("document.getElementById('palco').innerHTML") == a
    assert erros == []
    pg.close()


@precisa_navegador
@pytest.mark.parametrize('nome', [p.stem for p in SPECS])
def test_texto_na_area_segura_e_legivel(nav, nome):
    spec = json.loads((ED / 'specs' / f'{nome}.json').read_text(encoding='utf-8'))
    pg, _ = _abrir(nav, spec)
    for t in (spec['duracao'] * .55, spec['duracao'] - .6):
        pg.evaluate(f'seek({t})')
        for b in pg.evaluate('EDITORIAL.medir()'):
            if b['op'] < .5:
                continue
            assert b['fs'] >= 22, b
            assert 50 <= b['x'] and b['x'] + b['w'] <= 930 + 1, (t, b)
            assert 270 <= b['y'] and b['y'] + b['h'] <= 1150, (t, b)
    pg.close()


@precisa_navegador
def test_distancia_do_mapa_vem_das_coordenadas(nav):
    spec = json.loads((ED / 'specs' / 'mapa.json').read_text(encoding='utf-8'))
    pg, _ = _abrir(nav, spec)
    pg.evaluate(f"seek({spec['duracao']})")
    mostrado = int(pg.evaluate("document.querySelector('.mp-dist .n').textContent").replace('.', ''))
    o, d = spec['props']['origem'], spec['props']['destino']
    f1, f2, dl = map(math.radians, (o['lat'], d['lat'], d['lon'] - o['lon']))
    km = 6371 * math.acos(math.sin(f1) * math.sin(f2) + math.cos(f1) * math.cos(f2) * math.cos(dl))
    assert abs(mostrado - km) <= 1
    pg.close()


@precisa_navegador
def test_componente_desconhecido_recusado(nav):
    pg, _ = _abrir(nav, json.loads((ED / 'specs' / 'abertura.json').read_text(encoding='utf-8')))
    with pytest.raises(Exception, match='componente desconhecido'):
        pg.evaluate("EDITORIAL.carregar({componente: 'slide_corporativo', duracao: 2, props: {}})")
    pg.close()
