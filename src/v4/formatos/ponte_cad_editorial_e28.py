"""Private CAD-to-FilmeEditorial bridge. Not a production preflight bypass.

Only accepts a local stage with QA from E27; the same recorded frame clock
is used for cues. No unverified literal identity or publication rights.
The public production plan validator does not accept cad_preview.
"""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path


def fail(code):
    raise ValueError("E28-"+code)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def props(qa, asset):
    stage=qa.get("palco_cad",{})
    ev=qa.get("eventos_trajetoria",{})
    if (qa.get("publish") is not False or qa.get("visual_approved") is not False
            or stage.get("publish") is not False or stage.get("direitos_publicacao")!="NAO_AVALIADOS"
            or stage.get("homologacao_visual")!="NAO_HOMOLOGADO"
            or stage.get("schema")!="coringa.palco.cad.v1"
            or stage.get("tipo_evidencia")!="representacao_tecnica"
            or ev.get("schema")!="coringa.eventos.trajetoria.v1"
            or ev.get("interpretacao_causal")!="NAO_INFERIDA"):
        fail("PRIVADO_E_PROVENIENCIA")
    n=stage.get("quadros")
    if (type(n) is not int or n<2 or n>900 or ev.get("quadros")!=n
            or ev.get("fps")!=30 or stage.get("fps")!=30
            or stage.get("dimensoes")!=[1080,1920]
            or abs(ev.get("duracao_s",-1)-n/30)>1e-8
            or stage.get("verificacao_video",{}).get("quadros")!=n
            or stage.get("verificacao_video",{}).get("pico_pixels_mudados",0)<300):
        fail("RELOGIO")
    if not re.fullmatch(r"[0-9a-f]{64}",str(stage.get("sha256",""))):
        fail("HASH")
    for k in ("credito","licenca_informada","natureza"):
        if not isinstance(stage.get(k),str) or not stage[k].strip():
            fail("FONTE")
    if not isinstance(stage.get("fonte"),dict) or not stage["fonte"]:
        fail("FONTE")
    if not re.fullmatch(r"cad_e28/[0-9a-f]{64}\.mp4",asset):
        fail("ASSET")
    if asset.split("/")[-1]!=stage["sha256"]+".mp4":
        fail("HASH_ASSET")
    roi=stage.get("roi_px",[86,288,994,1230])
    if roi!=[86,288,994,1230]:
        fail("ROI")
    fases=ev.get("fases")
    if not isinstance(fases,list) or not fases:
        fail("EVENTOS")
    labels={"aumenta":"A medida aumenta","diminui":"A medida diminui",
            "variacao_pequena":"Pequena variação da medida"}
    unit=ev.get("medida",{}).get("unidade","mm")
    if unit not in ("mm","rad"):
        fail("UNIDADE_MEDIDA")
    cues=[]
    anterior=0
    for f in fases:
        a,b=f.get("frame_inicio"),f.get("frame_fim")
        if (type(a) is not int or type(b) is not int or a!=anterior
                or not 0<=a<b<n or f.get("tipo") not in labels
                or abs(f.get("tempo_inicio_s",-1)-a/30)>1e-8
                or abs(f.get("tempo_fim_s",-1)-b/30)>1e-8):
            fail("EVENTO_FORA_DO_VIDEO")
        delta=f.get("delta_"+unit)
        if not isinstance(delta,(int,float)) or not math.isfinite(delta):
            fail("EVENTO_MEDIDA")
        label=labels[f["tipo"]]
        cues.append(dict(at=a/30,label=label,kind="fact"))
        anterior=b
    if anterior!=n-1:
        fail("EVENTOS_INCOMPLETOS")
    medida=ev.get("medida",{}).get("rotulo")
    if not isinstance(medida,str) or not medida.strip():
        fail("MEDIDA")
    # Optional observed dwell. Check coverage and frame clock before using.
    dwell=ev.get("repouso")
    if dwell is not None:
        if (not isinstance(dwell,dict) or dwell.get("schema")!="coringa.repouso.amostrado.v1"
            or dwell.get("unidade")!=unit or dwell.get("fps")!=30 or dwell.get("quadros")!=n
            or dwell.get("interpretacao_causal")!="NAO_INFERIDA"
            or dwell.get("publish") is not False):
            fail("REPOUSO_CONTRATO")
        phases=dwell.get("fases")
        if not isinstance(phases,list) or not phases:
            fail("REPOUSO_FASES")
        new=[]; last=0
        for f in phases:
            a,b=f.get("frame_inicio"),f.get("frame_fim")
            kind=f.get("tipo")
            if (type(a) is not int or type(b) is not int or a!=last or not 0<=a<b<n
                or kind not in ("repouso_amostrado","variacao_observada")
                or abs(f.get("tempo_inicio_s",-1)-a/30)>1e-8
                or abs(f.get("tempo_fim_s",-1)-b/30)>1e-8):
                fail("REPOUSO_RELOGIO")
            label=("Repouso da medida" if kind=="repouso_amostrado" else "Variação da medida")
            new.append(dict(at=a/30,label=label,kind="fact"))
            last=b
        if last!=n-1:
            fail("REPOUSO_INCOMPLETO")
        if any(f["tipo"]=="repouso_amostrado" for f in phases):
            cues=new
    if "transmissao_observada" in qa:
        from . import editorial_e42 as E42
        cues=E42.cues(qa["transmissao_observada"],n)
    # No claimed causal explanation, no invented voice or duration.
    shot=dict(id="cad_privado_e28",start=0,end=n/30,type="cad_preview",
              asset=asset,cad_source_roi=roi,source=stage["credito"],
              source_display=stage["credito"],evidence="explainer",
              lead="Representação CAD",headline=medida[:85],subject="Estudo cinemático",
              cues=cues)
    if "transmissao_observada" in qa:
        shot["cad_transmissao"]=E42.painel(qa["transmissao_observada"],n)
    if qa.get("estado")=="REPROVADO_INTERFERENCIA_BREP":
        shot["cad_warning"]="INTERFERÊNCIA DETECTADA · MODELO NÃO VALIDADO"
    elif "interferencia_brep" in qa and qa.get("verificacao_contato")!="SEM_INTERFERENCIA_BREP_NA_AMOSTRA":
        shot["cad_warning"]="AUDITORIA DE CONTATO PENDENTE"
    return dict(duracao=n/30,shots=[shot],preview=True,private_review_only=True,
                direitos_pendentes=[stage["licenca_informada"]],
                safe_area_profile="MULTIPLATAFORMA_CONSERVADOR_V1")


def ffmpeg():
    import os
    if os.getenv("FFMPEG"):
        return os.environ["FFMPEG"]
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def verificar_video(path,n,w=1080,h=1920):
    info=subprocess.run([ffmpeg(),"-hide_banner","-i",str(path)],capture_output=True,text=True).stderr
    streams=re.findall(r"Stream #\d+:\d+.*?: (Video|Audio|Data|Subtitle): (.*)",info)
    if (len(streams)!=1 or streams[0][0]!="Video"
            or not re.search(rf"\b{w}x{h}\b",streams[0][1])
            or not re.search(r"\b30(?:\.0+)? fps\b",streams[0][1])):
        fail("VIDEO_FORMATO")
    import numpy as np
    data=subprocess.check_output([ffmpeg(),"-v","error","-i",str(path),"-vf",
                                  "scale=135:240","-f","rawvideo","-pix_fmt","rgb24","-"])
    frames=np.frombuffer(data,np.uint8).reshape(-1,240,135,3).astype(np.int16)
    if len(frames)!=n:
        fail("VIDEO_QUADROS")
    # Actual movement, not changing text alone, in the upper-middle stage.
    roi=frames[:,55:125,20:95]
    change=(np.abs(roi-roi[0]).max(axis=-1)>18).sum(axis=(1,2))
    if int(change.max())<20:
        fail("VIDEO_SEM_MOVIMENTO")
    return dict(quadros=n,pico_pixels_mudados=int(change.max()),dimensoes=[w,h],fps=30)


def preparar(qa_path,public_root,output):
    qa_path=Path(qa_path).resolve()
    qa=json.loads(qa_path.read_text())
    stage=qa.get("palco_cad",{})
    name=stage.get("arquivo","")
    if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z0-9_-]+_palco\.mp4",name):
        fail("ARQUIVO")
    src=qa_path.parent/name
    if src.is_symlink() or not src.is_file():
        fail("ARQUIVO")
    actual=sha(src)
    asset=f"cad_e28/{actual}.mp4"
    p=props(qa,asset)
    check=verificar_video(src,stage["quadros"])
    dst=Path(public_root)/asset
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    if sha(dst)!=actual:
        fail("COPIA")
    out=Path(output)
    out.mkdir(parents=True,exist_ok=True)
    (out/"props.json").write_text(json.dumps(p,ensure_ascii=False,indent=2))
    (out/"proveniencia.json").write_text(json.dumps(dict(palco=stage,eventos=qa["eventos_trajetoria"],
         verificacao_independente=check,private_review_only=True,publish=False),ensure_ascii=False,indent=2))
    return p


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("qa")
    p.add_argument("public")
    p.add_argument("output")
    a=p.parse_args()
    preparar(a.qa,a.public,a.output)
