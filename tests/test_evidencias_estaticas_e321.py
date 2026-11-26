import pytest
from pathlib import Path
from PIL import Image
from scripts import evidencias_estaticas_e321 as E

def test_static_binding_checks_actual_speech_source_and_duration(monkeypatch,tmp_path):
    monkeypatch.chdir(tmp_path)
    p=Path('stage_documental/x.jpg');p.parent.mkdir();Image.new('RGB',(800,600),'red').save(p)
    h=E.sha(p)
    m={'id':'x','label':'source','subject':'official record','local_source':str(p),'expected_sha256':h,
       'media_type':'photo','evidence_scope':'STATIC_ONLY','rights_status':'REVIEW_PENDING',
       'license':'Public domain','page':'https://www.usgs.gov/media/images/x','credit':'USGS','width':800,'height':600}
    c={'shot':'s','source':'x','label':'source','sha256':h,'chapter':'A','speech':'AREA','kind':'photo',
       'review_ref':'sheet','observed':'static evidence','lead':'35,5 KM²'}
    words=[{'w':'AREA','s':0,'e':2}]
    shot=E.shot_for(c,m,words,'A',0,2)
    assert shot['type']=='photo' and shot['photo_framing']=='integral' and shot['evidence']=='representative'
    assert 'video_framing' not in shot and 'source_in_seconds' not in shot
    with pytest.raises(ValueError,match='FALA'):E.shot_for({**c,'speech':'OTHER'},m,words,'A',0,2)
    with pytest.raises(ValueError,match='FALA'):E.shot_for(c,m,words,'A',0,4)
    with pytest.raises(ValueError,match='FONTE'):E.shot_for(c,{**m,'expected_sha256':'x'},words,'A',0,2)
