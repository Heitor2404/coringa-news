from contextlib import contextmanager
from src.v4.formatos import cobertura_documental as C

def need(i,kind='registro'):
    return {'id':i,'fatos':['f'+i],'necessidade':kind,'evidencia_visual':'estatica',
            'mostrar':'evidence '+i,'pesquisa':{'consultas_en':['subject feature '+i]}}

def test_budget_reserved_and_atlas_not_searched():
    count={'visao':0,'http':0,'bytes':0};calls=[];scopes=[]
    def search(n,limit):
        assert n['id']!='map'
        return {'id':n['id'],'candidatos':[{'fonte':'test','tipo':'foto','source_id':len(calls)+1}]}
    def inspect(c,n):
        count['visao']+=1;count['http']+=1;count['bytes']+=100
        calls.append(n['id'])
        return {'estado':'INSUFICIENTE','motivo':'SEM_PERTINENCIA'}
    @contextmanager
    def scope(h,b):
        scopes.append((h,b));yield
    r=C.cobrir([need('a'),need('map','territorio'),need('b'),need('c')],search,inspect,lambda:dict(count),
              max_visao=4,max_http=12,max_bytes=1200,limitar_aquisicao=scope)
    assert calls==['a','a','b','c']
    assert [x['necessidade_id'] for x in r['cobertura']]==['a','map','b','c']
    assert r['resumo']=={'CANDIDATO_PRIVADO_REVISADO':0,'LACUNA_PENDENTE':3,'DELEGAR_ATLAS':1}
    assert r['consumo']['visao']==4 and len(scopes)==3
    assert not r['pronto_para_render'] and not r['publicar']

def test_success_keeps_binding_and_rights_pending():
    count={'visao':0,'http':0,'bytes':0}
    def inspect(c,n):
        count['visao']+=1
        return {'estado':'PERTINENTE_PRIVADO','necessidade_id':n['id'],'revisao_id':'r',
                'publicar':False,'direitos_aprovados':False}
    r=C.cobrir([need('a'),need('b')],lambda n,l:{'id':n['id'],'candidatos':[{'fonte':'test','tipo':'foto','source_id':n['id']}]},inspect,lambda:dict(count),max_visao=2,max_http=4,max_bytes=1000)
    assert r['resumo']['CANDIDATO_PRIVADO_REVISADO']==2
    assert r['consumo']['visao']==2 and not r['pronto_para_render']
