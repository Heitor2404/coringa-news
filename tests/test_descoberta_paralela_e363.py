from threading import Barrier
import pytest
from src.v4.descoberta_paralela_e363 import RotaPublica,onda
from src.v4 import acervo_v4 as A
from scripts.qa_pesquisa_documental_e246 import usgs_byline
from bs4 import BeautifulSoup

def test_wave_real_overlap_and_failure_isolation():
    gate=Barrier(2,timeout=3)
    def a(q,transport):gate.wait();return [{'titulo':q}]
    def b(q,transport):gate.wait();raise OSError()
    result=onda([(RotaPublica('a.test',a),'first'),(RotaPublica('b.test',b),'second')])
    assert result[0]['raw']==[{'titulo':'first'}] and result[1]['error']=='OSError'
    assert min(x['fim_monotonic'] for x in result)>max(x['inicio_monotonic'] for x in result)
    assert sum(x['rede']['http'] for x in result)==0
def test_wave_refuses_same_origin_and_excess_budget():
    r=RotaPublica('a.test',lambda q,transport:[])
    with pytest.raises(ValueError,match='ORIGEM'):onda([(r,'x'),(r,'y')])
    with pytest.raises(ValueError,match='ORCAMENTO'):onda([(RotaPublica('a.test',r.buscar,9),'x')])
def test_actual_director_uses_wave_without_budget_growth(monkeypatch):
    gate=Barrier(2,timeout=3)
    def a(q,transport):gate.wait();return [{'url':'https://example.org/a','titulo':'a'}]
    def b(q,transport):gate.wait();return [{'url':'https://example.org/a','titulo':'duplicate'},{'url':'https://example.org/b','titulo':'b'}]
    routes=[('commons_video',lambda q:[]),('figshare',lambda q:[]),
            ('usgs_pagina',RotaPublica('a.test',a)),('noaa_pagina',RotaPublica('b.test',b))]
    monkeypatch.setattr(A,'fontes_documentais',lambda kind,**kw:routes)
    n=dict(id='n',necessidade='registro',evidencia_visual='movimento',pesquisa={'consultas_en':['volcanic event']})
    seen=set()
    r=A.pesquisar_cobertura(n,progressivo=True,max_buscas=4,buscas_vistas=seen)
    assert len(seen)==len(r['buscas'])==4 and len(r['candidatos'])==2
    assert r['ondas_publicas'][0]['consultas']==2 and not r['publicar']
def test_usgs_byline_is_explicit_and_not_navigation():
    html='<h1>Video</h1><p>By <a href="/observatories/hvo">Hawaiian Volcano Observatory</a> July 15</p><a href="/centers/test">Unrelated</a>'
    soup=BeautifulSoup(html,'html.parser')
    assert usgs_byline(soup,soup.h1,'https://www.usgs.gov/media/videos/test')['nome']=='Hawaiian Volcano Observatory'
    soup=BeautifulSoup('<h1>Video</h1><a href="/observatories/hvo">Explore Search</a>','html.parser')
    assert usgs_byline(soup,soup.h1,'https://www.usgs.gov/media/videos/test') is None
