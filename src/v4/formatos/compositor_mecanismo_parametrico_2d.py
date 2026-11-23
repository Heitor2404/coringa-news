"""F6 — compositor genérico SVG a partir de uma CENA JSON + kernel físico.

Não contém desenhos ou coordenadas específicas de um episódio.
As funções físicas são registradas por kernel e as peças são montadas
pela biblioteca de primitivas SVG já reutilizada na eclusa (F4).
Dois arquivos de cena usam EXATAMENTE este compositor; geometria e
seções mudam sem copiar o script ou alterar a regra de câmera.

Restrições: apenas 2D didático privado; metadados de fontes não
constituem licença de imagem; nada gera rig, foto ou modelo 3D externo.
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
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import cairosvg
from PIL import Image

from src.v4.formatos import (
    biblioteca_componentes_fisicos as B,
    camera_causal_svg as C,
    fisica_reservatorios_parametricos as F,
    grafo_causal as G,
    primitivas_fisicas_parametricas as P,
)

WIDTH,HEIGHT=540,960
SCHEMA="coringa-parametric-mechanism-scene-v1"
FAMILY="vasos_comunicantes"
KERNEL="equalizacao_2_reservatorios_sem_inercia"
# IDs formam o contrato de entrada do kernel, mas não representam
# peças prontas de nenhuma configuração de tanque.
ROLE_TYPES={
  "left_tank":"reservoir","right_tank":"reservoir",
  "left_water":"fluid_body","right_water":"fluid_body",
  "link_pipe":"conduit","control_valve":"valve",
}
HORIZONTAL=re.compile(r"^M (\d+) (\d+) H (\d+)$")


def _fail(code):
    raise ValueError(code)


def _number(x,lo,hi):
    if type(x) not in (int,float) or not math.isfinite(x) or not lo<=x<=hi:
        _fail("F-COMP-PARAMETRO-INVALIDO")
    return float(x)


def carregar(path:Path)->dict:
    p=Path(path)
    if not p.is_file() or p.suffix.lower()!=".json" or p.stat().st_size>60_000:
        _fail("F-COMP-CENA-AUSENTE")
    try:
        obj=json.loads(p.read_text("utf8"))
    except (ValueError,UnicodeError):
        _fail("F-COMP-JSON-INVALIDO")
    validar(obj)
    return obj


def validar(obj:dict)->dict:
    if (not isinstance(obj,dict) or obj.get("schema")!=SCHEMA or
        obj.get("version")!=1 or obj.get("publish") is not False or
        obj.get("identity_approval") is not False or
        obj.get("family")!=FAMILY or
        obj.get("camera")!="plano_geral_travado" or
        obj.get("video")!=[WIDTH,HEIGHT]):
        _fail("F-COMP-CENA-NAO-HOMOLOGADA")
    rights=obj.get("rights") or {}
    if (not isinstance(rights,dict) or
        rights.get("external_pixels_copied") is not False or
        rights.get("source_is_license") is not False or
        obj.get("source")!="https://openstax.org/books/university-physics-volume-1/pages/14-1-fluids-density-and-pressure" or
        obj.get("source_scope")!="PRINCIPIO_HIDROSTATICO_NAO_LICENCA_DE_PIXELS"):
        _fail("F-COMP-FONTE-NAO-VALIDADA")
    for k in ("id","title","subtitle"):
        x=obj.get(k)
        if not isinstance(x,str) or not 2<=len(x)<=74 or any(c in x for c in "<>&"):
            _fail("F-COMP-TEXTO-INVALIDO")
    duration=_number(obj.get("duration_s"),10,25)
    if obj.get("fps") not in (24,30):
        _fail("F-COMP-FPS")
    parts=obj.get("components")
    if not isinstance(parts,list) or len(parts)!=len(ROLE_TYPES):
        _fail("F-COMP-PECAS-INCOMPLETAS")
    if any(not isinstance(x,dict) for x in parts):
        _fail("F-COMP-PECA-INVALIDA")
    by={p.get("id"):p for p in parts}
    if len(by)!=len(parts) or set(by)!=set(ROLE_TYPES):
        _fail("F-COMP-ATOR-AUSENTE-OUDUPLICADO")
    for name,part in by.items():
        if (part.get("primitive")!=ROLE_TYPES[name] or
            part["primitive"] not in B.TIPOS_PERMITIDOS or
            part["primitive"] not in P.PRIMITIVAS_DESENHAVEIS):
            _fail("F-COMP-PRIMITIVA-INDISPONIVEL")
    # Requer ao mesmo tempo gramática causal, catálogo de primitivas e
    # câmera SEMÂNTICA global. Nenhum "tema" livre contorna essas travas.
    actions=tuple(x["acao"] for x in G.GRAFOS[FAMILY]["eventos"])
    causal=G.montar(FAMILY,actions)
    assert set(ROLE_TYPES)=={a["id"] for a in causal["atores"]}
    timeline=obj.get("timeline")
    if (not isinstance(timeline,list) or
        [x.get("acao") for x in timeline if isinstance(x,dict)]!=list(actions) or
        len(timeline)!=len(actions)):
        _fail("F-COMP-EVENTOS-DIVERGENTES")
    end=0.
    for step in timeline:
        if not isinstance(step,dict):
            _fail("F-COMP-EVENTO")
        start=_number(step.get("start"),0,duration)
        stop=_number(step.get("end"),start+.01,duration)
        if abs(start-end)>1e-7:
            _fail("F-COMP-CICLO-DESCONTINUO")
        end=stop
        for field in ("title","subtitle"):
            label=step.get(field)
            if not isinstance(label,str) or not 4<=len(label)<=86 or any(c in label for c in "<>&"):
                _fail("F-COMP-LEGENDA")
    if abs(end-duration)>1e-6:
        _fail("F-COMP-CICLO-NAO-TERMINA")
    tank={}
    for role in ("left_tank","right_tank"):
        part=by[role]
        x=_number(part.get("x"),12,430)
        y=_number(part.get("y"),300,500)
        w=_number(part.get("width"),100,260)
        h=_number(part.get("height"),200,480)
        if x+w>515 or y+h>835 or part.get("label") not in ("A","B"):
            _fail("F-COMP-TANQUE-FORA-PALCO")
        tank[role]=part
    l,r=tank["left_tank"],tank["right_tank"]
    if (l["x"]+l["width"]+56>r["x"] or
        abs(l["y"]-r["y"])>1e-7 or
        abs(l["height"]-r["height"])>1e-7):
        _fail("F-COMP-TANQUES-SOBREPOSTOS")
    for name,ref in (("left_water","left_tank"),("right_water","right_tank")):
        if by[name].get("container")!=ref:
            _fail("F-COMP-AGUA-SEM-TANQUE")
    pipe=by["link_pipe"]
    match=HORIZONTAL.fullmatch(str(pipe.get("path")))
    if match is None:
        _fail("F-COMP-CONDUTO-INVALIDO")
    p1,py,p2=map(int,match.groups())
    if (p1>=p2 or p2-p1<60 or
        abs(p1-(l["x"]+l["width"]-12))>3 or
        abs(p2-(r["x"]+12))>3 or
        py<l["y"]+l["height"]-108 or py>l["y"]+l["height"]-30 or
        py!=pipe.get("y")):
        _fail("F-COMP-TUBO-NAO-CONNECTADO")
    valve=by["control_valve"]
    vx=_number(valve.get("x"),p1+18,p2-18)
    vy=_number(valve.get("y"),py,py)
    if not p1+18<vx<p2-18:
        _fail("F-COMP-VALVULA-FORA-TUBO")
    f=obj.get("physics")
    if (not isinstance(f,dict) or f.get("solver")!=KERNEL or
        f.get("explanatory_time_not_measured") is not True or
        f.get("volume_conservation") is not True):
        _fail("F-COMP-SOLVER-SEM-PROVA")
    _number(f.get("initial_left_y"),l["y"]+21,py-18)
    _number(f.get("initial_right_y"),l["y"]+21,py-18)
    if f["initial_left_y"]>=f["initial_right_y"]:
        _fail("F-COMP-ORDEM-HIDROSTATICA")
    t_open=_number(f.get("opening_from_s"),timeline[1]["start"],timeline[1]["end"])
    _number(f.get("opening_to_s"),t_open+.01,timeline[2]["start"])
    _number(f.get("flow_from_s"),timeline[2]["start"],timeline[2]["start"])
    _number(f.get("flow_to_s"),timeline[3]["start"],timeline[3]["start"])
    # Confere TODAS as caixas curadas, inclusive nos dois presets.
    cfg=C.CAMERAS["familias"][FAMILY]
    for name,part in by.items():
        bbox=C.Caixa.parse(cfg["roles"][name])
        if name in ("left_tank","right_tank"):
            if not (bbox.x1<=part["x"] and bbox.y1<=part["y"]
                and bbox.x2>=part["x"]+part["width"]
                and bbox.y2>=part["y"]+part["height"]):
                _fail("F-COMP-ATOR-SEM-BBOX")
        elif name in ("left_water","right_water"):
            container=l if name=="left_water" else r
            if (bbox.x1>container["x"]+13 or bbox.x2<container["x"]+container["width"]-13
                 or bbox.y1>f["initial_left_y"] if name=="left_water" else False):
                _fail("F-COMP-AGUA-SEM-BBOX")
        elif name=="control_valve":
            if not (bbox.x1<=vx-18 and bbox.x2>=vx+18
                    and bbox.y1<=py-18 and bbox.y2>=py+18):
                _fail("F-COMP-VALVULA-SEM-BBOX")
    P.verificar_reuso()
    return {"componentes":by,"causal":causal,"duration":duration}


def simular(obj:dict,t:float):
    v=validar(obj)
    p=v["componentes"]
    f=obj["physics"]
    tank=p["left_tank"]
    return F.simular(
        t,duracao=v["duration"],
        area_esquerda=p["left_tank"]["width"]-26,
        area_direita=p["right_tank"]["width"]-26,
        fundo_y=tank["y"]+tank["height"]-13,
        topo_y=tank["y"]+13,
        esquerda_y=f["initial_left_y"],
        direita_y=f["initial_right_y"],
        abertura_de=f["opening_from_s"],
        abertura_ate=f["opening_to_s"],
        vazao_de=f["flow_from_s"],
        vazao_ate=f["flow_to_s"])


def frame_svg(obj:dict,t:float)->str:
    v=validar(obj)
    dur=v["duration"]
    t=_number(t,0,dur)
    steps=obj["timeline"]
    i=next((j for j,part in enumerate(steps)
             if part["start"]<=t<part["end"]),len(steps)-1)
    current=steps[i]
    if current["acao"]!=v["causal"]["eventos"][i]["acao"]:
        _fail("F-COMP-FISICA-DIVERGE-GRAFO")
    pose=C.calcular(FAMILY,current["acao"],t,current["start"],dur)
    if not C.verificar_pose(FAMILY,pose):
        _fail("F-COMP-CAMERA-CORTOU")
    parts=v["componentes"]
    state=simular(obj,t)
    def role(id_,contents):
        kind=ROLE_TYPES[id_]
        return (f'<g id="role-{id_}" data-primitive="{kind}" '
             f'data-source-tech="openstax_hidrostatica" '
             f'data-visual-identity="PENDENTE">{contents}</g>')
    scene=[]
    for id_ in ("left_tank","right_tank"):
        p=parts[id_]
        physical=P.reservatorio(p["x"],p["y"],p["width"],p["height"])
        scene.append(role(id_,physical))
    for id_,tank_role,level in (
         ("left_water","left_tank",state.nivel_esquerdo_y),
         ("right_water","right_tank",state.nivel_direito_y)):
        tank=parts[tank_role]
        scene.append(role(id_,P.agua_no_tanque(
            tank["x"]+13,level,tank["width"]-26,
            tank["y"]+tank["height"]-13)))
    pipe=parts["link_pipe"]
    stage_pipe=P.conduto(pipe["path"],vazao=state.fluxo,
                        deslocamento=-t*42,largura=25,miolo=13,fio=6)
    scene.append(role("link_pipe",stage_pipe))
    valve=parts["control_valve"]
    scene.append(role("control_valve",P.valvula(
        valve["x"],valve["y"],state.valvula_aberta,raio=15)))
    machine="\n".join(scene)
    # Todos os papéis têm desenho real único no SVG, não só catálogo.
    xmlroles=set(re.findall(r'id="role-([a-z_]+)"',machine))
    if xmlroles!=set(ROLE_TYPES):
        _fail("F-COMP-SVG-ATOR-AUSENTE")
    for name in ("left_tank","right_tank"):
        part=parts[name]
        machine+=(f'<text x="{part["x"]+part["width"]/2:.2f}" '
              f'y="{part["y"]-14:.2f}" font-size="17" '
              f'font-weight="900" fill="#385B71" text-anchor="middle" '
              f'font-family="DejaVu Sans">RESERVATÓRIO {escape(part["label"])}</text>')
    step=escape(current["title"])
    explanation=escape(current["subtitle"])
    title=escape(obj["title"])
    subtitle=escape(obj["subtitle"])
    transform=pose.transform_svg(0)
    progress=round(t/dur*472,2)
    # A única câmera para todo o ciclo; os estados movem só a física.
    svg=f"""<svg xmlns="http://www.w3.org/2000/svg" width="540" height="960"
        viewBox="0 0 540 960">
      <defs>
        <linearGradient id="background" x1="0" x2="0" y1="0" y2="1">
          <stop stop-color="#F7FCFB"/><stop offset="1" stop-color="#DBE9EC"/>
        </linearGradient>
        <pattern id="grid" width="38" height="38" patternUnits="userSpaceOnUse">
          <path d="M 38 0 H 0 V 38" fill="none" stroke="#C0D5DE"
            stroke-width=".8" opacity=".5"/>
        </pattern>
      </defs>
      <rect width="540" height="960" fill="url(#background)"/>
      <rect y="213" width="540" height="692" fill="url(#grid)"/>
      <rect width="540" height="211" fill="#112F43"/>
      <rect x="34" y="27" width="176" height="26" rx="7" fill="#FFCC69"/>
      <text x="47" y="45" font-family="DejaVu Sans" font-size="12"
        fill="#163548" font-weight="900">CORINGA EXPLICA</text>
      <text x="34" y="105" font-family="DejaVu Sans" font-size="29"
        fill="#F9FCFC" font-weight="900">{title}</text>
      <text x="35" y="143" font-family="DejaVu Sans" font-size="21"
        fill="#F5C46B" font-weight="900">{step}</text>
      <text x="35" y="173" font-family="DejaVu Sans" font-size="13.3"
        fill="#D6E6EE">{explanation}</text>
      <rect x="35" y="192" width="472" height="6" rx="3" fill="#496A7E"/>
      <rect x="35" y="192" width="{progress:.2f}" height="6"
        rx="3" fill="#F4C56C"/>
      <text x="35" y="270" font-family="DejaVu Sans" font-size="13"
        fill="#527287" font-weight="800">{subtitle}</text>
      <g id="machine-stage" transform="{transform}">
        {machine}
      </g>
      <text x="35" y="851" font-size="13.5" font-family="DejaVu Sans"
        fill="#355D72" font-weight="800">PRESSÃO DEPENDE DA ALTURA DA ÁGUA</text>
      <text x="35" y="873" font-size="11.5" font-family="DejaVu Sans"
        fill="#638597">ESCOAMENTO ILUSTRATIVO · TEMPO NÃO MEDIDO</text>
      <path d="M 34 903 H 505" stroke="#B2CAD3" stroke-width="2"/>
      <text x="34" y="929" fill="#527084" font-family="DejaVu Sans"
        font-weight="900" font-size="11">PROVA PRIVADA · CORTE 2D PARAMÉTRICO</text>
      <text x="463" y="929" fill="#527084" font-family="DejaVu Sans"
        font-weight="900" font-size="13">{i+1:02d}/04</text>
    </svg>"""
    try:
        tree=ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError("F-COMP-SVG-INVALIDO") from exc
    marker=[e.get("id") for e in tree.iter()
            if str(e.get("id","")).startswith("role-")]
    if len(marker)!=6 or len(set(marker))!=6:
        _fail("F-COMP-ATOR-DUPLICADO-SVG")
    return svg


def renderizar(obj:dict,arquivo:Path)->dict:
    validar(obj)
    duration=obj["duration_s"]
    fps=obj["fps"]
    filename=Path(arquivo)
    filename.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","rawvideo","-pix_fmt","rgb24","-video_size","540x960",
        "-r",str(fps),"-i","-","-c:v","libx264","-preset","veryfast",
        "-crf","23","-pix_fmt","yuv420p","-movflags","+faststart",str(filename)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in range(round(duration*fps)):
            xml=frame_svg(obj,frame/fps)
            data=cairosvg.svg2png(bytestring=xml.encode("utf8"))
            with Image.open(io.BytesIO(data)) as img:
                pixels=img.convert("RGB").tobytes()
            proc.stdin.write(pixels)
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not filename.is_file() or filename.stat().st_size<40000:
        raise ValueError("F-COMP-MP4-FALHOU")
    report={
      "schema":"coringa-parametric-qa-v1","family":FAMILY,
      "preset_id":obj["id"],"renderer":"UM_COMPOSITOR_COM_PRIMITIVAS_REAIS",
      "components":len(ROLE_TYPES),"components_parametric":sorted(P.PRIMITIVAS_DESENHAVEIS),
      "physics_kernel":KERNEL,
      "volume_conserved":True,"camera_static":True,
      "external_image_reused":False,"geometry_from_source_video":False,
      "publication_approved":False,"visual_approval":"PENDENTE",
      "duration_s":duration,"fps":fps,"size":[WIDTH,HEIGHT],
      "sha256":hashlib.sha256(filename.read_bytes()).hexdigest()
    }
    filename.with_suffix(".json").write_text(json.dumps(
       report,ensure_ascii=False,indent=2),encoding="utf8")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("scene_json",type=Path)
    parser.add_argument("output_mp4",type=Path)
    args=parser.parse_args()
    print(json.dumps(renderizar(carregar(args.scene_json),args.output_mp4),
                     ensure_ascii=False,indent=2))
