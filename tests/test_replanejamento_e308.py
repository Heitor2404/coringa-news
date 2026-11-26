from src.v4.formatos import replanejamento_e308 as E

def need():
    return {'id':'n','fatos':['f'],'mostrar':'ice surface','sujeito':'glacier',
            'necessidade':'registro','evidencia_visual':'estatica','preferencia_midia':'video_preferencial',
            'pesquisa':{'consultas_en':['glacier ice surface']}}

def test_resume_only_unseen_videos_and_preserve_scope():
    n=need()
    photo={'fonte':'commons','source_id':'p','tipo':'foto'}
    video={'fonte':'commons','source_id':'v','tipo':'video','titulo':'glacier ice surface'}
    state={'pendentes':[photo,video],'vistos':{('commons','p')},'buscas_vistas':{('foto','commons','glacier ice surface')}}
    seen=[]
    def inspect(c,scope):
        seen.append((c['source_id'],scope))
        return {'estado':'PERTINENTE_PRIVADO','necessidade_id':'n','revisao_id':'r','publicar':False,'direitos_aprovados':False}
    result=E.fila_alternativa(n,state,lambda *a:None,inspect,pode_buscar=lambda:False,pode_inspecionar=lambda:True,pode_reusar=lambda c:False)
    assert result['selecionado']==('commons','v')
    assert seen[0][1]['fatos']==['f'] and seen[0][1]['evidencia_visual']=='estatica'
    assert state['pendentes']==[photo,video] and 'decisao' not in video

def test_zero_budget_does_not_search_or_inspect_remote():
    n=need();state={'pendentes':[{'fonte':'commons','source_id':'v','tipo':'video'}]}
    def forbidden(*a):raise AssertionError('unexpected call')
    result=E.fila_alternativa(n,state,forbidden,forbidden,pode_buscar=lambda:False,pode_inspecionar=lambda:False,pode_reusar=lambda c:False)
    assert result['estado']=='LACUNA_PENDENTE' and result['tentativas']==0

def test_new_search_reuses_attempted_keys_and_filters_photo():
    n=need();key=('video','commons','glacier ice surface')
    def search(n,limit,attempted):
        assert key in attempted
        return {'id':'n','buscas':[{'tipo':'video'}],'candidatos':[{'fonte':'commons','source_id':'p','tipo':'foto'}]}
    result=E.fila_alternativa(n,{'buscas_vistas':{key}},search,lambda *a:None,pode_buscar=lambda:True,pode_inspecionar=lambda:True,pode_reusar=lambda c:False)
    assert result['estado']=='LACUNA_PENDENTE' and result['tentativas']==0

def test_accept_only_compatible_alternative_keep_photo_on_failure():
    old={'necessidade_id':'n','selecionado':['commons','p'],'estado':'CANDIDATO_PRIVADO_REVISADO'}
    alternative={'selecionado':['commons','v'],'estado':'CANDIDATO_PRIVADO_REVISADO'}
    for valid in (True,False):
        report={'cobertura':[old]};final=[]
        def preparar(r):
            selected=r['cobertura'][0]['selecionado'][1]
            if selected=='v' and not valid:return {},{'capacidade_s':0,'pronto_para_tts':False}
            return {'n':{'need':need(),'kind':'video' if selected=='v' else 'photo'}},{'capacidade_s':3.8,'pronto_para_tts':False}
        logs=E.replanejar(report,preparar,lambda n:alternative,final.append)
        assert final==[valid]
        assert report['cobertura'][0]['selecionado'][1]==('v' if valid else 'p')
        assert logs[0]['reserva_foto']==['commons','p'] and logs[0]['aprovacao_editorial'] is False

def test_preferred_photo_not_replaced():
    n={**need(),'preferencia_midia':'foto_preferencial'}
    report={'cobertura':[{'necessidade_id':'n'}]}
    def forbidden(*a):raise AssertionError('unexpected call')
    logs=E.replanejar(report,lambda r:({'n':{'need':n,'kind':'photo'}},{'capacidade_s':3.8,'pronto_para_tts':False}),forbidden,forbidden)
    assert logs[0]['estado']=='REVISAO_EXPLICATIVA_PENDENTE'
