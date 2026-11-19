"""Prova que somente preview privado, com QA válido, chega ao Telegram."""
import json
from types import SimpleNamespace
from pathlib import Path
import pytest
from src.v3 import previa_telegram
from scripts import qa_mapas_r2_telegram as T

def fixture(tmp_path:Path):
    (tmp_path/"mapas_narrados_r2.mp4").write_bytes(b"x"*150000)
    (tmp_path/"contato_editorial.jpg").write_bytes(b"y"*16000)
    (tmp_path/"qa_montagem.json").write_text(json.dumps({
        "status_tecnico":"PRONTO_PARA_REVISAO","problemas_tecnicos":[],
        "publicavel":False,"aprovacao_humana":"PENDENTE","tem_audio":True}))
    (tmp_path/"plano_sincronizado.json").write_text(json.dumps({
        "shots":[{"type":"map"}]*3,"sincronia_voz":{"tempo_audio":1.0}}))
    return tmp_path

def mock_telegram(monkeypatch):
    chamadas=[]
    monkeypatch.setattr(previa_telegram,"chat_autorizado",
                        lambda:("-12345",{"tipo":"group","membros":3}))
    monkeypatch.setattr(previa_telegram,"_caber",lambda p:p)
    def api(m,d,arquivo=None):
        chamadas.append((m,d,arquivo))
        return {"message_id":100+len(chamadas)}
    monkeypatch.setattr(previa_telegram,"_api",api)
    monkeypatch.setattr(T.subprocess,"run",lambda *a,**kw:
         SimpleNamespace(returncode=0,stdout=json.dumps({
           "streams":[{"codec_type":"audio"},{"codec_type":"video"}],
           "format":{"duration":"10.467"}})))
    return chamadas

def test_mp4_e_folha_privados_com_confirmacao_de_message_id(tmp_path,monkeypatch):
    pasta=fixture(tmp_path)
    calls=mock_telegram(monkeypatch)
    o=T.entregar(pasta)
    assert o['enviado'] and not o['publicado']
    assert o['destino']=='group privado autorizado'
    assert o['video_message_id']==101
    assert [c[0] for c in calls]==["sendVideo","sendPhoto","sendMessage"]
    assert all(c[1]['chat_id']=="-12345" for c in calls)
    assert 'NÃO PUBLICADO' in calls[0][1]['caption']

def test_qa_bloqueado_nao_envia_mp4(tmp_path,monkeypatch):
    pasta=fixture(tmp_path)
    p=pasta/"qa_montagem.json"
    a=json.loads(p.read_text());a['status_tecnico']="BLOQUEADO"
    p.write_text(json.dumps(a))
    calls=mock_telegram(monkeypatch)
    with pytest.raises(RuntimeError,match="QA técnico"):
        T.entregar(pasta)
    assert [x[0] for x in calls]==["sendMessage"]

def test_destino_publico_ou_indisponivel_recusa_sem_enviar(tmp_path,monkeypatch):
    pasta=fixture(tmp_path)
    calls=mock_telegram(monkeypatch)
    def fail():
        raise previa_telegram.EnvioRecusado("chat não é privado")
    monkeypatch.setattr(previa_telegram,'chat_autorizado',fail)
    with pytest.raises(previa_telegram.EnvioRecusado):
        T.entregar(pasta)
    assert calls==[]

def test_video_sem_audio_nao_envia(tmp_path,monkeypatch):
    pasta=fixture(tmp_path)
    calls=mock_telegram(monkeypatch)
    monkeypatch.setattr(T.subprocess,'run',lambda *a,**kw:
       SimpleNamespace(returncode=0,stdout=json.dumps({
         "streams":[{"codec_type":"video"}],"format":{"duration":"10.467"}})))
    with pytest.raises(RuntimeError,match="vídeo/áudio"):
        T.entregar(pasta)
    assert [x[0] for x in calls]==["sendMessage"]
