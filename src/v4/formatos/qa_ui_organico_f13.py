"""F13 — auditoria orgânica com proveniência explícita da UI, não "safe zone oficial".

Toma informações medidas publicamente por terceiros, separa guias para ads
dos orgânicos e reusa o render SVG F12/F13, sem imagens copiadas. Cada
zona foi transcrita e possui fonte e data. Captura do DISPOSITIVO do canal
não foi fornecida; publicação permanece BLOQUEADA em todos os casos.
"""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image,ImageChops,ImageDraw,ImageFont
from src.v4.formatos import compositor_cinematico_parametrico_2d as M
from src.v4.formatos import qa_svg_mobile_f11 as Q

ROOT=Path(__file__).with_name("perfis_ui_evidencia_f13.json")
W,H=540,960
LABELS={"title":"f13-essential-title","phase":"f13-essential-phase",
        "detail":"f13-essential-detail"}
ROLE_IDS=("piston","connecting_rod","flywheel","drive_belt")
TIMES=(1.1,3.6,6.7)

def fail(label):
    raise ValueError("F13-UI-"+label)

def _profiles():
    try:
        d=json.loads(ROOT.read_text("utf8"))
    except (OSError,UnicodeError,ValueError):
        fail("ARQUIVO")
    if (d.get("schema")!="coringa-ui-evidence-f13-v1"
        or d.get("canvas")!=[1080,1920]
        or d.get("captured_in_user_device") is not False
        or d.get("measurements_are_first_party") is not False
        or d.get("no_platform_certification") is not True
        or d.get("proof_requirements",{}).get("permission_to_publish") is not False):
        fail("PROVENIENCIA")
    records=d.get("profiles")
    if not isinstance(records,list) or len(records)!=5:
        fail("QUANTIDADE")
    keys=[]
    for p in records:
        if not isinstance(p,dict) or p.get("placement") not in ("organic","ad"):
            fail("FONTE")
        if (not isinstance(p.get("source"),str) or
            not p["source"].startswith("https://") or
            p.get("tier") not in ("third_party_screen_measurement",
                                  "third_party_multidevice_measurement",
                                  "third_party_multidevice_estimate",
                                  "publisher_ads_guidance_retranscribed")):
            fail("FONTE")
        for v in ("top","bottom","button_right_width","button_start_y",
                  "side_crop_left","side_crop_right"):
            n=p.get(v)
            if type(n) is not int or not 0<=n<=1920:
                fail("NUMERO")
        if p["top"]+p["bottom"]>=1920 or p["button_right_width"]>400:
            fail("FAIXA_INVALIDA")
        if p["side_crop_left"]>200 or p["side_crop_right"]>200:
            fail("CORTE_INVALIDO")
        keys.append(p.get("id"))
    if len(set(keys))!=5 or len(keys)!=len(set(keys)):
        fail("ID")
    return records

def _zones(profile):
    p=profile
    # A UI é estritamente um overlay de *simulação*, não valida o player.
    rects=[
      (0,0,1080,p["top"]),
      (0,1920-p["bottom"],1080,1920),
      (1080-p["button_right_width"],p["button_start_y"],1080,1920),
    ]
    if p["side_crop_left"]:
        rects.append((0,0,p["side_crop_left"],1920))
    if p["side_crop_right"]:
        rects.append((1080-p["side_crop_right"],0,1080,1920))
    return [(int(x/2),int(y/2),int(xx/2),int(yy/2)) for x,y,xx,yy in rects
            if xx>x and yy>y]

def mask(profile):
    if profile not in _profiles():
        fail("PERFIL_INVALIDO")
    canvas=Image.new("L",(W,H),0)
    d=ImageDraw.Draw(canvas)
    for x,y,x2,y2 in _zones(profile):
        d.rectangle((x,y,x2-1,y2-1),fill=255)
    return canvas

def _text_layer(root,name,scene,layout):
    clone=copy.deepcopy(root)
    if layout=="hero_lateral_f13":
        target=LABELS[name]
        matches=[(parent,node) for parent in clone.iter() for node in list(parent)
                 if node.get("id")==target]
    elif layout=="hero_elevado_f12":
        desired={"title":scene["title"],
                 "phase":next((p["title"] for p in scene["phases"]
                               if p["start"]<=root._time < p["end"]),None),
                 "detail":next((p["detail"] for p in scene["phases"]
                                if p["start"]<=root._time < p["end"]),None)}
        matches=[(clone,node) for node in list(clone)
                 if node.tag.endswith("}text") and node.text==desired[name]]
    else: fail("LAYOUT_INVALIDO")
    if len(matches)!=1:
        fail("TEXTO_AUSENTE:"+name)
    parent,child=matches[0]
    parent.remove(child)
    return ET.tostring(clone,encoding="unicode")

def _remove(root,layout,scene,role,time,typ):
    if typ=="role":
        return Q._no_role(root,role)
    clone=copy.deepcopy(root)
    if layout=="hero_lateral_f13":
        label=LABELS[role]
        found=[(parent,child) for parent in clone.iter() for child in list(parent)
               if child.get("id")==label]
    elif layout=="hero_elevado_f12":
        i=0 if time<scene["duration_s"]/2 else 1
        phase=scene["phases"][i]
        target={"title":scene["title"],"phase":phase["title"],
                "detail":phase["detail"]}[role]
        found=[(clone,child) for child in list(clone)
               if child.tag=="{http://www.w3.org/2000/svg}text" and
                   child.text==target]
    else: fail("LAYOUT_INVALIDO")
    if len(found)!=1:
        fail("TEXTO_NAO_ENCONTRADO:"+role)
    found[0][0].remove(found[0][1])
    return ET.tostring(clone,encoding="unicode")

def _measure(image,mask_image,p):
    count=Q._count(mask_image)
    if count<5:
        fail("ITEM_INVISIVEL")
    zone=ImageChops.multiply(mask_image,mask(p))
    return round(Q._count(zone)/count,4)

def avaliar(scene,t,layout,profiles=None):
    profiles=profiles or _profiles()
    xml=M.frame_svg(scene,t,transmissao_animada=True,
                    enquadramento_mobile=layout)
    root=Q._root(xml)
    base=Q._raster(xml)
    parts={}
    for group,ident in (("roles",role) for role in ROLE_IDS):
        removed=_remove(root,layout,scene,ident,t,"role")
        pic=Q._threshold_difference(base,Q._raster(removed))
        parts[ident]={"bbox":list(pic.getbbox()),"pixels":Q._count(pic),
                      "ui_risks":{p["id"]:_measure(base,pic,p) for p in profiles}}
    text={}
    for key in LABELS:
        removed=_remove(root,layout,scene,key,t,"text")
        pic=Q._threshold_difference(base,Q._raster(removed))
        text[key]={"bbox":list(pic.getbbox()),"pixels":Q._count(pic),
                   "ui_risks":{p["id"]:_measure(base,pic,p) for p in profiles}}
    return {"roles":parts,"essential_text":text}

def _font(size=16):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",size)

def contact(scene,output):
    base=Q._raster(M.frame_svg(scene,3.6,transmissao_animada=True,
                              enquadramento_mobile="hero_lateral_f13")).convert("RGBA")
    profiles=_profiles()
    board=Image.new("RGB",((len(profiles)+1)*270,510),"#eaf3f6")
    dr=ImageDraw.Draw(board)
    for n,profile in enumerate([None]+profiles):
        if profile is None:
            pic=base.copy()
            title="SEM UI"
        else:
            pic=base.copy()
            overlay=Image.new("RGBA",(W,H),(0,0,0,0))
            draw=ImageDraw.Draw(overlay)
            for rect in _zones(profile):
                draw.rectangle((rect[0],rect[1],rect[2]-1,rect[3]-1),
                               fill=(226,55,52,70),outline=(224,63,46,145),width=2)
            pic=Image.alpha_composite(pic,overlay)
            title=profile["id"].replace("_organic_"," ").replace("_"," ")[:32]
        board.paste(pic.convert("RGB").resize((270,480)),(n*270,30))
        dr.text((n*270+5,6),title,fill="#173d51",font=_font(10))
    board.save(output,quality=91)

def analisar(scene,path):
    M.validar(scene)
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    profiles=_profiles()
    report={
      "schema":"coringa-f13-ui-observed-vs-ad-v1",
      "profile_provenance":[{k:p[k] for k in ("id","placement","tier","source","date_measured")}
                            for p in profiles],
      "screenshot_user_device":False,"sources_are_third_party_estimates":True,
      "meta_ads_guidance_not_organic_measures":True,
      "screenshots_reproduced_in_artifact":False,
      "publisher_certification":False,"publish":False,
      "visual_approval":False,"no_auto_shrink":True,
      "scene":scene["id"],
      "samples":{},
    }
    for t in TIMES:
        report["samples"][str(t)]={
          "hero_f12":avaliar(scene,t,"hero_elevado_f12",profiles),
          "organic_f13":avaliar(scene,t,"hero_lateral_f13",profiles)
        }
    contact(scene,path/(scene["id"]+"_F13_FONTES_UI_CONTATO.jpg"))
    (path/(scene["id"]+"_F13_UI_RISCOS.json")).write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("scene",type=Path)
    p.add_argument("out",type=Path)
    args=p.parse_args()
    print(json.dumps(analisar(M.carregar(args.scene),args.out),
                     ensure_ascii=False,indent=2))
