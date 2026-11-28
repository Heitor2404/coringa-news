"""Metrologia de malhas articuladas, independente de equipamento e solver.

Não infere datums de fabricante. Faces são índices da malha compilada e
conferida, não índices de um STEP original. Não altera o curso nem os gates.
A separação de planos projetada NÃO comprova contato, folga mínima 3D ou
equivalência com a ficha técnica; tais conclusões exigem prova independente.
"""
from __future__ import annotations

import numpy as np


def recusar(motivo):
    raise ValueError("E22-" + motivo)


def vetor(x):
    a = np.asarray(x, dtype=float)
    if a.shape != (3,) or not np.isfinite(a).all():
        recusar("VETOR")
    return a


def unitario(x):
    a = vetor(x)
    n = np.linalg.norm(a)
    if not np.isfinite(n) or n < 1e-12:
        recusar("EIXO")
    return a / n


def referencial(t):
    t = np.asarray(t, dtype=float)
    if t.shape != (4, 4) or not np.isfinite(t).all():
        recusar("POSE")
    r = t[:3, :3]
    if not (np.allclose(r.T @ r, np.eye(3), atol=1e-7, rtol=0)
            and abs(np.linalg.det(r) - 1) < 1e-7
            and np.allclose(t[3], [0, 0, 0, 1], atol=1e-7, rtol=0)):
        recusar("POSE_NAO_RIGIDA")
    return t


def preparar_face(mont, spec):
    corpo = mont.indice_corpo(spec["corpo"])
    vv = [v for v in mont.visuais
          if v.corpo == corpo and v.nome == spec["visual"]]
    if len(vv) != 1:
        recusar("VISUAL_AUSENTE_OU_AMBIGUO")
    v = vv[0]
    idx = spec["triangulos"]
    if (not isinstance(idx, list) or not idx
            or any(type(i) is not int for i in idx)
            or len(set(idx)) != len(idx)):
        recusar("INDICES_FACE")
    f = np.asarray(v.faces)
    p = np.asarray(v.vertices, dtype=float)
    if (f.ndim != 2 or f.shape[1] != 3 or f.dtype.kind not in "iu"
            or p.ndim != 2 or p.shape[1] != 3 or not np.isfinite(p).all()
            or min(idx) < 0 or max(idx) >= len(f)):
        recusar("MALHA_OU_FACE")
    sub = f[idx]
    if sub.min() < 0 or sub.max() >= len(p):
        recusar("VERTICE")
    tri = p[sub]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    area2 = np.linalg.norm(n, axis=1)
    if not np.isfinite(area2).all() or (area2 <= 1e-14).any():
        recusar("TRIANGULO_DEGENERADO")
    T = referencial(v.local)
    return corpo, tri @ T[:3, :3].T + T[:3, 3], (n / area2[:, None]) @ T[:3, :3].T


def medir_planos(mont, qs, spec):
    """Eixo em corpo de referência; dois patches explícitos, sem autoajuste."""
    if spec.get("tipo") != "separacao_planos_projetada" or spec.get("unidade") != "m":
        recusar("TIPO_OU_UNIDADE")
    fonte = spec.get("fonte_datum")
    if not isinstance(fonte, str) or not fonte.strip():
        recusar("SEM_PROCEDENCIA_DATUM")
    tol = float(spec.get("planaridade_m", 1e-5))
    ang = float(spec.get("desvio_normal_deg", 1))
    if not (0 < tol <= 1e-3 and 0 < ang <= 5):
        recusar("TOLERANCIA_GEOMETRICA")
    eixo = unitario(spec["eixo_local"])
    base = mont.indice_corpo(spec["corpo_referencia"])
    a = preparar_face(mont, spec["a"])
    b = preparar_face(mont, spec["b"])
    if a[0] == b[0]:
        recusar("MESMO_CORPO")
    cmin = np.cos(np.deg2rad(ang))
    valores, espalhamentos = [], []
    for q in qs:
        X = mont.poses(q)
        d = referencial(X[base])[:3, :3] @ eixo
        planos = []
        for k, (corpo, tri, normais) in enumerate((a, b)):
            T = referencial(X[corpo])
            n = normais @ T[:3, :3].T
            # Winding não é usado para inferir o lado físico do contato.
            if (np.abs(n @ d) < cmin).any():
                recusar("NORMAL_INCOMPATIVEL")
            proj = (tri @ T[:3, :3].T + T[:3, 3]) @ d
            spread = float(np.ptp(proj))
            if not np.isfinite(spread) or spread > tol:
                recusar("PATCH_NAO_PLANAR")
            espalhamentos.append(spread)
            planos.append(float((proj.max() + proj.min()) / 2))
        valores.append(planos[1] - planos[0])
    if not valores:
        recusar("SEM_POSES")
    return dict(resumo_serie(valores), tipo=spec["tipo"], unidade="mm",
                fonte_datum=fonte, corpo_referencia=spec["corpo_referencia"],
                eixo_local=eixo.tolist(), a=spec["a"], b=spec["b"],
                maior_espalhamento_plano_mm=max(espalhamentos)*1000,
                equivalencia_fabricante="NAO_DEMONSTRADA",
                contato_3d="NAO_INFERIDO")


def resumo_serie(serie_m):
    s = np.asarray(serie_m, dtype=float)
    if s.ndim != 1 or not len(s) or not np.isfinite(s).all():
        recusar("SERIE")
    lo, hi = float(s.min()*1000), float(s.max()*1000)
    return dict(min_mm=lo, max_mm=hi, curso_mm=hi-lo,
                amostras=len(s), indice_min=int(s.argmin()), indice_max=int(s.argmax()))


def diagnostico(mont, qs, medida, serie_m):
    """Relatório auxiliar; nunca troca max por curso ou altera o oráculo."""
    r = dict(resumo_serie(serie_m), tipo_legado=medida["tipo"],
             equivalencia_fabricante="NAO_AVALIADA_POR_E22")
    if medida["tipo"] == "folga":
        r["definicao_legada"] = "extremos_projetados_das_subarvores"
        r["equivalencia_fabricante"] = "NAO_DEMONSTRADA_POR_DATUM"
    if "datum" in medida:
        r["datum"] = medir_planos(mont, qs, medida["datum"])
    return r
