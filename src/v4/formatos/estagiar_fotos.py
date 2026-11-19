"""Estagia fotos já comprovadas no catálogo compartilhado, sem nova curadoria.

Reutilizável para qualquer episódio/documentário. Lê somente os asset_ids das
cenas foto; nunca infere aprovação por haver um download bem-sucedido.
A saída é um OVERLAY efêmero do catálogo V4/V3 com arquivo_local verificado.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from PIL import Image

_DOMINIOS = {"upload.wikimedia.org", "thumb.wikimedia.org"}
_SHA = re.compile(r"^[0-9a-f]{64}$")
_EXT = (".jpg", ".jpeg", ".png")
_LIMITE = 24_000_000


def validar_fonte(item: dict) -> None:
    url = str(item.get("url") or "")
    p = urlsplit(url)
    if p.scheme != "https" or p.hostname not in _DOMINIOS or p.username or p.password:
        raise ValueError("somente mídia HTTPS em domínios de arquivo Commons aprovados")
    if not _SHA.fullmatch(str(item.get("sha256_origem") or "")):
        raise ValueError("foto sem SHA-256 curado")
    if item.get("natureza") != "foto" or not item.get("licenca") or not item.get("credito"):
        raise ValueError("catálogo sem natureza, licença e crédito existentes")
    if (item.get("prova") or {}).get("midia_corresponde") is not True:
        raise ValueError("foto ainda sem correspondência factual inspecionada")
    if not urlsplit(str(item.get("pagina") or "")).hostname == "commons.wikimedia.org":
        raise ValueError("página de proveniência Commons ausente")


def baixar_limitado(url: str) -> bytes:
    """Não aceita redirects para host diferente do Commons nem mídia imensa."""
    import requests
    atual = url
    for _ in range(4):
        u = urlsplit(atual)
        if u.scheme != "https" or u.hostname not in _DOMINIOS:
            raise ValueError("redirecionamento fora de Commons bloqueado")
        with requests.get(
            atual, headers={"User-Agent": "CoringaExplica/1.0 (github.com/Heitor2404/coringa-news)"},
            timeout=45, stream=True, allow_redirects=False
        ) as resposta:
            if resposta.status_code in (301, 302, 303, 307, 308):
                destino = resposta.headers.get("Location")
                if not destino:
                    raise ValueError("redirecionamento sem destino")
                atual = urljoin(atual, destino)
                continue
            resposta.raise_for_status()
            tamanho = 0
            buf = io.BytesIO()
            for parte in resposta.iter_content(chunk_size=1 << 18):
                tamanho += len(parte)
                if tamanho > _LIMITE:
                    raise ValueError("imagem excedeu limite de 24 MB")
                buf.write(parte)
            return buf.getvalue()
    raise ValueError("redirecionamentos excessivos")


def foto_cenas(contrato: dict) -> set[str]:
    ids = set()
    for cena in contrato.get("cenas") or []:
        m = cena.get("midia") or {}
        if m.get("tipo") == "foto":
            nome = m.get("asset_id")
            if not isinstance(nome, str) or not nome:
                raise ValueError("foto de cena sem asset_id")
            ids.add(nome)
    return ids


def preparar(contrato: dict, catalogo: dict, saida: Path, baixar=None) -> dict:
    """Reusa catálogo por SHA, não cria mídia nem altera a identidade do asset."""
    saida = Path(saida)
    if saida.is_absolute() or ".." in saida.parts:
        raise ValueError("saída deve ser caminho relativo ao workspace")
    if not saida.parts:
        raise ValueError("saída vazia")
    ids = foto_cenas(contrato)
    itens = {x.get("id"): x for x in catalogo.get("itens") or []}
    atualizados = [dict(x) for x in catalogo.get("itens") or []]
    encontrados = {}
    falhas = []
    for nome in sorted(ids):
        item = itens.get(nome)
        if not item:
            falhas.append({"asset_id": nome, "erro": "não existe no catálogo curado"})
            continue
        try:
            validar_fonte(item)
            sha = item["sha256_origem"]
            formato = Path(urlsplit(item["url"]).path).suffix.lower()
            if formato not in _EXT:
                raise ValueError("extensão de foto não suportada")
            destino = saida / f"{sha}{formato}"
            if destino.is_file():
                bruto = destino.read_bytes()
                origem = "cache SHA"
            else:
                bruto = (baixar or baixar_limitado)(item["url"])
                origem = "fonte Commons"
            if not isinstance(bruto, bytes) or not 4096 <= len(bruto) <= _LIMITE:
                raise ValueError("resposta não é arquivo de imagem válido")
            if hashlib.sha256(bruto).hexdigest() != sha:
                raise ValueError("SHA-256 diverge da aprovação original: mídia mudou")
            with Image.open(io.BytesIO(bruto)) as im:
                im.verify()
            with Image.open(io.BytesIO(bruto)) as im:
                if im.format not in ("JPEG", "PNG") or min(im.size) < 480:
                    raise ValueError("resolução/formato insuficiente para vídeo")
                dimensoes = list(im.size)
            declarado = item.get("wh")
            if declarado and dimensoes != declarado:
                raise ValueError("dimensões não correspondem ao catálogo original")
            destino.parent.mkdir(parents=True, exist_ok=True)
            if not destino.is_file():
                destino.write_bytes(bruto)
            encontrados[nome] = {
                "arquivo_local": destino.as_posix(), "sha256": sha,
                "wh": dimensoes, "origem": origem,
                "estado": "BYTES_CONFERIDOS_SEM_APROVACAO_EDITORIAL"
            }
        except Exception as e:
            falhas.append({"asset_id": nome, "erro": f"{type(e).__name__}: {str(e)[:180]}"})
    for item in atualizados:
        if item.get("id") in encontrados:
            item["arquivo_local"] = encontrados[item["id"]]["arquivo_local"]
    return {
        "catalogo": {**catalogo, "itens": atualizados},
        "relatorio": {"solicitadas": len(ids), "recuperadas": len(encontrados),
                      "originais": encontrados, "falhas": falhas,
                      "autorizacao_publicar": False, "autorizacao_editorial": False}
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("contrato", type=Path)
    ap.add_argument("catalogo_saida", type=Path)
    ap.add_argument("relatorio_saida", type=Path)
    ap.add_argument("--pasta", default="stage_acervo/fotos")
    a = ap.parse_args(argv)
    from src.v4.formatos.ponte_biblioteca import catalogo
    c = json.loads(a.contrato.read_text(encoding="utf8"))
    resultado = preparar(c, catalogo(), Path(a.pasta))
    a.catalogo_saida.parent.mkdir(parents=True, exist_ok=True)
    a.relatorio_saida.parent.mkdir(parents=True, exist_ok=True)
    a.catalogo_saida.write_text(json.dumps(resultado["catalogo"], ensure_ascii=False, indent=2),encoding="utf8")
    a.relatorio_saida.write_text(json.dumps(resultado["relatorio"], ensure_ascii=False, indent=2),encoding="utf8")
    print(json.dumps(resultado["relatorio"], ensure_ascii=False)[:5000])
    return 0 if not resultado["relatorio"]["falhas"] else 1


if __name__=="__main__":
    raise SystemExit(main())
