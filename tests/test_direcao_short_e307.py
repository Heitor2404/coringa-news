from src.v4.formatos import diretor_visual_e202 as D,revisao_documental as R
from src.v4 import acervo_v4 as A
from src.v4.formatos.direcao_short_e306 import diagnosticar
import pytest

def need(**kw):
    return {**{'id':'n','fatos':['f'],'sujeito':'glacier','mostrar':'glacier surface','necessidade':'registro','evidencia_visual':'estatica','consultas_en':['glacier surface','glacier ice']},**kw}

def test_preference_preserves_fact_and_evidence_and_rejects_invalid():
    n=D.triagem_documental([need(preferencia_midia='video_preferencial',papel_visual='detalhe')],[{'id':'f'}],{'itens':[]})[0]
    assert n['preferencia_midia']=='video_preferencial' and n['papel_visual']=='detalhe'
    assert n['fatos']==['f'] and n['evidencia_visual']=='estatica'
    with pytest.raises(ValueError,match='E307-PREFERENCIA'):
        D.triagem_documental([need(preferencia_midia='inventar')],[{'id':'f'}],{'itens':[]})
    n=D.triagem_documental([need(evidencia_visual='movimento',preferencia_midia='foto_preferencial')],[{'id':'f'}],{'itens':[]})[0]
    assert n['preferencia_midia']=='video_preferencial'

def test_search_preference_changes_order_not_eligibility():
    calls=[]
    def sources(t):
        def search(q):calls.append(t);return []
        return [(t,search)]
    n={**need(),'pesquisa':{'consultas_en':['glacier surface']}}
    A.pesquisar_cobertura({**n,'preferencia_midia':'video_preferencial'},fontes=sources,max_buscas=2)
    assert calls==['video','foto']
    calls.clear()
    A.pesquisar_cobertura({**n,'evidencia_visual':'movimento','preferencia_midia':'foto_preferencial'},fontes=sources,max_buscas=2)
    assert calls==['video']

def test_equivalent_video_preferred_but_photo_still_eligible():
    n={**need(),'preferencia_midia':'video_preferencial'}
    photo={'tipo':'foto','fonte':'commons','titulo':'glacier surface','source_id':'p'}
    video={**photo,'tipo':'video','source_id':'v'}
    assert R.ordenar_candidatos(n,[photo,video])[0] is video
    assert R.ordenar_candidatos(need(),[video,photo])[0] is photo
    assert R.ordenar_candidatos(n,[photo])==[photo]

def test_remediation_reuses_exact_need_not_invented_action():
    p={'shots':[{'id':'n','type':'photo','start':0,'end':3,'asset':'m'}],
       'media':{'m':{'width':1920,'height':1080}},
       'necessidades_direcao':[{'id':'n','fatos':['f'],'mostrar':'glacier surface','evidencia_visual':'estatica','preferencia_midia':'video_preferencial','papel_visual':'detalhe'}]}
    r=diagnosticar(p);t=r['tarefas_replanejamento'][0]
    assert t['fatos']==['f'] and t['mostrar']=='glacier surface'
    assert t['preservar_evidencia_visual']=='estatica' and not t['autoriza_animacao']
