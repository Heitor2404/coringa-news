from pathlib import Path

def test_documentary_media_no_blurred_duplicate_and_adapts_source_aspect():
    p=Path('motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text()
    assert 'defocused-non-evidence' not in p
    assert 'w/h<=1.15?[0,0,1080,1920]:[0,300,1080,1030]' in p
    assert 'rectStyle(integralMediaRect(shot))' in p
    assert "fontSize:18,lineHeight:1.12,fontWeight:450" in p
    assert "justifyContent:'center',textAlign:'center'" in p
    assert "objectFit:'contain'" in p

def test_photo_crop_uses_observed_region_not_theme_or_blind_center():
    from src.v4.formatos.filme_editorial import propor_recorte_foto
    sha='a'*64
    m={'expected_sha256':sha}
    r={'sha256':sha,'revisao_id':'review-1','escala_origem':'xy_0_1000','bbox':[.37,.32,.55,.50]}
    crop=propor_recorte_foto({'photo_roi_candidate':r},m,(1920,1080))
    assert crop and crop['height'] in (1080,1350) and crop['status']=='PRIVATE_CANDIDATE_REVIEW_PENDING'
    for bad in ({**r,'sha256':'b'*64},{**r,'escala_origem':'legado_xy_0_1000'},{**r,'bbox':[.05,.05,.95,.95]},{**r,'bbox':[.5,.5,.4,.9]}):
        assert propor_recorte_foto({'photo_roi_candidate':bad},m,(1920,1080)) is None
    assert propor_recorte_foto({},m,(1920,1080)) is None
