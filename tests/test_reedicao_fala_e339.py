import pytest
from src.v4.formatos.reedicao_fala_e339 import edit
H='a'*64;J='b'*64
def fixture():
    a={'id':'a','type':'video','asset':'film_editorial/'+H+'.mp4','start':0,'end':3,'source_in_seconds':5}
    b={'id':'b','type':'video','asset':'film_editorial/'+J+'.mp4','start':3,'end':7,'source_in_seconds':20,'documentary_integral_required':True,'video_framing':{'modo':'fonte_integral'},'documentary_static_reveal':{'label':'old scope'},'evidence':'literal'}
    p={'private_review_only':True,'preview':True,'documentary_caption_origin':'PALAVRAS_MEDIDAS','documentary_captions':[{'start':0,'end':3.2,'words':[{'w':'TESTE'}]}],'shots':[a,b]}
    q={'publish':False,'tasks':[{'shot':'a','start':0,'end':3,'speech':'target speech','sha256':H,'source_in':5,'source_out':8},{'shot':'b','start':3,'end':7,'speech':'different donor speech','sha256':J,'source_in':20,'source_out':24,'review_ref':'real ref','observed':'prior observation','status':'AMOSTRAS_REVISADAS_PERTINENTES'}]}
    return p,q
def test_preserve_measured_speech_and_reset_donor_approval():
    p,q=fixture();r,proof=edit(p,q,{'a':{'donor':'b','lead':'CONTEXT'}},3)
    s=r['shots'][0]
    assert s['source_in_seconds']==20 and s['end']==3 and s['evidence']=='representative'
    assert 'documentary_static_reveal' not in s and proof[0]['speech']=='target speech'
    assert proof[0]['status']=='NOVO_ESCOPO_PENDENTE' and not proof[0]['direct_evidence_verified']
    assert r['documentary_captions'][0]['end']==3 and p['documentary_captions'][0]['end']==3.2
    assert p['shots'][0]['asset'].endswith(H+'.mp4')
@pytest.mark.parametrize('fault',['sha','window','private','review','crop'])
def test_reject_unbound_donor(fault):
    p,q=fixture()
    if fault=='sha':q['tasks'][1]['sha256']=H
    if fault=='window':q['tasks'][1]['source_out']=22
    if fault=='private':p['preview']=False
    if fault=='review':q['tasks'][1]['review_ref']=None
    if fault=='crop':p['shots'][1]['documentary_integral_required']=False
    with pytest.raises(ValueError):edit(p,q,{'a':{'donor':'b','lead':'CONTEXT'}},3)
