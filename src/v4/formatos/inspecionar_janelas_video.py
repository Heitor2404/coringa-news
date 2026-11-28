"""Inspeção técnica de janela de vídeo AUTÊNTICO antes de decisão editorial.

Só gera evidência para curador: frames da fonte/tempos originais e crop
9:16 em 3 candidatos de ROI. Não inferir ação, identidade, direitos ou
qualidade editorial a partir de pixels diferentes. Sem publicação.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps


def verificar_original(arquivo: Path, manifest: dict) -> dict:
    if not arquivo.is_file():
        raise ValueError("V-SEM-ARQUIVO: obter original sem reencodar")
    digest=hashlib.sha256(arquivo.read_bytes()).hexdigest()
    if digest!=manifest.get("sha256_esperado"):
        raise ValueError("V-SHA-DIVERGENTE: arquivo não coincide com fonte catalogada")
    probe=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_entries",
        "stream=codec_type,width,height:format=duration",
        "-of","json",str(arquivo)],text=True,timeout=40))
    frames=[s for s in probe.get("streams") or [] if s.get("codec_type")=="video"]
    if len(frames)!=1:
        raise ValueError("V-VIDEO-STREAMS: original sem única faixa de vídeo")
    w,h=int(frames[0]["width"]),int(frames[0]["height"])
    duration=float((probe.get("format") or {}).get("duration") or 0)
    if not math.isfinite(duration) or min(w,h)<360 or duration<4:
        raise ValueError("V-ORIGINAL-INVALIDO: duração/dimensões")
    return {"sha256":digest,"width":w,"height":h,"duration_s":duration}


def _frame(path:Path,at:float)->Image.Image:
    data=subprocess.check_output([
        "ffmpeg","-hide_banner","-loglevel","error","-ss",f"{at:.3f}",
        "-i",str(path),"-frames:v","1","-f","image2pipe",
        "-vcodec","png","pipe:1"],timeout=55)
    with Image.open(io.BytesIO(data)) as x:
        return x.convert("RGB")


def inspecionar(manifest:dict,arquivo:Path,saida:Path)->dict:
    if manifest.get("versao")!=1 or manifest.get("modo")!="INSPECAO_PRIVADA_NAO_APROVADA":
        raise ValueError("V-CONTRATO: modo privado")
    if manifest.get("publicar") is not False:
        raise ValueError("V-PUBLICAR: inspeção não libera publicação")
    meta=verificar_original(arquivo,manifest)
    janelas=manifest.get("janelas")
    if not isinstance(janelas,list) or not 1<=len(janelas)<=4:
        raise ValueError("V-JANELAS: informar janelas reais")
    ids=set()
    folhas=[]
    rel=[]
    saida.mkdir(parents=True,exist_ok=True)
    for win in janelas:
        id=win.get("id")
        start=win.get("inicio_s")
        dur=win.get("duracao_s")
        if not isinstance(id,str) or not id.replace("_","").replace("-","").isalnum() or id in ids:
            raise ValueError("V-ID: janela sem id único")
        ids.add(id)
        if any(not isinstance(x,(int,float)) or isinstance(x,bool)
               or not math.isfinite(x) for x in [start,dur]) or start<0 or dur<2.4 or start+dur>meta["duration_s"]-.1:
            raise ValueError("V-JANELA: recorte ultrapassa original")
        frames=[]
        centers=[(k+.5)/8 for k in range(8)]
        original=[]
        vertical=[]
        for k,f in enumerate(centers):
            stamp=start+dur*f
            fr=_frame(arquivo,stamp)
            fr.thumbnail((420,242))
            original.append(fr)
            # Simular o crop de capa sem criar prova de ROI humano.
            w,h=fr.size
            cover=min(w,h*9/16)
            left=(w-cover)/2
            crop=fr.crop((int(left),0,int(left+cover),h))
            crop.thumbnail((140,242))
            vertical.append(crop)
            frames.append(round(stamp,3))
        sheet=Image.new("RGB",(4*560,2*277),(12,20,30))
        painter=ImageDraw.Draw(sheet)
        for i,im in enumerate(original):
            x=(i%4)*560;y=(i//4)*277
            sheet.paste(im,(x,y))
            sheet.paste(vertical[i],(x+430,y))
            painter.text((x+8,y+247),f"FONTE {frames[i]:.2f}s | crop CENTRAL NAO APROVADO",fill=(235,239,244))
        outfile=saida/(id+"_8frames.jpg")
        sheet.save(outfile,quality=89)
        rel.append({
            "id":id,"fonte_inicio_s":start,"fonte_duracao_s":dur,
            "tempos_amostrados_s":frames,"contato":outfile.name,
            "roi_vertical":"NAO_INSPECIONADA_POR_HUMANO",
            "acao_fisica_comprovada":False,"identidade_factual_confirmada":False,
            "licenca_confirmada":False,"aprovacao_de_video":"PENDENTE",
        })
    result={"modo":"QA_JANELAS_REAIS_SEM_APROVACAO",
            "fonte":manifest.get("fonte_id"),
            "original":meta,
            "janelas":rel,
            "publicar":False,"telegram":False,
            "proxima_etapa":"inspecao humana dos quadros, anotacao de ROI e uso contextual permitido"}
    (saida/"inspecao.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    return result
