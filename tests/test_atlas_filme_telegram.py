"""Contrato de envio privado sem acesso a Telegram real."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from scripts import atlas_filme_telegram as envio


def _preparar(tmp_path):
    d = tmp_path / "saida"
    d.mkdir()
    (d / "qa_causal.json").write_text(json.dumps({
        "status": "AGUARDANDO_REVISAO_HUMANA",
        "duracao": "7.800000",
        "sem_tts": True,
        "nao_publicado": True,
        "frames_sha256": {"0.2": "0" * 64}
    }), encoding="utf-8")
    (d / "prova_causal_8s.mp4").write_bytes(b"x" * 55000)
    (d / "contato_causal_8s.jpg").write_bytes(b"y" * 15000)
    # Fixture sem animação: vincula props e MP4 apenas para testar transporte.
    (d / 'props.json').write_text(json.dumps({'preview':True,'shots':[{'id':'m','type':'photo'}]}))
    qa=json.loads((d/'qa_causal.json').read_text())
    qa.update(props_sha256=hashlib.sha256((d/'props.json').read_bytes()).hexdigest(),
              video_sha256=hashlib.sha256((d/'prova_causal_8s.mp4').read_bytes()).hexdigest())
    (d/'qa_causal.json').write_text(json.dumps(qa))
    return d


def _mock(monkeypatch):
    eventos = []
    monkeypatch.setattr(envio.previa_telegram, "chat_autorizado",
                        lambda: ("CHAT_AUTORIZADO", {"tipo": "private"}))
    monkeypatch.setattr(envio.previa_telegram, "_api",
                        lambda metodo, dados, arquivo=None:
                        eventos.append((metodo, dados, arquivo)))
    monkeypatch.setattr(envio.previa_telegram, "_caber", lambda p: p)
    return eventos


def test_envia_video_e_contato_somente_no_chat_validado(tmp_path, monkeypatch):
    d = _preparar(tmp_path)
    enviados = _mock(monkeypatch)
    result = envio.entregar(d)
    assert result["enviado"] is True and result["publicado"] is False
    assert [m for m, *_ in enviados] == ["sendVideo", "sendPhoto", "sendMessage"]
    assert all(dados["chat_id"] == "CHAT_AUTORIZADO" for _, dados, _ in enviados)
    assert "SEM NARRAÇÃO" in enviados[0][1]["caption"]
    assert "NÃO PUBLICADO" in enviados[0][1]["caption"]
    assert enviados[0][2][1] == d / "prova_causal_8s.mp4"


def test_falta_qa_impede_envio_de_video_e_avisa_bloqueio(tmp_path, monkeypatch):
    d = _preparar(tmp_path)
    (d / "qa_causal.json").unlink()
    enviados = _mock(monkeypatch)
    with pytest.raises(RuntimeError, match="bloqueada"):
        envio.entregar(d)
    assert [m for m, *_ in enviados] == ["sendMessage"]
    assert "BLOQUEADA" in enviados[0][1]["text"]


def test_status_aprovado_automaticamente_nao_aceito(tmp_path, monkeypatch):
    d = _preparar(tmp_path)
    qa = json.loads((d / "qa_causal.json").read_text())
    qa["status"] = "APROVADO_HUMANO"
    (d / "qa_causal.json").write_text(json.dumps(qa))
    enviados = _mock(monkeypatch)
    with pytest.raises(RuntimeError):
        envio.entregar(d)
    assert "sendVideo" not in [m for m, *_ in enviados]


def test_nao_envia_quando_publicacao_privada_nao_comprovada(tmp_path, monkeypatch):
    d = _preparar(tmp_path)
    qa = json.loads((d / "qa_causal.json").read_text())
    qa["nao_publicado"] = False
    (d / "qa_causal.json").write_text(json.dumps(qa))
    enviados = _mock(monkeypatch)
    with pytest.raises(RuntimeError):
        envio.entregar(d)
    assert "sendVideo" not in [m for m, *_ in enviados]


def test_legado_e_artefato_sem_vinculo_nao_sao_entregues(tmp_path,monkeypatch):
    d=_preparar(tmp_path)
    eventos=_mock(monkeypatch)
    p=d/'props.json'
    p.write_text(json.dumps({'preview':True,'private_review_only':True,
        'animation_policy_mode':'LEGADO_REJEITADO_SOMENTE_QA',
        'shots':[{'id':'a','type':'mechanism','mechanism':'lock_filling'}]}))
    qa=json.loads((d/'qa_causal.json').read_text())
    qa['props_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    (d/'qa_causal.json').write_text(json.dumps(qa))
    with pytest.raises(RuntimeError,match='bloqueada'):
        envio.entregar(d)
    assert [e[0] for e in eventos]==['sendMessage']
    p.unlink()
    with pytest.raises(RuntimeError,match='bloqueada'):
        envio.entregar(d)
    assert all(e[0]=='sendMessage' for e in eventos)
