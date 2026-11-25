from PIL import Image
import pytest
from src.v3.biblioteca import Biblioteca
from src.v4.formatos import reuso_documental as R
from src.v4.formatos import revisao_documental as V

def need(ev='estatica'):
    return {'id':'n','necessidade':'registro','evidencia_visual':ev,'pesquisa':{'consultas_en':['glacier']},'mostrar':'glacier'}

def test_reuse_real_local_bytes_and_no_motion_in_photo(tmp_path):
    b=Biblioteca(tmp_path/'db',tmp_path/'files')
    f=tmp_path/'a.jpg';Image.new('RGB',(800,600),'blue').save(f)
    try:
        d=b.ingerir(f,{'titulo':'glacier','url':'https://example.org/a.jpg'})
        c=R.candidatos(b,need())[0]
        assert R.candidatos(b,need('movimento'))==[]
        m,im,p=R.amostra(b,c)
        assert m['sha256']==d['sha256'] and m['reuso_biblioteca'] and not m['direitos_aprovados']
        assert im.size==(800,600)
        verdict=V.decidir(need(),{**c,'aquisicao':m},{},tipo='foto')
        assert verdict['estado']=='INSUFICIENTE'
        p.write_bytes(b'bad')
        assert R.candidatos(b,need())==[]
        with pytest.raises(ValueError,match='E251-BYTES'):R.amostra(b,c)
    finally:b.fechar()

def test_library_candidate_is_not_automatic_coverage():
    c={'fonte':'biblioteca_v3','source_id':'cm-x','tipo':'foto'}
    result=V.fila_cobertura(need(),[c],lambda c,n:{'estado':'INSUFICIENTE','motivo':'SEM_PERTINENCIA'})
    assert result['estado']=='LACUNA_PENDENTE'


def test_explanatory_need_reuses_real_media_before_animation(tmp_path):
    b=Biblioteca(tmp_path/'db',tmp_path/'files')
    f=tmp_path/'a.jpg';Image.new('RGB',(800,600),'blue').save(f)
    try:
        d=b.ingerir(f,{'titulo':'glacier','url':'https://example.org/a.jpg'})
        n={**need(),'necessidade':'lacuna_explicativa','lacuna':'detalhe não mostrado'}
        c=R.candidatos(b,n)
        assert c and c[0]['sha_catalogo']==d['sha256'] and c[0]['publicar'] is False
        assert R.candidatos(b,{**n,'evidencia_visual':'movimento'})==[]
        assert R.candidatos(b,{**n,'necessidade':'territorio'})==[]
    finally:b.fechar()


def test_metadata_without_bytes_does_not_consume_local_quota(tmp_path):
    b=Biblioteca(tmp_path/'db',tmp_path/'files')
    try:
        for i in range(6):
            f=tmp_path/f'{i}.jpg';Image.new('RGB',(900-i*20,600),(i*30,0,0)).save(f)
            d=b.ingerir(f,{'titulo':'glacier','url':f'https://example.org/{i}.jpg'})
            if i<5:b.caminho(d['sha256'],'.jpg').unlink()
        assert [c['sha_catalogo'] for c in R.candidatos(b,need(),limite=1)]==[d['sha256']]
    finally:b.fechar()


def test_historical_lead_is_local_pending_and_scope_bound(tmp_path):
    b=Biblioteca(tmp_path/'db',tmp_path/'files')
    try:
        f=tmp_path/'a.jpg';Image.new('RGB',(800,600),'blue').save(f)
        d=b.ingerir(f,{'titulo':'IMG001','pagina':'https://example.org/a'})
        n=need()
        n['candidatos_historicos']=[{'escopo':R.escopo(n),'sha256':d['sha256'],'pagina':'https://example.org/a','tipo':'foto','relatorio':'old','necessidade_anterior':'other','estado':'PISTA_HISTORICA_PENDENTE','publicar':False,'direitos_aprovados':False}]
        c=R.candidatos(b,n)[0]
        assert c['sha_catalogo']==d['sha256'] and c['pista_historica']['estado']=='PISTA_HISTORICA_PENDENTE'
        assert V.decidir(n,c,{},tipo='foto')['estado']=='INSUFICIENTE'
        assert R.candidatos(b,{**n,'mostrar':'different'})==[]
        assert R.candidatos(b,{**n,'evidencia_visual':'movimento'})==[]
        b.caminho(d['sha256'],'.jpg').unlink()
        assert R.candidatos(b,n)==[]
    finally:b.fechar()

def test_memory_positive_is_hint_and_bound_to_source(tmp_path):
    import hashlib
    b=Biblioteca(tmp_path/'db',tmp_path/'files')
    try:
        f=tmp_path/'a.jpg';Image.new('RGB',(800,600),'blue').save(f)
        d=b.ingerir(f,{'titulo':'IMG001'})
        n=need()
        q={'publicar':False,'sha256_origem':d['sha256'],'necessidade_id':'n','mostrar':'glacier','pixels_sha256':'b'*64,'revisao_id':'r'}
        dec={'estado':'PERTINENTE_PRIVADO','publicar':False,'direitos_aprovados':False,'revisao_id':'r'}
        rec={'publicar':False,'direitos_aprovados':False,'revisao':q,'decisao':dec,'escopo_pesquisa':{**R.escopo(n),'consultas_en':['glacier']}}
        b.gravar_analise(d['sha256'],'documental:'+'a'*64,rec)
        c=R.candidatos(b,n)[0]
        assert c['pista_memoria_semantica'] and V.decidir(n,c,{},tipo='foto')['estado']=='INSUFICIENTE'
        assert R.candidatos(b,need('movimento'))==[]
        assert R.prioridade_memoria(n,{'tipo':'foto','sha256':'c'*64,'analises':{'r':rec}})==0
        rec['decisao']['estado']='INSUFICIENTE'
        assert R.prioridade_memoria(n,{'tipo':'foto','sha256':d['sha256'],'analises':{'r':rec}})==0
    finally:b.fechar()

def test_negative_sample_is_not_a_global_blacklist():
    import hashlib
    im=Image.new('RGB',(800,600),'blue')
    n=need()
    h={'escopo':R.escopo(n),'sha256':'a'*64,'pagina':'https://example.org/a','tipo':'foto','relatorio':'old','necessidade_anterior':'other','estado':'PISTA_HISTORICA_PENDENTE','publicar':False,'direitos_aprovados':False,
       'observacao_visual':{'estado':'INCOMPATIVEL_NA_AMOSTRA','publicar':False,'relatorio_amostra':'board','motivo':'different subject','px':list(im.size),'pixels_sha256':hashlib.sha256(im.tobytes()).hexdigest()}}
    n['candidatos_historicos']=[h]
    c={'tipo':'foto','sha_catalogo':'a'*64,'pagina':h['pagina'],'pista_historica':h}
    assert R.negativa_observada(n,c,im)
    assert R.negativa_observada(n,c,Image.new('RGB',im.size,'red')) is None
    assert R.negativa_observada({**n,'mostrar':'different'},c,im) is None

def test_replay_thumbnail_rounding_uses_original_square_bounds():
    import hashlib
    im=Image.new('RGB',(3001,2000))
    # Nonconstant pixels ensure size matching alone cannot pass.
    im.paste((255,0,0),(0,0,1500,1000))
    expected=im.copy();expected.thumbnail((1280,1280))
    old={'px':list(expected.size),'pixels_sha256':hashlib.sha256(expected.tobytes()).hexdigest()}
    restored=R.reproduzir_amostra_foto(im,old)
    assert restored is not None and restored.size==expected.size and restored.tobytes()==expected.tobytes()
    assert R.reproduzir_amostra_foto(im,{**old,'pixels_sha256':'0'*64}) is None
    assert R.reproduzir_amostra_foto(im,{**old,'px':[1281,853]}) is None

def test_video_memory_requires_observed_motion_for_motion_hint():
    n={'id':'new','sujeito':'planet','mostrar':'planet rotation','necessidade':'registro','evidencia_visual':'movimento'}
    sha='a'*64
    d={'estado':'PERTINENTE_PRIVADO','publicar':False,'direitos_aprovados':False,'revisao_id':'r','prova_de_acao_continua':True}
    obs={'sha256_origem':sha,'necessidade_id':'old','publicar':False}
    rec={'publicar':False,'direitos_aprovados':False,'escopo_pesquisa':{**n,'id':'old'},'janelas':[{'pacote':{'revisao_id':'r','revisao_assistida':obs},'decisao':d}]}
    row={'tipo':'video','sha256':sha,'analises':{'x':rec}}
    assert R.prioridade_memoria(n,row)==1.8
    d['prova_de_acao_continua']=False
    assert R.prioridade_memoria(n,row)==0
    d['prova_de_acao_continua']=True
    assert R.prioridade_memoria({**n,'mostrar':'different action'},row)==0
