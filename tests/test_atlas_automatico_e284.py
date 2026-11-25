"""E284: necessidade territorial vira entrega ATLAS pelo caminho existente, só com verificação geográfica."""
from src.v4.formatos import atlas_automatico as AA, geografia_verificada as GV


def _need():
    return {'id': 'n9', 'fatos': ['f9'], 'sujeito': 'Canal de Corinto', 'mostrar': 'localização do canal',
            'necessidade': 'territorio', 'pesquisa': {'contexto_busca': ['Greece']}}


def _ver(estado):
    def v(nome, ctx, **k):
        assert ctx == 'Greece'
        if estado != 'VERIFICADA':
            return {'estado': 'PENDENTE', 'motivo': 'FONTES_DIVERGEM'}
        return {'estado': 'VERIFICADA', 'origem': GV.ORIGEM, 'distancia_km': .2, 'tolerancia_km': 5,
                'wikidata': {'url': 'https://www.wikidata.org/wiki/Q1'}, 'osm': {'url': 'https://www.openstreetmap.org/way/1'},
                'caso_atlas': {'id': 'geo_n9', 'fontes': ['https://www.wikidata.org/wiki/Q1', 'https://www.openstreetmap.org/way/1'],
                               'atlas': {'roi': [22.9, 37.9, 23.0, 38.0], 'label': 'Canal de Corinto', 'lonlat': [22.98, 37.93]}}}
    return v


def test_entrega_automatica_usa_caminho_existente(tmp_path):
    chamadas = []
    e, info = AA.entregar(_need(), tmp_path, verificar=_ver('VERIFICADA'),
                          adquirir=lambda c: chamadas.append('adquirir') or {'bases': []},
                          resolver=lambda c, a, s: (c, {'p': 1}, {'zoom': 9}),
                          mapclip=lambda ch, s, p: (tmp_path / 'mapa.mp4', tmp_path / 'prova.json'), sha=lambda p: 'a' * 64)
    assert info['estado'] == 'ENTREGUE' and e['origem'] == GV.ORIGEM and GV.validar_verificacao(e['verificacao']) == []
    assert chamadas == ['adquirir'] and e['mostrar'] == 'localização do canal'


def test_sem_verificacao_nao_ha_mapa():
    e, info = AA.entregar(_need(), '/tmp', verificar=_ver('PENDENTE'))
    assert e is None and info['estado'] == 'PENDENTE'


def test_completar_nao_substitui_curadoria_e_so_age_em_delegar_atlas(tmp_path):
    rep = {'triagem': [_need()], 'cobertura': [{'necessidade_id': 'n9', 'estado': 'DELEGAR_ATLAS'}]}
    manual = {'atlas': {'n9': {'origem': 'CURADORIA_GEOGRAFICA_VERIFICADA'}}}
    out, log = AA.completar_entregas(rep, manual, tmp_path, verificar=_ver('VERIFICADA'))
    assert out['atlas']['n9']['origem'] == 'CURADORIA_GEOGRAFICA_VERIFICADA' and log == []
    falha = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('render'))
    out, log = AA.completar_entregas(rep, {}, tmp_path, verificar=_ver('VERIFICADA'), adquirir=falha,
                                     resolver=lambda *a: None, mapclip=lambda *a: None, sha=lambda p: '')
    assert 'n9' not in out['atlas'] and log[0]['estado'] == 'PENDENTE'
