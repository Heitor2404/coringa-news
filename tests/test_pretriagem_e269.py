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
