import copy,json
from pathlib import Path
from src.v4.formatos.motion_intake_e3888 import integrar,claim_from_fact
from src.v4.formatos.motion_direcao_e3884 import fila_plano,relacoes_plano
from src.v4.formatos.direcao_short_e306 import diagnosticar

# Real historical source receipts, adapter-only test; not new byte verification.
E342=json.loads(Path('benchmarks/e342/dados.json').read_text())['entries']
def sample():
    r=E342[0]
    f={'id':'f','fonte':r['source_url'],'quantitative_review':{'schema':'coringa.fact.quantity.review.private.v1','publish':False,'reviewed':True,'fact_id':'f','relevance':'central','source_url':r['source_url'],'source_sha256':r['sha256'],'source_date':r['source_date'],'statement':r['source_statement'],'review_id':'benchmarks/e342/dados.json#c3-2','measurement':{'kind':'range','title':'VELOCIDADE DA LAVA','scope':r['scope'],'unit':'km/h','qualifier':'approx','values':[{'label':'mínimo','value':21},{'label':'máximo','value':26}]}}}
    n={'id':'n','fatos':['f'],'necessidade':'explicacao_quantitativa','papel_visual':'quantificacao','exigir_evidencia_direta':False,'evidencia_visual':'estatica','mostrar':'explicar magnitude'}
    plan={'publicar':False,'shots':[{'id':'n','start':0,'end':4,'type':'video'}],'necessidades_direcao':[{'id':'n','fatos':['f'],'mostrar':'explicar magnitude','papel_visual':'quantificacao','evidencia_visual':'estatica'}]}
    return {'fatos':[f],'necessidades':[n]},plan

def test_actual_e342_receipt_to_existing_director():
    c,p=sample();before=copy.deepcopy(p);original=copy.deepcopy(c)
    q=integrar(c,p)
    assert p==before and c==original and q['shots']==p['shots']
    assert q['motion_claims'][0]['claim']['shape']=='interval'
    assert q['motion_intake']['source_bytes_reverified'] is False
    assert fila_plano(q)[0]['kind']=='range'
    report=diagnosticar(q)
    assert report['motion_candidates'][0]['kind']=='range'
    assert report['editorial_approval'] is False
def test_protected_missing_and_incidental():
    c,p=sample();c['necessidades'][0]['exigir_evidencia_direta']=True
    q=integrar(c,p)
    assert q['motion_claims']==[] and q['motion_intake']['audit'][0]['status']=='SUPPLEMENT_ONLY'
    del c['necessidades'][0]['exigir_evidencia_direta']
    assert integrar(c,p)['motion_claims']==[]
    c,p=sample();c['fatos'][0]['quantitative_review']['relevance']='incidental'
    assert integrar(c,p)['motion_intake']['audit'][0]['reason']=='INCIDENTAL_QUANTITY'
    c,p=sample();c['fatos'][0]['fonte']='https://example.org/other'
    assert integrar(c,p)['motion_claims']==[]
    c,p=sample();c['fatos'].append(copy.deepcopy(c['fatos'][0]))
    assert integrar(c,p)['motion_intake']['audit'][0]['reason']=='DUPLICATE_FACT'
def test_nonvolcanic_shapes_synthetic_contract_not_real_sources():
    # Hypothetical typed measurements only. No actual claims are asserted.
    cases=[('measurement','m', [{'label':'altura','value':12}],{},'scalar'),
           ('measurement','km²',[{'label':'área','value':2}],{},'area'),
           ('subset','%',[{'label':'produção','value':80}],{'denominator':100},'part'),
           ('comparable','s',[{'label':'A','value':4},{'label':'B','value':8}],{'same_basis':True},'comparison'),
           ('events','',[],{'events':[{'label':'A','date':'1900-01-01'},{'label':'B','date':'1910-01-01'}]},'timeline')]
    for kind,unit,values,extra,expected in cases:
        c,p=sample();f=c['fatos'][0];r=f['quantitative_review'];f['fonte']=r['source_url']='https://example.org/synthetic-contract'
        r['source_sha256']='a'*64;r['review_id']='SYNTHETIC_TEST_ONLY';r['statement']='Hypothetical test data, not source evidence'
        r['measurement']={'kind':kind,'unit':unit,'title':'Teste','scope':'Fixture de contrato','values':values,**extra}
        claim,reason=claim_from_fact(f)
        assert claim['shape']==expected
        q=integrar(c,p)
        assert fila_plano(q)[0]['status']=='CHART_CANDIDATE'
    c,p=sample();m=c['fatos'][0]['quantitative_review']['measurement'];m.update(kind='measurement',unit='USD',values=[{'label':'valor','value':1}])
    assert claim_from_fact(c['fatos'][0])[1]=='SPECIALIZED_MONEY_REVIEW'
def test_historical_case_without_review_untouched():
    p={'publicar':False,'shots':[]}
    assert integrar({'fatos':[{'id':'f','descricao':'2020 e 80%'}]},p) is p
def test_no_relations_guessed_from_units():
    c,p=sample();q=integrar(c,p)
    assert relacoes_plano(q)==[]
def test_ambiguous_quantities_do_not_choose_arbitrarily():
    c,p=sample();f=copy.deepcopy(c['fatos'][0]);f['id']=f['quantitative_review']['fact_id']='g'
    c['fatos'].append(f);p['necessidades_direcao'][0]['fatos'].append('g')
    assert integrar(c,p)['motion_claims']==[]
