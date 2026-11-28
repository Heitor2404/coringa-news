import pytest
from src.v4.formatos.paineis_fonte_e346 import aplicar
H='a'*64
def fixture():
    shot={'id':'a','type':'photo','photo_framing':'integral','asset':'film_editorial/'+H+'.png','start':0,'end':4,'source_dimensions':[2128,2089]}
    props={'preview':True,'private_review_only':True,'documentary_caption_origin':'PALAVRAS_MEDIDAS','documentary_captions':[{'start':1,'end':2}],'shots':[shot],'duracao':4}
    task={'shot':'a','start':0,'end':4,'speech':'BEFORE COLLAPSE','sha256':H,'review_ref':'review-a','status':'AMOSTRAS_REVISADAS_PERTINENTES','observed':'observed source'}
    row={'publish':False,'shot':'a','donor':'a','speech':task['speech'],'sha256':H,'review_ref':'review-a','bbox':[0,0,.49,.448],'kind':'SCHEME','label':'ANTES DO COLAPSO','anchor':'BEFORE','observation':'Source panel contains the entire original heading and structure.'}
    return props,{'publish':False,'tasks':[task]},[{'w':'BEFORE','s':1.2}],{'publish':False,'status':'RENDERED_PRIVATE_INTEGRAL','changes':[]},[row]
def test_panel_focus_is_private_and_bounded():
    p,q,w,prior,r=fixture();out,proof=aplicar(p,q,w,prior,r)
    panel=out['shots'][0]['documentary_static_reveal']
    assert panel['panel_focus'] and panel['detail_gain']>=1.4 and panel['at']==1.2
    assert proof['total_frames']==120 and not proof['semantic_approval'] and not proof['changes'][0]['direct_evidence_verified']
    assert out['documentary_captions']==p['documentary_captions'] and 'documentary_static_reveal' not in p['shots'][0]
@pytest.mark.parametrize('fault',['bbox','source','anchor','gain','review','private','speech'])
def test_panel_rejects_bad_binding(fault):
    p,q,w,prior,r=fixture()
    if fault=='bbox':r[0]['bbox']=[0,0,1,1]
    if fault=='source':r[0]['sha256']='b'*64
    if fault=='anchor':w[0]['s']=.1
    if fault=='gain':r[0]['bbox']=[0,0,.95,.45]
    if fault=='review':r[0]['review_ref']='missing'
    if fault=='private':p['preview']=False
    if fault=='speech':r[0]['speech']='other'
    with pytest.raises(ValueError):aplicar(p,q,w,prior,r)
