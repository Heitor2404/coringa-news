import json,pytest
from src.v4 import fontes_culturais_e366 as F,acervo_v4 as A
class T:
    def __init__(self,data):self.data=data;self.calls=[]
    def get(self,url,hosts,lim):self.calls.append((url,hosts,lim));return json.dumps(self.data).encode()
def test_smithsonian_media_not_metadata_license():
    media=dict(type='Images',content='https://ids.si.edu/ids/deliveryService/id/abc',idsId='abc',usage={'access':'CC0'})
    dnr=dict(record_link='http://n2t.net/ark:/65665/record',data_source='National Air and Space Museum',
             metadata_usage={'access':'CC0'},online_media={'media':[dict(media,usage={'access':'Usage conditions apply'}),media]})
    t=T({'response':{'rows':[dict(id='record',title='engine',content={'descriptiveNonRepeating':dnr})]}})
    diagnostico={}
    raw=F.smithsonian('engine',transport=t,key='test',diagnostico=diagnostico)
    assert diagnostico['reasons']=={'MEDIA_RIGHTS_NOT_CC0':1}
    assert 'media_usage%3ACC0' in t.calls[0][0]
    assert len(raw)==1 and raw[0]['recibo_fonte']['media_access']=='CC0'
    c=A._candidato_documental(raw[0],'smithsonian','foto')
    assert c['direitos']=='REVISAR_PAGINA_INDIVIDUAL' and not c['publicar']
    assert F.smithsonian_choices(c)[0][0]['url']==media['content']
    with pytest.raises(ValueError):F.smithsonian_choices(dict(c,url='https://evil.test/a.jpg'))
def test_europeana_page_not_record_license_as_media():
    t=T({'items':[dict(id='/1/abc',guid='https://www.europeana.eu/en/item/1/abc',title=['engine'],
          edmIsShownBy=['https://museum.example/a.jpg'],rights=['https://creativecommons.org/licenses/by/4.0/'])]})
    c=F.europeana('engine','foto',transport=t,key='test')[0]
    assert c['url']==c['pagina'] and not c['licenca'] and c['recibo_fonte']['resource_rights']=='PENDENTE'
def test_keys_absent_no_network(monkeypatch):
    monkeypatch.delenv('DATA_GOV_API_KEY',raising=False);monkeypatch.delenv('EUROPEANA_API_KEY',raising=False)
    t=T({})
    assert F.smithsonian('engine',transport=t)==[] and F.europeana('engine','video',transport=t)==[]
    assert not t.calls

def test_smithsonian_search_filter_and_rejection_counts():
    from urllib.parse import parse_qs,urlsplit
    dnr=dict(record_link='http://n2t.net/ark:/65665/record',data_source='Museum',online_media={'media':[dict(type='Images',content='https://ids.si.edu/ids/deliveryService/id/abc',usage={'access':'Usage conditions apply'})]})
    t=T({'response':{'rows':[dict(id='record',content={'descriptiveNonRepeating':dnr})]}})
    diag={}
    assert F.smithsonian('steam locomotive',transport=t,key='test',diagnostico=diag)==[]
    assert 'online_media_type:"Images"' in parse_qs(urlsplit(t.calls[0][0]).query)['q'][0]
    assert diag['counts']['non_cc0_or_non_image']==1 and diag['counts']['retained']==0
