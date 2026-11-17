"""Engenharia reversa de um vídeo vertical de REFERÊNCIA (uso interno; o vídeo e os quadros NÃO entram no repositório).

uso: python scripts/analisar_referencia.py <video.mp4> <pasta_saida>
Gera em <pasta_saida>: cortes.json (PySceneDetect, limiar de conteúdo), segundos.json (por segundo: mudança na zona de
conteúdo SEM a faixa de legenda, mudança na faixa de legenda, brilho, saturação, fração de bordas = densidade gráfica,
loudness momentâneo) e grade_<k>.jpg (4 quadros por segundo nas janelas de transição) para inspeção visual.
Distingue TROCA DE TOMADA (corte detectado) de PROGRESSÃO SOBRE PLANO PERSISTENTE (mudança local sem corte).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np


def quadros(mp4: Path, fps: float, w: int = 180):
    h = int(round(w * 16 / 9))
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-vf', f'fps={fps},scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 3)


def cortes(mp4: Path) -> list[float]:
    from scenedetect import ContentDetector, detect
    return [round(a.get_seconds(), 2) for a, _ in detect(str(mp4), ContentDetector(threshold=27.0))][1:]


def loudness_por_segundo(mp4: Path) -> list[float]:
    r = subprocess.run(['ffmpeg', '-nostats', '-i', str(mp4), '-af', 'ebur128=metadata=1,ametadata=print:key=lavfi.r128.M', '-f', 'null', '-'],
                       capture_output=True, text=True)
    vals = [float(l.split('=')[1]) for l in r.stderr.splitlines() if 'lavfi.r128.M=' in l]
    # ebur128 emite a cada 100 ms
    return [round(float(np.mean(vals[i:i + 10])), 1) for i in range(0, len(vals), 10)]


def main(mp4: Path, saida: Path):
    saida.mkdir(parents=True, exist_ok=True)
    qs = quadros(mp4, 4)
    H = qs.shape[1]
    zc = slice(int(.08 * H), int(.62 * H))          # conteúdo (acima da faixa típica de legenda)
    zl = slice(int(.62 * H), int(.80 * H))          # faixa de legenda
    seg = []
    for s in range(len(qs) // 4):
        b = qs[s * 4:(s + 1) * 4].astype(np.int16)
        mc = float(np.abs(np.diff(b[:, zc], axis=0)).mean())
        ml = float(np.abs(np.diff(b[:, zl], axis=0)).mean())
        q = b[2].astype(np.float32)
        g = q.mean(axis=2)
        bordas = float(((np.abs(np.diff(g, axis=1)) > 25).mean() + (np.abs(np.diff(g, axis=0)) > 25).mean()) / 2)
        sat = float((q.max(axis=2) - q.min(axis=2)).mean())
        seg.append({'s': s, 'mov_conteudo': round(mc, 2), 'mov_legenda': round(ml, 2), 'brilho': round(float(g.mean()), 1),
                    'saturacao': round(sat, 1), 'bordas': round(bordas, 3)})
    lu = loudness_por_segundo(mp4)
    for x in seg:
        x['lufs_m'] = lu[x['s']] if x['s'] < len(lu) else None
    cs = cortes(mp4)
    (saida / 'cortes.json').write_text(json.dumps(cs))
    (saida / 'segundos.json').write_text(json.dumps(seg))
    print(json.dumps({'duracao_s': len(seg), 'cortes': len(cs), 'cortes_por_min': round(60 * len(cs) / max(1, len(seg)), 1),
                      'mov_conteudo_mediana': float(np.median([x['mov_conteudo'] for x in seg])),
                      'segundos_sem_mudanca_conteudo': sum(x['mov_conteudo'] < .5 for x in seg)}))


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
