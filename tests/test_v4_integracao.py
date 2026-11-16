"""Regressões da execução real 43956541084 (Canal do Panamá): causas gerais, não casos do vídeo."""
from pathlib import Path

from src.v4.acervo_v4 import _licenca
from src.v4.backends import js, rembg_camadas


def test_backends_recebem_caminhos_absolutos(monkeypatch, tmp_path):
    vistos = []
    monkeypatch.setattr(js, 'rodar', lambda cmd, **k: vistos.append([str(c) for c in cmd]) or {'rc': 0})
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'rel').mkdir()
    (tmp_path / 'rel' / 'x.mp4').write_bytes(b'0')
    js.remotion('Camada', {}, Path('rel/x.mp4'), Path('rel'))
    js.revideo({}, Path('rel/x.mp4'), Path('rel'))
    for cmd in vistos:
        caminhos = [a.split('=', 1)[-1] for a in cmd if 'rel' in a]
        assert caminhos and all(Path(c).is_absolute() for c in caminhos), cmd


def test_rembg_le_o_json_mesmo_com_aviso_do_onnxruntime_depois():
    log = '$ cmd\n\n{"cobertura": 0.07, "fragmentos": 2}\n[W:onnxruntime:Default] Skipping pci_bus_id …\n'
    assert rembg_camadas.medidas_do_log(log)['cobertura'] == .07


def test_licenca_vem_do_ultimo_parentese_do_credito():
    assert _licenca('Ship (1913) — Fulano (CC BY-SA 3.0), Wikimedia Commons') == 'CC BY-SA 3.0'
    assert _licenca('"x" — y (GFDL), via Wikimedia Commons') == 'GFDL'
    assert _licenca('sem licença') is None
    assert _licenca('Navio na eclusa (1913) — autor desconhecido') is None, 'ano não é licença'
    assert _licenca('Gatun (1912) — X (Public domain), via Wikimedia Commons') == 'Public domain'


def test_telegram_tenta_de_novo_em_falha_passageira_do_servidor(monkeypatch):
    """execução 43956541084: getChat 502 Bad Gateway e a prévia não foi entregue. 5xx tenta de novo; 4xx não."""
    from src.v3 import previa_telegram as PT
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'x')
    monkeypatch.setattr(PT.time, 'sleep', lambda s: None)
    respostas = iter([(502, {}), (200, {'ok': True, 'result': {'id': 1}})])

    class R:
        def __init__(self, c, j): self.status_code, self._j, self.ok, self.text = c, j, c == 200, str(j)
        def json(self): return self._j
    monkeypatch.setattr(PT.requests, 'post', lambda *a, **k: R(*next(respostas)))
    assert PT._api('getChat', {'chat_id': 1}) == {'id': 1}
    monkeypatch.setattr(PT.requests, 'post', lambda *a, **k: R(403, {'ok': False}))
    import pytest
    with pytest.raises(PT.EnvioRecusado):
        PT._api('getChat', {'chat_id': 1})
