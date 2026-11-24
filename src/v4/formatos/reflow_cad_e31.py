"""Private visual reflow from actual decoded E27 stage pixels.

The all-frame motion-difference mask is a proxy, not a semantic CAD body
mask or a universal guarantee about app UI. Static context may extend past
the narrow action strip but not beyond the scene viewport. Text is never
placed there. No publication approval.
"""
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np
from .ponte_cad_editorial_e28 import ffmpeg,sha,fail

W,H=1080,1920
SW,SH=270,480
VIEW=[50,400,1030,1092]
VIEW_E46=[50,400,1030,962]
LEGACY_SCALE=min(620/908,600/942)


def masks(frames):
    if frames.ndim!=4 or frames.shape[1:]!=(SH,SW,3) or len(frames)<2:
        fail("E31-FRAMES")
    fr=frames.astype(np.int16)
    y,x=np.mgrid[0:SH,0:SW]
    t=np.linspace(0,1,SH)[:,None,None]
    g=np.array([16,27,38])*(1-t)+np.array([6,11,16])*t
    bg=g*(1.12-.5*np.hypot((x-SW/2)/SW,(y-SH*.42)/SH)[...,None])
    motion=(np.abs(fr-fr[0]).max(-1)>20).any(0)
    # Positive foreground above known background; union includes temporal
    # differences too. A dark stationary object may be missed: QA limitation.
    fg=(np.max(fr-bg,axis=-1)>13).any(0)|motion
    if motion.sum()<20 or fg.sum()<20:
        fail("E31-SEM_MOVIMENTO")
    return fg,motion


def limites(fg,motion,s,ty,view=VIEW):
    yy,xx=np.nonzero(fg)
    fx0,fx1=4*xx.min()-4,4*(xx.max()+1)+4
    fy0,fy1=4*yy.min()-4,4*(yy.max()+1)+4
    yy,xx=np.nonzero(motion)
    mx,my=4*xx,4*yy
    if s*fy0+ty<view[1]-1e-7 or s*fy1+ty>view[3]+1e-7:
        return None
    my0=s*my+ty-8
    my1=s*(my+4)+ty+8
    if my0.min()<view[1] or my1.max()>view[3]:
        return None
    # Union of platform bands: wider above y840, conservative narrower
    # band below. Pixel cells crossing boundary obey the narrower band.
    lower=my1>=840
    lefts=np.where(lower,150,120)
    rights=np.where(lower,770,960)
    lo=max(view[0]-s*fx0,float(np.max(lefts-s*mx+8)))
    hi=min(view[2]-s*fx1,float(np.min(rights-s*(mx+4)-8)))
    if lo>hi:
        return None
    return lo,hi,(fx0,fy0,fx1,fy1)


def planejar(fg,motion,view=VIEW):
    if fg.shape!=(SH,SW) or motion.shape!=(SH,SW) or not fg.any() or not motion.any():
        fail("E31-MASCARAS")
    yy,xx=np.nonzero(fg)
    fy0=4*yy.min()-4
    best=None
    for scale in range(160,34,-1):
        s=scale/100
        for top in range(400,551,5):
            ty=top-s*fy0
            r=limites(fg,motion,s,ty,view)
            if r is None:
                continue
            lo,hi,b=r
            tx=float(np.clip(500-s*(b[0]+b[2])/2,lo,hi))
            best=(s,tx,float(ty),b)
            break
        if best:
            break
    if not best:
        fail("E31-SEM_ENQUADRAMENTO")
    s,tx,ty,b=best
    return dict(schema="coringa.cad.reflow.private.v1",scale=s,tx=tx,ty=ty,
                viewport=list(view),mask_resolution=[SW,SH],mask_method="all_frames_rgb_difference",
                motion_pixels=int(motion.sum()),foreground_pixels=int(fg.sum()),
                foreground_bbox=[int(x) for x in b],
                scale_legacy=LEGACY_SCALE,scale_ratio=s/LEGACY_SCALE,
                status="EXPERIMENTAL_PIXEL_PROXY",publish=False)


def preparar(props_path,public_root,qa_path,painel=False):
    props_path=Path(props_path)
    p=json.loads(props_path.read_text())
    if p.get("preview") is not True or p.get("private_review_only") is not True or p.get("subtitle_mode"):
        fail("E31-PRIVADO_SEM_LEGENDA")
    if len(p.get("shots",[]))!=1 or p["shots"][0].get("type")!="cad_preview":
        fail("E31-CENA")
    shot=p["shots"][0]
    root=Path(public_root).resolve()
    clip=(root/shot["asset"]).resolve()
    if not clip.is_relative_to(root) or not clip.is_file() or clip.stem!=sha(clip):
        fail("E31-HASH")
    raw=subprocess.check_output([ffmpeg(),"-v","error","-i",str(clip),"-vf","scale=270:480",
                                  "-f","rawvideo","-pix_fmt","rgb24","-"])
    fr=np.frombuffer(raw,np.uint8).reshape(-1,SH,SW,3)
    if len(fr)!=round(p["duracao"]*30):
        fail("E31-RELOGIO")
    fg,motion=masks(fr)
    if painel and not shot.get("cad_transmissao"):
        fail("E46-SEM_TRANSMISSAO")
    r=planejar(fg,motion,VIEW_E46 if painel else VIEW)
    shot["cad_reflow"]=r
    # Existing safe-area certificate does not cover this experimental variant.
    p.pop("safe_area_profile",None)
    props_path.write_text(json.dumps(p,ensure_ascii=False,indent=2))
    Path(qa_path).write_text(json.dumps(r,ensure_ascii=False,indent=2))
    return r


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("props")
    p.add_argument("public")
    p.add_argument("qa")
    p.add_argument("--painel-e46",action="store_true")
    a=p.parse_args()
    print(json.dumps(preparar(a.props,a.public,a.qa,a.painel_e46),ensure_ascii=False))
