from src.v4 import acervo_v4 as A
def test_bounded_fallback_after_empty(monkeypatch):
    calls=[]
    def fn(name,results):
        def f(q):calls.append(name);return results
        return f
    def routes(kind,**kwargs):
        assert kind=='video'
        return [(x,fn(x,[])) for x in ('commons_video','figshare','nasa_video','archive_video')]+[
          ('noaa_pagina',fn('noaa_pagina',[dict(url='https://oceanexplorer.noaa.gov/multimedia/test/',pagina='https://oceanexplorer.noaa.gov/multimedia/test/',titulo='test')]))]
    monkeypatch.setattr(A,'fontes_documentais',routes)
    n=dict(id='x',necessidade='registro',evidencia_visual='movimento',sujeito='test',pesquisa={'consultas_en':['test event']})
    r=A.pesquisar_cobertura(n,max_buscas=3,max_candidatos=5,progressivo=True)
    assert calls==['commons_video','figshare','noaa_pagina'] and len(r['buscas'])==3
    assert not r['publicar'] and r['candidatos'][0]['direitos']=='REVISAR_PAGINA_INDIVIDUAL'
def test_no_forced_route_when_budget_small(monkeypatch):
    calls=[]
    def f(q):calls.append(q);return []
    monkeypatch.setattr(A,'fontes_documentais',lambda kind,**kw:[('commons_video',f),('noaa_pagina',f)])
    n=dict(id='x',necessidade='registro',evidencia_visual='movimento',sujeito='test',pesquisa={'consultas_en':['test event']})
    r=A.pesquisar_cobertura(n,max_buscas=1,progressivo=True)
    assert len(calls)==len(r['buscas'])==1
