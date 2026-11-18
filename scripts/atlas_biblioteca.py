"""Consulta OFFLINE ao catálogo experimental ATLAS (somente metadados).

Uso:
  python scripts/atlas_biblioteca.py resumo
  python scripts/atlas_biblioteca.py buscar asml
  python scripts/atlas_biblioteca.py buscar taiwan

Não baixa mídia, não chama APIs, não altera nem é importado no render.
Status 'candidato' NUNCA significa item liberado para produção.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "src/v4/formatos/biblioteca_atlas"


def ler() -> tuple[dict, dict]:
    catalogo = json.loads((BASE / "catalogo.json").read_text(encoding="utf-8"))
    candidatas = json.loads((BASE / "midias_candidatas_chips.json").read_text(encoding="utf-8"))
    return catalogo, candidatas


def liberado_para_render(item: dict) -> bool:
    """Falha fechada: exige liberação editorial E arquivo auditado."""
    return (item.get("estado") == "liberado"
            and item.get("aprovacao_editorial") is True
            and isinstance(item.get("sha256"), str)
            and len(item["sha256"]) == 64
            and bool(item.get("licenca"))
            and bool(item.get("licenca_url"))
            and bool(item.get("credito"))
            and bool(item.get("prova_correspondencia"))
            and bool(item.get("largura")) and bool(item.get("altura")))


def buscar(termo: str, limit: int = 30) -> list[dict]:
    _, cand = ler()
    termo = termo.casefold().strip()
    if not termo:
        return []
    achados = []
    for item in cand["itens"]:
        textos = [item["id"], item["titulo"], item["mostra"], item["destino"]]
        textos += item.get("permite_narrar", [])
        if termo in " ".join(textos).casefold():
            achados.append({
                "id": item["id"],
                "titulo": item["titulo"],
                "status": "LIBERADO" if liberado_para_render(item) else "CANDIDATO_BLOQUEADO",
                "pagina": item["pagina"],
                "licenca": item["licenca"],
                "mostra": item["mostra"],
                "proibicoes": item["nao_comprova"],
            })
    return achados[:limit]


def resumo() -> dict:
    catalogo, cand = ler()
    return {
        "versao": catalogo["versao"],
        "status": catalogo["status"],
        "mapas_referenciados": len(catalogo["cartografia"]),
        "composicoes": len(catalogo["composicoes"]),
        "imagens_candidatas": len(cand["itens"]),
        "imagens_liberadas_dessas_candidatas": sum(liberado_para_render(x) for x in cand["itens"]),
        "avisos": [
            "Candidatas nao se confundem com as 7 midias preexistentes do indice comprovado.",
            "Catalogo experimental nao alimenta o motor aprovado.",
            "As restricoes sobre o que cada imagem NAO comprova sao obrigatorias.",
        ],
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Consulta offline Biblioteca ATLAS")
    sub = ap.add_subparsers(dest="comando", required=True)
    sub.add_parser("resumo")
    busca = sub.add_parser("buscar")
    busca.add_argument("termo")
    args = ap.parse_args()
    result = resumo() if args.comando == "resumo" else buscar(args.termo)
    print(json.dumps(result, indent=2, ensure_ascii=False))
