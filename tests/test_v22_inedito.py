"""V2.2 — assunto inédito com narração humana real (Venezuela, CC0): o motor decide a partir do contrato do roteirista."""
from pathlib import Path

import pytest

from src.v2 import inedito


@pytest.fixture(scope='module')
def r(tmp_path_factory):
    return inedito.montar(tmp_path_factory.mktemp('ined'))


def test_todas_as_cenas_narradas_escolhidas_pelo_contrato(r):
    narradas = [d for d in r['direcao'] if d.get('fala')]
    assert narradas and all(d.get('origem') == 'contrato' for d in narradas), [(d.get('comp'), d.get('origem')) for d in narradas]
    comps = [sc['comp'] for sc in r['v2']['scenes']]
    assert comps[:5] == ['mapa.territorio', 'mapa.localizacao', 'foto.documental', 'numero.animado', 'mapa.territorio'], comps
    assert comps[-1] == 'encerramento.editorial'


def test_acervo_real_escolheu_foto_de_caracas(r):
    e = next(x for x in r['acervo'] if x['img'])
    assert 'caracas' in Path(e['img']).name.lower()


def test_alinhamento_com_voz_humana(r):
    a = r['alinhamento']
    assert sum(w['casada'] for w in a) / len(a) >= .8          # ≥ 80% das palavras casadas com o reconhecimento
    ts = [w['s'] for w in a]
    assert ts == sorted(ts)                                       # tempos monotônicos


def test_edicao_da_narracao_nao_repete_audio(r):
    c = r['cortes']
    for x, y in zip(c, c[1:]):
        assert x['original_s'][1] <= y['original_s'][0] + 1e-6, c


def test_legenda_dentro_das_cenas_e_em_ordem(r):
    caps = r['v2']['captions']
    for a, b in zip(caps, caps[1:]):
        assert a['end'] <= b['start'] + 1e-6
    assert caps[-1]['end'] <= r['fim_fala'] + .3


def test_vizinhos_acendem_quando_o_nome_e_dito(r):
    sc = r['v2']['scenes'][4]
    viz = {v['nome']: v['t'] for v in sc['params']['vizinhos']}
    assert set(viz) == {'Colômbia', 'Brasil', 'Guiana'}
    palavras = {w['w'].strip(',.').lower(): w['s'] for w in r['trechos'][4]}
    for nome, t in viz.items():
        assert abs(sc['start'] + t - palavras[nome.lower()]) < .02, (nome, t)
    assert viz['Colômbia'] < viz['Brasil'] < viz['Guiana']


@pytest.mark.parametrize('resumo', ['Venezuela: norte da América do Sul, de frente para o Caribe.',
                                    'Quem ergue o navio é a *gravidade*, não uma bomba.', 'Curto.'])
def test_encerramento_mascote_nao_encosta_no_resumo(tmp_path, resumo):
    """Achado do render inédito: com resumo de 3 linhas o chapéu do mascote encostava em 'Caribe.'."""
    from src.v2 import palco
    d = {'duration': 4, 'meta': {'motor': 'v2', 'fontes': ['Wikipédia']}, 'captions': [], 'scenes': [{'comp': 'encerramento.editorial',
         'start': 0, 'end': 4, 'params': {'variante': 'conclusao', 'resumo': resumo, 'mascote': 'apontando', 'marca': '@coringa.explica'}}]}
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        pg.evaluate('seek(3.5)')
        g = pg.evaluate("""(()=>{const e=V2.cenas[0].el,m=e.querySelector('.mascw').getBoundingClientRect(),c=e.querySelector('.mc').getBoundingClientRect();
          const rg=document.createRange(); rg.selectNodeContents(e.querySelector('.rz'));
          const col=[...rg.getClientRects()].filter(q=>q.right>670-24).map(q=>q.bottom);
          return {rz:Math.max(0,...col),m0:m.top,m1:m.bottom,mc:c.top,h:m.height,avisos:V2.avisos}})()""")
    assert g['m0'] >= g['rz'] + 20, g           # espaço entre o texto que entra na coluna do mascote e o mascote
    assert g['m1'] <= g['mc'], g                # mascote acima do painel da marca
    assert g['h'] >= 240 and not g['avisos'], g
    assert abs(g['m0'] - max(560, g['rz'] + 24)) <= 1, g   # encolhe só o que o conflito real exige (linha curta não conta)
