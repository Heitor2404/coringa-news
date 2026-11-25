"""E284 — riscos 3.1 e 3.2 da auditoria independente da varredura temporal.

3.1: fps=max(.5, …) não garantia o limite de quadros acima de ~24 min e capturava todo o stdout do FFmpeg em memória.
3.2: ha_janelas_promissoras() abandonava um arquivo só porque o PLANO já tinha sido observado; uma câmera fixa pode
registrar vários acontecimentos distintos no mesmo plano.
"""
from __future__ import annotations

import shutil
import subprocess

import numpy as np
import pytest
from PIL import Image

from src.v4.formatos import amostragem_documental as A

pytestmark = pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='ffmpeg ausente')


def _encode(path, frames_iter, w, h, fps):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{w}x{h}', '-r', str(fps),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-g', str(fps * 4), str(path)],
                         stdin=subprocess.PIPE)
    for f in frames_iter:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    assert p.wait() == 0


def _fundo(w, h, seed=7):
    rng = np.random.default_rng(seed)
    base = rng.integers(40, 200, (h // 12 + 2, w // 12 + 2), dtype=np.uint8)
    return np.asarray(Image.fromarray(base).resize((w, h), Image.BICUBIC), dtype=np.uint8)


@pytest.fixture(scope='module')
def longo(tmp_path_factory):
    """26 min de câmera fixa; um objeto se desloca só entre 20:00 e 20:30."""
    w, h, fps, dur = 96, 54, 2, 26 * 60
    bg = _fundo(w, h)

    def frames():
        for i in range(dur * fps):
            t = i / fps
            f = bg.copy()
            if 1200 <= t < 1230:
                x = int(5 + (t - 1200) / 30 * (w - 25))
                f[20:34, x:x + 14] = 250
            yield f
    p = tmp_path_factory.mktemp('e284') / 'longo.mp4'
    _encode(p, frames(), w, h, fps)
    return p


def test_limite_de_quadros_respeitado_acima_de_24_min_cobrindo_o_arquivo_inteiro(longo):
    v = A.varrer(longo, 26 * 60.0, max_quadros=720)
    assert v['modo'] == 'ancoras' and v['quadros'] <= 720
    assert abs(v['duracao_varrida_s'] - 1560) < 2
    ts = [q['t'] for q in v['pares']]
    assert min(ts) < 10 and max(ts) > 1550 and v['maior_lacuna_s'] < 10
    # O acontecimento tardio aparece como movimento local de algum par.
    ativos = [q['t'] for q in v['pares'] if q['referente'] > .02]
    assert ativos and all(1195 <= t <= 1235 for t in ativos)


def test_orcamento_de_tempo_interrompe_sem_abandonar_a_cobertura(longo):
    v = A.varrer(longo, 26 * 60.0, max_quadros=720, tempo_max_s=1.0)
    assert v is not None and v['quadros'] < 720
    ts = [q['t'] for q in v['pares']]
    assert min(ts) < 1560 * .3 and max(ts) > 1560 * .7     # prefixo hierárquico abrange o arquivo
    ordem = A._ordem_hierarquica(16)
    assert sorted(ordem[:4]) == [0, 4, 8, 12]


def test_metadados_de_duracao_incorretos(longo, monkeypatch):
    # Duração declarada muito menor que a real: limite respeitado, duração real usada.
    v = A.varrer(longo, 30.0, max_quadros=200)
    assert v['quadros'] <= 200 and v['duracao_varrida_s'] > 1500
    # Sem sonda de pacotes (metadados ausentes): o estouro do limite leva à duração por demux, não à leitura sem fim.
    monkeypatch.setattr(A, 'sondar_video', lambda *_a, **_k: None)
    v2 = A.varrer(longo, 30.0, max_quadros=200, largura_origem=96, altura_origem=54)
    assert v2['quadros'] <= 200 and v2['duracao_varrida_s'] > 1500 and v2['modo'] == 'ancoras'


def test_duracao_declarada_maior_que_a_real_nao_gera_janelas_fora_do_arquivo(tmp_path):
    w, h = 64, 36
    bg = _fundo(w, h)
    p = tmp_path / 'curto.mp4'
    _encode(p, (bg for _ in range(40)), w, h, 4)            # 10 s reais
    m = {'expected_sha256': 'c' * 64, 'duration_s': 600.0, 'local_source': str(p), 'width': w, 'height': h}
    e = A.explorar(m, lambda path, t, width: Image.new('RGB', (width, 120), 'gray'))
    assert e['varredura_local']['duracao_varrida_s'] < 11
    assert all(r['inicio_s'] + r['duracao_s'] <= 10.5 for r in e['janelas'])


@pytest.mark.parametrize('w,h', [(400, 16), (16, 400), (2, 2)])
def test_proporcoes_e_resolucoes_extremas(tmp_path, w, h):
    p = tmp_path / f'x{w}x{h}.mp4'
    bg = _fundo(max(w, 24), max(h, 24))[:h, :w]
    ok = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{w}x{h}', '-r', '4', '-i', '-',
                         '-c:v', 'libx264', '-pix_fmt', 'yuv420p' if w % 2 == 0 and h % 2 == 0 else 'yuv444p', str(p)],
                        input=np.stack([bg] * 24).tobytes(), capture_output=True).returncode == 0
    if not ok:
        pytest.skip('codificador não aceita essa dimensão')
    v = A.varrer(p, 6.0)
    assert v is None or (v['largura'] >= 16 and v['altura'] >= 16 and v['quadros'] <= 720)


def test_arquivo_ilegivel_recupera_com_grade_historica(tmp_path):
    p = tmp_path / 'quebrado.mp4'
    p.write_bytes(b'nao e video' * 100)
    assert A.varrer(p, 60.0) is None
    m = {'expected_sha256': 'd' * 64, 'duration_s': 60.0, 'local_source': str(p), 'width': 320, 'height': 180}
    e = A.explorar(m, lambda path, t, width: Image.new('RGB', (width, 120), 'gray'))
    assert e['varredura_local']['estado'] == 'INDISPONIVEL' and len(e['janelas']) >= 3


@pytest.fixture(scope='module')
def plano_unico(tmp_path_factory):
    """Um único plano fixo de 180 s: evento A (40–50 s), evento B (120–130 s), transformação lenta (150–178 s)."""
    w, h, fps = 160, 90, 5
    bg = _fundo(w, h, seed=3).astype(np.float32)

    def frames():
        for i in range(180 * fps):
            t = i / fps
            f = bg.copy()
            if 40 <= t < 50:
                x = int(10 + (t - 40) / 10 * 120)
                f[30:50, x:x + 20] = 250
            if 120 <= t < 130:
                y = int(70 - (t - 120) / 10 * 55)
                f[y:y + 16, 70:86] = 15
            if t >= 150:
                f = np.clip(f * (1 + .9 * (t - 150) / 30), 0, 255)   # mudança gradual de aparência, sem objeto móvel
            yield f.astype(np.uint8)
    p = tmp_path_factory.mktemp('e284u') / 'plano_unico.mp4'
    _encode(p, frames(), w, h, fps)
    return p


def _frame(path, t, width):
    import io
    z = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', str(path), '-frames:v', '1',
                                 '-vf', f'scale={width}:-2', '-f', 'image2pipe', '-vcodec', 'png', 'pipe:1'])
    return Image.open(io.BytesIO(z)).convert('RGB')


def _need():
    return {'id': 'n', 'fatos': ['f'], 'mostrar': 'acontecimento', 'evidencia_visual': 'movimento'}


def test_eventos_distintos_no_mesmo_plano_continuam_alcancaveis(plano_unico):
    m = {'expected_sha256': 'e' * 64, 'duration_s': 180.0, 'local_source': str(plano_unico), 'width': 160, 'height': 90}
    e = A.explorar(m, _frame)
    assert len(e['varredura_local']['planos']) == 1 and e['varredura_local']['eventos'] >= 3
    rows = [r for r in e['janelas'] if 'diagnostico' in r]
    toca = lambda r, a, b: r['inicio_s'] < b and r['inicio_s'] + r['duracao_s'] > a
    assert any(toca(r, 40, 50) for r in rows) and any(toca(r, 120, 130) for r in rows)
    assert any(toca(r, 150, 180) for r in rows)
    # Depois de observar só o evento A, o mesmo plano ainda tem acontecimento promissor (B).
    a = {round(r['inicio_s'], 4) for r in rows if toca(r, 40, 50)}
    assert A.ha_janelas_promissoras(e, a, priorizar_movimento=True) is True
    # A seleção do primeiro lote diversifica eventos dentro do plano.
    sel = A.selecionar(e, limite=3, priorizar_movimento=True)
    assert any(toca(r, 40, 50) for r in sel) and any(toca(r, 120, 130) for r in sel)


def test_sem_sinal_novo_o_arquivo_nao_e_insistido(plano_unico):
    m = {'expected_sha256': 'e' * 64, 'duration_s': 180.0, 'local_source': str(plano_unico), 'width': 160, 'height': 90}
    e = A.explorar(m, _frame)
    rows = [r for r in e['janelas'] if 'diagnostico' in r]
    toca = lambda r, a, b: r['inicio_s'] < b and r['inicio_s'] + r['duracao_s'] > a
    vistos = {round(r['inicio_s'], 4) for r in rows if toca(r, 40, 50) or toca(r, 120, 130) or toca(r, 150, 180)}
    # Restam só trechos parados sem deriva: preferir outro candidato.
    assert A.ha_janelas_promissoras(e, vistos, priorizar_movimento=True) is False


def test_arquivo_da_biblioteca_com_negativas_repetidas_cede_lugar_a_candidato_novo():
    """E281.2/E284: o clipe Apollo (biblioteca) tinha 3 janelas revisadas sem a decolagem; um candidato novo deve
    ser inspecionado antes de nova chamada nesse ângulo — sem excluí-lo."""
    from src.v4.formatos import revisao_documental as R
    n = {'id': 'n2', 'mostrar': 'foguete se elevando', 'evidencia_visual': 'movimento', 'fatos': ['f']}
    velho = {'fonte': 'biblioteca_v3', 'source_id': 'apollo', 'tipo': 'video', 'titulo': 'launch',
             'revisao_adicional_possivel': True, 'negativas_revisadas': 3}
    novo = {'fonte': 'commons', 'source_id': 'novo', 'tipo': 'video', 'titulo': 'launch'}
    ordem = []
    R.fila_cobertura(n, [velho, novo], lambda c, _n: ordem.append(c['source_id']) or {'estado': 'INSUFICIENTE'},
                     priorizar_novos=True)
    assert ordem == ['novo', 'apollo']
    poucos = {**velho, 'negativas_revisadas': 1}
    ordem.clear()
    R.fila_cobertura(n, [poucos, novo], lambda c, _n: ordem.append(c['source_id']) or {'estado': 'INSUFICIENTE'},
                     priorizar_novos=True)
    assert ordem[0] == 'apollo'


def test_mesmos_bytes_de_outra_fonte_nao_ganham_nova_chamada_antes_de_candidatos_novos():
    """Run 45666408862: o clipe Apollo voltou pelo Commons (mesmo SHA da biblioteca) e recebeu a 2ª chamada.
    O E247 adia nova chamada em arquivo com >=3 negativas revisadas para a necessidade enquanto não é a última fase."""
    from pathlib import Path
    code = (Path(__file__).resolve().parents[1] / 'scripts/qa_revisao_documental_e247.py').read_text()
    bloco = code[code.index('# E284: the SAME BYTES'):code.index('cached_starts=set();cached_exact={}')]
    assert "n['evidencia_visual']=='movimento' and phase<1" in bloco and 'negs>=3' in bloco
    assert "ADIADO_ANGULO_COM_NEGATIVAS_REVISADAS" in bloco and "c['revisao_adicional_possivel']=True" in bloco
    assert "'angulos_adiados':deferred_angles" in code
