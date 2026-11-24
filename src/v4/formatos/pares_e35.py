"""E35 — pares superiores (contato de pino em rasgo) sobre o solver E18.

Um par pino–rasgo é uma restrição de CONTATO INTERMITENTE: enquanto o centro
do pino está dentro do canal do rasgo, ele fica sobre a linha média do rasgo
(1 equação no plano perpendicular aos eixos paralelos). Fora do canal, não há
restrição; o corpo do rasgo, se ficar sem determinação, é um GL ocioso do
E18 (mantido onde estava) — e a auditoria de colisões (FCL) acusa se ele
precisava de um travamento que não foi modelado.

Não há fórmula de mecanismo aqui: só ponto-sobre-reta com ativação por
pertinência geométrica ao canal. O oráculo analítico de cada CLASSE de
mecanismo fica fora do solver (oraculos_e35).
"""
from __future__ import annotations

import numpy as np

from . import multicorpo_e18 as M


class ParPinoRasgo:
    def __init__(self, mont, par, ctr, f=1e-3):
        eix = ctr["_eixos"]
        ia, ib = par["corpo_pino"], par["corpo_rasgo"]
        self.a, self.b = 1 + ia, 1 + ib   # índices na Montagem (0 = suporte)
        self.raio = par["pino"]["raio"] * f
        # centro do pino no referencial do corpo A (origem = eixo próprio)
        self.pino_local = (par["pino"]["centro"] - eix[ia]["origem"]) * f
        self.eixo_b = np.asarray(eix[ib]["eixo"], float)
        self.rasgos = []
        for r in par["rasgos"]:
            self.rasgos.append(dict(ponto=(r["ponto"] - eix[ib]["origem"]) * f, dir=np.asarray(r["direcao"]),
                                    t_dentro=r["t_dentro"] * f, t_boca=r["t_boca"] * f,
                                    meia=r["largura"] * f / 2))

    def _local(self, X, k):
        """Centro do pino no referencial de B, coordenadas (ao longo, lateral)."""
        pa = X[self.a][:3, :3] @ self.pino_local + X[self.a][:3, 3]
        Tb = X[self.b]
        p = Tb[:3, :3].T @ (pa - Tb[:3, 3])
        r = self.rasgos[k]
        w = p - r["ponto"]
        lat = np.cross(self.eixo_b, r["dir"])
        return float(w @ r["dir"]), float(w @ lat)

    def residuo(self, X, k):
        return self._local(X, k)[1]

    def dentro(self, X, k, folga_boca=0.0):
        ao_longo, lateral = self._local(X, k)
        r = self.rasgos[k]
        return (r["t_dentro"] - self.raio - 1e-9 <= ao_longo <= r["t_boca"] + folga_boca
                and abs(lateral) <= r["meia"])


class ResolvedorComPares(M.Resolvedor):
    def __init__(self, mont, acion, pares):
        super().__init__(mont, acion)
        self.pares = pares
        self.ativos = []    # [(i_par, k_rasgo)]

    def restricoes(self, q, alvo):
        base = super().restricoes(q, alvo)
        if not self.ativos:
            return base
        X = self.m.poses(q)
        return np.concatenate([base, [self.pares[i].residuo(X, k) for i, k in self.ativos]])


def _passo(s, pares, alvo, q):
    """Um subpasso: resolve com os contatos ativos; solta os que saíram pela
    boca; ativa os que entraram no canal; re-resolve se o conjunto mudou."""
    q1, info = s.resolver(alvo, q)
    X1 = s.m.poses(q1)
    ainda = [(i, k) for i, k in s.ativos if pares[i].dentro(X1, k)]
    if ainda != s.ativos:
        s.ativos = ainda
        q1, info = s.resolver(alvo, q)
        X1 = s.m.poses(q1)
    novos = [(i, k) for i, p in enumerate(pares) for k in range(len(p.rasgos))
             if (i, k) not in s.ativos and p.dentro(X1, k)]
    if novos:
        s.ativos = s.ativos + novos
        q1, info = s.resolver(alvo, q)
    return q1, info


def trajetoria(mont, acion, pares, alvos, semente, passo_max=np.radians(1.0)):
    """Resolve quadro a quadro; entre quadros, subdivide a entrada em passos
    ≤ passo_max e decide os contatos em cada subpasso (entrada/saída do
    canal não são puladas quando os quadros são espaçados)."""
    s = ResolvedorComPares(mont, acion, pares)
    q = np.array(semente, float)
    X = mont.poses(q)
    s.ativos = [(i, k) for i, p in enumerate(pares) for k in range(len(p.rasgos)) if p.dentro(X, k)]
    out = []
    anterior = None
    for alvo in alvos:
        alvo = np.asarray(alvo, float)
        if anterior is None:
            subs = [alvo]
        else:
            n = max(1, int(np.ceil(np.abs(alvo - anterior).max() / passo_max)))
            subs = [anterior + (alvo - anterior) * (j / n) for j in range(1, n + 1)]
        for sub in subs:
            q, info = _passo(s, pares, sub, q)
        out.append((q, dict(info, contatos_ativos=[list(a) for a in s.ativos])))
        anterior = alvo
    return out, s
