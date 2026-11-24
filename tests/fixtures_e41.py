"""Montagens sintéticas com relações CONHECIDAS por construção (E41)."""
import math
from pathlib import Path

import cadquery as cq


def _rolamento(z, rp=12.0, rb=2.0, n=8, largura=6.0, r_furo=6.0, r_ext=18.0):
    """Anel interno (pista cilíndrica r=rp-rb), externo (pista r=rp+rb) e n esferas."""
    interno = cq.Workplane("XY").circle(rp - rb).circle(r_furo).extrude(largura).translate((0, 0, z))
    externo = cq.Workplane("XY").circle(r_ext).circle(rp + rb).extrude(largura).translate((0, 0, z))
    bolas = [cq.Workplane("XY").sphere(rb).translate((rp * math.cos(2 * math.pi * k / n),
                                                      rp * math.sin(2 * math.pi * k / n), z + largura / 2))
             for k in range(n)]
    return interno, externo, bolas


def eixo_em_mancais(tmp):
    """Carcaça com furo r=18 (2 rolamentos); eixo r=6 com colar r=10; flange
    preso ao colar por 2 parafusos (cabeça apoiada no flange, haste em furo de
    passagem r=1,75 do flange e furo roscado modelado r=1,25 no colar)."""
    asm = cq.Assembly()
    carcaca = cq.Workplane("XY").box(50, 50, 30, centered=(True, True, False)).faces(">Z").workplane() \
        .hole(36)
    asm.add(carcaca, name="carcaca")
    for k, z in enumerate((2.0, 22.0)):
        i, e, bolas = _rolamento(z)
        asm.add(i, name=f"anel_int_{k}").add(e, name=f"anel_ext_{k}")
        for m, b in enumerate(bolas):
            asm.add(b, name=f"esfera_{k}_{m}")
    eixo = cq.Workplane("XY").circle(6).extrude(40).union(
        cq.Workplane("XY").circle(10).extrude(5).translate((0, 0, 32)))
    for x in (-7.0, 7.0):
        eixo = eixo.cut(cq.Workplane("XY").center(x, 0).circle(1.25).extrude(4).translate((0, 0, 33)))
    asm.add(eixo, name="eixo")
    flange = cq.Workplane("XY").circle(14).circle(6).extrude(3).translate((0, 0, 37))
    for x in (-7.0, 7.0):
        flange = flange.cut(cq.Workplane("XY").center(x, 0).circle(1.75).extrude(3).translate((0, 0, 37)))
    asm.add(flange, name="flange")
    for k, x in enumerate((-7.0, 7.0)):
        p = cq.Workplane("XY").center(x, 0).circle(1.5).extrude(7).translate((0, 0, 33)) \
            .union(cq.Workplane("XY").center(x, 0).circle(2.6).extrude(2).translate((0, 0, 40)))
        asm.add(p, name=f"parafuso_{k}")
    caminho = Path(tmp) / "eixo_em_mancais.step"
    asm.save(str(caminho))
    return caminho


def placas_dois_pinos(tmp, pinos=2, apoio_solto=False, coaxial_com_folga=False):
    asm = cq.Assembly()
    base = cq.Workplane("XY").box(60, 30, 6, centered=(True, True, False))
    topo = cq.Workplane("XY").box(60, 30, 6, centered=(True, True, False)).translate((0, 0, 6))
    xs = [-20.0, 20.0][:pinos]
    for x in xs:
        base = base.cut(cq.Workplane("XY").center(x, 0).circle(2.0).extrude(6))
        topo = topo.cut(cq.Workplane("XY").center(x, 0).circle(2.0).extrude(6).translate((0, 0, 6)))
    asm.add(base, name="base").add(topo, name="topo")
    for k, x in enumerate(xs):
        asm.add(cq.Workplane("XY").center(x, 0).circle(2.0).extrude(12), name=f"pino_{k}")
    if apoio_solto:
        asm.add(cq.Workplane("XY").box(10, 10, 2, centered=(True, True, False)).translate((0, 0, 12)), name="apoiado")
    if coaxial_com_folga:
        # Disco coaxial ao pino 0, sem tocar nada (folga de 1 mm acima do topo)
        asm.add(cq.Workplane("XY").center(xs[0], 0).circle(5).circle(2.0).extrude(2).translate((0, 0, 13)),
                name="coaxial_solto")
    caminho = Path(tmp) / f"placas_{pinos}_{int(apoio_solto)}{int(coaxial_com_folga)}.step"
    asm.save(str(caminho))
    return caminho


def cicloide_pontos(R, Rr, E, N, n=2400):
    """Perfil clássico de disco cicloidal (N roletes, N−1 lóbulos), referencial do disco."""
    import numpy as np
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    psi = np.arctan2(np.sin((1 - N) * t), R / (E * N) - np.cos((1 - N) * t))
    x = R * np.cos(t) - Rr * np.cos(t + psi) - E * np.cos(N * t)
    y = -R * np.sin(t) + Rr * np.sin(t + psi) + E * np.sin(N * t)
    return np.c_[x, y]


def disco_lobulado(tmp, R=40.0, Rr=4.0, E=1.5, N=10, falso=False, fase=0.0):
    """Disco de perfil (cicloidal OU senoidal 'falso' com N−1 lóbulos e mesma
    amplitude média), furo central, excêntrico E em +x; N roletes (corpos
    separados, cilindro convexo r=Rr) a raio R. Devolve o caminho do STEP."""
    import numpy as np
    pts = cicloide_pontos(R, Rr, E, N)
    if falso:
        r = np.hypot(*pts.T)
        a = 0.5 * (r.max() - r.min())
        t = np.linspace(0, 2 * np.pi, len(pts), endpoint=False)
        rr = r.mean() + a * np.cos((N - 1) * t)
        pts = np.c_[rr * np.cos(t), rr * np.sin(t)]
    c, s = np.cos(fase), np.sin(fase)
    pts = pts @ np.array([[c, s], [-s, c]])
    disco = (cq.Workplane("XY").spline([tuple(p) for p in pts], periodic=True).close().extrude(5)
             .cut(cq.Workplane("XY").circle(8).extrude(5))).translate((E, 0, 0))
    # o furo central é o eixo próprio do disco (cilindro completo junto ao centroide)
    asm = cq.Assembly().add(disco, name="disco")
    for k in range(N):
        a = 2 * np.pi * k / N
        asm.add(cq.Workplane("XY").circle(Rr).extrude(5).translate((R * np.cos(a), R * np.sin(a), 0)),
                name=f"rolete_{k}")
    caminho = Path(tmp) / f"disco_{'falso' if falso else 'ciclo'}_{N}.step"
    asm.save(str(caminho))
    return caminho
