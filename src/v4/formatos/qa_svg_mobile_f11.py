"""F11 — auditoria de oclusao REAL das pecas SVG em interfaces simuladas.

Reusa unicamente os perfis ativos_seguros de plataformas.json via layout.py.
A diferenca de imagens com/sem um ator mede a area realmente VISIVEL
que ele contribui ao frame; evita usar envelope largo da camera como
falsa deteccao. Nao declara a UI atual de nenhum app como garantida.
"""
from __future__ import annotations

import argparse
import copy
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image, ImageChops, ImageDraw, ImageFont

from src.v4.formatos import compositor_cinematico_parametrico_2d as M
from src.v4.formatos import layout as L

W,H=540,960
CRITICAL=("piston","connecting_rod","flywheel","drive_belt")
TIMES=(1.1,3.6,6.7)
PROFILE_NAMES=tuple(L.CFG["ativos_seguros"])


def _error(msg):
    raise ValueError("F11-ZONA-"+msg)


def _raster(xml):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=xml.encode("utf8")))) as im:
        return im.convert("RGB").copy()


def _root(svg):
    try:
        root=ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError("F11-ZONA-SVG-INVALIDO") from exc
    if root.get("width")!=str(W) or root.get("height")!=str(H):
        _error("FORMATO")
    return root


def _no_role(root,actor):
    cloned=copy.deepcopy(root)
    found=[]
    for parent in cloned.iter():
        for child in list(parent):
            if child.attrib.get("id")==f"role-{actor}":
                found.append((parent,child))
    if len(found)!=1:
        _error("ATOR_AUSENTE_OU_DUPLICADO:"+actor)
    found[0][0].remove(found[0][1])
    return ET.tostring(cloned,encoding="unicode")


def _threshold_difference(a,b):
    delta=ImageChops.difference(a,b)
    # Diferenca perceptivel de canal, nao ruido do encoder (SVG puro).
    return delta.convert("L").point(lambda v:255 if v>=18 else 0,mode="L")


def _rects(name,include_feed=False):
    if name not in PROFILE_NAMES:
        _error("PERFIL_DESCONHECIDO")
    rectangles=[]
    for item in L.mascaras(name):
        if item.get("aviso") and not include_feed:
            continue
        x,y,w,h=item["caixa"]
        if not all(type(z) in (int,float) for z in (x,y,w,h)):
            _error("PERFIL_CORROMPIDO")
        rect=(
            max(0,min(W,int(round(x/2)))),
            max(0,min(H,int(round(y/2)))),
            max(0,min(W,int(round((x+w)/2)))),
            max(0,min(H,int(round((y+h)/2)))),
        )
        if rect[2]<=rect[0] or rect[3]<=rect[1]:
            _error("PERFIL_VAZIO")
        rectangles.append((item["tipo"],rect))
    return rectangles


def mascara(name):
    m=Image.new("L",(W,H),0)
    draw=ImageDraw.Draw(m)
    for _,rect in _rects(name):
        draw.rectangle((rect[0],rect[1],rect[2]-1,rect[3]-1),fill=255)
    return m


def _count(image):
    return image.histogram()[-1]


def medir(svg,roles=CRITICAL):
    root=_root(svg)
    base_xml=ET.tostring(root,encoding="unicode")
    base=_raster(base_xml)
    if not isinstance(roles,tuple) or not roles:
        _error("PAPEIS")
    result={}
    for role in roles:
        without=_raster(_no_role(root,role))
        mask=_threshold_difference(base,without)
        total=_count(mask)
        if total<25:
            _error("ATOR_SEM_CONTRIBUICAO_VISIVEL:"+role)
        risks={}
        for name in PROFILE_NAMES:
            over=ImageChops.multiply(mask,mascara(name))
            risk=_count(over)/total
            risks[name]=round(risk,4)
        result[role]={
            "pixel_bbox":list(mask.getbbox()),
            "visible_pixel_area":total,
            "overlap_fraction_per_platform":risks,
            "max_overlap_fraction":round(max(risks.values()),4),
        }
    return result


def _font(size=18):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",size)
    except OSError:
        return ImageFont.load_default()


def prancha(svg,path):
    frame=_raster(svg)
    panels=[]
    for name in ("sem_mascara",)+PROFILE_NAMES:
        copy_frame=frame.copy().convert("RGBA")
        if name!="sem_mascara":
            overlay=Image.new("RGBA",(W,H),(0,0,0,0))
            d=ImageDraw.Draw(overlay)
            for typ,rect in _rects(name):
                alpha=42 if typ in ("topo","base") else 69
                d.rectangle((rect[0],rect[1],rect[2]-1,rect[3]-1),
                            fill=(224,55,35,alpha),outline=(190,50,30,160),width=2)
            copy_frame=Image.alpha_composite(copy_frame,overlay)
        panels.append((name,copy_frame.convert("RGB")))
    board=Image.new("RGB",(4*W,H+42),"#e6eef3")
    draw=ImageDraw.Draw(board)
    for i,(name,im) in enumerate(panels):
        board.paste(im,(i*W,42))
        label=name.upper().replace("_MULTIPLATAFORMA","")
        draw.text((i*W+10,9),label,font=_font(17),fill="#183a50")
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    board.save(path,quality=89)


def analisar(scene, out, *, animation=True, enquadramento_mobile=None):
    """Faz QA de 3 instantes das duas fases, sem fingir safe zone aprovada."""
    M.validar(scene)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    slices={}
    worst=0.0
    for t in TIMES:
        xml=M.frame_svg(scene,t,transmissao_animada=animation,
                        enquadramento_mobile=enquadramento_mobile)
        data=medir(xml)
        slices[str(t)]=data
        worst=max(worst,*(item["max_overlap_fraction"] for item in data.values()))
    suffix="F12" if enquadramento_mobile else "F11"
    prancha(M.frame_svg(scene,3.6,transmissao_animada=animation,
                        enquadramento_mobile=enquadramento_mobile),
           out/(scene["id"]+f"_{suffix}_MASCARAS_PERFIL_SIMULADO.jpg"))
    report={
        "schema":"coringa-svg-mobile-role-audit-v1",
        "scene":scene["id"],"renderer":"compositor_cinematico_parametrico_2d",
        "image":[W,H],"sample_times_s":list(TIMES),"critical_roles":list(CRITICAL),
        "platform_source":"src/v4/formatos/plataformas.json:ativos_seguros",
        "masks_are_conservative_estimates":True,
        "mask_measurement":"DELTAS_RASTER_SVG_SEM_CODEC",
        "bbox_is_effectively_visible_not_envelope_camera":True,
        "worst_observed_overlap_fraction":round(worst,4),
        "status":"INSPECAO_UI_HUMANA_PENDENTE",
        "mobile_layout_mode":enquadramento_mobile or "original_f11",
        "publish":False,"visual_approval":False,
        "automatically_shrink_machine":False,
        "windows":slices,
    }
    (out/(scene["id"]+f"_{suffix}_AUDITORIA.json")).write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("scene",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--baseline",action="store_true")
    p.add_argument("--hero-f12",action="store_true")
    args=p.parse_args()
    print(json.dumps(analisar(M.carregar(args.scene),args.out,
                              animation=not args.baseline,
                              enquadramento_mobile="hero_elevado_f12" if args.hero_f12 else None),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
