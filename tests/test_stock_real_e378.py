from src.v4 import fontes_contextuais_e359 as S
def test_declared_ai_and_animation_not_real():
    assert S.stock_declarado_sintetico('rain, ai generated')
    assert S.stock_declarado_sintetico('rain, AI-generated')
    assert S.stock_declarado_sintetico('3D rendering')
    assert not S.stock_declarado_sintetico('train, rail, actual footage')
def test_recheck_existing_cache_without_network(monkeypatch):
    c=lambda i,title:dict(id=i,title=title,variant={'w':1080,'h':1920})
    monkeypatch.setattr(S,'_cached',lambda *a,**kw:{'status':'LEADS','cache_hit':True,'candidates':[c('a','rain AI generated'),c('b','rain window')]})
    r=S.pixabay('rain window')
    assert [x['id'] for x in r['candidates']]==['b'] and r['cache_hit'] is True
    assert r['declared_synthetic_filtered']==1
    monkeypatch.setattr(S,'_cached',lambda *a,**kw:{'status':'LEADS','cache_hit':True,'candidates':[c('a','rain AI generated')]})
    assert S.pixabay('rain window')['status']=='EMPTY'
