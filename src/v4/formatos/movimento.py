"""MOVIMENTO REAL medido em vídeo (referência × Coringa), sem IA:
- câmera por segundo: afim parcial por SIFT na zona de conteúdo (sem legenda/créditos) → escala/s, deslocamento;
- entrada de elemento: numa caixa, quantos quadros o pixel leva para assentar (início → 90 % da mudança total).
Medidas de MP4 comprimido: servem para comparar ordens de grandeza, não para afirmar easing exato."""
from __future__ import annotations

import cv2
import numpy as np


def _quadro(v, fps, t, zona=(.05, .70)):
    v.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * fps)))
    ok, f = v.read()
    if not ok:
        return None, None
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    if g.shape[1] > 540:
        g = cv2.resize(g, (540, int(g.shape[0] * 540 / g.shape[1])))
    m = np.zeros_like(g)
    m[int(zona[0] * g.shape[0]):int(zona[1] * g.shape[0]), :] = 255
    return g, m


def camera(arq: str, t0: float, t1: float, passo: float = 1.0, zona=(.05, .70)) -> list[dict]:
    v = cv2.VideoCapture(arq)
    fps = v.get(cv2.CAP_PROP_FPS)
    s, bf, out = cv2.SIFT_create(1500), cv2.BFMatcher(), []
    t = t0
    while t + passo <= t1 + 1e-6:
        a, ma = _quadro(v, fps, t, zona)
        b, mb = _quadro(v, fps, t + passo, zona)
        r = None
        if a is not None and b is not None:
            k1, d1 = s.detectAndCompute(a, ma)
            k2, d2 = s.detectAndCompute(b, mb)
            if d1 is not None and d2 is not None and len(k1) > 12 and len(k2) > 12:
                mt = [m for m, n in bf.knnMatch(d1, d2, k=2) if m.distance < .7 * n.distance]
                if len(mt) >= 12:
                    p1 = np.float32([k1[m.queryIdx].pt for m in mt]); p2 = np.float32([k2[m.trainIdx].pt for m in mt])
                    M, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=2.0)
                    if M is not None and inl.sum() >= 12:
                        r = {'escala_por_s': round(float(np.hypot(M[0, 0], M[1, 0])) ** (1 / passo), 4),
                             'dx_px_s': round(float(M[0, 2]) / passo * 1080 / 540, 1), 'dy_px_s': round(float(M[1, 2]) / passo * 1080 / 540, 1), 'inliers': int(inl.sum())}
        out.append({'t': round(t, 2), **(r or {'corte_ou_sem_textura': True})})
        t += passo
    return out


def entrada(arq: str, t0: float, t1: float, caixa_frac: tuple) -> dict:
    """caixa em frações (x0, y0, x1, y1) do quadro; mede a mudança média por quadro entre t0 e t1"""
    v = cv2.VideoCapture(arq)
    fps = v.get(cv2.CAP_PROP_FPS)
    v.set(cv2.CAP_PROP_POS_FRAMES, int(round(t0 * fps)))
    fr = []
    for _ in range(int(round((t1 - t0) * fps)) + 1):
        ok, f = v.read()
        if not ok:
            break
        h, w = f.shape[:2]
        x0, y0, x1, y1 = caixa_frac
        fr.append(cv2.cvtColor(f[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)], cv2.COLOR_BGR2GRAY).astype(np.float32))
    ini = fr[0]
    d = np.array([np.abs(x - ini).mean() for x in fr])
    tot = d[-1] if d[-1] > 1 else d.max()
    if tot <= 1:
        return {'sem_mudanca': True}
    k0 = int(np.argmax(d > .1 * tot)); k9 = int(np.argmax(d > .9 * tot))
    return {'comeca_s': round(t0 + k0 / fps, 2), 'assenta_s': round(t0 + k9 / fps, 2), 'duracao_entrada_s': round((k9 - k0) / fps, 2)}
