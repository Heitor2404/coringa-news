"""E41 — montagem com suporte real → grupos rígidos → articulações → pares
superiores comprovados → solver E18 → oráculos → MP4 (renderer compartilhado).

Uso: python -m src.v4.formatos.pipeline_e41 <arquivo.step> <saida> [--voltas 3] [--quadros 240]
     [--sem-render]

Sem nomes de equipamento: toda decisão vem de vinculos_e41 / lobulos_e41 /
transmissao_e41. Hipóteses declaradas no relatório:
- BASE = portador do conjunto de roletes externo do par lobulado aceito;
- juntas não necessárias ao núcleo ficam CONGELADAS (listadas), e entre juntas
  coaxiais em série a de ROLAMENTO (elementos rolantes comprovados) é a livre;
- giro dos roletes nos seus pinos e dos anéis/esferas não é modelado.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from . import brep_e35 as B
from . import editorial_e42 as E42
from . import gates_qualidade_e21 as Q
from . import lobulos_e41 as LB
from . import multicorpo_e18 as M
from . import transmissao_e41 as TR
from . import vinculos_e41 as V
from .pipeline_e35 import _limpar


def interferencia_nucleo(formas, mont, grupo_de, pares_alvo, qs, quadros):
    """Volume exato (OCC) entre os pares de sólidos indicados, nas poses dadas."""
    from .oraculos_e35 import _mover, _volume
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    pior, por_quadro = dict(volume_mm3=0.0), {}
    for i in quadros:
        X = mont.poses(qs[i])
        mov = {}
        for k in {a for a, _ in pares_alvo} | {b for _, b in pares_alvo}:
            T = X[grupo_de[k]].copy()
            T[:3, 3] *= 1000.0
            mov[k] = _mover(formas[k].wrapped, T)
        for a, b in pares_alvo:
            com = BRepAlgoAPI_Common(mov[a], mov[b]).Shape()
            v = _volume(com)
            if v > 1e-6:
                from OCP.Bnd import Bnd_Box
                from OCP.BRepBndLib import BRepBndLib
                bb = Bnd_Box()
                BRepBndLib.Add_s(com, bb)
                x0, y0, z0, x1, y1, z1 = bb.Get()
                # menor lado da caixa alinhada aos eixos: NÃO é profundidade (lente curva);
                # a profundidade vem da conjugação 2D (penetracao_max_mm)
                esp = float(min(x1 - x0, y1 - y0, z1 - z0))
                por_quadro.setdefault(str(i), []).append([int(a), int(b), v, esp])
                if v > pior["volume_mm3"]:
                    pior = dict(volume_mm3=v, quadro=int(i), par=[int(a), int(b)], menor_lado_caixa_mm=esp)
    return dict(metodo="interseção booleana exata OCC (perfil × roletes) nas poses do solver",
                quadros_auditados=len(quadros), pares_por_quadro=len(pares_alvo),
                quadros_com_interferencia=len(por_quadro), pior=pior, por_quadro=por_quadro)


def _marca(rel, etapa, t0=[None]):
    import sys
    agora = time.time()
    rel.setdefault("tempos_s", {})[etapa] = round(agora - (t0[0] or agora), 1)
    t0[0] = agora
    print("E41-ETAPA", etapa, rel["tempos_s"][etapa], file=sys.stderr, flush=True)


def executar(step, saida, voltas=3.0, quadros=240, renderizar=True, n_theta=120, fonte=None):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    rel = dict(arquivo=str(step), publish=False, visual_approved=False, homologacao_visual="NAO_HOMOLOGADO")
    t = time.time()
    leitura = B.ler(step, tesselar=False)
    corpos = leitura["corpos"]
    rel["leitura"] = dict(solidos=len(corpos), unidade=leitura["unidade"], sha256=leitura["sha256"],
                          segundos=round(time.time() - t, 1))
    _marca(rel, "leitura")
    an = V.analisar(leitura)
    _marca(rel, "vinculos")
    rel["vinculos"] = V.resumo(leitura, an)
    conjuntos = LB.conjuntos_cilindricos(corpos, convexo=True)      # uma vez só (busca por consenso é cara)
    tr = TR.analisar_transmissao(leitura, an, lambda ids: E42.formas(leitura, ids), n_theta, conjuntos)
    _marca(rel, "transmissao")
    aceitos = [p for p in tr.get("pares", []) if p["lobulado"].get("aceito")]
    rel["transmissao"] = dict(conjuntos_roletes=len(tr.get("conjuntos_roletes", [])),
                              candidatos=[dict(corpo=p["corpo"], nome=p["nome"], motivo=p.get("motivo"),
                                               lobulado={k: v for k, v in p["lobulado"].items()
                                                         if k not in ("alternativas",)},
                                               alternativas=p["lobulado"].get("alternativas"),
                                               portador_roletes=p.get("portador_roletes"),
                                               entrada_candidatos=p.get("entrada_candidatos"),
                                               saidas=p.get("saidas")) for p in tr.get("pares", [])])
    if not aceitos:
        rel["resultado"] = "RECUSADO:" + tr.get("motivo", "NENHUM_PAR_LOBULADO_COMPROVADO")
        return _gravar(rel, saida)
    # papéis estruturais: precisam ser únicos e coerentes entre os pares aceitos
    bases = {p["portador_roletes"] for p in aceitos}
    entradas = {tuple(p["entrada_candidatos"]) for p in aceitos}
    saidas_g = {s["portador"] for p in aceitos for s in p["saidas"]}
    razoes = {round(p["lobulado"]["razao_derivada"], 12) for p in aceitos}
    faltas = []
    if len(bases) != 1 or None in bases:
        faltas.append(f"PORTADOR_DOS_ROLETES_AMBIGUO:{sorted(map(str, bases))}")
    if len(entradas) != 1 or len(next(iter(entradas))) != 1:
        faltas.append(f"ENTRADA_AMBIGUA:{sorted(entradas)}")
    if len(saidas_g) > 1 or None in saidas_g:
        faltas.append(f"SAIDA_AMBIGUA:{sorted(map(str, saidas_g))}")
    if len(razoes) != 1:
        faltas.append(f"RAZOES_DIVERGENTES:{sorted(razoes)}")
    if faltas:
        rel["resultado"] = "RECUSADO:EVIDENCIA_INSUFICIENTE"
        rel["faltas"] = faltas
        return _gravar(rel, saida)
    uf = V.uniao_de(an)
    base = bases.pop()
    entrada = next(iter(entradas))[0]
    k = razoes.pop()
    mont0, idx, info, uf = TR.montar(leitura, an, base)
    perfis = [uf.achar(p["corpo"]) for p in aceitos]
    nucleo = {g: idx[g] for g in [entrada, *perfis, *saidas_g] if g in idx}
    if len(nucleo) != 1 + len(perfis) + len(saidas_g):
        rel["resultado"] = "RECUSADO:NUCLEO_FORA_DO_MODELO_CONEXO"
        return _gravar(rel, saida)
    mont, livres, congeladas = TR.podar(mont0, list(nucleo.values()))
    d = np.asarray(next(c for c in conjuntos
                        if any(abs(c["R"] - p["lobulado"]["raio_roletes_mm"]) < 1e-6 for p in aceitos))["eixo"])
    lin = {g: TR.linha_angular(mont, nucleo[g], d) for g in nucleo}
    G = [lin[g] - k * lin[entrada] for g in perfis] + [lin[s] - lin[perfis[0]] for s in saidas_g]
    rel["modelo"] = dict(base_grupo=int(base), base_hipotese="portador do conjunto de roletes externo do par lobulado",
                         entrada_grupo=int(entrada), perfis=[int(p) for p in perfis], saida=[int(s) for s in saidas_g],
                         razao=k, grupos_no_modelo=len(idx), solidos_fora_do_modelo=len(info["fora_do_modelo"]),
                         juntas_livres=livres, juntas_congeladas=len(congeladas))
    alvos = np.linspace(0, 2 * math.pi * voltas, quadros)
    t = time.time()
    traj, s = TR.trajetoria(mont, lin[entrada], np.array(G), alvos)
    qs = [q for q, _ in traj]
    _marca(rel, "trajetoria")
    ang = lambda g: np.array([lin[g] @ q for q in qs])
    rel["solver"] = dict(segundos=round(time.time() - t, 1), mobilidade_max=max(i["mobilidade"] for _, i in traj),
                         residuo_max=max(i["residuo"] for _, i in traj),
                         entrada_graus=float(np.degrees(ang(entrada)[-1])),
                         saida_graus=float(np.degrees(ang(next(iter(saidas_g)) if saidas_g else perfis[0])[-1])),
                         razao_observada=float(ang(next(iter(saidas_g)) if saidas_g else perfis[0])[-1] / ang(entrada)[-1]))
    # Oráculo independente: interferência exata perfil × roletes (anel e saída)
    grupo_de = {}
    for g, membros in an["grupos"].items():
        if uf.achar(g) in idx:
            for m in membros:
                grupo_de[m] = idx[uf.achar(g)]
    # corpos congelados seguem o pai: idx já aponta ao corpo da Montagem correspondente
    alvo_pares = []
    for p in aceitos:
        # superfícies de contato do par: roletes com o raio EXATO usado na conjugação
        conj_ext = [c for c in conjuntos if p["corpo"] not in c["corpos"]
                    and abs(c["R"] - p["lobulado"]["raio_roletes_mm"]) < 1e-6
                    and abs(c["raio"] - p["lobulado"]["raio_rolete_mm"]) < 1e-6]
        for c in conj_ext:
            if abs(c["z"] - np.dot(corpos[p["corpo"]].centroide, np.asarray(c["eixo"]))) < 3:
                alvo_pares += [(p["corpo"], r) for r in c["corpos"] if r in grupo_de]
        for sd in p["saidas"]:
            for c in conjuntos:
                if abs(c["R"] - sd["R"]) < 1e-6 and abs(c["raio"] - sd["raio_rolete_mm"]) < 1e-6 and abs(c["z"] - np.dot(corpos[p["corpo"]].centroide, np.asarray(c["eixo"]))) < 3:
                    alvo_pares += [(p["corpo"], r) for r in c["corpos"] if r in grupo_de]
    alvo_pares = sorted(set(alvo_pares))
    formas = E42.formas(leitura, sorted({a for a, _ in alvo_pares} | {b for _, b in alvo_pares}))
    if not alvo_pares:
        rel["resultado"]="RECUSADO:SEM_PARES_AUDITADOS"
        return _gravar(rel,saida)
    rel["pares_auditados"] = len(alvo_pares)
    _marca(rel, "preparar_auditoria")
    rel["interferencia_brep"] = interferencia_nucleo(formas, mont, grupo_de, alvo_pares, qs,
                                                     list(range(0, quadros, max(1, quadros // 8))))
    _marca(rel, "interferencia")
    if renderizar:
        from . import filme_e18 as F
        ids = sorted(grupo_de)
        sol = E42.formas(leitura, ids)
        visuais = []
        for i in ids:
            v, f = sol[i].tessellate(0.1, 0.2)
            visuais.append(M.Visual(grupo_de[i], corpos[i].nome, np.eye(4),
                                    np.array([p.toTuple() for p in v]) * 1e-3, np.array(f, int),
                                    np.array([.72, .76, .79, 1.])))
        # Exibe só o que participa da transmissão: grupos do núcleo + corpos de contato dos
        # pares superiores. Estrutura fixa e subsistemas congelados ficam fora (declarado).
        exibir_corpos = set(nucleo.values()) | {grupo_de[r] for _, r in alvo_pares}
        mont.visuais = [v for v in visuais if v.corpo in exibir_corpos]
        rel["render_exibicao"] = dict(regra="núcleo da transmissão + superfícies de contato dos pares",
                                      solidos_exibidos=len(mont.visuais), solidos_ocultos=len(visuais) - len(mont.visuais))
        oculta = True
        serie = ang(next(iter(saidas_g)) if saidas_g else perfis[0])
        serie = serie - serie[0]
        medida = dict(tipo="angulo", unidade="rad", rotulo="Rotação do eixo de saída")
        from .oraculos_e35 import carregar_classes
        classe = next((k2 for k2, c2 in carregar_classes().items()
                       if c2["assinatura"].get("par") == "engrenamento_lobulado"), "par_lobulado")
        nome_classe = carregar_classes().get(classe, {}).get("nome_exibicao", classe)
        rel["classe_pela_assinatura"] = classe
        qa = dict(id="e41_" + classe, mobilidade_max=rel["solver"]["mobilidade_max"],
                  residuo_max=rel["solver"]["residuo_max"], natureza="CAD de projeto; vínculos e pares inferidos",
                  homologacao_visual="NAO_HOMOLOGADO", publish=False, visual_approved=False)
        if fonte is not None and fonte.get("step_sha256")!=leitura["sha256"]:
            raise ValueError("E42-FONTE_HASH")
        modelo = dict(id="e41_" + classe, titulo=nome_classe,
                      credito=("CAD: "+fonte["url"].split("github.com/")[-1] if fonte else "CAD local · procedência pendente"),
                      licenca=(fonte["licenca_informada"] if fonte else "NAO_VERIFICADA"), natureza=("Estrutura fixa oculta · " if oculta else "") +
                      f"entrada {voltas:g} voltas · razão {k:.4f} deduzida da geometria",
                      estilo_visual="e33", exportar_palco=True, fonte_cad=fonte,
                      camera_alvos=[nucleo[g] for g in perfis])
        acion = {"entrada": {j: float(c) for j, c in enumerate(lin[entrada]) if c}}
        qa = F.renderizar_trajetoria(mont, acion, qs, medida, serie, qa, modelo, saida, varrido="entrada")
        qa["interferencia_brep"]=rel["interferencia_brep"]
        qa["transmissao_observada"]=E42.transmissao(ang(entrada),serie,k,F.FPS)
        qa["escopo_auditoria"]="apenas pares perfil-roletes selecionados; componentes omitidos/congelados"
        qa=Q.classificar(qa)
        rel["gates"]={x:qa[x] for x in ("estado","estado_execucao","validacao_externa",
                            "verificacao_contato","liberado_para_publicacao")}
        rel["render"] = {k2: qa.get(k2) for k2 in ("sha256_mp4", "sha256_quadros_rgb", "verificacao_video", "camera",
                            "palco_cad","eventos_trajetoria","transmissao_observada","apresentacao_e33")}
        (saida/"QA.json").write_text(json.dumps(_limpar(qa),ensure_ascii=False,indent=2))
    _marca(rel, "fim")
    rel["resultado"] = "MP4_GERADO" if renderizar else "SOLVER_E_ORACULOS"
    return _gravar(rel, saida)


def _gravar(rel, saida):
    (Path(saida) / "E41_relatorio.json").write_text(json.dumps(_limpar(rel), ensure_ascii=False, indent=2, default=str))
    return rel


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("step")
    p.add_argument("saida")
    p.add_argument("--voltas", type=float, default=3.0)
    p.add_argument("--quadros", type=int, default=240)
    p.add_argument("--sem-render", action="store_true")
    a = p.parse_args()
    rel = executar(a.step, a.saida, a.voltas, a.quadros, not a.sem_render)
    print("E41-RESULTADO", json.dumps(_limpar(dict(resultado=rel["resultado"], modelo=rel.get("modelo"),
                                                   solver=rel.get("solver"), faltas=rel.get("faltas"),
                                                   interferencia={k: v for k, v in (rel.get("interferencia_brep") or {}).items()
                                                                  if k != "por_quadro"},
                                                   render=rel.get("render"))), ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
