from src.v4.formatos import revisao_documental as R

def need(ev='estatica'):
    return {'id':'n','necessidade':'registro','evidencia_visual':ev,
            'pesquisa':{'consultas_en':['subject visible feature','subject detail']},'mostrar':'referente'}

def candidate(i,kind='foto',**kw):
    return {'fonte':'commons','source_id':i,'tipo':kind,'url':f'https://example.org/{i}',**kw}

def accepted(n):
    return {'estado':'PERTINENTE_PRIVADO','necessidade_id':n['id'],'revisao_id':'r',
            'publicar':False,'direitos_aprovados':False}

def test_adaptive_after_refusal_preserves_obligation_and_skips_duplicate():
    searches=[];inspected=[]
    def search(n,limit):
        searches.append(n)
        assert limit==4 and n['id']=='n' and n['mostrar']=='referente'
        return {'id':'n','candidatos':[candidate(1)] if len(searches)==1 else [candidate(1),candidate(2)]}
    def inspect(c,n):
        inspected.append(c['source_id'])
        return {'estado':'INSUFICIENTE','motivo':'NATUREZA_INCOMPATIVEL_OU_INCERTA'} if c['source_id']==1 else accepted(n)
    r=R.cobertura_adaptativa(need(),search,inspect,lambda phase:len(inspected)<phase+1)
    assert inspected==[1,2] and len(searches)==2
    assert searches[1]['pesquisa']['consultas_en'][0]=='subject visible photograph'
    assert r['estado']=='CANDIDATO_PRIVADO_REVISADO' and r['tentativas']==2 and not r['pronto_para_render']

def test_no_extra_search_after_valid_candidate():
    searches=[]
    def search(n,limit):
        searches.append(n);return {'id':'n','candidatos':[candidate(1)]}
    r=R.cobertura_adaptativa(need(),search,lambda c,n:accepted(n),lambda phase:True)
    assert len(searches)==1 and r['estado']=='CANDIDATO_PRIVADO_REVISADO'

def test_motion_requery_never_uses_photo_and_honors_budget():
    searches=[];inspected=[]
    def search(n,limit):
        searches.append(n);return {'id':'n','candidatos':[candidate(1),candidate(len(searches)+1,'video')]}
    def inspect(c,n):
        inspected.append(c['tipo']);return {'estado':'INSUFICIENTE','motivo':'SEM_JANELA_PERTINENTE_NO_ORCAMENTO'}
    r=R.cobertura_adaptativa(need('movimento'),search,inspect,lambda phase:len(inspected)<phase+1)
    assert inspected==['video','video'] and r['estado']=='LACUNA_PENDENTE'
    assert searches[1]['pesquisa']['consultas_en'][0]=='subject visible'
    r=R.cobertura_adaptativa(need(),search,inspect,lambda phase:False)
    assert r['rodadas']==[] and r['tentativas']==0

def test_uninspected_previous_candidate_not_lost():
    calls=[]
    def search(n,limit):
        return {'id':'n','candidatos':[candidate(1),candidate(2)] if not calls else []}
    def inspect(c,n):
        calls.append(c['source_id'])
        return {'estado':'INSUFICIENTE','motivo':'SEM_PERTINENCIA'} if len(calls)==1 else accepted(n)
    r=R.cobertura_adaptativa(need(),search,inspect,lambda phase:len(calls)<phase+1)
    assert calls==[1,2] and r['estado']=='CANDIDATO_PRIVADO_REVISADO'
