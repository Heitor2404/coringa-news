import json,hashlib
from src.v4 import fontes_cientificas as F
from src.v4 import acervo_v4 as A

class Response:
    status_code=200
    def __init__(self,obj):self.obj=obj
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,n):yield json.dumps(self.obj).encode()

class Session:
    def __init__(self,rows):self.rows=iter(rows)
    def request(self,method,url,**kw):
        assert kw['allow_redirects'] is False
        return Response(next(self.rows))

def article(license='https://creativecommons.org/licenses/by/4.0/'):
    return {'id':7,'doi':'10.1234/example','title':'Observed movement','authors':[{'full_name':'Test Author'}],
       'url_public_html':'https://figshare.com/articles/media/example/7','license':{'url':license},
       'files':[{'id':8,'name':'movie.mp4','size':100,'download_url':'https://ndownloader.figshare.com/files/8','computed_md5':'a'*32},
                {'id':9,'name':'thumb.jpg','size':100,'download_url':'https://ndownloader.figshare.com/files/9','computed_md5':'b'*32}]}

def test_explicit_license_file_identity_and_kind():
    v=F.candidatos('movement','video',session=Session([[{'id':7}],article()]))
    assert len(v)==1 and v[0]['source_id']=='7:8'
    c=A._candidato_documental(v[0],'figshare','video')
    assert c['recibo_cientifico']['doi']=='10.1234/example'
    assert c['direitos']=='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' and not c['publicar']

def test_reject_nc_unknown_embargo_and_spoof():
    for lic in ('https://creativecommons.org/licenses/by-nc/4.0/',''):
        assert F.candidatos('movement','video',session=Session([[{'id':7}],article(lic)]))==[]
    d=article();d['is_embargoed']=True
    assert F.candidatos('movement','video',session=Session([[{'id':7}],d]))==[]
    assert not F.safe_url('https://ndownloader.figshare.com.evil.test/files/8',F.HOSTS)
    assert not F.safe_url('http://ndownloader.figshare.com/files/8',F.HOSTS)

def test_md5_integrity_before_decoder(tmp_path):
    from scripts.qa_pesquisa_documental_e246 import sample
    import pytest
    c=A._candidato_documental(F.candidatos('movement','video',session=Session([[{'id':7}],article()]))[0],'figshare','video')
    class T:
        def get(self,*a):return b'x'*100
    with pytest.raises(ValueError,match='FIGSHARE_INTEGRIDADE'):sample(c,tmp_path,T())
