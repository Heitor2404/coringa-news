"""E246: exercise the real director search contract with injected sources."""
import pytest
from src.v4 import acervo_v4 as A
from src.v4.formatos import diretor_visual_e202 as D

def need(ev='movimento',kind='registro'):
    return {'id':'n','fatos':['f'],'sujeito':'referente','mostrar':'ação ou forma',
            'necessidade':kind,'evidencia_visual':ev,'consultas_en':['first query','alternate query'],
            **({'lacuna':'ação interna'} if kind=='lacuna_explicativa' else {})}

def triage(ev='movimento',kind='registro'):
    return D.triagem_documental([need(ev,kind)],[{'id':'f'}],{'itens':[],'reprovados':[]})

def raw(q,lic='CC BY 4.0'):
    return {'titulo':q,'url':'https://upload.wikimedia.org/'+q.replace(' ','_')+'.jpg',
            'pagina':'https://commons.wikimedia.org/wiki/File:test.jpg','licenca':lic,
            'credito':'Autor ('+lic+')','w':1280,'h':720}

def test_motion_never_substitutes_photo_and_requeries():
    calls=[]
    def sources(tipo):
        assert tipo=='video'
        def lookup(q):
            calls.append(q)
            return [] if q=='first query' else [raw(q)]
        return [('commons_video',lookup)]
    r=D.pesquisar_triagem(triage(),fontes=sources)[0]
    assert calls==['first query','alternate query']
    assert r['estado']=='REVISAR_CANDIDATOS' and len(r['candidatos'])==1
    assert not r['pronto_para_render'] and not r['publicar']

def test_photo_and_video_candidates_remain_unverified():
    r=D.pesquisar_triagem(triage('estatica'),fontes=lambda t:[('commons' if t=='foto' else 'commons_video',lambda q:[raw(q+' '+t)])])[0]
    assert {c['tipo'] for c in r['candidatos']}=={'foto','video'}
    assert all(c['estado']=='CANDIDATO_NAO_INSPECIONADO' for c in r['candidatos'])
    assert all(not c['publicar'] for c in r['candidatos'])

def test_catalogue_review_stops_before_network():
    n=triage()[0];n['candidatos']=[{'asset_id':'existing','natureza':'video','sha_catalogo':'a'*64}]
    def never(t):pytest.fail('external search unnecessary')
    r=A.pesquisar_cobertura(n,fontes=never,inspecionar=lambda c,n:{'estado':'PERTINENTE_PRIVADO','necessidade_id':n['id']})
    assert r['estado']=='CANDIDATO_PRIVADO_REVISADO' and r['buscas']==[]
    assert not r['pronto_para_render']

def test_other_need_review_cannot_stop_search():
    r=D.pesquisar_triagem(triage(),fontes=lambda t:[('commons_video',lambda q:[raw(q)])],
            inspecionar=lambda c,n:{'estado':'PERTINENTE_PRIVADO','necessidade_id':'other'})[0]
    assert len(r['buscas'])==2 and r['estado']=='REVISAR_CANDIDATOS'

def test_geo_delegation_and_no_auto_animation_on_gap():
    def never(t):pytest.fail('map discovery is separate')
    assert D.pesquisar_triagem(triage('estatica','territorio'),fontes=never)[0]['estado']=='DELEGAR_ATLAS'
    r=D.pesquisar_triagem(triage('movimento','lacuna_explicativa'),fontes=lambda t:[])[0]
    assert r['estado']=='LACUNA_NAO_VERIFICADA' and not r['pronto_para_render']

def test_reject_nc_and_keep_generic_source_rights_pending():
    r=D.pesquisar_triagem(triage('estatica'),fontes=lambda t:[('nasa',lambda q:[raw(q,'CC BY-NC 4.0'),raw(q+' good','CC BY 4.0')])])[0]
    assert all('NC' not in c['licenca'] for c in r['candidatos'])
    assert all(c['direitos']=='REVISAR_PAGINA_INDIVIDUAL' for c in r['candidatos'])
    assert r['candidatos']

def test_global_library_before_network_and_source_failure():
    class Lib:
        def buscar(self,q,tipo,limite):
            return [{'id':'v3','sha256':'a'*64}]
    def fail(q):raise OSError()
    r=D.pesquisar_triagem(triage(),biblioteca_global=Lib(),fontes=lambda t:[('broken',fail)])[0]
    assert r['biblioteca'][0]['origem']=='biblioteca_v3'
    assert all(x['estado']=='FALHA' for x in r['buscas'])
    assert not r['pronto_para_render']

def test_budget_and_dedupe():
    r=D.pesquisar_triagem(triage(),fontes=lambda t:[('commons_video',lambda q:[raw('same')]*9)]*4,max_buscas=2)[0]
    assert len(r['buscas'])==2 and len(r['candidatos'])==1
