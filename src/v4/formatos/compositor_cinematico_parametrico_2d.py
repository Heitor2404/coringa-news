"""F7 — um compositor mecânico para dois rigs de biela-manivela via JSON.

Não escolhe mecanismo por título/episódio; cenas compartilham as mesmas
peças desenháveis, física exata e câmera fixa que o motor de compressor
e o Otto. SEM identidade fotográfica / engenharia CAD / publicação.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import cairosvg
from PIL import Image

from src.v4.formatos import (
    cinematica_biela_manivela as K,
    camera_causal_svg as C,
    grafo_causal as G,
    primitivas_fisicas_parametricas as P,
    pecas_visuais_f8 as V,
    layout_hero_mecanico_f12 as H12,
)

FAMILY="slider_crank_parametrico"
SCHEMA="coringa-parametric-slider-crank-v1"
ACTORS=("motor_pulley","drive_belt","flywheel",
        "connecting_rod","piston","cylinder")
TYPES={"motor_pulley":"rotor","drive_belt":"transmission",
       "flywheel":"rotor","connecting_rod":"transmission",
       "piston":"piston","cylinder":"chamber"}
WIDTH=540
HEIGHT=960


def fail(code):
    raise ValueError(code)


def finite(x,lo,hi):
    if type(x) not in (float,int) or not math.isfinite(x) or not lo<=x<=hi:
        fail("F-COMP-MEC-PARAMETRO")
    return float(x)


def _hex(x):
    if not isinstance(x,str) or len(x)!=7 or x[0]!="#" or any(
        c not in "0123456789abcdefABCDEF" for c in x[1:]):
        fail("F-COMP-MEC-COR")
    return x


def carregar(path:Path)->dict:
    path=Path(path)
    if not path.is_file() or path.suffix!=".json" or path.stat().st_size>45000:
        fail("F-COMP-MEC-CENA-AUSENTE")
    try:
        scene=json.loads(path.read_text("utf8"))
    except (UnicodeError,ValueError):
        fail("F-COMP-MEC-JSON")
    validar(scene)
    return scene


def validar(scene:dict)->dict:
    if (not isinstance(scene,dict) or scene.get("schema")!=SCHEMA or
        scene.get("version")!=1 or scene.get("family")!=FAMILY or
        scene.get("publish") is not False or
        scene.get("visual_approval") is not False or
        scene.get("video")!=[WIDTH,HEIGHT] or
        scene.get("camera")!="plano_geral_travado"):
        fail("F-COMP-MEC-NAO-HOMOLOGADO")
    if scene.get("actors")!=list(ACTORS):
        fail("F-COMP-MEC-ATOR-AUSENTE")
    if scene.get("fps")!=24:
        fail("F-COMP-MEC-FPS")
    duration=finite(scene.get("duration_s"),8,14)
    for name in ("id","title","subtitle"):
        value=scene.get(name)
        if not isinstance(value,str) or len(value)<4 or len(value)>65 or any(
            c in value for c in "<>&"):
            fail("F-COMP-MEC-TEXTO")
    physics=scene.get("physics")
    source=scene.get("source")
    legal=scene.get("legal")
    if (not isinstance(physics,dict) or
        physics.get("kernel")!="crank_slider_exact" or
        physics.get("rigid_rod") is not True or
        physics.get("ideal_belt_no_slip") is not True or
        physics.get("cycles")!=1 or
        not isinstance(source,dict) or source.get("kind")!="equacao_geometrica_interna" or
        source.get("verified_core")!="cinematica_biela_manivela.py" or
        source.get("external_pixels_copied") is not False or
        source.get("external_license_inferred") is not False or
        not isinstance(legal,dict) or
        legal.get("publish_permission") is not False or
        legal.get("external_media_used") is not False):
        fail("F-COMP-MEC-FISICA-OU-DIREITOS")
    raw=scene.get("phases")
    if not isinstance(raw,list) or len(raw)!=2:
        fail("F-COMP-MEC-FASES")
    graph=G.montar(FAMILY,tuple(x["acao"] for x in G.GRAFOS[FAMILY]["eventos"]))
    if [x["action"] for x in raw]!=[x["acao"] for x in graph["eventos"]]:
        fail("F-COMP-MEC-FASE-DIVERGENTE")
    for i,phase in enumerate(raw):
        start=finite(phase.get("start"),0,duration)
        end=finite(phase.get("end"),0,duration)
        if (abs(start-(duration/2)*i)>1e-6 or
            abs(end-(duration/2)*(i+1))>1e-6):
            fail("F-COMP-MEC-TEMPO-DE-FASE")
        for k in ("title","detail"):
            x=phase.get(k)
            if not isinstance(x,str) or len(x)<5 or len(x)>75 or any(c in x for c in "<>&"):
                fail("F-COMP-MEC-LEGENDA")
    crank=scene.get("crank")
    motor=scene.get("motor")
    piston=scene.get("piston")
    cylinder=scene.get("cylinder")
    palette=scene.get("palette")
    if not all(isinstance(x,dict) for x in (crank,motor,piston,cylinder,palette)):
        fail("F-COMP-MEC-COMPONENTE")
    cx=finite(crank.get("cx"),235,350)
    cy=finite(crank.get("cy"),660,760)
    r=finite(crank.get("radius"),20,85)
    L=finite(crank.get("rod"),115,280)
    wheel=finite(crank.get("wheel"),55,94)
    mx=finite(motor.get("cx"),80,120)
    my=finite(motor.get("cy"),660,760)
    mr=finite(motor.get("pulley"),21,40)
    pw=finite(piston.get("width"),100,160)
    ph=finite(piston.get("height"),60,105)
    x=finite(cylinder.get("x"),215,260)
    y=finite(cylinder.get("y"),340,400)
    w=finite(cylinder.get("width"),120,172)
    h=finite(cylinder.get("height"),260,320)
    _hex(palette.get("primary"));_hex(palette.get("accent"))
    if abs(my-cy)>15 or abs(x+w/2-cx)>6:
        fail("F-COMP-MEC-EIXO-DESALINHADO")
    if x+w>425 or y+h>670 or L<=r+35:
        fail("F-COMP-MEC-MAQUINA-FORA-PALCO")
    if math.hypot(cx-mx,cy-my)<=mr+wheel+9:
        fail("F-COMP-MEC-CORREIA-IMPOSSSIVEL")
    upper=K.calcular(0,r,L,cx,cy)
    lower=K.calcular(math.pi,r,L,cx,cy)
    ytop=upper.piston_y-ph/2
    ybottom=lower.piston_y+ph/2
    if x+(w-pw)/2<0 or ytop<y+38 or ybottom>y+h-6:
        fail("F-COMP-MEC-CURSO-CORTA-CILINDRO")
    if min(mx-mr,cx-wheel)<53 or cx+wheel>402 or cy+wheel>815:
        fail("F-COMP-MEC-ROTOR-FORA-PALCO")
    # Check all swept envelopes against the shared camera's curated bboxes.
    cfg=C.CAMERAS["familias"][FAMILY]
    for key in ACTORS:
        if key not in cfg["roles"]:
            fail("F-COMP-MEC-ATOR-SEM-CAMERA")
    box=C.Caixa.parse(cfg["roles"]["piston"])
    if (box.x1>cx-pw/2-4 or box.x2<cx+pw/2+4 or
        box.y1>ytop-5 or box.y2<ybottom+5):
        fail("F-COMP-MEC-PISTAO-SEM-ENVELOPE")
    # Physics-and-parts checks require a FULL belt path in the same frame.
    P.transmissao_correia(mx,my,mr,cx,cy,wheel)
    P.verificar_reuso()
    V.validar_pecas(scene.get("visual_parts"))
    return {"graph":graph,"duration":duration,
            "radius":r,"rod":L,"center":(cx,cy),
            "motor":(mx,my,mr),"wheel_radius":wheel,
            "piston":(pw,ph),"cylinder":(x,y,w,h)}


def estado(scene:dict,t:float)->dict:
    spec=validar(scene)
    t=finite(t,0,spec["duration"])
    theta=2*math.pi*t/spec["duration"]
    cx,cy=spec["center"]
    rig=K.calcular(theta,spec["radius"],spec["rod"],cx,cy)
    angle_motor=K.angulo_motor(theta,spec["wheel_radius"],spec["motor"][2])
    return {"rig":rig,"theta":theta,"motor_angle_rad":angle_motor,
            "stroke":2*spec["radius"],
            "angle_ratio":spec["wheel_radius"]/spec["motor"][2],
            "time":t}


def frame_svg(scene:dict,t:float,*,transmissao_animada:bool=False,
              enquadramento_mobile:str|None=None)->str:
    spec=validar(scene)
    if enquadramento_mobile not in (None,"hero_elevado_f12"):
        fail("F-COMP-MEC-LAYOUT-NAO-CADASTRADO")
    state=estado(scene,t)
    rig=state["rig"]
    steps=scene["phases"]
    i=0 if t<spec["duration"]/2 else 1
    action=steps[i]["action"]
    phase=steps[i]
    pose=C.calcular(FAMILY,action,state["time"],phase["start"],spec["duration"])
    if not C.verificar_pose(FAMILY,pose):
        fail("F-COMP-MEC-CAMERA-CORTOU")
    cx,cy=spec["center"]
    motor_x,motor_y,motor_r=spec["motor"]
    wheel=spec["wheel_radius"]
    pwidth,pheight=spec["piston"]
    tx,ty,tw,th=spec["cylinder"]
    colors=scene["palette"]
    primary=colors["primary"]
    accent=colors["accent"]
    top=rig.piston_y-pheight/2
    px=cx-pwidth/2
    def role(name,markup):
        return (f'<g id="role-{name}" data-primitive="{TYPES[name]}" '
                'data-visual-identity="PENDENTE">'
                +markup+'</g>')
    # Build from parts, not a screenshot. Every actor exists ONLY ONCE.
    cylinder_svg=(f'<rect x="{tx-9:.2f}" y="{ty:.2f}" width="{tw+18:.2f}" '
       f'height="{th:.2f}" rx="18" fill="#527386" stroke="#244B60" stroke-width="8"/>'
       f'<rect x="{tx:.2f}" y="{ty+8:.2f}" width="{tw:.2f}" '
       f'height="{th-16:.2f}" rx="9" fill="#F6FBFC" stroke="#C0D8E1" stroke-width="5"/>'
       f'<path d="M {tx+7:.2f} {ty+25:.2f} V {ty+th-12:.2f} '
       f'M {tx+tw-7:.2f} {ty+25:.2f} V {ty+th-12:.2f}" '
       'stroke="#B5CDD3" stroke-width="4" fill="none"/>'
       f'<rect x="{tx-13:.2f}" y="{ty-15:.2f}" width="{tw+26:.2f}" '
       'height="23" rx="7" fill="#375D72" stroke="#25475B" stroke-width="4"/>')
    if scene.get("visual_parts"):
        cylinder_svg=V.desenhar_cilindro(scene["visual_parts"], tx-9, ty-15, tw+18, th+23)
    motor_casing=(f'<rect x="{motor_x-37:.2f}" y="{motor_y-81:.2f}" '
       'width="74" height="137" rx="17" fill="#62899D" stroke="#34596C" '
       'stroke-width="6"/>'
       f'<rect x="{motor_x-30:.2f}" y="{motor_y-75:.2f}" width="60" '
       'height="126" rx="12" fill="#94B8C4" opacity=".72"/>'
       f'<path d="M {motor_x-25:.2f} {motor_y-48:.2f} H {motor_x+25:.2f} '
       f'M {motor_x-25:.2f} {motor_y-32:.2f} H {motor_x+25:.2f}" '
       'stroke="#3C6478" stroke-width="6"/>')
    # F11 opt-in: MESMO operador de tangentes e marcacoes do compressor F10.
    # theta*raio_volante e a distancia ideal sem escorregamento; a camera fica travada.
    belt=P.transmissao_correia(motor_x,motor_y,motor_r,
                              cx,cy,wheel,largura=11,
                              deslocamento_trama_px=(state["theta"]*wheel if transmissao_animada else None))
    flywheel=P.rotor(cx,cy,wheel,math.degrees(state["theta"]),
                     corpo="#345C72",borda="#173D52",raios=5)
    pulley=P.rotor(motor_x,motor_y,motor_r,math.degrees(state["motor_angle_rad"]),
                   corpo="#416D80",borda="#234555",raios=4)
    rod=P.biela(rig.piston_x,rig.piston_y,rig.crank_x,rig.crank_y,
                largura=22,cor="#DDA86B")
    head=P.pistao(px,top,pwidth,pheight,cor=primary,
                  borda="#294D63",topo="#EAF5F6")
    pieces=[
       role("cylinder",cylinder_svg),
       motor_casing,
       role("drive_belt",belt),
       role("motor_pulley",pulley),
       role("flywheel",flywheel),
       role("connecting_rod",rod),
       role("piston",head),
    ]
    status=(f'CURSO {state["stroke"]:.0f} PX · '
            f'RAZÃO POLIAS {state["angle_ratio"]:.2f}×')
    content="\n".join(pieces)
    # The physical pose changes, never the camera. No cards on the stage.
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="540"
      height="960" viewBox="0 0 540 960">
      <defs>
        <linearGradient id="canvas" x1="0" y1="0" x2="0" y2="1">
          <stop stop-color="#F3FAFC"/><stop offset="1" stop-color="#DAEAF0"/>
        </linearGradient>
        <pattern id="grid" width="37" height="37" patternUnits="userSpaceOnUse">
          <path d="M 37 0 H 0 V 37" stroke="#BBD2DC"
            stroke-width=".85" fill="none" opacity=".60"/>
        </pattern>
      </defs>
      <rect width="540" height="960" fill="url(#canvas)"/>
      <rect y="207" width="540" height="708" fill="url(#grid)"/>
      <rect width="540" height="207" fill="#122F43"/>
      <rect x="35" y="26" width="172" height="26" rx="6" fill="#FFCF68"/>
      <text x="47" y="44" font-family="DejaVu Sans" font-size="12"
        font-weight="900" fill="#153444">CORINGA EXPLICA</text>
      <text x="34" y="104" font-family="DejaVu Sans" font-size="27"
        font-weight="900" fill="white">{escape(scene["title"])}</text>
      <text x="35" y="145" font-family="DejaVu Sans" font-size="22"
        font-weight="900" fill="{accent}">{escape(phase["title"])}</text>
      <text x="35" y="174" font-family="DejaVu Sans" font-size="12.3"
        fill="#DCEAEF">{escape(phase["detail"])}</text>
      <rect x="35" y="190" width="472" height="6" rx="3" fill="#496A7E"/>
      <rect x="35" y="190" width="{472*t/spec["duration"]:.2f}" height="6"
        rx="3" fill="{accent}"/>
      <text x="35" y="268" font-family="DejaVu Sans" font-size="13"
        font-weight="900" fill="#486B7B">{escape(scene["subtitle"])}</text>
      <g id="machine-stage" transform="{pose.transform_svg(0)}">
        {content}
      </g>
      <text x="36" y="852" font-family="DejaVu Sans" font-size="14"
        font-weight="900" fill="#375C72">{escape(status)}</text>
      <text x="36" y="876" font-family="DejaVu Sans" font-size="11.5"
        fill="#587C90">BIELA RÍGIDA · CORREIA IDEAL SEM ESCORREGAMENTO</text>
      <path d="M 35 904 H 505" stroke="#AFCCD6" stroke-width="2"/>
      <text x="35" y="930" font-family="DejaVu Sans" font-size="11"
        fill="#507086" font-weight="900">PROVA PRIVADA · CORTE 2D PARAMÉTRICO</text>
      <text x="464" y="930" font-family="DejaVu Sans" font-size="13"
        font-weight="900" fill="#507086">{i+1:02d}/02</text>
    </svg>'''
    try:
        root=ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError("F-COMP-MEC-SVG-INVALIDO") from exc
    found=[x.get("id")[5:] for x in root.iter()
           if (x.get("id") or "").startswith("role-")]
    if len(found)!=len(ACTORS) or set(found)!=set(ACTORS):
        fail("F-COMP-MEC-SVG-ATOR-INCOERENTE")
    if enquadramento_mobile=="hero_elevado_f12":
        svg,_=H12.aplicar(svg,family=FAMILY,pose=pose)
    return svg


def renderizar(scene:dict,path:Path,*,transmissao_animada:bool=False,
              enquadramento_mobile:str|None=None)->dict:
    spec=validar(scene)
    filename=Path(path)
    filename.parent.mkdir(parents=True,exist_ok=True)
    fps=scene["fps"]
    duration=spec["duration"]
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-video_size","540x960",
         "-r",str(fps),"-i","-","-c:v","libx264",
         "-preset","veryfast","-crf","23","-pix_fmt","yuv420p",
         "-movflags","+faststart",str(filename)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(round(duration*fps)):
            markup=frame_svg(scene,i/fps,transmissao_animada=transmissao_animada,
                             enquadramento_mobile=enquadramento_mobile)
            data=cairosvg.svg2png(bytestring=markup.encode("utf8"))
            with Image.open(io.BytesIO(data)) as im:
                pixels=im.convert("RGB").tobytes()
            proc.stdin.write(pixels)
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not filename.is_file() or filename.stat().st_size<45000:
        fail("F-COMP-MEC-MP4-INVALIDO")
    result={
       "schema":"coringa-mechanics-f7-qa-v1",
       "status":"LAB_NAO_HOMOLOGADO_ARTISTICAMENTE",
       "family":FAMILY,"id":scene["id"],
       "renderer":"UM_COMPOSITOR_PARA_DUAS_CENAS_JSON",
       "kernel":"cinematica_biela_manivela.calcular",
       "rod_constraint_exact":True,
       "belt_ratio_no_slip_ideal":True,
       "belt_animation_f11":bool(transmissao_animada),
       "layout_mobile_f12":enquadramento_mobile or "f7_original",
       "scale_reduction_f12":False,
       "belt_primitive_shared":"primitivas_fisicas_parametricas.transmissao_correia",
       "camera_fixed":True,"video":[WIDTH,HEIGHT],"fps":fps,
       "duration_s":duration,"has_audio":False,
       "external_media_copied":False,"publish":False,
       "visual_part_source":"autoral_interno_f8" if scene.get("visual_parts") else "f7_original",
       "industrial_reference_verified":False,
       "visual_approval":False,
       "sha256":hashlib.sha256(filename.read_bytes()).hexdigest()
    }
    filename.with_suffix(".json").write_text(
       json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("scene_json",type=Path)
    parser.add_argument("saida_mp4",type=Path)
    parser.add_argument("--visual-f8",action="store_true",help="Opt-in: peca SVG autoral com hash; nao homologada")
    parser.add_argument("--transmissao-animada",action="store_true",help="LAB F11: marcacoes no trajeto da correia usando F10")
    parser.add_argument("--hero-f12",action="store_true",help="LAB F12: cabeçalho compacto e mecanismo deslocado pra cima, SEM encolher")
    args=parser.parse_args()
    scene=carregar(args.scene_json)
    if args.visual_f8:
        scene["visual_parts"]={"cylinder":"cylinder_shell_f8"}
        scene["id"]+="_f8"
    print(json.dumps(renderizar(scene,args.saida_mp4,transmissao_animada=args.transmissao_animada,
                               enquadramento_mobile="hero_elevado_f12" if args.hero_f12 else None),
                     ensure_ascii=False,indent=2))
