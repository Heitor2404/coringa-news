import pytest
from src.v4.formatos import politica_animacao as P, ponte_animacao_editorial as B

def test_real_media_has_priority(tmp_path):
    with pytest.raises(ValueError,match='SEM-NECESSIDADE'):
        B.preparar('x',tmp_path/'x',tmp_path,cid='a',acao='ação',lacuna='interior',motivo_lacuna='IMPOSSIVEL_FILMAR',midia_adequada=True)

def test_unregistered_or_wrong_hash(tmp_path):
    f=tmp_path/'x.mp4';f.write_bytes(b'not an animation')
    with pytest.raises(ValueError,match='E213-ORIGEM'):
        B.verificar('unknown',f)
    with pytest.raises(ValueError,match='E213-HASH'):
        B.verificar('render_eclusa_hidraulica_2d.py',f)

def test_candidate_metadata_does_not_allow_arbitrary_clip():
    s={'id':'x','type':'animation_clip','animation_proof':{'schema':B.SCHEMA},'asset':'anything.mp4'}
    assert not P.avaliar([s],privado=True)['permitido']

def test_no_retime_existing_audio(tmp_path):
    with pytest.raises(ValueError,match='RETIMAR-VOZ'):
        B.inserir({'preview':True,'scene_narration_asset':'existing.wav'}, {}, 0,tmp_path)
