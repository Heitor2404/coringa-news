from scripts.diagnosticar_diversidade_documental import fila_editorial
def test_scoped_editorial_review_does_not_erase_technical_coverage():
    n={'id':'n','mostrar':'waterfall','evidencia_visual':'estatica','pesquisa':{'consultas_en':['waterfall']}}
    c={'fonte':'commons','source_id':'a','tipo':'foto','aquisicao':{'sha256':'a'*64},'decisao':{'estado':'PERTINENTE_PRIVADO'}}
    v={'fonte':'commons_video','source_id':'b','tipo':'video','titulo':'waterfall'}
    report={'publish':False,'triagem':[n],'cobertura':[{'necessidade_id':'n','estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','a'],'rodadas':[{'pesquisa':{'candidatos':[c,v]}}]}]}
    obs={'id':'n','mostrar':'waterfall','sha256':'a'*64,'motivo':'detail'}
    out=fila_editorial(report,{'publicar':False,'observacoes':[obs]})
    assert out['fila'][0]['estado_tecnico']=='CANDIDATO_PRIVADO_REVISADO'
    assert out['fila'][0]['pistas_video'][0]['source_id']=='b'
    assert not out['aprovacao_editorial']
    assert not fila_editorial(report,{'publicar':False,'observacoes':[{**obs,'sha256':'b'*64}]})['fila']
    assert not fila_editorial(report,{'publicar':False,'observacoes':[{**obs,'mostrar':'other'}]})['fila']
