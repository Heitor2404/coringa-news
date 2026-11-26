"""Routing tests: deliberately synthetic packets; actual pixel proof is E333."""
from src.v4.formatos import recuperacao_cache_e333 as C

def setup():
    n={'id':'n','fatos':['f'],'mostrar':'exact action','evidencia_visual':'movimento'}
    p={'revisao_id':'new','publicar':False,'sha256_origem':'h','fato_id':'f','necessidade':'exact action',
       'amostras':[1,2,3],'revisao_assistida':{'revisao_id':'new'}}
    c={'tipo':'video','source_id':'v','fonte':'commons','aquisicao':{'sha256':'h','duration_s':10,'width':1920,'height':1080},
       'decisao':{'revisao_id':'old'},'janelas':[{'pacote':p}]}
    return n,c,p

def test_scope_never_reuses_wrong_fact_or_rejected_revision(monkeypatch):
    n,c,p=setup()
    def fail(*args,**kwargs):raise AssertionError('must not review')
    monkeypatch.setattr(C.R,'decidir',fail)
    for k,v in [('fato_id','other'),('necessidade','other'),('sha256_origem','other'),('publicar',True),('revisao_id','old')]:
        altered={**c,'janelas':[{'pacote':{**p,k:v}}]}
        assert C.alternativa(n,altered,fail) is None

def test_alternative_requires_pixel_callback_and_preserves_original(monkeypatch):
    n,c,p=setup()
    monkeypatch.setattr(C.R,'decidir',lambda *a,**k:{'estado':'PERTINENTE_PRIVADO','revisao_id':'new'})
    monkeypatch.setattr(C.DE,'candidato_revisado',lambda *a,**k:{'estado':'CANDIDATO_PERTINENTE','revisao_id':'new'})
    monkeypatch.setattr(C.DE,'selecionar_revisados',lambda *a,**k:[{'ordem':0}])
    assert C.alternativa(n,c,lambda *a:None) is None
    row=C.alternativa(n,c,lambda *a:['authenticated'])
    assert row['origem']=='JANELA_HISTORICA_REVALIDADA'
    assert row['rodadas'][0]['pesquisa']['candidatos'][0]['decisao']['revisao_id']=='new'
    assert c['decisao']['revisao_id']=='old' and not row['publicar']


def test_strict_recovery_requires_same_explicit_correspondence(monkeypatch):
    n,c,p=setup()
    monkeypatch.setattr(C.R,'decidir',lambda *a,**k:{'estado':'PERTINENTE_PRIVADO','revisao_id':'new'})
    monkeypatch.setattr(C.DE,'candidato_revisado',lambda *a,**k:{'estado':'CANDIDATO_PERTINENTE','revisao_id':'new'})
    monkeypatch.setattr(C.DE,'selecionar_revisados',lambda *a,**k:[{'ordem':0}])
    def forbidden(*a):raise AssertionError('legacy must not be promoted')
    assert C.alternativa(n,c,forbidden,estrita=True) is None
    statement={'estado':'direta','referente':'A visible object in the sample','mudanca':'A specific observed displacement','referencia_estavel':'Stable features in the background'}
    q=p['revisao_assistida'];q['resposta_bruta']={'correspondencia_acao':statement};q['resposta_observada']={'correspondencia_acao':{**statement,'estado':'incerta'}}
    assert C.alternativa(n,c,forbidden,estrita=True) is None
    q['resposta_observada']['correspondencia_acao']=statement
    assert C.alternativa(n,c,lambda *a:True,estrita=True)['origem']=='JANELA_HISTORICA_REVALIDADA'

def test_selected_row_uses_latest_matching_video_only():
    n,c,p=setup();c['decisao']['estado']='PERTINENTE_PRIVADO'
    row={'selecionado':['commons','v'],'rodadas':[{'pesquisa':{'candidatos':[c,{**c,'source_id':'wrong'}]}}]}
    assert C.selecionado(row) is c
