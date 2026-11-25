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
