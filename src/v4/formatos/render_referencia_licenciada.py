"""Fallback REFERENCE-FIRST 2D licenciado: GIF real -> preview vertical privado.

NAO e reconstrucao de geometria, rig ou 3D. Usa a animacao de origem
quando a licenca permite adaptacao, exige credito e mantem saida PRIVADA.
Renderer generico: eventos/titulos/creditos sao DADOS, nao codigo por tema.
Nao autorizado para publicacao automatica.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 540, 960
RESTRICTED = re.compile(r"non.?commercial|\bNC\b|no.?derivatives|\bND\b", re.I)


def validar(arquivo: Path, plano: dict) -> tuple[int,float]:
    if not isinstance(plano,dict) or plano.get("schema")!="licensed-reference-private-v1":
        raise ValueError("F-PLANO-NAO-ESPECIFICADO")
    if plano.get("publicar") is not False:
        raise ValueError("F-REFERENCIA-SEM-PUBLICACAO-AUTORIZADA")
    if not arquivo.is_file() or arquivo.suffix.lower()!=".gif":
        raise ValueError("F-GIF-AUSENTE")
    if arquivo.stat().st_size>30_000_000:
        raise ValueError("F-GIF-GRANDE")
    raw=arquivo.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=plano.get("origem_sha256"):
        raise ValueError("F-SHA-DIVERGENTE")
    license_name=str(plano.get("licenca") or "")
    if (plano.get("licenca_verificada_manual") is not True
         or not license_name or license_name.lower()=="unknown"
         or RESTRICTED.search(license_name)):
        raise ValueError("F-LICENCA-NAO-PERMITE-USO-AQUI")
    if not all(isinstance(plano.get(field),str) and len(plano[field].strip())>3
               for field in ("pagina","autores","licenca_url","titulo")):
        raise ValueError("F-ATRIBUICAO-OBRIGATORIA")
    labels=plano.get("etapas")
    if not isinstance(labels,list) or not 3<=len(labels)<=8:
        raise ValueError("F-ETAPAS-NAO-REVISADAS")
    frames=[]
    with Image.open(arquivo) as gif:
        if gif.format!="GIF" or gif.n_frames<12:
            raise ValueError("F-REFERENCIA-SEM-ANIMACAO-SUFICIENTE")
        n=gif.n_frames
        duration=sum(max(20.,float(gif.info.get("duration",100)))
                     for i in range(n) if gif.seek(i) is None)/1000.
    for stage in labels:
        if (not isinstance(stage,dict) or not isinstance(stage.get("frame"),int)
            or isinstance(stage.get("frame"),bool)
            or not 0<=stage["frame"]<n
            or not isinstance(stage.get("titulo"),str)
            or not isinstance(stage.get("detalhe"),str)
            or not 4<=len(stage["titulo"])<=46
            or not 5<=len(stage["detalhe"])<=110):
            raise ValueError("F-ETAPA-INCONSISTENTE")
        frames.append(stage["frame"])
    if frames!=sorted(set(frames)) or frames[0]!=0:
        raise ValueError("F-ETAPAS-DESORDENADAS")
    return n,duration


def _font(size:int,bold=False):
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",size)
    except OSError:
        return ImageFont.load_default()


def renderizar(arquivo:Path,plano:dict,saida:Path, *,
              fps:int=24,velocidade:float=.625) -> dict:
    """GIF em plano editorial, nao geometria reconstruida."""
    arquivo,saida=Path(arquivo),Path(saida)
    n,duration=validar(arquivo,plano)
    if fps not in (24,30) or not .25<=velocidade<=1:
        raise ValueError("F-TEMPO-INVALIDO")
    total=duration/velocidade
    if total>60:
        raise ValueError("F-VIDEO-ACIMA-DE-60-SEGUNDOS")
    with Image.open(arquivo) as gif:
        copies=[]
        starts=[0.]
        for i in range(n):
            gif.seek(i)
            frame=gif.convert("RGB")
            if min(frame.size)<80 or frame.width*frame.height>8_000_000:
                raise ValueError("F-GIF-RESOLUCAO")
            frame.thumbnail((420,585),Image.Resampling.LANCZOS)
            copies.append(frame.copy())
            if i<n-1:
                starts.append(starts[-1] + max(.020,float(gif.info.get("duration",100))/1000))
    stages=plano["etapas"]
    saida.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo",
         "-pixel_format","rgb24","-video_size",f"{WIDTH}x{HEIGHT}",
         "-framerate",str(fps),"-i","-","-c:v","libx264","-preset","veryfast",
         "-crf","21","-pix_fmt","yuv420p","-movflags","+faststart",str(saida)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        last=0
        for fi in range(round(total*fps)):
            origin_t=fi/fps*velocidade
            while last+1<n and starts[last+1]<=origin_t:
                last+=1
            stage=next(j for j,item in reversed(list(enumerate(stages)))
                       if last>=item["frame"])
            canvas=Image.new("RGB",(WIDTH,HEIGHT),"#E9F4F8")
            draw=ImageDraw.Draw(canvas)
            draw.rectangle((0,0,WIDTH,134),fill="#0B2C4A")
            draw.rounded_rectangle((42,144,235,172),radius=7,fill="#FFE064")
            draw.text((53,150),"CORINGA EXPLICA",font=_font(15,True),fill="#122A3F")
            draw.text((42,188),plano["titulo"][:27].upper(),font=_font(23,True),
                      fill="#082D4B")
            draw.text((42,219),plano.get("subtitulo","ANIMACAO TECNICA")[:28].upper(),
                      font=_font(23,True),fill="#082D4B")
            draw.line((42,259,498,259),fill="#75A8BC",width=2)
            draw.text((42,273),f"{stage+1:02d}  {stages[stage]['titulo'].upper()}",
                      font=_font(21,True),fill="#0E5878")
            image=copies[last]
            x=(WIDTH-image.width)//2
            canvas.paste(image,(x,313))
            draw.rounded_rectangle((47,899,494,944),radius=9,fill="#0B2D49")
            draw.text((60,907),"REFERÊNCIA LICENCIADA · PRÉVIA PRIVADA",
                      font=_font(10,True),fill="#F4FFFF")
            if proc.stdin is None:
                raise ValueError("F-FFMPEG-SEM-PIPE")
            proc.stdin.write(canvas.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not saida.is_file() or saida.stat().st_size<10000:
        raise ValueError("F-RENDER-FALHOU")
    # Sidecar completo de cumprimento de licenca; nao apagar.
    attribution={
        "fonte":plano["pagina"],"autores":plano["autores"],
        "licenca":plano["licenca"],"licenca_url":plano["licenca_url"],
        "mudancas":"escala, ajuste de velocidade, cartelas de texto, corte editorial",
        "classe":"ADAPTACAO_DA_MIDIA_ORIGINAL_NAO_RECONSTRUCAO",
        "licenca_da_adaptacao":plano["licenca"],
        "publicar":False,
        "arquivo_sha256":hashlib.sha256(saida.read_bytes()).hexdigest(),
    }
    sidecar=saida.with_name(saida.stem+"_creditos.json")
    sidecar.write_text(json.dumps(attribution,ensure_ascii=False,indent=2),
                       encoding="utf8")
    return {"estado":"VIDEO_REFERENCIA_PRIVADO_RENDERIZADO",
            "publicar":False,"video":str(saida),
            "duracao_s":round(total,3),"credito":str(sidecar),
            "renderer":"GIF_LICENCIADO_NAO_2D_RECONSTRUIDO"}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("gif");p.add_argument("plano_json");p.add_argument("saida")
    args=p.parse_args(argv)
    plan=json.loads(Path(args.plano_json).read_text("utf8"))
    result=renderizar(Path(args.gif),plan,Path(args.saida))
    print(json.dumps(result,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
