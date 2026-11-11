"""FISCAL DA TELA no pytest: trava o "conserta aqui, quebra ali".

Toda mudança no template passa por aqui no GitHub (workflow Testes). Se algum texto voltar a cair em cima de outro
(legenda × cartão, lugar × etiqueta da foto, número × legenda...) o teste fica vermelho ANTES de virar vídeo.
Precisa do Chromium do Playwright e do node_modules (o workflow instala os dois); sem eles, o teste é pulado.
"""
import shutil
from pathlib import Path

import pytest

from tests.caso_tela import RAIZ, coober_pedy, tem_mapa


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


@precisa_navegador
def test_coober_pedy_sem_texto_em_cima(tmp_path):
    """O vídeo de 10/11 (que saiu com legenda em cima de cartão) agora sai limpo."""
    from src.render.render import fiscal_tela, preparar
    dados = preparar(coober_pedy(tmp_path / 'img', com_mapa=tem_mapa()))
    erros = fiscal_tela(dados, tmp_path)
    assert erros == [], 'texto em cima de texto:\n' + '\n'.join(erros)


@precisa_navegador
def test_fiscal_enxerga_choque(tmp_path):
    """Prova de que o fiscal não está cego: uma citação enorme invade a faixa da legenda e ele PRECISA reagir
    (descer a legenda sozinho ou acusar o erro)."""
    from src.render.render import fiscal_tela, preparar
    dados = coober_pedy(tmp_path / 'img', com_mapa=False)
    cit = next(c for c in dados['scenes'] if c['tipo'] == 'numero')
    for k in [k for k in cit if k not in ('start', 'end')]:
        cit.pop(k)
    cit.update({'tipo': 'citacao', 'autor': 'Teste', 'texto': ' '.join(['palavra comprida'] * 30)})
    dados = preparar(dados)
    erros = fiscal_tela(dados, tmp_path)
    assert erros or dados['cap_baixo'], 'o fiscal não viu a citação gigante em cima da legenda'


@precisa_navegador
@pytest.mark.parametrize('nome', ['exemplo_explica.json', 'exemplo_historia.json', 'exemplo_ira.json', 'exemplo_anvisa.json'])
def test_exemplos_sem_texto_em_cima(nome, tmp_path):
    """Os roteiros de exemplo cobrem os outros tipos de cena (mapa, citação, escala, cards, lista, revelação...)."""
    import json
    from src.render.render import fiscal_tela, preparar
    from tests.caso_tela import exemplo
    tipos = {c['tipo'] for c in json.loads((RAIZ / 'tests' / nome).read_text(encoding='utf-8'))['cenas']}
    if 'mapa' in tipos and not tem_mapa():
        pytest.skip('sem d3-geo no node_modules (o workflow instala)')
    dados = preparar(exemplo(nome, tmp_path))
    erros = fiscal_tela(dados, tmp_path)
    assert erros == [], f'{nome}: texto em cima de texto:\n' + '\n'.join(erros)


def test_legenda_repetida_some_no_final():
    """No cartão final, a legenda que só repete 'Segue o @coringa.explica' é escondida (estava duplicada na tela)."""
    html = (RAIZ / 'src' / 'render' / 'template.html').read_text(encoding='utf-8')
    assert 'function repete(' in html and 'repete(c,t)' in html


def test_template_sem_posicao_na_faixa_da_legenda():
    """Nenhum bloco do meio da tela é posicionado dentro da faixa da legenda (1150+) no template."""
    import re
    html = (RAIZ / 'src' / 'render' / 'template.html').read_text(encoding='utf-8')
    corpo = html[html.index('B.numero='):html.index('/* ---------- foto real na moldura')]
    tops = [int(x) for x in re.findall(r'top:(\d{3,4})px', corpo)]
    assert tops and max(tops) <= 1120, f'bloco começando em {max(tops)}px invade a faixa da legenda'


if __name__ == '__main__':
    shutil.rmtree('/tmp/tela', ignore_errors=True)
    print(pytest.main([__file__, '-q']))
