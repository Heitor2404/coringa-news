import pytest
from src.v4.formatos.dados_atribuidos_e342 import vincular
H='a'*64
def fixture():
    p={'preview':True,'private_review_only':True,'documentary_caption_origin':'PALAVRAS_MEDIDAS','shots':[{'id':'a','type':'video','asset':'film_editorial/'+H+'.mp4','start':10,'end':14,'source_in_seconds':2,'video_context_layout':'cena_integral','focus':[.5,.5]}]}
    q={'publish':False,'tasks':[{'shot':'a','speech':'TEN UNITS','sha256':H,'start':10,'end':14,'source_in':2}]}
    w=[{'w':'TEN','s':10.5,'e':11}]
    r=[{'shot':'a','speech':'TEN UNITS','sha256':H,'publish':False,'source_url':'https://example.org/report','authority':'Institute','source_statement':'ten units at location','source_date':'2020','value':'10 units','scope':'at location','anchor':'TEN'}]
    return p,q,w,r
def test_attributed_value_does_not_change_voice_or_claim_pixels():
    p,q,w,r=fixture();out,proof=vincular(p,q,w,r)
    s=out['shots'][0];assert s['documentary_reported_fact']['at']==.5 and s['documentary_integral_required']
    assert not proof[0]['measurement_from_pixels'] and not proof[0]['direct_evidence_verified']
    assert 'focus' not in s and 'documentary_reported_fact' not in p['shots'][0]
@pytest.mark.parametrize('fault',['speech','sha','anchor','source','private','window'])
def test_reject_mismatch(fault):
    p,q,w,r=fixture()
    if fault=='speech':r[0]['speech']='wrong'
    if fault=='sha':r[0]['sha256']='b'*64
    if fault=='anchor':w[0]['s']=13.9
    if fault=='source':r[0]['source_url']='not a url'
    if fault=='private':p['preview']=False
    if fault=='window':p['shots'][0]['source_in_seconds']=3
    with pytest.raises(ValueError):vincular(p,q,w,r)
