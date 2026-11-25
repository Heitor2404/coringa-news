from pathlib import Path

def test_documentary_media_no_blurred_duplicate_and_adapts_source_aspect():
    p=Path('motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text()
    assert 'defocused-non-evidence' not in p
    assert 'w/h<=1.15?[0,0,1080,1920]:w/h>=1080/610?[0,405,1080,1015]:[0,405,1080,1135]' in p
    assert 'rectStyle(integralMediaRect(shot))' in p
    assert "role==='source'?[30,24]" in p
    assert "getBoundingClientRect()" in p and "OVERFLOW_REVIEW" in p
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

def test_e290_documentary_text_slots_are_distinct_and_within_existing_safe_zone():
    import json,re
    code=Path('motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text()
    cfg=json.loads(Path('motor4/remotion/src/formatos/safe-zones-vertical.json').read_text())
    decl=next(x for x in code.splitlines() if x.startswith('const DOC_MEDIA='))
    boxes=[cfg['slots']['brand']]
    for role in ('section','subtitle','source'):
        m=re.search(role+r':\[([0-9,]+)\]',decl)
        assert m,role
        boxes.append([int(x) for x in m.group(1).split(',')])
    uni=cfg['universal']
    for x,y,r,b in boxes:
        assert uni[0]<=x<r<=uni[2] and uni[1]<=y<b<=uni[3]
    assert all(a[3]<=b[1] for a,b in zip(boxes,boxes[1:]))
    assert boxes[1][3]<=405 and 1015<boxes[2][1]
    # E290 failed for a 116px measured four-line credit. Preserve all authors,
    # the readable 24px floor, and full-width 16:9 pixels.
    assert boxes[3][3]-boxes[3][1]>=116
    assert 1015-405>=1080*9/16
    assert "width:'fit-content',maxWidth:'100%'" in code
    assert 'documentaryPixelRect' in code and 'documentaryOverlay' in code
    assert 'documentaryProtected' in code and 'INTEGRAL_PROTECTED' in code
    assert 'evidenceCollision' in code and 'actualOverlay' in code
    assert "documentary_text_probe&&(!preview||!private_review_only)" in code
    assert "overflowWrap:'anywhere'" in code
