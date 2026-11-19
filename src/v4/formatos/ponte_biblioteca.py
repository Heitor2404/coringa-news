"""Ponte OPT-IN da biblioteca global V3 para o catálogo comprovado do ATLAS.

Não cria banco paralelo. A V3 continua dona do arquivo e do sha256.
A lista de autorizações é uma evidência editorial explícita, por SHA, separada
da classificação automática de licenças e do score textual de busca.

Ativar só com CORINGA_ATLAS_APROVACOES_V3=<arquivo_json>. Ausente => V4 legado.
Não publica, não baixa mídias e não reescreve biblioteca_comprovada.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from src.v4 import viabilidade

_SHA = re.compile(r"^[0-9a-f]{64}$")
_EXT = {".mp4", ".webm", ".mov", ".jpg", ".jpeg", ".png"}
_VIDEO = {".mp4", ".webm", ".mov"}


def _aprovacoes() -> tuple[list[dict], str]:
    arq = os.environ.get("CORINGA_ATLAS_APROVACOES_V3")
    if not arq:
        return [], ""
    p = Path(arq)
    if not p.is_file():
        raise RuntimeError("ATLAS: manifesto de aprovações V3 informado mas ausente")
    dados = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(dados, dict) or dados.get("versao") != 1 or not isinstance(dados.get("aprovacoes"), list):
        raise RuntimeError("ATLAS: manifesto V3 inválido; exige {versao:1,aprovacoes:[...]}")
    return dados["aprovacoes"], str(p)


def catalogo() -> dict:
    """Catálogo comprovado de formatos, eventualmente ampliado por itens APROVADOS da V3.

    Se o banco/arquivo mudar após homologação, SHA e prova não batem e a operação falha.
    Não faz fallback para outro vídeo de um assunto parecido.
    """
    base = viabilidade.carregar()
    provas, _ = _aprovacoes()
    if not provas:
        return base
    from src.v3.biblioteca import Biblioteca

    db = Path(os.environ.get("BIBLIOTECA_DB") or BibliotecaDB())
    if not db.is_file():
        raise RuntimeError("ATLAS: banco global V3 indisponível; mídia manual não pode ser aprovada sem arquivo")
    bib = Biblioteca(db=db)
    try:
        itens = list(base.get("itens") or [])
        ids = {it["id"] for it in itens}
        hashes = {it.get("sha256_origem") for it in itens if it.get("sha256_origem")}
        reprovados = {r.get("id") for r in base.get("reprovados") or []}
        for ap in provas:
            if not isinstance(ap, dict):
                raise RuntimeError("ATLAS: aprovação de mídia V3 inválida")
            mid = ap.get("midia_id")
            sha = ap.get("sha256")
            prova = ap.get("prova") or {}
            if not isinstance(mid, str) or not mid.startswith("cm-") or not isinstance(sha, str) or not _SHA.fullmatch(sha):
                raise RuntimeError("ATLAS: aprovação V3 precisa de id cm-* e sha256 válido")
            if not isinstance(prova, dict) or not (prova.get("midia_corresponde") is True
                    and prova.get("revisor") and prova.get("evidencia")
                    and prova.get("acontecimento") and prova.get("licenca_evidencia")):
                raise RuntimeError(f"ATLAS: {mid} sem revisão editorial explícita do conteúdo")
            reg = bib.obter(mid)
            if not reg or reg.get("sha256") != sha or reg.get("uso_comercial") != "sim" or reg.get("ia"):
                raise RuntimeError(f"ATLAS: {mid} não existe, mudou, é IA ou não tem uso comercial confirmado")
            if sha in hashes:
                raise RuntimeError(f"ATLAS: {mid} já consta no acervo comprovado pelo SHA; reuse o ID existente")
            hashes.add(sha)
            ext = (reg.get("ext") or "").lower()
            if ext not in _EXT or (reg.get("tipo") == "video") != (ext in _VIDEO):
                raise RuntimeError(f"ATLAS: {mid} tipo de arquivo incompatível com o registro")
            if not reg.get("licenca") or not reg.get("licenca_prova") or not reg.get("url_pagina") or not reg.get("autor"):
                raise RuntimeError(f"ATLAS: {mid} sem licença comprovada, página e autoria")
            # Validar bytes locais; NÃO chamar Biblioteca.recuperar(), que poderia baixar
            # uma URL que é apenas a página de um vídeo manual do Pexels.
            original = bib.caminho(sha, ext)
            if not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != sha:
                raise RuntimeError(f"ATLAS: {mid} sem original local íntegro na biblioteca V3")
            asset = f"v3:{mid}"
            if asset in ids or asset in reprovados:
                raise RuntimeError(f"ATLAS: ID {asset} duplicado ou reprovado")
            ids.add(asset)
            lic = reg["licenca"]
            cred = reg.get("atribuicao") or f'{reg["autor"]} · {lic}'
            if lic.lower() not in cred.lower():
                cred += f" · {lic}"
            itens.append({
                "id": asset, "titulo": reg.get("titulo") or "",
                "natureza": "video" if reg["tipo"] == "video" else "foto",
                "url": reg.get("url_original") or reg["url_pagina"],
                "pagina": reg["url_pagina"],
                "credito": cred, "licenca": lic, "uso_comercial": "sim",
                "autor": reg["autor"], "ext": ext,
                "sha256_origem": sha, "lugar": [reg.get("local") or ""],
                "mostra": reg.get("mostra") or reg.get("descricao") or "",
                "prova": dict(prova), "origem_biblioteca_v3": mid,
            })
        return {**base, "itens": itens}
    finally:
        bib.fechar()


def inventario_para_diretor(fatos: list[dict], limite: int = 12) -> str:
    """Mídias aprovadas RELEVANTES ao roteiro. Reusa viabilidade._tokens;
    não transforma pesquisa textual em verificação editorial.
    """
    if limite < 1:
        return "(nenhuma mídia solicitada)"
    base = catalogo()
    rep = {it.get("id") for it in base.get("reprovados") or []}
    alvo = viabilidade._tokens(*(str(f.get("texto") or "") for f in fatos))
    pontuados = []
    for it in base.get("itens") or []:
        if it.get("id") in rep or not it.get("licenca") or not it.get("credito"):
            continue
        prova = it.get("prova") or {}
        if prova.get("midia_corresponde") is not True:
            continue
        tags = viabilidade._tokens(it.get("titulo"), it.get("mostra"), " ".join(it.get("termos") or []))
        score = len(alvo & tags)
        if score:
            pontuados.append((score, it))
    pontuados.sort(key=lambda x: (-x[0], x[1]["id"]))
    if not pontuados:
        return "(nenhum registro comprovado pertinente: bloquear pedido de mídia específica)"
    linhas = []
    for score, it in pontuados[:limite]:
        dur = f", duração original {it['duracao']} s" if it.get("duracao") else ""
        lines = f"- {it['id']}: {it.get('natureza', 'foto')} comprovada, {it.get('mostra') or it.get('titulo') or 'sem descrição'}, licença {it['licenca']}{dur}; crédito {it['credito']}"
        linhas.append(lines[:600])
    return "\n".join(linhas)


def BibliotecaDB() -> str:
    from src.v3.biblioteca import DB_PADRAO
    return str(DB_PADRAO)


def bytes_originais(it: dict) -> tuple[bytes, str]:
    """Recupera o arquivo LOCAL da V3 por SHA, jamais pela URL da página da mídia."""
    from src.v3.biblioteca import Biblioteca
    mid, sha = it["origem_biblioteca_v3"], it["sha256_origem"]
    db = Path(os.environ.get("BIBLIOTECA_DB") or BibliotecaDB())
    if not db.is_file():
        raise RuntimeError("ATLAS: banco da biblioteca V3 não está disponível")
    bib = Biblioteca(db=db)
    try:
        reg = bib.obter(mid)
        if not reg or reg["sha256"] != sha:
            raise RuntimeError(f"ATLAS: {mid} teve identidade alterada")
        arq = bib.caminho(sha, (reg.get("ext") or "").lower())
        if not arq.is_file():
            raise RuntimeError(f"ATLAS: arquivo original de {mid} indisponível")
        data = arq.read_bytes()
        if hashlib.sha256(data).hexdigest() != sha:
            raise RuntimeError(f"ATLAS: bytes originais de {mid} não conferem com SHA")
        return data, f"biblioteca-v3:{mid}"
    finally:
        bib.fechar()
