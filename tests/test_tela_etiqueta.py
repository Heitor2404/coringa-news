"""Fase 3, correção 1 (12/11/2026): texto em cima de texto — etiqueta da foto × destaque × legenda × lugar.

O vídeo da Torre Eiffel 3 foi barrado por "FOTO · 1902" encostando no cartão "FERRO-VELHO": na foto real em tela cheia
o destaque ficava em 990 px e a etiqueta, fixa em 1062 px, dentro dele. Agora a etiqueta sobe para cima do destaque
(mesmo estilo) e, se ainda bater em algo, o fiscal da tela a esconde só naquele trecho. Sem vídeo, sem IA.
"""
import itertools
from pathlib import Path

import pytest

from tests.caso_tela import _foto, _legendas
from tests.test_tela import precisa_navegador

DESTAQUES = [None, 'FERRO-VELHO', 'O MAIOR GOLPE DA HISTÓRIA DE PARIS EM 1925']   # nada, 1 linha, 2 linhas
FALAS = ['Ele vendeu a torre como ferro-velho', 'Victor Lustig *forjou* documentos oficiais do governo francês']


def _dados(pasta: Path, cenas: list[dict]) -> dict:
    pasta.mkdir(parents=True, exist_ok=True)
    em_pe = _foto(pasta, 'torre', 1200, 1600, (120, 100, 80))
    deitada = _foto(pasta, 'paris', 1600, 1000, (90, 110, 140))
    t, out, falas = 0.0, [], []
    for k, c in enumerate(cenas):
        dur = c.pop('dur', 3.0)
        f, wh = (deitada, [1600, 1000]) if c.pop('deitada', False) else (em_pe, [1200, 1600])
        base = {'img': f, 'foto_wh': wh, 'img_fundo': f}
        out.append({**base, **c, 'start': round(t, 3), 'end': round(t + dur, 3)})
        falas.append((t + 0.1, t + dur - 0.1, FALAS[k % 2]))
        t += dur
    return {'meta': {'titulo': 'Torre', 'marca': '@coringa.explica'}, 'scenes': out, 'captions': _legendas(falas),
            'duration': round(t, 3)}


def _fiscal(dados, tmp):
    from src.render.render import fiscal_tela, preparar
    d = preparar(dados)
    return d, fiscal_tela(d, tmp)


@precisa_navegador
def test_torre_eiffel_foto_1902_x_ferro_velho(tmp_path):
    """O caso exato que barrou o vídeo: sai limpo, com a etiqueta VISÍVEL (não escondida) acima do destaque."""
    cena = {'tipo': 'historia', 'real': True, 'etiqueta': 'FOTO · 1902', 'destaque': 'FERRO-VELHO', 'dur': 4.0}
    d, erros = _fiscal(_dados(tmp_path / 'img', [cena, {'tipo': 'historia', 'real': True}]), tmp_path)
    assert erros == [] and d['etq_some'] == []
    pos = _posicoes(tmp_path, d, 2.0)
    assert pos['etq'] and pos['dq'] and pos['etq']['bottom'] + 8 <= pos['dq']['top']     # etiqueta inteira acima
    assert pos['etq_top_css'] == '930px'


@precisa_navegador
def test_sem_destaque_a_etiqueta_fica_onde_sempre_esteve(tmp_path):
    cena = {'tipo': 'historia', 'real': True, 'etiqueta': 'FOTO · 1902'}
    d, erros = _fiscal(_dados(tmp_path / 'img', [cena]), tmp_path)
    assert erros == [] and _posicoes(tmp_path, d, 1.5)['etq_top_css'] == '1062px'      # identidade visual mantida


@precisa_navegador
def test_todas_as_combinacoes_sem_texto_em_cima(tmp_path):
    """historia: real × destaque (nenhum, 1 linha, 2 linhas) × lugar × etiqueta × moldura; imagem: real × etiqueta ×
    moldura × rótulo; fotos em pé e deitadas. Nenhum choque e a etiqueta nunca precisa sumir."""
    cenas = []
    for real, dq, lugar, etq, mold in itertools.product([True, False], DESTAQUES, [None, 'PARIS · 1925'],
                                                         [None, 'FOTO · 1902'], [False, True]):
        c = {'tipo': 'historia', 'real': real, 'moldura': mold, 'deitada': len(cenas) % 3 == 0}
        c.update({k: v for k, v in (('destaque', dq), ('lugar', lugar), ('etiqueta', etq)) if v})
        cenas.append(c)
    for real, etq, mold, rot in itertools.product([True, False], [None, 'FOTO · 1902'], [False, True],
                                                  [None, 'O GOLPE DO SÉCULO']):
        c = {'tipo': 'imagem', 'real': real, 'moldura': mold, 'deitada': len(cenas) % 2 == 0}
        c.update({k: v for k, v in (('etiqueta', etq), ('rotulo', rot)) if v})
        cenas.append(c)
    assert len(cenas) == 64
    d, erros = _fiscal(_dados(tmp_path / 'img', cenas), tmp_path)
    assert erros == [], 'texto em cima de texto:\n' + '\n'.join(erros)
    assert d['etq_some'] == [], f"etiqueta precisou sumir em {d['etq_some']}"


@precisa_navegador
def test_etiqueta_some_so_no_trecho_marcado_pelo_fiscal(tmp_path):
    from src.render.render import preparar
    cena = {'tipo': 'historia', 'real': True, 'etiqueta': 'FOTO · 1902'}
    d = preparar(_dados(tmp_path / 'img', [dict(cena, dur=3.0), dict(cena, dur=3.0)]))
    d['etq_some'] = [[0.0, 3.0]]
    assert _posicoes(tmp_path, d, 1.5)['etq_opacidade'] == '0'
    assert _posicoes(tmp_path, d, 4.5)['etq_opacidade'] == '1'


def _posicoes(tmp, dados, t):
    """Abre a página do template e lê, no segundo t, a caixa da etiqueta e do destaque da cena atual."""
    from playwright.sync_api import sync_playwright
    from src.render.render import NAVEGADOR, _escrever_pagina
    pagina = _escrever_pagina(dados, tmp)
    with sync_playwright() as p:
        nav = p.chromium.launch(args=NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(Path(pagina).as_uri())
        pg.wait_for_function('window.READY===true', timeout=60000)
        pg.evaluate(f'seek({t})')
        r = pg.evaluate('''t => {
            const vis = [...document.querySelectorAll('#stage > *')].filter(e => getComputedStyle(e).opacity === '1');
            const cx = sel => { for (const v of vis) { const e = v.querySelector(sel); if (e) { const b = e.getBoundingClientRect();
                return {top: b.top, bottom: b.bottom, el: e} } } return null };
            const etq = cx('.etq'), dq = cx('.dq');
            return {etq: etq && {top: etq.top, bottom: etq.bottom}, dq: dq && {top: dq.top, bottom: dq.bottom},
                    etq_top_css: etq ? etq.el.style.top : null, etq_opacidade: etq ? etq.el.style.opacity : null} }''', t)
        nav.close()
    return r


# ───────── lógica do fiscal sem navegador ─────────
def test_fiscal_esconde_a_etiqueta_e_desce_a_legenda(monkeypatch, tmp_path):
    from src.render import render
    choque_cap = {'tipo': 'choque', 'cap': True, 'etq': False, 'txt': '"ferro" encostando no cartão "X"', 'cena': 'historia'}
    choque_etq = {'tipo': 'choque', 'cap': False, 'etq': True, 'txt': '"FOTO · 1902" encostando no cartão "FERRO-VELHO"',
                  'cena': 'historia'}
    outro = {'tipo': 'choque', 'cap': False, 'etq': False, 'txt': '"A" em cima de "B"', 'cena': 'cards'}
    rodadas = iter([[(t, choque_cap) for t in (1.0, 1.2, 1.4)] + [(t, choque_etq) for t in (2.0, 2.2, 2.4)],
                    [(t, choque_etq) for t in (2.0, 2.2, 2.4)] + [(t, outro) for t in (5.0, 5.2, 5.4)],
                    [(t, outro) for t in (5.0, 5.2, 5.4)]])
    monkeypatch.setattr(render, '_medir', lambda pagina, dur: next(rodadas))
    monkeypatch.setattr(render, '_escrever_pagina', lambda dados, trab: tmp_path / 'p.html')
    d = {'duration': 6.0}
    erros = render.fiscal_tela(d, tmp_path)
    assert d['cap_baixo'] == [[0.7, 1.7]] and d['etq_some'] == [[1.7, 2.7]]
    assert erros == ['5.0s (cards): "A" em cima de "B"']                       # o que não tem conserto continua barrando


@precisa_navegador
def test_video_na_moldura_com_cartao_no_alto(tmp_path):
    """Produção: moldura só existe em vídeo deitado ("▶ VÍDEO · ano"); com destaque ou rótulo no alto, a etiqueta da
    moldura desce para o canto de baixo e nada se encosta."""
    from tests.caso_tela import _clipe
    clipe = _clipe(tmp_path / 'clipe')
    quadro = str(Path(clipe['dir']) / 'f_0001.jpg')
    base = {'img': quadro, 'video': clipe, 'moldura': True, 'video_moldura': True, 'foto_wh': [960, 540],
            'etiqueta': '▶ VÍDEO · 1925'}
    cenas = [dict(base, tipo='historia', destaque='FERRO-VELHO'), dict(base, tipo='historia', destaque='FERRO-VELHO',
             lugar='PARIS · 1925'), dict(base, tipo='imagem', rotulo='O GOLPE DO SÉCULO'), dict(base, tipo='historia')]
    d = _dados(tmp_path / 'img', cenas)
    for c in d['scenes']:
        c['img'] = c['img_fundo'] = quadro
    d, erros = _fiscal(d, tmp_path)
    assert erros == [] and d['etq_some'] == []
