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
        assert 'title:"Apollo"' in q and 'title:"11"' in q and 'licenseurl:' in q
        assert 'subject:"Apollo"' in q and 'description:"11"' in q
        assert 'collection:prelinger' not in q
        return Resp()
    monkeypatch.setattr(midia.requests,'get',get)
    assert midia.candidatos_archive('Apollo 11',documental=True)==[]


def test_archive_ranks_title_before_incidental_description(monkeypatch):
    from src import midia
    class Resp:
        def raise_for_status(self):pass
        def json(self):
            return {'response':{'docs':[
                {'identifier':'incidental','title':'Unrelated podcast','description':'Apollo 11'},
                {'identifier':'specific','title':'Apollo 11 mission','description':'Mission footage'}]}}
    monkeypatch.setattr(midia.requests,'get',lambda *a,**k:Resp())
    rows=midia.candidatos_archive('Apollo 11',documental=True)
    assert rows[0]['source_id']=='specific'
    assert rows[0]['descricao']=='Mission footage' and rows[0]['licenca']==''

def test_archive_receipt_documented_workable_servers_and_error():
    c={'source_id':'example','tipo':'video'}
    d={'metadata':{'identifier':'example','licenseurl':'https://creativecommons.org/publicdomain/zero/1.0/'},
       'dir':'/12/items/example','workable_servers':['ia123.us.archive.org','evil.test'],
       'files':[{'name':'video.mp4','size':'100','md5':'a'*32}]}
    variants,hosts=archive_receipt(c,Transport(d))
    assert hosts=={'ia123.us.archive.org'} and len(variants)==1
    assert c['recibo_archive']['direitos']=='PENDENTE_AUDITORIA_INDIVIDUAL'
    with pytest.raises(ValueError,match='ARCHIVE_METADATA_ERRO_102'):
        archive_receipt(c,Transport({'error':'unavailable','errcode':102}))
    d['dir']='/12/items/other'
    with pytest.raises(ValueError,match='ARCHIVE_DIRETORIO_PENDENTE'):
        archive_receipt(c,Transport(d))


def test_documentary_providers_do_not_hide_candidates_after_three(monkeypatch):
    from src import midia
    class Resp:
        def raise_for_status(self):pass
        def json(self):
            return {'collection':{'items':[{'data':[{'nasa_id':f'VIDEO{i}','title':'Record'}]} for i in range(8)]},
                    'response':{'docs':[{'identifier':f'video{i}','title':'Record'} for i in range(8)]}}
    monkeypatch.setattr(midia.requests,'get',lambda *a,**k:Resp())
    assert len(midia.candidatos_nasa_video('record',documental=True))==8
    assert len(midia.candidatos_archive('record',documental=True))==8

def test_progressive_nasa_prefers_small_declared_video_derivative():
    base='https://images-assets.nasa.gov/video/VIDEO123/'
    c={'source_id':'VIDEO123','tipo':'video'}
    urls=[base+'VIDEO123~'+x+'.mp4' for x in ('orig','large','mobile','small','medium')]
    result=nasa_receipt(c,Transport({'collection':{'items':[{'href':u} for u in urls]}}),progressivo=True)
    assert [x['url'] for x in result][:2]==[urls[3],urls[4]]
    assert set(x['url'] for x in result)==set(urls)
    assert c['recibo_nasa']['direitos']=='PENDENTE_AUDITORIA_INDIVIDUAL'


def test_metadata_rank_prioritizes_specific_query_without_rejecting_unlabelled():
    n={**need(),'pesquisa':{'consultas_en':['Apollo 11 moonwalk','lunar surface walking']}}
    candidates=[
        {**candidate(1),'titulo':'Unrelated interview','descricao':'Apollo 11 was mentioned. Photographed on Earth.'},
        {**candidate(2),'titulo':'Apollo 11 Restored Moonwalk','descricao':''},
        {**candidate(3),'titulo':'KSC-05-S-00286','descricao':''},
    ]
    assert [c['source_id'] for c in R.ordenar_candidatos(n,candidates)]==[2,1,3]
    assert R.relevancia_textual(n,candidates[1])=={'cobertura':1.,'titulo':1.,'proximidade':.75,'prova_visual':False}
    # No hard metadata veto: later candidate without title can still be reviewed.
    order=[]
    def inspect(c,n):
        order.append(c['source_id'])
        return accepted() if c['source_id']==3 else {'estado':'INSUFICIENTE','motivo':'SEM_PERTINENCIA'}
    assert R.fila_cobertura(n,candidates,inspect)['estado']=='CANDIDATO_PRIVADO_REVISADO'
    assert order==[2,1,3]


def test_metadata_rank_retains_local_priority_and_alternative_query():
    n={**need(),'pesquisa':{'consultas_en':['Earth rotating','planet rotation']}}
    rows=[{**candidate(1),'titulo':'How Sunlight Pushes Asteroids','descricao':'Near-Earth asteroids'},
          {**candidate(2),'titulo':'Planet rotation','descricao':''},
          {**candidate(3),'fonte':'biblioteca_v3','titulo':'Unknown local record'}]
    assert [c['source_id'] for c in R.ordenar_candidatos(n,rows)]==[3,2,1]
    assert R.relevancia_textual(n,rows[0])['cobertura']<1


def test_nasa_real_metadata_mixed_subjects_do_not_rank_equal():
    # Short excerpts from the actual E261.7 provider report; no claim of
    # visual relevance from metadata. Both contain both query terms.
    n={**need(),'pesquisa':{'consultas_en':['Earth rotating']}}
    rows=[{**candidate(1),'titulo':'How Sunlight Pushes Asteroids',
           'descricao':'Near-Earth asteroids pose a danger. When sunlight strikes a rotating asteroid, the dayside heats up.'},
          {**candidate(2),'titulo':'Orion Camera Views of Artemis II Apogee Raise Burn',
           'descricao':'A view from cameras on the exterior of the Orion spacecraft. The Earth is seen rotating below.'},
          {**candidate(3),'titulo':'KSC-05-S-00286','descricao':'The Earth is rotating at 24 hours.'}]
    assert all(R.relevancia_textual(n,c)['cobertura']==1 for c in rows)
    assert R.relevancia_textual(n,rows[1])['proximidade']>R.relevancia_textual(n,rows[0])['proximidade']
    assert R.ordenar_candidatos(n,rows)[0]['source_id']==2

def test_cache_first_queue_reopens_only_deferred_candidates():
    local={**candidate(1),'fonte':'biblioteca_v3'}
    other={**candidate(2),'fonte':'biblioteca_v3'}
    st={'vistos':{('biblioteca_v3',1),('biblioteca_v3',2)},'pendentes':[],'rever':[local],'descoberta_sem_visao':True}
    R.reabrir_pendentes(st)
    assert st['pendentes']==[local] and st['vistos']=={('biblioteca_v3',2)}
    assert not st['descoberta_sem_visao'] and 'rever' not in st
    R.reabrir_pendentes(st)
    assert st['pendentes']==[local]

def test_missing_cache_is_not_a_semantic_negative():
    r=R.diagnostico_cobertura([{'cobertura':{'trilha':[{'decisao':{'estado':'ORCAMENTO','motivo':'ANALISE_COMPATIVEL_NAO_DISPONIVEL'}}]}}],'ORCAMENTO')
    assert r['decisoes_por_tipo']=={'REVISAO_SEM_CACHE_COMPATIVEL':1}
    assert r['inexistencia_de_midia_comprovada'] is False

def test_progressive_alternative_query_reaches_primary_early():
    calls=[]
    def providers(t):
        return [(k,lambda q,k=k:calls.append((k,q)) or []) for k in ('primary','secondary','third')]
    A.pesquisar_cobertura(need(),fontes=providers,max_buscas=2,progressivo=True)
    assert calls==[('primary','subject change'),('primary','subject transformation')]

def test_repeated_series_titles_do_not_crowd_out_other_candidates():
    n={**need(),'pesquisa':{'consultas_en':['planet rotation']}}
    rows=[{**candidate(i),'titulo':'planet rotation'} for i in range(1,4)]
    other={**candidate(9),'titulo':'planet surface'}
    ordered=R.ordenar_candidatos(n,rows+[other])
    assert [c['source_id'] for c in ordered]==[1,9,2,3]

def test_explicit_metadata_mismatch_is_soft_and_scope_sensitive():
    from src.v4.formatos import revisao_documental as R
    n={'necessidade':'registro','mostrar':'sharp mountain peak','evidencia_visual':'estatica','pesquisa':{'consultas_en':['mountain peak']}}
    bad={'fonte':'commons','tipo':'foto','source_id':1,'titulo':'Topographic map of mountain peak'}
    good={'fonte':'commons','tipo':'foto','source_id':2,'titulo':'Mountain landscape'}
    assert R.ordenar_candidatos(n,[bad,good])==[good,bad]
    assert not R.incompatibilidade_metadados({**n,'mostrar':'historical map of mountain peak'},bad)
    assert not R.incompatibilidade_metadados({**n,'necessidade':'territorio'},bad)
    assert not R.incompatibilidade_metadados(n,{**bad,'fonte':'biblioteca_v3'})
    assert R.incompatibilidade_metadados(n,{**bad,'titulo':'Mountain panorama distorted'})

def test_search_facets_require_distinct_visual_components_in_metadata_ranking():
    from src.v4.formatos import revisao_documental as R
    n={'necessidade':'registro','mostrar':'valley and lake','evidencia_visual':'estatica','pesquisa':{'consultas_en':['glacial valley lake'],'componentes_busca':[['lake','tarn'],['valley','mountains']]}}
    good={'fonte':'commons','tipo':'foto','source_id':1,'titulo':'Mountain landscape','descricao':'Lake in a valley'}
    bad={'fonte':'commons','tipo':'foto','source_id':2,'titulo':'Glacial valley','descricao':'Landscape'}
    assert R.ordenar_candidatos(n,[bad,good])==[good,bad]
    assert R.cobertura_componentes(n,{'titulo':'Lakeside valley'})[0]==1
    assert R.cobertura_componentes(n,good)[0]==2
    assert not R.relevancia_textual(n,good)['prova_visual']
