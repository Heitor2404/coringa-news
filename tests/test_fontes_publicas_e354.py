import json
import pytest
from src.v4 import fontes_publicas_e354 as F
from src.v4 import acervo_v4 as A
class T:
    def __init__(self,data):self.data=data;self.calls=[]
    def get(self,url,hosts,lim):
        self.calls.append((url,hosts,lim))
        return self.data if isinstance(self.data,bytes) else json.dumps(self.data).encode()
def ov(**kw):
    return dict(id='item',title='bird',url='https://live.staticflickr.com/1/2.jpg',foreign_landing_url='https://www.flickr.com/photos/a/2',creator='Author',license='by',license_version='4.0',license_url='https://creativecommons.org/licenses/by/4.0/',width=1200,height=1600,**kw)
def test_openverse_keeps_original_and_pending():
    row=ov(); bad=dict(row,license='by-nc'); malicious=dict(row,url='https://evil.test/a.jpg')
    t=T({'results':[bad,malicious,row]});out=F.openverse('bird',transport=t)
    assert len(out)==1 and len(t.calls)==1
    c=A._candidato_documental(out[0],'openverse','foto')
    assert c['direitos']=='REVISAR_PAGINA_INDIVIDUAL' and not c['publicar']
    assert F.receipt_choices(c)[0][0]['url']==row['url']
    with pytest.raises(ValueError):F.receipt_choices(dict(c,url='https://evil.test/a.jpg'))
def test_inaturalist_photo_licence_not_observation():
    p=dict(id=12,url='https://inaturalist-open-data.s3.amazonaws.com/photos/12/square.jpg',license_code='cc-by',attribution='Author')
    o=dict(id=99,quality_grade='research',license_code='cc0',taxon={'name':'Bird'},photos=[dict(p,license_code='cc-by-nc'),p])
    out=F.inaturalist('bird',transport=T({'results':[o]}))
    assert len(out)==1 and out[0]['url'].endswith('/12/original.jpg') and out[0]['pagina'].endswith('/99')
    c=A._candidato_documental(out[0],'inaturalist','foto')
    assert c and F.receipt_choices(c)
    assert c['direitos']=='REVISAR_PAGINA_INDIVIDUAL'
def test_usgs_only_real_item_pages():
    t=T(b'<a href="/media/videos/example">Example</a><a href="/media/videos/example">duplicate</a><a href="https://evil.test/media/videos/other">bad</a><a href="/media/images/test">photo</a>')
    out=F.usgs('lava','video',transport=t)
    assert len(out)==1 and out[0]['credito']=='' and out[0]['licenca']==''
    assert A._candidato_documental(out[0],'usgs_pagina','video')['direitos']=='REVISAR_PAGINA_INDIVIDUAL'
def test_routes_opt_in_progressive():
    assert 'openverse' not in dict(A.fontes_documentais('foto'))
    assert {'openverse','inaturalist','usgs_pagina'}<=set(dict(A.fontes_documentais('foto',expandir=True)))
    assert 'usgs_pagina' in dict(A.fontes_documentais('video',expandir=True))
