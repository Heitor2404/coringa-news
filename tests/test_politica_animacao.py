import json
from pathlib import Path
import pytest
from src.v4.formatos import politica_animacao as P, filme_editorial as F
from src.v4.formatos import diretor_visual_e202 as D

def test_fixture_e207_reprovada_na_saida():
    p=json.loads(Path('docs/v4/formatos/filme_panama_12s_prova.json').read_text())
    r=P.avaliar(p['shots'],privado=True)
    assert not r['permitido']
    assert r['rotas']==[{'cena':'02-principio-hidraulico','renderer':'mechanism:lock_filling','status':'REPROVADO'}]

@pytest.mark.parametrize('renderer',['lock_filling','lock_causal','lock_cycle','lock_cycle_standalone','lock_explainer','optical_projection','inventado'])
def test_todas_rotas_legadas_e_desconhecidas_reprovadas(renderer):
    with pytest.raises(ValueError,match='E211-POLITICA-VISUAL'):
        P.exigir([{'id':'a','type':'mechanism','mechanism':renderer}],privado=True)

def test_qa_legado_explicito_nao_equivale_a_editorial():
    s=[{'id':'a','type':'mechanism','mechanism':'lock_filling'}]
    assert not P.avaliar(s,modo=P.LEGACY,privado=False)['permitido']
    assert not P.avaliar(s,modo=P.LEGACY,privado=True,preview=False)['permitido']
    r=P.exigir(s,modo=P.LEGACY,privado=True)
    assert not r['editorial_homologado']
    assert not P.avaliar([{'id':'a','type':'mechanism','mechanism':'inventado'}],modo=P.LEGACY,privado=True)['permitido']

def test_preservar_midia_e_atlas_candidato_privado():
    s=[{'id':'v','type':'video'},{'id':'p','type':'photo'},{'id':'m','type':'atlas_map'}]
    assert P.avaliar(s)['permitido']
    s.append({'id':'a','type':'scene_graph','scene_graph':{'schema':'coringa.scene_graph.private.v2'}})
    assert not P.avaliar(s)['permitido']
    r=P.exigir(s,privado=True)
    assert not r['editorial_homologado']

def test_midias_primeiro_e_fallback_honesto():
    kwargs=dict(acao='fluxo por dentro de um equipamento',lacuna='interior invisível',motivo_lacuna='IMPOSSIVEL_FILMAR')
    assert P.decidir_complemento(midia_adequada=True,**kwargs,renderer='mechanism:lock_filling')=='USAR_MIDIA_REAL'
    assert P.decidir_complemento(midia_adequada=False,**kwargs,renderer='mechanism:lock_filling')=='REPLANEJAR_MIDIA_REAL_OU_DECLARAR_LACUNA'
    assert P.decidir_complemento(midia_adequada=False,**kwargs,renderer='scene_graph:coringa.scene_graph.private.v2')=='ANIMACAO_COMPLEMENTAR_EM_QA_PRIVADA'
    assert P.decidir_complemento(midia_adequada=False,**{**kwargs,'motivo_lacuna':'SEM_PESQUISA'})=='PESQUISAR_OU_REPLANEJAR_MIDIA_REAL'

def test_preflight_bloqueia_fixture_antiga_antes_de_baixar(tmp_path,monkeypatch):
    p=json.loads(Path('docs/v4/formatos/filme_panama_12s_prova.json').read_text())
    p['publicar']=False
    # The structural preflight is deliberately stubbed: test the independent visual gate.
    monkeypatch.setattr(F,'avaliar',lambda p:{'pronto':True})
    with pytest.raises(ValueError,match='E211-POLITICA-VISUAL'):
        F.preparar(p,tmp_path/'out',tmp_path/'public',downloader=lambda u:pytest.fail('download indevido'))
    assert not (tmp_path/'out'/'props.json').exists()
    assert not json.loads((tmp_path/'out'/'politica_animacao.json').read_text())['permitido']

def test_narracao_nao_aceita_bypass_qa(tmp_path):
    p={'preview':True,'private_review_only':True,'animation_policy_mode':P.LEGACY,
       'shots':[{'id':'a','type':'mechanism','mechanism':'lock_filling'}]}
    with pytest.raises(ValueError,match='E211-LEGADO-NAO-ENTRA-EM-DOCUMENTARIO'):
        D.anexar_audio_documental(p,'',[],tmp_path,'PALAVRAS_MEDIDAS')
