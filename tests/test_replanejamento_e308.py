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

def test_optional_discovery_failure_preserves_full_original_receipt():
    old={'necessidade_id':'n','selecionado':['commons','p'],'estado':'CANDIDATO_PRIVADO_REVISADO',
         'rodadas':[{'receipt':'original scope'}]}
    report={'cobertura':[old]};finished=[]
    def fail(n):raise RuntimeError('provider unavailable')
    logs=E.replanejar(report,lambda r:({'n':{'need':need(),'kind':'photo'}},{'capacidade_s':3.8,'pronto_para_tts':False}),fail,finished.append)
    assert report['cobertura']==[old] and finished==[False]
    assert logs[0]['estado']=='FALHA_REPLANEJAMENTO_RESERVA_PRESERVADA'
    assert logs[0]['cobertura_reserva']==old and 'provider unavailable' in logs[0]['erro']

def test_e308_actual_bridge_rechecks_hash_and_duration(tmp_path,monkeypatch):
    # Synthetic review receipts/bytes: tests the real bridge, not media semantics.
    from pathlib import Path
    from hashlib import sha256
    from src.v4.formatos import ponte_cobertura_filme as P
    monkeypatch.chdir(tmp_path)
    Path('stage_documental').mkdir()
    n={**need(),'exigir_evidencia_direta':True}
    def row(kind,bad=False):
        name='p.jpg' if kind=='foto' else 'v.mp4'
        path=Path('stage_documental')/name
        path.write_bytes(name.encode())
        h=sha256(path.read_bytes()).hexdigest()
        c={'fonte':'commons','source_id':name,'tipo':kind,'pagina':'https://commons.wikimedia.org/wiki/File:'+name,
           'credito':'Test fixture','licenca':'CC0','local_source':str(path),
           'aquisicao':{'sha256':'0'*64 if bad else h,'width':1920,'height':1080,'duration_s':10},
           'decisao':{'estado':'PERTINENTE_PRIVADO','necessidade_id':'n','revisao_id':'r','publicar':False,'direitos_aprovados':False}}
        if kind=='video':c['selecao_janela']={'source_in_seconds':0,'duracao_s':3.8}
        return {'necessidade_id':'n','estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons',name],
                'rodadas':[{'pesquisa':{'candidatos':[c]}}]}
    case={'chapters':[{'needs':['n']}]}
    for bad in (False,True):
        old=row('foto')
        report={'publish':False,'triagem':[n],'cobertura':[old]}
        finished=[]
        logs=E.replanejar(report,lambda r:P.preparar_cobertura(r,case),lambda n:row('video',bad),finished.append)
        assert finished==[not bad]
        assert report['cobertura'][0]['selecionado'][1]==('p.jpg' if bad else 'v.mp4')
        assert logs[0]['cobertura_reserva']==old
