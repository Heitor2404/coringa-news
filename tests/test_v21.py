"""Testes da V2.1 (refinamento). Cada teste corresponde a um defeito encontrado e corrigido neste ramo.
Teste automático não é aprovação visual: as capturas e a galeria ficam para a avaliação do Heitor."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from src.v2 import avaliacao_fiscal, avaliacao_selecao, capacidades, experimental, galeria, geo, palco
from src.v2.temas_exemplo import TEMAS

TEM_NE = (palco.PASTA / 'dados' / 'ne').exists()


# ---------- seleção visual ----------
def test_selecao_8_dominios_e_negativos():
    r = avaliacao_selecao.rodar()
    falhas = [x['id'] for x in r['positivos'] + r['negativos'] if not x['passou']]
    assert not falhas, falhas
    assert set(r['por_dominio']) == {'historia', 'geografia', 'biologia', 'quimica', 'fisica', 'astronomia', 'tecnologia', 'fenomenos'}


def test_reserva_e_medida_nao_portao():
    # o conjunto de reserva mede a generalização (10/16 na primeira rodada); não é ajustado para passar
    r = avaliacao_selecao.rodar()
    assert r['reserva_total'] == 16 and 0 <= r['reserva_passaram'] <= 16


def test_negativo_nunca_inventa_grafico_mapa_ou_numero():
    for x in avaliacao_selecao.rodar()['negativos']:
        assert x['escolha'] not in x['proibidos'], x


def test_coordenada_invalida_nao_conta_como_ponto():
    r = capacidades.escolher({'fala': 'O navio vai de Santos até Roterdã.'}, {'pontos': [{'lon': -46, 'lat': -24}, {'lon': 4, 'lat': 999}]})
    assert r['comp'] is None and 'pontos' in r['limitacao']


# ---------- fiscal ----------
def test_fiscal_detecta_defeitos_injetados_sem_falso_positivo():
    r = avaliacao_fiscal.rodar()
    assert r['detectados'] == r['total'] and r['falsos_positivos'] == 0, [x for x in r['casos'] if not x['detectou'] or x['falso_positivo']]


def test_fiscal_tem_tres_categorias_e_estetica_nao_bloqueia():
    from src.v2 import fiscal_v2
    d = {'duration': 4, 'scenes': [{'comp': 'foto.documental', 'start': 0, 'end': 4, 'params': {}}], 'captions': []}
    r = fiscal_v2.avaliar(d, [{}], [])
    assert set(r['por_categoria']) == {'deterministico', 'semantico', 'estetico'}
    assert r['por_categoria']['estetico']['bloqueios'] == 0
    for a in r['achados']:
        assert {'cena', 'instante', 'problema', 'evidencia', 'gravidade', 'solucao'} <= set(a)


# ---------- geografia ----------
def test_rota_maritima_reta_sobre_continente_e_rejeitada():
    assert not geo.validar_rota([[-74.0, 40.7], [-122.4, 37.8]], 'maritima')['ok']
    rotas = TEMAS['mapas'][1]['scenes'][2]['params']['rotas']
    for r in rotas:
        assert geo.validar_rota(r['rota'], 'maritima')['ok'], r['nome']


def test_caixa_nao_passa_dos_polos():
    bb = geo.caixa_de([(-74, 40), (-70, -57)], folga=3)
    assert bb[1] >= -80 and bb[3] <= 84 and bb[0] >= -180 and bb[2] <= 180


@pytest.mark.skipif(not TEM_NE, reason='Natural Earth não baixado (scripts/v2_natural_earth.py)')
def test_mapa_mundial_cabe_no_quadro_e_nomes_nao_somem(tmp_path):
    d = galeria._resolver(json.loads(json.dumps(TEMAS['mapas'][1])), galeria.midia(avisar=False))
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        sc = d['scenes'][2]
        pg.evaluate(f"seek({sc['end'] - .2:.2f})")
        k = 2
        ys = pg.evaluate(f"""(()=>{{const c=V2.cenas[{k}];const m=c.el.querySelector('.mapa-host')._map;
            return {json.dumps([pt for r in sc['params']['rotas'] for pt in r['rota']])}.map(p=>m.project(p).y)}})()""")
        assert min(ys) > 330 and max(ys) < 1215, (min(ys), max(ys))      # Cabo Horn dentro do quadro
        caixas = pg.evaluate(f"""(()=>{{const c=V2.cenas[{k}].el;const b=e=>{{const r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom,+getComputedStyle(e).opacity]}};
            return {{cab:b(c.querySelector('.cab')),nomes:[...c.querySelectorAll('.rot-mapa.destaque')].map(b)}}}})()""")
        cab = caixas['cab']
        for n in caixas['nomes']:
            assert n[4] > .5
            assert n[1] >= cab[3] or n[3] <= cab[1], ('nome sob o cabeçalho', n)
        a, b = caixas['nomes'][:2]
        assert not (a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]), 'nomes de pino se cruzam'


# ---------- acervo ----------
def test_falta_de_foto_vira_substituto_marcado(monkeypatch, tmp_path):
    monkeypatch.setattr(galeria, 'AUD', tmp_path / 'nao_existe')
    M = galeria.midia(avisar=False)
    assert 'substitutos' in M['navio_eclusa'] and Path(M['navio_eclusa']).exists()
    assert M['navio_eclusa'] != M.get('fundo_b')


# ---------- eclusa: física e sentido ----------
@pytest.mark.parametrize('sentido', ['subir', 'descer'])
def test_eclusa_estado_fisico(tmp_path, sentido):
    m = next(x for x in galeria.catalogo(tmp_path / 'cat') if x['id'] == 'mecanismo.eclusa')
    d = galeria.dados_exemplo(m)
    d['scenes'][0]['params']['sentido'] = sentido
    T = d['scenes'][0]['params']['tempos']
    with palco.abrir(palco.preparar(d), tmp_path / 'p') as pg:
        est = lambda t: (pg.evaluate(f'seek({t})'), pg.evaluate('V2.cenas[0].ctx.estadoFisico'))[1]
        antes, ig, depois = est(T[1] - .2), est(T[2] + .05), est(T[2] + 1.0)
        assert not antes['comporta_frente_aberta']                 # nunca abre com desnível
        assert abs(ig['delta_m']) < .3                              # no instante combinado os níveis estão iguais
        assert depois['comporta_frente_aberta']
        assert abs(antes['delta_m']) > 5


# ---------- legenda ----------
def test_legenda_sobreposta_mostra_o_bloco_mais_recente(tmp_path):
    caps = [{'start': 0.2, 'end': 1.3, 'words': [{'w': 'PRIMEIRO', 's': .2}, {'w': 'BLOCO', 's': .6}]},
            {'start': 1.1, 'end': 2.2, 'words': [{'w': 'SEGUNDO', 's': 1.1}, {'w': 'AQUI', 's': 1.5}]}]
    d = {'duration': 3, 'meta': {'motor': 'v2'}, 'captions': caps,
         'scenes': [{'comp': 'destaque.palavras', 'start': 0, 'end': 3, 'params': {'frase': 'Uma *frase* qualquer de teste.'}}]}
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        pg.evaluate('seek(1.15)')
        assert 'SEGUNDO' in pg.evaluate("document.getElementById('legenda').innerText.toUpperCase()")


# ---------- pipeline experimental (sem render) ----------
def test_experimental_amarra_animacao_e_legenda_a_palavra(tmp_path):
    audio, por_cena = experimental.voz(experimental.ROTEIRO, tmp_path, silencio=True)
    dados, direcao, sincs = experimental.montar(experimental.ROTEIRO, por_cena, por_cena[-1][-1]['e'] + 1.2)
    ec = next(s for s in sincs if s['param'] == 'tempos')
    sc = dados['scenes'][ec['cena']]
    assert sc['comp'] == 'mecanismo.eclusa'
    for rel, t in zip(sc['params']['tempos'], ec['instantes_palavra']):
        assert abs(sc['start'] + rel - t) < 1e-3
    caps = dados['captions']
    for a, b in zip(caps, caps[1:]):
        assert a['end'] <= b['start'] + 1e-6, 'blocos de legenda se sobrepõem'
    num = [sc for sc in dados['scenes'] if sc['comp'] == 'numero.animado']
    assert any(sc['params'].get('prefixo', '').startswith('US$') and 'leilão' in sc['params'].get('contexto', '') for sc in num)
    assert not [d for d in direcao if d.get('bloqueio')]


# ---------- integridade ----------
def test_todo_js_do_palco_compila_e_catalogo_completo(tmp_path):
    """Um erro de sintaxe num arquivo de composições derrubava 4 composições do catálogo sem erro visível."""
    import shutil, subprocess
    if shutil.which('node'):
        for f in sorted((palco.PASTA).glob('**/*.js')):
            if 'dados' in f.parts:
                continue
            r = subprocess.run(['node', '--check', str(f)], capture_output=True, text=True)
            assert r.returncode == 0, (f.name, r.stderr[:300])
    ids = {m['id'] for m in galeria.catalogo(tmp_path)}
    assert len(ids) >= 33 and {'foto.historica', 'foto.sequencia', 'comparacao.antes_depois', 'video.documental'} <= ids
