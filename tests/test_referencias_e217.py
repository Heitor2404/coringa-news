import pytest
from src.v4.formatos.diretor_visual_e202 import selecionar_complemento as select

N={'id':'a','necessidade':'lacuna_explicativa','mostrar':'Transmitir movimento entre eixos','lacuna':'Interior não visível','fatos':['f']}
R={'id':'a','acao':N['mostrar'],'fatos':['f'],'origem':'CURADORIA_HUMANA',
   'midia_adequada':False,'justificativa':'Interior opaco','motivo':'IMPOSSIVEL_FILMAR',
   'alvo_tecnico':'modelo auditado','exige_contorno_industrial':True}
C={'tipo':'cad_real','alvo':R['alvo_tecnico'],'identidade_verificada':True,
   'fonte_sha256':'a'*64,'fonte_url':'https://example.org/fixture',
   'licenca_candidata':'permissiva','juntas_fundamentadas':True,'movimento_fundamentado':True,
   'estado':'VALIDADO_TECNICAMENTE_SEM_HOMOLOGACAO_VISUAL',
   'verificacao_contato':'SEM_INTERFERENCIA_BREP_NA_AMOSTRA','sobreposicao_inicial_fonte':False,
   'acao_revisada':N['mostrar'],'fatos_revisados':['f']}

def test_media_first_does_not_search_cad():
    r=select(N,{**R,'midia_adequada':True},[C],pesquisar_cad=True,
             getter_cad=lambda _:pytest.fail('pesquisa desnecessaria'))
    assert r['decisao']=='USAR_MIDIA_REAL'

def test_reference_must_match_action_and_scope():
    assert select(N,R,[{**C,'acao_revisada':'Outra ação'}])['rota']['decisao'] is None
    assert select(N,R,[{**C,'alvo':'Outro modelo'}])['rota']['decisao'] is None
    assert select(N,R,[{**C,'estado':'REPROVADO_INTERFERENCIA_BREP'}])['rota']['decisao'] is None
    r=select(N,R,[C])
    assert r['renderer_proposto']=='cad_preview' and not r['pronto_para_render']

def test_search_requires_review_and_never_homologates():
    with pytest.raises(ValueError,match='SEM-BUSCA'):
        select(N,{**R,'motivo':'BUSCA_SEM_REGISTRO_ADEQUADO'},[])
    with pytest.raises(ValueError,match='ORIGEM-REVISAO'):
        select(N,{**R,'origem':'LLM'},[C])
    r=select(N,{**R,'consulta_cad':'mechanism CAD'},[],pesquisar_cad=True,
             getter_cad=lambda _:{'items':[]})
    assert not r['pesquisa_cad']['candidates'] and not r['pronto_para_render']
    assert r['decisao']=='REPLANEJAR_MIDIA_REAL_OU_DECLARAR_LACUNA'
