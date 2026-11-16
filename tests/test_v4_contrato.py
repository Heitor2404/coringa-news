"""Regras de direção do V4 como comportamento verificável (não prompt)."""
import copy

import pytest

from src.v4 import contrato, diretor
from src.v4.componentes import COMPONENTES, buscar_registro


def _ep(**cena):
    base = {'id': 'c1', 'ini': 0, 'fim': 4, 'fala': 'x', 'objetivo': 'x', 'o_que_precisa_aparecer': 'o navio na eclusa',
            'modalidade': 'registro_foto', 'componente': 'registro.foto', 'params': {'asset': 'a1'}, 'camera': {'tipo': 'fixa'},
            'transicao': {'tipo': 'corte'}}
    base.update(cena)
    return {'versao_contrato': '4.0', 'cenas': [base]}


ACV = {'a1': {'id': 'a1', 'credito': '"x" — y (CC BY-SA 4.0), via Wikimedia Commons', 'licenca': 'CC BY-SA 4.0'}}


def regras(ep, acv=ACV):
    return {v['regra'] for v in contrato.validar(ep, acv) if v['gravidade'] == 'erro'}


def test_cena_valida_passa():
    assert regras(_ep()) == set()


def test_acao_fisica_em_foto_parada_e_erro():
    assert 'R-ACAO-SEM-DEMONSTRACAO' in regras(_ep(o_que_precisa_aparecer='a água enche a câmara e o navio sobe'))


def test_acao_em_esquema_passa():
    ep = _ep(o_que_precisa_aparecer='a água enche e o navio sobe', modalidade='esquema_2d', componente='mecanismo.nivel_vasos', params={})
    assert regras(ep) == set()


def test_recuo_sem_revelacao_e_movimento_sem_motivo():
    r = regras(_ep(camera={'tipo': 'revelar'}))
    assert {'R-RECUO-SEM-REVELACAO', 'R-MOVIMENTO-SEM-MOTIVO', 'R-GANCHO-RECUO'} <= r


def test_zoom_decorativo_nao_existe():
    assert 'R-CAMERA-PROIBIDA' in regras(_ep(camera={'tipo': 'zoom_lento'}))


@pytest.mark.parametrize('t', ['whip', 'iris', 'flash'])
def test_transicoes_proibidas(t):
    assert 'R-TRANSICAO-PROIBIDA' in regras(_ep(transicao={'tipo': t}))


def test_dissolve_exige_motivo():
    assert 'R-TRANSICAO-SEM-MOTIVO' in regras(_ep(transicao={'tipo': 'dissolve'}))
    assert 'R-TRANSICAO-SEM-MOTIVO' not in regras(_ep(transicao={'tipo': 'dissolve', 'justificativa': 'passagem de tempo 1913→hoje'}))


def test_asset_sem_licenca_e_erro():
    assert 'R-ASSET-SEM-LICENCA' in regras(_ep(), {'a1': {'id': 'a1', 'credito': 'x'}})
    assert 'R-ASSET-AUSENTE' in regras(_ep(), {})


def test_repeticao_de_asset():
    ep = _ep()
    c = ep['cenas'][0]
    ep['cenas'] = [dict(c, id=f'c{i}', ini=i * 4, fim=i * 4 + 4) for i in range(3)]
    assert 'R-REPETICAO' in regras(ep)


def test_rota_sem_fonte_e_erro():
    ep = _ep(modalidade='mapa', componente='mapa.rota', params={'rota': {'de': 0, 'ate': 1}})
    assert 'R-ROTA-SEM-FONTE' in regras(ep)


def test_impor_corrige_so_o_que_e_seguro():
    ep = _ep(camera={'tipo': 'zoom'}, transicao={'tipo': 'whip'}, o_que_precisa_aparecer='o navio sobe')
    reg = contrato.impor(ep)
    assert ep['cenas'][0]['camera']['tipo'] == 'fixa' and ep['cenas'][0]['transicao'] == {'tipo': 'corte'} and len(reg) == 2
    assert 'R-ACAO-SEM-DEMONSTRACAO' in regras(ep)              # sem correção segura: continua erro


def test_fracoes_viram_segundos():
    p = diretor.segundos({'rota': {'de': .2, 'ate': .8}, 'tempos': {'entra': .1, 'enche': .4}, 'camera': [{'t': 0, 'zoom': 8.7}], 'desnivel_m': 9}, 10)
    assert p['rota'] == {'de': 2.0, 'ate': 8.0} and p['tempos'] == {'entra': 1.0, 'enche': 4.0} and p['camera'][0]['zoom'] == 8.7 and p['desnivel_m'] == 9


def test_catalogo_inteiro_acessivel_e_filtrado_para_tela_cheia():
    from src.v4.backends import hyperframes as HF
    assert HF.CATALOGO['resumo']['total'] >= 450
    r = buscar_registro('notes reveal', 5)
    assert r and all(x['orientacao'] in ('retrato', 'responsivo') for x in r)


def test_registro_em_paisagem_e_recusado_em_tela_cheia(tmp_path):
    from src.v4.backends import hyperframes as HF
    with pytest.raises(HF.Recusado, match='cartão'):
        HF.render_registro('world-map', {}, 3, tmp_path, tmp_path / 'x.mp4')


def test_todo_componente_tem_despacho():
    import inspect
    from src.v4 import episodio
    fonte = inspect.getsource(episodio.render_cena)
    assert all(f"'{c}'" in fonte for c in COMPONENTES)
