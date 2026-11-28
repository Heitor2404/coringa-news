import pytest
from src.v4.formatos.auditoria_fala_visual_e338 import organizar
def fixture():
    h='a'*64
    p={'publicar':False,'duracao':7,'media':{'a':{'expected_sha256':h,'width':1920,'height':1080}},
       'shots':[{'id':'s','type':'video','asset':'a','start':0,'end':3,'source_in_seconds':7},
                {'id':'t','type':'video','asset':'a','start':3,'end':6,'source_in_seconds':12},
                {'id':'m','type':'atlas_map','start':6,'end':7}]}
    r={'shot':'s','chapter':'A','start':0,'end':3,'speech':'FALA EXATA','source':'a','source_sha256':h,'source_in':7,'source_out':10,'status':'REVISAR_EVIDENCIA_POR_FALA','direct_evidence_verified':False}
    b={**r,'shot':'t','start':3,'end':6,'source_in':12,'source_out':15,'status':'AMOSTRAS_REVISADAS_PERTINENTES'}
    b['reviewed_binding']={k:b[k] for k in ('shot','chapter','speech','source')}
    b['reviewed_binding'].update(sha256=h,window_start=12,window_duration=3.8,observed='Context only',review_ref='private')
    return p,{'publish':False,'semantic_review':'PENDING','shots':[r,b]}
def test_queue_preserves_measured_speech_and_groups_source_without_merging_facts():
    p,o=fixture();x=organizar(p,o)
    assert x['unreviewed_shots']==x['sample_reviewed_shots']==1
    assert x['direct_verified_shots']==0 and not x['semantic_approval']
    assert x['source_batches'][0]['shots']==['s','t'] and x['tasks'][1]['adjacent_same_source']
    assert x['tasks'][1]['observed']=='Context only' and x['specialized_shots'][0]['shot']=='m'
@pytest.mark.parametrize('key,value',[('source_sha256','b'*64),('source_in',8),('end',4),('direct_evidence_verified',True)])
def test_bad_receipt_never_becomes_queue(key,value):
    p,o=fixture();o['shots'][0][key]=value
    with pytest.raises(ValueError):organizar(p,o)
def test_missing_or_repeated_obligation_is_not_silent():
    p,o=fixture();o['shots'].pop()
    with pytest.raises(ValueError):organizar(p,o)
    p,o=fixture();o['shots'].append(o['shots'][0])
    with pytest.raises(ValueError):organizar(p,o)
def test_binding_speech_must_match_actual_obligation():
    p,o=fixture();o['shots'][1]['reviewed_binding']['speech']='OTHER'
    with pytest.raises(ValueError):organizar(p,o)
