"""Etapa 3 (13/11/2026): protótipo ISOLADO do ESQUEMA e do clímax (prototipos/esquema). Não toca o template principal.
Confere: specs válidas e sem erro de JS, tipo desconhecido rejeitado, seek determinístico, rótulos legíveis e dentro da
área do diagrama (fora das zonas do Instagram e da faixa da legenda)."""
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PROTO = RAIZ / 'prototipos' / 'esquema'
SPECS = sorted((PROTO / 'specs').glob('*.json'))


def _pronto() -> bool:
    if not (RAIZ / 'node_modules' / '@fontsource' / 'montserrat').exists():
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
def pagina():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)))
        pg.goto((PROTO / 'pagina.html').as_uri())
        pg.evaluate('document.fonts.ready')
        pg.erros = erros
        yield pg
        nav.close()


def _spec(nome):
    return json.loads((PROTO / 'specs' / f'{nome}.json').read_text(encoding='utf-8'))


def test_ha_esquema_do_polvo_climax_e_dois_outros_dominios():
    nomes = {p.stem for p in SPECS}
    assert {'cromatoforo', 'climax_polvo', 'ceu_azul', 'micro_ondas'} <= nomes
    for p in SPECS:                                   # cada spec declara os fatos que o desenho afirma (nada inventado)
        s = json.loads(p.read_text(encoding='utf-8'))
        assert s.get('fatos'), p.name


def test_template_principal_nao_usa_o_prototipo():
    tpl = (RAIZ / 'src' / 'render' / 'template.html').read_text(encoding='utf-8')
    assert 'prototipos' not in tpl and 'ESQUEMA' not in tpl


@precisa_navegador
@pytest.mark.parametrize('nome', [p.stem for p in SPECS])
def test_spec_carrega_sem_erro_e_seek_e_deterministico(pagina, nome):
    s = _spec(nome)
    assert pagina.evaluate('s => ESQUEMA.validar(s)', s) == []
    pagina.evaluate('s => ESQUEMA.carregar(s, {legenda: true})', s)
    meio = round(s['duracao'] * .6, 2)
    pagina.evaluate(f'seek({meio})')
    a = pagina.evaluate("document.getElementById('esq').innerHTML")
    pagina.evaluate('seek(0.5)')
    pagina.evaluate(f'seek({meio})')
    assert pagina.evaluate("document.getElementById('esq').innerHTML") == a
    assert pagina.erros == []


@precisa_navegador
@pytest.mark.parametrize('nome', [p.stem for p in SPECS])
def test_rotulos_legiveis_e_dentro_da_area_do_diagrama(pagina, nome):
    s = _spec(nome)
    pagina.evaluate('s => ESQUEMA.carregar(s, {legenda: false})', s)
    tempos = sorted({round(r.get('de', 0) + .8, 2) for r in s.get('rotulos', [])} | {s['duracao'] - .05})
    vistos = 0
    for t in tempos:
        pagina.evaluate(f'seek({t})')
        m = pagina.evaluate('ESQUEMA.medir()')
        for b in m['rotulos'] + m['textos']:
            vistos += 1
            assert b['fs'] >= 24, b                                   # legível no celular
            assert b['x'] >= 50 and b['x'] + b['w'] <= 930, (t, b)     # fora da coluna de botões
            assert b['y'] >= 270 and b['y'] + b['h'] <= 1150, (t, b)   # fora do topo e da faixa da legenda
    assert vistos


@precisa_navegador
def test_tipo_ou_prop_desconhecidos_sao_rejeitados(pagina):
    ruim = {'duracao': 2, 'elementos': [{'id': 'x', 'tipo': 'caixa_generica', 'x': 0, 'y': 0},
                                        {'id': 'y', 'tipo': 'brilho', 'x': 0, 'y': 0, 'props': {'cor_magica': 1}}]}
    erros = pagina.evaluate('s => ESQUEMA.validar(s)', ruim)
    assert any('caixa_generica' in e for e in erros) and any('cor_magica' in e for e in erros)
    with pytest.raises(Exception, match='spec inválida'):
        pagina.evaluate('s => ESQUEMA.carregar(s)', ruim)


@precisa_navegador
def test_cromatoforo_demonstra_o_mecanismo_em_ordem(pagina):
    """Sinal → contração → saco estica → pele muda: medido no desenho, não só no roteiro."""
    pagina.evaluate('s => ESQUEMA.carregar(s)', _spec('cromatoforo'))
    area = 'document.querySelector(\'[data-id="detalhe"] path.saco\').getBBox().width'
    pagina.evaluate('seek(5.0)'); antes = pagina.evaluate(area)
    pagina.evaluate('seek(8.3)'); depois = pagina.evaluate(area)
    assert depois > antes * 2.5                                       # o saco de pigmento esticou
    pagina.evaluate('seek(5.9)')
    assert pagina.evaluate('+document.querySelector(\'[data-id="nervo"] circle\').getAttribute("opacity")') == 1   # impulso viajando
    raio = 'Math.max(...[...document.querySelectorAll(\'[data-id="pele"] circle[fill^="#"]\')].map(c => +c.getAttribute("r")))'
    pagina.evaluate('seek(1.0)'); r0 = pagina.evaluate(raio)
    pagina.evaluate('seek(11.5)'); r1 = pagina.evaluate(raio)
    assert r1 > r0 * 4                                                # os cromatóforos da pele abriram
