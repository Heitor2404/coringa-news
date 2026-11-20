"""Prospecção de cenas de AÇÕES REAIS do Wikimedia Commons.

Diferencia: URL/licença declaradas → bytes com SHA1 de arquivo histórico
→ contato de quadros → ANOTAÇÃO humana de ação → direitos.
Jamais rotula progresso de pixels ou título da origem como ação provada.

Foi pensado para qualquer processo, não apenas usinagem ou encadernação.
Os originais são baixados unicamente em QA, sem publicação.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw

_HOST="upload.wikimedia.org"
_MAX=25_000_000
_SHA1=re.compile(r"[0-9a-f]{40}")


def validar_fonte(info:dict)->None:
    if not isinstance(info,dict) or info.get("publicar") is True:
        raise ValueError("A-FONTE-FORMATO: fonte não pode autorizar publicação")
    for k in ("id","dominio","sujeito","processo_declarado","pagina","original_licenca","autor"):
        if not isinstance(info.get(k),str) or len(info[k].strip())<3:
            raise ValueError("A-FONTE-CONTRATO: falta "+k)
    if not re.fullmatch(r"[a-z][a-z0-9_-]{5,65}",info["id"]):
        raise ValueError("A-FONTE-ID: formato não permitido")
    url=urlsplit(str(info.get("uri") or ""))
    page=urlsplit(info["pagina"])
    if (url.scheme!="https" or url.hostname!=_HOST
        or url.username or url.password or url.port is not None
        or not url.path.startswith("/wikipedia/commons/")
        or not url.path.endswith((".webm",".ogv"))
        or url.query or url.fragment):
        raise ValueError("A-FONTE-URL: só original Wikimedia HTTPS")
    if (page.scheme!="https" or page.hostname!="commons.wikimedia.org"
        or not page.path.startswith("/wiki/File:") or page.username
        or page.password or page.port is not None):
        raise ValueError("A-FONTE-PAGINA: Commons específica")
    if info.get("original_licenca") not in ("CC BY 3.0","CC BY 4.0","CC BY-SA 4.0","CC0","Public domain"):
        raise ValueError("A-FONTE-LICENCA: licença incompatível/desconhecida")
    if info.get("status_licenca") not in ("REVISAO_HUMANA_DERIVADOS_PENDENTE",
                                         "CONFIRMAR_SHARE_ALIKE_E_DERIVADOS"):
        raise ValueError("A-FONTE-DIREITOS: não promover licença")
    sha1=info.get("expected_sha1")
    size=info.get("expected_bytes")
    if not isinstance(sha1,str) or not _SHA1.fullmatch(sha1):
        raise ValueError("A-FONTE-SHA1: identificação histórica obrigatória")
    if not isinstance(size,int) or isinstance(size,bool) or not 50_000<=size<=_MAX:
        raise ValueError("A-FONTE-TAMANHO: limite inválido")
    window=info.get("janela_candidata")
    if (not isinstance(window,dict) or
        any(not isinstance(window.get(k),(int,float)) or isinstance(window[k],bool)
            or not math.isfinite(window[k]) for k in ("inicio_s","duracao_s"))
        or window["inicio_s"]<0 or not 2.5<=window["duracao_s"]<=8):
        raise ValueError("A-FONTE-JANELA: duração/corte inválidos")


def verificar_bytes(data:bytes, info:dict)->dict:
    validar_fonte(info)
    if len(data)!=info["expected_bytes"]:
        raise ValueError("A-BYTES-TAMANHO: arquivo parcial ou versão alterada")
    sha1=hashlib.sha1(data).hexdigest()
    if sha1!=info["expected_sha1"]:
        raise ValueError("A-BYTES-SHA: original não corresponde ao Commons catalogado")
    return {"sha1":sha1,"sha256":hashlib.sha256(data).hexdigest(),
            "bytes":len(data),"integridade":"ORIGINAL_SHA1_CONFERIDO"}


def baixar_original(info:dict,destino:Path,reader=None)->dict:
    validar_fonte(info)
    if reader is None:
        import requests
        def reader(url):
            with requests.get(url,timeout=(12,45),stream=True,allow_redirects=False,
                              headers={"User-Agent":"CoringaExplica/QA-Privada/1.0"}) as response:
                if response.status_code!=200:
                    redirect=response.headers.get("Location","")
                    dest=urlsplit(redirect).hostname if redirect else None
                    raise ValueError(
                        f"A-HTTP-ORIGINAL: status {response.status_code}; "
                        f"redirect_host={dest or 'nenhum'}; sem tentar contornar acesso")
                content_type=response.headers.get("Content-Type","").lower()
                if not any(c in content_type for c in ("video/","application/octet-stream")):
                    raise ValueError("A-HTTP-TIPO: resposta não é vídeo")
                if int(response.headers.get("Content-Length") or 0)>_MAX:
                    raise ValueError("A-HTTP-LIMITE: arquivo excessivo")
                collected=bytearray()
                for chunk in response.iter_content(256*1024):
                    collected.extend(chunk)
                    if len(collected)>_MAX:
                        raise ValueError("A-HTTP-LIMITE: arquivo excessivo")
                return bytes(collected)
    data=reader(info["uri"])
    if not isinstance(data,bytes):
        raise ValueError("A-HTTP-BYTES: coletor inválido")
    check=verificar_bytes(data,info)
    destino=Path(destino)
    destino.parent.mkdir(parents=True,exist_ok=True)
    # O arquivo é gravado SOMENTE após a verificação completa.
    destino.write_bytes(data)
    return check


def ffprobe(arquivo:Path)->dict:
    obj=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_entries",
        "stream=codec_type,width,height:format=duration",
        "-of","json",str(arquivo)],text=True,timeout=40))
    tracks=[x for x in obj.get("streams") or [] if x.get("codec_type")=="video"]
    if len(tracks)!=1:
        raise ValueError("A-PROBE-FAIXAS: vídeo original ausente/ambíguo")
    w,h=int(tracks[0]["width"]),int(tracks[0]["height"])
    dur=float(obj["format"]["duration"])
    if min(w,h)<400 or not math.isfinite(dur) or dur<3 or dur>600:
        raise ValueError("A-PROBE-INVALIDO: mídia inviável")
    return {"largura":w,"altura":h,"duracao_s":dur}


def frame(arquivo:Path,stamp:float)->Image.Image:
    b=subprocess.check_output([
        "ffmpeg","-hide_banner","-loglevel","error",
        "-ss",f"{stamp:.3f}","-i",str(arquivo),
        "-frames:v","1","-vf","scale=420:-2",
        "-f","image2pipe","-vcodec","png","pipe:1"],timeout=40)
    with Image.open(io.BytesIO(b)) as im:
        return im.convert("RGB")


def contato(arquivo:Path, info:dict,saida:Path, metadata:dict, count:int=12)->dict:
    w=info["janela_candidata"]
    ini,dur=w["inicio_s"],w["duracao_s"]
    if ini+dur>metadata["duracao_s"]-.06:
        raise ValueError("A-JANELA-FIM: original termina antes da janela")
    folha=Image.new("RGB",(4*432,3*273),(8,18,26))
    dr=ImageDraw.Draw(folha)
    stamps=[]
    for i in range(count):
        at=round(ini+(i+.5)*dur/count,3)
        im=frame(arquivo,at)
        im.thumbnail((420,238))
        row,col=divmod(i,4)
        x=col*432+(432-im.width)//2
        y=row*273
        folha.paste(im,(x,y))
        dr.text((col*432+8,y+243),f"ORIGINAL {at:.2f}s (quadro {i+1}/{count})",
                fill=(235,241,246))
        stamps.append(at)
    saida.parent.mkdir(parents=True,exist_ok=True)
    folha.save(saida,quality=91)
    return {"quadros_amostrados_s":stamps,
            "contato":saida.name,
            "processo_visivel_confirmado":False,
            "observacao_da_acao":"EXIGE_INSPECAO_HUMANA",
            "direitos_terceiros":"PENDENTE",
            "autorizacao_publicar":False}


def executar(receita:dict,stage:Path,saida:Path)->dict:
    if (not isinstance(receita,dict)
        or receita.get("versao")!=1
        or receita.get("modo")!="PROSPECCAO_ORIGINAIS_SEM_APROVACAO"
        or receita.get("publicar") is not False):
        raise ValueError("A-CONTRATO: somente prospecção privada")
    items=receita.get("video_fontes")
    if not isinstance(items,list) or not items:
        raise ValueError("A-CONTRATO: lista de fontes inválida")
    keys=set()
    for item in items:
        validar_fonte(item)
        if item["id"] in keys:
            raise ValueError("A-DUPLICACAO: fonte repetida")
        keys.add(item["id"])
    stage,saida=Path(stage),Path(saida)
    saida.mkdir(parents=True,exist_ok=True)
    report=[]
    for it in items:
        master=stage/(it["id"]+".webm")
        try:
            check=baixar_original(it,master)
            technical=ffprobe(master)
            inspect=contato(master,it,saida/(it["id"]+"_contato.jpg"),technical)
            report.append({
                "id":it["id"],"dominio":it["dominio"],"sujeito":it["sujeito"],
                "processo_declarado":it["processo_declarado"],
                "pagina":it["pagina"],"autor":it["autor"],
                "licenca_declarada":it["original_licenca"],
                "status_licenca":"REVISAR_TERCEIROS_E_EVENTUAL_DERIVACAO",
                "estado":"ORIGINAL_CONFERIDO_SEM_ACAO_CURADA",
                "original":check,"sonda":technical,"inspecao":inspect,
                "revisao_humana":"PENDENTE","publicar":False
            })
        except Exception as ex:
            master.unlink(missing_ok=True)
            report.append({"id":it["id"],"estado":"BLOQUEADO",
                           "codigo":str(ex)[:200],"publicar":False})
    result={"estado":"PROSPECCAO_PRIVADA",
            "total":len(report),
            "originais_conferidos":sum(x["estado"]=="ORIGINAL_CONFERIDO_SEM_ACAO_CURADA" for x in report),
            "acoes_comprovadas":0,"publicar":False,
            "fontes":report}
    (saida/"relatorio_prospeccao.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return result


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("receita",type=Path)
    ap.add_argument("stage",type=Path)
    ap.add_argument("saida",type=Path)
    args=ap.parse_args(argv)
    plan=json.loads(args.receita.read_text(encoding="utf8"))
    res=executar(plan,args.stage,args.saida)
    print(json.dumps({"originais":res["originais_conferidos"],
                      "total":res["total"],"acoes":res["acoes_comprovadas"]}))
    return 0 if res["originais_conferidos"]==res["total"] else 2


if __name__=="__main__":
    raise SystemExit(main())
