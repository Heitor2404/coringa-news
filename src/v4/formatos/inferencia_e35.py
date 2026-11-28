"""E35 — inferência genérica de juntas e pares superiores a partir do B-rep.

Entrada: corpos de `brep_e35.ler` (sem juntas na fonte). Saída: contrato
intermediário em que CADA elemento declara sua natureza de evidência:

- ``comprovado``: lido literalmente do arquivo (nome de produto, unidade, hash);
- ``derivado``: calculado da geometria com valores e tolerâncias registrados
  (eixo próprio de um corpo, par pino–rasgo, folgas);
- ``hipotese``: suposição necessária e não verificável na fonte (ex.: suporte
  fixo não modelado que segura os eixos).

Regras (todas por geometria, nenhuma por nome de peça ou de equipamento):
1. Eixo próprio: face cilíndrica completa (≥300°) cujo eixo passa mais perto
   do centroide do corpo; aceita se a distância ≤ 3% da maior dimensão.
2. Suporte: um corpo que tem furo/eixo coaxial ao eixo próprio de OUTRO corpo
   o sustenta (junta de revolução relativa). Se nenhum corpo sustenta, cria-se
   um suporte implícito (hipótese) e cada corpo gira no seu eixo próprio.
3. Par pino–rasgo: cilindro CONVEXO completo de A, paralelo ao eixo de A e fora
   dele (pino), contra par de faces planas de B paralelas ao eixo de B, com
   normais opostas voltadas uma para a outra (rasgo), largura entre 2r e 2r·1,25,
   sobreposição axial e alcance do círculo do pino na extensão do rasgo.
"""
from __future__ import annotations

import numpy as np

from . import multicorpo_e18 as M

TOL_PARALELO = 1e-6
TOL_COAXIAL_MM = 0.05


def fail(codigo):
    raise ValueError("E35-INF-" + codigo)


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def _dist_ponto_reta(p, o, d):
    w = p - o
    return float(np.linalg.norm(w - np.dot(w, d) * d))


def _orientar(d):
    """Sentido canônico para eixos (componente de maior módulo positiva)."""
    d = _unit(d)
    return d if d[np.argmax(np.abs(d))] > 0 else -d


def eixo_proprio(corpo):
    tam = max(np.subtract(corpo.caixa[1], corpo.caixa[0]))
    cands = [c for c in corpo.cilindros if c.extensao_graus >= 300]
    if not cands:
        return None
    melhor = min(cands, key=lambda c: _dist_ponto_reta(corpo.centroide, c.origem, c.eixo))
    dist = _dist_ponto_reta(corpo.centroide, melhor.origem, melhor.eixo)
    if dist > 0.03 * tam:
        return None
    d = _orientar(melhor.eixo)
    # ponto do eixo mais próximo do centroide (origem do referencial do corpo)
    o = melhor.origem + np.dot(corpo.centroide - melhor.origem, d) * d
    coax = [c for c in corpo.cilindros if np.linalg.norm(np.cross(c.eixo, d)) < TOL_PARALELO
            and _dist_ponto_reta(c.origem, o, d) < TOL_COAXIAL_MM]
    return dict(origem=o, eixo=d, raio_referencia=melhor.raio, concavo=melhor.concavo,
                distancia_centroide_mm=dist, faces_coaxiais=len(coax),
                evidencia="derivado", regra="cilindro completo mais próximo do centroide")


def pinos(corpo, eixo):
    out = []
    for c in corpo.cilindros:
        if c.concavo or c.extensao_graus < 300:
            continue
        if np.linalg.norm(np.cross(c.eixo, eixo["eixo"])) > TOL_PARALELO:
            continue
        rho = _dist_ponto_reta(c.origem, eixo["origem"], eixo["eixo"])
        if rho < 2 * c.raio:   # cubo/eixo do próprio corpo, não pino excêntrico
            continue
        centro = c.origem + np.dot(eixo["origem"] - c.origem, c.eixo) * c.eixo  # no plano do eixo
        z0 = np.dot(c.origem - eixo["origem"], eixo["eixo"])
        zs = sorted([z0 + c.zmin * np.dot(c.eixo, eixo["eixo"]), z0 + c.zmax * np.dot(c.eixo, eixo["eixo"])])
        out.append(dict(raio=c.raio, centro=centro, braco=rho, z=zs, evidencia="derivado"))
    return out


def rasgos(corpo, eixo, tol_ang=1e-6):
    e = eixo["eixo"]
    planos = [p for p in corpo.planos if abs(np.dot(p.normal, e)) < tol_ang]
    out = []
    for i, a in enumerate(planos):
        for b in planos[i + 1:]:
            if np.dot(a.normal, b.normal) > -1 + 1e-6:
                continue
            w = float(np.dot(b.centro - a.centro, a.normal))
            if w <= 0:                       # normais não se encaram: não é rasgo
                continue
            n = a.normal
            u = _orientar(np.cross(e, n))
            meio = (a.centro + b.centro) / 2
            # extensões ao longo da direção do rasgo e do eixo, relativas ao eixo do corpo
            ta = (a.vertices - eixo["origem"]) @ u
            tb = (b.vertices - eixo["origem"]) @ u
            t_lo, t_hi = max(ta.min(), tb.min()), min(ta.max(), tb.max())
            if t_hi - t_lo <= 0:
                continue
            za = (a.vertices - eixo["origem"]) @ e
            zb = (b.vertices - eixo["origem"]) @ e
            z_lo, z_hi = max(za.min(), zb.min()), min(za.max(), zb.max())
            if z_hi - z_lo <= 0:
                continue
            desvio = float(np.dot(meio - eixo["origem"], n))   # distância do eixo à linha média
            # Ponto da linha média no plano do eixo e sentido "para fora" do eixo
            ponto = eixo["origem"] + desvio * n
            if abs(t_lo) < abs(t_hi):
                sentido, t_in, t_out = u, t_lo, t_hi
            else:
                sentido, t_in, t_out = -u, -t_hi, -t_lo
            out.append(dict(largura=w, ponto=ponto, direcao=sentido, t_dentro=float(t_in),
                            t_boca=float(t_out), z=[float(z_lo), float(z_hi)],
                            radial=abs(desvio) < TOL_COAXIAL_MM, desvio_mm=desvio,
                            evidencia="derivado"))
    return out


def pares_pino_rasgo(corpos, eixos):
    pares = []
    for ia, A in enumerate(corpos):
        if eixos[ia] is None:
            continue
        for pin in pinos(A, eixos[ia]):
            for ib, B in enumerate(corpos):
                if ib == ia or eixos[ib] is None:
                    continue
                eB = eixos[ib]
                if np.linalg.norm(np.cross(eB["eixo"], eixos[ia]["eixo"])) > TOL_PARALELO:
                    continue
                c = _dist_ponto_reta(eixos[ia]["origem"], eB["origem"], eB["eixo"])
                compat = []
                for r in rasgos(B, eB):
                    folga = r["largura"] - 2 * pin["raio"]
                    if not (0 <= folga <= 0.25 * 2 * pin["raio"]):
                        continue
                    zp = [np.dot(eixos[ia]["origem"] - eB["origem"], eB["eixo"]) + z for z in pin["z"]]
                    if min(zp[1], r["z"][1]) - max(zp[0], r["z"][0]) <= 0:
                        continue
                    # o círculo do pino alcança a faixa radial do rasgo?
                    if not (c - pin["braco"] <= r["t_boca"] and c + pin["braco"] >= r["t_dentro"] - pin["raio"]):
                        continue
                    compat.append(dict(r, folga_mm=folga))
                if compat:
                    pares.append(dict(tipo="pino_rasgo", corpo_pino=ia, corpo_rasgo=ib, pino=pin,
                                      rasgos=compat, distancia_eixos_mm=c, evidencia="derivado"))
    return pares


def suportes(corpos, eixos):
    """Arestas corpo-suporte → corpo-sustentado por furo/eixo coaxial."""
    arestas = []
    for ib, B in enumerate(corpos):
        if eixos[ib] is None:
            continue
        for ia, A in enumerate(corpos):
            if ia == ib:
                continue
            for c in A.cilindros:
                if c.extensao_graus < 300 or np.linalg.norm(np.cross(c.eixo, eixos[ib]["eixo"])) > TOL_PARALELO:
                    continue
                if _dist_ponto_reta(c.origem, eixos[ib]["origem"], eixos[ib]["eixo"]) < TOL_COAXIAL_MM:
                    arestas.append((ia, ib))
                    break
    return arestas


def diagnostico(leitura):
    """O que a geometria permitiu entender, mesmo quando o contrato não fecha."""
    corpos = leitura["corpos"]
    eixos = [eixo_proprio(c) for c in corpos]
    grupos = []
    for i, e in enumerate(eixos):
        if e is None:
            continue
        for g in grupos:
            e0 = eixos[g[0]]
            if (np.linalg.norm(np.cross(e0["eixo"], e["eixo"])) < TOL_PARALELO
                    and _dist_ponto_reta(e["origem"], e0["origem"], e0["eixo"]) < TOL_COAXIAL_MM):
                g.append(i)
                break
        else:
            grupos.append([i])
    paralelos = [(a, b) for ai, a in enumerate(grupos) for b in grupos[ai + 1:]
                 if np.linalg.norm(np.cross(eixos[a[0]]["eixo"], eixos[b[0]]["eixo"])) < TOL_PARALELO]
    return dict(corpos=len(corpos), com_eixo_proprio=sum(e is not None for e in eixos),
                grupos_coaxiais=[[corpos[i].nome for i in g] for g in grupos if len(g) > 1][:12],
                n_grupos_coaxiais=len(grupos),
                pares_de_eixos_paralelos_distintos=len(paralelos),
                excentricidades_mm=sorted({round(_dist_ponto_reta(eixos[a[0]]["origem"], eixos[b[0]]["origem"],
                                                                   eixos[b[0]]["eixo"]), 3)
                                           for a, b in paralelos})[:12],
                arestas_de_suporte=len(suportes(corpos, eixos)),
                pares_pino_rasgo=len(pares_pino_rasgo(corpos, eixos)),
                sem_eixo=[c.nome for c, e in zip(corpos, eixos) if e is None][:12])


def contrato(leitura):
    corpos = leitura["corpos"]
    eixos = [eixo_proprio(c) for c in corpos]
    pares = pares_pino_rasgo(corpos, eixos)
    sup = suportes(corpos, eixos)
    juntas, hipoteses = [], []
    if sup:
        fail("SUPORTE_MODELADO_AINDA_NAO_IMPLEMENTADO")
    moveis = [i for i, e in enumerate(eixos) if e is not None]
    sem_eixo = [corpos[i].nome for i, e in enumerate(eixos) if e is None]
    if sem_eixo:
        fail("CORPO_SEM_EIXO_PROPRIO:" + ",".join(sem_eixo))
    hipoteses.append(dict(codigo="SUPORTE_IMPLICITO", evidencia="hipotese",
                          texto="Nenhum corpo da fonte sustenta os eixos; supõe-se um suporte "
                                "fixo não modelado e cada corpo gira no seu eixo próprio."))
    for i in moveis:
        juntas.append(dict(tipo="revolucao", corpo=i, pai="suporte_implicito",
                           origem_mm=eixos[i]["origem"].tolist(), eixo=eixos[i]["eixo"].tolist(),
                           evidencia="derivado+hipotese", base=eixos[i]))
    return dict(unidade=leitura["unidade"], sha256=leitura["sha256"],
                corpos=[dict(indice=c.indice, nome_fonte=c.nome, evidencia_nome="comprovado",
                             volume_mm3=c.volume, eixo=None if eixos[c.indice] is None else
                             {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in eixos[c.indice].items()})
                        for c in corpos],
                juntas=juntas, pares=pares, hipoteses=hipoteses, _eixos=eixos)


def montagem(leitura, ctr):
    """Contrato → Montagem E18 (metros). Suporte implícito é a raiz fixa."""
    f = 1e-3   # OCP entrega mm; a unidade do arquivo fica no QA
    corpos = leitura["corpos"]
    nomes = ["suporte_implicito"] + [f"c{c.indice}:{c.nome}" for c in corpos]
    pai = [-1] + [0] * len(corpos)
    eixos = ctr["_eixos"]
    local = [np.eye(4)] + [M.pose(np.eye(3), eixos[c.indice]["origem"] * f) for c in corpos]
    juntas = [M.Junta(nome=f"rev_c{c.indice}", corpo=1 + c.indice, tipo="hinge",
                      eixo=eixos[c.indice]["eixo"], ponto=np.zeros(3), limite=None,
                      rigidez=0.0, mola_ref=0.0, q0=0.0) for c in corpos]
    visuais = [M.Visual(1 + c.indice, c.nome, np.eye(4), c.vertices * f - eixos[c.indice]["origem"] * f,
                        c.faces, np.array([.72, .76, .79, 1.])) for c in corpos]
    mont = M.Montagem(nomes, pai, local, juntas, [], visuais, {}, {}, None, [])
    mont.chaves["qpos0"] = np.zeros(mont.nq)
    return mont
