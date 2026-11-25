"""E284 (run 45675321595): 9/165 palavras começavam na pausa antes da fala real (legenda antecipada; limite 3%)."""
import wave

import numpy as np

from src.v4.formatos import legenda_sync as LS


def _wav(tmp_path):
    sr = 16000
    t = lambda s: (np.sin(np.arange(int(s * sr)) * 2 * np.pi * 180 / sr) * 9000).astype(np.int16)
    z = lambda s: np.zeros(int(s * sr), np.int16)
    a = np.concatenate([t(1.0), z(.5), t(1.0)])          # fala 0–1 s, pausa 1–1,5 s, fala 1,5–2,5 s
    p = tmp_path / 'v.wav'
    with wave.open(str(p), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(a.tobytes())
    return p


def test_inicio_na_pausa_vai_para_o_comeco_real_da_fala(tmp_path):
    p = _wav(tmp_path)
    ws = [{'w': 'A', 's': .1, 'e': .9}, {'w': 'NAS', 's': 1.15, 'e': 1.9}, {'w': 'C', 's': 2.0, 'e': 2.4}]
    out = LS.alinhar_inicios_a_fala(ws, p)
    assert out[0]['s'] == .1 and out[2]['s'] == 2.0
    assert 1.45 <= out[1]['s'] <= 1.6 and out[1]['s_alinhador'] == 1.15 and out[1]['e'] == 1.9


def test_sem_fala_proxima_nao_inventa(tmp_path):
    p = _wav(tmp_path)
    ws = [{'w': 'X', 's': 1.02, 'e': 1.2}]        # pausa e fim antes da fala seguinte
    assert LS.alinhar_inicios_a_fala(ws, p)[0]['s'] == 1.02
