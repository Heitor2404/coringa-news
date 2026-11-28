import json
from src.v4.formatos.direcao_short_e306 import diagnosticar
from scripts.qa_documentario_integral_e254 import gate_direcao_short

def film(kind='photo'):
    return {'media':{'m':{'width':1920,'height':1080}},'shots':[
        {'id':str(i),'type':kind,'asset':'m','start':i*3.5,'end':(i+1)*3.5,
         'cues':[{'at':1,'label':'TITLE'}],'video_zoom':1.4} for i in range(18)]}

def test_slideshow_is_not_approved_by_camera_or_text_and_stops_before_tts(tmp_path):
    p=film();r=diagnosticar(p)
    assert r['status']=='REPLANEJAR' and r['passive_photo_s']==63
    assert r['longest_passive_s']==63 and r['shots'][0]['integral_canvas_fraction']==.3164
    (tmp_path/'props.json').write_text('{}')
    assert not gate_direcao_short(tmp_path,{'pronto_para_tts':True},p,phase='preflight')
    assert not (tmp_path/'props.json').exists()
    assert json.loads((tmp_path/'integral.json').read_text())['pronto_para_render_privado'] is False

def test_no_video_quota_and_no_automatic_approval():
    p=film();p['shots'][3]['type']='comparison'
    r=diagnosticar(p)
    assert r['pronto_para_analise_visual'] and not r['editorial_approval']
    assert 'SEQUENCIA_FOTOGRAFICA_LONGA_REVISAR' in r['issues']
    p=film('video');assert diagnosticar(p)['status']=='REVISAR'

def test_full_vertical_crop_candidate_is_grounded_and_not_a_passive_photo_exemption():
    from src.v4.formatos.filme_editorial import propor_recorte_foto
    h='a'*64;media={'width':1920,'height':1080,'expected_sha256':h}
    p=film();p['media']['m']=media
    p['shots'][0]['photo_roi_candidate']={'sha256':h,'revisao_id':'r','escala_origem':'xy_0_1','bbox':[.47,.44,.53,.49]}
    crop=propor_recorte_foto(p['shots'][0],media,(1920,1080))
    assert crop and crop['height']==1920
    r=diagnosticar(p);assert r['shots'][0]['observed_photo_crop_candidate'] and r['status']=='REPLANEJAR'
