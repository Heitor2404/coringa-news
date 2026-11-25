import json
import pytest
from src.v4 import acervo_v4 as A
from src.v4.formatos import revisao_documental as R, amostragem_documental as AD
from scripts.qa_pesquisa_documental_e246 import nasa_receipt,archive_receipt
from PIL import Image

def need():
    return {'id':'n','necessidade':'registro','evidencia_visual':'movimento',
            'mostrar':'observed physical change','fatos':['f'],
            'pesquisa':{'consultas_en':['subject change','subject transformation','subject motion']}}
def candidate(i):
    return {'fonte':'test','source_id':i,'tipo':'video','url':'https://example.org/'+str(i)}
def accepted():
    return {'estado':'PERTINENTE_PRIVADO','necessidade_id':'n','revisao_id':'r',
            'publicar':False,'direitos_aprovados':False}

def test_progressive_reaches_fourth_candidate_without_discarding_queue():
    def oldsearch(n,l):return {'id':'n','buscas':[],'candidatos':[candidate(i) for i in range(1,6)]}
    def inspector(c,n):
        return accepted() if c['source_id']==4 else {'estado':'INSUFICIENTE','motivo':'SEM_PERTINENCIA'}
    # Compare fixed first queue (3 candidates) with progressive queue (same candidates).
    assert R.fila_cobertura(need(),oldsearch(None,None)['candidatos'],inspector,max_candidatos=3)['estado']=='LACUNA_PENDENTE'
    calls=[]
    def search(n,l,seen):
        calls.append(l)
        return {'id':'n','buscas':[{'consulta':'subject change'}],'candidatos':[candidate(i) for i in range(1,6)]}
    r=R.cobertura_progressiva(need(),search,inspector,pode_buscar=lambda:True,pode_inspecionar=lambda:True,max_buscas=4)
    assert r['estado']=='CANDIDATO_PRIVADO_REVISADO' and r['tentativas']==4 and calls==[4]
    assert not r['publicar']

def test_discovery_without_vision_and_resume_no_repeat():
    ready=False; calls=[]
    def search(n,l,seen):
        calls.append(l);return {'id':'n','buscas':[{'consulta':'subject change'}],'candidatos':[candidate(1)]}
    st={}
    r=R.cobertura_progressiva(need(),search,lambda c,n:accepted(),pode_buscar=lambda:True,pode_inspecionar=lambda:ready,max_buscas=4,estado=st)
    assert r['pendentes']==1 and r['diagnostico']['parada']=='REVISAO_PENDENTE_ORCAMENTO'
    ready=True
    r=R.cobertura_progressiva(need(),search,lambda c,n:accepted(),pode_buscar=lambda:True,pode_inspecionar=lambda:ready,max_buscas=4,estado=st)
    assert r['estado']=='CANDIDATO_PRIVADO_REVISADO' and len(calls)==1

def test_progressive_queries_preserved_and_no_fixed_two_results():
    calls=[]
    def source(q):
        calls.append(q)
        return [{'url':'https://example.org/'+str(len(calls))+'/'+str(i),'source_id':i,'titulo':q} for i in range(5)]
    seen=set()
    for _ in range(3):
        r=A.pesquisar_cobertura(need(),fontes=lambda t:[('test',source)],max_buscas=1,max_candidatos=64,progressivo=True,buscas_vistas=seen)
        assert len(r['candidatos'])==5
    assert calls==['subject change','subject transformation','subject motion']

class Transport:
    def __init__(self,body):self.body=body
    def get(self,url,hosts,lim):return json.dumps(self.body).encode()

def test_nasa_video_not_thumbnail_or_spoof():
    c={'source_id':'NASA-test','tipo':'video'}
    t=Transport({'collection':{'items':[{'href':u} for u in ['http://images-assets.nasa.gov/video/NASA-test/~medium.mp4','https://images-assets.nasa.gov/video/NASA-test/thumb.jpg','https://images-assets.nasa.gov.evil.test/video.mp4']]}})
    assert nasa_receipt(c,t)==[{'url':'https://images-assets.nasa.gov/video/NASA-test/~medium.mp4'}]
    assert c['recibo_nasa']['direitos']=='PENDENTE_AUDITORIA_INDIVIDUAL'

def test_archive_requires_explicit_item_license_and_file_identity():
    c={'source_id':'example','tipo':'video'}
    doc={'metadata':{'identifier':'example','creator':'Example author','licenseurl':'https://creativecommons.org/licenses/by/4.0/'},
         'dir':'/12/items/example','d1':'ia123.us.archive.org','d2':'ia123.us.archive.org.evil.test',
         'files':[{'name':'a.mp4','size':'100','md5':'a'*32},{'name':'../bad.mp4','size':'100','md5':'a'*32}]}
    variants,hosts=archive_receipt(c,Transport(doc))
    assert hosts=={'ia123.us.archive.org'} and len(variants)==1
    assert c['recibo_archive']['direitos']=='PENDENTE_AUDITORIA_INDIVIDUAL'
    doc['metadata'].pop('licenseurl')
    doc['metadata']['collection']='prelinger'
    with pytest.raises(ValueError,match='ARCHIVE_LICENCA_PENDENTE'):archive_receipt(c,Transport(doc))

def test_second_batch_never_repeats_reviewed_starts():
    m={'expected_sha256':'a'*64,'duration_s':60,'local_source':'fixture','width':960}
    def frame(p,t,width):
        return Image.new('RGB',(width,width//2),(int(t)%255,90,80))
    e,first=AD.preparar_lote(m,need(),frame)
    reviewed={round(p['inicio_s'],4) for p,_ in first}
    _,second=AD.preparar_lote(m,need(),frame,exploracao=e,excluir=reviewed)
    assert first and second and not reviewed & {round(p['inicio_s'],4) for p,_ in second}


def test_private_analysis_roundtrip_on_existing_v3_package(tmp_path):
    from src.v3.biblioteca import Biblioteca
    from src.v3 import pacote_biblioteca as P
    b=Biblioteca(tmp_path/'source.db',tmp_path/'source')
    p=tmp_path/'photo.jpg';Image.new('RGB',(800,600),'blue').save(p)
    d=b.ingerir(p,{'titulo':'private original'})
    key='documental:'+'f'*64
    obs={'publicar':False,'direitos_aprovados':False,'revisao':{'veredito':'insuficiente'}}
    b.gravar_analise(d['sha256'],key,obs,origem='fixture')
    b.gravar_analise(d['sha256'],'documental:'+'e'*64,{'publicar':True,'direitos_aprovados':True})
    dest=tmp_path/'pack'
    idx=P.exportar(b,[d['id']],dest,incluir_analises_privadas=True);b.fechar()
    assert 'analises_sha256' in idx
    c,r=P.restaurar(dest,db=tmp_path/'target.db',armazem=tmp_path/'target',restaurar_analises_privadas=True)
    try:
        assert r['analises_restauradas']==1
        assert c.analise(d['sha256'],key)==obs
        assert c.obter(d['id'])['uso_comercial']=='indefinido'
    finally:c.fechar()
    (dest/'analises-privadas.json').write_text('{}')
    with pytest.raises(ValueError,match='E258-SHA-ANALISES'):
        P.restaurar(dest,db=tmp_path/'bad.db',armazem=tmp_path/'bad',restaurar_analises_privadas=True)


def test_nasa_documentary_identity_does_not_require_thumbnail(monkeypatch):
    from src import midia
    class Resp:
        def raise_for_status(self):pass
        def json(self):return {'collection':{'items':[{'data':[{'nasa_id':'VIDEO123','title':'Real record','center':'GSFC'}],'links':[]}]}}
    monkeypatch.setattr(midia.requests,'get',lambda *args,**kw:Resp())
    rows=midia.candidatos_nasa_video('test',documental=True)
    assert len(rows)==1 and rows[0]['source_id']=='VIDEO123'
    assert rows[0]['url']=='https://images.nasa.gov/details/VIDEO123'
    assert rows[0]['licenca']=='' and rows[0]['variantes']==[]

def test_archive_documentary_search_keeps_all_terms(monkeypatch):
    from src import midia
    class Resp:
        def raise_for_status(self):pass
        def json(self):return {'response':{'docs':[]}}
    def get(url,**kw):
        q=kw['params']['q']
        assert '"Apollo" AND "11"' in q and 'licenseurl:' in q
        assert 'collection:prelinger' not in q
        return Resp()
    monkeypatch.setattr(midia.requests,'get',get)
    assert midia.candidatos_archive('Apollo 11',documental=True)==[]
