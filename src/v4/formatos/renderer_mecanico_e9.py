"""E9 experimental shared industrial-*illustration* renderer.

Renders source-grounded kinematic locations as layered machined-link symbols.
It does NOT recover original CAD bodies, manufacture contours, mass or material.
All pieces in all machines use identical geometry-derived rules; no dispatch
by mechanism title, body ID or upstream example. E1 remains the solver.
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
from xml.sax.saxutils import escape

import cairosvg
from PIL import Image

from src.v4.formatos import solver_restricoes_e1 as S
from src.v4.formatos import renderer_corpos_e1 as R

SVG_CLOSING="</g>"
BODY_PATTERN=re.compile(r'(<g id="body-([a-z][a-z0-9_]{0,39})"[^>]*>)(.*?)(</g>)',
                        re.DOTALL)
STEEL_COLORS=("#538DA2","#D3A757","#6393A5","#B092BA","#C68069","#8EAAA3")
SCHEMA="coringa-e9-source-anchored-illustration-v1"

def err(code):
    raise ValueError("E9-VISUAL-"+code)

def _num(n):
    if type(n) not in (float,int) or not math.isfinite(n):
        err("NAN")
    return f"{n:.7f}"

def _line(a,b,width,color,**other):
    stroke=" ".join(f'{k.replace("_","-")}="{escape(str(v))}"'
                    for k,v in other.items())
    return (f'<line x1="{_num(a[0])}" y1="{_num(a[1])}" '
            f'x2="{_num(b[0])}" y2="{_num(b[1])}" '
            f'stroke="{color}" stroke-width="{_num(width)}" '
            f'stroke-linecap="round" {stroke}/>')

def _circle(pos,radius,fill,stroke="#1A2A35",sw=1):
    return (f'<circle cx="{_num(pos[0])}" cy="{_num(pos[1])}" '
            f'r="{_num(radius)}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{_num(sw)}"/>')

def _body_markup(body,scale,idx):
    parts=[]
    color=STEEL_COLORS[idx%len(STEEL_COLORS)]
    # Source segments are the centerlines of movable rigid parts. Width is
    # illustrative, screen-space bounded, and not industrial CAD evidence.
    for sh in body["shapes"]:
        kind=sh["kind"]
        if kind in ("segment","slotted_link"):
            a=sh["a"];b=sh["b"]
            length=math.dist(a,b)
            if length<1e-8:err("DEGENERATE_BODY_SHAPE")
            width_px=min(26.,max(13.5,11.+.11*length*scale))
            if kind=="slotted_link":width_px=max(24.,width_px)
            w=width_px/scale
            parts.append(_line(a,b,w+4.2/scale,"#07121D"))
            parts.append(_line(a,b,w,color))
            parts.append(_line(a,b,w*.50,"#8FB8C1",opacity=".28"))
            # Use the same machining language on all rigid members.
            if kind=="slotted_link":
                parts.append(_line(a,b,w*.38,"#0C202D"))
                parts.append(_line(a,b,w*.20,"#B4CBD0",opacity=".35"))
            else:
                parts.append(_line(a,b,1.8/scale,"#D3ECF1",opacity=".68"))
            # End caps / bored-link ends follow source segment endpoints.
            if kind=="segment":
                for p in (a,b):
                    parts.append(_circle(p,w*.48,color,stroke="#163040",sw=2.1/scale))
                    parts.append(_circle(p,w*.23,"#203C4A",stroke="#B6D6DD",
                                         sw=1.4/scale))
            continue
        if kind=="disc":
            p=sh["center"];rad=float(sh["radius"])
            parts.append(_circle(p,rad,"#1E4050",stroke="#8DB3C5",sw=3.2/scale))
            parts.append(_circle(p,rad*.82,color,stroke="#0D2535",sw=1.4/scale))
            parts.append(_circle(p,rad*.18,"#0D2535",stroke="#D1E3E7",sw=1.6/scale))
            continue
        if kind=="gear":
            # The solver's reusable generic gear primitive is retained.
            # A pitch circle is visualization, not an industrial tooth profile.
            p=sh["center"];rad=float(sh["pitch_radius_m"])
            parts.append(_circle(p,rad,"#356076",stroke="#C0D7DE",sw=2.3/scale))
            parts.append(_circle(p,rad*.82,color,stroke="#183647",sw=2.3/scale))
            parts.append(_circle(p,rad*.21,"#0D2332",stroke="#D8EBEC",sw=2.3/scale))
            for index in range(0,sh["teeth"],max(1,sh["teeth"]//18)):
                angle=2*math.pi*index/sh["teeth"]
                start=[p[0]+rad*.85*math.cos(angle),
                       p[1]+rad*.85*math.sin(angle)]
                end=[p[0]+(rad+sh["tooth_height_m"])*math.cos(angle),
                     p[1]+(rad+sh["tooth_height_m"])*math.sin(angle)]
                parts.append(_line(start,end,4.5/scale,"#A9CBD8"))
            continue
        if kind=="rack":
            a=sh["a"];b=sh["b"];width=max(13/scale,sh["thickness"])
            parts.extend([_line(a,b,width+3/scale,"#152635"),
                          _line(a,b,width,color),
                          _line(a,b,2/scale,"#D6E8EC",opacity=".6")])
            continue
        err("UNSUPPORTED_VISUAL_SHAPE")
    return '<g class="e9-machine-body" data-source-geometry="centerlines-only">' + "".join(parts) + "</g>"

def _guide_markup(spec,frames,scale):
    """Show an actual ground slot as a guide *axis* over observed travel.
    Guide length is from solved poses; there is NO claim of physical end stops.
    """
    pieces=[]
    ground=spec["ground"]["id"]
    for joint in spec["joints"]:
        if joint["kind"]!="slot" or joint["b"]!=ground:
            continue
        gp=spec["ground"]["pose"]
        origin=S.world(gp,joint["pb"])
        axis=S.rotate(joint["axis_b"],gp[2])
        coords=[]
        for frame in frames:
            point=S.world(frame["poses"][joint["a"]],joint["pa"])
            offset=point-origin
            lateral=float(abs(axis[0]*offset[1]-axis[1]*offset[0]))
            if lateral>1e-5:err("GUIDE_AXIS_DISAGREEMENT")
            coords.append(float(axis@offset))
        margin=25/scale
        p=origin+axis*(min(coords)-margin)
        q=origin+axis*(max(coords)+margin)
        if math.dist(p,q)<25/scale:
            p=origin-axis*(25/scale);q=origin+axis*(25/scale)
        pieces.append(_line(p,q,41/scale,"#091C2A"))
        pieces.append(_line(p,q,33/scale,"#56798C"))
        pieces.append(_line(p,q,24/scale,"#0D2A3B"))
        pieces.append(_line(p,q,2.4/scale,"#A1C0C9",opacity=".6"))
    return '<g id="e9-source-ground-guides">'+"".join(pieces)+"</g>"

def _joints_markup(spec,frame,scale):
    pieces=[]
    ground=spec["ground"]["id"]
    for j in spec["joints"]:
        if j["kind"] not in ("pin","slot"):continue
        p=S.world((spec["ground"]["pose"] if j["a"]==ground
                  else frame["poses"][j["a"]]),j["pa"])
        if j["kind"]=="pin" and (j["a"]==ground or j["b"]==ground):
            # Symbolic floor-mounted bearing. Inferred *drawing convention*,
            # not a source-validated housing or part dimension.
            base=(p[0],p[1]-18/scale)
            pieces.append(_line([base[0]-21/scale,base[1]],
                                [base[0]+21/scale,base[1]],
                                5/scale,"#6D99AA"))
            pieces.append(_line(base,p,15/scale,"#294B5B"))
        size=(13 if j["kind"]=="pin" else 11)/scale
        if j["kind"]=="slot":
            pieces.append(_circle(p,size*1.42,"none",stroke="#FFD16A",sw=2.4/scale))
        pieces.append(_circle(p,size,"#294B5B",stroke="#E0EFF0",sw=2.2/scale))
        pieces.append(_circle(p,size*.57,"#D9E7E5",stroke="#648E9D",sw=1.4/scale))
        pieces.append(_circle(p,size*.18,"#15374A",stroke="#15374A",sw=1/scale))
    return '<g id="e9-pivots-source-anchored">'+"".join(pieces)+"</g>"

def _driver_marker(spec,frame,scale):
    """Mark rotating input visually without inventing the machine output."""
    body=spec["driver"]["body"]; ground=spec["ground"]["id"]
    origin=None
    for j in spec["joints"]:
        if j["kind"]!="pin":continue
        if (j["a"]==body and j["b"]==ground):
            origin=S.world(frame["poses"][body],j["pa"]);break
        if (j["b"]==body and j["a"]==ground):
            origin=S.world(spec["ground"]["pose"],j["pa"]);break
    if origin is None:return ""
    radius=37/scale
    angle=frame["poses"][body][2]
    a=angle-.62; b=angle+.35
    p=(origin[0]+radius*math.cos(a),origin[1]+radius*math.sin(a))
    q=(origin[0]+radius*math.cos(b),origin[1]+radius*math.sin(b))
    # These arcs are a *driver cue*, not evidence of torque/force.
    arrow=(q[0]+9/scale*math.cos(b+2.7),
           q[1]+9/scale*math.sin(b+2.7))
    return ('<g id="e9-input-marker" opacity=".90">'
            f'<path d="M {_num(p[0])} {_num(p[1])} '
            f'A {_num(radius)} {_num(radius)} 0 0 1 {_num(q[0])} {_num(q[1])}" '
            f'fill="none" stroke="#FFE0A1" stroke-width="{_num(2.7/scale)}"/>'
            +_line(q,arrow,2.7/scale,"#FFE0A1")+"</g>")

def _stage_backdrop(svg):
    # No source-dependent image generated; the grid is a stable graphic device.
    grid=[]
    for x in range(40,520,40):
        grid.append(f'<line x1="{x}" y1="154" x2="{x}" y2="766" '
                    'stroke="#416274" stroke-opacity=".14" stroke-width="1"/>')
    for y in range(174,767,40):
        grid.append(f'<line x1="15" y1="{y}" x2="525" y2="{y}" '
                    'stroke="#416274" stroke-opacity=".14" stroke-width="1"/>')
    grid.append('<rect x="32" y="171" width="159" height="26" rx="5" '
                'fill="#163A4D" stroke="#5E8DA0" stroke-opacity=".55"/>')
    grid.append('<text x="43" y="188" font-family="DejaVu Sans" '
                'font-size="10" font-weight="bold" fill="#E2ECEE">'
                'MECANISMO · 2D</text>')
    grid.append('<text x="33" y="743" font-family="DejaVu Sans" '
                'font-size="10" fill="#A9C1CC">GEOMETRIA E MOVIMENTO VERIFICADOS</text>')
    old='<g id="generic-machine-stage"'
    if old not in svg:err("SVG_SHARED_STAGE_MISSING")
    svg=svg.replace(old,'<g id="e9-industrial-grid">'+"".join(grid)+"</g>"+old,1)
    swaps=[
       ('fill="#E8F3F7"','fill="#061927"'),
       ('fill="#113448"','fill="#0B2737"'),
       ('fill="#D8E9F0" stroke="#A3BEC9"','fill="#0C293B" stroke="#48697D"'),
       ('fill="#31536B"','fill="#C6D9DF"'),
       ('fill="#4A6B7D"','fill="#95B1C0"'),
       ('CORPOS + JUNTAS · SOLVER COMUM · UNIDADES EM METROS',
        'PEÇAS ILUSTRATIVAS · MOVIMENTO DO SOLVER · METROS'),
       ('LAB E1/E2 — NÃO PUBLICAR · ESTÉTICA NÃO HOMOLOGADA',
        'LAB E9 — MODELO ILUSTRATIVO · NÃO PUBLICAR'),
    ]
    for before,after in swaps:
        svg=svg.replace(before,after)
    return svg

def svg_frame(spec,frame,camera,frames,*,title="MECANISMO · E9"):
    S.validate(spec)
    if len(frames)<9:err("FRAMES_INSUFICIENTES")
    if not camera["world_fixed_for_all_frames"]:err("CAMERA_NAO_FIXA")
    scale=float(camera["scale_px_per_m"])
    base=R.svg_frame(spec,frame,camera,title=title)
    base=_stage_backdrop(base)
    # Replaces only body GRAPHICS in a shared SVG. Poses, dynamics,
    # geometry projection and camera remain the existing E1 systems.
    used=[]
    by_id={b["id"]:(n,b) for n,b in enumerate(spec["bodies"])}
    def replace_body(match):
        ident=match.group(2)
        if ident not in by_id:err("UNTRACKED_BODY")
        used.append(ident)
        idx,body=by_id[ident]
        return match.group(1)+_body_markup(body,scale,idx)+match.group(4)
    base=BODY_PATTERN.sub(replace_body,base)
    if set(used)!=set(by_id):err("MISSING_BODY")
    # Original small dots are replaced by true sourced-joint bearing symbols.
    pins_match=re.search(r'(<g id="generic-machine-stage"[^>]*>)(.*?)(</g>)',
                         base,re.DOTALL)
    if pins_match is None:err("MISSING_STAGE")
    new_stage=_guide_markup(spec,frames,scale)
    # Guide *behind* the movable structures, never on top of their contacts.
    base=base.replace(pins_match.group(1),pins_match.group(1)+new_stage,1)
    # Hide old light simple pin indicators by locating the tail of stage.
    old_pin_pattern=re.compile(r'(<circle cx="[^"]+" cy="[^"]+" r="[^"]+" '
                               r'fill="(?:#FFE7A6|#F7F3DD)" stroke="#263E4A" '
                               r'stroke-width="[^"]+"/>)+')
    base=old_pin_pattern.sub("",base)
    overlay=_joints_markup(spec,frame,scale)+_driver_marker(spec,frame,scale)
    if "</g>\n    <text x=\"27\" y=\"818\"" not in base:
        err("TAIL_MARKER")
    base=base.replace('</g>\n    <text x="27" y="818"',
        overlay+'</g>\n    <text x="27" y="818"',1)
    if '<script' in base or 'href=' in base:err("UNTRUSTED_ASSET")
    return base

def render(spec,out,*,fps=18,title="GEOMETRIA INDUSTRIAL · PROVA"):
    S.validate(spec)
    if fps!=18:err("FPS")
    frames=S.trajectory(spec,int(spec["duration_s"]*fps)+1)
    camera=R.geometry_bounds(spec,frames)
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-video_size","540x960",
         "-r",str(fps),"-i","-","-c:v","libx264","-preset","veryfast",
         "-crf","22","-pix_fmt","yuv420p","-movflags","+faststart",str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in frames[:-1]:
            svg=svg_frame(spec,frame,camera,frames,title=title)
            pic=cairosvg.svg2png(bytestring=svg.encode("utf8"))
            with Image.open(io.BytesIO(pic)) as im:
                proc.stdin.write(im.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
    if proc.wait()!=0 or not out.is_file() or out.stat().st_size<10000:
        err("MP4")
    meta={
      "schema":SCHEMA,"solver":"shared_joint_residuals",
      "renderer":"single_generic_e9_illustration_renderer",
      "mechanism_specific_shape_templates":False,
      "body_centerlines_from_source":True,
      "joint_locations_from_solver":True,
      "body_housing_dimensions_from_CAD":False,
      "synthetic_machine_appearance":True,
      "camera_fixed":True,
      "duration_s":spec["duration_s"],"fps":fps,"resolution":[540,960],
      "visual_approved":False,"industrial_machine_identity_verified":False,
      "publish":False,"third_party_media_copied":False,
      "sha256":hashlib.sha256(out.read_bytes()).hexdigest()}
    out.with_suffix(".json").write_text(json.dumps(meta,indent=2),encoding="utf8")
    return meta

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("spec",type=Path);ap.add_argument("out",type=Path)
    ap.add_argument("--title",default="LAB MECÂNICO E9")
    args=ap.parse_args()
    spec=json.loads(args.spec.read_text("utf8"))
    print(json.dumps(render(spec,args.out,title=args.title),ensure_ascii=False))
if __name__=="__main__":main()
