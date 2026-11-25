from scripts.qa_pretriagem_e269 import candidatos
def test_preview_declared_only_no_repeat_no_approval():
    n={'necessidade':'registro','mostrar':'mountain','evidencia_visual':'estatica','pesquisa':{'consultas_en':['mountain']}}
    c={'fonte':'commons','tipo':'foto','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA','pagina':'p','titulo':'mountain','url':'original','variantes':[{'url':'thumb','width':640,'height':480}]}
    assert candidatos(n,[c])[0][1]['url']=='thumb'
    assert candidatos(n,[c],['p'])==[]
    assert candidatos(n,[{**c,'variantes':[]}])==[]
    assert candidatos(n,[{**c,'titulo':'Topographic map of mountain'}])==[]
    assert candidatos(n,[{**c,'variantes':[{'url':'original','width':640,'height':480}]}])==[]
