"""F14 — compositor ÚNICO para pares de engrenagens com parâmetros JSON.

Cena de REDUÇÃO EXTERNA 2D em caixa aberta didática, não CAD validado.
Primitiva distinta da biela e eclusa. Sem busca de pixels, sem narração,
publicação desabilitada. Duas configurações com dentes/diâmetros diferentes.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image

from src.v4.formatos import engrenagens_parametricas_f14 as G

SCHEMA="coringa-spur-gear-pair-f14-v1"
FAMILY="external_spur_gear_reduction"
SIZE=[540,960]
SOURCE=G.SOURCE
ACTIONS=("engagement","reduction")

def err(tag): raise ValueError("F14-COMPOSITOR-"+tag)

def _string(s,lo=4,hi=85):
    if not isinstance(s,str) or not lo<=len(s)<=hi or any(c in s for c in "<>&\n"):
        err("TEXTO")
    return s

def load(path):
    path=Path(path)
    if not path.is_file() or path.suffix.lower()!=".json" or path.stat().st_size>30_000:
        err("CENA_AUSENTE")
    try: data=json.loads(path.read_text("utf8"))
    except (OSError,UnicodeError,ValueError) as e:
        raise ValueError("F14-COMPOSITOR-JSON") from e
    validate(data)
    return data

def validate(s):
    if (not isinstance(s,dict) or s.get("schema")!=SCHEMA or
        s.get("family")!=FAMILY or s.get("version")!=1 or
        s.get("video")!=SIZE or s.get("fps")!=24 or
        s.get("camera")!="locked" or s.get("publish") is not False or
        s.get("industrial_approval") is not False or
        s.get("visual_approval") is not False):
        err("CONTRATO")
    for key in ("id","title","subtitle"):
        _string(s.get(key),4,72)
    source=s.get("source")
    if (not isinstance(source,dict) or source.get("url")!=SOURCE or
        source.get("scope")!="PRINCIPIO_FISICO_NAO_ASSET_VISUAL" or
        source.get("external_pixels_copied") is not False or
        source.get("source_is_license") is not False):
        err("PROVENIENCIA")
    if s.get("physics")!={"model":"external_spur_gears_ideal",
                         "module_units":"pixels_didaticos",
                         "no_slip_pitch_circles":True,
                         "tooth_profile":"20deg_involute_with_simplified_root",
                         "stress_tolerance_verified":False}:
        err("FISICA")
    t=G.num(s.get("duration_s"),8,11)
    if type(s.get("driver_revolutions")) is not int or not 1<=s["driver_revolutions"]<=2:
        err("GIRO_ENTRADA")
    shape=s.get("gears")
    if not isinstance(shape,dict) or set(shape)!={"z1","z2","module","input_x","center_y"}:
        err("ENGRENAGEM")
    p=G.pair(shape["z1"],shape["z2"],shape["module"],shape["input_x"],shape["center_y"])
    if p.ratio<=1 or p.ratio>3:
        err("REDEMOINHO_SEM_REDUCAO")
    if (p.cx1-p.driving.tip<81 or p.cx2+p.driven.tip>451 or
        p.cy-max(p.driving.tip,p.driven.tip)<370 or
        p.cy+max(p.driving.tip,p.driven.tip)>645):
        err("PALCO_MECANICO")
    phases=s.get("phases")
    if not isinstance(phases,list) or len(phases)!=2 or [x.get("action") for x in phases if isinstance(x,dict)]!=list(ACTIONS):
        err("FASES")
    for i,phase in enumerate(phases):
        if (not isinstance(phase,dict)
            or abs(G.num(phase.get("start"),0,t)-i*t/2)>1e-7
            or abs(G.num(phase.get("end"),0,t)-(i+1)*t/2)>1e-7):
            err("TEMPO")
        _string(phase.get("title"),4,33)
        _string(phase.get("detail"),10,65)
    if not isinstance(s.get("palette"),dict) or s["palette"].get("input") not in ("silver","blue") or s["palette"].get("output") not in ("silver","blue") or s["palette"]["input"]==s["palette"]["output"]:
        err("PALETA")
    return p

def state(scene,t):
    p=validate(scene)
    # Uma volta do eixo de entrada em todo o clip didático.
    return G.state(p,t,scene["duration_s"],turns=scene["driver_revolutions"])

def frame(scene,t):
    p=validate(scene)
    data=state(scene,t)
    duration=scene["duration_s"]
    i=0 if t<duration/2 else 1
    stage=scene["phases"][i]
    g1=G.gear_svg(p.driving,p.cx1,p.cy,data["driver_angle_deg"],
                  role="input_gear",color=scene["palette"]["input"])
    g2=G.gear_svg(p.driven,p.cx2,p.cy,data["driven_angle_deg"],
                  role="output_gear",color=scene["palette"]["output"])
    cx=(p.cx1+p.cx2)/2.
    move=round(t/duration*474,3)
    ratio=f"{data['speed_ratio']:.2f}".replace(".",",")
    title=escape(scene["title"])
    detail=escape(stage["detail"])
    step=escape(stage["title"])
    subtitle=escape(scene["subtitle"])
    # Os cubos do eixo ficam atrás das rodas; a placa é uma janela técnica,
    # não um print ou objeto CAD copiado de terceiro.
    x1=p.cx1;x2=p.cx2;y=p.cy
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="540" height="960" viewBox="0 0 540 960" data-family="{FAMILY}">
      <defs>
        <linearGradient id="f14_bg" x1="0" y1="0" x2="0.18" y2="1">
          <stop stop-color="#F1F8FA"/><stop offset="1" stop-color="#DCEAF0"/>
        </linearGradient>
        <radialGradient id="f14_silver" cx=".27" cy=".19" r=".95">
          <stop stop-color="#F8FCFD"/><stop offset=".28" stop-color="#B9D3DC"/><stop offset=".70" stop-color="#698EA1"/><stop offset="1" stop-color="#41637A"/>
        </radialGradient>
        <radialGradient id="f14_blue" cx=".24" cy=".15" r=".9">
          <stop stop-color="#96D4E4"/><stop offset=".34" stop-color="#559DB8"/><stop offset=".72" stop-color="#31728C"/><stop offset="1" stop-color="#1B5069"/>
        </radialGradient>
        <pattern id="f14_grid" width="30" height="30" patternUnits="userSpaceOnUse">
          <path d="M30 0 H0 V30" fill="none" stroke="#ABC9D5" stroke-width="1" opacity=".5"/>
        </pattern>
      </defs>
      <rect width="540" height="960" fill="url(#f14_bg)"/>
      <rect width="540" height="106" fill="#112F43"/>
      <rect x="28" y="13" width="130" height="21" rx="5" fill="#FFCF68"/>
      <text x="38" y="28" fill="#153648" font-family="DejaVu Sans" font-size="9.2" font-weight="900">CORINGA EXPLICA</text>
      <text x="30" y="162" data-essential="machine_title" fill="#173A50" font-family="DejaVu Sans" font-size="22" font-weight="900">{title}</text>
      <text x="30" y="185" data-essential="subtitle" fill="#567888" font-family="DejaVu Sans" font-size="11">{subtitle}</text>
      <rect x="28" y="98" width="474" height="4" rx="2" fill="#55778A"/>
      <rect x="28" y="98" width="{move:.3f}" height="4" rx="2" fill="#F6BE57"/>
      <text x="30" y="225" data-essential="phase" fill="#153A50" font-family="DejaVu Sans" font-size="20" font-weight="900">{step}</text>
      <text x="30" y="250" data-essential="detail" fill="#436A7C" font-family="DejaVu Sans" font-size="12">{detail}</text>
      <path d="M30 269 H510" stroke="#B9D1DB" stroke-width="2"/>
      <g id="machine-stage" data-camera-policy="static" transform="translate(0 0)">
        <rect x="65" y="292" width="410" height="434" rx="30" fill="#426B81" stroke="#244658" stroke-width="9"/>
        <rect x="79" y="308" width="382" height="400" rx="18" fill="url(#f14_bg)" stroke="#AECBD6" stroke-width="5"/>
        <rect x="89" y="317" width="362" height="382" rx="8" fill="url(#f14_grid)" opacity=".72"/>
        <g id="rotational-shafts" fill="#2B5267" stroke="#D5E7EC" stroke-width="4">
          <rect x="76" y="{y-13:.2f}" width="{x1-76:.2f}" height="26" rx="9"/>
          <rect x="{x2:.2f}" y="{y-13:.2f}" width="{457-x2:.2f}" height="26" rx="9"/>
          <circle cx="{x1:.2f}" cy="{y:.2f}" r="26"/>
          <circle cx="{x2:.2f}" cy="{y:.2f}" r="27"/>
        </g>
        <g id="pair-gear-components">
          {g1}
          {g2}
        </g>
        <g id="pitch-contact" fill="none">
          <circle cx="{x1:.2f}" cy="{y:.2f}" r="{p.driving.pitch:.3f}" stroke="#FFDB84" stroke-width="1" stroke-dasharray="2 6" opacity=".35"/>
          <circle cx="{x2:.2f}" cy="{y:.2f}" r="{p.driven.pitch:.3f}" stroke="#FFDB84" stroke-width="1" stroke-dasharray="2 6" opacity=".35"/>
          <circle cx="{x1+p.driving.pitch:.2f}" cy="{y:.2f}" r="3.6" fill="#F2C66F" stroke="#25495B" stroke-width="1.2"/>
        </g>
        <g fill="#DDEAF0" stroke="#23485D" stroke-width="3">
          <circle cx="93" cy="323" r="6"/><circle cx="447" cy="323" r="6"/>
          <circle cx="93" cy="692" r="6"/><circle cx="447" cy="692" r="6"/>
        </g>
        <g font-family="DejaVu Sans" font-size="11" fill="#1D4458" font-weight="900">
          <text x="{x1:.2f}" y="652" text-anchor="middle">ENTRADA · Z={p.driving.z}</text>
          <text x="{x2:.2f}" y="652" text-anchor="middle">SAÍDA · Z={p.driven.z}</text>
        </g>
      </g>
      <text x="30" y="772" fill="#173C50" font-family="DejaVu Sans" font-size="25" font-weight="900">REDUÇÃO {ratio}:1</text>
      <text x="30" y="803" fill="#446A7F" font-family="DejaVu Sans" font-size="14">ENGRENAGENS EXTERNAS · GIROS OPOSTOS</text>
      <path d="M30 826 H510" stroke="#B0CAD5" stroke-width="2"/>
      <text x="30" y="851" fill="#4E7183" font-family="DejaVu Sans" font-size="12">MÓDULO {p.driving.module:g} px · DISTÂNCIA {p.center_distance:g} px</text>
      <text x="30" y="922" fill="#4C7085" font-family="DejaVu Sans" font-size="11" font-weight="900">LAB F14 · ILUSTRAÇÃO NÃO INDUSTRIAL</text>
      <text x="457" y="922" fill="#4C7085" font-family="DejaVu Sans" font-size="11.5" font-weight="900">{i+1:02d}/02</text>
    </svg>'''
    try:
        root=ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError("F14-COMPOSITOR-SVG") from exc
    if not G.svg_actors_check(svg):
        err("ATORES")
    stage_nodes=[n for n in root.iter() if n.get("id")=="machine-stage"]
    if len(stage_nodes)!=1 or stage_nodes[0].get("transform")!="translate(0 0)":
        err("CAMERA")
    return svg

def render(scene,out_path):
    p=validate(scene)
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True)
    fps=scene["fps"];dur=scene["duration_s"]
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-video_size","540x960",
         "-r",str(fps),"-i","-","-c:v","libx264","-preset","veryfast",
         "-crf","23","-pix_fmt","yuv420p","-movflags","+faststart",str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(round(fps*dur)):
            svg=frame(scene,i/fps)
            raw=cairosvg.svg2png(bytestring=svg.encode("utf8"))
            with Image.open(io.BytesIO(raw)) as image:
                proc.stdin.write(image.convert("RGB").tobytes())
    finally:
        if proc.stdin is not None:proc.stdin.close()
    if proc.wait()!=0 or not out.is_file() or out.stat().st_size<35_000:
        err("MP4_INVALIDO")
    record={
       "schema":"coringa-spur-gear-qa-f14-v1",
       "id":scene["id"],"family":FAMILY,"video":SIZE,"fps":fps,
       "duration_s":dur,"source_technical_only":SOURCE,
       "source_image_copied":False,"model":"involute_no_root_fillet",
       "industrial_accuracy_approved":False,
       "industrial_identity_verified":False,"user_device_ui_verified":False,
       "visual_approval":False,"publish":False,
       "camera_static":True,"geometry_generated_from_module_and_teeth":True,
       "teeth":[p.driving.z,p.driven.z],
       "ratio":p.ratio,"center_distance_px":p.center_distance,
       "driver_revolutions":scene["driver_revolutions"],
       "sha256":hashlib.sha256(out.read_bytes()).hexdigest()
    }
    out.with_suffix(".json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf8")
    return record

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("scene",type=Path)
    ap.add_argument("video",type=Path)
    args=ap.parse_args()
    print(json.dumps(render(load(args.scene),args.video),ensure_ascii=False,indent=2))
