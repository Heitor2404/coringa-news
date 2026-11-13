"""V2.2 — centralização horizontal medida (não basta text-align: center).

Critério da ordem: centro da caixa e centro dos glifos a no máximo 20 px de x = 540 (1080 × 1920), e a mesma
proporção na prévia 540 × 960. Medição dupla: pelo DOM (V2.medirCentros) e pelos PIXELS do quadro renderizado.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from PIL import Image

from src.v2 import centros, galeria, palco

CASOS = [   # (texto do bloco, palavras destacadas) — os casos extremos pedidos
    ('GRAVIDADE', {0}), ('I', set()), ('DOIS OCEANOS', set()), ('O NAVIO SOBE 26', {3}), ('A ÁGUA DESCE DO LAGO E ENCHE A CÂMARA INTEIRA', {1, 7}),
    ('INCONSTITUCIONALISSIMAMENTE', set()), ('ESCHERICHIA COLI', {0, 1}), ('US$ 5,3 MILHÕES', {0, 1}), ('— E AGORA?!', set()),
    ('A É PARALELEPÍPEDO', {2}), ('PANAMÁ, 1914.', set()),
]


def _dados(tmp: Path, preto: bool = True, comp='foto.documental', params=None, dur_bloco=1.0):
    img = tmp / 'preto.png'
    Image.new('RGB', (1080, 1920), (8, 8, 10)).save(img)
    caps, t = [], .2
    for txt, hl in CASOS:
        ws = txt.split()
        caps.append({'start': t, 'end': t + dur_bloco - .1, 'words': [{'w': w, 'hl': i in hl, 's': t + i * .05} for i, w in enumerate(ws)]})
        t += dur_bloco
    sc = {'comp': comp, 'start': 0, 'end': t + .2, 'params': params or {'img': str(img)}, 'legenda': 'livre'}
    return {'duration': t + .2, 'meta': {'motor': 'v2'}, 'captions': caps, 'scenes': [sc]}


def test_legenda_casos_extremos_dom(tmp_path):
    d = _dados(tmp_path)
    with palco.abrir(palco.preparar(d), tmp_path / 'p') as pg:
        for c in d['captions']:
            for frac in (.15, .5, .9):     # palavras ainda por dizer / ditas: o conjunto não pode andar
                pg.evaluate(f"seek({c['start'] + (c['end'] - c['start']) * frac:.3f})")
                leg = [m for m in pg.evaluate('V2.medirCentros()') if m['g'] == 'legenda']
                assert len(leg) == 1, c
                m = leg[0]
                assert abs(m['desvio_caixa']) <= centros.TOL_CAIXA and abs(m['desvio_glifos']) <= centros.TOL_GLIFOS, m
                for ln in m['linhas']:     # cada linha centrada, não só o bloco
                    assert abs(ln['centro'] - 540) <= centros.TOL_GLIFOS, (m['texto'], ln)


def test_legenda_casos_extremos_pixels_1080_e_previa_540(tmp_path):
    d = _dados(tmp_path)
    with palco.abrir(palco.preparar(d), tmp_path / 'p') as pg:
        mp4 = palco.previa(pg, 0, d['duration'], tmp_path / 'previa.mp4', fps=10)
        for c in d['captions']:
            t = c['start'] + (c['end'] - c['start']) * .6
            arq = tmp_path / f"q_{t:.2f}.png"
            palco.capturar(pg, t, arq)
            topo = pg.evaluate(f'estadoV2({t:.3f})')['topo'] or 1240
            m = centros.centro_pixels(arq, topo, topo + 260)
            assert m and abs(m['desvio']) <= centros.TOL_GLIFOS, (c['words'][0]['w'], m)
            # mesma cena na prévia proporcional 540×960 (quadro extraído do mp4, sem reescala da medição)
            q = tmp_path / f"p_{t:.2f}.png"
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', str(mp4), '-frames:v', '1', str(q)], check=True)
            im = Image.open(q)
            assert im.size == (540, 960), im.size
            m2 = centros.centro_pixels(im, topo // 2, (topo + 260) // 2)
            assert m2 and abs(m2['desvio']) <= centros.TOL_GLIFOS / 2, (c['words'][0]['w'], m2)


def test_titulo_subtitulo_e_legenda_simultaneos(tmp_path):
    caps = [{'start': .3, 'end': 2.6, 'words': [{'w': w, 'hl': w == 'MECANISMO', 's': .3 + i * .1} for i, w in enumerate('AGORA, O MECANISMO DA ECLUSA.'.split())]}]
    d = {'duration': 3, 'meta': {'motor': 'v2'}, 'captions': caps,
         'scenes': [{'comp': 'titulo.capitulo', 'start': 0, 'end': 3, 'legenda': 'livre',
                     'params': {'numero': '02', 'titulo': 'O *mecanismo*', 'subtitulo': 'como a água faz o trabalho'}}]}
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        pg.evaluate('seek(2.2)')
        ms = {m['g']: m for m in pg.evaluate('V2.medirCentros()')}
        for g in ('tt', 'sb', 'legenda'):
            assert g in ms, (g, list(ms))
            assert abs(ms[g]['desvio_caixa']) <= centros.TOL_CAIXA and abs(ms[g]['desvio_glifos']) <= centros.TOL_GLIFOS, ms[g]


def test_todas_as_composicoes_centro_declarado_no_eixo_inclusive_animado(tmp_path):
    """Cada composição amostrada a cada 0,5 s (entradas, escalas e saídas incluídas). Todo texto centralizado precisa
    declarar a intenção: centro de TELA (data-centro, medido contra x = 540) ou centro LOCAL de um objeto."""
    falhas = []
    for m in galeria.catalogo(tmp_path / 'cat'):
        if m['id'].startswith('mapa.') and not (palco.PASTA / 'dados' / 'ne').exists():
            continue
        d = galeria.dados_exemplo(m)
        with palco.abrir(palco.preparar(d), tmp_path / m['id']) as pg:
            v = centros.violacoes(centros.medir(pg, d['duration'], .5))
        falhas += [(m['id'], 'fora', x['g'], x['desvio_caixa'], x['desvio_glifos'], x['t']) for x in v['centro_fora']]
        falhas += [(m['id'], 'sem intenção', x['g'], x['desvio_caixa'], x['texto']) for x in v['sem_intencao']]
    assert not falhas, falhas


def test_resposta_da_revelacao_nao_sai_do_eixo_durante_a_escala(tmp_path):
    m = next(x for x in galeria.catalogo(tmp_path / 'cat') if x['id'] == 'revelacao.surpresa')
    d = galeria.dados_exemplo(m)
    v = float(d['scenes'][0]['params'].get('virada', 1.2))
    with palco.abrir(palco.preparar(d), tmp_path / 'p') as pg:
        for k in range(0, 12):                      # 0–0,55 s depois da virada: escala 1,25 → 1
            pg.evaluate(f'seek({v + k * .05:.3f})')
            rs = next(x for x in pg.evaluate('V2.medirCentros()') if x['g'] == 'rs')
            assert abs(rs['desvio_glifos']) <= 2, (k, rs)
