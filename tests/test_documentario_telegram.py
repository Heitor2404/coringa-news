import hashlib,json
import pytest
from scripts import documentario_telegram as D

def fixture(tmp_path):
    v=tmp_path/'filme.mp4';v.write_bytes(b'fixture only')
    p=tmp_path/'props.json';p.write_text(json.dumps({'private_review_only':True,'preview':True,'duracao':75,'shots':[{'id':'x','type':'video'}]}))
    q={'publish':False,'visual_approval':'PENDING','voice_approval':'PENDING','duration':75,
       'props_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'video_sha256':hashlib.sha256(v.read_bytes()).hexdigest()}
    (tmp_path/'qa.json').write_text(json.dumps(q))
    return v

def test_private_delivery_mock(tmp_path,monkeypatch):
    v=fixture(tmp_path)
    monkeypatch.setattr(D,'verificar_video',lambda *a:None)
    monkeypatch.setattr(D.T,'chat_autorizado',lambda:('123',{'tipo':'private'}))
    monkeypatch.setattr(D.T,'_caber',lambda p:p)
    calls=[]
    def api(*args):
        calls.append(args);return {'message_id':1}
    monkeypatch.setattr(D.T,'_api',api)
    assert D.entregar(tmp_path,'teste')['enviado']
    assert len(calls)==1 and calls[0][0]=='sendVideo' and calls[0][2]==('video',v)

def test_tampered_video_never_calls_bot(tmp_path,monkeypatch):
    v=fixture(tmp_path);v.write_bytes(b'altered')
    monkeypatch.setattr(D.T,'chat_autorizado',lambda:pytest.fail('bot called before validation'))
    with pytest.raises(ValueError,match='HASH'):D.entregar(tmp_path,'teste')

def test_private_flag_required(tmp_path):
    fixture(tmp_path)
    p=tmp_path/'props.json';d=json.loads(p.read_text());d['private_review_only']=False;p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='PRIVADO'):D.validar(tmp_path)

def test_bot_failure_redacted(tmp_path,monkeypatch):
    fixture(tmp_path)
    monkeypatch.setattr(D,'verificar_video',lambda *a:None)
    def fail():raise RuntimeError('secret-value')
    monkeypatch.setattr(D.T,'chat_autorizado',fail)
    with pytest.raises(RuntimeError,match='E223-TELEGRAM') as exc:D.entregar(tmp_path,'teste')
    assert 'secret-value' not in str(exc.value)
