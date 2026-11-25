from pathlib import Path

def test_documentary_media_no_blurred_duplicate_and_adapts_source_aspect():
    p=Path('motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text()
    assert 'defocused-non-evidence' not in p
    assert 'w/h<=1.15?[0,0,1080,1920]:[0,400,1080,1030]' in p
    assert 'rectStyle(integralMediaRect(shot))' in p
    assert "fontSize:18,lineHeight:1.12,fontWeight:450" in p
    assert "justifyContent:'center',textAlign:'center'" in p
    assert "objectFit:'contain'" in p
