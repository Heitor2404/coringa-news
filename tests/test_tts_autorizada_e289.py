import hashlib,json,wave
import pytest
from src import voz,caixa
from src.v4 import orcamento_visao as O

def test_tts_rest_preserves_last_reservation_and_never_sends_unsupported_system(monkeypatch,tmp_path):
    arm=O.ArmazemLocal(tmp_path/'livro.json')
    monkeypatch.setenv('CORINGA_TTS_AUTORIZACAO','tts-e289-havai')
    monkeypatch.setenv('GEMINI_API_KEY','fake')
    monkeypatch.setenv('CORINGA_ORCAMENTO_TOKEN','fake')
    monkeypatch.setattr(O,'armazem_padrao',lambda _:arm)
    monkeypatch.setattr(caixa,'faturamento',lambda _: 'cota')
    O.abrir('tts-e289-havai',limite_logico=2,limite_operacoes=2,max_operacoes_por_chamada=1)
    t=O.reservar('tts-e289-havai','sintese-voz')
    O.liquidar('tts-e289-havai',t['id'],operacoes=1,ok=False,motivo='HTTP400')
    calls=[]
    def fake(modelo,pedido,voice,formato,sistema=None):
        calls.append((modelo,pedido,voice,formato,sistema))
        return b'\x01\x00'*24000
    monkeypatch.setattr(voz,'_rest_tts',fake)
    p=tmp_path/'gemini0.wav'
    voz._tts_autorizada('Somente roteiro','instrução recusada',p,'Charon')
    assert calls==[('gemini-3.8-flash-tts','Somente roteiro','Charon','antigo',None)]
    receipt=json.loads(p.with_suffix('.json').read_text())
    assert receipt['audio_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
    assert receipt['pedido_sha256']==hashlib.sha256(b'Somente roteiro').hexdigest()
    assert O.saldo('tts-e289-havai')['saldo_logico']==0
    with pytest.raises(O.SaldoEsgotado):
        voz._tts_autorizada('Somente roteiro',None,p,'Charon')
    assert len(calls)==1

def test_invalid_pcm_consumes_operation_and_never_produces_receipt(monkeypatch,tmp_path):
    arm=O.ArmazemLocal(tmp_path/'livro.json')
    monkeypatch.setenv('CORINGA_TTS_AUTORIZACAO','tts-test')
    monkeypatch.setenv('GEMINI_API_KEY','fake')
    monkeypatch.setenv('CORINGA_ORCAMENTO_TOKEN','fake')
    monkeypatch.setattr(O,'armazem_padrao',lambda _:arm)
    monkeypatch.setattr(caixa,'faturamento',lambda _: 'cota')
    monkeypatch.setattr(voz,'_rest_tts',lambda *a,**k:b'x')
    p=tmp_path/'gemini0.wav'
    with pytest.raises(ValueError,match='PCM'):
        voz._tts_autorizada('roteiro',None,p,'Charon')
    assert not p.exists() and not p.with_suffix('.json').exists()
    assert O.saldo('tts-test')['operacoes_consumidas']==1


def test_recover_exact_raw_voice_without_provider(monkeypatch,tmp_path):
    raw=tmp_path/'raw.wav'
    with wave.open(str(raw),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(b'\x01\x00'*24000)
    pedido='Somente roteiro'
    r={'publicar':False,'modelo':'gemini-3.8-flash-tts','voz':'Charon','estilo_externo':False,
       'pedido_sha256':hashlib.sha256(pedido.encode()).hexdigest(),'audio_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()}
    raw.with_suffix('.json').write_text(json.dumps(r))
    dst=tmp_path/'restaurada.wav'
    assert voz.recuperar_gravacao_gemini(raw,dst,pedido,'Charon')==dst
    assert dst.read_bytes()==raw.read_bytes()
    for text,voice in [('outro roteiro','Charon'),(pedido,'Kore')]:
        with pytest.raises(ValueError,match='VINCULO'):
            voz.recuperar_gravacao_gemini(raw,dst,text,voice)
    raw.write_bytes(raw.read_bytes()+b'x')
    with pytest.raises(ValueError,match='VINCULO'):
        voz.recuperar_gravacao_gemini(raw,dst,pedido,'Charon')
