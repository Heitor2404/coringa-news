import json
from pathlib import Path
import pytest
from src.v4.formatos.cartografia_global_e396d import *
CASES=json.loads(Path('benchmarks/e396d/cases.json').read_text())['cases']
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
