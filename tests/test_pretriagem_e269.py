from scripts.qa_pretriagem_e269 import candidatos
def test_preview_declared_only_no_repeat_no_approval():
    n={'necessidade':'registro','mostrar':'mountain','evidencia_visual':'estatica','pesquisa':{'consultas_en':['mountain']}}
    c={'fonte':'commons','tipo':'foto','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA','pagina':'p','titulo':'mountain','url':'original','variantes':[{'url':'thumb','width':640,'height':480}]}
    assert candidatos(n,[c])[0][1]['url']=='thumb'
    assert candidatos(n,[c],['p'])==[]
    assert candidatos(n,[{**c,'variantes':[]}])==[]
    assert candidatos(n,[{**c,'titulo':'Topographic map of mountain'}])==[]
    assert candidatos(n,[{**c,'variantes':[{'url':'original','width':640,'height':480}]}])==[]

def test_identity_context_does_not_double_count_a_single_component():
    from src.v4.formatos import revisao_documental as R
    n={'necessidade':'registro','mostrar':'mountain','evidencia_visual':'estatica','pesquisa':{'componentes_busca':[['Matterhorn'],['Matterhorn','summit']],'contexto_busca':['Switzerland'],'contextos_alternativos':['Nevada']}}
    assert R.cobertura_componentes(n,{'titulo':'Matterhorn'})[0]==1
    a={'fonte':'commons','tipo':'foto','source_id':1,'titulo':'Matterhorn summit Nevada'}
    b={'fonte':'commons','tipo':'foto','source_id':2,'titulo':'Matterhorn mountain Switzerland'}
    assert R.ordenar_candidatos(n,[a,b])[0]==b
    assert R.contexto_de_busca(n,{'titulo':'Nevadan'})[0] is False

def test_round_robin_preview_budget_does_not_starve_later_obligations():
    import io
    from PIL import Image
    from src.v4.pretriagem_documental import coletar_fila
    buf=io.BytesIO();Image.new('RGB',(640,480),'blue').save(buf,format='JPEG')
    class Transport:
        http=0;bytes=0;max_http=3;max_bytes=9000000
        def get(self,url,hosts,lim):
            self.http+=1
            if url=='fail':raise ValueError('LIMITE_CONTENT_LENGTH')
            raw=buf.getvalue();self.bytes+=len(raw);return raw
    queues=[({'id':n},[({'pagina':n+str(i)},{'url':v}) for i,v in enumerate(vs)]) for n,vs in [('a',['fail','a2','a3']),('b',['b1']),('c',['c1'])]]
    report=coletar_fila(queues,Transport(),lambda n,c,v,im,h,i:{'id':n['id'],'sha':h})
    assert [len(r['amostras']) for r in report]==[0,1,1]
    assert report[0]['erros'][0]['motivo']=='LIMITE_CONTENT_LENGTH'

def test_photo_preview_never_routes_a_motion_or_atlas_obligation():
    assert candidatos({'necessidade':'registro','evidencia_visual':'movimento'},[{}])==[]
    assert candidatos({'necessidade':'territorio','evidencia_visual':'estatica'},[{}])==[]


def test_documentary_preview_width_is_requested_from_provider(monkeypatch):
    from src import acervo
    calls=[]
    monkeypatch.setattr(acervo,'_busca_commons',lambda q,n:['File:mountain.jpg'])
    monkeypatch.setattr(acervo,'_categoria_commons',lambda q,n:[])
    def get(url,**kwargs):
        calls.append(kwargs)
        return {'query':{'pages':[]}}
    monkeypatch.setattr(acervo,'_get',get)
    acervo.f_commons_documental('mountain',preview_width=640)
    acervo.f_commons_documental('mountain')
    assert [c['iiurlwidth'] for c in calls]==[640,1400]


def test_optional_facets_are_not_a_visual_negative():
    from src.v4.formatos import revisao_documental as R
    n={'necessidade':'registro','mostrar':'rings','evidencia_visual':'estatica','pesquisa':{'consultas_en':['Saturn rings']}}
    c={'titulo':'Saturn rings','fonte':'commons','tipo':'foto'}
    assert R.cobertura_componentes(n,c)==(0,0,0)
    assert R.relevancia_textual(n,c)['cobertura']>0


def test_existing_progressive_queue_preview_only_unresolved_static_needs():
    from src.v4.pretriagem_documental import pendencias_do_fluxo
    n={'id':'a','necessidade':'registro','mostrar':'mountain','evidencia_visual':'estatica','pesquisa':{'consultas_en':['mountain']}}
    c={'fonte':'commons','tipo':'foto','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA','pagina':'p','titulo':'mountain','url':'original','variantes':[{'url':'thumb','width':640,'height':480}]}
    needs=[n,{**n,'id':'b'},{**n,'id':'c','evidencia_visual':'movimento'},{**n,'id':'d','necessidade':'territorio'}]
    rows=[{'necessidade_id':x['id'],'estado':'LACUNA_PENDENTE' if x['id']!='b' else 'CANDIDATO_PRIVADO_REVISADO'} for x in needs]
    states={x['id']:{'pendentes':[c]} for x in needs}
    assert [(x['id'],v[0][0]['pagina']) for x,v in pendencias_do_fluxo(needs,rows,states)]==[('a','p')]
    assert states['a']['pendentes']==[c]


def test_preview_diversifies_query_origin_without_discarding_candidates():
    n={'necessidade':'registro','mostrar':'mountain','evidencia_visual':'estatica','pesquisa':{'consultas_en':['mountain']}}
    base={'fonte':'commons','tipo':'foto','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA','titulo':'mountain','url':'original','variantes':[{'url':'thumb','width':640,'height':480}]}
    rows=[{**base,'pagina':str(i),'source_id':i+1,'consulta_origem':q} for i,q in enumerate(['mountain one','mountain one','mountain two'])]
    result=candidatos(n,rows)
    assert [x[0]['pagina'] for x in result]==['0','2','1']


def test_progressive_provider_preview_width_is_opt_in(monkeypatch):
    from src import acervo
    from src.v4 import acervo_v4 as A
    seen=[]
    monkeypatch.setattr(acervo,'f_commons_documental',lambda q,preview_width=1400:seen.append(preview_width) or [])
    dict(A.fontes_documentais('foto',pretriagem=True))['commons']('subject')
    dict(A.fontes_documentais('foto'))['commons']('subject')
    assert seen==[640,1400]
    assert [k for k,_ in A.fontes_documentais('video',pretriagem=True)]==[k for k,_ in A.fontes_documentais('video')]


def test_preview_prefers_smaller_declared_variant_without_changing_original():
    n={'id':'a','necessidade':'registro','mostrar':'mountain','evidencia_visual':'estatica','pesquisa':{'consultas_en':['mountain']}}
    c={'fonte':'commons','tipo':'foto','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA','titulo':'mountain','pagina':'p','url':'original','variantes':[{'url':'large','width':1920,'height':1080},{'url':'small','width':640,'height':480}]}
    assert candidatos(n,[c])[0][1]['url']=='small'
    assert c['url']=='original' and len(c['variantes'])==2


def test_diversity_never_promotes_homonym_above_contextually_matching_previews():
    n={'necessidade':'registro','mostrar':'rings','evidencia_visual':'estatica','pesquisa':{'consultas_en':['Saturn rings Cassini','Saturn rings spacecraft'],'consultas':['Saturno']}}
    base={'fonte':'commons','tipo':'foto','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA','url':'original','variantes':[{'url':'thumb','width':640,'height':480}]}
    rows=[{**base,'pagina':'a','source_id':1,'titulo':'Top view of the rings of Saturn by Cassini','consulta_origem':'Saturn rings Cassini'},
          {**base,'pagina':'b','source_id':2,'titulo':'Saturn rings by Cassini','consulta_origem':'Saturn rings Cassini'},
          {**base,'pagina':'c','source_id':3,'titulo':'Saturno Meletti, 1946','descricao':'Black and white portrait photograph of baritone Saturno Meletti','consulta_origem':'Saturno'}]
    assert [x[0]['pagina'] for x in candidatos(n,rows)]==['a','b','c']
    assert len(candidatos(n,rows))==3


def test_motor_preview_batch_scopes_and_validates_observations_without_approval(tmp_path):
    import pytest
    from PIL import Image
    from src.v4.pretriagem_documental import revisar_folhas_lote
    n={'id':'x','sujeito':'referente','mostrar':'estrutura','fatos':['f'],'necessidade':'registro','evidencia_visual':'estatica'}
    rows=[]
    for i in range(2):
        name=f'{i}.jpg';Image.new('RGB',(300,300),'blue').save(tmp_path/name)
        rows.append({'necessidade_id':'x','mostrar':'estrutura','pagina':f'p{i}','source_id':i,'preview_sha256':'a'*64,'folha':name,'estado':'PRETRIAGEM_PENDENTE','publicar':False})
    calls=[]
    def ask(prompt,images):
        calls.append(len(images))
        return {'observacoes':[{'indice':1,'decisao':'PRIORIZAR_AQUISICAO','observacao':'Estrutura visivel.'},{'indice':0,'decisao':'NAO_PRIORIZAR','observacao':'Sem estrutura.'}]}
    out=revisar_folhas_lote(n,rows,tmp_path,ask)
    assert calls==[2] and out[1]['source_id']==1 and out[1]['origem']=='VISAO_MOTOR' and not out[1]['publicar']
    assert all(o['escopo']==n for o in out)
    assert not revisar_folhas_lote(n,[],tmp_path,ask) and calls==[2]
    with pytest.raises(ValueError,match='E278.1-PRIORIDADE'):
        revisar_folhas_lote(n,rows,tmp_path,lambda p,i:{'observacoes':[{'indice':k,'decisao':'PRIORIZAR_AQUISICAO','observacao':'x'} for k in (0,1)]})
    with pytest.raises(ValueError,match='E278.1-RESPOSTA'):
        revisar_folhas_lote(n,rows,tmp_path,lambda p,i:{'observacoes':[{'indice':0,'decisao':'NAO_PRIORIZAR','observacao':'x'}]*2})


def test_chain_reservation_does_not_take_motion_budget_or_expand_total():
    from src.v4.pretriagem_documental import reservar_encadeamento
    a={'id':'a','necessidade':'registro','evidencia_visual':'estatica'}
    b={**a,'id':'b','evidencia_visual':'movimento'}
    c={**a,'id':'c','necessidade':'territorio'}
    assert reservar_encadeamento([a,b,c],2)==set()
    assert reservar_encadeamento([a,b,c],3)=={'a'}
    assert reservar_encadeamento([a,b,c],0)==set()


def test_observed_priority_uses_formal_review_and_preserves_rounds():
    import pytest
    from src.v4.pretriagem_documental import candidato_priorizado,revisar_prioridade
    n={'id':'n','sujeito':'x','mostrar':'structure','fatos':['f'],'necessidade':'registro','evidencia_visual':'estatica','pesquisa':{'consultas_en':['structure']}}
    from src.v4.formatos import reuso_documental as RE
    c={'fonte':'commons','tipo':'foto','pagina':'p','source_id':1,'url':'original','variantes':[{'url':'thumb'}],'titulo':'structure'}
    a={'pagina':'p','source_id':1,'preview_sha256':'a'*64,'preview_url':'thumb'}
    o={'escopo':RE.escopo(n),'decisao':'PRIORIZAR_AQUISICAO','source_id':1,'publicar':False}
    choice={'id':'n','pagina':'p','preview_sha256':'a'*64,'observacao_previa':o}
    selected=candidato_priorizado(n,choice,[a],[c])
    assert selected is c and selected['url']=='original'
    with pytest.raises(ValueError):candidato_priorizado(n,choice,[a],[{**c,'source_id':2}])
    row={'necessidade_id':'n','estado':'LACUNA_PENDENTE','rodadas':[],'tentativas':0}
    assert revisar_prioridade(n,row,c,lambda *_:pytest.fail('no budget'),lambda:False)==row
    result=revisar_prioridade(n,row,c,lambda *_:{'estado':'INSUFICIENTE','motivo':'SEM_PERTINENCIA'},lambda:True)
    assert result['estado']=='LACUNA_PENDENTE' and result['tentativas']==1
    result=revisar_prioridade(n,row,c,lambda *_:{'estado':'PERTINENTE_PRIVADO','necessidade_id':'n','revisao_id':'formal','publicar':False,'direitos_aprovados':False},lambda:True)
    assert result['estado']=='CANDIDATO_PRIVADO_REVISADO' and result['rodadas'][-1]['pesquisa']['candidatos'][0]['decisao']['revisao_id']=='formal'


def test_e279_full_progressive_path_selects_preview_then_reviews_distinct_bytes(tmp_path,monkeypatch):
    import io,json,sys
    from PIL import Image
    from src.v4 import acervo_v4 as A
    from src import acervo,gemini
    from scripts import qa_revisao_documental_e247 as E247
    case={'id':'fixture','tema':'controlled documentary','fatos':[{'id':'f','tipo':'pedido_visual_de_teste'}],
        'necessidades':[{'id':'n','fatos':['f'],'sujeito':'mountain','mostrar':'mountain structure','necessidade':'registro','evidencia_visual':'estatica','consultas_en':['mountain structure','mountain landscape']}]}
    spec=tmp_path/'spec.json';spec.write_text(json.dumps({'publish':False,'cases':[case]}))
    out=tmp_path/'review'
    page='https://commons.wikimedia.org/wiki/File:Fixture.jpg'
    original='https://upload.wikimedia.org/fixture-master.jpg';thumb='https://thumb.wikimedia.org/fixture-preview.jpg'
    raw={'titulo':'mountain structure','desc':'mountain landscape','url_original':original,'url':thumb,'pagina':page,'source_id':11,'licenca':'CC BY 4.0','credito':'Fixture author (CC BY 4.0)','w':1200,'h':900,'variantes':[{'url':thumb,'width':640,'height':480}]}
    widths=[]
    def sources(kind,*,pretriagem=False):
        widths.append((kind,pretriagem))
        return [('commons',lambda _: [raw])] if kind=='foto' else []
    monkeypatch.setattr(A,'fontes_documentais',sources)
    monkeypatch.setattr(acervo,'_commons_infos',lambda *args,**kwargs:[{**raw,'variantes':[]}])
    def jpeg(size,color):
        b=io.BytesIO();Image.new('RGB',size,color).save(b,format='JPEG');return b.getvalue()
    downloads=[]
    class Transport:
        def __init__(self,**kw):
            self.http=0;self.bytes=0;self.max_http=kw['max_http'];self.max_bytes=kw['max_bytes']
        def get(self,url,hosts,lim):
            downloads.append(url);self.http+=1
            assert url in (thumb,original)
            b=jpeg((640,480),'blue') if url==thumb else jpeg((1200,900),'green')
            self.bytes+=len(b);return b
        def resumo(self):return {'http':self.http,'bytes':self.bytes}
    monkeypatch.setattr(E247,'Transporte',Transport)
    calls=[]
    def model(prompt,images,**kw):
        assert images and all(isinstance(x,bytes) and x.startswith(bytes.fromhex('ffd8')) for x in images)
        calls.append(prompt)
        if 'miniaturas anexadas' in prompt:
            return {'observacoes':[{'indice':0,'decisao':'PRIORIZAR_AQUISICAO','observacao':'Controlled preview observation.'}]}
        return {'veredito':'pertinente','natureza_visual':'registro_compativel','inspecao':'Controlled formal observation of the acquired image.'}
    monkeypatch.setattr(gemini,'json_visao',model)
    for k in ('CORINGA_PACOTE_PRIVADO','CORINGA_CHECKPOINTS_DESCOBERTOS'):
        monkeypatch.delenv(k,raising=False)
    monkeypatch.setenv('CORINGA_LIMITE_VISAO_DOCUMENTAL','2')
    monkeypatch.setattr(sys,'argv',['qa',str(spec),str(out),'fixture','--progressiva','--multicenas','--pretriagem-pendente','--revisar-previas','--encadear-previas'])
    E247.main()
    report=json.loads((out/'revisao.json').read_text())
    obs=json.loads((out/'observacoes-previas.json').read_text())
    assert downloads==[thumb,original] and len(calls)==2, obs.get('status')
    assert ('foto',True) in widths
    assert report['visao_chamadas_logicas']==report['visao_limite']==2
    row=report['cobertura'][0]
    assert row['estado']=='CANDIDATO_PRIVADO_REVISADO'
    c=row['rodadas'][-1]['pesquisa']['candidatos'][0]
    assert c['aquisicao']['width']==1200 and c['aquisicao']['url_adquirida']==original
    assert c['aquisicao']['sha256']!=obs['observacoes'][0]['preview_sha256']
    assert obs['cobertura_nova']==0 and report['publish'] is False and c['decisao']['direitos_aprovados'] is False


def test_network_reservation_preserves_global_ceiling_and_other_modalities():
    from src.v4.pretriagem_documental import reserva_rede_encadeamento
    assert reserva_rede_encadeamento(14,140_000_000,0)==(0,0)
    assert reserva_rede_encadeamento(14,140_000_000,1)==(4,29_000_000)
    assert reserva_rede_encadeamento(14,140_000_000,20)==(7,70_000_000)
    assert reserva_rede_encadeamento(1,100,1)==(0,50)
