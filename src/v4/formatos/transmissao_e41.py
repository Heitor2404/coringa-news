"""E41 — montagem com suportes reais + pares superiores no solver E18.

Liga as peças da E41 (vinculos_e41 → grupos/articulações; lobulos_e41 → pares
comprovados) ao Resolvedor E18, sem tocar o núcleo:

* PORTADOR de um conjunto de roletes: grupo comum alcançado de TODOS os roletes
  por articulações coaxiais a cada rolete (o rolete gira no seu pino; o pino
  está no portador).
* ENTRADA: grupo da cadeia coaxial ao eixo do corpo de perfil que também se
  articula no eixo principal (a excêntrica).
* Em cadeias de eixos PARALELOS, o ângulo absoluto de um grupo é a soma
  (com sinal) das coordenadas das juntas no caminho desde a base ⇒ os pares
  superiores viram linhas LINEARES exatas: perfil = razão·entrada; saída = perfil.
  Eixo não paralelo no caminho ⇒ recusa.
* Todo GL restante sem determinação (anel de rolamento, rolete girando no
  pino, subsistemas ligados só por fixação NÃO comprovada) é mantido onde
  estava (convenção do E18, estendida) e LISTADO por grupo no QA.
"""
from __future__ import annotations

import numpy as np

from . import multicorpo_e18 as M
from . import vinculos_e41 as V


def fail(c):
    raise ValueError("E41-TRANS-" + c)


def _coaxial(x, d, o, tol=V.TOL_EIXO):
    return V._paralelos(x["eixo"], d) and V._dist_reta(x["origem"], o, d) < tol


def alcance_coaxial(an, uf, inicio, d, o):
    """Grupos alcançados de `inicio` por articulações coaxiais ao eixo (o, d)."""
    viz = {}
    for x in an["articulacoes"]:
        if _coaxial(x, d, o):
            viz.setdefault(x["a"], []).append(x["b"])
            viz.setdefault(x["b"], []).append(x["a"])
    vistos, fila = {inicio}, [inicio]
    while fila:
        k = fila.pop()
        for j in viz.get(k, []):
            if j not in vistos:
                vistos.add(j)
                fila.append(j)
    return {uf.achar(k) for k in vistos}


def portador(an, uf, corpos, conjunto):
    comuns = None
    for b, c in zip(conjunto["corpos"], conjunto["centros"]):
        gs = alcance_coaxial(an, uf, b, np.asarray(conjunto["eixo"]), np.asarray(c)) - {uf.achar(b)}
        comuns = gs if comuns is None else comuns & gs
    comuns = sorted(comuns or [])
    if len(comuns) != 1:
        return None, comuns
    return comuns[0], comuns


def linha_angular(mont, idx_corpo, d):
    """Linha r (nq) tal que r·q = ângulo absoluto do corpo em torno de d."""
    r = np.zeros(mont.nq)
    por_corpo = {j.corpo: j for j in mont.juntas}
    b = idx_corpo
    while b > 1:
        j = por_corpo.get(b)
        if j is None:          # junta congelada: o corpo segue o pai
            b = mont.pai[b]
            continue
        if not V._paralelos(j.eixo, d):
            fail("CAMINHO_COM_EIXO_NAO_PARALELO")
        r[j.adr] += float(np.sign(np.dot(j.eixo, d)))
        b = mont.pai[b]
    return r


class ResolvedorTransmissao(M.Resolvedor):
    """Acionador = ângulo absoluto da entrada; pares superiores = linhas G·q = 0;
    todo GL restante sem determinação é mantido (lista em `mantidos`)."""

    def __init__(self, mont, linha_entrada, G):
        super().__init__(mont, {"entrada": {k: float(c) for k, c in enumerate(linha_entrada) if c}})
        self.G = np.atleast_2d(G) if len(G) else np.zeros((0, mont.nq))

    def restricoes(self, q, alvo):
        base = super().restricoes(q, alvo)
        return np.concatenate([base, self.G @ q]) if len(self.G) else base

    def ociosos(self, q, alvo, h=1e-6, eps=1e-9):
        guardado, self._extra = getattr(self, "_extra", None), None
        try:
            J = M.jacobiano(lambda x: self.restricoes(x, alvo), q)
        finally:
            self._extra = guardado
        Z, _ = self._nulo(J)
        return None if not Z.shape[1] else Z.T


def montar(leitura, an, base_gid, f=1e-3):
    uf = V.uniao_de(an)
    mont, idx, info = V.modelo(leitura["corpos"], uf, an["articulacoes"], base=base_gid, f=f)
    return mont, idx, info, uf


def classificar_mantidos(mont, idx, nucleo, tol=1e-6):
    """Direções do espaço nulo com a entrada fixa: quais grupos movem."""
    Z, T = V.mobilidade_relativa(mont)
    return Z, T


def trajetoria(mont, linha_in, G, alvos, semente=None):
    s = ResolvedorTransmissao(mont, linha_in, G)
    q = np.zeros(mont.nq) if semente is None else np.array(semente, float)
    out = []
    for a in alvos:
        q, info = s.resolver([a], q)
        out.append((q, info))
    return out, s


def analisar_transmissao(leitura, an, formas_de, n_theta=120, conjuntos=None):
    """Pares superiores comprovados + papéis estruturais. `formas_de(indices)`
    devolve as formas B-rep (para seções exatas). Recusa com motivo quando
    falta evidência."""
    from . import lobulos_e41 as LB
    from . import inferencia_e35 as I
    corpos = leitura["corpos"]
    uf = V.uniao_de(an)
    conj = conjuntos if conjuntos is not None else LB.conjuntos_cilindricos(corpos, convexo=True)
    pares, rel = [], dict(conjuntos_roletes=[dict(n=c["n"], raio=c["raio"], R=c["R"], z=c["z"]) for c in conj])
    candidatos = []
    for c in conj:
        d, O = np.asarray(c["eixo"]), np.asarray(c["centro"])
        for k, corpo in enumerate(corpos):
            if k in c["corpos"] or V.esferico(corpo):
                continue
            ep = I.eixo_proprio(corpo)
            if ep is None or not V._paralelos(ep["eixo"], d):
                continue
            e = V._dist_reta(ep["origem"], O, d)
            z0, z1 = sorted(np.dot(np.array(corpo.caixa), d))
            if not (1e-3 < e < 0.25 * c["R"]) or not (z0 <= np.dot(O, d) <= z1):
                continue
            # alcance: raio externo do corpo em torno do próprio eixo ≈ R − r_rolete (± e + 2 mm)
            meia = 0.5 * np.max(np.abs(np.subtract(corpo.caixa[1], corpo.caixa[0])))
            if abs(meia - (c["R"] - c["raio"])) > e + 2.0:
                continue
            candidatos.append((c, k, ep, e))
    if not candidatos:
        return dict(rel, aceito=False, motivo="SEM_CORPO_DE_PERFIL_EXCENTRICO_NOS_ROLETES")
    formas = formas_de(sorted({k for _, k, _, _ in candidatos}))
    for c, k, ep, e in candidatos:
        try:
            lob = LB.par_lobulado(formas[k], ep, c, n_theta)
        except ValueError as err:
            pares.append(dict(corpo=k, nome=corpos[k].nome, lobulado=dict(aceito=False), motivo=str(err)))
            continue
        reg = dict(corpo=k, nome=corpos[k].nome, lobulado=lob)
        if not lob["aceito"]:
            reg["motivo"] = "PERFIL_NAO_CONJUGADO_AOS_ROLETES"
            pares.append(reg)
            continue
        d, O = np.asarray(c["eixo"]), np.asarray(c["centro"])
        reg["portador_roletes"], reg["portadores_candidatos"] = portador(an, uf, corpos, c)
        # cadeia coaxial ao eixo do perfil → grupo que também gira no eixo principal (entrada)
        alc = alcance_coaxial(an, uf, k, d, np.asarray(ep["origem"]))
        entrada = [g for g in alc - {uf.achar(k)} if any(
            _coaxial(x, d, O) and uf.achar(x["a"]) == g or _coaxial(x, d, O) and uf.achar(x["b"]) == g
            for x in an["articulacoes"])]
        reg["entrada_candidatos"] = sorted(entrada)
        # acoplamento de saída por pino-em-furo
        saidas = []
        for c2 in conj:
            if c2 is c or V._dist_reta(c2["centro"], O, d) > V.TOL_EIXO:
                continue
            pf = LB.pinos_em_furos(corpos[k], ep, c2, e)
            if pf["aceito"]:
                g, cands = portador(an, uf, corpos, c2)
                saidas.append(dict(pf, portador=g, portadores_candidatos=cands, roletes=c2["n"], R=c2["R"]))
        reg["saidas"] = saidas
        pares.append(reg)
    return dict(rel, pares=pares, aceito=any(p["lobulado"]["aceito"] for p in pares))


def podar(mont, nucleo_corpos):
    """Libera, para cada corpo do núcleo (do mais raso ao mais fundo), UMA junta
    do seu caminho até a base situada ABAIXO da última já liberada (para ter
    rotação relativa própria) — de rolamento se houver, senão a mais próxima
    do corpo. As demais juntas são congeladas (filho segue o pai). Devolve
    (montagem_podada, livres, congeladas). Fechamentos por pontos de eixo
    continuam satisfeitos."""
    por_corpo = {j.corpo: j for j in mont.juntas}

    def caminho(b):
        out = []
        while b > 1:
            out.append(por_corpo[b])
            b = mont.pai[b]
        return out          # do corpo para a base

    livres = set()
    for b in sorted(nucleo_corpos, key=lambda x: len(caminho(x))):
        cam = caminho(b)
        abaixo = []
        for j in cam:                 # do corpo em direção à base, até achar junta já livre
            if j.nome in livres:
                break
            abaixo.append(j)
        if not abaixo:
            fail("NUCLEO_SEM_JUNTA_PROPRIA")
        rol = [j for j in abaixo if j.nome.startswith("rolamento")]
        livres.add((rol[0] if rol else abaixo[0]).nome)
    juntas = [M.Junta(j.nome, j.corpo, j.tipo, j.eixo, j.ponto, j.limite, j.rigidez, j.mola_ref, j.q0)
              for j in mont.juntas if j.nome in livres]
    nova = M.Montagem(mont.corpos, mont.pai, mont.local, juntas, mont.igualdades, mont.visuais, {}, {}, None, [])
    nova.chaves["qpos0"] = np.zeros(nova.nq)
    return nova, sorted(livres), sorted(j.nome for j in mont.juntas if j.nome not in livres)
