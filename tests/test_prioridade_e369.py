from src.v4 import acervo_v4 as A
from src.v4.descoberta_paralela_e363 import RotaPublica
from src.v4.prioridade_fontes_e369 import afinidade,candidato_promissor
from src.v4.fontes_culturais_e366 import smithsonian_redirect
from src.v4.aquisicao_documental import Transporte,AquisiçãoErro
import pytest
def test_specialist_opportunity_and_no_budget_growth(monkeypatch):
    calls=[]
    def broad(q):calls.append('broad');return [{'url':'https://example.org/a','titulo':'octopus underwater'}]
    def specific(q,transport):calls.append('noaa');return [{'url':'https://example.org/b','titulo':'octopus underwater'}]
    monkeypatch.setattr(A,'fontes_documentais',lambda kind,**kw:[('commons_video',broad),('figshare',lambda q:[]),('noaa_pagina',RotaPublica('oceanexplorer.noaa.gov',specific))])
    n=dict(id='n',necessidade='registro',evidencia_visual='movimento',pesquisa={'consultas_en':['octopus underwater']})
    r=A.pesquisar_cobertura(n,max_buscas=2,progressivo=True)
    assert calls==['broad','noaa'] and len(r['buscas'])==2
    assert r['buscas'][1]['prioridade']=='AFINIDADE_FONTE' and not r['publicar']
def test_metadata_is_hint_not_veto():
    n={'necessidade':'registro','pesquisa':{'consultas_en':['octopus underwater']}}
    assert candidato_promissor(n,{'titulo':'octopus underwater'})
    assert not candidato_promissor(n,{'titulo':'unrelated video'})
    assert afinidade(n,'octopus underwater','noaa_pagina')>0
class R:
    def __init__(self,status,location=None):
        self.status_code=status;self.headers={'Location':location} if location else {}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def close(self):pass
    def iter_content(self,n):yield b'abc'
class S:
    def __init__(self,*rs):self.rs=iter(rs);self.calls=[]
    def get(self,url,**kw):self.calls.append(url);return next(self.rs)
def test_redirect_budget_and_explicit_host():
    start='https://ids.si.edu/ids/deliveryService?id=123'
    target='https://ids.si.edu/ids/deliveryService/id/123'
    session=S(R(307,target),R(200))
    t=Transporte(session=session,max_http=2)
    assert t.get(start,{'ids.si.edu'},100,redirect_policy=smithsonian_redirect)==b'abc'
    assert t.http==2 and t.events[0]['redirect_permitido']
    for bad in ('https://evil.test/ids/deliveryService/id/123','http://ids.si.edu/ids/deliveryService/id/123','https://ids.si.edu/other','https://ids.si.edu/ids/deliveryService/%2e%2e/private'):
        t=Transporte(session=S(R(307,bad)))
        with pytest.raises(AquisiçãoErro,match='REDIRECT_PENDENTE'):t.get(start,{'ids.si.edu'},100,redirect_policy=smithsonian_redirect)
        assert t.http==1
def test_other_sources_do_not_follow_redirects():
    t=Transporte(session=S(R(307,'https://ids.si.edu/ids/deliveryService/id/123')))
    with pytest.raises(AquisiçãoErro):t.get('https://ids.si.edu/ids/deliveryService?id=123',{'ids.si.edu'},100)
