"""Reidrata originais verificados por SHA na Biblioteca V3 EXISTENTE.

A fonte permanece CANDIDATA: ingerir na V3 não libera uso comercial, não
atesta adequação semântica e não autoriza publicar. A receita (provider+ID+SHA)
é versionável; os bytes vão ao armazenamento por SHA da própria V3.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

_SHA = re.compile(r"^[0-9a-f]{64}$")
_ENTRY = re.compile(r"^[0-9]+_[A-Za-z0-9]+$")
_DOMINIOS = {"www.nist.gov", "nist.gov"}
_EXT = {".mp4", ".webm", ".mov"}


def validar_item(it: dict) -> None:
    if (it.get("provider") != "kaltura" or
        str(it.get("partner_id") or "") != "684682" or
        not _ENTRY.fullmatch(str(it.get("entry_id") or ""))):
        raise ValueError("fonte não reconhecida: exige Kaltura NIST comprovado")
    if urlsplit(str(it.get("pagina") or "")).hostname not in _DOMINIOS:
        raise ValueError("página original não pertence ao NIST")
    if not _SHA.fullmatch(str(it.get("sha256") or "")):
        raise ValueError("sha256 esperado ausente ou inválido")
    if not re.fullmatch(r"[a-z0-9_]{4,64}", str(it.get("id") or "")):
        raise ValueError("ID de fonte inválido")
    if not str(it.get("titulo") or "").strip() or not str(it.get("credito") or "").strip():
        raise ValueError("metadados originais ausentes")
    if it.get("aprovado_publicacao") is not False:
        raise ValueError("receita não concede publicação")
    formato = str(it.get("formato") or "")
    if formato not in ("best[ext=mp4]/best",
                       "best[height<=720][ext=mp4]/worst[ext=mp4]/worst"):
        raise ValueError("formato de download não auditado")


def sha256_arquivo(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def baixar_kaltura(it: dict, pasta: Path) -> Path:
    """Somente ao invocar CLI. Nenhuma chamada IA e nenhum fallback de licença."""
    nome = it["id"]
    destino = str(pasta / (nome + ".%(ext)s"))
    subprocess.run([
        "yt-dlp", "--no-playlist", "--no-progress", "--no-warnings",
        "--socket-timeout", "22", "--retries", "1", "--fragment-retries", "1",
        "--max-filesize", "95M", "-f", it["formato"],
        "--merge-output-format", "mp4", "--output", destino,
        f"kaltura:{it['partner_id']}:{it['entry_id']}",
    ], check=True, timeout=400)
    candidatos = [x for x in pasta.glob(nome + ".*") if x.suffix.lower() in _EXT]
    if len(candidatos) != 1:
        raise ValueError(f"{nome}: Kaltura não devolveu vídeo único")
    return candidatos[0]



def provar_video(p: Path) -> dict:
    "Confere que os bytes são vídeo decodificável, não um arquivo renomeado."
    saida=subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height:format=duration",
        "-of", "json", str(p)
    ], text=True, timeout=35)
    d=json.loads(saida)
    stream=(d.get("streams") or [{}])[0]
    formato=d.get("format") or {}
    largura, altura=stream.get("width",0),stream.get("height",0)
    dur=float(formato.get("duration") or 0)
    if min(largura,altura)<360 or dur<4:
        raise ValueError("clipe não atende qualidade técnica mínima")
    return {"dimensoes":[largura,altura], "duracao_s":round(dur,3)}


def reidratar(it: dict, pasta: Path, bib, baixar=None) -> dict:
    """Reconcilia arquivo SHA e V3. baixar é substituível apenas em testes."""
    validar_item(it)
    pasta=Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    existentes=[p for p in pasta.glob(it["id"]+".*") if p.suffix.lower() in _EXT]
    if len(existentes)>1:
        raise ValueError("fontes duplicadas com mesma identidade")
    p=existentes[0] if existentes else (baixar or baixar_kaltura)(it,pasta)
    if not p.resolve().is_relative_to(pasta.resolve()):
        raise ValueError("fonte fora do workspace de ingestão")
    if not p.is_file() or p.suffix.lower() not in _EXT:
        raise ValueError("arquivo fonte não é vídeo")
    sha=sha256_arquivo(p)
    if sha != it["sha256"]:
        raise ValueError(f"{it['id']}: SHA divergente, fonte mudou; revalidar antes de usar")
    if p.stat().st_size>100_000_000 or p.stat().st_size<50_000:
        raise ValueError("arquivo inválido ou grande demais")
    metadados_video=provar_video(p)
    # Importante: nenhuma licença é atribuída por inferência automática.
    # Sem confirmação específica, o acervo V3 deve deixar uso comercial indefinido.
    meta={"titulo":it["titulo"],"desc":it.get("descricao") or "",
          "mostra":it.get("mostra") or "CANDIDATO, inspeção parcial",
          "credito":it["credito"],"pagina":it["pagina"],"url":it["pagina"],
          "licenca_prova":"CANDIDATO: conferir direitos do item NIST, inclusive terceiros",
          "lugar":it.get("local") or "NIST, Estados Unidos"}
    registro=bib.ingerir(p,meta,tema=it.get("tema") or "semicondutores")
    d=bib.obter(registro["id"])
    if d.get("uso_comercial") == "sim":
        raise ValueError("candidato não pode se tornar autorizado automaticamente")
    return {"fonte_id":it["id"],"id_v3":registro["id"],"sha256":sha,
            "reuso":registro["reuso"],"uso_comercial":d.get("uso_comercial"),
            "video":metadados_video,
            "status":"INGESTAO_V3_CANDIDATA_SEM_APROVACAO"}


def executar(manifesto:dict, pasta:Path, db:Path, armazem:Path,
             manifesto_v3:Path, baixar=None) -> dict:
    if manifesto.get("versao")!=1 or not isinstance(manifesto.get("itens"),list):
        raise ValueError("receita inválida")
    itens=manifesto["itens"]
    if not itens or len({x.get("id") for x in itens})!=len(itens):
        raise ValueError("receita vazia ou com IDs duplicados")
    for it in itens:
        validar_item(it)
    from src.v3.biblioteca import Biblioteca
    bib=Biblioteca(db=db,armazem=armazem)
    try:
        resultados=[reidratar(it,pasta,bib,baixar=baixar) for it in itens]
        bib.exportar_manifesto(manifesto_v3)
        return {"itens":resultados,"publicado":False,"aprovado":False,
                "v3_integrada":True,"manifesto_v3":str(manifesto_v3)}
    finally:
        bib.fechar()


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("receita",type=Path)
    ap.add_argument("pasta",type=Path)
    ap.add_argument("db",type=Path)
    ap.add_argument("armazem",type=Path)
    ap.add_argument("manifesto_v3",type=Path)
    a=ap.parse_args(argv)
    r=executar(json.loads(a.receita.read_text(encoding="utf8")),
               a.pasta,a.db,a.armazem,a.manifesto_v3)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
