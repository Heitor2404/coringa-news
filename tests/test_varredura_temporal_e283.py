"""E283 — varredura temporal local antes da visão externa (regressão da E281.2).

Falha original: num arquivo longo (Apollo 11, 496 s) as janelas eram uma grade uniforme com diversidade por terços e
ranking por diferença bruta de pixels; duas chamadas reais caíram em planos sem a ação pedida e a segunda rodada
insistiu no mesmo arquivo. Aqui um vídeo sintético reproduz o padrão genérico (nada específico de foguetes): planos
parados, panorâmica (movimento só da câmera), cortes, e a ação do referente concentrada num único plano tardio.
"""
from __future__ import annotations

import io
import shutil
import subprocess

import numpy as np
import pytest
from PIL import Image

from src.v4.formatos import amostragem_documental as A

pytestmark = pytest.mark.skipif(not shutil.which('ffmpeg'), reason='ffmpeg ausente')

W, H, FPS = 320, 180, 10


def _textura(seed, w, h):
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 255, (h // 24 + 2, w // 24 + 2), dtype=np.uint8)  # textura natural, não ruído branco
    im = Image.fromarray(base).resize((w, h), Image.BICUBIC)
    return np.asarray(im, dtype=np.uint8)


def _video(path):
    """0-20 s plano parado; 20-34 s panorâmica sobre cena estática; 34-46 s outro plano parado;
    46-54 s objeto sobe dentro de plano fixo (ação do referente); 54-60 s plano parado."""
    largo = _textura(1, W * 3, H)
    fixo_a, fixo_b, fixo_c = _textura(2, W, H), _textura(3, W, H), _textura(4, W, H)
    frames = []
    for i in range(60 * FPS):
        t = i / FPS
        if t < 20:
            f = fixo_a.copy()
        elif t < 34:
            x = int((t - 20) / 14 * (W * 2 - 1))
            f = largo[:, x:x + W].copy()
        elif t < 46:
            f = fixo_b.copy()
        elif t < 54:
            f = fixo_c.copy()
            y = int(H - 30 - (t - 46) / 8 * (H - 50))
            f[y:y + 26, 140:170] = 250
        else:
            f = fixo_a.copy()
        frames.append(np.dstack([f, f, f]))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-g', '20', str(path)],
                         stdin=subprocess.PIPE)
    p.communicate(np.stack(frames).tobytes())
    assert p.returncode == 0


def _frame(path, t, width):
    z = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', str(path), '-frames:v', '1',
                                 '-vf', f'scale={width}:-2', '-f', 'image2pipe', '-vcodec', 'png', 'pipe:1'])
    return Image.open(io.BytesIO(z)).convert('RGB')


@pytest.fixture(scope='module')
def video(tmp_path_factory):
    p = tmp_path_factory.mktemp('e283') / 'acao_tardia.mp4'
    _video(p)
    return p


def _midia(p, **extra):
    return {'expected_sha256': 'b' * 64, 'duration_s': 60.0, 'local_source': str(p), 'width': W, 'height': H, **extra}


def _need():
    return {'id': 'n', 'fatos': ['f'], 'mostrar': 'objeto subindo', 'evidencia_visual': 'movimento'}


def test_varredura_detecta_cortes_e_separa_camera_do_referente(video):
    v = A.varrer(video, 60.0, largura_origem=W, altura_origem=H)
    assert v and v['prova_semantica'] is False
    cuts = [q['t'] for q in v['pares'] if q['corte']]
    for esperado in (20, 34, 46, 54):
        assert any(abs(c - esperado) <= 1.0 for c in cuts), (esperado, cuts)
    pan = A._janela_movimento(v, 24, 3.8)
    acao = A._janela_movimento(v, 48, 3.8)
    parado = A._janela_movimento(v, 5, 3.8)
    assert pan['camera_dominante'] and not acao['camera_dominante']
    assert acao['referente'] > 3 * max(parado['referente'], 1e-4)
    assert parado['parado'] and not acao['parado']


def test_lote_de_movimento_alcanca_a_acao_tardia_em_plano_proprio(video):
    exp, windows = A.preparar_lote(_midia(video), _need(), _frame)
    starts = [p['inicio_s'] for p, _ in windows]
    assert any(46 <= a and a + 3.8 <= 54.2 for a in starts), starts
    assert exp['varredura_local']['cortes'] >= 4 and exp['cobertura_semantica_integral'] is False
    # Nenhuma janela escolhida atravessa um corte detectado quando havia alternativa dentro de um plano.
    by_start = {round(r['inicio_s'], 4): r for r in exp['janelas']}
    assert not any(by_start[round(a, 4)]['movimento_local']['corte_na_janela'] for a in starts)
    # A grade antiga (sem varredura) não oferecia essa janela entre as três primeiras.
    old, old_w = A.preparar_lote(_midia(video, varredura_local=False), _need(), _frame)
    assert 'varredura_local' not in old
    assert not any(46 <= p['inicio_s'] and p['inicio_s'] + 3.8 <= 54.2 for p, _ in old_w)


def test_marca_temporal_declarada_orienta_sem_provar(video):
    texto = 'Shot list\n00:10 static wide view\n0:47 object rising from the pad\n'
    marks = A.marcas_temporais(texto, 60.0, ['object rising'])
    assert [m['t'] for m in marks] == [10.0, 47.0]
    assert marks[1]['termos_comuns'] == ['object', 'rising'] and marks[0]['termos_comuns'] == []
    exp, _ = A.preparar_lote(_midia(video, metadados_texto=texto, termos_necessidade=['object rising']), _need(), _frame)
    assert any(r.get('marca_metadado', {}).get('t') == 47.0 for r in exp['janelas'])
    assert A.marcas_temporais('ISBN 12:345:678 sem horário válido', 60, ['x']) == []


def test_nao_insistir_no_mesmo_arquivo_sem_plano_promissor(video):
    exp, windows = A.preparar_lote(_midia(video), _need(), _frame)
    vistos = {round(p['inicio_s'], 4) for p, _ in windows}
    # Depois de ver a ação e os melhores planos, as janelas restantes são paradas, de câmera ou de planos já vistos.
    assert A.ha_janelas_promissoras(exp, vistos, priorizar_movimento=True) is False
    # Sem necessidade de movimento, a regra histórica (qualquer janela não vista) é preservada.
    assert A.ha_janelas_promissoras(exp, vistos, priorizar_movimento=False) is True
    # Se só uma janela parada foi vista, ainda há plano promissor.
    parado = next(round(r['inicio_s'], 4) for r in exp['janelas'] if r['movimento_local']['parado'])
    assert A.ha_janelas_promissoras(exp, {parado}, priorizar_movimento=True) is True


def test_reuso_de_checkpoint_independe_da_grade(video):
    exp, _ = A.preparar_lote(_midia(video, varredura_local=False), _need(), _frame)
    antigo = 17.3456  # início revisado por uma grade anterior, ausente da grade atual
    assert antigo not in {round(r['inicio_s'], 4) for r in exp['janelas']}
    _, w1 = A.preparar_lote(_midia(video, varredura_local=False), _need(), _frame, priorizar_cache={antigo})
    _, w2 = A.preparar_lote(_midia(video, varredura_local=False), _need(), _frame, priorizar_cache={antigo})
    assert antigo in {round(p['inicio_s'], 4) for p, _ in w1}
    assert [p['revisao_id'] for p, _ in w1] == [p['revisao_id'] for p, _ in w2]


def test_janela_com_analise_privada_armazenada_continua_alcancavel(video):
    exp, windows = A.preparar_lote(_midia(video), _need(), _frame)
    vistos = {round(p['inicio_s'], 4) for p, _ in windows}
    restante = next(round(r['inicio_s'], 4) for r in exp['janelas'] if round(r['inicio_s'], 4) not in vistos)
    assert A.ha_janelas_promissoras(exp, vistos, priorizar_movimento=True) is False
    assert A.ha_janelas_promissoras(exp, vistos, priorizar_movimento=True, gratuitas={restante}) is True


def test_transicao_gradual_real_nao_vira_varios_planos():
    """Clipe real do repositório (Canal do Panamá, timelapse com fusão ~2,6–3,4 s)."""
    v = A.varrer('tests/midia/video_horizontal_navio.mp4', 6.0, largura_origem=1280, altura_origem=720)
    assert v['transicoes'] and all(b - a < .8 for a, b in v['transicoes'])
    assert all(b - a >= .8 for a, b in v['planos']) and len(v['planos']) == 2
