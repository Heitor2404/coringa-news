from scripts.qa_replanejamento_e319 import alternatives

def test_alternatives_exclude_reserved_and_cover_later_original():
    r=alternatives(120,3.8,[(0,5),(20,40),(70,90)])
    assert r and max(r)>100 and len(r)<=5
    assert all(not any(t<b and t+3.8>a for a,b in [(0,5),(20,40),(70,90)]) for t in r)
    assert alternatives(3,3.8,[])==[]
    assert alternatives(10,3.8,[(0,10)])==[]
