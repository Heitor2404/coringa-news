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
    monkeypatch.setattr(C.DE,'selecionar_revisados',lambda rows,*a,**k:[{'ordem':0}] if rows else [])
    assert C.alternativa(n,c,lambda *a:None) is None
    row=C.alternativa(n,c,lambda *a:['authenticated'])
    assert row['origem']=='JANELA_HISTORICA_REVALIDADA'
    assert row['rodadas'][0]['pesquisa']['candidatos'][0]['decisao']['revisao_id']=='new'
    assert c['decisao']['revisao_id']=='old' and not row['publicar']


def test_strict_recovery_requires_same_explicit_correspondence(monkeypatch):
    n,c,p=setup()
    monkeypatch.setattr(C.R,'decidir',lambda *a,**k:{'estado':'PERTINENTE_PRIVADO','revisao_id':'new'})
    monkeypatch.setattr(C.DE,'candidato_revisado',lambda *a,**k:{'estado':'CANDIDATO_PERTINENTE','revisao_id':'new'})
    monkeypatch.setattr(C.DE,'selecionar_revisados',lambda rows,*a,**k:[{'ordem':0}] if rows else [])
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


def test_reserved_cache_recovery_uses_current_decision_and_rolls_forward_only_when_reservation_accepts(monkeypatch):
    n,c,p=setup();c['decisao']['estado']='PERTINENTE_PRIVADO'
    c['janelas'][0]['decisao']={'estado':'PERTINENTE_PRIVADO'}
    statement={'estado':'direta','referente':'A visible object in the sample','mudanca':'A specific observed displacement','referencia_estavel':'Stable features in the background'}
    p['revisao_assistida'].update(resposta_bruta={'correspondencia_acao':statement},resposta_observada={'correspondencia_acao':statement})
    monkeypatch.setattr(C.R,'decidir',lambda *a,**k:{'estado':'PERTINENTE_PRIVADO','revisao_id':'new'})
    monkeypatch.setattr(C.DE,'candidato_revisado',lambda *a,**k:{'estado':'CANDIDATO_PERTINENTE','revisao_id':'new'})
    monkeypatch.setattr(C.DE,'selecionar_revisados',lambda rows,*a,**k:[{'ordem':0}] if rows else [])
    monkeypatch.setattr(C,'revalidar',lambda *a,**k:{'status':'PIXELS_REVALIDATED','decisao_atual':'PERTINENTE_PRIVADO','correspondencia_explicita':True})
    row={'selecionado':['commons','v'],'rodadas':[{'pesquisa':{'candidatos':[c]}}]}
    for accept in (False,True):
        calls=[];diagnostics=[]
        def reserve(n,x):
            calls.append(x['decisao']['revisao_id']);return accept
        r=C.recuperar_reservada(n,row,None,reserve,diagnosticos=diagnostics)
        assert calls==['new'] and len(diagnostics)==1
        assert bool(r)==accept
        assert c['decisao']['revisao_id']=='old' and 'recuperacao_amostras' not in c


def test_historical_timestamp_precision_is_exactly_six_decimal_tolerance():
    import pytest
    for start in (26.2379090909091,29.986181818181823):
        p={'inicio_s':start,'duracao_s':3.8,'amostras':[{'at':at,'fonte_s':round(start+at,6)} for at in (0,1.9,3.42)]}
        assert C.tempos_amostras(p)==[x['fonte_s'] for x in p['amostras']]
        p['amostras'][0]['fonte_s']-=.000002
        with pytest.raises(ValueError,match='E334-TEMPOS'):C.tempos_amostras(p)

def test_timestamp_order_and_relative_offset_cannot_be_forged():
    import pytest
    p={'inicio_s':1.0,'duracao_s':3.8,'amostras':[{'at':at,'fonte_s':1+at} for at in (0,1.9,3.42)]}
    p['amostras'][2]['at']=3.8
    with pytest.raises(ValueError,match='E334-TEMPOS'):C.tempos_amostras(p)
    p['amostras'][2]={'at':1.9,'fonte_s':2.9}
    with pytest.raises(ValueError,match='E334-TEMPOS'):C.tempos_amostras(p)
