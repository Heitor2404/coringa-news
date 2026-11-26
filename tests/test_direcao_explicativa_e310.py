import hashlib,json,shutil
from pathlib import Path
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F
from src.v4.formatos.direcao_short_e306 import diagnosticar

def test_detail_travels_from_review_through_actual_bridge_and_preflight(tmp_path,monkeypatch):
    # Exact real image reviewed in E309. Scope/ROI is assisted, not model discovery.
    source=Path(__file__).resolve().parents[1]/'tests/midia/foto_vertical_salto_angel.jpg'
    monkeypatch.chdir(tmp_path)
    Path('stage_documental').mkdir()
    dest=Path('stage_documental')/'water.jpg'
    shutil.copyfile(source,dest)
    data=dest.read_bytes()
    assert hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()=='a0d3e9edf55d675d7e8d69aecafb43cd2c467878'
    h=hashlib.sha256(data).hexdigest()
    n={'id':'n','fatos':['f'],'mostrar':'coluna de agua intermediaria','sujeito':'Salto Ángel',
       'papel_visual':'detalhe','evidencia_visual':'estatica','exigir_evidencia_direta':True}
    c={'fonte':'commons','source_id':'water','tipo':'foto','pagina':'https://commons.wikimedia.org/wiki/File:Salto_Angel_Dry_Season.jpg',
       'credito':'Berrucomons · CC BY-SA 4.0','licenca':'CC BY-SA 4.0','local_source':str(dest),
       'aquisicao':{'sha256':h,'width':946,'height':1600,'duration_s':None},
       'decisao':{'estado':'PERTINENTE_PRIVADO','necessidade_id':'n','revisao_id':'E309-assisted-fixture',
                  'publicar':False,'direitos_aprovados':False,
                  'evidencia_direta_normalizada':{'bbox':[.49,.37,.56,.52],'escala_origem':'xy_0_1'}}}
    row={'necessidade_id':'n','estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','water'],
         'rodadas':[{'pesquisa':{'candidatos':[c]}}]}
    case={'tema':'Salto Ángel','chapters':[{'title':'Detalhe','needs':['n']}]}
    chosen,gate=P.preparar_cobertura({'publish':False,'triagem':[n],'cobertura':[row]},case,minimo_s=1.4)
    assert gate['pronto_para_tts'],gate
    p=P.plano(case,chosen,[90])
    assert p['shots'][0]['documentary_detail_intent'] is True
    diag=diagnosticar(p)
    assert diag['direcao_explicativa'][0]['estado']=='CANDIDATO_DESTAQUE_OBSERVADO'
    assert not diag['pronto_para_analise_visual'] # still a static photo; marker is not an event
    result=F.preparar(p,tmp_path/'out',tmp_path/'public',fragmento_misto=True)
    props=json.loads(Path(result['props']).read_text())
    assert props['shots'][0]['documentary_detail_roi']['sha256']==h
    assert props['private_review_only'] and props['documentary_media_preview']
    p['shots'][0]['documentary_detail_intent']=False
    p['shots'][0]['documentary_detail_roi']={'invented':True}
    result=F.preparar(p,tmp_path/'out2',tmp_path/'public',fragmento_misto=True)
    assert 'documentary_detail_roi' not in json.loads(Path(result['props']).read_text())['shots'][0]

def test_roles_preserve_fact_without_implying_visual_approval():
    roles={'comparacao':'REVISAR_PARES_E_CRITERIO_COMUM','mecanismo':'REVISAR_ETAPAS_E_RELACOES_FUNDAMENTADAS',
           'consequencia':'REVISAR_CONSEQUENCIA_VISIVEL_SEM_INFERIR_CAUSA','acao':'REVISAR_ACAO_NOS_PIXELS_E_NO_TEMPO'}
    for role,state in roles.items():
        p={'shots':[{'id':'n','type':'video','start':0,'end':3,'asset':'m'}],
           'media':{'m':{}},'necessidades_direcao':[{'id':'n','fatos':['f'],'mostrar':'factual scope','papel_visual':role}]}
        d=diagnosticar(p)['direcao_explicativa'][0]
        assert d['estado']==state and d['fatos']==['f'] and d['mostrar']=='factual scope'
        assert not d['aprovacao_editorial'] and not d['autoriza_animacao']
