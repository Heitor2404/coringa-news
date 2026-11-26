from src.v4.formatos.direcao_short_e306 import diagnosticar

def test_immersion_triage_preserves_facts_and_never_approves():
    p={'media':{'a':{'width':3000,'height':800,'expected_sha256':'h'}},'shots':[
        {'id':'a','asset':'a','type':'video','start':0,'end':3},
        {'id':'b','asset':'a','type':'video','start':3,'end':6}],
        'necessidades_direcao':[{'id':'a','fatos':['f'],'mostrar':'Ação observável'}]}
    r=diagnosticar(p)['imersao_documental']
    assert r['low_integral_fraction_s']==6 and r['adjacent_same_source_video_s']==3
    assert r['tasks'][0]['fatos']==['f']
    assert 'REVISAR_REGIAO_DE_ACAO_ANTES_DE_RECORTAR' in r['tasks'][0]['tarefas']
    assert not r['editorial_approval'] and not r['actual_render_verified']

def test_e329_prioritizes_real_obligations_without_penalizing_native_area():
    p={'media':{'a':{'width':1920,'height':1080},'b':{'width':1080,'height':1920}},'shots':[
        {'id':'a','asset':'a','type':'video','start':0,'end':3},
        {'id':'b','asset':'b','type':'video','start':3,'end':6}],
        'necessidades_direcao':[{'id':'a','fatos':['f1'],'mostrar':'Ação','evidencia_visual':'movimento'},
                              {'id':'b','fatos':['f2'],'mostrar':'Consequência','papel_visual':'consequencia'}]}
    r=diagnosticar(p)['imersao_documental']
    assert r['moderate_integral_fraction_s']==3 and r['unknown_portrait_s']==3
    assert r['tasks'][0]['prioridade']=='GANCHO' and r['tasks'][1]['prioridade']=='EVIDENCIA'
    assert 'REVISAR_SOBREPOSICAO_E_LEGENDAS_ORIGINAIS' in r['tasks'][1]['tarefas']
    assert r['tasks'][1]['fatos']==['f2'] and not r['editorial_approval']
