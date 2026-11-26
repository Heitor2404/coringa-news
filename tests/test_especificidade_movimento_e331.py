from copy import deepcopy
from pathlib import Path
from src.v4.formatos import especificidade_movimento_e331 as M,revisao_documental as R,ponte_cobertura_filme as B
from src.v3.pacote_biblioteca import sha

def test_scope_feedback_is_exact_and_never_global():
    x=M.registros()[0]
    n={'id':x['necessidade_id'],'fatos':x['fatos'],'mostrar':x['mostrar'],'evidencia_visual':'movimento'}
    assert M.feedback(n,x['sha256'],x['review_id'],x['source_in_seconds'])
    for k,v in [('mostrar','outra ação'),('fatos',['f2']),('id','n2'),('evidencia_visual','estatica')]:
        assert M.feedback({**n,k:v},x['sha256'],x['review_id']) is None
    assert M.feedback(n,x['sha256'],'b'*64) is None
    assert M.feedback(n,x['sha256'],x['review_id'],x['source_in_seconds']+1) is None
    q={'sha256_origem':x['sha256'],'necessidade_id':n['id'],'revisao_id':x['review_id'],
        'resposta':{'veredito':'pertinente','natureza_visual':'registro_compativel',
        'mudanca_observada':True,'indices_mudanca':[0,2],'descricao_mudanca':'Mudança observável de algum elemento.'}}
    c={'aquisicao':{'sha256':x['sha256']}}
    d=R.decidir(n,c,q,tipo='video')
    assert d['motivo']=='REVISAR_ACAO_ESPECIFICA' and not d['publicar']
    assert R.decidir({**n,'mostrar':'outra ação'},c,q,tipo='video')['estado']=='PERTINENTE_PRIVADO'

def test_partial_action_cannot_pass_generic_positive_and_legacy_remains_private():
    n={'id':'n','fatos':['f'],'mostrar':'mudança específica','evidencia_visual':'movimento'}
    h='a'*64;c={'aquisicao':{'sha256':h}}
    q={'sha256_origem':h,'necessidade_id':'n','revisao_id':'r','resposta':{'veredito':'pertinente',
        'natureza_visual':'registro_compativel','mudanca_observada':True,'indices_mudanca':[0,2],
        'descricao_mudanca':'Mudança visível de posição entre as amostras.'}}
    assert R.decidir(n,c,q,tipo='video')['correspondencia_acao']['estado']=='LEGADO_REVISAR'
    for value in ('parcial','incerta','nao_corresponde'):
        q['resposta']['correspondencia_acao']={'estado':value}
        assert R.decidir(n,c,q,tipo='video')['motivo']=='REVISAR_ACAO_ESPECIFICA'
    q['resposta']['correspondencia_acao']={'estado':'direta'}
    assert R.decidir(n,c,q,tipo='video')['motivo']=='FORMATO_CORRESPONDENCIA_ACAO_INVALIDO'
    q['resposta']['correspondencia_acao']={'estado':'direta','referente':'Elemento específico da cena.',
        'mudanca':'Mudança de posição observável.','referencia_estavel':'Objeto imóvel entre os quadros.'}
    d=R.decidir(n,c,q,tipo='video')
    assert d['estado']=='PERTINENTE_PRIVADO' and not d['correspondencia_acao']['especificidade_verificada']
    assert not d['prova_de_acao_continua']

def test_bridge_replans_instead_of_using_known_partial_action(monkeypatch,tmp_path):
    monkeypatch.chdir(tmp_path)
    x=M.registros()[0];p=Path('stage_documental/test.webm');p.parent.mkdir();p.write_bytes(b'fixture only')
    n={'id':x['necessidade_id'],'fatos':x['fatos'],'mostrar':x['mostrar'],'evidencia_visual':'movimento','exigir_evidencia_direta':True}
    # Test only bridge routing. Actual historical source separately authenticated E330.
    monkeypatch.setattr(B,'sha',lambda _:x['sha256'])
    c={'fonte':'commons','source_id':'s','tipo':'video','local_source':str(p),'pagina':'https://commons.wikimedia.org/wiki/File:Example.webm',
        'credito':'Author','licenca':'Public domain','aquisicao':{'sha256':x['sha256'],'width':1920,'height':1080,'duration_s':45},
        'decisao':{'estado':'PERTINENTE_PRIVADO','necessidade_id':n['id'],'revisao_id':x['review_id'],'publicar':False,'direitos_aprovados':False},
        'selecao_janela':{'revisao_id':x['review_id'],'source_in_seconds':x['source_in_seconds'],'duracao_s':3.8}}
    report={'publish':False,'triagem':[n],'cobertura':[{'necessidade_id':n['id'],'estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','s'],'rodadas':[{'pesquisa':{'candidatos':[c]}}]}]}
    case={'chapters':[{'needs':[n['id']]}]}
    selected,gate=B.preparar_cobertura(report,case,minimo_s=1.4)
    assert not selected and not gate['pronto_para_tts']
    task=gate['replanejamento_por_fato'][0]
    assert task['mostrar']==n['mostrar'] and task['fatos']==n['fatos'] and task['acao']=='BUSCAR_OUTRA_JANELA_OU_FONTE_DA_ACAO_EXATA'
    assert not task['autoriza_animacao'] and not task['publicar']
