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

def test_inclusion_pair_other_theme():
    # Source reviewed 27 Nov 2026: Census 2010 table, Delaware row.
    # Source excerpt is transcribed, not a claimed original byte hash.
    from src.v4.formatos.motion_direcao_e3884 import relacoes_plano
    url='https://www.census.gov/geographies/reference-files/2010/geo/state-area.html.html'
    source={'url':url,'date':'2010','statement':'Delaware: total 6446 km²; land 5047 km²; water 1399 km².'}
    def claim(label,value):
        return {'schema':'coringa.motion.claim.private.v1','publish':False,'fixture':False,'shape':'area','unit':'km²','title':label,'scope':'Delaware · Censo 2010','values':[{'label':label,'value':value}],'relation':'exact','source':source}
    a,z=claim('Área total',6446),claim('Área aquática',1399)
    # Test-only candidate decisions: no fabricated original source checksum.
    plan={'publicar':False,'shots':[{'id':'a','start':0,'end':4},{'id':'b','start':4,'end':8}]}
    cs=[{'status':'CHART_CANDIDATE','need_id':i,'fact_id':i,'claim':c} for i,c in [('a',a),('b',z)]]
    r={'schema':'coringa.motion.inclusion.receipt.private.v1','publish':False,'reviewed':True,'relation':'included_area','total_need':'a','total_fact':'a','part_need':'b','part_fact':'b','source_url':url,'source_date':'2010','statement':'Table separates total area into land and water area.','total_claim':a,'part_claim':z}
    assert relacoes_plano(plan,cs)==[]
    plan['motion_relation_receipts']=[r]
    got=relacoes_plano(plan,cs)[0]
    assert got['status']=='RELATION_CANDIDATE' and abs(got['ratio']-1399/6446)<1e-12 and got['render_authorized'] is False
    assert got['relations'][1]['part']['values'][0]['label']=='Área aquática'
    assert relacoes_plano(plan,cs[:1])[0]['status']=='KEEP_EXISTING'
    r['reviewed']=False
    assert relacoes_plano(plan,cs)[0]['reason']=='NO_REVIEWED_INCLUSION'
    r['reviewed']=True
    r['source_date']='2020'
    assert relacoes_plano(plan,cs)[0]['reason']=='UNBOUND_INCLUSION_SOURCE'
    r['source_date']='2010'
    plan['shots'][1]['start']=5
    assert relacoes_plano(plan,cs)[0]['reason']=='NONCONTIGUOUS_OR_INSUFFICIENT_TIME'
