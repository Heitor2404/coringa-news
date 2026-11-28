import copy,hashlib
import pytest
from scripts.qa_integral_e376 import bind_atlas,restore_exact_asset
def fixture(tmp_path):
    old='a'*64
    data=b'new rendered map'
    h=hashlib.sha256(data).hexdigest()
    public=tmp_path/'public';(public/'film_editorial').mkdir(parents=True)
    (public/'film_editorial'/f'{h}.mp4').write_bytes(data)
    shot=dict(id='mapa-1',type='atlas_map',start=2,end=7.5,headline='place',lead='where',atlas_direcao={'roi':[1,2,3,4]},direcao_evento={'fato_id':'location'},evidence='explainer',source='source',source_in_seconds=0,documentary_atlas_layout=True)
    p={'shots':[{**shot,'asset':f'film_editorial/{old}.mp4'}]}
    q={'shots':[{**shot,'asset':f'film_editorial/{h}.mp4'}]}
    r=dict(renderer='ATLAS/Formato/PalcoMapa/MapLibre',status='PRONTO_PARA_REVISAO_HUMANA',publicado=False,aprovacao_humana='PENDENTE',fps=30,quadro_alvo=[1080,1920],documentary_layout=True,duracao_s=5.5,quadros_decodificados=165,quadros_reais=[{'t':1}],mapeamento=dict(roi=[1,2,3,4],beat='local',palco='PalcoMapa',rasters_ativos=[{'sha256':'x'}],origem_geografica='geo'),atlas_sha256='a')
    a={**copy.deepcopy(r),'video_sha256':old,'video_bytes':99}
    b={**copy.deepcopy(r),'video_sha256':h,'video_bytes':len(data)}
    return p,q,a,b,public
def test_map_rebind_exact_receipt(tmp_path):
    p,q,a,b,public=fixture(tmp_path)
    result=bind_atlas(p,q,a,b,public)
    assert p==q and result['old_asset']!=result['new_asset'] and result['frames']==165
@pytest.mark.parametrize('failure',['geo','duration','identity','bytes','hash','credit','raster','count'])
def test_map_reject_mismatch(tmp_path,failure):
    p,q,a,b,public=fixture(tmp_path)
    if failure=='geo':b['mapeamento']['roi']=[4,3,2,1]
    elif failure=='duration':b['duracao_s']=4
    elif failure=='identity':q['shots'][0]['id']='another'
    elif failure=='bytes':(public/q['shots'][0]['asset']).write_bytes(b'corrupt')
    elif failure=='hash':b['video_sha256']='b'*64
    elif failure=='credit':q['shots'][0]['source']='other'
    elif failure=='raster':b['mapeamento']['rasters_ativos']=[{'sha256':'other'}]
    else:b['quadros_decodificados']=164
    with pytest.raises(ValueError,match='E379'):bind_atlas(p,q,a,b,public)
def test_restore_only_exact_local_bytes(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    stage=tmp_path/'stage_documental';stage.mkdir()
    src=stage/'x.mp4';src.write_bytes(b'original')
    h=hashlib.sha256(src.read_bytes()).hexdigest()
    public=tmp_path/'public';name=f'film_editorial/{h}.mp4'
    assert restore_exact_asset(name,[{'local_source':str(src),'expected_sha256':h}],public)
    assert not restore_exact_asset(name,[],public)
    (public/name).write_bytes(b'bad')
    with pytest.raises(ValueError,match='E376-SHA'):restore_exact_asset(name,[],public)
def test_no_fallback_for_wrong_source(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    stage=tmp_path/'stage_documental';stage.mkdir()
    src=stage/'x.mp4';src.write_bytes(b'wrong')
    h='a'*64
    with pytest.raises(ValueError,match='E379-SOURCE-SHA'):restore_exact_asset(f'film_editorial/{h}.mp4',[{'local_source':str(src),'expected_sha256':h}],tmp_path/'public')
