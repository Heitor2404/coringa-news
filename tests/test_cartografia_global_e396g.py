import json
from pathlib import Path
import pytest
from src.v4.formatos.cartografia_global_e396g import *
CASES=json.loads(Path('benchmarks/e396g/cases.json').read_text())['cases']
@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_all_cases(case):
    geo=json.loads((GEO/case['geo']).read_text());p=plan(case,geo);rows=specs(case,p)
    check(p,theoretical_layers(rows))
    assert rows and all(r['tiles']<=100 for r in rows)
    assert p['end']>p['start']
def test_cruise_monotone():
    v=[cruise(i/1000) for i in range(1001)]
    assert v[0]==0 and v[-1]==1 and all(a<=b for a,b in zip(v,v[1:]))
    assert max(b-a for a,b in zip(v,v[1:]))<.0013
def test_unhandled_polar_and_antimeridian():
    for roi in ([179,-3,-179,3],[-10,84,10,89]):
        with pytest.raises(ValueError,match='GLOBAL-ROI'):plan({'id':'test','source':'https://example.org','roi':roi},{})

def test_timing_and_complete_route():
    for c in CASES:
        geo=json.loads((GEO/c['geo']).read_text());p=plan(c,geo)
        assert abs((p['end']-p['start'])/(p['arrival']-.05)-ZOOM_PER_SECOND)<.03
        if p['route']:
            assert p['follow_end']<p['duration'] and ROUTE_SECONDS_MIN-.02<=p['follow_end']-p['follow_start']<=ROUTE_SECONDS_MAX+.02

def test_return_to_overview():
    c=next(c for c in CASES if c['route']);geo=json.loads((GEO/c['geo']).read_text());p=plan(c,geo)
    assert camera_zoom(p,p['follow_end'])==pytest.approx(p['detail'])
    assert camera_zoom(p,p['follow_end']+1.4)==pytest.approx(p['end'])
    assert p['duration']>p['follow_end']+1.4
