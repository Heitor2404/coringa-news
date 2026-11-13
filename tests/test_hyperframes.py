"""13/11/2026: componentes HyperFrames no template real. Confere que número, comparação, revelação e fechamento usam o
componente (código original) quando o dado cabe, que o número sai em pt-BR, e que sem os componentes o template volta
aos construtores antigos sem erro."""
import pytest

from src.render import render
from tests.test_identidade import _catalogo, precisa_navegador


def _abrir(p, pagina):
    nav = p.chromium.launch(args=render.NAVEGADOR)
    pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto(pagina.as_uri())
    pg.wait_for_function('window.READY===true', timeout=60000)
    return nav, pg, erros


@precisa_navegador
def test_cenas_de_dados_usam_componentes_hyperframes(tmp_path):
    from playwright.sync_api import sync_playwright
    dados = render.preparar(_catalogo(tmp_path / 'fotos'))
    pagina = render._escrever_pagina(dados, tmp_path)
    usados = {}
    with sync_playwright() as p:
        nav, pg, erros = _abrir(p, pagina)
        for sc in dados['scenes']:
            pg.evaluate(f"seek({sc['end'] - 0.3:.3f})")
            if sc['tipo'] in ('numero', 'comparacao', 'revelacao', 'fechamento'):
                k = dados['scenes'].index(sc)
                usados[sc['tipo']] = pg.evaluate(f"!!document.querySelectorAll('#stage .layer')[{k}].querySelector('.hfbox [data-hf]')")
                if sc['tipo'] == 'numero' and float(str(sc['valor']).replace(',', '.')) >= 1000:
                    txt = pg.evaluate(f"document.querySelectorAll('#stage .layer')[{k}].querySelector('.hfbox').innerText")
                    assert '.' in txt and ',' not in txt, txt            # 2.734, não 2,734
        nav.close()
    assert erros == []
    assert usados and all(usados.values()), usados


@precisa_navegador
def test_sem_componentes_o_template_volta_ao_antigo(tmp_path):
    from playwright.sync_api import sync_playwright
    dados = render.preparar(_catalogo(tmp_path / 'fotos'))
    pagina = render._escrever_pagina(dados, tmp_path)
    (tmp_path / 'hf_src.js').write_text('window.HF_SRC={};', encoding='utf-8')     # catálogo ausente
    with sync_playwright() as p:
        nav, pg, erros = _abrir(p, pagina)
        pg.evaluate(f"seek({dados['scenes'][-1]['end'] - 0.3:.3f})")
        assert pg.evaluate("document.querySelectorAll('.hfbox').length") == 0
        nav.close()
    assert erros == []


def test_pendente_vira_frase_anotada_sem_inventar():
    import main
    hf = main._anotacao({'fala': 'As eclusas erguem o navio *26 metros* acima do mar. Depois ele desce.'})
    assert hf['nome'] == 'vox-annotate'
    assert hf['vars']['text'] == 'As eclusas erguem o navio 26 metros acima'
    assert hf['vars']['keyword'] == '26 metros'
