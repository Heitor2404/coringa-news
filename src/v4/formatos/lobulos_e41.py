"""E41 — pares superiores por geometria: contato lobulado e pino-em-furo.

Nada aqui assume que um perfil periódico é engrenagem. O par LOBULADO só é
aceito quando, simulado com a razão derivada das CONTAGENS (lóbulos L do
perfil real, M roletes) e a excentricidade MEDIDA, o perfil do sólido real
permanece CONJUGADO aos roletes ao longo de uma volta inteira da entrada:
nenhuma penetração acima de PEN_MAX e algum rolete sempre dentro de
FOLGA_CONTATO. As razões alternativas são testadas e registradas; a aceita
precisa ser claramente melhor (discriminação), senão recusa.

Critérios fixados ANTES da primeira medição (24/11/2026): PEN_MAX = 0,02 mm;
FOLGA_CONTATO = 0,25 mm (ordem da folga de peça impressa/usinada).

Pino-em-furo: furos côncavos do corpo de perfil co-circulares em torno do seu
eixo e roletes convexos co-circulares em torno do eixo principal, mesmo raio
de círculo, com r_furo − r_rolete = excentricidade (±TOL) ⇒ a saída copia a
rotação absoluta do corpo de perfil (mecanismo de eixos paralelos).
"""
from __future__ import annotations

import math

import numpy as np

from .vinculos_e41 import _ajusta_circulo, _dist_reta, _paralelos, _u, TOL_EIXO

PEN_MAX = 0.02
FOLGA_CONTATO = 0.25
TOL_EXC = 0.02


def fail(c):
    raise ValueError("E41-LOB-" + c)


def conjuntos_cilindricos(corpos, convexo=True, minimo=5, ext_min=300):
    """Cilindros completos de mesmo raio, eixos paralelos, centros co-circulares
    e mesma camada axial, cada um num corpo (roletes) — ou furos (côncavos)."""
    itens = []
    for i, c in enumerate(corpos):
        for cy in c.cilindros:
            if cy.concavo == convexo or cy.extensao_graus < ext_min:
                continue
            itens.append((i, cy))
    out, usados = [], set()
    for a, (i, ca) in enumerate(itens):
        if a in usados:
            continue
        d = _u(ca.eixo)
        z = lambda cy: np.dot(cy.origem, d) + 0.5 * (cy.zmin + cy.zmax) * np.dot(cy.eixo, d)
        grupo = [b for b, (j, cb) in enumerate(itens) if b not in usados and abs(cb.raio - ca.raio) < 1e-3
                 and _paralelos(cb.eixo, d) and abs(z(cb) - z(ca)) < 0.5 * (ca.zmax - ca.zmin) + 1e-6]
        corpos_g = {itens[b][0] for b in grupo}
        if len(grupo) < minimo or len(corpos_g) < (minimo if convexo else 1):
            continue
        P = np.array([itens[b][1].origem - np.dot(itens[b][1].origem, d) * d for b in grupo])
        # remove duplicatas (mesmo eixo)
        uniq, idx = [], []
        for k, p in enumerate(P):
            if all(np.linalg.norm(p - q) > TOL_EIXO for q in uniq):
                uniq.append(p)
                idx.append(grupo[k])
        # Círculos por consenso: vários anéis de cilindros iguais podem dividir a camada.
        restantes = list(range(len(uniq)))
        U = np.array(uniq) if uniq else np.zeros((0, 3))
        while len(restantes) >= minimo:
            melhor = None
            for t1 in range(len(restantes)):
                for t2 in range(t1 + 1, len(restantes)):
                    for t3 in range(t2 + 1, len(restantes)):
                        tri = U[[restantes[t1], restantes[t2], restantes[t3]]]
                        c3, _, R3, _, _ = _ajusta_circulo(tri)
                        if not np.isfinite(R3) or R3 <= ca.raio:
                            continue
                        dist = np.abs(np.linalg.norm(U[restantes] - c3, axis=1) - R3)
                        inl = [restantes[k] for k in np.nonzero(dist < TOL_EIXO)[0]]
                        if melhor is None or len(inl) > len(melhor):
                            melhor = inl
            if not melhor or len(melhor) < minimo:
                break
            centro, n, R, res, plan = _ajusta_circulo(U[melhor])
            sel = [idx[k] for k in melhor]
            usados |= set(sel)
            out.append(dict(raio=ca.raio, n=len(melhor), centro=centro + z(ca) * d, eixo=d, R=R, residuo=res,
                            corpos=sorted({itens[b][0] for b in sel}), centros=U[melhor] + z(ca) * d,
                            z=float(z(ca)), meia_altura=0.5 * (ca.zmax - ca.zmin)))
            restantes = [k for k in restantes if k not in melhor]
        usados |= set(grupo)
    return out


def _base_plano(d):
    a = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = _u(a - np.dot(a, d) * d)
    return e1, np.cross(d, e1)


def perfil(vertices, centro, eixo, z, meia, bins=7200):
    """Contorno externo do corpo na camada axial, em torno de `centro`.

    Devolve (φ, ρ, (e1, e2), Q): φ/ρ reamostrados (só para contar lóbulos) e Q,
    os pontos VERDADEIROS do contorno externo (o de maior raio em cada setor
    de 0,05°), usados na conjugação — a reamostragem por setor desloca pontos
    tangencialmente e não serve para medir penetração."""
    d = _u(eixo)
    e1, e2 = _base_plano(d)
    w = vertices - centro
    zz = w @ d
    sel = np.abs(zz - (z - np.dot(centro, d))) <= meia
    x, y = w[sel] @ e1, w[sel] @ e2
    phi = np.arctan2(y, x)
    rho = np.hypot(x, y)
    k = ((phi + math.pi) / (2 * math.pi) * bins).astype(int) % bins
    ordem = np.lexsort((-rho, k))            # por setor, maior raio primeiro
    k_ord = k[ordem]
    primeiro = np.r_[True, k_ord[1:] != k_ord[:-1]]
    esc = ordem[primeiro]
    if len(esc) < 0.8 * bins:
        fail("PERFIL_ESPARSO")
    esc = esc[np.argsort(phi[esc])]
    Q = np.c_[x[esc], y[esc]]
    ang = -math.pi + (np.arange(1440) + 0.5) * 2 * math.pi / 1440
    r = np.interp(ang, phi[esc], rho[esc], period=2 * math.pi)
    return ang, r, (e1, e2), Q


def secao(forma, ponto, normal, passo=0.02):
    """Pontos (mm) da seção EXATA do sólido B-rep pelo plano (ponto, normal)."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopoDS import TopoDS
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GCPnts import GCPnts_UniformAbscissa
    sec = BRepAlgoAPI_Section(getattr(forma, "wrapped", forma), gp_Pln(gp_Pnt(*map(float, ponto)), gp_Dir(*map(float, normal))))
    sec.Build()
    ex = TopExp_Explorer(sec.Shape(), TopAbs_EDGE)
    pts = []
    while ex.More():
        cur = BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current()))
        ab = GCPnts_UniformAbscissa(cur, passo)
        if ab.IsDone():
            for i in range(1, ab.NbPoints() + 1):
                q = cur.Value(ab.Parameter(i))
                pts.append((q.X(), q.Y(), q.Z()))
        ex.Next()
    if not pts:
        fail("SECAO_VAZIA")
    return np.array(pts)


def lobulos(rho):
    F = np.abs(np.fft.rfft(rho - rho.mean()))
    k = int(np.argmax(F[2:len(F) // 4])) + 2
    return k, float(F[k] / (np.sort(F[2:len(F) // 4])[-2] + 1e-12))


def _dist_poligono(P, Q):
    """Distância de cada ponto P (n,2) à poligonal fechada Q (m,2) e se P está
    dentro (par/ímpar)."""
    A, B = Q, np.roll(Q, -1, axis=0)
    AB = B - A
    L2 = (AB ** 2).sum(1)
    d = np.empty(len(P))
    dentro = np.zeros(len(P), bool)
    for i, p in enumerate(P):
        t = np.clip(((p - A) * AB).sum(1) / L2, 0, 1)
        proj = A + t[:, None] * AB
        d[i] = np.sqrt(((proj - p) ** 2).sum(1)).min()
        cruza = ((A[:, 1] > p[1]) != (B[:, 1] > p[1])) & \
                (p[0] < (B[:, 0] - A[:, 0]) * (p[1] - A[:, 1]) / (B[:, 1] - A[:, 1] + 1e-300) + A[:, 0])
        dentro[i] = cruza.sum() % 2 == 1
    return d, dentro


def conjugacao(Q, roletes_xy, r_rolete, c0_xy, O_xy, razao, n_theta=180):
    """Simula a entrada θ ∈ [0, 2π): centro do perfil gira com a excêntrica
    em torno de O; o perfil gira (absoluto) razao·θ. Folga de cada rolete =
    distância do centro ao perfil − r (negativa = penetração)."""
    pens, contatos = [], []
    for th in np.linspace(0, 2 * math.pi, n_theta, endpoint=False):
        c = O_xy + _rot(th) @ (c0_xy - O_xy)
        P = (_rot(-razao * th) @ (roletes_xy - c).T).T
        d, dentro = _dist_poligono(P, Q)
        folga = np.where(dentro, -(d + r_rolete), d - r_rolete)
        pens.append(float(max(0.0, -folga.min())))
        contatos.append(float(max(folga.min(), 0.0)))
    return dict(razao=razao, penetracao_max_mm=max(pens), folga_contato_max_mm=max(contatos),
                aceito=max(pens) <= PEN_MAX and max(contatos) <= FOLGA_CONTATO)


def _rot(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


def par_lobulado(forma, eixo_perfil, roletes, n_theta=180):
    """Identifica L, testa a razão derivada −(M−L)/L contra alternativas e
    devolve a evidência. `eixo_perfil` = eixo próprio do corpo de perfil;
    o perfil vem da seção exata do sólido no plano médio dos roletes."""
    d = _u(roletes["eixo"])
    e1, e2 = _base_plano(d)
    c0 = np.asarray(eixo_perfil["origem"], float)
    meio = roletes["centro"]
    pts = secao(forma, meio, d)
    c0 = c0 + np.dot(meio - c0, d) * d       # centro do perfil no plano da seção
    phi, rho, _, Q = perfil(pts, c0, d, float(np.dot(meio, d)), 1e-3)
    L, destaque = lobulos(rho)
    M = roletes["n"]
    O = roletes["centro"]
    e = _dist_reta(c0, O, d)
    plano = lambda p: np.array([np.dot(p - O, e1), np.dot(p - O, e2)])
    rol_xy = np.array([plano(p) for p in roletes["centros"]])
    c0_xy, O_xy = plano(c0), np.zeros(2)
    # perfil medido no referencial (e1, e2) com origem no centro do perfil
    derivada = -(M - L) / L
    alternativas = sorted({derivada, (M - L) / L, -1.0 / M, -(M - L) / M, 1.0 / L} - {0.0})
    testes = [conjugacao(Q, rol_xy, roletes["raio"], c0_xy, O_xy, r, n_theta) for r in alternativas]
    princ = next(t for t in testes if abs(t["razao"] - derivada) < 1e-12)
    outras = [t for t in testes if t is not princ]
    discrimina = all(t["penetracao_max_mm"] > 10 * max(princ["penetracao_max_mm"], PEN_MAX) for t in outras)
    return dict(pontos_contorno=len(Q), lobulos=L, destaque_harmonico=destaque, roletes=M, raio_roletes_mm=roletes["R"],
                raio_rolete_mm=roletes["raio"], excentricidade_mm=e, razao_derivada=derivada,
                teste_razao_derivada=princ, alternativas=outras, discriminacao=discrimina,
                aceito=bool(princ["aceito"] and discrimina),
                criterios=dict(penetracao_max_mm=PEN_MAX, folga_contato_mm=FOLGA_CONTATO,
                               fixados_antes_da_medicao="2026-11-24"))


def pinos_em_furos(corpo_perfil, eixo_perfil, roletes_saida, e):
    """Furos do corpo de perfil × roletes de saída: r_furo − r_rolete = e."""
    c0 = np.asarray(eixo_perfil["origem"], float)
    d = _u(roletes_saida["eixo"])
    furos = [cy for cy in corpo_perfil.cilindros if cy.concavo and cy.extensao_graus >= 300
             and _paralelos(cy.eixo, d) and abs(_dist_reta(cy.origem, c0, d) - roletes_saida["R"]) < 0.05]
    if len(furos) < 3:
        return dict(aceito=False, motivo="FUROS_INSUFICIENTES", furos=len(furos))
    rh = sorted({round(f.raio, 4) for f in furos})
    dif = rh[0] - roletes_saida["raio"]
    return dict(aceito=len(rh) == 1 and abs(dif - e) <= TOL_EXC, furos=len(furos), raio_furo_mm=rh[0],
                raio_rolete_mm=roletes_saida["raio"], diferenca_mm=dif, excentricidade_mm=e,
                razao=1.0, evidencia="r_furo − r_rolete = excentricidade ⇒ saída copia a rotação do perfil")
