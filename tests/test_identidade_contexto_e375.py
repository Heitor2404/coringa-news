import json
from src.v4 import fontes_publicas_e354 as F,fontes_culturais_e366 as C,acervo_v4 as A,fontes_contextuais_e359 as S
from src.v4.descoberta_paralela_e363 import RotaPublica
from urllib.parse import urlsplit,parse_qs
class T:
    def __init__(self,*rows):self.rows=iter(rows);self.calls=[]
    def get(self,url,*args):self.calls.append(url);return json.dumps(next(self.rows)).encode()
def test_smithsonian_phrase_then_broad():
    t=T({'response':{'rows':[]}},{'response':{'rows':[]}},{'response':{'rows':[]}})
    d={}
    assert C.smithsonian_identidade('steam locomotive photograph',transport=t,key='fixture',diagnostico=d)==[]
    q=parse_qs(urlsplit(t.calls[0]).query)['q'][0]
    assert '"steam locomotive"' in q and 'object_type:"Photographs"' in q
    assert len(t.calls)==3 and 'broad' in d and 'subject_phrase' in d
    q2=parse_qs(urlsplit(t.calls[1]).query)['q'][0]
    q3=parse_qs(urlsplit(t.calls[2]).query)['q'][0]
    assert '"steam locomotive"' in q2 and 'object_type' not in q2
    assert '(steam locomotive)' in q3 and 'photograph' not in q3.lower()
def test_exact_taxon_and_ambiguous_fallback():
    tax={'id':23,'name':'Calypte anna','rank':'species','is_active':True}
    obs={'id':3,'quality_grade':'research','taxon':tax,'photos':[dict(id=2,url='https://inaturalist-open-data.s3.amazonaws.com/photos/2/square.jpg',license_code='cc0',attribution='A')]}
    t=T({'results':[tax]},{'results':[obs]})
    out=F.inaturalist_identidade('Calypte anna',transport=t)
    assert out[0]['recibo_fonte']['requested_taxon_id']==23
    assert parse_qs(urlsplit(t.calls[1]).query)['taxon_id']==['23']
    t=T({'results':[tax,dict(tax,id=24)]},{'results':[]})
    assert F.inaturalist_identidade('Calypte anna',transport=t)==[]
    assert parse_qs(urlsplit(t.calls[1]).query)['q']==['Calypte anna']
def test_stock_context_lane_never_factual(monkeypatch):
    monkeypatch.setenv('CORINGA_STOCK_CONTEXT_ENABLED','1')
    monkeypatch.setenv('PIXABAY_API_KEY','fixture')
    monkeypatch.setenv('CORINGA_STOCK_CACHE_DB','fixture')
    calls=[]
    monkeypatch.setattr(S,'pixabay',lambda q:(calls.append(q) or {'status':'LEADS','candidates':[{'id':'1','editorial_scope':'CONTEXTO_APENAS'}]}))
    monkeypatch.setattr(A,'fontes_documentais',lambda kind,**kw:[('commons',lambda q:[])])
    n=dict(id='n',necessidade='registro',evidencia_visual='contexto',pesquisa={'consultas_en':['city street']})
    r=A.pesquisar_cobertura(n,max_buscas=2,progressivo=True)
    assert len(r['buscas'])==2 and r['stock_contextual']['prova_factual'] is False and not r['candidatos']
    assert r['estado']=='LACUNA_NAO_VERIFICADA'
    n['evidencia_visual']='movimento'
    r=A.pesquisar_cobertura(n,max_buscas=2,progressivo=True)
    assert 'stock_contextual' not in r and len(calls)==1
    n.update(evidencia_visual='contexto',exigir_evidencia_direta=True)
    assert 'stock_contextual' not in A.pesquisar_cobertura(n,max_buscas=2,progressivo=True)


def test_subject_phrase_avoids_unnecessary_third_call():
    record={'id':'rec','title':'Steam locomotive','content':{'descriptiveNonRepeating':{'record_link':'https://americanhistory.si.edu/collections/object/nmah_1','data_source':'Museum','online_media':{'media':[{'type':'Images','usage':{'access':'CC0'},'content':'https://ids.si.edu/ids/deliveryService?id=1','idsId':'1'}]}},'indexedStructured':{'object_type':['Photographs']}}}
    t=T({'response':{'rows':[]}},{'response':{'rows':[record]}})
    d={}
    out=C.smithsonian_identidade('steam locomotive photograph',transport=t,key='fixture',diagnostico=d)
    assert len(t.calls)==2 and len(out)==1 and 'broad' not in d
    assert out[0]['recibo_fonte']['media_access']=='CC0'
