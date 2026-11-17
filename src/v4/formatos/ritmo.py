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


def por_segundo_sem_camera(qs, fps: float = 4) -> list[float]:
    """mudança por segundo DESCONTANDO o movimento de câmera: estima a transformação global (ORB + RANSAC, afim parcial)
    entre quadros vizinhos, alinha o anterior ao atual e mede só o resíduo — zoom/pan decorativo não conta como progresso"""
    import cv2
    H = qs.shape[1]
    zc = slice(int(.08 * H), int(.62 * H))
    orb = cv2.ORB_create(800)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    res = []
    for i in range(1, len(qs)):
        a = cv2.cvtColor(qs[i - 1], cv2.COLOR_RGB2GRAY)
        b = cv2.cvtColor(qs[i], cv2.COLOR_RGB2GRAY)
        ka, da = orb.detectAndCompute(a, None)
        kb, db = orb.detectAndCompute(b, None)
        M = None
        if da is not None and db is not None and len(ka) > 12 and len(kb) > 12:
            mt = bf.match(da, db)
            if len(mt) >= 12:
                pa = np.float32([ka[m.queryIdx].pt for m in mt])
                pb = np.float32([kb[m.trainIdx].pt for m in mt])
                M, _ = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=2.0)
        if M is None:
            M = np.float32([[1, 0, 0], [0, 1, 0]])
        al = cv2.warpAffine(qs[i - 1], M, (qs.shape[2], H), borderMode=cv2.BORDER_REPLICATE)
        res.append(float(np.abs(al[zc].astype(np.int16) - qs[i][zc].astype(np.int16)).mean()))
    out = []
    for s in range(len(qs) // int(fps)):
        bloco = res[s * int(fps):(s + 1) * int(fps) - 1] or [0.0]
        out.append(round(float(np.mean(bloco)), 2))
    return out


def medir_completo(mp4: Path) -> dict:
    """métrica bruta (comparável às referências) + métrica sem câmera (a que decide o portão de progresso)"""
    qs = quadros(Path(mp4))
    bruto = resumo(por_segundo(qs))
    sem = resumo(por_segundo_sem_camera(qs))
    return {**bruto, 'sem_camera': sem}
