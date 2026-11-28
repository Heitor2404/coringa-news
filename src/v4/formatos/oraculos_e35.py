"""E35 — identidade geométrica por classe, auditoria exata no B-rep e oráculos.

Fora do solver. Três coisas:
1. ``classe_da_consulta`` + ``assinatura``: a consulta diz qual CLASSE se
   espera; a geometria inferida tem de exibir a assinatura da classe, senão a
   identidade não está confirmada (o texto do repositório não basta).
2. ``interferencia_brep``: volume EXATO da interseção booleana (OCC) entre os
   sólidos originais nas poses do solver. Toque de faces dá zero (o FCL sobre
   malhas conta toque e erro de corda como colisão).
3. ``genebra_classico``: conferência com a relação de livro-texto. Atenção: a
   relação do engate é a própria geometria do pino sobre a reta radial, então
   ela confere a montagem/ativação, NÃO é independente da restrição do solver.
   Independentes: avanço por volta, fração de repouso, cotas do autor.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


def fail(codigo):
    raise ValueError("E35-ORACULO-" + codigo)


def carregar_classes(caminho="benchmarks/e35_classes_mecanismo.json"):
    return json.loads(Path(caminho).read_text())["classes"]


def classe_da_consulta(consulta, classes):
    t = consulta.lower()
    achadas = [k for k, c in classes.items() if any(term in t for term in c["termos"])]
    if len(achadas) != 1:
        return None
    return achadas[0]


def _ang(v, ref, eixo):
    return math.atan2(float(np.dot(np.cross(ref, v), eixo)), float(np.dot(ref, v)))


def assinatura(classe, cfg, ctr):
    """Confere a assinatura geométrica da classe no contrato inferido."""
    a = cfg["assinatura"]
    if a["par"] != "pino_rasgo":
        return dict(confirmada=False, motivo="PAR_SUPERIOR_NAO_SUPORTADO:" + a["par"])
    melhores = []
    for p in ctr["pares"]:
        rs = [r for r in p["rasgos"] if r["radial"] or not a["rasgos_radiais"]]
        n = len(rs)
        if n < a["rasgos_min"]:
            continue
        eixo = np.asarray(ctr["_eixos"][p["corpo_rasgo"]]["eixo"])
        ang = sorted((_ang(r["direcao"], rs[0]["direcao"], eixo) % (2 * math.pi)) for r in rs)
        passos = np.diff(ang + [ang[0] + 2 * math.pi])
        desvio = float(np.degrees(np.abs(passos - 2 * math.pi / n).max()))
        c, braco = p["distancia_eixos_mm"], p["pino"]["braco"]
        ortog = abs(c * math.sin(math.pi / n) - braco) / braco
        ok = desvio <= a["espacamento_uniforme_tol_graus"] and ortog <= a["entrada_ortogonal_tol_rel"]
        melhores.append(dict(confirmada=ok, n=n, desvio_espacamento_graus=desvio,
                             erro_rel_entrada_ortogonal=ortog, c_mm=c, a_mm=braco,
                             raio_pino_mm=p["pino"]["raio"], largura_rasgo_mm=rs[0]["largura"],
                             corpo_pino=p["corpo_pino"], corpo_rasgo=p["corpo_rasgo"], evidencia="derivado"))
    if not melhores:
        return dict(confirmada=False, motivo="SEM_PAR_COM_RASGOS_SUFICIENTES")
    m = max(melhores, key=lambda x: (x["confirmada"], x["n"]))
    if not m["confirmada"]:
        m["motivo"] = "ASSINATURA_FORA_DA_TOLERANCIA"
    return m


# --------------------------------------------------------------- B-rep exato
def _mover(forma, T):
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    t = gp_Trsf()
    R, p = T[:3, :3], T[:3, 3]
    t.SetValues(*R[0], p[0], *R[1], p[1], *R[2], p[2])
    return BRepBuilderAPI_Transform(forma, t, True).Shape()


def _volume(forma):
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(forma, g)
    return float(g.Mass())


def interferencia_brep(leitura, mont, qs, indices=None):
    """Volume de interseção (mm³) por par de corpos e por quadro amostrado."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    corpos = leitura["corpos"]
    X0 = mont.poses(np.zeros(mont.nq))
    indices = range(len(qs)) if indices is None else indices
    por_quadro, pior = {}, dict(volume_mm3=0.0)
    for i in indices:
        X = mont.poses(qs[i])
        formas = []
        for c in corpos:
            T = X[1 + c.indice] @ np.linalg.inv(X0[1 + c.indice])
            T = T.copy()
            T[:3, 3] *= 1000.0
            formas.append(_mover(c.forma.wrapped, T))
        for a in range(len(formas)):
            for b in range(a + 1, len(formas)):
                com = BRepAlgoAPI_Common(formas[a], formas[b]).Shape()
                v = _volume(com)
                if v > 1e-6:
                    por_quadro.setdefault(str(i), []).append([corpos[a].nome, corpos[b].nome, v])
                    if v > pior["volume_mm3"]:
                        bb = Bnd_Box()
                        BRepBndLib.Add_s(com, bb)
                        x0, y0, z0, x1, y1, z1 = bb.Get()
                        pior = dict(volume_mm3=v, quadro=i, par=[corpos[a].nome, corpos[b].nome],
                                    caixa_intersecao_mm=[x1 - x0, y1 - y0, z1 - z0])
    return dict(metodo="interseção booleana exata OCC entre sólidos originais posicionados",
                quadros_auditados=len(list(indices)), quadros_com_interferencia=len(por_quadro),
                pior=pior, por_quadro=por_quadro)


# --------------------------------------------------------------- Genebra
def genebra_classico(mont, traj, par, ctr, sig):
    """Conferências: (a) relação do engate; (b) avanço por volta = 2π/n;
    (c) fração de repouso = (π + 2π/n)/(2π)."""
    n = sig["n"]
    ia, ib = 1 + par.a - 1, 1 + par.b - 1
    e = np.asarray(ctr["_eixos"][sig["corpo_rasgo"]]["eixo"])
    erros, engate = [], []
    for q, info in traj:
        X = mont.poses(q)
        D, S = X[par.a][:3, 3], X[par.b][:3, 3]
        P = X[par.a][:3, :3] @ par.pino_local + X[par.a][:3, 3]
        ativo = bool(info["contatos_ativos"])
        engate.append(ativo)
        if not ativo:
            continue
        theta = _ang(P - D, S - D, e)
        beta_a = math.atan2(sig["a_mm"] * math.sin(theta), sig["c_mm"] - sig["a_mm"] * math.cos(theta))
        # β medido: direção do rasgo ativo (mundo) relativa à reta S→D
        i_par, k = info["contatos_ativos"][0]
        r = par.rasgos[k]
        u = X[par.b][:3, :3] @ r["dir"]
        beta_m = _ang(u, D - S, e)
        erros.append(abs((beta_m + beta_a + math.pi) % (2 * math.pi) - math.pi))  # sentidos opostos
    ang = np.unwrap(np.array([q[par.b - 1 + 0] for q, _ in traj]))
    avanco = abs(ang[-1] - ang[0])
    entrada = np.unwrap(np.array([q[par.a - 1] for q, _ in traj]))
    voltas = abs(entrada[-1] - entrada[0]) / (2 * math.pi)
    repouso = 1 - float(np.mean(engate))
    return dict(relacao_engate_erro_max_graus=float(np.degrees(max(erros))) if erros else None,
                quadros_engate=len(erros),
                avanco_por_volta_graus=float(np.degrees(avanco / max(voltas, 1e-9))),
                avanco_esperado_graus=360.0 / n,
                fracao_repouso=repouso, fracao_repouso_esperada=(math.pi + 2 * math.pi / n) / (2 * math.pi),
                independencia="relacao_engate NÃO é independente da restrição pino-sobre-reta; avanço "
                              "e repouso emergem da ativação/desativação do contato")
