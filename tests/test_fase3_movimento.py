"""Fase 3, correção 3 (12/11/2026): planos longos e movimento com propósito — sem cortes novos, sem imagem nova.
Câmera pelo que o plano mostra, transição pela mudança de acontecimento, cartões seguidos viram UM quadro que cresce
com a narração (linha do tempo se há datas; senão lista). Sem vídeo, sem IA."""
import copy
from pathlib import Path

import pytest

import main
from src import acontecimentos as ac, estaticos

AC = lambda quem='', onde='', quando='', recurso='': {'quem': quem, 'onde': onde, 'quando': quando, 'recurso': recurso}


def _p(g, t0, t1, img=None, **k):
    return {'tipo': 'historia', 'grupo': g, 'evento': k.pop('evento', f'e{g}'), 'start': t0, 'end': t1, 'img': img,
            'fala': k.pop('fala', f'Frase *{g}*'), 'acontecimento': k.pop('acontecimento', AC()), **k}


# ───────── câmera e transição ─────────
def test_camera_pelo_que_o_plano_mostra_e_sem_repetir_direcao():
    cenas = [{'tipo': 'gancho', 'grupo': 0, 'evento': 'e0', 'start': 0, 'end': 3, 'img': 'g.jpg'},
             _p(1, 3, 6, 'lustig.jpg', relacao='pessoa'),
             _p(2, 6, 9, 'jornal.jpg', relacao='documento'),
             _p(3, 9, 12, 'paris.jpg', relacao='lugar'),
             _p(4, 12, 15, 'rua.jpg', relacao='ambiente'),
             _p(5, 15, 18, 'torre.jpg', relacao='fato'),
             _p(5, 18, 21, 'torre.jpg', relacao='fato', sub=1),
             _p(6, 21, 24, 'v.jpg', video={'dir': 'x', 'n': 30}),
             _p(7, 24, 27, 'tremor.jpg', relacao='fato', camera='tremor')]
    main._dar_movimento(cenas)
    cams = [c.get('camera') for c in cenas]
    assert cams[0] is None and cams[1] == 'aproxima'                     # gancho intocado; retrato: aproxima
    assert cams[2] == 'afasta'                                           # documento logo depois: não repete "aproxima"
    assert cams[3] == 'esquerda' and cams[4] == 'direita'                # lugar e ambiente: panorâmica, lados alternados
    assert cams[5] == 'afasta' and cams[6] is None                       # reenquadramento segue o detalhe do template
    assert cams[7] is None and cams[8] == 'tremor'                       # vídeo sem câmera; escolha do roteiro fica
    for a, b in zip(cenas, cenas[1:]):
        if a.get('camera') and b.get('camera') and not b.get('sub'):
            assert a['camera'] != b['camera']


def test_transicao_pela_mudanca_de_acontecimento():
    cenas = [_p(1, 0, 3, 'a.jpg', acontecimento=AC(onde='Paris', quando='1925')),
             _p(1, 3, 6, 'a.jpg', sub=1, acontecimento=AC(onde='Paris', quando='1925')),           # mesma ideia
             _p(2, 6, 9, 'b.jpg', evento='e1', acontecimento=AC(onde='Paris', quando='1925')),     # mesmo evento
             _p(3, 9, 12, 'c.jpg', acontecimento=AC(onde='Paris', quando='1927')),                 # outro fato, perto
             _p(4, 12, 15, 'd.jpg', acontecimento=AC(onde='Viena', quando='1935')),                # salto de 8 anos
             _p(5, 15, 18, 'e.jpg', lugar='ALCATRAZ · 1936', acontecimento=AC(quando='1936'))]    # etiqueta do roteiro
    main._dar_movimento(cenas)
    assert [c.get('transicao') for c in cenas] == [None, 'corte', 'corte', None, 'preto', 'preto']


# ───────── cartões seguidos ─────────
def test_cartoes_seguidos_com_datas_viram_linha_do_tempo():
    cenas = [_p(1, 0, 3, 'a.jpg'),
             _p(2, 3, 6, fala='Lustig *fugiu* para Viena', acontecimento=AC('Lustig', 'Viena', '1925')),
             _p(3, 6, 9, fala='Foi *preso* em Nova York', acontecimento=AC('Lustig', 'Nova York', 'dezembro de 1935')),
             _p(4, 9, 12, fala='Morreu em *Alcatraz*', acontecimento=AC('Lustig', 'Alcatraz', '1947')),
             _p(5, 12, 15, 'b.jpg')]
    out = main._juntar_cartoes(copy.deepcopy(cenas))
    assert [c['tipo'] for c in out] == ['historia', 'linha_tempo', 'historia']
    lt = out[1]
    assert lt['itens'] == [{'ano': '1925', 'texto': 'fugiu'}, {'ano': '1935', 'texto': 'preso'}, {'ano': '1947', 'texto': 'Alcatraz'}]
    assert (lt['start'], lt['end'], lt['tempos']) == (3, 12, [3.15, 6.15, 9.15]) and not lt.get('img')
    assert [f['grupo'] for f in lt['fundidas']] == [2, 3, 4]


def test_cartoes_sem_datas_viram_lista_e_pedacos_contam_uma_vez():
    cenas = [_p(1, 0, 3, fala='Poisson *pagou*'), _p(1, 3, 5, fala='a *propina*', sub=1),
             _p(2, 5, 8, fala='E *calou-se* por vergonha'), _p(3, 8, 11, 'x.jpg')]
    out = main._juntar_cartoes(copy.deepcopy(cenas))
    assert out[0]['tipo'] == 'lista' and out[0]['itens'] == ['pagou', 'calou-se'] and out[0]['tempos'] == [0.15, 5.15]
    assert (out[0]['start'], out[0]['end']) == (0, 8) and out[1]['img'] == 'x.jpg'


def test_um_cartao_sozinho_fica_e_fila_longa_vira_blocos_de_4():
    so = [_p(1, 0, 3, 'a.jpg'), _p(2, 3, 6), _p(3, 6, 9, 'b.jpg')]
    assert main._juntar_cartoes(copy.deepcopy(so)) == so
    fila = [_p(k, 3 * k, 3 * k + 3) for k in range(6)]
    out = main._juntar_cartoes(copy.deepcopy(fila))
    assert [c['tipo'] for c in out] == ['lista', 'lista'] and [len(c['itens']) for c in out] == [4, 2]
    fila7 = [_p(k, 3 * k, 3 * k + 3) for k in range(5)]
    assert [c['tipo'] for c in main._juntar_cartoes(fila7)] == ['lista', 'historia']   # sobra 1: fica cartão


def test_linha_do_tempo_so_com_ano_em_todos_e_anos_diferentes():
    mesmo_ano = [_p(1, 0, 3, acontecimento=AC(quando='1925')), _p(2, 3, 6, acontecimento=AC(quando='1925'))]
    falta_ano = [_p(1, 0, 3, acontecimento=AC(quando='1925')), _p(2, 3, 6, acontecimento=AC())]
    assert main._juntar_cartoes(mesmo_ano)[0]['tipo'] == 'lista'
    assert main._juntar_cartoes(falta_ano)[0]['tipo'] == 'lista'


def test_cobertura_conta_cada_fato_do_quadro_e_nada_de_imagem_nova():
    cenas = [_p(1, 0, 3, 'a.jpg', relacao='fato'), _p(2, 3, 6), _p(3, 6, 9), _p(4, 9, 12, 'b.jpg', relacao='pessoa')]
    out = main._juntar_cartoes(copy.deepcopy(cenas))
    cob = ac.cobertura(out)
    assert cob['ideias'] == 4 and cob['contagem']['grafico'] == 2 and cob['contagem']['cartao'] == 0
    assert cob['aba'] == 0 and {c.get('img') for c in out} == {'a.jpg', None, 'b.jpg'}


# ───────── montagem completa ─────────
def _jpg(p: Path):
    from PIL import Image
    Image.new('RGB', (900, 1200), (90, 80, 70)).save(p)
    return p


def test_montagem_com_acontecimentos_sem_a_b_a_sem_cartoes_seguidos(tmp_path):
    v = {'titulo': 'Torre', 'cenas': [
        {'tipo': 'gancho', 'fala': 'Ele vendeu a *torre*', 'imagem': 'a0', 'grupo': 0, 'evento': 'e0'},
        {'tipo': 'historia', 'fala': 'Lustig *forjou* papéis', 'imagem': 'a1', 'grupo': 1, 'evento': 'e1', 'relacao': 'pessoa',
         'acontecimento': AC('Lustig', 'Paris', '1925', 'retrato')},
        {'tipo': 'historia', 'fala': 'Poisson *pagou*', 'grupo': 2, 'evento': 'e2', 'midia': 'cartao', 'acontecimento': AC('Poisson', quando='1925')},
        {'tipo': 'historia', 'fala': 'Lustig *fugiu*', 'grupo': 3, 'evento': 'e3', 'midia': 'cartao', 'acontecimento': AC('Lustig', 'Viena', '1925')},
        {'tipo': 'historia', 'fala': 'Voltou e tentou de *novo*', 'imagem': 'a2', 'grupo': 4, 'evento': 'e4', 'relacao': 'lugar',
         'acontecimento': AC('Lustig', 'Paris', '1926', 'lugar')},
        {'tipo': 'fechamento', 'fala': 'Segue', 'grupo': 5}]}
    reais = {f'a{k}': {'tipo': 'foto', 'arq': _jpg(tmp_path / f'a{k}.jpg'), 'ano': 1925} for k in range(3)}
    tempos = [(0, 3), (3, 8), (8, 11), (11, 14), (14, 22), (22, 24)]
    cenas = main._montar_cenas(v, reais, {}, tempos, tmp_path)
    tipos = [c['tipo'] for c in cenas]
    assert 'lista' in tipos and tipos.count('historia') >= 3
    for a, b in zip(cenas, cenas[1:]):                                   # nunca 2 cartões de texto seguidos
        assert a.get('img') or b.get('img') or a['tipo'] not in ('historia', 'imagem') or b['tipo'] not in ('historia', 'imagem')
    assert ac.aba(cenas) == 0 and not any(c.get('repetida') for c in cenas if c['tipo'] != 'gancho')
    longos = [c for c in cenas if c.get('grupo') == 4]
    assert len(longos) == 3 and len({c['img'] for c in longos}) == 1     # 8 s: a mesma foto, 3 enquadramentos
    assert longos[0]['camera'] == 'esquerda' and [c.get('transicao') for c in longos[1:]] == ['corte', 'corte']


def test_criterio_do_detector_de_estaticos_nao_mudou():
    assert estaticos.ESTATICO_S == 4.0 and main.PLANO_MAX == 3.5


# ───────── na tela ─────────
from tests.test_tela import precisa_navegador   # noqa: E402


@precisa_navegador
def test_quadro_de_cartoes_cresce_com_a_narracao_sem_texto_em_cima(tmp_path):
    from playwright.sync_api import sync_playwright
    from src.render.render import NAVEGADOR, _escrever_pagina, fiscal_tela, preparar
    from tests.caso_tela import _legendas
    from tests.caso_tela import _foto
    foto = _foto(tmp_path, 'torre', 1200, 1600, (120, 100, 80))
    cenas = main._juntar_cartoes([
        _p(1, 0, 3, fala='Lustig *fugiu* para Viena', acontecimento=AC(quando='1925')),
        _p(2, 3, 6, fala='Foi *preso* em Nova York', acontecimento=AC(quando='1935')),
        _p(3, 6, 9, fala='Morreu em *Alcatraz*', acontecimento=AC(quando='1947')),
        _p(9, 9, 10, foto, real=True, foto_wh=[1200, 1600], fala='A *torre*'),
        _p(4, 10, 12, fala='Poisson *pagou*'), _p(5, 12, 15, fala='E *calou-se*')])
    d = preparar({'meta': {'titulo': 'T', 'marca': '@coringa.explica'}, 'scenes': cenas, 'duration': 15.0,
                  'captions': _legendas([(3 * k + 0.1, 3 * k + 2.9, f) for k, f in enumerate(
                      ['Lustig fugiu para Viena', 'Foi preso em Nova York', 'Morreu em Alcatraz', 'Poisson pagou', 'E calou-se'])])})
    assert [c['tipo'] for c in d['scenes']] == ['linha_tempo', 'historia', 'lista']
    assert fiscal_tela(d, tmp_path) == []
    pagina = _escrever_pagina(d, tmp_path)
    with sync_playwright() as p:
        nav = p.chromium.launch(args=NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(Path(pagina).as_uri())
        pg.wait_for_function('window.READY===true', timeout=60000)
        vis = lambda t, sel: (pg.evaluate(f'seek({t})'), pg.evaluate(
            f"() => {{const e=document.querySelector('{sel}');return e?+getComputedStyle(e).opacity:-1}}"))[1]
        assert vis(2.5, '.ev1') < 0.1 and vis(4.5, '.ev1') > 0.9          # o 2º fato entra quando a narração chega
        assert vis(11.5, '.c1') < 0.1 and vis(13.8, '.c1') > 0.9
        nav.close()
