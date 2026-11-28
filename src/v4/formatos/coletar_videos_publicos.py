"""Prospecção de vídeos reais de fonte institucional, SEM liberação editorial.

Etapa anterior à curadoria: obtém candidato público, computa SHA dos bytes,
amostra quadros e indexa na Biblioteca V3 já existente. Jamais cria aprovação
no catálogo V4 nem trata descrição, 'domínio público' ou movimento de pixels
como prova da ação física narrada.

Adapter DVIDS é reutilizável entre temas; nenhum país/roteiro é codificado.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw

_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{3,63}$")
_VIDEO_ID = re.compile(r"^[0-9]{5,10}$")
_MAX_BYTES = 66_000_000


def validar_fonte(fonte: dict) -> None:
    if not isinstance(fonte, dict):
        raise ValueError("fonte inválida")
    if not _ID.fullmatch(str(fonte.get("id") or "")):
        raise ValueError("id de acervo inválido")
    provedor=fonte.get("provedor")
    pagina=urlsplit(str(fonte.get("pagina") or ""))
    if (pagina.scheme != "https" or pagina.username or pagina.password
            or pagina.port not in (None, 443) or pagina.query or pagina.fragment):
        raise ValueError("página institucional inválida")
    if provedor=="dvids":
        video_id=str(fonte.get("video_id") or "")
        download_id=str(fonte.get("download_id") or "")
        if not _VIDEO_ID.fullmatch(video_id) or not _VIDEO_ID.fullmatch(download_id):
            raise ValueError("identificadores DVIDS inválidos")
        if (pagina.hostname!="www.dvidshub.net" or
                not pagina.path.startswith("/video/"+video_id+"/")):
            raise ValueError("página de origem não corresponde ao DVIDS")
        situacao="REVISAR_TERCEIROS_E_NAO_ENDOSSO"
    elif provedor=="nist_kaltura":
        if (pagina.hostname!="www.nist.gov" or
                not pagina.path.startswith("/video/") or
                not re.fullmatch(r"[a-z0-9-]+", pagina.path[len("/video/"):]) or
                str(fonte.get("partner_id") or "")!="684682" or
                not re.fullmatch(r"[0-9]_[a-z0-9]{8}",str(fonte.get("entry_id") or ""))):
            raise ValueError("NIST Kaltura exige origem institucional e entry_id comprovado")
        situacao="REVISAR_DIREITOS_DO_ITEM_E_TERCEIROS"
    else:
        raise ValueError("provedor institucional não permitido")
    if (fonte.get("situacao_direitos") != situacao or
            fonte.get("autorizar_publicacao") is not False or
            not str(fonte.get("credito") or "").strip() or
            not str(fonte.get("titulo") or "").strip()):
        raise ValueError("fonte não é candidata privada com direitos pendentes")
    esperado=fonte.get("sha256_esperado")
    if esperado is not None and not re.fullmatch(r"[0-9a-f]{64}",str(esperado)):
        raise ValueError("SHA-256 fixado da fonte inválido")


def sha256_arquivo(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fd:
        for trecho in iter(lambda:fd.read(1024 * 1024),b""):
            h.update(trecho)
    return h.hexdigest()


def baixar_dvids(fonte:dict, destino:Path) -> None:
    """Tenta download público oficial; erro HTTP/acesso não é contornado."""
    import requests
    url = "https://www.dvidshub.net/download/videofile/" + str(fonte["download_id"])
    atual=url
    try:
        for _ in range(4):
            host=urlsplit(atual).hostname or ""
            if host!="dvidshub.net" and host!="www.dvidshub.net" and not host.endswith(".dvidshub.net"):
                raise ValueError("redirecionamento de origem não permitido")
            with requests.get(
                atual, timeout=(15,45), stream=True, allow_redirects=False,
                headers={"User-Agent":"Mozilla/5.0 (Coringa pesquisa documental)",
                         "Referer":fonte["pagina"]}
            ) as r:
                if r.status_code in (301,302,303,307,308):
                    from urllib.parse import urljoin
                    loc=r.headers.get("Location")
                    if not loc: raise ValueError("redirecionamento vazio")
                    atual=urljoin(atual,loc)
                    continue
                r.raise_for_status()
                if "video" not in r.headers.get("Content-Type","").lower() and "octet-stream" not in r.headers.get("Content-Type","").lower():
                    raise ValueError("DVIDS não devolveu arquivo de vídeo")
                if int(r.headers.get("Content-Length") or 0)>_MAX_BYTES:
                    raise ValueError("download acima do limite")
                total=0
                with destino.open("wb") as fd:
                    for bloco in r.iter_content(1024*256):
                        total+=len(bloco)
                        if total>_MAX_BYTES:
                            raise ValueError("download acima do limite")
                        fd.write(bloco)
                if total<50_000: raise ValueError("download incompleto")
                return
        raise ValueError("número de redirecionamentos excedido")
    except Exception:
        destino.unlink(missing_ok=True)
        raise


def baixar_nist(fonte:dict, destino:Path) -> None:
    """Usa Kaltura NIST já suportado pelo yt-dlp, sem acessar rede fora da fonte."""
    if fonte.get("provedor")!="nist_kaltura":
        raise ValueError("provedor não é NIST")
    try:
        subprocess.run([
            "yt-dlp","--no-playlist","--no-progress","--no-warnings",
            "--socket-timeout","20","--retries","1","--fragment-retries","1",
            "--max-filesize","60M",
            "-f","best[height<=720][ext=mp4]/worst[ext=mp4]/worst",
            "--merge-output-format","mp4","-o",str(destino),
            f"kaltura:{fonte['partner_id']}:{fonte['entry_id']}"
        ], check=True, timeout=220)
        if not destino.is_file():
            raise ValueError("Kaltura não devolveu MP4 de acesso público")
    except Exception:
        destino.unlink(missing_ok=True)
        raise


def baixar_fonte(fonte:dict, destino:Path) -> None:
    if fonte["provedor"]=="nist_kaltura":
        baixar_nist(fonte,destino)
    else:
        baixar_dvids(fonte,destino)


def provar_video(p:Path) -> dict:
    s=subprocess.check_output(
        ["ffprobe","-v","error","-select_streams","v:0",
         "-show_entries","stream=width,height,codec_name:format=duration",
         "-of","json",str(p)],text=True,timeout=30)
    j=json.loads(s)
    st=(j.get("streams") or [{}])[0]
    largura,altura=int(st.get("width") or 0),int(st.get("height") or 0)
    dur=float((j.get("format") or {}).get("duration") or 0)
    if min(largura,altura)<360 or not (4<=dur<=900):
        raise ValueError("vídeo sem dimensões/duração úteis")
    return {"largura":largura,"altura":altura,"duracao_s":round(dur,3),
            "codec":st.get("codec_name")}


def folha_contato(p:Path, destino:Path, dur:float) -> dict:
    """Amostras indicam ONDE inspecionar; nunca declaram processo demonstrado."""
    imagens=[]
    timestamps=[]
    for i in range(12):
        t=round(dur*(i+.5)/12,3)
        arq=destino.parent / f"_amostra_{i:02d}.jpg"
        subprocess.run(
            ["ffmpeg","-hide_banner","-loglevel","error","-y",
             "-ss",str(t),"-i",str(p),"-frames:v","1",
             "-vf","scale=270:-2",str(arq)],
            check=True,timeout=35
        )
        with Image.open(arq) as im:
            img=im.convert("RGB")
            img.thumbnail((270,172))
            imagens.append(img.copy())
        timestamps.append(t)
        arq.unlink(missing_ok=True)
    contato=Image.new("RGB",(270*4,205*3),(19,23,29))
    desenho=ImageDraw.Draw(contato)
    for i,im in enumerate(imagens):
        col,lin=i%4,i//4
        contato.paste(im,(col*270+(270-im.width)//2,lin*205))
        desenho.text((col*270+8,lin*205+178),f"amostra {i+1:02d} | {timestamps[i]:.2f}s",fill=(240,241,242))
    destino.parent.mkdir(parents=True,exist_ok=True)
    contato.save(destino,quality=86)
    return {"amostras":12,"tempos_s":timestamps,
            "estado":"QUADROS_EXTRAIDOS_SEM_INTERPRETACAO_DA_ACAO"}


def coletar(fonte:dict, pasta:Path, bib, baixar=None,
            inspecionar=None, quadros=None) -> dict:
    validar_fonte(fonte)
    pasta=Path(pasta)
    pasta.mkdir(parents=True,exist_ok=True)
    p=pasta/(fonte["id"]+".mp4")
    try:
        if not p.is_file():
            (baixar or baixar_fonte)(fonte,p)
        if not p.is_file() or p.stat().st_size<50_000 or p.stat().st_size>_MAX_BYTES:
            raise ValueError("arquivo de vídeo incompleto ou excessivo")
        dados=(inspecionar or provar_video)(p)
        hash_original=sha256_arquivo(p)
        esperado=fonte.get("sha256_esperado")
        if esperado is not None and hash_original!=esperado:
            raise ValueError("SHA-256 do vídeo diverge da receita; fonte alterada, não usar")
        contato=(pasta/(fonte["id"]+"_contato.jpg"))
        amostragem=(quadros or folha_contato)(p,contato,dados["duracao_s"])
        # Campos de direitos deliberadamente NÃO trazem uma licença automática;
        # Classificador V3 deve deixar uso_comercial='indefinido'.
        meta={
            "titulo":fonte["titulo"],
            "desc":"CANDIDATO sem inspeção factual nem autorização comercial individual",
            "mostra":"CANDIDATO — ação ainda não identificada nos quadros",
            "pagina":fonte["pagina"],
            "url":fonte["pagina"],
            "credito":fonte["credito"],
            "licenca_prova":(
                "DVIDS marca PUBLIC DOMAIN; verificar terceiros, marcas, pessoas e não-endosso"
                if fonte["provedor"]=="dvids" else
                "Política geral NIST não substitui conferência de direitos deste vídeo e de terceiros"
            ),
            "video":{"url":fonte["pagina"],"dur":dados["duracao_s"]},
            "lugar":fonte.get("local") or "Estados Unidos",
        }
        registro=bib.ingerir(p,meta,tema=fonte.get("tema") or "documentario")
        info=bib.obter(registro["id"])
        if info.get("uso_comercial")=="sim":
            raise RuntimeError("fonte candidata foi indevidamente promovida a uso comercial")
        return {
            "id":fonte["id"],"status":"CANDIDATO_BAIXADO_NAO_HOMOLOGADO",
            "id_v3":registro["id"],"sha256":hash_original,
            "tamanho_bytes":p.stat().st_size,"video":dados,
            "inspecao":amostragem,"uso_comercial":info.get("uso_comercial"),
            "licenca_individual":"PENDENTE","acao_fisica_comprovada":False,
            "confirmacao_humana":False,"publicado":False,
            "origem":fonte["pagina"],"credito":fonte["credito"],
        }
    except Exception as erro:
        # Distinguir falha de rede de avaliação editorial; nunca contar
        # candidata sem arquivo em quantidade de vídeo demonstrativo.
        p.unlink(missing_ok=True)
        return {"id":fonte["id"],"status":"SEM_VIDEO_VERIFICADO",
                "tipo_erro":type(erro).__name__,"motivo":str(erro)[:220],
                "publicado":False,"acao_fisica_comprovada":False}


def executar(receita:dict,pasta:Path,db:Path,armazem:Path,baixar=None,inspecionar=None,quadros=None)->dict:
    if receita.get("versao")!=1 or not isinstance(receita.get("itens"),list):
        raise ValueError("receita inválida")
    itens=receita["itens"]
    if not itens or len({x.get("id") for x in itens})!=len(itens):
        raise ValueError("IDs repetidos ou receita vazia")
    for it in itens:
        validar_fonte(it)
    from src.v3.biblioteca import Biblioteca
    bib=Biblioteca(db=db,armazem=armazem)
    try:
        resultados=[
            coletar(x,pasta,bib,baixar=baixar,inspecionar=inspecionar,quadros=quadros)
            for x in itens]
        bib.exportar_manifesto(pasta/"manifesto_v3.jsonl")
    finally:
        bib.fechar()
    resumo={
        "versao":1,"fontes":resultados,
        "baixados":sum(x["status"]=="CANDIDATO_BAIXADO_NAO_HOMOLOGADO" for x in resultados),
        "aprovados_editorialmente":0,"liberados_publicacao":0,
        "inspecao_humana":"PENDENTE","gastos_ia_usd":0,
    }
    (pasta/"relatorio.json").write_text(json.dumps(resumo,ensure_ascii=False,indent=2),encoding="utf8")
    return resumo


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("receita",type=Path)
    p.add_argument("saida",type=Path)
    a=p.parse_args(argv)
    p=a.saida
    p.mkdir(parents=True,exist_ok=True)
    r=executar(json.loads(a.receita.read_text(encoding="utf8")),p,
               p/"biblioteca.sqlite3",p/"armazem_v3")
    print(json.dumps(r,ensure_ascii=False)[:8500])
    # Coleta parcial é resultado normal, não aprovação de mídia.
    return 0


if __name__=="__main__":
    raise SystemExit(main())
