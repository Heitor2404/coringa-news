"""Private preview of closed-loop CAD; one fixed camera for the entire trajectory."""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .cad_fechado_e17 import load, solver, audit
from .render_cad_e15 import raster, unit


def ffmpeg_exe():
    if os.environ.get('FFMPEG'):
        return os.environ['FFMPEG']
    return shutil.which('ffmpeg') or 'ffmpeg'


def project(solids, plane, origins, frames):
    normal = np.cross(*plane)
    # Oblique view from the side of the moving links; roll uses the portrait frame.
    eye = unit(-normal + .28*plane[1] + .16*plane[0])
    right = unit(plane[0] - eye*(plane[0]@eye))
    down = unit(np.cross(eye,right))
    if down@plane[1] > 0:
        down = -down
    roll = math.radians(42)
    view = np.stack([right*math.cos(roll)+down*math.sin(roll),
                     down*math.cos(roll)-right*math.sin(roll),eye],axis=1)
    parts = {}
    for name,solid in solids.items():
        verts, indices = solid.tessellate(.08,.22)
        vertex = np.array([v.toTuple() for v in verts])
        parts[name] = (vertex @ plane.T-origins[name], vertex @ normal, np.array(indices))
    series, bounds = [], []
    for f in frames:
        result = {}
        for n,(xy,z,idx) in parts.items():
            x,y,angle = f["poses"][n]
            c,s = math.cos(angle),math.sin(angle)
            posed = xy @ np.array([[c,s],[-s,c]]) + [1000*x,1000*y]
            points = (posed @ plane + z[:,None]*normal) @ view
            bounds.extend([points.min(axis=0),points.max(axis=0)])
            result[n] = points[idx]
        series.append(result)
    low,high = np.min(bounds,axis=0),np.max(bounds,axis=0)
    scale = min(418/(high[0]-low[0]),405/(high[1]-low[1]))
    return series, (low+high)/2, scale


def render(manifest,solids,plane,origins,frames,out):
    series,center,scale = project(solids,plane,origins,frames)
    target = out/"volta_completa.mp4"
    source_color = manifest["palette"]
    fonts = [ImageFont.truetype("DejaVuSans.ttf",n) for n in (17,21,32)]
    direction = plane @ manifest["guide_direction"]
    positions = np.array([np.dot(f["poses"][manifest["measurement_body"]][:2],direction)
                          for f in frames])*1000
    positions -= positions.min()
    chart = [(48+int(i*396/(len(frames)-1)),int(754-v*60/positions.max())) for i,v in enumerate(positions)]
    cmd = [ffmpeg_exe(),"-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s","540x960",
           "-r","24","-i","-","-c:v","libx264","-threads","2","-crf","17","-pix_fmt","yuv420p",
           "-metadata","comment=CAD: Xem Studio; adaptation: motion study and editorial colors. "+manifest["source"],
           str(target)]
    ground = manifest["ground"]
    base = None
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as enc:
        for i,parts in enumerate(series):
            rgb = np.full((960,540,3),[17,31,44],dtype=np.uint8)
            depth = np.full((960,540),-np.inf)
            for name,tri in parts.items():
                if name == ground and base is not None:
                    low,z,pixels = base
                else:
                    low,z,pixels = raster((tri-center)*scale+[255,382,0], np.array(source_color[name]))
                    if name == ground:
                        base = low,z,pixels
                x,y = low
                h,w = z.shape
                tile = depth[y:y+h,x:x+w]
                front = z>tile
                tile[front] = z[front]
                rgb[y:y+h,x:x+w][front] = pixels[front]
            im = Image.fromarray(rgb)
            pen = ImageDraw.Draw(im)
            pen.text((48,104),manifest["title"],font=fonts[2],fill="white")
            pen.text((48,152),"Do giro ao movimento em linha reta",font=fonts[1],fill="#ffcc62")
            for x,(name,label) in zip((48,212,323),manifest["legend"].items()):
                swatch = tuple((np.sqrt(source_color[name])*225).astype(int))
                pen.ellipse((x,601,x+10,611),fill=swatch)
                pen.text((x+17,594),label,font=fonts[0],fill="#bed0db")
            pen.text((48,635),"Posição do cursor",font=fonts[1],fill="white")
            pen.text((310,635),f"{positions[i]:.1f} mm".replace(".",","),font=fonts[1],fill="#ffcc62")
            pen.line(chart,fill="#4c6271",width=2)
            if i:
                pen.line(chart[:i+1],fill="#ffcc62",width=3)
            u,v = chart[i]
            pen.ellipse((u-4,v-4,u+4,v+4),fill="white")
            pen.text((48,760),"0°",font=fonts[0],fill="#b3c3cf")
            pen.text((405,760),"360°",font=fonts[0],fill="#b3c3cf")
            pen.text((48,810),"CAD · "+manifest["credit"],font=fonts[0],fill="#b3c3cf")
            enc.stdin.write(im.tobytes())
        enc.stdin.close()
        if enc.wait():
            raise RuntimeError("encoding failed")
    return target


def check_video(path):
    if shutil.which("ffprobe"):
        streams = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-of","json",str(path)]))["streams"]
        stream, = streams
        if (stream["width"],stream["height"],stream["r_frame_rate"]) != (540,960,"24/1"):
            raise ValueError("unexpected media format")
    else:
        # Wheel estático imageio-ffmpeg não traz ffprobe. Preservar as
        # verificações de codec, stream único, dimensão e fps sem apt.
        info = subprocess.run([ffmpeg_exe(),"-hide_banner","-i",str(path)],
                              capture_output=True,text=True).stderr
        streams = re.findall(r"Stream #\d+:\d+.*?: (Video|Audio|Data|Subtitle): (.*)",info)
        if (len(streams)!=1 or streams[0][0]!="Video"
                or not streams[0][1].startswith("h264")
                or not re.search(r"\b540x960\b",streams[0][1])
                or not re.search(r"\b24(?:\.0+)? fps\b",streams[0][1])):
            raise ValueError("unexpected media format (ffmpeg metadata)")
    data = subprocess.check_output([ffmpeg_exe(),"-v","error","-i",str(path),"-vf","scale=270:480",
                                    "-f","rawvideo","-pix_fmt","rgb24","-"])
    frames = np.frombuffer(data,np.uint8).reshape(-1,480,270,3)
    roi = frames[:,95:310].astype(np.int16)
    change = (np.abs(roi-roi[0]).max(axis=-1)>18).sum(axis=(1,2))
    if len(frames)!=97 or change.max()<500 or change[-1]>.04*change.max():
        raise ValueError("encoded cycle or visible motion failed")
    Image.fromarray(np.concatenate(frames[[0,24,48,72,96]],axis=1)).save(path.with_suffix(".jpg"))
    return dict(decoded_frames=len(frames),peak_changed_pixels=int(change.max()),return_changed_pixels=int(change[-1]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for arg in ("manifest","step","license","output"):
        parser.add_argument(arg,type=Path)
    args = parser.parse_args()
    m = json.loads(args.manifest.read_text())
    solids,plane,origins,pins,spec = load(m,args.step,args.license)
    frames = solver.trajectory(spec,97,cad_bodies=solids)
    report = audit(m,solids,plane,origins,pins,frames)
    args.output.mkdir(exist_ok=True,parents=True)
    movie = render(m,solids,plane,origins,frames,args.output)
    report.update(check_video(movie), source=m["source"],license=m["license_name"], bindings=list(solids),
                  sha256=hashlib.sha256(movie.read_bytes()).hexdigest(),publish=False)
    (args.output/"QA.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
