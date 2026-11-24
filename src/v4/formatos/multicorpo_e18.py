"""E18 — núcleo multicorpo 3D genérico. EXPERIMENTAL, NÃO produção.

Entrada: um modelo compilado pelo MuJoCo (MJCF ou URDF). O MuJoCo é usado
SOMENTE como analisador de arquivo (corpos, juntas, malhas, igualdades,
atuadores, molas). A cinemática direta, o fechamento de laços, a análise de
mobilidade e a resolução quase-estática são deste módulo; o MuJoCo volta a
aparecer apenas como ORÁCULO independente em `auditar_*`.

Juntas: hinge e slide (ball/free são recusadas). Igualdades: connect, weld e
joint (polinomial). Graus de liberdade que sobram depois dos acionadores só
são resolvidos quando a fonte declara rigidez de mola; a postura é o mínimo
da energia elástica respeitando os batentes. Se ainda assim não houver
solução única, recusa (`E18-SUBDETERMINADO`).

Não simula dinâmica, atrito, contato com objetos, folga ou carga.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation

from .solver_restricoes_e1 import solve_constraints


def fail(reason):
    raise ValueError("E18-" + reason)


def quat_wxyz(q):
    q = np.asarray(q, dtype=float)
    return Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()


def pose(rot, pos):
    out = np.eye(4)
    out[:3, :3] = rot
    out[:3, 3] = pos
    return out


def axis_angle(axis, angle):
    return Rotation.from_rotvec(np.asarray(axis) * angle).as_matrix()


@dataclass
class Junta:
    nome: str
    corpo: int
    tipo: str            # "hinge" | "slide"
    eixo: np.ndarray     # no referencial do corpo
    ponto: np.ndarray    # no referencial do corpo
    limite: tuple | None
    rigidez: float
    mola_ref: float
    q0: float


@dataclass
class Igualdade:
    tipo: str            # "connect" | "weld" | "joint"
    a: int               # corpo (connect/weld) ou junta (joint)
    b: int
    dados: np.ndarray


@dataclass
class Visual:
    corpo: int
    nome: str
    local: np.ndarray    # 4x4 no referencial do corpo
    vertices: np.ndarray
    faces: np.ndarray
    rgba: np.ndarray


@dataclass
class Montagem:
    corpos: list
    pai: list
    local: list          # 4x4 do corpo relativo ao pai em q0
    juntas: list
    igualdades: list
    visuais: list
    atuadores: dict = field(default_factory=dict)   # nome -> {junta_indice: coef}
    chaves: dict = field(default_factory=dict)      # nome -> q

    @property
    def nq(self):
        return len(self.juntas)

    def indice_corpo(self, nome):
        if nome not in self.corpos:
            fail("CORPO_DESCONHECIDO")
        return self.corpos.index(nome)

    def indice_junta(self, nome):
        nomes = [j.nome for j in self.juntas]
        if nome not in nomes:
            fail("JUNTA_DESCONHECIDA")
        return nomes.index(nome)

    # ---------------------------------------------------------------- FK
    def poses(self, q):
        q = np.asarray(q, dtype=float)
        if q.shape != (self.nq,) or not np.isfinite(q).all():
            fail("ESTADO")
        mundo = [None] * len(self.corpos)
        por_corpo = {}
        for k, j in enumerate(self.juntas):
            por_corpo.setdefault(j.corpo, []).append(k)
        for b in range(len(self.corpos)):
            base = np.eye(4) if self.pai[b] < 0 else mundo[self.pai[b]] @ self.local[b]
            for k in por_corpo.get(b, []):
                j = self.juntas[k]
                d = q[k] - j.q0
                if j.tipo == "hinge":
                    r = axis_angle(j.eixo, d)
                    base = base @ pose(r, j.ponto - r @ j.ponto)
                else:
                    base = base @ pose(np.eye(3), j.eixo * d)
            mundo[b] = base
        return mundo

    # ------------------------------------------------------- restrições
    def residuo(self, q, referencia):
        x = self.poses(q)
        out = []
        for e in self.igualdades:
            if e.tipo == "connect":
                pa = x[e.a][:3, :3] @ e.dados[:3] + x[e.a][:3, 3]
                pb = x[e.b][:3, :3] @ e.dados[3:6] + x[e.b][:3, 3]
                out.extend(pa - pb)
            elif e.tipo == "weld":
                rel = np.linalg.inv(x[e.a]) @ x[e.b]
                alvo = referencia[id(e)]
                out.extend(rel[:3, 3] - alvo[:3, 3])
                out.extend(Rotation.from_matrix(rel[:3, :3] @ alvo[:3, :3].T).as_rotvec())
            else:
                ja, jb = self.juntas[e.a], self.juntas[e.b]
                x2 = q[e.b] - jb.q0
                c = e.dados
                out.append(q[e.a] - ja.q0 - (c[0] + c[1]*x2 + c[2]*x2**2 + c[3]*x2**3 + c[4]*x2**4))
        return np.asarray(out, dtype=float)

    def referencia_weld(self):
        x = self.poses(np.array([j.q0 for j in self.juntas]))
        return {id(e): np.linalg.inv(x[e.a]) @ x[e.b] for e in self.igualdades if e.tipo == "weld"}


def jacobiano(fun, q, h=1e-7):
    f0 = fun(q)
    jac = np.zeros((len(f0), len(q)))
    for k in range(len(q)):
        dq = np.zeros_like(q)
        dq[k] = h
        jac[:, k] = (fun(q + dq) - fun(q - dq)) / (2 * h)
    return jac


# --------------------------------------------------------------- leitura
def de_mujoco(m):
    """Converte um MjModel compilado no contrato Montagem (sem usar dinâmica)."""
    import mujoco
    obj = mujoco.mjtObj
    nome = lambda t, i: mujoco.mj_id2name(m, t, i) or f"{t.name[6:].lower()}_{i}"
    corpos = [nome(obj.mjOBJ_BODY, i) for i in range(m.nbody)]
    pai = [-1] + [int(m.body_parentid[i]) for i in range(1, m.nbody)]
    local = [np.eye(4)] + [pose(quat_wxyz(m.body_quat[i]), m.body_pos[i]) for i in range(1, m.nbody)]
    tipos = {int(mujoco.mjtJoint.mjJNT_HINGE): "hinge", int(mujoco.mjtJoint.mjJNT_SLIDE): "slide"}
    juntas = []
    for k in range(m.njnt):
        t = int(m.jnt_type[k])
        if t not in tipos:
            fail("JUNTA_NAO_SUPORTADA")
        if int(m.jnt_qposadr[k]) != k:
            fail("ENDERECO_QPOS")
        lim = tuple(float(v) for v in m.jnt_range[k]) if m.jnt_limited[k] else None
        juntas.append(Junta(nome(obj.mjOBJ_JOINT, k), int(m.jnt_bodyid[k]), tipos[t],
                            np.array(m.jnt_axis[k], float), np.array(m.jnt_pos[k], float), lim,
                            float(m.jnt_stiffness[k]), float(m.qpos_spring[k]), float(m.qpos0[k])))
    igualdades = []
    for e in range(m.neq):
        if not m.eq_active0[e]:
            continue
        t = int(m.eq_type[e])
        if int(m.eq_objtype[e]) not in (int(obj.mjOBJ_BODY), int(obj.mjOBJ_JOINT), int(obj.mjOBJ_UNKNOWN)):
            fail("IGUALDADE_OBJETO")
        if t == int(mujoco.mjtEq.mjEQ_CONNECT):
            igualdades.append(Igualdade("connect", int(m.eq_obj1id[e]), int(m.eq_obj2id[e]), np.array(m.eq_data[e][:6])))
        elif t == int(mujoco.mjtEq.mjEQ_WELD):
            igualdades.append(Igualdade("weld", int(m.eq_obj1id[e]), int(m.eq_obj2id[e]), np.array(m.eq_data[e])))
        elif t == int(mujoco.mjtEq.mjEQ_JOINT):
            if int(m.eq_obj2id[e]) < 0:
                fail("IGUALDADE_JUNTA_FIXA")
            igualdades.append(Igualdade("joint", int(m.eq_obj1id[e]), int(m.eq_obj2id[e]), np.array(m.eq_data[e][:5])))
        else:
            fail("IGUALDADE_NAO_SUPORTADA")
    visuais = []
    malha = int(mujoco.mjtGeom.mjGEOM_MESH)
    # Por corpo: malhas só-visuais quando a fonte as separa; senão, as malhas que existirem.
    escolhidos = []
    for b in range(m.nbody):
        todas = [g for g in range(m.ngeom) if m.geom_bodyid[g] == b and m.geom_type[g] == malha]
        so_visual = [g for g in todas if m.geom_contype[g] == 0 and m.geom_conaffinity[g] == 0]
        escolhidos.extend(so_visual or todas)
    for g in escolhidos:
        mid = int(m.geom_dataid[g])
        va, vn = int(m.mesh_vertadr[mid]), int(m.mesh_vertnum[mid])
        fa, fn = int(m.mesh_faceadr[mid]), int(m.mesh_facenum[mid])
        rgba = np.array(m.mat_rgba[m.geom_matid[g]] if m.geom_matid[g] >= 0 else m.geom_rgba[g], float)
        visuais.append(Visual(int(m.geom_bodyid[g]), nome(obj.mjOBJ_MESH, mid),
                              pose(quat_wxyz(m.geom_quat[g]), m.geom_pos[g]),
                              np.array(m.mesh_vert[va:va+vn], float), np.array(m.mesh_face[fa:fa+fn], np.int32), rgba))
    if not visuais:
        fail("SEM_MALHA")
    atuadores = {}
    for a in range(m.nu):
        t = int(m.actuator_trntype[a])
        alvo = int(m.actuator_trnid[a][0])
        if t == int(mujoco.mjtTrn.mjTRN_JOINT):
            coef = {alvo: 1.0}
        elif t == int(mujoco.mjtTrn.mjTRN_TENDON):
            coef = {}
            for w in range(int(m.tendon_adr[alvo]), int(m.tendon_adr[alvo] + m.tendon_num[alvo])):
                if int(m.wrap_type[w]) != int(mujoco.mjtWrap.mjWRAP_JOINT):
                    fail("TENDAO_ESPACIAL")
                coef[int(m.wrap_objid[w])] = float(m.wrap_prm[w])
        else:
            fail("TRANSMISSAO_NAO_SUPORTADA")
        atuadores[nome(obj.mjOBJ_ACTUATOR, a)] = coef
    chaves = {"qpos0": np.array(m.qpos0, float)}
    for k in range(m.nkey):
        chaves[nome(obj.mjOBJ_KEY, k)] = np.array(m.key_qpos[k], float)
    return Montagem(corpos, pai, local, juntas, igualdades, visuais, atuadores, chaves)


# ----------------------------------------------------------- resolução
class Resolvedor:
    """Acionadores prescritos + fechamentos; mola/batente só se a fonte declarar."""

    def __init__(self, mont: Montagem, acionadores: dict):
        # acionadores: nome -> {indice_junta: coef}; o valor-alvo é dado por quadro.
        if not acionadores:
            fail("SEM_ACIONADOR")
        self.m = mont
        self.nomes = list(acionadores)
        self.linhas = np.zeros((len(acionadores), mont.nq))
        for r, n in enumerate(self.nomes):
            for k, c in acionadores[n].items():
                self.linhas[r, k] = c
        self.ref = mont.referencia_weld()
        self.k = np.array([j.rigidez for j in mont.juntas])
        self.qs = np.array([j.mola_ref for j in mont.juntas])
        lo = [j.limite[0] if j.limite else -np.inf for j in mont.juntas]
        hi = [j.limite[1] if j.limite else np.inf for j in mont.juntas]
        self.lo, self.hi = np.array(lo), np.array(hi)

    def restricoes(self, q, alvo):
        return np.concatenate([self.m.residuo(q, self.ref), self.linhas @ q - alvo])

    def mobilidade(self, q, alvo):
        J = jacobiano(lambda x: self.restricoes(x, alvo), q)
        return self.m.nq - int(np.linalg.matrix_rank(J, tol=1e-7)), J

    def faixa_acionador(self, r):
        """Faixa da transmissão a partir dos limites das juntas envolvidas."""
        lo = hi = 0.0
        for k in np.nonzero(self.linhas[r])[0]:
            c = self.linhas[r, k]
            a, b = self.lo[k], self.hi[k]
            if not np.isfinite([a, b]).all():
                fail("ACIONADOR_SEM_LIMITE")
            lo += min(c*a, c*b)
            hi += max(c*a, c*b)
        return lo, hi

    def _projetar(self, fun, q):
        res, err, rank = solve_constraints(fun, q)
        return res.x, err, rank

    def _com_fixos(self, alvo, fixos):
        f = dict(fixos)
        return lambda x: np.concatenate([self.restricoes(x, alvo), np.array([x[i] - v for i, v in f.items()])])

    def _nulo(self, J):
        """Base ortonormal do espaço nulo de J (colunas) e posto."""
        _, sv, vt = np.linalg.svd(J)
        rank = int((sv > 1e-7 * max(1.0, sv[0] if len(sv) else 1.0)).sum())
        return vt[rank:].T, rank

    def quase_estatico(self, q, alvo, tol_bat=1e-9, iter_max=300):
        """Mínimo da energia elástica declarada na fonte (½·k·(q−q_mola)²) sobre
        a variedade de fechamento, dentro dos batentes (conjunto ativo).

        Cada iteração: projeta no fechamento com os batentes ativos fixados;
        se ainda há grau de liberdade, passo de Newton no espaço nulo (recortado
        no primeiro batente atingido, que entra no conjunto ativo); se o
        gradiente reduzido zera, confere os multiplicadores de cada batente e
        solta o que estiver puxando para dentro (KKT). Termina quando o ponto é
        estacionário e todos os batentes ativos empurram para fora. Se sobrar
        grau de liberdade sem rigidez que o determine, recusa."""
        nq = self.m.nq
        q = np.clip(np.array(q, float), self.lo, self.hi)
        # Partida a quente: batentes ativos do quadro anterior (o KKT solta os errados).
        fixos = {i: v for i, v in getattr(self, "_fixos", {}).items()}
        soltos = set()  # liberados pelo teste KKT; só voltam se o passo os empurrar
        presos = set()  # soltá-los não moveu o ponto: ficam ativos
        H = np.diag(self.k)
        for _ in range(iter_max):
            try:
                q, fixos = self._projetar_ativo(alvo, q, fixos)
            except ValueError:
                if not fixos:
                    raise
                fixos, soltos = {}, set()
                q, fixos = self._projetar_ativo(alvo, q, fixos)
            F = self._com_fixos(alvo, fixos)
            J = jacobiano(F, q)
            Z, rank = self._nulo(J)
            g = self.k * (q - self.qs)
            if Z.shape[1]:
                gr = Z.T @ g
                if np.abs(gr).max() > 1e-11:
                    Hr = Z.T @ H @ Z
                    if np.linalg.eigvalsh(Hr).min() > 1e-12:
                        d = -Z @ np.linalg.solve(Hr, gr)
                    else:
                        d = -Z @ gr
                    passo, bate = 1.0, None
                    for i in range(nq):
                        if i in fixos or abs(d[i]) < 1e-15:
                            continue
                        lim = self.hi[i] if d[i] > 0 else self.lo[i]
                        if np.isfinite(lim):
                            a = (lim - q[i]) / d[i]
                            if a < passo:
                                passo, bate = max(a, 0.0), i
                    q = q + passo * d
                    if bate is not None:
                        fixos[bate] = self.hi[bate] if d[bate] > 0 else self.lo[bate]
                        if bate in soltos and passo < 1e-12:
                            presos.add(bate)
                    soltos.clear()
                    continue
            # Estacionário na face atual: multiplicadores dos batentes.
            if not fixos:
                break
            lam = np.linalg.lstsq(J.T, g, rcond=None)[0]
            n_base = len(J) - len(fixos)
            soltar, pior = None, 1e-10
            for r, (i, v) in enumerate(fixos.items()):
                if i in presos:
                    continue
                li = lam[n_base + r]
                errado = -li if v == self.lo[i] else li   # lo exige λ≥0; hi exige λ≤0
                if errado > pior:
                    soltar, pior = i, errado
            if soltar is None:
                break
            del fixos[soltar]
            soltos.add(soltar)
        else:
            fail("QUASE_ESTATICO_NAO_CONVERGIU")
        F = self._com_fixos(alvo, fixos)
        J = jacobiano(F, q)
        Z, rank = self._nulo(J)
        if Z.shape[1]:
            if np.linalg.eigvalsh(Z.T @ H @ Z).min() < 1e-9:
                fail("SUBDETERMINADO")
            modo = "quase_estatico_mola"
        else:
            r, _, rank = solve_constraints(F, q)
            q, modo = r.x, "quase_estatico_batente"
        err = float(np.abs(F(q)).max())
        if err > 1e-7:
            fail("FECHAMENTO")
        self._fixos = dict(fixos)
        self.ultimos_batentes = sorted(self.m.juntas[i].nome for i in fixos)
        return q, err, rank, modo

    def _projetar_ativo(self, alvo, q, fixos):
        """Ponto do fechamento dentro dos batentes. Gauss-Newton exato; se
        juntas livres saem do curso, tenta fixar cada uma no seu batente (da
        mais violada para a menos) e segue a primeira opção cujo fechamento
        continua viável (busca em profundidade, poucas juntas). TRF com
        limites só como último recurso. Devolve (q, fixos)."""
        from scipy.optimize import least_squares
        visitados = set()

        def busca(fx, prof):
            chave = frozenset(fx.items())
            if chave in visitados or prof > self.m.nq:
                return None
            visitados.add(chave)
            try:
                x = self._sem_resto(self._com_fixos(alvo, fx), q)
            except ValueError:
                return None
            fora = [i for i in range(self.m.nq) if i not in fx and
                    (x[i] < self.lo[i] - 1e-9 or x[i] > self.hi[i] + 1e-9)]
            if not fora:
                livres = [i for i in range(self.m.nq) if i not in fx]
                x[livres] = np.clip(x[livres], self.lo[livres], self.hi[livres])
                return x, fx
            for i in sorted(fora, key=lambda k: -max(self.lo[k] - x[k], x[k] - self.hi[k])):
                r = busca({**fx, i: self.lo[i] if x[i] < self.lo[i] else self.hi[i]}, prof + 1)
                if r is not None:
                    return r
            return None

        r = busca(dict(fixos), 0)
        if r is not None:
            return r
        F = self._com_fixos(alvo, fixos)
        lo = np.array([-np.inf if i in fixos else self.lo[i] for i in range(self.m.nq)])
        hi = np.array([np.inf if i in fixos else self.hi[i] for i in range(self.m.nq)])
        res = least_squares(F, np.clip(q, lo + 1e-12, hi - 1e-12), bounds=(lo, hi), method="trf",
                            xtol=1e-15, ftol=1e-15, gtol=1e-15, max_nfev=4000)
        if float(np.abs(res.fun).max()) > 1e-8:
            fail("LIMITE_EXCEDIDO")
        return res.x, dict(fixos)

    def _sem_resto(self, fun, q):
        """Gauss-Newton sem exigir posto completo (variedade com dimensão > 0)."""
        from scipy.optimize import least_squares
        res = least_squares(fun, q, method="lm", xtol=1e-14, ftol=1e-14, gtol=1e-14, max_nfev=2000)
        if float(np.abs(res.fun).max()) > 1e-9:
            fail("FECHAMENTO")
        return res.x

    def resolver(self, alvo, semente, passo_max=0.05):
        """Continuação: do valor atual do acionador até o alvo em passos curtos,
        para seguir o mesmo ramo de montagem."""
        alvo = np.asarray(alvo, float)
        q = np.array(semente, float)
        atual = self.linhas @ q
        n = max(1, int(np.ceil(np.abs(alvo - atual).max() / passo_max)))
        for t in np.linspace(0, 1, n + 1)[1:]:
            q, info = self._resolver(atual + t * (alvo - atual), q)
        return q, info

    def _resolver(self, alvo, semente):
        q = np.array(semente, float)
        mob, _ = self.mobilidade(q, alvo)
        if mob == 0:
            res, err, rank = solve_constraints(lambda x: self.restricoes(x, alvo), q)
            q = res.x
            modo = "cinematico"
        else:
            if not (self.k > 0).any():
                fail("SUBDETERMINADO")
            q, err, rank, modo = self.quase_estatico(q, alvo)
        fora = (q < self.lo - 1e-8) | (q > self.hi + 1e-8)
        if fora.any():
            fail("LIMITE_EXCEDIDO:" + ",".join(self.m.juntas[i].nome for i in np.nonzero(fora)[0]))
        return q, dict(modo=modo, residuo=float(np.abs(self.restricoes(q, alvo)).max()), mobilidade=int(mob))


def trajetoria(mont, acionadores, alvos, semente):
    """alvos: array (quadros, n_acionadores). Continuidade de ramo verificada."""
    solver = Resolvedor(mont, acionadores)
    q = np.array(semente, float)
    out = []
    for alvo in alvos:
        novo, info = solver.resolver(alvo, q)
        if out and float(np.max(np.abs(novo - q))) > 0.35:
            fail("SALTO_DE_RAMO")
        q = novo
        out.append((q.copy(), info))
    return out, solver


# ------------------------------------------------------------- medidas
def subarvore(mont, nome):
    raiz = mont.indice_corpo(nome)
    corpos = {raiz}
    for b in range(len(mont.corpos)):
        c = b
        while c >= 0:
            if c == raiz:
                corpos.add(b)
                break
            c = mont.pai[c]
    return corpos


def pontos_mundo(mont, X, corpos):
    blocos = []
    for v in mont.visuais:
        if v.corpo in corpos:
            T = X[v.corpo] @ v.local
            blocos.append(v.vertices @ T[:3, :3].T + T[:3, 3])
    if not blocos:
        fail("MEDIDA_SEM_MALHA")
    return np.vstack(blocos)


def folga(mont, q, a, b, eixo=None):
    """Distância livre entre as malhas das subárvores a e b ao longo do eixo
    que liga seus centróides na pose de referência (ou do eixo dado)."""
    X = mont.poses(q)
    pa = pontos_mundo(mont, X, subarvore(mont, a))
    pb = pontos_mundo(mont, X, subarvore(mont, b))
    if eixo is None:
        eixo = pb.mean(0) - pa.mean(0)
        if np.linalg.norm(eixo) < 1e-9:
            return -np.inf, None  # centróides coincidentes: sem eixo de medida
        eixo = eixo / np.linalg.norm(eixo)
    return float((pb @ eixo).min() - (pa @ eixo).max()), eixo


def corte_no_contato(mont, solver, faixa, a, b, semente, passos=60):
    """Faixa do acionador em que as malhas das subárvores a e b NÃO se cruzam.

    O eixo de medida é fixado no extremo de maior folga. Cada extremo com
    folga negativa é recuado por bisseção até o primeiro contato (folga 0).
    Devolve ((inicio, fim), [extremos cortados], eixo)."""
    lo, hi = faixa
    alvos = np.linspace(lo, hi, passos)
    q = np.array(semente, float)
    qs = []
    for alvo in alvos:
        q, _ = solver.resolver([alvo], q)
        qs.append(q)
    candidatos = []
    for extremo in (qs[0], qs[-1]):
        _, e = folga(mont, extremo, a, b)
        if e is not None:
            candidatos.append((e, [folga(mont, x, a, b, e)[0] for x in qs]))
    if not candidatos:
        fail("MEDIDA_SEM_EIXO")
    eixo, g = max(candidatos, key=lambda c: max(c[1]))
    livre = [k for k, v in enumerate(g) if v >= 0]
    if not livre:
        fail("SEM_POSTURA_SEM_CONTATO")
    i0, i1 = livre[0], livre[-1]
    if livre != list(range(i0, i1 + 1)):
        fail("CONTATO_INTERMITENTE")
    cortes = []

    def bissecao(dentro, fora, qd):
        for _ in range(40):
            meio = (dentro + fora) / 2
            qm, _ = solver.resolver([meio], qd)
            if folga(mont, qm, a, b, eixo)[0] < 0:
                fora = meio
            else:
                dentro, qd = meio, qm
        return dentro

    ini, fim = alvos[i0], alvos[i1]
    if i0 > 0:
        ini = bissecao(alvos[i0], alvos[i0 - 1], qs[i0]); cortes.append("inicio")
    if i1 < passos - 1:
        fim = bissecao(alvos[i1], alvos[i1 + 1], qs[i1]); cortes.append("fim")
    return (float(ini), float(fim)), cortes, eixo


# ------------------------------------------------------- oráculos MuJoCo
def oraculo_cinematica(model, mont, qs):
    """Pose de cada corpo calculada pelo MuJoCo (mj_kinematics) vs. a nossa;
    resíduo das igualdades calculado pelo MuJoCo (efc_pos)."""
    import mujoco
    d = mujoco.MjData(model)
    pos = rot = eq = 0.0
    for q in qs:
        d.qpos[:] = q
        mujoco.mj_forward(model, d)
        X = mont.poses(q)
        for b in range(model.nbody):
            pos = max(pos, float(np.abs(X[b][:3, 3] - d.xpos[b]).max()))
            rot = max(rot, float(np.abs(X[b][:3, :3] - d.xmat[b].reshape(3, 3)).max()))
        linhas = d.efc_type[:d.nefc] == mujoco.mjtConstraint.mjCNSTR_EQUALITY
        if linhas.any():
            eq = max(eq, float(np.abs(d.efc_pos[:d.nefc][linhas]).max()))
    return dict(fk_pos_max_m=pos, fk_rot_max=rot, igualdade_mujoco_max=eq)


def oraculo_simulacao(model, mont, solver, alvos, segundos=3.0):
    """Para modelos subatuados: integra a dinâmica do MuJoCo (sem gravidade,
    sem contato) com o comando do atuador ajustado por bisseção até a
    transmissão atingir o alvo; compara a postura estacionária com a nossa."""
    import mujoco
    if model.nu != 1:
        fail("ORACULO_UM_ATUADOR")
    m = model
    m.opt.gravity[:] = 0
    m.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
    d = mujoco.MjData(m)
    lo, hi = m.actuator_ctrlrange[0] if m.actuator_ctrllimited[0] else (-1e3, 1e3)
    passos = int(segundos / m.opt.timestep)

    def estacionario(c):
        mujoco.mj_resetData(m, d)
        d.ctrl[0] = c
        for _ in range(passos):
            mujoco.mj_step(m, d)
        return float(d.actuator_length[0]), d.qpos.copy()

    resultado = []
    q = mont.chaves["qpos0"].copy()
    for alvo in alvos:
        a, b = float(lo), float(hi)
        la, _ = estacionario(a); lb, _ = estacionario(b)
        if not min(la, lb) - 1e-9 <= alvo <= max(la, lb) + 1e-9:
            resultado.append(dict(alvo=float(alvo), fora_do_alcance_do_atuador=True))
            continue
        crescente = lb > la
        for _ in range(30):
            c = (a + b) / 2
            l, qm = estacionario(c)
            if (l < alvo) == crescente:
                a = c
            else:
                b = c
        l, qm = estacionario((a + b) / 2)
        q, _ = solver.resolver([l], q)
        resultado.append(dict(alvo=float(l), max_dif_junta_rad=float(np.abs(qm - q).max())))
    return resultado


# --------------------------------------------------- interferência (FCL)
def pares_excluidos(mont, excluidos_fonte=()):
    fora = set()
    for b, p in enumerate(mont.pai):
        if p >= 0:
            fora.add(frozenset((b, p)))
    for e in mont.igualdades:
        if e.tipo in ("connect", "weld"):
            fora.add(frozenset((e.a, e.b)))
    for a, b in excluidos_fonte:
        fora.add(frozenset((a, b)))
    return fora


def interferencias(mont, q, excluidos):
    """Pares de corpos NÃO adjacentes cujas malhas se cruzam (teste exato
    triângulo-triângulo com BVH do FCL)."""
    import fcl
    X = mont.poses(q)
    objetos = {}
    for v in mont.visuais:
        T = X[v.corpo] @ v.local
        bvh = fcl.BVHModel()
        bvh.beginModel(len(v.vertices), len(v.faces))
        bvh.addSubModel(v.vertices @ T[:3, :3].T + T[:3, 3], v.faces)
        bvh.endModel()
        objetos.setdefault(v.corpo, []).append(fcl.CollisionObject(bvh, fcl.Transform()))
    achados = []
    corpos = sorted(objetos)
    for i, a in enumerate(corpos):
        for b in corpos[i+1:]:
            if frozenset((a, b)) in excluidos:
                continue
            for oa in objetos[a]:
                for ob in objetos[b]:
                    if fcl.collide(oa, ob, fcl.CollisionRequest(), fcl.CollisionResult()):
                        achados.append((mont.corpos[a], mont.corpos[b]))
                        break
                else:
                    continue
                break
    return sorted(set(achados))
