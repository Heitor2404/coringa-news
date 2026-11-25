"""Direct adapter regressions, transport and portable library restoration."""
from datetime import datetime,timezone
import pytest
from src import midia
from src.v4.aquisicao_documental import Transporte,retry_after,AquisiçãoErro
from src.v3.biblioteca import restaurar_catalogo
from src.v4 import acervo_v4 as A
from scripts.qa_pesquisa_documental_e246 import variants

def test_commons_photo_and_video_real_adapter(monkeypatch):
    meta={k:{'value':v} for k,v in {'LicenseShortName':'CC BY 4.0','Artist':'Author','LicenseUrl':'https://creativecommons.org/licenses/by/4.0/'}.items()}
    info={'url':'https://upload.wikimedia.org/master','descriptionurl':'https://commons.wikimedia.org/wiki/File:Test','width':1920,'height':1080,'mime':'image/jpeg','size':123,'extmetadata':meta,'thumburl':'https://upload.wikimedia.org/thumb','duration':7,'derivatives':[{'src':'https://upload.wikimedia.org/derived.webm','width':854,'height':480}]}
    monkeypatch.setattr(midia,'_commons',lambda q,video:[{'title':'File:Test.jpg','pageid':42,('videoinfo' if video else 'imageinfo'):[info]}])
    monkeypatch.setattr(midia,'_relevante',lambda *a:True)
    p=midia.candidatos_foto('test')[0];v=midia.candidatos_arquivo('test',estrito=True)[0]
    assert p['derivado'] and p['pagina']==info['descriptionurl']
    assert v['licenca']=='CC BY 4.0' and v['source_id']==42 and v['derivado']
    assert v['variantes'][0]['url'].endswith('.webm')
    assert A._candidato_documental(v,'commons_video','video')['direitos']=='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA'

class Response:
    def __init__(self,status,headers=None,data=b'ok'):self.status_code=status;self.headers=headers or {};self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,n):yield self.data
class Session:
    def __init__(self,rs):self.rs=iter(rs)
    def get(self,*a,**k):return next(self.rs)

def test_retry_and_limits():
    waits=[]
    t=Transporte(session=Session([Response(429,{'Retry-After':'6'}),Response(200)]),sleep=waits.append)
    assert t.get('https://example.org/a',{'example.org'},10)==b'ok'
    assert len(waits)==1 and waits[0]>=6 and t.http==2
    assert retry_after('Wed, 25 Nov 2026 01:00:10 GMT',datetime(2026,11,25,1,tzinfo=timezone.utc))==10
    t=Transporte(session=Session([Response(429,{'Retry-After':'120'})]),sleep=waits.append,max_wait=30)
    with pytest.raises(AquisiçãoErro,match='FONTE_SUSPENSA'):t.get('https://example.org/a',{'example.org'},10)
    with pytest.raises(AquisiçãoErro,match='FONTE_SUSPENSA'):t.get('https://example.org/b',{'example.org'},10)
    assert t.http==1

def test_size_budget_and_no_403_retry():
    t=Transporte(session=Session([Response(403)]),sleep=lambda x:pytest.fail('retry'))
    with pytest.raises(AquisiçãoErro,match='403'):t.get('https://example.org/a',{'example.org'},10)
    assert t.http==1
    t=Transporte(session=Session([Response(200,{'Content-Length':'100'})]))
    with pytest.raises(AquisiçãoErro,match='CONTENT_LENGTH'):t.get('https://example.org/a',{'example.org'},10)
    assert t.bytes==0
    assert t.events[-1]['content_length']==100 and t.events[-1]['limite_bytes']==10
    assert t.events[-1]['resultado']=='LIMITE_CONTENT_LENGTH'

def test_real_manifest_restoration(tmp_path):
    b,r=restaurar_catalogo(db=tmp_path/'db.sqlite3',armazem=tmp_path/'files')
    try:
        assert r['registros_db']>=258 and r['direitos_revalidados'] is False
        assert not list((tmp_path/'files').glob('*/*'))
    finally:b.fechar()

def test_size_precheck_and_declared_rendering():
    c={'tipo':'foto','url':'https://example.org/big','tamanho_declarado':38_000_000,'variantes':[{'url':'https://example.org/small','size':2000}]}
    assert [x['url'] for x in variants(c)]==['https://example.org/small']
    assert A.natureza_preliminar({'desc':'Rendered using Autodesk Maya'})=='REPRESENTACAO_DECLARADA'
    assert A.natureza_preliminar({'desc':'Cassini mosaic'})=='NATUREZA_PENDENTE_INSPECAO'

def test_legacy_thumbnail_cannot_satisfy_motion():
    class B:
        def buscar(self,*a,**k):return [{'id':'cm-x','sha256':'a'*64,'ext':'.jpg'}]
    n={'id':'n','necessidade':'registro','evidencia_visual':'movimento','pesquisa':{'consultas_en':['octopus movement']}}
    def inspector(c,n):
        pytest.fail('thumbnail must not be offered as video evidence')
    r=A.pesquisar_cobertura(n,biblioteca=B(),fontes=lambda t:[],inspecionar=inspector)
    assert r['biblioteca'][0]['estado']=='MINIATURA_NAO_E_VIDEO'
    assert r['estado']!='CANDIDATO_PRIVADO_REVISADO'

def test_nasa_receipt_legacy_http_upgrade_and_exact_host():
    import json
    from scripts.qa_pesquisa_documental_e246 import nasa_receipt
    class T:
        def get(self,url,hosts,lim):
            assert url=='https://images-api.nasa.gov/asset/PIA123'
            return json.dumps({'collection':{'items':[{'href':u} for u in [
                'http://images-assets.nasa.gov/image/PIA123/~medium.jpg',
                'https://images-assets.nasa.gov/image/PIA123/~medium.jpg',
                'https://images-assets.nasa.gov.evil.test/a.jpg',
                'http://user@images-assets.nasa.gov/a.jpg',
                'https://images-assets.nasa.gov:80/a.jpg',
                'https://images-assets.nasa.gov/a.json'
            ]]}}).encode()
    c={'source_id':'PIA123'}
    assert nasa_receipt(c,T())==[{'url':'https://images-assets.nasa.gov/image/PIA123/~medium.jpg'}]
    assert c['recibo_nasa']['variantes_declaradas'][0]['href_declarado'].startswith('http:')
    assert c['recibo_nasa']['direitos']=='PENDENTE_AUDITORIA_INDIVIDUAL'
