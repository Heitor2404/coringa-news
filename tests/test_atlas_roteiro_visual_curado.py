"""Pilot-specific shot design smoke; no proof can be invented."""
from src.v4.formatos.roteiro_visual_curado import montar


def _cat():
    return {'relatorio': [
        {'id':'chip-macro','estado':'CANDIDATO_VERIFICADO','asset':'scout:abc'},
        {'id':'wafer-visivel','estado':'CANDIDATO_VERIFICADO','asset':'scout:def'}]}


def test_storyboard_substitui_mapamundi_e_card_por_objetos():
    p=montar(_cat())
    assert len(p['beats'])==5
    assert p['beats'][0]['composicao']=='atlas.prova'
    assert p['beats'][2]['composicao']=='atlas.prova'
    assert p['beats'][3]['composicao']=='atlas.tecnica'
    assert p['beats'][4]['composicao']=='atlas.prova'
    assert p['beats'][3]['camadas'][0]['componente']=='editorial.flowConnections'
    assert not any(b.get('roi') and b['roi'][2]-b['roi'][0]>70 for b in p['beats'])
    assert p['narracao']['texto']


def test_storyboard_nao_segue_sem_imagens_reais():
    import pytest
    with pytest.raises(ValueError,match='SEM_PROVA'):
        montar({'relatorio':[]})
