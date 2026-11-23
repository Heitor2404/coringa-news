"""E1 generic 2D pose renderer: body shapes only, no if by mechanism name.

All frames share a camera computed from the full solved trajectory.
A single SVG compositor consumes any correctly solved MechanismSpec. This
is proof of a common renderer, NOT the approved Coringa industrial style.
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
import cairosvg
from PIL import Image
import numpy as np

from src.v4.formatos import solver_restricoes_e1 as S

COLORS=("#437D96","#E4AD4C","#4A9BA0","#A76BA1","#D96F58","#6E8E5B")

def geometry_bounds(spec,frames):
    hits=[]
    for frame in frames:
        for b in spec["bodies"]:
            p=frame["poses"][b["id"]]
            for shape in b["shapes"]:
                if shape["kind"]=="segment":
                    hits.extend([S.world(p,shape["a"]),S.world(p,shape["b"])])
                else:
                    center=S.world(p,shape["center"])
                    r=float(shape["radius"])
                    hits.extend([center+[-r,-r],center+[r,r]])
    allpoints=np.array(hits,dtype=float)
    lo=np.min(allpoints,axis=0); hi=np.max(allpoints,axis=0)
    middle=(lo+hi)/2
    span=np.maximum(hi-lo,1.)
    # 420x430 stage; reserve upper and lower UI areas.
    scale=float(min(420/(span[0]+.5),425/(span[1]+.5)))
    return {"center":[float(n) for n in middle],
            "scale_px_per_m":scale,"span_m":[float(x) for x in span],
            "world_fixed_for_all_frames":True}

def svg_frame(spec,frame,camera,*,title="CORINGA · PROVA E1"):
    S.validate(spec)
    if not frame["poses"] or not camera["world_fixed_for_all_frames"]:
        raise ValueError("E1-RENDER-ESTADO")
    cx,cy=camera["center"];scale=camera["scale_px_per_m"]
    if not 20<scale<1000:raise ValueError("E1-RENDER-CAMERA")
    shapes=[]
    for idx,b in enumerate(spec["bodies"]):
        x,y,ang=frame["poses"][b["id"]]
        parts=[]
        color=COLORS[idx%len(COLORS)]
        for shape in b["shapes"]:
            if shape["kind"]=="segment":
                ax,ay=shape["a"];bx,by=shape["b"]
                parts.append(f'<line x1="{ax:.7g}" y1="{ay:.7g}" x2="{bx:.7g}" y2="{by:.7g}" '
                   f'stroke="{color}" stroke-width="{shape["thickness"]:.7g}" stroke-linecap="round"/>')
            else:
                u,v=shape["center"]
                parts.append(f'<circle cx="{u:.7g}" cy="{v:.7g}" r="{shape["radius"]:.7g}" '
                    f'fill="{color}" stroke="#153347" stroke-width=".015"/>')
        shapes.append(f'<g id="body-{b["id"]}" data-pose-x="{x:.9f}" data-pose-y="{y:.9f}" '
           f'data-pose-angle="{ang:.9f}" transform="translate({x:.10f} {y:.10f}) rotate({math.degrees(ang):.10f})">'
           +''.join(parts)+'</g>')
    pins=[]
    for j in spec["joints"]:
        if j["kind"]!="pin":continue
        pose=frame["poses"][j["a"]]
        u,v=S.world(pose,j["pa"])
        pins.append(f'<circle cx="{u:.7g}" cy="{v:.7g}" r=".045" '
                    'fill="#FCE8B0" stroke="#263E4A" stroke-width=".013"/>')
    fraction=frame["t"]/spec["duration_s"]
    title=escape(title[:55])
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="540" height="960" viewBox="0 0 540 960"
                 data-layout="E1_SHARED_RENDERER_PRIVATE">
    <rect width="540" height="960" fill="#E8F3F7"/>
    <rect width="540" height="99" fill="#113448"/>
    <rect x="25" y="15" width="140" height="23" rx="5" fill="#FFD16A"/>
    <text x="34" y="31" fill="#17394D" font-family="DejaVu Sans" font-size="10" font-weight="900">CORINGA · LAB</text>
    <text x="25" y="74" fill="white" font-family="DejaVu Sans" font-size="19" font-weight="900">{title}</text>
    <rect x="0" y="99" width="540" height="8" fill="#B0CAD5"/>
    <rect x="0" y="99" width="{540*fraction:.3f}" height="8" fill="#E0A44F"/>
    <rect x="18" y="210" width="504" height="570" rx="22" fill="#D8E9F0" stroke="#A3BEC9" stroke-width="3"/>
    <g id="generic-machine-stage"
       transform="translate(270 505) scale({scale:.10f} {-scale:.10f}) translate({-cx:.10f} {-cy:.10f})">
       {''.join(shapes)}{''.join(pins)}
    </g>
    <text x="27" y="818" fill="#31536B" font-family="DejaVu Sans" font-size="13">CORPOS + JUNTAS · SOLVER COMUM · UNIDADES EM METROS</text>
    <text x="27" y="846" fill="#4A6B7D" font-family="DejaVu Sans" font-size="12">RESÍDUO MÁXIMO: {frame["max_residual_m"]:.2e} m</text>
    <text x="27" y="921" fill="#4A6B7D" font-family="DejaVu Sans" font-size="12">LAB E1 — NÃO PUBLICAR · ESTÉTICA NÃO HOMOLOGADA</text>
    </svg>'''
    return svg

def render(spec,out,*,fps=18,title="MECANISMO EXPERIMENTAL"):
    S.validate(spec)
    if fps!=18:raise ValueError("E1-RENDER-FPS")
    frames=S.trajectory(spec,int(spec["duration_s"]*fps)+1)
    camera=geometry_bounds(spec,frames)
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-video_size","540x960",
         "-r",str(fps),"-i","-","-c:v","libx264","-preset","veryfast",
         "-crf","24","-pix_fmt","yuv420p","-movflags","+faststart",str(out)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in frames[:-1]:
            pic=cairosvg.svg2png(bytestring=svg_frame(spec,frame,camera,title=title).encode("utf8"))
            with Image.open(io.BytesIO(pic)) as im:
                p.stdin.write(im.convert("RGB").tobytes())
    finally:
        p.stdin.close()
    if p.wait()!=0 or not out.is_file() or out.stat().st_size<10000:
        raise ValueError("E1-RENDER-MP4")
    record={
      "schema":"coringa-generic-render-e1-v0","solver":"shared_joint_residuals",
      "renderer":"single_shared_svg_compositor",
      "units":"m","camera_fixed":True,"geometry_family_specific_in_renderer":False,
      "duration_s":spec["duration_s"],"fps":fps,"resolution":[540,960],
      "max_residual_m":max(f["max_residual_m"] for f in frames),
      "source_generated":False,"human_specification_required":True,
      "visual_approved":False,"publish":False,
      "sha256":hashlib.sha256(out.read_bytes()).hexdigest()
    }
    out.with_suffix(".json").write_text(json.dumps(record,indent=2),encoding="utf8")
    return record

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("spec",type=Path);ap.add_argument("out",type=Path)
    ap.add_argument("--title",default="MECANISMO DO LAB")
    args=ap.parse_args()
    spec=json.loads(args.spec.read_text("utf8"))
    print(json.dumps(render(spec,args.out,title=args.title),ensure_ascii=False))

if __name__=="__main__":main()
