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

def test_static_reveal_is_real_distinct_timed_information(monkeypatch,tmp_path):
    from src.v4.formatos import progressao_estatica_e322 as R,fiscal_progressao
    monkeypatch.chdir(tmp_path)
    p=Path('stage_documental/x.jpg');p.parent.mkdir();Image.new('RGB',(1600,900),'red').save(p)
    h=E.sha(p)
    m={'id':'x','label':'source','subject':'official record','local_source':str(p),'expected_sha256':h,
       'media_type':'photo','evidence_scope':'STATIC_ONLY','rights_status':'REVIEW_PENDING',
       'license':'Public domain','page':'https://www.usgs.gov/media/images/x','credit':'USGS','width':1600,'height':900}
    c={'shot':'s','source':'x','label':'source','sha256':h,'chapter':'A','speech':'AREA TOTAL','kind':'photo',
       'review_ref':'sheet','observed':'static evidence','lead':'AREA',
       'reveal':{'anchor_word':'TOTAL','label':'35,5 KM²','bbox':[.2,.3,.6,.7],'observation':'A fonte informa explicitamente o total da área observada.'}}
    words=[{'w':'AREA','s':0,'e':1.1},{'w':'TOTAL','s':1.1,'e':3.7}]
    shot=E.shot_for(c,m,words,'A',0,3.7)
    assert not fiscal_progressao.verificar([shot],{'x':m})
    assert R.validar(shot,m,h,private=True)['label']=='35,5 KM²'
    with pytest.raises(ValueError,match='VINCULO'):R.validar(shot,m,h,private=False)
    with pytest.raises(ValueError,match='MARCO'):R.validar({**shot,'lead':'35,5 KM²'},m,h,private=True)
    with pytest.raises(ValueError,match='CUE'):R.validar({**shot,'cues':[]},m,h,private=True)
    with pytest.raises(ValueError,match='REGIAO'):R.validar({**shot,'static_fact_reveal':{**shot['static_fact_reveal'],'bbox':[0,.3,.6,.7]}},m,h,private=True)

def test_e325_detail_gain_is_real_and_rejects_oversized_region():
    from src.v4.formatos import progressao_estatica_e322 as R
    h='a'*64
    m={'expected_sha256':h,'width':3300,'height':2550}
    p={'schema':'coringa.static.reveal.private.v1','publicar':False,'shot':'s','sha256':h,
       'review_ref':'review','at':1.5,'label':'35,5 KM²','bbox':[.58,.84,.76,.93],
       'observation':'O quadro de dados do mapa original comprova esta medida.','detail_zoom':True}
    s={'id':'s','type':'photo','photo_framing':'integral','start':0,'end':3.7,'lead':'AREA',
       'cues':[{'at':1.5,'label':p['label']}],'static_fact_reveal':p}
    out=R.validar(s,m,h,private=True)
    assert out['detail_zoom'] is True and out['detail_gain']>3
    with pytest.raises(ValueError,match='SEM-GANHO'):
        R.validar({**s,'static_fact_reveal':{**p,'bbox':[.1,.2,.9,.7]}},m,h,private=True)
    with pytest.raises(ValueError,match='FLAG'):
        R.validar({**s,'static_fact_reveal':{**p,'detail_zoom':False}},m,h,private=True)

def test_e326_full_data_box_has_gain_with_larger_overview():
    from src.v4.formatos import progressao_estatica_e322 as R
    h='a'*64
    m={'expected_sha256':h,'width':3300,'height':2550}
    p={'schema':'coringa.static.reveal.private.v1','publicar':False,'shot':'s','sha256':h,
       'review_ref':'review','at':1.5,'label':'35,5 KM²','bbox':[.58,.824,.766,.975],
       'observation':'O quadro original contém ambas as medidas e suas unidades.','detail_zoom':True}
    s={'id':'s','type':'photo','photo_framing':'integral','start':0,'end':3.7,'lead':'AREA',
       'cues':[{'at':1.5,'label':p['label']}],'static_fact_reveal':p}
    out=R.validar(s,m,h,private=True)
    assert out['detail_gain']>2 and out['overview_gain']>4
