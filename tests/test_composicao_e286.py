from pathlib import Path

def test_documentary_media_no_blurred_duplicate_and_adapts_source_aspect():
    p=Path('motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text()
    assert 'defocused-non-evidence' not in p
    assert 'w/h<=1.15?[0,0,1080,1920]:w/h>=1080/610?[0,405,1080,1015]:[0,405,1080,1135]' in p
    assert 'rectStyle(integralMediaRect(shot))' in p
    assert "role==='source'?[30,24]" in p
    assert "getBoundingClientRect()" in p and "OVERFLOW_REVIEW" in p
    # E298: legacy remains centered; authenticated private ATLAS aligns left.
    assert "documentary_atlas_layout&&preview&&private_review_only?'flex-start':'center'" in p
    assert "documentary_atlas_layout&&preview&&private_review_only?'left':'center'" in p
    assert "objectFit:'contain'" in p

def test_photo_crop_uses_observed_region_not_theme_or_blind_center():
    from src.v4.formatos.filme_editorial import propor_recorte_foto
    sha='a'*64
    m={'expected_sha256':sha}
    r={'sha256':sha,'revisao_id':'review-1','escala_origem':'xy_0_1000','bbox':[.37,.32,.55,.50]}
    crop=propor_recorte_foto({'photo_roi_candidate':r},m,(1920,1080))
    assert crop and crop['height'] in (1080,1350,1920) and crop['status']=='PRIVATE_CANDIDATE_REVIEW_PENDING'
    for bad in ({**r,'sha256':'b'*64},{**r,'escala_origem':'legado_xy_0_1000'},{**r,'bbox':[.05,.05,.95,.95]},{**r,'bbox':[.5,.5,.4,.9]}):
        assert propor_recorte_foto({'photo_roi_candidate':bad},m,(1920,1080)) is None
    assert propor_recorte_foto({},m,(1920,1080)) is None

def test_e290_documentary_text_slots_are_distinct_and_within_existing_safe_zone():
    import json,re
    code=Path('motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text()
    cfg=json.loads(Path('motor4/remotion/src/formatos/safe-zones-vertical.json').read_text())
    decl=next(x for x in code.splitlines() if x.startswith('const DOC_MEDIA='))
    boxes=[]
    for role in ('brand','section','subtitle','source'):
        m=re.search(role+r':\[([0-9,]+)\]',decl)
        assert m,role
        boxes.append([int(x) for x in m.group(1).split(',')])
    # Private E295 candidate: no relaxation of the canonical safe profile.
    assert cfg['universal']==[150,300,770,1240]
    for x,y,r,b in boxes:
        assert x==120 and x<r<=760 and 300<=y<b<=1608
    assert all(a[3]<=b[1] for a,b in zip(boxes,boxes[1:]))
    assert boxes[1][3]<480 and 1380<boxes[2][1]
    # E290 failed for a 116px measured four-line credit. Preserve all authors,
    # the readable 24px floor, and full-width 16:9 pixels.
    assert boxes[3][3]-boxes[3][1]>=116
    assert 1015-405>=1080*9/16
    assert "width:'fit-content',maxWidth:'100%'" in code
    assert 'documentaryPixelRect' in code and 'documentaryOverlay' in code
    assert 'documentaryProtected' in code and 'INTEGRAL_PROTECTED' in code
    assert 'evidenceCollision' in code and 'actualOverlay' in code
    assert 'PORTRAIT_REVIEW' in code and 'UNKNOWN_REVIEW' in code
    assert 'if(nativePortrait(shot)&&!observed)' in code
    assert 'data-media-layout="native-portrait-full"' in code
    assert 'containPixels([0,0,W,H],shot.source_dimensions!)' in code
    assert 'const stage=[0,480,1080,1380]' in code
    assert 'shot.documentary_integral_required' in code
    assert "if(shot.documentary_roi_points?.length||shot.framing_positions?.length)return full;" in code
    assert 'CENTERED_CROP_REVIEW' in code and 'CENTERED_CROP_OBSERVED' in code
    assert 'const centered=centeredLandscape(shot)' in code
    assert "documentary_text_probe&&(!preview||!private_review_only)" in code
    assert "overflowWrap:'anywhere'" in code


def test_e293_signature_is_decoration_behind_real_media_only():
    root=Path('motor4/remotion/src/formatos')
    code=(root/'FilmeEditorial.tsx').read_text()
    bg=(root/'SignatureBackground.tsx').read_text()
    assert 'SIGNATURE_B_V1' in bg and 'aria-hidden="true"' in bg
    # E293.1: source-string assertions alone missed the import inside the opening comment.
    import re
    uncommented=re.sub(r'/\*.*?\*/','',code,flags=re.S)
    assert re.search(r"^import \{SignatureBackground,signatureHasVisibleArea\} from '\./SignatureBackground';$",uncommented,re.M)
    assert 'signatureHasVisibleArea(layout.media)&&<SignatureBackground/>' in code
    segment=code.split('if(mediaFirst&&realMedia(shot)) {',1)[1]
    assert segment.index('<SignatureBackground/>') < segment.index('<Body shot={shot}')
    assert 'staticFile' not in bg and 'Math.random' not in bg and 'filter:' not in bg
