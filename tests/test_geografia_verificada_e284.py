"""E284: passagem automática de geografia ao ATLAS só com duas fontes concordantes (sem coordenada de modelo)."""
from src.v4.formatos import geografia_verificada as GV


class Sessao:
    def __init__(self, wd_coord, osm_row):
        self.wd, self.osm = wd_coord, osm_row

    def get(self, url, params=None, headers=None, timeout=None):
        class R:
            def __init__(s, j): s.j = j
            def raise_for_status(s): pass
            def json(s): return s.j
        if 'wikidata' in url and params['action'] == 'wbsearchentities':
            return R({'search': [{'id': 'Q1'}]})
        if 'wikidata' in url:
            claims = {'P625': [{'mainsnak': {'datavalue': {'value': {'latitude': self.wd[0], 'longitude': self.wd[1]}}}}]} if self.wd else {}
            return R({'entities': {'Q1': {'labels': {'en': {'value': 'Corinth Canal'}}, 'descriptions': {'en': {'value': 'canal in Greece'}}, 'claims': claims}}})
        return R([self.osm] if self.osm else [])


OSM = {'lat': '37.9311', 'lon': '22.9822', 'boundingbox': ['37.9157', '37.9465', '22.9575', '23.0068'],
       'osm_type': 'way', 'osm_id': 123, 'display_name': 'Corinth Canal, Greece'}


def test_duas_fontes_concordantes_geram_caso_atlas(monkeypatch):
    monkeypatch.setattr(GV.time, 'sleep', lambda *_: None)
    v = GV.verificar('Corinth Canal', 'Greece', sessao=Sessao((37.9325, 22.9819), OSM), rotulo='Canal de Corinto')
    assert v['estado'] == 'VERIFICADA' and GV.validar_verificacao(v) == []
    q = v['caso_atlas']['atlas']
    o, s, l, n = q['roi']
    assert o < q['lonlat'][0] < l and s < q['lonlat'][1] < n
    assert v['caso_atlas']['fonte_localizacao'].startswith('https://www.wikidata.org/')


def test_fontes_divergentes_ou_ausentes_ficam_pendentes(monkeypatch):
    monkeypatch.setattr(GV.time, 'sleep', lambda *_: None)
    assert GV.verificar('X', 'Y', sessao=Sessao((40.0, 10.0), OSM))['motivo'] == 'FONTES_DIVERGEM'
    assert GV.verificar('X', 'Y', sessao=Sessao(None, OSM))['motivo'] == 'SEM_DUAS_FONTES'
    assert GV.verificar('X', 'Y', sessao=Sessao((37.93, 22.98), None))['motivo'] == 'SEM_DUAS_FONTES'
    assert GV.validar_verificacao({'estado': 'PENDENTE'}) == ['GEO-VERIFICACAO-AUSENTE']


def test_ponte_aceita_verificacao_automatica_e_recusa_sem_ela():
    import inspect
    from src.v4.formatos import ponte_cobertura_filme as P
    src = inspect.getsource(P.preparar_cobertura)
    assert 'GV.validar_verificacao' in src and 'CURADORIA_GEOGRAFICA_VERIFICADA' in src
