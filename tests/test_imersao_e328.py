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
