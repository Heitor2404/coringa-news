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


def test_e336_vertical_tie_break_does_not_override_relevance_or_memory():
    from src.v4.formatos.revisao_documental import ordenar_candidatos
    n={'id':'n','fatos':['f'],'sujeito':'canal','mostrar':'canal lock gate','necessidade':'registro',
       'evidencia_visual':'movimento','pesquisa':{'consultas_en':['canal lock gate']}}
    base={'fonte':'commons_video','tipo':'video','titulo':'canal lock gate','source_id':'a','direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA'}
    landscape={**base,'largura_declarada':1920,'altura_declarada':1080}
    portrait={**base,'source_id':'b','largura_declarada':1080,'altura_declarada':1920}
    assert ordenar_candidatos(n,[landscape,portrait])[0] is landscape
    opt={**n,'preferir_imersao_vertical':True}
    assert ordenar_candidatos(opt,[landscape,portrait])[0] is portrait
    unrelated={**portrait,'titulo':'unrelated mountain'}
    assert ordenar_candidatos(opt,[unrelated,landscape])[0] is landscape
    memory={**landscape,'fonte':'biblioteca_v3','pista_revisao_mesmo_escopo':True}
    assert ordenar_candidatos(opt,[portrait,memory])[0] is memory
    tiny={**portrait,'largura_declarada':180,'altura_declarada':320}
    assert ordenar_candidatos(opt,[landscape,tiny])[0] is landscape

def test_e336_crop_estimate_is_not_render_or_editorial_approval():
    from src.v4.formatos import imersao_documental_e328 as I
    assert I.fracao_integral(1920,1080)==.3164
    assert I.fracao_integral(1080,1920)==1
    assert I.fracao_integral(0,1920) is None
    assert I.potencial_recorte({'type':'video'},{'width':1920,'height':1080}) is None
    assert I.potencial_recorte({'type':'photo'},{},{'height':1350})==.7031
    shot={'id':'a','asset':'a','type':'photo','start':0,'end':3}
    row={'id':'a','start':0,'end':3,'kind':'photo','fatos':['f'],'mostrar':'component',
         'evidencia_visual':'estatica','papel_visual':'detalhe','integral_canvas_fraction':.3164,
         'observed_crop_candidate_fraction':.7031}
    r=I.diagnosticar({'shots':[shot],'media':{'a':{'width':1920,'height':1080}}},[row])
    assert 'COMPARAR_RECORTE_OBSERVADO_COM_FONTE_INTEGRAL' in r['tasks'][0]['tarefas']
    assert not r['actual_render_verified'] and not r['editorial_approval']
