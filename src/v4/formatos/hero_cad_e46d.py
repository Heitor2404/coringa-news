"""Private wide hero: fit the entire visible silhouette, not the text box.
UI exposure is measured on motion pixels. Semantic essential masks are optional
and must come from trusted renderer evidence, not guessed from RGB.
"""
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np
from . import reflow_cad_e31 as R

ROOT=Path(__file__).resolve().parents[3]
LAYOUTS=json.loads((ROOT/"motor4/remotion/src/formatos/safe-zones-vertical.json").read_text())
LAYOUT=LAYOUTS["cad_hero_private"]
BALANCED=LAYOUTS["cad_hero_balanced_private"]
VIEW=LAYOUT["viewport"]
BUDGET=LAYOUT["max_motion_ui_fraction"]
PROFILES=json.loads((ROOT/"src/v4/formatos/plataformas.json").read_text())


def pontos(mask):
    y,x=np.nonzero(mask)
    return 4*x+2.,4*y+2.


def riscos(x,y,margin):
    result={}
    for name in PROFILES["ativos_seguros"]:
        p=PROFILES["perfis"][name]
        d=p["direita"]
        r=((x-margin<p["esquerda"]) | (y-margin<p["topo"]) |
           (y+margin>R.H-p["base"]) |
           ((x+margin>R.W-d["largura"]) &
            (y+margin>=d["de_y"]) & (y-margin<=d["ate_y"])))
        result[name]=float(np.mean(r))
    return result


def planejar(fg,motion,essential=None,balanced=False):
    layout=BALANCED if balanced else LAYOUT
    view=layout["viewport"]
    budget=layout["max_motion_ui_fraction"]
    if (fg.shape!=(R.SH,R.SW) or motion.shape!=fg.shape or
        not fg.any() or not motion.any() or np.any(motion & ~fg)):
        R.fail("E46D-MASCARAS")
    if essential is not None and (essential.shape!=fg.shape or
        not essential.any() or np.any(essential & ~fg)):
        R.fail("E46D-ESSENCIAIS")
    x,y=pontos(fg)
    box=np.array([x.min()-6,y.min()-6,x.max()+6,y.max()+6])
    mx,my=pontos(motion)
    ex,ey=pontos(essential) if essential is not None else (None,None)
    x0,y0,x1,y1=view
    max_scale=min(2.4,(x1-x0)/(box[2]-box[0]),(y1-y0)/(box[3]-box[1]))
    best=None
    # At each scale search translations; no crop of measured foreground.
    for i in range(int(max_scale*100),34,-1):
        s=i/100
        lx,hx=x0-s*box[0],x1-s*box[2]
        ly,hy=y0-s*box[1],y1-s*box[3]
        if balanced:
            cy=(box[1]+box[3])/2
            ly=max(ly,layout["center_y_range"][0]-s*cy)
            hy=min(hy,layout["center_y_range"][1]-s*cy)
        if lx>hx or ly>hy:
            continue
        xs=np.unique(np.clip(np.r_[np.linspace(lx,hx,5),500-s*(box[0]+box[2])/2],lx,hx))
        ys=np.unique(np.clip(np.r_[np.linspace(ly,hy,5),950-s*(box[1]+box[3])/2] if balanced else np.r_[np.linspace(ly,hy,5),180-s*box[1],260-s*box[1]],ly,hy))
        for tx in xs:
            for ty in ys:
                risk=riscos(s*mx+tx,s*my+ty,2*s+4)
                worst=max(risk.values())
                if worst>budget:
                    continue
                if essential is not None and max(riscos(s*ex+tx,s*ey+ty,2*s+4).values())>0:
                    continue
                # Prefer lower exposure then centered near x500; scale is primary.
                score=(abs(s*(box[1]+box[3])/2+ty-950),worst,abs(s*(box[0]+box[2])/2+tx-500)) if balanced else (worst,abs(s*(box[0]+box[2])/2+tx-500),s*box[1]+ty)
                if best is None or score<best[0]:
                    best=(score,s,float(tx),float(ty),risk)
        if best is not None:
            break
    if best is None:
        R.fail("E46D-SEM_ENQUADRAMENTO")
    _,s,tx,ty,risk=best
    legacy=R.planejar(fg,motion)
    out=box*s+np.array([tx,ty,tx,ty])
    return dict(schema="coringa.cad.hero.balanced.private.v1" if balanced else "coringa.cad.hero.private.v1",scale=s,tx=tx,ty=ty,
        viewport=view,foreground_bbox=box.tolist(),output_bbox=out.tolist(),
        width_fraction=float((out[2]-out[0])/R.W),
        height_fraction=float((out[3]-out[1])/R.H),
        previous_scale=legacy["scale"],scale_ratio=s/legacy["scale"],
        motion_ui_fraction=risk,motion_ui_budget=budget,center_y=float((out[1]+out[3])/2),
        essential_status="MASK_CHECKED" if essential is not None else "SEM_MASCARA_SEMANTICA",
        status="EXPERIMENTAL_PIXEL_PROXY",publish=False)


def preparar(props_path,public_root,qa_path,balanced=False):
    pth=Path(props_path)
    p=json.loads(pth.read_text())
    if p.get("preview") is not True or p.get("private_review_only") is not True or p.get("subtitle_mode"):
        R.fail("E46D-PRIVADO")
    if len(p.get("shots",[]))!=1 or p["shots"][0].get("type")!="cad_preview":
        R.fail("E46D-CENA")
    shot=p["shots"][0]
    root=Path(public_root).resolve()
    clip=(root/shot["asset"]).resolve()
    if not clip.is_relative_to(root) or not clip.is_file() or clip.stem!=R.sha(clip):
        R.fail("E46D-HASH")
    raw=subprocess.check_output([R.ffmpeg(),"-v","error","-i",str(clip),"-vf","scale=270:480",
        "-f","rawvideo","-pix_fmt","rgb24","-"])
    fr=np.frombuffer(raw,np.uint8).reshape(-1,R.SH,R.SW,3)
    if len(fr)!=round(p["duracao"]*30):
        R.fail("E46D-RELOGIO")
    fg,motion=R.masks(fr)
    report=planejar(fg,motion,balanced=balanced)
    shot["cad_reflow"]=report
    shot["cad_compact_panel"]=bool(shot.get("cad_transmissao"))
    p.pop("safe_area_profile",None)
    pth.write_text(json.dumps(p,ensure_ascii=False,indent=2))
    Path(qa_path).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report

if __name__=="__main__":
    a=argparse.ArgumentParser()
    for k in ("props","public","qa"):
        a.add_argument(k)
    a.add_argument("--balanced",action="store_true")
    v=a.parse_args()
    print(json.dumps(preparar(v.props,v.public,v.qa,v.balanced),ensure_ascii=False))
