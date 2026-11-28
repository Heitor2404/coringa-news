"""E41 — grafo de vínculos com evidência, agrupamento rígido e suportes.

Entrada: sólidos de `brep_e35.ler` (TODOS; nada é removido pelo nome). Saída:
grupos rígidos, estrutura de referência, articulações de revolução e corpos
sem vínculo comprovado — cada relação com a evidência geométrica usada.

Regras (geometria; nomes de produto só entram como texto de apoio no QA):

* AJUSTE (revolução): cilindro convexo de A e côncavo de B, eixos paralelos e
  coincidentes (≤ TOL_EIXO), raios iguais dentro de TOL_AJUSTE, sobreposição
  axial. Um ajuste nominal NÃO prova fixação: é modelado como o par mais
  permissivo compatível (revolução em torno do eixo). Rigidez só aparece se
  outra evidência bloquear a rotação.
* FIXADOR (rígido): corpo F com haste cilíndrica convexa no eixo X que entra
  em furos coaxiais (ajuste, folga até 35% do raio, ou furo menor = rosca
  modelada) de ≥ 2 corpos distintos, E com face plana perpendicular a X em
  contato (coplanar, normais opostas, sobre o eixo) com um deles (aperto da
  cabeça/porca). Une F e os corpos atravessados num grupo rígido.
* DOIS EIXOS (rígido, derivado): dois ajustes entre os MESMOS grupos com eixos
  não coincidentes bloqueiam a rotação relativa (ex.: dois pinos-guia).
* ROLAMENTO: ≥ 5 corpos esféricos de mesmo raio com centros num círculo
  (resíduo ≤ TOL_CIRCULO) definem eixo, raio primitivo e raio da esfera; os
  anéis são os corpos coaxiais cujas superfícies de pista (toro ou cilindro)
  tocam as esferas por dentro e por fora. Gera revolução anel interno × anel
  externo. As esferas e corpos só ligados a elas são "elementos rolantes".
* Corpos sem nenhuma dessas evidências ficam SEM VÍNCULO COMPROVADO (listados).
  Coaxialidade e proximidade sozinhas nunca unem corpos.
"""
from __future__ import annotations

import numpy as np

TOL_EIXO = 0.02        # mm: distância entre eixos para "coincidentes"
TOL_PARALELO = 1e-5    # |sin| entre direções
TOL_AJUSTE = 0.05      # mm: diferença de raio para ajuste nominal
FOLGA_PASSAGEM = 0.35  # fração do raio para furo de passagem de fixador
TOL_PLANO = 0.02       # mm: faces coplanares
TOL_CIRCULO = 0.02     # mm: centros de esferas num círculo


def _u(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def _dist_reta(p, o, d):
    w = np.asarray(p, float) - o
    return float(np.linalg.norm(w - np.dot(w, d) * d))


def _paralelos(a, b):
    return np.linalg.norm(np.cross(a, b)) < TOL_PARALELO


def _coaxiais(c1, c2):
    return _paralelos(c1.eixo, c2.eixo) and _dist_reta(c2.origem, c1.origem, c1.eixo) < TOL_EIXO


def _intervalo(c, o, d):
    """Extensão do cilindro c projetada no eixo (o, d)."""
    z0 = np.dot(c.origem - o, d)
    s = np.dot(c.eixo, d)
    a, b = z0 + c.zmin * s, z0 + c.zmax * s
    return min(a, b), max(a, b)


def _sobrepoe(i1, i2, minimo=0.1):
    return min(i1[1], i2[1]) - max(i1[0], i2[0]) > minimo


def _caixas_proximas(c1, c2, folga=0.5):
    a0, a1 = np.array(c1.caixa[0]), np.array(c1.caixa[1])
    b0, b1 = np.array(c2.caixa[0]), np.array(c2.caixa[1])
    return bool(np.all(a0 - folga <= b1) and np.all(b0 - folga <= a1))


class UniaoBusca:
    def __init__(self, n):
        self.p = list(range(n))

    def achar(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def unir(self, a, b):
        a, b = self.achar(a), self.achar(b)
        if a != b:
            self.p[max(a, b)] = min(a, b)
        return a != b


# ------------------------------------------------------------- primitivas
def esferico(c):
    return bool(c.esferas) and not c.cilindros and not c.planos and not c.toros


def ajustes(corpos, pares):
    """Ajustes nominais (revolução) e engates de haste em furo (para fixador)."""
    aj, hastes = [], []
    for i, j in pares:
        for a, b in ((i, j), (j, i)):
            for ca in corpos[a].cilindros:
                if ca.concavo:
                    continue
                for cb in corpos[b].cilindros:
                    if not cb.concavo or not _coaxiais(ca, cb):
                        continue
                    o, d = ca.origem, _u(ca.eixo)
                    if not _sobrepoe(_intervalo(ca, o, d), _intervalo(cb, o, d)):
                        continue
                    dr = cb.raio - ca.raio
                    reg = dict(convexo=a, concavo=b, raio=ca.raio, folga_mm=dr, eixo=d, origem=o,
                               intervalo=_intervalo(ca, o, d))
                    if abs(dr) <= TOL_AJUSTE:
                        aj.append(dict(reg, tipo="ajuste"))
                    elif -0.25 * ca.raio <= dr < -TOL_AJUSTE:
                        # interferência: rosca modelada OU ajuste prensado — ambíguo;
                        # fora de fixador comprovado vale o par mais permissivo (revolução)
                        aj.append(dict(reg, tipo="ajuste_interferencia"))
                    if -0.25 * ca.raio <= dr <= FOLGA_PASSAGEM * ca.raio:
                        hastes.append(dict(reg, tipo="rosca_modelada" if dr < -TOL_AJUSTE else
                                           "ajuste" if abs(dr) <= TOL_AJUSTE else "passagem"))
    return aj, hastes


def contatos_planos(corpos, pares):
    out = []
    for i, j in pares:
        for pa in corpos[i].planos:
            for pb in corpos[j].planos:
                if np.dot(pa.normal, pb.normal) > -1 + 1e-6:
                    continue
                if abs(np.dot(pb.centro - pa.centro, pa.normal)) > TOL_PLANO:
                    continue
                ra, rb = np.sqrt(pa.area / np.pi), np.sqrt(pb.area / np.pi)
                w = pb.centro - pa.centro
                w = w - np.dot(w, pa.normal) * pa.normal
                if np.linalg.norm(w) <= ra + rb:
                    out.append(dict(a=i, b=j, normal=pa.normal, ponto=pa.centro))
    return out


def fixadores(corpos, hastes, planos):
    """Junta aparafusada (rígida): F com ROSCA MODELADA (furo coaxial menor que
    a haste) num corpo H2 e face de aperto perpendicular ao eixo com um corpo
    H1 atravessado pela mesma haste (H1 pode ser H2, ex.: parafuso de ombro).
    Rosca só no diâmetro nominal não prova aperto: vira 'possivel_fixador'."""
    por_eixo = {}
    for h in hastes:
        d = h["eixo"]
        chave = (h["convexo"], tuple(np.round(h["origem"] - np.dot(h["origem"], d) * d, 2)),
                 tuple(np.round(np.abs(d), 4)))
        por_eixo.setdefault(chave, []).append(h)
    out, possiveis = [], []
    for (f, _, _), hs in por_eixo.items():
        d, o = hs[0]["eixo"], hs[0]["origem"]
        atravessados = sorted({h["concavo"] for h in hs})
        roscados = sorted({h["concavo"] for h in hs if h["tipo"] == "rosca_modelada"})
        aperto = sorted({(p["b"] if p["a"] == f else p["a"]) for p in planos
                         if f in (p["a"], p["b"]) and abs(abs(np.dot(p["normal"], d)) - 1) < 1e-6
                         and (p["b"] if p["a"] == f else p["a"]) in atravessados})
        # porte de fixador: pequeno frente a CADA corpo que aperta/rosqueia
        envolvidos = sorted(set(roscados) | set(aperto))
        vol_f = corpos[f].volume
        r_haste = min(h["raio"] for h in hs)
        porte = all(vol_f <= 0.25 * corpos[b].volume and
                    r_haste <= 0.2 * max(np.subtract(corpos[b].caixa[1], corpos[b].caixa[0])) for b in envolvidos)
        if roscados and aperto and not porte:
            possiveis.append(dict(corpo=f, atravessados=atravessados, aperto_com=aperto,
                                  motivo="interferência + face, mas sem porte de fixador (pode ser ajuste prensado)"))
            continue
        if roscados and aperto:
            out.append(dict(fixador=f, corpos=sorted(set(roscados) | set(aperto)), eixo=d.tolist(),
                            origem=o.tolist(), roscado_em=roscados, aperto_com=aperto,
                            evidencia="rosca modelada (furo < haste) + face de aperto no mesmo eixo"))
        elif aperto and len(atravessados) >= 1:
            possiveis.append(dict(corpo=f, atravessados=atravessados, aperto_com=aperto,
                                  motivo="aperto por face sem rosca modelada: fixação não comprovada"))
    return out, possiveis


def _ajusta_circulo(P):
    m = P.mean(0)
    _, _, vt = np.linalg.svd(P - m)
    n = _u(vt[2])
    e1, e2 = vt[0], vt[1]
    Q = np.c_[(P - m) @ e1, (P - m) @ e2]
    A = np.c_[2 * Q, np.ones(len(Q))]
    sol = np.linalg.lstsq(A, (Q ** 2).sum(1), rcond=None)[0]
    c2 = sol[:2]
    rp = float(np.sqrt(max(sol[2] + c2 @ c2, 0.0)))
    centro = m + c2[0] * e1 + c2[1] * e2
    res = float(np.abs(np.linalg.norm(Q - c2, axis=1) - rp).max())
    plan = float(np.abs((P - m) @ n).max())
    return centro, n, rp, res, plan


def conjuntos_rolantes(corpos, minimo=5):
    """Esferas de mesmo raio em círculo. Agrupa por vizinhança com limiares
    decrescentes (8r → 3r) e só aceita componentes cujo círculo ajusta."""
    restantes = {i for i, c in enumerate(corpos) if esferico(c)}
    out = []
    for fator in (8.0, 6.0, 4.5, 3.0):
        for raio in sorted({round(corpos[i].esferas[0].raio, 6) for i in restantes}):
            bolas = [i for i in restantes if abs(corpos[i].esferas[0].raio - raio) < 1e-6]
            uf = UniaoBusca(len(bolas))
            C = np.array([corpos[i].esferas[0].centro for i in bolas])
            for a in range(len(bolas)):
                d = np.linalg.norm(C - C[a], axis=1)
                for b in np.nonzero(d < fator * raio)[0]:
                    uf.unir(a, int(b))
            comps = {}
            for a in range(len(bolas)):
                comps.setdefault(uf.achar(a), []).append(bolas[a])
            for grupo in comps.values():
                if len(grupo) < minimo:
                    continue
                P = np.array([corpos[k].esferas[0].centro for k in grupo])
                centro, n, rp, res, plan = _ajusta_circulo(P)
                if res > TOL_CIRCULO or plan > TOL_CIRCULO or rp <= raio:
                    continue
                out.append(dict(bolas=sorted(grupo), raio_bola=raio, raio_primitivo=rp, centro=centro, eixo=n,
                                residuo_circulo_mm=res, residuo_plano_mm=plan))
                restantes -= set(grupo)
    return out


def aneis(corpos, conj, candidatos):
    """Anéis interno/externo de um conjunto rolante.

    Pista = toro coaxial (raio maior ≈ raio primitivo, raio menor ≈ raio da
    esfera) ou cilindro coaxial tangente às esferas (r = rp ∓ rb). Lado: anel
    INTERNO tem todas as superfícies cilíndricas coaxiais abaixo do raio
    primitivo; EXTERNO, todas acima."""
    o, d, rp, rb = conj["centro"], conj["eixo"], conj["raio_primitivo"], conj["raio_bola"]
    interno, externo = [], []
    for k in candidatos:
        c = corpos[k]
        if esferico(c):
            continue
        pista = any(_paralelos(t.eixo, d) and _dist_reta(t.centro, o, d) < TOL_EIXO
                    and abs(np.dot(t.centro - o, d)) < rb and abs(t.raio_maior - rp) <= 0.6 * rb
                    and abs(t.raio_menor - rb) <= 0.15 * rb for t in c.toros)
        pista = pista or any(_paralelos(cy.eixo, d) and _dist_reta(cy.origem, o, d) < TOL_EIXO
                             and min(abs(cy.raio - (rp - rb)), abs(cy.raio - (rp + rb))) <= 0.05 * rb
                             for cy in c.cilindros)
        if not pista:
            continue
        raios = [cy.raio for cy in c.cilindros if _paralelos(cy.eixo, d) and _dist_reta(cy.origem, o, d) < TOL_EIXO]
        if raios and max(raios) < rp:
            interno.append(k)
        elif raios and min(raios) > rp:
            externo.append(k)
    return sorted(set(interno)), sorted(set(externo))


# ------------------------------------------------------------- modelo cinemático
def _grupos(uf, n):
    g = {}
    for i in range(n):
        g.setdefault(uf.achar(i), []).append(i)
    return g


def modelo(corpos, uf, arts, base=None, f=1e-3):
    """Montagem E18 com um corpo por grupo rígido e uma revolução por eixo de
    articulação entre grupos (árvore a partir da base; demais arestas viram
    fechamento por dois pontos do eixo — 'connect' ×2). Referencial de todos
    os grupos = mundo na pose de referência. Devolve (mont, ids_grupo, info)."""
    from . import multicorpo_e18 as M
    g = _grupos(uf, len(corpos))
    arestas = []
    vistos = set()
    for x in arts:
        ga, gb = uf.achar(x["a"]), uf.achar(x["b"])
        if ga == gb:
            continue
        d = _u(x["eixo"])
        o = np.asarray(x["origem"], float)
        chave = (min(ga, gb), max(ga, gb), tuple(np.round(np.abs(d), 4)), tuple(np.round(o - np.dot(o, d) * d, 2)))
        if chave in vistos:
            continue
        vistos.add(chave)
        arestas.append((ga, gb, d, o, x["tipo"]))
    # rolamento (elementos rolantes comprovados) primeiro: é a interface rotativa preferida da árvore
    arestas.sort(key=lambda e: 0 if e[4] == "rolamento" else 1)
    ligados = {e[0] for e in arestas} | {e[1] for e in arestas}
    if base is None:
        vol = lambda gid: max(np.prod(np.subtract(corpos[i].caixa[1], corpos[i].caixa[0])) for i in g[gid])
        base = max(ligados or g, key=vol)
    nomes, idx = ["mundo"], {}
    pai, local, juntas, iguais = [-1], [np.eye(4)], [], []
    nomes.append(f"g{base}")
    idx[base] = 1
    pai.append(0)
    local.append(np.eye(4))
    usadas = set()
    fila = [base]
    while fila:
        atual = fila.pop(0)
        for k, (a, b, d, o, tipo) in enumerate(arestas):
            if k in usadas or atual not in (a, b):
                continue
            filho = b if a == atual else a
            if filho in idx:
                continue
            usadas.add(k)
            idx[filho] = len(nomes)
            nomes.append(f"g{filho}")
            pai.append(idx[atual])
            local.append(np.eye(4))
            juntas.append(M.Junta(nome=f"{tipo}#{k}", corpo=idx[filho], tipo="hinge", eixo=d, ponto=o * f,
                                  limite=None, rigidez=0.0, mola_ref=0.0, q0=0.0))
            fila.append(filho)
    for k, (a, b, d, o, _) in enumerate(arestas):
        if k in usadas or a not in idx or b not in idx:
            continue
        for t in (0.0, 10.0):
            pt = (o + t * d) * f
            iguais.append(M.Igualdade("connect", idx[a], idx[b], np.r_[pt, pt]))
    mont = M.Montagem(nomes, pai, local, juntas, iguais, [], {}, {}, None, [])
    mont.chaves["qpos0"] = np.zeros(mont.nq)
    return mont, idx, dict(base=int(base), arestas=len(arestas), fora_do_modelo=sorted(set(g) - set(idx)))


def mobilidade_relativa(mont, h=1e-6):
    """Espaço nulo das restrições na referência e torção de cada corpo por
    direção admissível: (Z, T[corpo, 6, k])."""
    from . import multicorpo_e18 as M
    from scipy.spatial.transform import Rotation
    q0 = np.zeros(mont.nq)
    if not mont.igualdades:
        Z = np.eye(mont.nq)
    else:
        ref = mont.referencia_weld()
        J = M.jacobiano(lambda x: mont.residuo(x, ref), q0)
        _, sv, vt = np.linalg.svd(J)
        r = int((sv > 1e-7 * max(1.0, sv[0])).sum())
        Z = vt[r:].T
    nb = len(mont.corpos)
    T = np.zeros((nb, 6, Z.shape[1]))
    for c in range(Z.shape[1]):
        Xp, Xm = mont.poses(q0 + h * Z[:, c]), mont.poses(q0 - h * Z[:, c])
        for b in range(nb):
            T[b, :3, c] = (Xp[b][:3, 3] - Xm[b][:3, 3]) / (2 * h)
            T[b, 3:, c] = Rotation.from_matrix(Xp[b][:3, :3] @ Xm[b][:3, :3].T).as_rotvec() / (2 * h)
    return Z, T


def fundir_por_mobilidade(corpos, uf, arts, tol=1e-6):
    """Funde grupos sem movimento relativo admissível (rigidez DERIVADA das
    restrições, ex.: duas placas ligadas por dois pinos). Itera até estável."""
    fusoes = []
    while True:
        mont, idx, _ = modelo(corpos, uf, arts)
        if mont.nq == 0:
            return fusoes
        Z, T = mobilidade_relativa(mont)
        inv = {v: k for k, v in idx.items()}
        mudou = False
        for a in range(1, len(mont.corpos)):
            for b in range(a + 1, len(mont.corpos)):
                rel = T[b] - T[a]
                # velocidade relativa do ponto de B sobre a origem do mundo + rotação relativa
                if Z.shape[1] == 0 or np.abs(rel).max() < tol:
                    if uf.unir(inv[a], inv[b]):
                        fusoes.append(dict(tipo="sem_movimento_relativo", grupos=[int(inv[a]), int(inv[b])],
                                           evidencia="nenhuma direção admissível das restrições move um em "
                                                     "relação ao outro (posto do Jacobiano na referência)"))
                        mudou = True
            if mudou:
                break
        if not mudou:
            return fusoes


# ------------------------------------------------------------- análise
def analisar(leitura, folga_caixa=0.5):
    corpos = leitura["corpos"]
    n = len(corpos)
    pares = [(i, j) for i in range(n) for j in range(i + 1, n) if _caixas_proximas(corpos[i], corpos[j], folga_caixa)]
    aj, hastes = ajustes(corpos, pares)
    planos = contatos_planos(corpos, pares)
    fix, possiveis = fixadores(corpos, hastes, planos)
    rol = conjuntos_rolantes(corpos)
    uf = UniaoBusca(n)
    rigidas = []
    for f in fix:
        for b in f["corpos"]:
            uf.unir(f["fixador"], b)
        rigidas.append(dict(tipo="fixador", **f))
    rolantes = set()
    arts = []   # articulações candidatas entre corpos (depois entre grupos)
    for r in rol:
        rolantes |= set(r["bolas"])
        viz = sorted({j for b in r["bolas"] for j in range(n) if j not in r["bolas"]
                      and _caixas_proximas(corpos[b], corpos[j], 0.05)})
        ins, outs = aneis(corpos, r, viz)
        r.update(aneis_internos=ins, aneis_externos=outs)
        # corpos que só tocam as bolas (gaiola/blindagem sem outra evidência) ficam rolantes
        if len(ins) >= 1 and len(outs) >= 1:
            arts.append(dict(tipo="rolamento", a=ins[0], b=outs[0], eixo=r["eixo"], origem=r["centro"],
                             evidencia=f"{len(r['bolas'])} esferas r={r['raio_bola']:.3f} mm em círculo "
                                       f"r={r['raio_primitivo']:.3f} mm (resíduo {r['residuo_circulo_mm']:.1e})"))
        else:
            r["incompleto"] = "ANEIS_NAO_IDENTIFICADOS"
    for a in aj:
        if a["convexo"] in rolantes or a["concavo"] in rolantes:
            continue
        arts.append(dict(tipo=a["tipo"], a=a["concavo"], b=a["convexo"], eixo=a["eixo"], origem=a["origem"],
                         evidencia=f"{a['tipo']} coaxial r={a['raio']:.3f} mm, folga {a['folga_mm']:.3f} mm"))
    rigidas_por_mobilidade = fundir_por_mobilidade(corpos, uf, arts)
    rigidas += rigidas_por_mobilidade
    grupos = {}
    for i in range(n):
        grupos.setdefault(uf.achar(i), []).append(i)
    ligados = set()
    for f in fix:
        ligados |= {f["fixador"], *f["corpos"]}
    juntas = []
    vistos = set()
    for x in arts:
        ga, gb = uf.achar(x["a"]), uf.achar(x["b"])
        if ga == gb:
            continue
        ligados |= {x["a"], x["b"]}
        chave = (min(ga, gb), max(ga, gb), tuple(np.round(np.abs(x["eixo"]), 4)),
                 tuple(np.round(x["origem"] - np.dot(x["origem"], x["eixo"]) * x["eixo"], 2)))
        if chave in vistos:     # mesmo eixo entre os mesmos grupos: redundante
            continue
        vistos.add(chave)
        juntas.append(dict(x, grupo_a=int(ga), grupo_b=int(gb)))
    sem_vinculo = [i for i in range(n) if i not in ligados and i not in rolantes and len(grupos[uf.achar(i)]) == 1]
    return dict(corpos=n, pares_proximos=len(pares), ajustes=len(aj), contatos_planos=len(planos),
                possiveis_fixadores=possiveis, articulacoes=arts,
                rigidas=rigidas, rolamentos=rol, juntas=juntas,
                grupos={int(k): v for k, v in grupos.items()}, rolantes=sorted(rolantes),
                sem_vinculo=sem_vinculo)


def resumo(leitura, an):
    corpos = leitura["corpos"]
    nome = lambda i: corpos[i].nome
    multi = {g: m for g, m in an["grupos"].items() if len(m) > 1}
    return dict(corpos=an["corpos"], grupos_rigidos_multicorpo=len(multi),
                grupos=[dict(id=g, n=len(m), exemplos=[nome(i) for i in m[:6]]) for g, m in
                        sorted(multi.items(), key=lambda kv: -len(kv[1]))[:20]],
                juntas=[dict(tipo=j["tipo"], a=nome(j["a"]), b=nome(j["b"]), evidencia=j["evidencia"])
                        for j in an["juntas"]][:60],
                n_juntas=len(an["juntas"]), rolamentos=len(an["rolamentos"]),
                rolamentos_incompletos=sum("incompleto" in r for r in an["rolamentos"]),
                fixacoes=sum(r["tipo"] == "fixador" for r in an["rigidas"]),
                rigidez_por_dois_eixos=sum(r["tipo"] == "dois_eixos" for r in an["rigidas"]),
                sem_vinculo=len(an["sem_vinculo"]), exemplos_sem_vinculo=[nome(i) for i in an["sem_vinculo"][:15]],
                possiveis_fixadores=len(an["possiveis_fixadores"]),
                rigidez_derivada=sum(r["tipo"] == "sem_movimento_relativo" for r in an["rigidas"]))


def uniao_de(an):
    uf = UniaoBusca(an["corpos"])
    for g, membros in an["grupos"].items():
        for m in membros:
            uf.unir(g, m)
    return uf


def modos(leitura, an, base=None, tol=1e-6):
    """Graus de liberdade restantes (sem pares superiores): para cada direção
    do espaço nulo, quais grupos se movem. Classifica GL ociosos (um só grupo,
    giro em torno do próprio eixo de articulação)."""
    corpos = leitura["corpos"]
    uf = uniao_de(an)
    mont, idx, info = modelo(corpos, uf, an["articulacoes"], base)
    Z, T = mobilidade_relativa(mont)
    inv = {v: k for k, v in idx.items()}
    # base fixa: remover componentes onde a base se move (não deve ocorrer: raiz)
    lista = []
    # base esparsa: rotação de grupos individuais costuma separar os modos
    for c in range(Z.shape[1]):
        mov = [inv[b] for b in range(2, len(mont.corpos)) if np.abs(T[b, :, c]).max() > tol]
        lista.append(sorted(mov))
    return mont, idx, info, Z, T, lista
