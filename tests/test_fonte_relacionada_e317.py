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

def test_full_source_review_survives_actual_bridge(tmp_path,monkeypatch):
    from pathlib import Path
    import hashlib,shutil
    from src.v4.formatos import ponte_cobertura_filme as P
    src=Path(__file__).resolve().parent/'midia/video_horizontal_navio.mp4'
    monkeypatch.chdir(tmp_path);Path('stage_documental').mkdir()
    target=Path('stage_documental/ship.mp4');shutil.copyfile(src,target)
    h=hashlib.sha256(target.read_bytes()).hexdigest()
    n={'id':'n','fatos':['f'],'sujeito':'ship','mostrar':'context','exigir_evidencia_direta':True,'evidencia_visual':'estatica'}
    c={'fonte':'commons','source_id':'ship','tipo':'video','pagina':'https://commons.wikimedia.org/wiki/File:Continuing_Promise_transits_the_Panama_Canal-ZLIWzvfdisQ-248%2B251.webm',
       'credito':'U.S. Navy','licenca':'Public domain','local_source':str(target),'aquisicao':{'sha256':h,'width':1280,'height':720,'duration_s':6.006},
       'decisao':{'estado':'PERTINENTE_PRIVADO','necessidade_id':'n','revisao_id':'r','publicar':False,'direitos_aprovados':False},
       'selecao_janela':{'source_in_seconds':0,'duracao_s':3,'revisao_id':'r','video_framing':{'modo':'fonte_integral','sha256_origem':h,
            'inspecao':'Preservar o contexto do navio e seus referentes visíveis no quadro.',
            'motivo':'Evitar remoção de elementos do registro original.'}}}
    report={'publish':False,'triagem':[n],'cobertura':[{'necessidade_id':'n','estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','ship'],'rodadas':[{'pesquisa':{'candidatos':[c]}}]}]}
    case={'tema':'test','chapters':[{'title':'test','needs':['n']}]}
    chosen,gate=P.preparar_cobertura(report,case,minimo_s=1.4)
    assert gate['pronto_para_tts']
    plan=P.plano(case,chosen,[90])
    assert plan['shots'][0]['video_framing']['modo']=='fonte_integral'
    c['selecao_janela']['video_framing']['sha256_origem']='0'*64
    chosen,gate=P.preparar_cobertura(report,case,minimo_s=1.4)
    assert gate['pronto_para_tts'] and chosen['n']['framing'] is None
