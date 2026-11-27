import copy,json
from pathlib import Path
from src.v4.formatos.motion_direcao_e3884 import decidir
CLAIMS=[s['documentary_chart_trial'] for s in json.loads(Path('benchmarks/e3883/props.json').read_text())['shots']]
def inputs(i=0):
    c=copy.deepcopy(CLAIMS[i]);n={'fact_id':'fact','role':'quantitative_explainer','purpose':['magnitude','magnitude','proportion','comparison','chronology','magnitude'][i],'requires_direct_evidence':False}
    r={'fact_id':'fact','verified_claim':copy.deepcopy(c),'source_sha256':'a'*64,'publish':False}
    return n,c,r
def test_real_families():
    for i,k in enumerate(('range','area','proportion')):
        assert decidir(*inputs(i))['kind']==k
def test_preserves_evidence():
    n,c,r=inputs();n['requires_direct_evidence']=True
    assert decidir(n,c,r)['status']=='KEEP_EXISTING'
def test_no_incidental_number():
    n,c,r=inputs();n['role']='context'
    assert decidir(n,c,r)['status']=='KEEP_EXISTING'
def test_reject_unbound_claim():
    n,c,r=inputs();c['values'][0]['value']=99
    assert decidir(n,c,r)['status']=='KEEP_EXISTING'
def test_reject_wrong_intent_and_fixture():
    n,c,r=inputs();n['purpose']='chronology'
    assert decidir(n,c,r)['status']=='KEEP_EXISTING'
    assert decidir(*inputs(3))['status']=='KEEP_EXISTING'
