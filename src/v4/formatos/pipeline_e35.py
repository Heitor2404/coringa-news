"""E35 — tema inédito → fontes → geometria → juntas → solver → oráculos → MP4.

Uso:
  python -m src.v4.formatos.pipeline_e35 <candidatos.json> <trabalho> <saida> [--rapido] [--sem-render]

<candidatos.json>: {"consulta": "...", "candidatos": [{"url": ..., "commit"?: ...,
"origem_descoberta": ...}]}. A lista vem da camada de descoberta (E34, busca do
agente); o código não conhece nenhum candidato por nome.

Estágios registrados por candidato e por arquivo (o primeiro que falha é o
motivo): CLONE → LICENCA/TRIAGEM → LEITURA_BREP → TERCEIROS → EIXOS → PARES →
ASSINATURA_DA_CLASSE → ENTRADA → TRAJETORIA → ORACULOS → RENDER.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from . import brep_e35 as B
from . import fontes_e35 as Fo
from . import inferencia_e35 as I
from . import oraculos_e35 as O
from . import pares_e35 as P


def _limpar(o):
    if isinstance(o, dict):
        return {k: _limpar(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_limpar(v) for v in o]
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


def filtrar_terceiros(leitura):
    """Remove sólidos cujo NOME DE PRODUTO indica peça comprada/terceiro."""
    manter, fora = [], list(leitura.get("excluidos", []))
    for c in leitura["corpos"]:
        (fora.append(c.nome) if Fo.TERCEIRO.search(c.nome) else manter.append(c))
    for k, c in enumerate(manter):
        c.indice = k
    return dict(leitura, corpos=manter), fora


def analisar_arquivo(caminho, classe, cfg):
    reg = dict(arquivo=str(caminho))
    t = time.time()
    try:
        leitura = B.ler(caminho, excluir=lambda n: bool(Fo.TERCEIRO.search(n)))
    except Exception as e:  # noqa: BLE001 — registrar o motivo e seguir
        return dict(reg, estagio="LEITURA_BREP", motivo=str(e)), None, None
    reg.update(sha256=leitura["sha256"], unidade=leitura["unidade"], solidos=len(leitura["corpos"]),
               segundos_leitura=round(time.time() - t, 1))
    leitura, terceiros = filtrar_terceiros(leitura)
    reg.update(solidos_terceiros_excluidos=len(terceiros), exemplos_terceiros=terceiros[:8],
               solidos_proprios=len(leitura["corpos"]))
    if len(leitura["corpos"]) < 2:
        return dict(reg, estagio="TERCEIROS", motivo="MENOS_DE_DOIS_SOLIDOS_PROPRIOS"), None, None
    try:
        ctr = I.contrato(leitura)
    except ValueError as e:
        return dict(reg, estagio="JUNTAS", motivo=str(e), entendido=I.diagnostico(leitura)), None, None
    if cfg["assinatura"]["par"] == "pino_rasgo" and not ctr["pares"]:
        return dict(reg, estagio="PARES", motivo="NENHUM_PAR_PINO_RASGO"), None, None
    sig = O.assinatura(classe, cfg, ctr)
    reg["entendido"] = I.diagnostico(leitura)
    reg["assinatura"] = sig
    if not sig["confirmada"]:
        return dict(reg, estagio="ASSINATURA_DA_CLASSE", motivo=sig.get("motivo")), None, None
    return dict(reg, estagio="PRONTO_PARA_SOLVER"), leitura, ctr


def escolher_entrada(leitura, ctr, mont, pares, n_amostras=25):
    """Entre os corpos móveis, a entrada é o que gira 360° atravessando MENOS
    material (interseção exata no B-rep). Registra os valores de todos."""
    avaliados = []
    for corpo in range(len(leitura["corpos"])):
        acion = {"entrada": {corpo: 1.0}}
        alvos = [[a] for a in np.linspace(0, 2 * math.pi, n_amostras)]
        try:
            traj, _ = P.trajetoria(mont, acion, pares, alvos, np.zeros(mont.nq))
        except ValueError as e:
            avaliados.append(dict(corpo=leitura["corpos"][corpo].nome, motivo=str(e)))
            continue
        inter = O.interferencia_brep(leitura, mont, [q for q, _ in traj])
        avaliados.append(dict(corpo=leitura["corpos"][corpo].nome, indice=corpo,
                              interferencia_max_mm3=inter["pior"]["volume_mm3"],
                              quadros_com_interferencia=inter["quadros_com_interferencia"]))
    validos = [a for a in avaliados if "indice" in a]
    if not validos:
        raise ValueError("E35-ENTRADA-NENHUMA")
    escolhido = min(validos, key=lambda a: (a["interferencia_max_mm3"], a["quadros_com_interferencia"]))
    return escolhido["indice"], dict(criterio="menor interferência exata em 360°", avaliados=avaliados,
                                     escolhido=escolhido["corpo"], evidencia="derivado")


def executar(candidatos_json, trabalho, saida, rapido=False, renderizar=True, classes_json=None):
    cand = json.loads(Path(candidatos_json).read_text())
    consulta = cand["consulta"]
    classes = O.carregar_classes(classes_json or "benchmarks/e35_classes_mecanismo.json")
    classe = O.classe_da_consulta(consulta, classes)
    rel = dict(consulta=consulta, classe=classe, candidatos=[], publish=False, visual_approved=False)
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    if classe is None:
        rel["resultado"] = "CLASSE_DE_MECANISMO_NAO_IDENTIFICADA_NA_CONSULTA"
        return rel
    cfg = classes[classe]
    escolhido = None
    for c in cand["candidatos"]:
        reg = dict(url=c["url"], origem_descoberta=c.get("origem_descoberta"))
        rel["candidatos"].append(reg)
        destino = Path(trabalho) / c["url"].rstrip("/").split("github.com/")[-1].replace("/", "__")
        try:
            reg["commit"] = Fo.clonar(c["url"], destino, c.get("commit"))
        except ValueError as e:
            reg.update(estagio="CLONE", motivo=str(e))
            continue
        inv = Fo.inventario(destino, consulta)
        reg.update(licenca=inv["licenca"], identidade_textual=inv["identidade_textual"],
                   arquivos=[dict(a) for a in inv["arquivos"]])
        ok, motivo, steps = Fo.triagem(inv)
        if not ok:
            reg.update(estagio="TRIAGEM", motivo=motivo)
            continue
        reg["analises"] = []
        for a in sorted(steps, key=lambda a: a["bytes"]):
            r, leitura, ctr = analisar_arquivo(destino / a["caminho"], classe, cfg)
            r["arquivo"] = a["caminho"]
            reg["analises"].append(r)
            if leitura is not None and escolhido is None:
                escolhido = (reg, a, leitura, ctr)
        reg["estagio"] = "PRONTO_PARA_SOLVER" if any(x["estagio"] == "PRONTO_PARA_SOLVER" for x in reg["analises"]) \
            else reg["analises"][-1]["estagio"]
    if escolhido is None:
        rel["resultado"] = "NENHUMA_FONTE_CHEGOU_AO_SOLVER"
        (saida / "E35_relatorio.json").write_text(json.dumps(_limpar(rel), ensure_ascii=False, indent=2))
        return rel
    reg, arq, leitura, ctr = escolhido
    rel["escolha"] = dict(url=reg["url"], commit=reg["commit"], arquivo=arq["caminho"], sha256=arq["sha256"],
                          licenca=reg["licenca"])
    rel["contrato"] = _limpar(ctr)
    mont = I.montagem(leitura, ctr)
    pares = [P.ParPinoRasgo(mont, p, ctr) for p in ctr["pares"]]
    entrada, rel["entrada"] = escolher_entrada(leitura, ctr, mont, pares, 13 if rapido else 25)
    n = 120 if rapido else 240
    voltas = 1.0
    alvos = [[a] for a in np.linspace(0, 2 * math.pi * voltas, n)]
    traj, solver = P.trajetoria(mont, {"entrada": {entrada: 1.0}}, pares, alvos, np.zeros(mont.nq))
    qs = [q for q, _ in traj]
    sig = rel["candidatos"] and next(x["assinatura"] for x in reg["analises"] if x.get("assinatura", {}).get("confirmada"))
    par_idx = next(i for i, p in enumerate(ctr["pares"]) if p["corpo_rasgo"] == sig["corpo_rasgo"])
    rel["solver"] = dict(quadros=n, mobilidade_max=max(i["mobilidade"] for _, i in traj),
                         ociosos_max=max(i.get("ociosos", 0) for _, i in traj),
                         residuo_max=max(i["residuo"] for _, i in traj),
                         quadros_com_contato=sum(bool(i["contatos_ativos"]) for _, i in traj))
    if cfg["oraculo"] == "genebra_classico":
        rel["oraculo_classe"] = O.genebra_classico(mont, traj, pares[par_idx], ctr, sig)
    rel["interferencia_brep"] = O.interferencia_brep(leitura, mont, qs,
                                                     range(0, n, 4 if rapido else 2))
    rel["referencia_textual_autor"] = "ver README da fonte (cotas declaradas pelo autor) no relatório"
    rel["readme_trecho"] = None
    serie = np.unwrap(np.array([q[sig["corpo_rasgo"]] for q in qs]))
    serie = serie - serie[0]
    if renderizar:
        from . import filme_e18 as F
        medida = dict(tipo="angulo", unidade="rad", rotulo="Rotação da roda movida")
        qa = dict(id="e35_" + classe, mobilidade_max=rel["solver"]["mobilidade_max"],
                  residuo_max=rel["solver"]["residuo_max"], natureza="CAD de projeto; juntas inferidas da geometria",
                  homologacao_visual="NAO_HOMOLOGADO", publish=False, visual_approved=False)
        nome_rep = reg["url"].rstrip("/").split("/")[-1]
        modelo = dict(id="e35_" + classe, titulo=f"{cfg.get('nome_exibicao', classe)} — {nome_rep}",
                      credito=f"CAD: {reg['url'].split('github.com/')[-1]} · {reg['licenca'].get('spdx')}",
                      licenca=str(reg["licenca"].get("spdx")),
                      natureza="Juntas e contato deduzidos da geometria · prévia privada",
                      estilo_visual="e33", exportar_palco=True,
                      fonte_cad=dict(url=reg["url"], commit=reg["commit"], step_sha256=arq["sha256"]))
        qa = F.renderizar_trajetoria(mont, {"entrada": {entrada: 1.0}}, qs, medida, serie, qa, modelo,
                                     saida, varrido="entrada")
        rel["render"] = {k: qa.get(k) for k in ("sha256_mp4", "sha256_quadros_rgb", "verificacao_video",
                                                "camera", "quadros", "eventos_trajetoria")}
    rel["resultado"] = "MP4_GERADO" if renderizar else "SOLVER_E_ORACULOS"
    (saida / "E35_relatorio.json").write_text(json.dumps(_limpar(rel), ensure_ascii=False, indent=2))
    return rel


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidatos")
    p.add_argument("trabalho")
    p.add_argument("saida")
    p.add_argument("--rapido", action="store_true")
    p.add_argument("--sem-render", action="store_true")
    a = p.parse_args()
    rel = executar(a.candidatos, a.trabalho, a.saida, a.rapido, not a.sem_render)
    print("E35-RESULTADO", json.dumps(dict(consulta=rel["consulta"], classe=rel["classe"],
                                           resultado=rel["resultado"],
                                           estagios=[(c["url"], c.get("estagio"), c.get("motivo")) for c in rel["candidatos"]]),
                                      ensure_ascii=False))


if __name__ == "__main__":
    main()
