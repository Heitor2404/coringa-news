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


def test_video_de_banco_de_outro_lugar_e_descartado_antes_da_visao():
    """execução 43972774128: vídeo do Pixabay 'sunset, canal, city' (outro país) foi aceito pela visão como eclusa do
    Panamá. Vídeo de banco só se identifica pelas tags: sem nome próprio do pedido, é outro lugar."""
    from src.v4 import acervo_v4 as A
    nomes = A.nomes_proprios(['Panama Canal locks video', 'Miraflores Locks ship', 'Gatun Locks ship transit'])
    assert nomes == {'panama', 'miraflores', 'gatun'}
    errado = {'url': 'https://cdn.pixabay.com/video/x.mp4', 'titulo': 'pixabay #230248: sunset, canal, city, light', 'video': {'url': 'x'}}
    certo = {'url': 'https://cdn.pixabay.com/video/y.mp4', 'titulo': 'pixabay #1: panama, canal, ship, lock', 'video': {'url': 'y'}}
    assert not A.mesmo_lugar(errado, nomes) and A.mesmo_lugar(certo, nomes)
    esc, info = A.escolher([errado], 'navio na eclusa', set(), ['Panama Canal locks video'])
    assert esc is None and 'outro lugar' in info['motivo']


def test_roi_em_pixels_e_descartada():
    from src.v4.acervo_v4 import _roi_valida
    assert _roi_valida([428, 523, 132, 30]) is None
    assert _roi_valida([.1, .2, .5, .6]) == [.1, .2, .5, .6]
    assert _roi_valida(None) is None


def test_pico_do_aac_e_corrigido_sem_baixar_a_loudness(monkeypatch, tmp_path):
    """execução 43972774128: master −1,4 dBTP, MP4 −0,1 dBTP (o AAC sobe o pico). O MP4 é medido e o limitador age só
    nos picos, com teto que desconta o excesso do AAC."""
    from src.v4 import compositor as C
    cmds = []
    monkeypatch.setattr(C, 'rodar', lambda cmd, **k: cmds.append([str(x) for x in cmd]) or (tmp_path / 'final_pico.mp4').write_bytes(b'x'))
    mp4, wav = tmp_path / 'v.mp4', tmp_path / 'm.wav'
    mp4.write_bytes(b'x')
    medidas = {str(mp4): [{'pico': -0.1, 'lufs': -14.6}, {'pico': -2.4, 'lufs': -14.6}], str(wav): [{'pico': -1.4}]}
    r = C.corrigir_pico_aac(mp4, wav, tmp_path, medir=lambda p: medidas[str(p)].pop(0))
    assert r['corrigido'] and r['teto_limitador_db'] == -2.6 and r['pico_depois'] <= -1 and r['lufs_depois'] == -14.6
    assert 'volume=' not in ' '.join(cmds[0]) and 'alimiter' in ' '.join(cmds[0]) and '-c:v' in cmds[0] and 'copy' in cmds[0]
    assert C.corrigir_pico_aac(mp4, wav, tmp_path, medir=lambda p: {'pico': -1.5})['corrigido'] is False


def test_revideo_registra_o_chrome_e_tenta_flags_minimas():
    """execução 43972774128: 'Target closed' na partida, sem o motivo no log. NÃO VERIFICADO NO RUNNER: este teste só
    garante que o motivo passa a aparecer (dumpio) e que há segunda tentativa; o render real depende da próxima execução."""
    import subprocess
    src = (Path(__file__).resolve().parents[1] / 'motor4' / 'revideo' / 'render.mjs')
    t = src.read_text()
    assert 'dumpio: true' in t and t.count('executablePath') >= 3 and "'--disable-dev-shm-usage'" in t
    assert subprocess.run(['node', '--check', str(src)]).returncode == 0


def test_demonstracao_exige_render_e_revisao_semantica():
    """execução 43972774128: c6 (backend falhou, quadro preto) e c5 (vídeo de outro lugar) contavam como 'demonstra'
    só pela modalidade declarada."""
    from src.v4 import metricas as M
    m = {'por_cena': [{'cena': 'c5', 'demonstra_acao': True}, {'cena': 'c6', 'demonstra_acao': False},
                      {'cena': 'c8', 'demonstra_acao': True}, {'cena': 'c9', 'demonstra_acao': True}], 'resumo': {}}
    rev = {'planos': [{'evento_id': 'c5', 'veredito': {'demonstra': 'nao'}}, {'evento_id': 'c6', 'veredito': {'demonstra': 'nao'}},
                      {'evento_id': 'c8', 'veredito': {'demonstra': 'sim'}}, {'evento_id': 'c9', 'veredito': {'_nao_revisado': 'erro'}}]}
    r = M.combinar_revisao(m, rev)
    assert [c['demonstra_acao'] for c in r['por_cena']] == [False, False, True, False]
    assert r['resumo']['pct_cenas_que_demonstram'] == 25.0 and r['resumo']['cenas_demonstracao_pendente'] == ['c9']
