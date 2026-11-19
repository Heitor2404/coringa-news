"""Stage cinematic Panama: no decorative geography, actual movement and honest illustration."""
import json
from pathlib import Path

from src.v4.formatos.filme_editorial import avaliar, preparar

ROOT=Path(__file__).resolve().parents[1]


def _p():
    return json.loads((ROOT/'docs/v4/formatos/filme_panama_12s_prova.json').read_text())


def test_two_real_clips_and_mechanism_action():
    p=_p()
    r=avaliar(p)
    assert r['pronto'], r['bloqueios']
    assert sum(s['type']=='video' for s in p['shots'])==2
    assert sum(s['type']=='mechanism' for s in p['shots'])==1
    assert sum(s['type']=='photo' for s in p['shots'])==1
    assert r['medias_unicas']==3
    assert p['shots'][1]['evidence']=='explainer'
    assert not any(s['type']=='comparison' for s in p['shots'])


def test_mechanism_never_claims_literal_footage():
    p=_p()
    p['shots'][1]['evidence']='literal'
    p['shots'][1]['literal_identity']='filmagem exata da eclusa de 1913'
    r=avaliar(p)
    assert not r['pronto']
    assert 'F-MECANISMO-NÃO-IDENTIFICADO' in [b['codigo'] for b in r['bloqueios']]


def test_mechanism_has_events_during_actual_water_rise():
    p=_p()
    mech=p['shots'][1]
    assert mech['end']-mech['start']>=3.4
    assert len(mech['cues'])>=2
    assert mech['cues'][1]['at']>mech['cues'][0]['at']
    assert not mech.get('asset')
