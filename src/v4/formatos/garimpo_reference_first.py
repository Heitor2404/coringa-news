"""Garimpo Reference First: pesquisa alinhada ao PROCESSO, não à palavra 'piston'.

Conecta ao scout de Commons/Archive/Sketchfab já existente. Nenhuma pontuação
por metadados é certificação visual, de licença ou download 3D autorizado.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from src.v4.formatos import referencias_mecanismos as SCOUT

REGRAS = {
    "compressor_alternativo": {
        "pergunta": "Como a valvula de admissao e a descarga de um compressor alternativo trabalham com o pistao?",
        "consultas_en": [
            "reciprocating air compressor suction discharge valves animation",
            "piston compressor cutaway valve operation animation",
        ],
        "termos_principais": ("compressor", "compressed air", "reciprocating"),
        "termos_adicionais": ("piston", "valve", "suction", "discharge", "cutaway", "animation"),
        "contra_exemplos": ("minecraft", "game engine", "lego", "toy", "engine block", "heart shaped"),
    },
    "motor_otto_4t": {
        "pergunta": "Como o motor Otto quatro tempos anima admissao compressao ignicao expansao e escape?",
        "consultas_en": [
            "four stroke Otto gasoline engine valve cutaway animation",
            "spark ignition four stroke engine piston valve animation",
        ],
        "termos_principais": ("engine", "four stroke", "otto", "combustion"),
        "termos_adicionais": ("valve", "spark", "piston", "cutaway", "crankshaft", "animation"),
        "contra_exemplos": ("minecraft", "diesel", "game engine", "electric", "decorative", "heart"),
    },
}
LICENCA_RESTRITA = re.compile(r"non.commercial|(^|[^a-z])nc([^a-z]|$)|no.derivatives|(^|[^a-z])nd([^a-z]|$)", re.I)


def _pontuar(item: dict, regra: dict) -> tuple[int,list[str]]:
    title = str(item.get("titulo") or "").lower()
    reasons = []
    score = 0
    for term in regra["contra_exemplos"]:
        if term in title:
            reasons.append("F-PALAVRA-DE-OUTRO-TIPO:" + term)
    matches = [p for p in regra["termos_principais"] if p in title]
    if not matches:
        reasons.append("F-SEM-TERMO-DO-PROCESSO")
    score += len(matches) * 3
    score += sum(1 for t in regra["termos_adicionais"] if t in title)
    license_name = str(item.get("licenca_declarada") or "")
    if not license_name or license_name == "None":
        reasons.append("F-LICENCA-NAO-CONFIRMADA")
    elif LICENCA_RESTRITA.search(license_name):
        reasons.append("F-LICENCA-RESTRITIVA")
    if item.get("midia") == "modelo_3d":
        reasons.append("F-3D-MESH-RIG-NAO-BAIXADOS")
    return score, reasons


def procurar(processo: str, *, buscar=None, get=None, sem_rede=False) -> dict:
    if processo not in REGRAS:
        raise ValueError("F-PROCESSO-DESCONHECIDO")
    regra = REGRAS[processo]
    base = {
        "schema": "reference-first-discovery-v1",
        "processo_requerido": processo,
        "publicar": False,
        "renderer": None,
        "analise_visual": "NAO_EXECUTADA",
        "candidatos": [],
        "bloqueios": ["F-REFERENCIAS-AINDA-NAO-INSPECIONADAS"],
    }
    if sem_rede:
        return {**base,"estado":"BUSCA_DESLIGADA_NESTA_EXECUCAO"}
    brief = {"id":"ref-first-" + processo,
             "pergunta":regra["pergunta"],"consultas_en":regra["consultas_en"]}
    discovered = SCOUT.descobrir(brief,buscar=buscar,get=get)
    out = []
    for item in discovered.get("candidatos") or []:
        if not isinstance(item,dict):
            continue
        score,flags = _pontuar(item,regra)
        if any(x.startswith("F-PALAVRA-DE-OUTRO-TIPO") or
               x=="F-SEM-TERMO-DO-PROCESSO" for x in flags):
            continue
        out.append({
            "id": item.get("id"),
            "origem": item.get("provedor"),
            "pagina": item.get("pagina"),
            "arquivo": item.get("origem_media"),
            "titulo": item.get("titulo"),
            "midia": item.get("midia"),
            "score_apenas_metadata": score,
            "sinais_de_restricao": flags,
            "licenca_declarada": item.get("licenca_declarada"),
            "pode_reproduzir": False,
            "evidencia_movimento": None,
            "estado":"CANDIDATO_NAO_INSPECIONADO",
        })
    out.sort(key=lambda c:(-c["score_apenas_metadata"],c["id"] or ""))
    return {
        **base,
        "estado":"CANDIDATOS_METADATA_APENAS" if out else "SEM_REFERENCIAS_COMPATIVEIS_POR_TITULO",
        "candidatos":out[:12],
        "erros_de_fonte":discovered.get("erros") or [],
        "rejeitados_por_metadados": max(0,len(discovered.get("candidatos") or [])-len(out)),
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description="Candidatos visuais; nunca aprovar por titulo")
    p.add_argument("processo",choices=sorted(REGRAS))
    p.add_argument("saida")
    p.add_argument("--rede",action="store_true",help="permitir pesquisa remota")
    args=p.parse_args(argv)
    result=procurar(args.processo,sem_rede=not args.rede)
    dest=Path(args.saida)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"estado":result["estado"],
                      "candidatos":len(result["candidatos"]),
                      "publicar":False},ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
