"""Terceira família do palco — eclusa HIDRÁULICA no Remotion existente.

Não confundir solver geométrico com inspeção visual independente. O JSON lido
pelo TS tem de corresponder ao PalcoVertical Python. Teste de frames reais no CI.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from src.v4.formatos.palco_vertical import CaixaVisivel, PalcoVertical
from src.v4.formatos.catalogo_mecanismos import CAPACIDADES, decidir
from src.v4.formatos.filme_editorial import avaliar

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'motor4/remotion/src/formatos/palco-eclusa-hidraulica-lab.json'
TS=ROOT/'motor4/remotion/src/formatos/LockCausalCycle.tsx'
ROOT_TS=ROOT/'motor4/remotion/src/Root.tsx'


def load():
    return json.loads(LAB.read_text('utf8'))


def solver(m):
    b=m['caixa_conservadora']
    return PalcoVertical(
        largura=m['canvas']['width'], altura=m['canvas']['height'],
        caixa=CaixaVisivel(b['left'],b['top'],b['right'],b['bottom']),
        editorial_termina_y=m['editorial_termina_y'],
        rodape_comeca_y=m['rodape_comeca_y'],
        folga_superior=m['folga_superior'],
        folga_inferior=m['folga_inferior'],
    )


def test_terceira_familia_eclusa_usa_exatamente_o_mesmo_solver():
    m=load()
    assert m['schema']=='palco-vertical-lab-v1'
    assert m['familia']=='eclusa_hidraulica_ciclo'
    assert m['canvas']=={'width':1080,'height':1920}
    assert solver(m).deslocar()==m['subida_px']==155
    assert solver(m).faixa_resultante()==(453,1345)
    assert m['publicar'] is False
    assert m['tipografia']['rotulos_cotas_y'] < solver(m).faixa_resultante()[0]-20
    assert m['tipografia']['title_y'] < m['tipografia']['rotulos_cotas_y']-50
    assert m['tipografia']['rodape_subida_px'] == 120
    assert solver(m).faixa_resultante()[1] < m['rodape_comeca_y']-m['folga_inferior']


def test_eclusa_nao_reusa_nenhuma_equacao_ou_peca_de_pistao():
    from src.v4.formatos.render_compressor_conjunto_2d import EditorialHeader
    from src.v4.formatos.render_reconstrucao_causal_2d import PALCO_OTTO
    m=load()
    assert (EditorialHeader().palco().deslocar(),PALCO_OTTO.deslocar(),solver(m).deslocar())==(100,28,155)
    assert m['familia'] not in ('compressor_alternativo','motor_otto_4t')
    assert len(m['eventos'])==7
    assert not any('piston' in e['action'] or 'crank' in e['action'] for e in m['eventos'])


def test_reusa_capacidade_de_eclusa_existente_e_sete_eventos_reais():
    m=load()
    c=CAPACIDADES['lock_cycle_standalone']
    assert m['duracao_s']==c.duracao_referencia
    assert tuple(e['action'] for e in m['eventos'])==c.acoes
    assert tuple(e['at'] for e in m['eventos'])==c.tempos_referencia
    assert all(len(e['label'])>9 for e in m['eventos'])
    assert m['eventos'][3]['at']<m['eventos'][4]['at']-5
    scene={'type':'mechanism','mechanism':'auto',
           'processo_visual':{'acoes_necessarias':list(c.acoes),
                             'fases_necessarias':list(c.fases)},
           'cues':m['eventos']}
    assert decidir(scene)==('lock_cycle_standalone',[])


def test_outra_familia_pede_manifesta_o_e_palco_adequados():
    m=load()
    high=solver(m)
    with pytest.raises(ValueError,match="SUBIDA-FORA-DA-AREA"):
        high.deslocar(156)
    with pytest.raises(ValueError,match="SUBIDA-FORA-DA-AREA"):
        high.deslocar(-1)
    with pytest.raises(ValueError,match="SUBIDA-FORA-DA-AREA"):
        high.deslocar(float('nan'))
    bigger=copy.deepcopy(m)
    bigger['caixa_conservadora']['top']=440
    with pytest.raises(ValueError,match="SEMPRE-INVADIRIA"):
        solver(bigger).deslocar()


def test_ts_move_cena_inteira_e_so_no_modo_privado():
    code=TS.read_text('utf8')
    rt=ROOT_TS.read_text('utf8')
    assert "privateStageLayout=false" in code
    assert "privateStageLayout?palcoLaboratorio.subida_px:0" in code
    assert 'id="lock-physical-stage"' in code
    assert 'id="lock-editorial-footer"' in code
    assert 'clipPath="url(#cycleMapClip)"' in code
    assert code.index('id="lock-physical-stage"')<code.index('clipPath="url(#cycleMapClip)"')
    assert code.index('id="lock-physical-stage"')<code.index('AS VÁLVULAS',0) if 'AS VÁLVULAS' in code else True
    assert "privateStageLayout={modo==='compacto'}" in rt
    assert 'id="ProvaPalcoEclusaHidraulica"' in rt
    # Cenários publicados/legados continuam sem flag.
    filmes=(ROOT/'motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text('utf8')
    assert 'privateStageLayout' not in filmes


def test_filme_existente_e_publicacao_continuam_sem_mudanca():
    original=json.loads((ROOT/'docs/v4/formatos/filme_panama_ciclo_19s.json').read_text('utf8'))
    assert avaliar(original)['pronto']
    assert original['tipo']=='PROVA_VISUAL_PRIVADA'
    assert original['shots'][1]['mechanism']=='lock_cycle'
    assert tuple(e['action'] for e in original['shots'][1]['cues'])==CAPACIDADES['lock_cycle'].acoes
    assert original['shots'][1]['reference_asset']==original['shots'][0]['asset']
