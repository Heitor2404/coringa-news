"""V2.2 — video.documental com FILMAGEM REAL (Commons: U.S. Navy e NASA em domínio público; time-lapse CC BY 3.0).
O clipe sintético continua como teste técnico; aqui a validação é com mídia real."""
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.v2 import centros, palco

M = Path(__file__).parent / 'midia'
VIDEOS = sorted(p.name for p in M.glob('video_*.mp4'))


def _quadro(arq, t, out):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', str(arq), '-frames:v', '1', str(out)], check=True)
    return np.asarray(Image.open(out).convert('L').resize((64, 64)), dtype=float)


def _dados(video, ini=1.0, dur=4.0, **extra):
    return {'duration': dur, 'meta': {'motor': 'v2'}, 'captions': [], 'scenes': [{'comp': 'video.documental', 'start': 0, 'end': dur,
            'params': {'video': str(M / video), 'inicio': ini, 'etiqueta': 'VÍDEO · ACERVO', **extra}}]}


@pytest.mark.parametrize('video', VIDEOS)
def test_quadro_no_palco_e_o_do_instante_certo_do_original(tmp_path, video):
    ini = 1.0
    d = palco.preparar(_dados(video, ini))
    q = d['scenes'][0]['params']['quadros']
    for t in (0.4, 1.9, 3.3):
        with palco.abrir(d, tmp_path / 'p') as pg:
            pg.evaluate(f'seek({t})')
            fr = int(pg.evaluate("V2.cenas[0].el.querySelector('.vq').dataset.f || 1"))
        assert fr == 1 + int(t * q['fps']), (t, fr)                             # mapeamento tempo → quadro
        extraido = np.asarray(Image.open(Path(q['dir']) / f'f_{fr:04d}.jpg').convert('L').resize((64, 64)), dtype=float)
        certo = _quadro(M / video, ini + (fr - 1) / q['fps'], tmp_path / 'a.png')
        longe = _quadro(M / video, ini + (fr - 1) / q['fps'] + 1.0, tmp_path / 'b.png')
        d_certo, d_longe = np.abs(extraido - certo).mean(), np.abs(extraido - longe).mean()
        assert d_certo < 10 and d_certo < d_longe, (video, t, d_certo, d_longe)


@pytest.mark.parametrize('video', VIDEOS)
def test_enquadramento_por_orientacao(tmp_path, video):
    d = palco.preparar(_dados(video))
    wh = d['scenes'][0]['params']['quadros']['wh']
    with palco.abrir(d, tmp_path) as pg:
        pg.evaluate('seek(2.0)')
        r = pg.evaluate("(()=>{const e=V2.cenas[0].el.querySelector('.vq').getBoundingClientRect();return [e.left,e.top,e.right,e.bottom]})()")
    if wh[0] > wh[1]:      # deitado: moldura inteira, centrada, sem cortar o quadro
        assert abs((r[0] + r[2]) / 2 - 540) <= 2 and r[2] - r[0] >= 990, r
    else:                  # vertical: cobre a tela
        assert r[0] <= 0 and r[2] >= 1080 and r[1] <= 0 and r[3] >= 1920, r


def test_corte_temporal_muda_o_trecho(tmp_path):
    v = next(x for x in VIDEOS if 'navio' in x)
    a = palco.preparar(_dados(v, ini=0.5))['scenes'][0]['params']['quadros']
    b = palco.preparar(_dados(v, ini=3.5))['scenes'][0]['params']['quadros']
    fa = np.asarray(Image.open(Path(a['dir']) / 'f_0001.jpg').convert('L').resize((64, 64)), dtype=float)
    fb = np.asarray(Image.open(Path(b['dir']) / 'f_0001.jpg').convert('L').resize((64, 64)), dtype=float)
    assert a['dir'] != b['dir'] and np.abs(fa - fb).mean() > 3


def test_sequencia_com_transicao_legenda_e_banner(tmp_path):
    caps = [{'start': .2, 'end': 1.8, 'words': [{'w': w, 's': .2 + i * .2} for i, w in enumerate('O NAVIO-HOSPITAL CRUZA O CANAL'.split())]},
            {'start': 2.2, 'end': 3.8, 'words': [{'w': w, 's': 2.2 + i * .2, 'hl': w == 'GATÚN'} for i, w in enumerate('E SOBE ATÉ GATÚN'.split())]}]
    d = {'duration': 6, 'meta': {'motor': 'v2'}, 'captions': caps, 'scenes': [
        {'comp': 'video.documental', 'start': 0, 'end': 4, 'transicao': 'mascara', 'params': {'video': str(M / next(x for x in VIDEOS if 'navio' in x)), 'inicio': 1,
         'etiqueta': 'VÍDEO · U.S. NAVY · DOMÍNIO PÚBLICO', 'lower_third': {'nome': 'USNS Comfort', 'descricao': 'Canal do Panamá'}}},
        {'comp': 'banner.discreto', 'start': 4, 'end': 6, 'params': {'rotulo': 'CONTEXTO', 'texto': 'Filmagem da Marinha dos EUA'}}]}
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        geo = palco.medir(pg, d['duration'], .25)
        assert not [g for g in geo if g.get('grave')], geo
        for t in (1.0, 3.0):
            pg.evaluate(f'seek({t})')
            leg = [m for m in pg.evaluate('V2.medirCentros()') if m['g'] == 'legenda']
            assert leg and abs(leg[0]['desvio_glifos']) <= centros.TOL_GLIFOS
        assert not pg.erros


def _rms(arq, t0, t1):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', str(arq), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(float)
    return float(np.sqrt((x ** 2).mean())) if len(x) else 0.0


@pytest.mark.parametrize('vol', [0.0, 0.9])
def test_audio_original_presente_ou_removido(tmp_path, vol):
    from src.render import render
    v = next(x for x in VIDEOS if 'navio' in x)
    silencio = tmp_path / 'voz.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', '3', str(silencio)], check=True)
    d = _dados(v, ini=1.0, dur=3.0, audio_original=vol)
    d['meta'] = {'motor': 'v2'}
    out = render.renderizar(d, silencio, tmp_path / 'out.mp4', tmp_path / 'tr', workers=1)
    original = _rms(M / v, 2.0, 3.0)
    r = _rms(out, 1.0, 2.0)
    if vol == 0:
        assert r < 80, r                       # removido (sobra no máximo o swish do corte)
    else:
        assert original > 200 and r > 0.15 * original, (r, original)   # presente (depois da masterização)
