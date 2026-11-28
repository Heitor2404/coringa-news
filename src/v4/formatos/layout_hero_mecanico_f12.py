"""F12 — compositor editorial HERO em cima do mesmo rig (LAB opt-in).

Desloca TODO o mecanismo somente em Y, por um unico transform SVG; nao
reescreve fisica, juntas, raio, escala ou camera. Compacta cabecalho e
remove metadata do rodape inferior. Usa envelope curado do CAMERAS (sem
inventar segmentacao). Perfis da F11 seguem estimativas, nao UI real.
"""
from __future__ import annotations

import math
from xml.etree import ElementTree as ET

from src.v4.formatos import camera_causal_svg as C

NS="http://www.w3.org/2000/svg"
TAG=lambda v:"{"+NS+"}"+v
HEADER_H=134
MECHANISM_GAP=12
TOP_GOAL=HEADER_H+MECHANISM_GAP
ALLOWED_FAMILY="slider_crank_parametrico"


def _fail(code):
    raise ValueError("F12-HERO-"+code)


def _one(root,kind,**attrs):
    matches=[node for node in root if node.tag==TAG(kind)
             and all(node.get(k)==str(v) for k,v in attrs.items())]
    if len(matches)!=1:
        _fail("ELEMENTO_NAO_IDENTIFICADO:"+kind+":"+str(attrs))
    return matches[0]


def _set(node,**values):
    for key,value in values.items():
        node.set(key,str(value))


def aplicar(svg:str,*,family:str,pose:C.Pose)->tuple[str,dict]:
    """Retorna novo SVG e diagnostico de layout. Falha em vez de minificar."""
    if family!=ALLOWED_FAMILY or not isinstance(pose,C.Pose):
        _fail("FAMILIA_OU_CAMERA")
    cfg=C.CAMERAS["familias"][family]
    if (cfg.get("width"),cfg.get("height"))!=(540,960):
        _fail("FORMATO")
    box=C.Caixa.parse(cfg["bounds"])
    if not C.verificar_pose(family,pose):
        _fail("POSE_FORA_PALCO")
    top=pose.scale*box.y1+pose.ty
    bottom=pose.scale*box.y2+pose.ty
    lift=round(top-TOP_GOAL,3)
    if (not math.isfinite(lift) or not 90<=lift<=165
            or top-lift<HEADER_H+MECHANISM_GAP-.1
            or bottom-lift>860):
        _fail("SEM_ESPACO_SEM_REDUZIR")
    try:
        root=ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError("F12-HERO-SVG_INVALIDO") from exc
    if root.tag!=TAG("svg") or root.get("width")!="540" or root.get("height")!="960":
        _fail("SVG_FORMATO")
    if root.get("data-layout"):
        _fail("DUPLO_LAYOUT")
    root.set("data-layout","hero_elevado_f12")
    grid=_one(root,"rect",y="207",width="540",height="708")
    _set(grid,y=HEADER_H,height=914-HEADER_H)
    header=_one(root,"rect",width="540",height="207")
    _set(header,height=HEADER_H)
    chip=_one(root,"rect",x="35",y="26",width="172",height="26")
    _set(chip,x=35,y=9,width=141,height=21,rx=5)
    brand=_one(root,"text",x="47",y="44")
    _set(brand,x=45,y=24,**{"font-size":"10.4"})
    title=_one(root,"text",x="34",y="104")
    _set(title,x=34,y=59,**{"font-size":"25"})
    phase=_one(root,"text",x="35",y="145")
    _set(phase,x=35,y=88,**{"font-size":"18"})
    detail=_one(root,"text",x="35",y="174")
    _set(detail,x=35,y=107,**{"font-size":"11.5"})
    subtitle=_one(root,"text",x="35",y="268")
    _set(subtitle,x=35,y=121,**{"font-size":"10.5"},fill="#BBD8E4")
    progress_bg=_one(root,"rect",x="35",y="190",width="472",height="6")
    _set(progress_bg,y=127,height=4,rx=2)
    progress_fg=[node for node in root
                 if node.tag==TAG("rect") and node.get("x")=="35"
                 and node.get("y")=="190" and node.get("height")=="6"
                 and node is not progress_bg]
    if len(progress_fg)!=1:
        _fail("PROGRESSO")
    _set(progress_fg[0],y=127,height=4,rx=2)
    status=_one(root,"text",x="36",y="852")
    _set(status,x=303,y=24,**{"font-size":"10.5"},fill="#D1E5EA")
    status.text=(status.text or "").replace("RAZÃO POLIAS","RAZÃO")
    note=_one(root,"text",x="36",y="876")
    root.remove(note)
    stage=_one(root,"g",id="machine-stage")
    original=stage.get("transform")
    if not original or "translate(" not in original or "scale(" not in original:
        _fail("TRANSFORM_INCOMPATIVEL")
    _set(stage,transform=f"translate(0 {-lift:.3f}) {original}",
         **{"data-layout-lift-px":f"{lift:.3f}"})
    ET.register_namespace("",NS)
    result=ET.tostring(root,encoding="unicode")
    return result,{
        "layout":"hero_elevado_f12","lift_px":lift,
        "scale_before":pose.scale,"scale_after":pose.scale,
        "camera_pose_unaltered":True,
        "mechanical_geometry_changed":False,
        "stage_top_px":round(top-lift,2),
        "stage_bottom_px":round(bottom-lift,2),
        "editorial_end_px":HEADER_H,
        "minimum_gap_px":MECHANISM_GAP,
        "mobile_ui_approved":False,
        "publish":False,
    }
