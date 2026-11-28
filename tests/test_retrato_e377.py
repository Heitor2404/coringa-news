from src import midia
from src.v4 import acervo_v4 as A
def test_vertical_derivative_and_title(monkeypatch):
    p={'title':'File:Waterfall.webm','pageid':1,'videoinfo':[{'url':'https://upload.wikimedia.org/a.webm','width':1080,'height':1920,'size':5000000,'duration':5,
       'descriptionurl':'https://commons.wikimedia.org/wiki/File:Waterfall.webm','extmetadata':{'LicenseShortName':{'value':'CC BY 4.0'},'ImageDescription':{'value':'View of the falls'}},
       'derivatives':[{'src':'https://upload.wikimedia.org/s.webm','width':360,'height':640},{'src':'https://upload.wikimedia.org/l.webm','width':1080,'height':1920}]}]}
    monkeypatch.setattr(midia,'_commons',lambda *a,**kw:[p])
    monkeypatch.setattr(midia,'_relevante',lambda *a:True)
    monkeypatch.setattr(midia,'_licenca_ok',lambda *a:True)
    c=midia.candidatos_arquivo('waterfall',estrito=True,preferir_vertical=True,pesquisa_retrato=True)[0]
    assert c['w']==1080 and c['h']==1920 and c['titulo']=='Waterfall'
    assert len(c['variantes'])==2
def test_portrait_route_budget_and_canonical_source(monkeypatch):
    def fn(q):return [{'titulo':'waterfall','url':'https://upload.wikimedia.org/'+str(len(calls))+'.webm','w':1920,'h':1080}]
    calls=[]
    def route(name):
        def f(q):
            calls.append(name)
            if name=='commons_video_retrato':return [{'titulo':'waterfall','url':'https://upload.wikimedia.org/vertical.webm','w':1080,'h':1920}]
            return fn(q)
        return f
    monkeypatch.setattr(A,'fontes_documentais',lambda kind,**kw:[(x,route(x)) for x in ('commons_video','figshare','nasa_video','commons_video_retrato')])
    n=dict(id='n',necessidade='registro',evidencia_visual='movimento',preferir_imersao_vertical=True,pesquisa={'consultas_en':['waterfall']})
    r=A.pesquisar_cobertura(n,progressivo=True,max_buscas=3)
    assert calls==['commons_video','figshare','commons_video_retrato']
    assert r['buscas'][-1]['prioridade']=='ALTERNATIVA_RETRATO' and len(r['buscas'])==3
    assert any(c['fonte']=='commons_video' and c['altura_declarada']==1920 for c in r['candidatos'])


def test_native_original_rescues_608px_derivative(monkeypatch):
    p={'title':'File:Train.webm','pageid':1,'videoinfo':[{'url':'https://upload.wikimedia.org/native.webm','width':1080,'height':1920,'size':7000000,'duration':8,'descriptionurl':'https://commons.wikimedia.org/wiki/File:Train.webm','extmetadata':{'LicenseShortName':{'value':'CC BY 4.0'}},'derivatives':[{'src':'https://upload.wikimedia.org/low.webm','width':608,'height':1080,'size':1000000}]}]}
    monkeypatch.setattr(midia,'_commons',lambda *a,**kw:[p])
    monkeypatch.setattr(midia,'_relevante',lambda *a:True)
    monkeypatch.setattr(midia,'_licenca_ok',lambda *a:True)
    c=midia.candidatos_arquivo('train',estrito=True,preferir_vertical=True,pesquisa_retrato=True)[0]
    assert (c['w'],c['h'])==(1080,1920) and not c['derivado']
    assert c['variantes'][0]['size']==7000000 and c['variantes'][1]['width']==608
    p['videoinfo'][0]['size']=80000001
    c=midia.candidatos_arquivo('train',estrito=True,preferir_vertical=True,pesquisa_retrato=True)[0]
    assert c['w']==608 and c['derivado']
