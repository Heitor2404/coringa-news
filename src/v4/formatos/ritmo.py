"""Ritmo visual MEDIDO no MP4 (mesma métrica da engenharia reversa das referências, scripts/analisar_referencia.py):
mudança média por segundo na zona de conteúdo (8–62 % da altura, sem a faixa de legenda), a 4 quadros/s.
Segundo "parado" = mudança < 0,5. Serve para COMPROVAR (não só citar) a correção do congelamento do DOSSIÊ (ERR-067)
e comparar com as referências (A: maior trecho parado 2 s; B: 1 s)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

LIMIAR = .5


def quadros(mp4: Path, fps: float = 4, w: int = 180):
    h = int(round(w * 16 / 9))
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-vf', f'fps={fps},scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 3)


def por_segundo(qs) -> list[float]:
    H = qs.shape[1]
    zc = slice(int(.08 * H), int(.62 * H))
    out = []
    for s in range(len(qs) // 4):
        b = qs[s * 4:(s + 1) * 4].astype(np.int16)
        out.append(round(float(np.abs(np.diff(b[:, zc], axis=0)).mean()), 2))
    return out


def resumo(movs: list[float]) -> dict:
    maior = atual = 0
    for m in movs:
        atual = atual + 1 if m < LIMIAR else 0
        maior = max(maior, atual)
    return {'segundos': len(movs), 'segundos_parados': sum(m < LIMIAR for m in movs), 'maior_trecho_parado_s': maior,
            'mov_mediana': float(np.median(movs)) if movs else 0.0, 'por_segundo': movs}


def medir(mp4: Path) -> dict:
    return resumo(por_segundo(quadros(Path(mp4))))
