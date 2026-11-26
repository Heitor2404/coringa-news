from src.v4.formatos import fonte_relacionada_e317 as F

def test_exact_factual_source_reuses_download_but_not_decision():
    page='https://example.org/record'
    a={'id':'a','fatos':['f1'],'papel_visual':'acao'};b={'id':'b','fatos':['f2'],'papel_visual':'consequencia'}
    case={'fatos':[{'id':'f1','fonte':page},{'id':'f2','fonte':page}]}
    c={'fonte':'commons','source_id':'v','url':page,'pagina':page,'tipo':'video','titulo':'video',
       'aquisicao':{'sha256':'h'},'decisao':{'estado':'PERTINENTE_PRIVADO','necessidade_id':'a','revisao_id':'r','publicar':False,'direitos_aprovados':False},
       'selecao_janela':{'source_in_seconds':7},'janelas':[1]}
    key=('commons','v');rows={'a':{'estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':key,'rodadas':[{'pesquisa':{'candidatos':[c]}}]}}
    acq={key:({'sha256':'h'},None,None,{})}
    order={'a':0,'b':1}
    result=F.pista(b,case,[a,b],rows,acq,order)
    assert result['pista_fonte_relacionada']=='a'
    assert not set(result)&{'decisao','aquisicao','selecao_janela','janelas'}
    assert F.pista(b,case,[a,b],rows,{},order) is None
    assert F.pista(b,{'fatos':[{'id':'f1','fonte':page},{'id':'f2','fonte':'other'}]},[a,b],rows,acq,order) is None
    assert F.pista({**b,'papel_visual':'contexto'},case,[a,b],rows,acq,order) is None
