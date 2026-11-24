"""E19 — rasterizador 3D em CPU (numba) para malhas CAD posadas. EXPERIMENTAL.

Sem OpenGL: resultado determinístico e reproduzível no runner. Gera um
G-buffer (profundidade, normal, id de peça) por supersampling e faz o
sombreamento em NumPy: luz principal, preenchimento, recorte (rim), brilho
especular, contorno por descontinuidade de id/profundidade/normal e sombra de
contato suave no plano de apoio. Nenhuma regra depende do nome da máquina.
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit
from PIL import Image, ImageFilter


@njit(cache=True)
def _rasterizar(px, py, pz, faces, ident, W, H, depth, idbuf, nbuf, nx, ny, nz):
    for t in range(faces.shape[0]):
        a, b, c = faces[t, 0], faces[t, 1], faces[t, 2]
        if pz[a] <= 1e-6 or pz[b] <= 1e-6 or pz[c] <= 1e-6:
            continue
        x0, y0, x1, y1, x2, y2 = px[a], py[a], px[b], py[b], px[c], py[c]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-12:
            continue
        xmin = max(int(math.floor(min(x0, min(x1, x2)))), 0)
        xmax = min(int(math.ceil(max(x0, max(x1, x2)))), W - 1)
        ymin = max(int(math.floor(min(y0, min(y1, y2)))), 0)
        ymax = min(int(math.ceil(max(y0, max(y1, y2)))), H - 1)
        if xmin > xmax or ymin > ymax:
            continue
        iz0, iz1, iz2 = 1.0 / pz[a], 1.0 / pz[b], 1.0 / pz[c]
        for y in range(ymin, ymax + 1):
            fy = y + 0.5
            for x in range(xmin, xmax + 1):
                fx = x + 0.5
                w0 = ((x1 - fx) * (y2 - fy) - (x2 - fx) * (y1 - fy)) / area
                w1 = ((x2 - fx) * (y0 - fy) - (x0 - fx) * (y2 - fy)) / area
                w2 = 1.0 - w0 - w1
                if w0 < 0 or w1 < 0 or w2 < 0:
                    continue
                iz = w0 * iz0 + w1 * iz1 + w2 * iz2
                z = 1.0 / iz
                if z < depth[y, x]:
                    depth[y, x] = z
                    idbuf[y, x] = ident[t]
                    nbuf[y, x, 0] = nx[t]
                    nbuf[y, x, 1] = ny[t]
                    nbuf[y, x, 2] = nz[t]


class Camera:
    """Perspectiva com ponto de vista fixo durante todo o filme."""

    def __init__(self, olho, alvo, cima, fov_graus, largura, altura):
        self.olho = np.asarray(olho, float)
        frente = np.asarray(alvo, float) - self.olho
        frente /= np.linalg.norm(frente)
        direita = np.cross(frente, cima)
        direita /= np.linalg.norm(direita)
        baixo = np.cross(frente, direita)
        self.R = np.stack([direita, baixo, frente])  # linhas: x, y(para baixo), z(profundidade)
        self.f = 0.5 * altura / math.tan(math.radians(fov_graus) / 2)
        self.W, self.H = largura, altura
        self.cx, self.cy = largura / 2, altura / 2

    def projetar(self, p):
        c = (p - self.olho) @ self.R.T
        z = c[:, 2]
        return self.f * c[:, 0] / z + self.cx, self.f * c[:, 1] / z + self.cy, z, c


def enquadrar(pontos, direcao, cima, fov_graus, largura, altura, regiao):
    """Câmera que olha na `direcao` e cabe todos os `pontos` na `regiao`
    (x0,y0,x1,y1 em fração do quadro), por busca de distância e recentragem."""
    direcao = np.asarray(direcao, float) / np.linalg.norm(direcao)
    centro = pontos.mean(axis=0)
    raio = float(np.linalg.norm(pontos - centro, axis=1).max())
    x0, y0, x1, y1 = regiao
    alvo_cx, alvo_cy = (x0 + x1) / 2 * largura, (y0 + y1) / 2 * altura
    dist = 3 * raio / math.tan(math.radians(fov_graus) / 2)
    alvo = centro.copy()
    for _ in range(40):
        cam = Camera(alvo - direcao * dist, alvo, cima, fov_graus, largura, altura)
        u, v, _, _ = cam.projetar(pontos)
        ocup = max((u.max() - u.min()) / ((x1 - x0) * largura), (v.max() - v.min()) / ((y1 - y0) * altura))
        du = (u.max() + u.min()) / 2 - alvo_cx
        dv = (v.max() + v.min()) / 2 - alvo_cy
        # Recentraliza em coordenadas de mundo (aprox. pela escala local) e ajusta a distância.
        escala = dist / cam.f
        alvo = alvo + cam.R[0] * du * escala + cam.R[1] * dv * escala
        dist *= ocup
        if abs(ocup - 1) < 1e-3 and abs(du) < .5 and abs(dv) < .5:
            break
    return Camera(alvo - direcao * dist, alvo, cima, fov_graus, largura, altura)


def renderizar(cam, malhas, fundo, luz=(.45, .62, .64), ss=2, chao=None, contorno=(14, 20, 26)):
    """malhas: lista de (vertices_mundo, faces, rgb 0-1, brilho 0-1).
    fundo: imagem RGB uint8 (H, W, 3) no tamanho final.
    chao: altura z do plano de apoio para sombra de contato (ou None)."""
    W, H = cam.W * ss, cam.H * ss
    f, cx, cy = cam.f * ss, cam.cx * ss, cam.cy * ss
    depth = np.full((H, W), np.inf)
    idbuf = np.full((H, W), -1, np.int32)
    nbuf = np.zeros((H, W, 3))
    cores = np.zeros((len(malhas) + 1, 3))
    brilhos = np.zeros(len(malhas) + 1)
    for k, (V, F, rgb, brilho) in enumerate(malhas):
        c = (V - cam.olho) @ cam.R.T
        z = c[:, 2]
        px = f * c[:, 0] / z + cx
        py = f * c[:, 1] / z + cy
        tri = c[F]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
        # Dupla face: a normal sempre aponta para a câmera.
        vis = np.einsum("ij,ij->i", n, tri.mean(axis=1))
        n[vis > 0] *= -1
        ident = np.full(len(F), k, np.int32)
        _rasterizar(px, py, z, F.astype(np.int64), ident, W, H, depth, idbuf, nbuf,
                    n[:, 0].copy(), n[:, 1].copy(), n[:, 2].copy())
        cores[k] = rgb
        brilhos[k] = brilho
    obj = idbuf >= 0
    # Luzes no referencial da câmera (x direita, y baixo, z profundidade):
    # direção em que a luz VIAJA. Principal do alto-esquerda, preenchimento à direita.
    L = np.asarray(luz, float) / np.linalg.norm(luz)
    Lf = np.array([-.7, .1, .7]) / np.linalg.norm([-.7, .1, .7])
    N = nbuf
    Nm = N[obj]
    lam = np.clip(-(Nm @ L), 0, 1)
    fill = np.clip(-(Nm @ Lf), 0, 1)
    rim = np.clip(1 - np.abs(Nm[:, 2]), 0, 1) ** 3
    meio = -L + np.array([0, 0, -1.0])
    meio /= np.linalg.norm(meio)
    spec = np.clip(Nm @ meio, 0, 1) ** 48
    ids = idbuf[obj]
    base = cores[ids]
    br = brilhos[ids]
    cor = base * (0.30 + 0.62 * lam[:, None] + 0.18 * fill[:, None])
    cor += (0.22 * rim)[:, None] * np.array([.55, .7, .85])
    cor += (spec * (0.25 + 0.75 * br))[:, None]
    cor = np.clip(cor, 0, 1)
    # Contorno: troca de peça, salto relativo de profundidade ou quebra de normal.
    borda = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0)):
        a_id, b_id = idbuf[: H - dy, : W - dx], idbuf[dy:, dx:]
        a_z, b_z = depth[: H - dy, : W - dx], depth[dy:, dx:]
        a_n, b_n = N[: H - dy, : W - dx], N[dy:, dx:]
        with np.errstate(invalid="ignore"):
            salto = np.abs(a_z - b_z) / np.minimum(a_z, b_z) > 0.012
        quebra = np.einsum("ijk,ijk->ij", a_n, b_n) < 0.55
        e = (a_id != b_id) | ((a_id >= 0) & (salto | quebra))
        borda[: H - dy, : W - dx] |= e
        borda[dy:, dx:] |= e
    img = np.asarray(Image.fromarray(fundo).resize((W, H), Image.Resampling.BILINEAR), float) / 255
    if chao is not None:
        img = _sombra(img, cam, malhas, chao, ss, obj)
    img[obj] = cor
    img[borda] = img[borda] * 0.35 + np.array(contorno) / 255 * 0.65
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    return np.asarray(out.resize((cam.W, cam.H), Image.Resampling.BOX)), dict(cobertura=float(obj.mean()))


def _sombra(img, cam, malhas, chao, ss, obj):
    """Sombra de contato: projeção vertical das malhas no plano z=chao,
    acumulada em baixa resolução e desfocada."""
    H, W = img.shape[:2]
    fator = 4
    h, w = H // fator, W // fator
    acum = np.zeros((h, w))
    for V, _, _, _ in malhas:
        P = V[:: max(1, len(V) // 20000)].copy()
        altura = P[:, 2] - chao
        P[:, 2] = chao
        c = (P - cam.olho) @ cam.R.T
        u = (cam.f * ss * c[:, 0] / c[:, 2] + cam.cx * ss) / fator
        v = (cam.f * ss * c[:, 1] / c[:, 2] + cam.cy * ss) / fator
        ok = (u >= 0) & (u < w) & (v >= 0) & (v < h)
        peso = np.exp(-np.maximum(altura, 0) / 0.08)
        np.add.at(acum, (v[ok].astype(int), u[ok].astype(int)), peso[ok])
    if acum.max() <= 0:
        return img
    acum = np.clip(acum / np.percentile(acum[acum > 0], 90), 0, 1)
    m = Image.fromarray((acum * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
    m = np.asarray(m.resize((W, H), Image.Resampling.BILINEAR), float) / 255
    return img * (1 - 0.55 * m[..., None])


def fundo_gradiente(largura, altura, topo=(16, 27, 38), base=(6, 11, 16)):
    t = np.linspace(0, 1, altura)[:, None, None]
    g = np.array(topo) * (1 - t) + np.array(base) * t
    y, x = np.mgrid[0:altura, 0:largura]
    r = np.hypot((x - largura / 2) / largura, (y - altura * 0.42) / altura)
    g = g * (1.12 - 0.5 * r[..., None])
    return np.clip(g, 0, 255).astype(np.uint8)
