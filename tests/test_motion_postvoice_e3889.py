import copy,hashlib
from src.v4.formatos.motion_postvoice_e3889 import preparar_alternativa,measured_anchor
from src.v4.formatos.motion_intake_e3888 import integrar
import json
from pathlib import Path
E342=json.loads(Path('benchmarks/e342/dados.json').read_text())['entries']
def sample():
    r=E342[0]
    f={'id':'f','fonte':r['source_url'],'quantitative_review':{'schema':'coringa.fact.quantity.review.private.v1','publish':False,'reviewed':True,'fact_id':'f','relevance':'central','source_url':r['source_url'],'source_sha256':r['sha256'],'source_date':r['source_date'],'statement':r['source_statement'],'review_id':'benchmarks/e342/dados.json#c3-2','measurement':{'kind':'range','title':'VELOCIDADE DA LAVA','scope':r['scope'],'unit':'km/h','qualifier':'approx','values':[{'label':'mínimo','value':21},{'label':'máximo','value':26}]}}}
    n={'id':'n','fatos':['f'],'necessidade':'explicacao_quantitativa','papel_visual':'quantificacao','exigir_evidencia_direta':False,'evidencia_visual':'estatica','mostrar':'explicar magnitude'}
    plan={'publicar':False,'shots':[{'id':'n','start':0,'end':4,'type':'video'}],'necessidades_direcao':[{'id':'n','fatos':['f'],'mostrar':'explicar magnitude','papel_visual':'quantificacao','evidencia_visual':'estatica'}]}
    return {'fatos':[f],'necessidades':[n]},plan



def fixture(tmp):
    # Explicit synthetic bytes and timing for contract testing, not media proof.
    def asset(folder,ext,data):
        h=hashlib.sha256(data).hexdigest();p=tmp/folder/(h+ext);p.parent.mkdir(exist_ok=True);p.write_bytes(data)
        return str(p.relative_to(tmp)),h
    v,h=asset('film_editorial','.mp4',b'synthetic contextual fixture')
    audio,_=asset('e202','.wav',b'synthetic measured timing fixture')
    c,p=sample();c['motion_private_alternatives']=True
    r=c['fatos'][0]['quantitative_review'];r.update(source_sha256=h,review_id='SYNTHETIC_CONTRACT_ONLY',anchor_phrase=['VINTE','QUILOMETROS'],anchor_word_index=0)
    p['shots'][0].update(evidence='representative')
    p=integrar(c,p)
    s={**p['shots'][0],'asset':v,'source_display':'Fixture','source_in_seconds':0}
    words=[{'w':'VINTE','s':.7,'e':.9},{'w':'QUILOMETROS','s':.9,'e':1.2}]
    props={'preview':True,'private_review_only':True,'documentary_media_preview':True,'documentary_caption_origin':'PALAVRAS_MEDIDAS','scene_narration_asset':audio,'duracao':4,'shots':[s],'documentary_captions':[{'start':.7,'end':1.2,'words':[{'w':'VINTE'},{'w':'QUILOMETROS'}]}]}
    return c,p,props,words

def test_measured_private_alternative_keeps_canonical(tmp_path):
    c,p,props,w=fixture(tmp_path);before=copy.deepcopy(props)
    alt,report=preparar_alternativa(c,p,props,w,{'ok':True},tmp_path)
    assert props==before and alt['documentary_captions']==before['documentary_captions'] and alt['scene_narration_asset']==before['scene_narration_asset']
    s=alt['shots'][0];assert s['documentary_chart_trial']['shape']=='interval' and s['documentary_chart_anchor']['at']==.7
    assert s['documentary_chart_context']['asset']==before['shots'][0]['asset']
    assert report['render_authorized'] is False and report['semantic_review_reperformed'] is False
def test_no_audio_sync_or_permission_no_alternative(tmp_path):
    c,p,props,w=fixture(tmp_path)
    assert preparar_alternativa(c,p,props,w,{'ok':False},tmp_path)[0] is None
    c['motion_private_alternatives']=False
    assert preparar_alternativa(c,p,props,w,{'ok':True},tmp_path)[0] is None
def test_protected_literal_or_existing_lane(tmp_path):
    c,p,props,w=fixture(tmp_path)
    props['shots'][0]['evidence']='literal'
    assert preparar_alternativa(c,p,props,w,{'ok':True},tmp_path)[0] is None
    props['shots'][0].update(evidence='representative',documentary_reported_fact={})
    assert preparar_alternativa(c,p,props,w,{'ok':True},tmp_path)[0] is None
def test_source_changed_or_phrase_ambiguous(tmp_path):
    c,p,props,w=fixture(tmp_path)
    dup=w+[{'w':'VINTE','s':1.5,'e':1.7},{'w':'QUILOMETROS','s':1.7,'e':2}]
    assert preparar_alternativa(c,p,props,dup,{'ok':True},tmp_path)[0] is None
    (tmp_path/props['shots'][0]['asset']).write_bytes(b'changed')
    assert preparar_alternativa(c,p,props,w,{'ok':True},tmp_path)[0] is None
def test_timing_guard(tmp_path):
    c,p,props,w=fixture(tmp_path)
    w=[{'w':'VINTE','s':.1,'e':.2},{'w':'QUILOMETROS','s':.2,'e':.3}]
    assert preparar_alternativa(c,p,props,w,{'ok':True},tmp_path)[0] is None
