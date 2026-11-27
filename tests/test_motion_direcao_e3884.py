import copy,json
from pathlib import Path
from src.v4.formatos.motion_direcao_e3884 import decidir,ancorar
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

def test_measured_anchor():
    import pytest
    d=decidir(*inputs());s={'id':'fact','start':0,'end':4};r={'shot':'fact','sha256':'a'*64,'source_url':'https://example.org','value':'20','scope':'here','anchor':'VINTE','publish':False};f={'sha256':r['sha256'],'url':r['source_url'],'value':'20','scope':'here','at':1,'publish':False};caps=[{'start':.8,'end':1.4,'words':[{'w':'VINTE'}]}]
    assert ancorar(d,s,f,r,caps)['at']==1
    with pytest.raises(ValueError):ancorar(d,s,f,r,[])
    with pytest.raises(ValueError):ancorar(d,s,{**f,'at':3},r,caps)
    with pytest.raises(ValueError):ancorar(d,s,{**f,'value':'21'},r,caps)

def test_director_handoff_preserves_original():
    from src.v4.formatos.motion_direcao_e3884 import fila_plano
    n,c,r=inputs()
    plan={'publicar':False,'shots':[{'id':'s','type':'photo'}],'necessidades_direcao':[{'id':'s','fatos':['fact'],'motion_role':n['role'],'motion_purpose':n['purpose'],'exigir_evidencia_direta':False}],'motion_claims':[{'need_id':'s','fact_id':'fact','claim':c,'receipt':r}]}
    original=copy.deepcopy(plan)
    assert fila_plano(plan)[0]['status']=='CHART_CANDIDATE'
    assert fila_plano(plan)[0]['render_authorized'] is False
    assert plan==original
    plan['necessidades_direcao'][0]['exigir_evidencia_direta']=True
    assert fila_plano(plan)[0]['status']=='KEEP_EXISTING'
    plan['necessidades_direcao'][0]['fatos']=['other']
    assert fila_plano(plan)[0]['reason']=='UNBOUND_OR_DUPLICATE_OBLIGATION'
