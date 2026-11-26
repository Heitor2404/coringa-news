from src.v4.formatos import filme_editorial as F

def test_detail_requires_explicit_intent_bound_observation_and_actual_hash():
    h='a'*64
    m={'expected_sha256':h}
    shot={'type':'photo','documentary_detail_intent':True,'photo_roi_candidate':
          {'sha256':h,'revisao_id':'r','bbox':[.49,.37,.56,.52],'escala_origem':'xy_0_1'}}
    result=F.detalhe_fotografico(shot,m,h)
    assert result['bbox']==[.49,.37,.56,.52] and result['status']=='PRIVATE_DETAIL_REVIEW_PENDING'
    assert F.detalhe_fotografico(shot,m,'b'*64) is None
    assert F.detalhe_fotografico({**shot,'documentary_detail_intent':False},m,h) is None
    assert F.detalhe_fotografico({**shot,'type':'video'},m,h) is None
    assert F.detalhe_fotografico(shot,{**m,'original_graphic':True},h) is None
    for box in ([0,0,1,1],[.8,0,.1,.9],[False,0,.1,.9],[0,0,float('nan'),1]):
        assert F.detalhe_fotografico({**shot,'photo_roi_candidate':{**shot['photo_roi_candidate'],'bbox':box}},m,h) is None
