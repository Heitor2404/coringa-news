"""E18 — núcleo multicorpo 3D genérico. EXPERIMENTAL, NÃO produção.

Entrada: um modelo compilado pelo MuJoCo (MJCF ou URDF). O MuJoCo é usado
SOMENTE como analisador de arquivo (corpos, juntas, malhas, igualdades,
atuadores, molas). A cinemática direta, o fechamento de laços, a análise de
mobilidade e a resolução quase-estática são deste módulo; o MuJoCo volta a
aparecer apenas como ORÁCULO independente em `auditar_*`.

Juntas: hinge, slide e ball (esférica, 3 coordenadas = vetor de rotação); a
junta free da base é CONGELADA na pose de referência (o mecanismo é mostrado
em relação à própria base); free em outro corpo é recusada. Igualdades:
connect, weld e joint (polinomial). Graus de liberdade OCIOSOS — que só giram
um corpo e não movem nenhum outro, sem rigidez declarada (ex.: giro de uma
haste sobre o eixo entre seus dois vínculos) — são mantidos onde estavam no
quadro anterior (convenção registrada no QA, não física). Graus de liberdade que sobram depois dos acionadores só
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

from .solver_restricoes_e1 import solve_constraints as _solve_constraints_e1


def solve_constraints(fun, q):
    """Fechamento de posto completo. Usa o E1; se o critério de parada do
    LM do E1 falhar (visto com coordenadas ~1e-16), cai na projeção
    Gauss-Newton de norma mínima e REPETE a verificação de posto do E1."""
    try:
        return _solve_constraints_e1(fun, q)
    except ValueError as e:
        if "FECHAMENTO" not in str(e):
            raise
    q = np.array(q, float)
    for _ in range(60):
        r = fun(q)
        if np.abs(r).max() < 1e-13:
            break
        J = jacobiano(fun, q)
        q = q + np.linalg.lstsq(J, -r, rcond=None)[0]
    r = fun(q)
    err = float(np.abs(r).max())
    if err > 1e-7:
        raise ValueError("E1-SOLVER-FECHAMENTO")
    J = jacobiano(fun, q)
    rank = int(np.linalg.matrix_rank(J, tol=1e-8))
    if rank < len(q):
        raise ValueError("E1-SOLVER-SINGULAR_OU_SUBDETERMINADO")

    class _R:  # mesma interface usada pelo E18 (x, fun)
        pass
    res = _R()
    res.x, res.fun = q, r
    return res, err, rank


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
    tipo: str            # "hinge" | "slide" | "ball"
    eixo: np.ndarray     # no referencial do corpo
    ponto: np.ndarray    # no referencial do corpo
    limite: tuple | None
    rigidez: float
    mola_ref: float
    q0: float
    adr: int = 0         # primeira coordenada em q (nosso vetor)
    dim: int = 1         # 1 (hinge/slide) ou 3 (ball)
    qposadr: int = 0     # endereço no qpos do MuJoCo (só para oráculos)


@dataclass
class Coord:
    """Uma coordenada do vetor q (uma junta 1-GL, ou um eixo de uma esférica)."""
    nome: str
    junta: int
    corpo: int
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
    atuadores: dict = field(default_factory=dict)   # nome -> {indice_coordenada: coef}
    chaves: dict = field(default_factory=dict)      # nome -> q
    qpos0: np.ndarray | None = None                 # qpos completo do MuJoCo (oráculos)
    base_congelada: list = field(default_factory=list)

    def __post_init__(self):
        self.coords = []
        for k, j in enumerate(self.juntas):
            j.adr = len(self.coords)
            if j.tipo == "ball":
                for eixo in "xyz":
                    self.coords.append(Coord(f"{j.nome}[{eixo}]", k, j.corpo, None, 0.0, 0.0, 0.0))
            else:
                self.coords.append(Coord(j.nome, k, j.corpo, j.limite, j.rigidez, j.mola_ref, j.q0))

    @property
    def nq(self):
        return len(self.coords)

    def q_referencia(self):
        return np.array([c.q0 for c in self.coords], float)

    def para_qpos(self, q):
        """Nosso q → qpos do MuJoCo (base congelada fica em qpos0)."""
        out = np.array(self.qpos0, float)
        for j in self.juntas:
            if j.tipo == "ball":
                x, y, z, w = Rotation.from_rotvec(q[j.adr:j.adr + 3]).as_quat()
                out[j.qposadr:j.qposadr + 4] = (w, x, y, z)
            else:
                out[j.qposadr] = q[j.adr]
        return out

    def de_qpos(self, qpos):
        q = np.zeros(self.nq)
        for j in self.juntas:
            if j.tipo == "ball":
                w, x, y, z = qpos[j.qposadr:j.qposadr + 4]
                q[j.adr:j.adr + 3] = Rotation.from_quat([x, y, z, w]).as_rotvec()
            else:
                q[j.adr] = qpos[j.qposadr]
        return q

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
                if j.tipo == "ball":
                    r = Rotation.from_rotvec(q[j.adr:j.adr + 3]).as_matrix()
                    base = base @ pose(r, j.ponto - r @ j.ponto)
                    continue
                d = q[j.adr] - j.q0
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
                ca, cb = self.coords[e.a], self.coords[e.b]
                x2 = q[e.b] - cb.q0
                c = e.dados
                out.append(q[e.a] - ca.q0 - (c[0] + c[1]*x2 + c[2]*x2**2 + c[3]*x2**3 + c[4]*x2**4))
        return np.asarray(out, dtype=float)

    def referencia_weld(self):
        x = self.poses(self.q_referencia())
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
    tipos = {int(mujoco.mjtJoint.mjJNT_HINGE): "hinge", int(mujoco.mjtJoint.mjJNT_SLIDE): "slide",
             int(mujoco.mjtJoint.mjJNT_BALL): "ball"}
    juntas, mj_para_junta, congeladas = [], {}, []
    for k in range(m.njnt):
        t = int(m.jnt_type[k])
        b = int(m.jnt_bodyid[k])
        if t == int(mujoco.mjtJoint.mjJNT_FREE):
            if int(m.body_parentid[b]) != 0:
                fail("JUNTA_LIVRE_FORA_DA_BASE")
            congeladas.append(nome(obj.mjOBJ_BODY, b))
            continue
        if t not in tipos:
            fail("JUNTA_NAO_SUPORTADA")
        adr = int(m.jnt_qposadr[k])
        if tipos[t] == "ball":
            if m.jnt_limited[k]:
                fail("ESFERICA_LIMITADA")
            if m.jnt_stiffness[k]:
                fail("ESFERICA_COM_MOLA")
            if np.abs(m.qpos0[adr:adr + 4] - np.array([1, 0, 0, 0])).max() > 1e-12:
                fail("ESFERICA_REFERENCIA")
            lim, ref, q0 = None, 0.0, 0.0
        else:
            lim = tuple(float(v) for v in m.jnt_range[k]) if m.jnt_limited[k] else None
            ref, q0 = float(m.qpos_spring[adr]), float(m.qpos0[adr])
        mj_para_junta[k] = len(juntas)
        juntas.append(Junta(nome(obj.mjOBJ_JOINT, k), b, tipos[t],
                            np.array(m.jnt_axis[k], float), np.array(m.jnt_pos[k], float), lim,
                            float(m.jnt_stiffness[k]), ref, q0, qposadr=adr))
    # endereço em q de cada junta 1-GL (como o __post_init__ da Montagem calcula)
    adr_q, n = {}, 0
    for k, j in enumerate(juntas):
        adr_q[k] = n
        n += 3 if j.tipo == "ball" else 1

    def coord(jmj):
        if jmj not in mj_para_junta or juntas[mj_para_junta[jmj]].tipo == "ball":
            fail("REFERENCIA_A_JUNTA_SEM_COORDENADA_UNICA")
        return adr_q[mj_para_junta[jmj]]
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
            igualdades.append(Igualdade("joint", coord(int(m.eq_obj1id[e])), coord(int(m.eq_obj2id[e])),
                                        np.array(m.eq_data[e][:5])))
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
    atuadores, servos = {}, {}
    for a in range(m.nu):
        t = int(m.actuator_trntype[a])
        alvo = int(m.actuator_trnid[a][0])
        if t == int(mujoco.mjtTrn.mjTRN_JOINT):
            coef = {coord(alvo): 1.0}
        elif t == int(mujoco.mjtTrn.mjTRN_TENDON):
            coef = {}
            for w in range(int(m.tendon_adr[alvo]), int(m.tendon_adr[alvo] + m.tendon_num[alvo])):
                if int(m.wrap_type[w]) != int(mujoco.mjtWrap.mjWRAP_JOINT):
                    fail("TENDAO_ESPACIAL")
                coef[coord(int(m.wrap_objid[w]))] = float(m.wrap_prm[w])
        else:
            fail("TRANSMISSAO_NAO_SUPORTADA")
        atuadores[nome(obj.mjOBJ_ACTUATOR, a)] = coef
        # Servo de posição afim: equilíbrio estático em g·ctrl + b0 + b1·L = 0.
        if (int(m.actuator_biastype[a]) == int(mujoco.mjtBias.mjBIAS_AFFINE)
                and int(m.actuator_gaintype[a]) == int(mujoco.mjtGain.mjGAIN_FIXED)
                and m.actuator_biasprm[a][1] < 0):
            servos[nome(obj.mjOBJ_ACTUATOR, a)] = (float(m.actuator_gainprm[a][0]), float(m.actuator_biasprm[a][0]),
                                                   float(m.actuator_biasprm[a][1]))
    mont = Montagem(corpos, pai, local, juntas, igualdades, visuais, atuadores, {},
                    np.array(m.qpos0, float), congeladas)
    mont.chaves["qpos0"] = mont.de_qpos(m.qpos0)
    mont.servos, mont.comandos = servos, {}
    for k in range(m.nkey):
        mont.chaves[nome(obj.mjOBJ_KEY, k)] = mont.de_qpos(m.key_qpos[k])
        if m.nu:
            mont.comandos[nome(obj.mjOBJ_KEY, k)] = dict(zip(atuadores, map(float, m.key_ctrl[k])))
    return mont


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
        self.k = np.array([c.rigidez for c in mont.coords])
        self.qs = np.array([c.mola_ref for c in mont.coords])
        lo = [c.limite[0] if c.limite else -np.inf for c in mont.coords]
        hi = [c.limite[1] if c.limite else np.inf for c in mont.coords]
        self.lo, self.hi = np.array(lo), np.array(hi)

    def restricoes(self, q, alvo):
        base = np.concatenate([self.m.residuo(q, self.ref), self.linhas @ q - alvo])
        extra = getattr(self, "_extra", None)
        return base if extra is None else np.concatenate([base, extra[0] @ q - extra[1]])

    def ociosos(self, q, alvo, h=1e-6, eps=1e-9):
        """Direções do espaço nulo SEM rigidez que movem um único corpo.

        Ex.: haste com esférica numa ponta e pino na outra gira livre sobre o
        próprio eixo; nenhuma outra peça se move e nada na fonte determina o
        ângulo. Devolve uma base ortonormal (linhas) dessas direções."""
        guardado, self._extra = getattr(self, "_extra", None), None
        try:
            J = jacobiano(lambda x: self.restricoes(x, alvo), q)
        finally:
            self._extra = guardado
        Z, _ = self._nulo(J)
        if not Z.shape[1]:
            return None
        Nk, _ = self._nulo(np.sqrt(self.k)[:, None] * Z)   # combinações sem rigidez
        Z0 = Z @ Nk
        if not Z0.shape[1]:
            return None
        nb = len(self.m.corpos)
        T = np.zeros((nb, 6, Z0.shape[1]))
        for c in range(Z0.shape[1]):
            Xp, Xm = self.m.poses(q + h * Z0[:, c]), self.m.poses(q - h * Z0[:, c])
            for b in range(nb):
                T[b, :3, c] = (Xp[b][:3, 3] - Xm[b][:3, 3]) / (2 * h)
                T[b, 3:, c] = Rotation.from_matrix(Xp[b][:3, :3] @ Xm[b][:3, :3].T).as_rotvec() / (2 * h)
        vetores = []
        for b in range(nb):
            outros = np.delete(T, b, axis=0).reshape(-1, Z0.shape[1])
            Nb, _ = self._nulo(outros) if len(outros) else (np.eye(Z0.shape[1]), 0)
            for c in range(Nb.shape[1]):
                if np.abs(T[b] @ Nb[:, c]).max() > eps:
                    vetores.append(Z0 @ Nb[:, c])
        if not vetores:
            return None
        U, sv, _ = np.linalg.svd(np.array(vetores).T, full_matrices=False)
        return U[:, sv > 1e-9].T

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
                Hr = Z.T @ H @ Z
                if np.linalg.eigvalsh(Hr).min() > 1e-12:
                    d = -Z @ np.linalg.solve(Hr, gr)
                else:
                    d = -Z @ gr
                # Estacionário: gradiente reduzido no nível do ruído do Jacobiano
                # por diferenças finitas (~1e-8 relativo), ou passo de Newton
                # menor que 1e-9 (rad ou m) — muito abaixo de qualquer medida.
                if (np.abs(gr).max() > 1e-7 * max(1.0, np.abs(g).max())
                        and np.abs(d).max() > 1e-9):
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
        self.ultimos_batentes = sorted(self.m.coords[i].nome for i in fixos)
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

    def _sem_resto(self, fun, q, iter_max=60):
        """Projeção no fechamento por Gauss-Newton com passo de norma mínima
        (funciona com mais incógnitas que equações, i.e. variedade com GL)."""
        q = np.array(q, float)
        r = fun(q)
        for _ in range(iter_max):
            if np.abs(r).max() < 1e-13:
                return q
            J = jacobiano(fun, q)
            dq = np.linalg.lstsq(J, -r, rcond=None)[0]
            passo = 1.0
            for _ in range(20):  # busca linear simples: o resíduo tem de cair
                qn = q + passo * dq
                rn = fun(qn)
                if np.linalg.norm(rn) < np.linalg.norm(r):
                    break
                passo /= 2
            else:
                break
            q, r = qn, rn
        if float(np.abs(r).max()) > 1e-9:
            fail("FECHAMENTO")
        return q

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
        self._extra = None
        A = self.ociosos(q, alvo)
        if A is not None:
            self._extra = (A, A @ q)   # mantém o GL ocioso onde estava
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
            fail("LIMITE_EXCEDIDO:" + ",".join(self.m.coords[i].nome for i in np.nonzero(fora)[0]))
        return q, dict(modo=modo, residuo=float(np.abs(self.restricoes(q, alvo)).max()), mobilidade=int(mob),
                       ociosos=0 if A is None else int(len(A)))


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


def faixa_viavel(solver, faixa, inicio, semente, montar=lambda s: [s], passo=0.02):
    """Parte do curso do acionador alcançável sem que OUTRA junta atravesse o
    batente (ou o fechamento deixe de existir). Caminha do início para cada
    extremo e, na primeira recusa, faz bisseção até o último ponto viável.
    Devolve ((lo, hi), [extremos limitados])."""
    lo, hi = faixa
    out, limitados = [inicio, inicio], []
    for lado, fim in ((0, lo), (1, hi)):
        q, atual = np.array(semente, float), inicio
        n = max(1, int(np.ceil(abs(fim - inicio) / passo)))
        for alvo in np.linspace(inicio, fim, n + 1)[1:]:
            try:
                q, _ = solver.resolver(montar(alvo), q)
                atual = alvo
            except ValueError as e:
                if "LIMITE_EXCEDIDO" not in str(e) and "FECHAMENTO" not in str(e):
                    raise
                ok, ruim, qok = atual, alvo, q
                for _ in range(30):
                    meio = (ok + ruim) / 2
                    try:
                        qok, _ = solver.resolver(montar(meio), qok)
                        ok = meio
                    except ValueError:
                        ruim = meio
                atual = ok
                limitados.append("inicio" if lado == 0 else "fim")
                break
        out[lado] = float(atual)
    return (out[0], out[1]), limitados


def corte_no_contato(mont, solver, faixa, a, b, semente, passos=60, montar=lambda s: [s]):
    """Faixa do acionador em que as malhas das subárvores a e b NÃO se cruzam.

    O eixo de medida é fixado no extremo de maior folga. Cada extremo com
    folga negativa é recuado por bisseção até o primeiro contato (folga 0).
    Devolve ((inicio, fim), [extremos cortados], eixo)."""
    lo, hi = faixa
    alvos = np.linspace(lo, hi, passos)
    q = np.array(semente, float)
    qs = []
    for alvo in alvos:
        q, _ = solver.resolver(montar(alvo), q)
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
            qm, _ = solver.resolver(montar(meio), qd)
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
        d.qpos[:] = mont.para_qpos(q)
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
        d.qpos[:] = mont.qpos0
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
        resultado.append(dict(alvo=float(l), max_dif_junta_rad=float(np.abs(mont.de_qpos(qm) - q).max())))
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


class Colisor:
    """Malhas no referencial de cada corpo, com BVH montada UMA vez (FCL);
    cada pose só troca a transformação dos objetos."""

    def __init__(self, mont, excluidos):
        import fcl
        self.fcl, self.mont, self.excluidos = fcl, mont, excluidos
        self.objetos = {}
        for v in mont.visuais:
            Vl = v.vertices @ v.local[:3, :3].T + v.local[:3, 3]
            bvh = fcl.BVHModel()
            bvh.beginModel(len(Vl), len(v.faces))
            bvh.addSubModel(Vl, v.faces)
            bvh.endModel()
            self.objetos.setdefault(v.corpo, []).append(fcl.CollisionObject(bvh, fcl.Transform()))

    def pares(self, q):
        fcl = self.fcl
        X = self.mont.poses(q)
        for b, objs in self.objetos.items():
            for o in objs:
                o.setTransform(fcl.Transform(X[b][:3, :3], X[b][:3, 3]))
        achados = set()
        corpos = sorted(self.objetos)
        for i, a in enumerate(corpos):
            for b in corpos[i + 1:]:
                if frozenset((a, b)) in self.excluidos:
                    continue
                if any(fcl.collide(oa, ob, fcl.CollisionRequest(), fcl.CollisionResult())
                       for oa in self.objetos[a] for ob in self.objetos[b]):
                    achados.add((self.mont.corpos[a], self.mont.corpos[b]))
        return sorted(achados)


def interferencias(mont, q, excluidos):
    """Pares de corpos NÃO adjacentes cujas malhas se cruzam (teste exato
    triângulo-triângulo com BVH do FCL)."""
    return Colisor(mont, excluidos).pares(q)


def faixa_sem_contato_novo(solver, colisor, faixa, inicio, semente, montar, referencia, passos=36):
    """Recorta o curso do acionador no primeiro contato NOVO entre peças.

    `referencia` = pares que já se cruzam na pose de referência da fonte
    (malhas simplificadas sobrepostas por construção): ficam registrados, não
    cortam. Caminha do início para cada extremo; no primeiro quadro com par
    novo, bisseção até o último instante sem ele. ((lo, hi), cortes, pares)."""
    ref = set(map(tuple, referencia))
    out, cortes, novos = [inicio, inicio], [], set()
    for lado, fim in ((0, faixa[0]), (1, faixa[1])):
        if abs(fim - inicio) < 1e-12:
            out[lado] = float(fim)
            continue
        q, atual = np.array(semente, float), inicio
        for alvo in np.linspace(inicio, fim, passos + 1)[1:]:
            qn, _ = solver.resolver(montar(alvo), q)
            extra = set(colisor.pares(qn)) - ref
            if extra:
                novos |= extra
                ok, ruim, qok = atual, alvo, q
                for _ in range(24):
                    meio = (ok + ruim) / 2
                    qm, _ = solver.resolver(montar(meio), qok)
                    if set(colisor.pares(qm)) - ref:
                        ruim = meio
                    else:
                        ok, qok = meio, qm
                atual = ok
                cortes.append("inicio" if lado == 0 else "fim")
                break
            q, atual = qn, alvo
        out[lado] = float(atual)
    return (out[0], out[1]), cortes, sorted(novos)
