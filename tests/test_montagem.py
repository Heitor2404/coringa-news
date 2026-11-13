"""Plano-mestre, etapa G (12/11/2026): montagem e ritmo com propósito. Timelines simuladas, sem vídeo e sem IA.
Ritmo ≠ quantidade de cortes: detalhe só com resolução, nada antecipado, transição pelo motivo, sem tela preta, e o
detector separa imagem idêntica, movimento geométrico e mudança semântica (Ken Burns não melhora nada)."""
from pathlib import Path

import main
from src import estaticos, storyboard as sbm
from tests.test_tela import precisa_navegador


def _jpg(p: Path, w, h, cor=(90, 110, 140)):
    from PIL import Image
    Image.new('RGB', (w, h), cor).save(p)
    return p


def _montar(tmp, cenas_v, duracoes, tamanhos=None):
    reais = {}
    for k, c in enumerate(cenas_v):
        if c.get('foto'):
            w, h = (tamanhos or {}).get(c['foto'], (900, 1200))
            reais[c['foto']] = {'tipo': 'foto', 'arq': _jpg(tmp / f"{c['foto']}.jpg", w, h, (40 * k % 255, 90, 120)), 'ano': 1925}
            c['imagem'] = c['foto']
    t, tempos = 0.0, []
    for d in duracoes:
        tempos.append((t, t + d)); t += d
    return main._montar_cenas({'cenas': cenas_v, 'titulo': 'T'}, reais, {}, tempos, tmp), tempos


def _ideias(n, sem=(), evento_igual=()):
    cenas = [{'tipo': 'gancho' if k == 0 else 'historia', 'fala': f'frase {k}', 'grupo': k, 'evento': f'e{k}',
              'bloco': {'funcao': 'abertura' if k == 0 else 'mecanismo'}, **({} if k in sem else {'foto': f'a{k}'})}
             for k in range(n)]
    for k in evento_igual:
        cenas[k]['evento'] = cenas[k - 1]['evento']
    cenas.append({'tipo': 'fechamento', 'fala': 'segue'})
    return sbm.construir({'cenas': cenas, 'plano': {'modos': ['historico_investigativo']}})['cenas']


def _nome(c):
    return Path(str(c.get('img'))).stem if c.get('img') else None


# ───────── detalhe só com resolução; nada de corte nervoso ─────────
def test_plano_longo_ganha_detalhe_so_com_resolucao(tmp_path):
    cenas, _ = _montar(tmp_path, _ideias(3), [3.0, 6.0, 6.0, 2.0], {'a1': (1800, 2700), 'a2': (900, 600)})
    p1 = [c for c in cenas if c.get('grupo') == 1]
    p2 = [c for c in cenas if c.get('grupo') == 2]
    assert len(p1) == 2 and p1[1]['zoom_detalhe'] >= main.DETALHE_MIN and {_nome(c) for c in p1} == {'a1'}
    assert all(c['end'] - c['start'] >= main.PLANO_MIN for c in p1)
    assert len(p2) == 1 and p2[0]['end'] - p2[0]['start'] == 6.0                # foto pequena: fica inteira


def test_documento_so_ganha_detalhe_depois_do_tempo_de_leitura(tmp_path):
    ids = _ideias(2)
    ids[1]['sb']['midia_preferida'] = 'documento'
    cenas, _ = _montar(tmp_path, ids, [3.0, 6.0, 2.0], {'a1': (1800, 2700)})
    doc = [c for c in cenas if c.get('grupo') == 1]
    assert doc[0]['end'] - doc[0]['start'] >= 0.6 * 6.0 - 1e-6


# ───────── nada antecipado, nada voltando ─────────
def test_ideia_sem_imagem_continua_a_anterior_e_nunca_antecipa_a_proxima(tmp_path):
    cenas, _ = _montar(tmp_path, _ideias(5, sem=(0, 2)), [3.0] * 5 + [2.0])
    por = {c['grupo']: _nome(c) for c in cenas if c.get('grupo') is not None}
    assert por[2] == 'a1'                                                          # continua a anterior (contexto)
    assert por[0] == 'a1'                                                          # só o gancho abre com a seguinte
    ordem = [c['grupo'] for c in cenas if c.get('grupo') is not None]
    for c in cenas[1:]:
        dona = int(_nome(c)[1:]) if _nome(c) else None
        if dona is not None and c.get('grupo') is not None:
            assert dona <= c['grupo'], f'imagem da ideia {dona} antes da hora na ideia {c["grupo"]}'
    vistas, ant = set(), None
    for c in cenas[:-1]:
        n = _nome(c)
        assert not (n != ant and n in vistas)                                     # sem A-B-A
        vistas.add(n); ant = n
    assert ordem == sorted(ordem)


def test_imagem_aparece_quando_a_narracao_dela_comeca(tmp_path):
    cenas, tempos = _montar(tmp_path, _ideias(4), [3.0, 6.0, 3.0, 3.0, 2.0], {'a1': (1800, 2700)})
    for g, (a, _) in enumerate(tempos[:-1]):
        primeiro = next(c for c in cenas if c.get('grupo') == g)
        assert primeiro['start'] == a and primeiro['sb']['span'][0] == a


# ───────── transição pelo motivo, sem tela preta ─────────
def test_transicao_pelo_motivo_e_sem_tela_preta(tmp_path):
    ids = _ideias(5, evento_igual=(2,))
    ids[3]['lugar'] = 'VIENA · 1925'
    ids[4]['sb']['proposito'] = 'virada'
    cenas, _ = _montar(tmp_path, ids, [3.0, 6.0, 3.0, 3.0, 3.0, 2.0], {'a1': (1800, 2700)})
    tr = {(c['grupo'], c.get('sub') or 0): c.get('transicao') for c in cenas if c.get('grupo') is not None}
    assert tr[(1, 1)] == 'corte'                                                   # detalhe da mesma ideia
    assert tr[(2, 0)] == 'corte'                                                   # mesmo acontecimento
    assert tr[(3, 0)] == 'zoom'                                                    # mudou de lugar/tempo
    assert tr[(4, 0)] == 'chicote'                                                 # contraste
    assert 'preto' not in tr.values()


def test_roteiro_antigo_sem_storyboard_fica_com_as_transicoes_de_sempre(tmp_path):
    cenas_v = [{'tipo': 'gancho', 'fala': 'a', 'foto': 'a0'}, {'tipo': 'historia', 'fala': 'b', 'foto': 'a1'},
               {'tipo': 'fechamento', 'fala': 'c'}]
    cenas, _ = _montar(tmp_path, cenas_v, [3.0, 3.0, 2.0])
    assert not any(c.get('transicao') for c in cenas)


# ───────── detector: idêntica × geométrica × semântica ─────────
def _plano(t0, t1, img='x.jpg', **kw):
    return {'tipo': 'historia', 'img': img, 'start': t0, 'end': t1, **kw}


def test_detector_separa_identica_geometrica_e_semantica():
    ken_burns = estaticos.medir_movimento([_plano(0, 6, camera='aproxima')])
    sub_fraco = estaticos.medir_movimento([_plano(0, 3, camera='aproxima', evento='e'), _plano(3, 6, sub=1, evento='e')])
    detalhe = estaticos.medir_movimento([_plano(0, 3, camera='aproxima', evento='e'), _plano(3, 6, sub=1, evento='e', zoom_detalhe=1.6)])
    troca = estaticos.medir_movimento([_plano(0, 3), _plano(3, 6, img='y.jpg')])
    assert ken_burns['movimento'] == 0 and ken_burns['frac_estatica'] == 1.0      # cosmético não conta
    assert sub_fraco['movimento'] == 0 and sub_fraco['frac_estatica'] == 1.0
    assert detalhe['movimento'] == 1 and detalhe['semanticas'] == 0 and detalhe['frac_estatica'] == 0.0
    assert troca['semanticas'] == 1 and troca['movimento'] == 0


@precisa_navegador
def test_template_aplica_o_detalhe_como_o_detector_calcula(tmp_path):
    from playwright.sync_api import sync_playwright
    from src.render import render
    from tests.caso_tela import coober_pedy
    d = coober_pedy(tmp_path / 'f')
    k = next(i for i, sc in enumerate(d['scenes']) if sc['tipo'] == 'historia' and sc.get('img'))
    d['scenes'][k].update(sub=1, zoom_detalhe=1.6, moldura=False)
    dados = render.preparar(d)
    pagina = render._escrever_pagina(dados, tmp_path)
    with sync_playwright() as p:
        nav = p.chromium.launch(args=render.NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(pagina.as_uri())
        pg.wait_for_function('window.READY===true', timeout=60000)
        sc = dados['scenes'][k]
        tr = pg.evaluate(f"CAMERA(D.scenes[{k}], {sc['start'] + 0.1})")
        nav.close()
    assert tr.startswith('scale(1.6')
    v = estaticos._vista(dict(sc, sub=1, zoom_detalhe=1.6), sc['start'] + 0.1, k)
    assert abs((v[2] - v[0]) - 1 / 1.6) < 0.01                                     # a mesma vista que o detector usa
