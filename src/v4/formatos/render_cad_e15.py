"""Orthographic depth-buffer rendering of rigid translating STL visuals."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .cad_urdf_e15 import checked, load_model

SIZE = (540, 960)
FRAMES = 97
FPS = 24


def unit(a):
    return a / np.linalg.norm(a)


def raster(tris, color):
    """Crop a visual's color/depth tile once, interpolating depth across each face."""
    low = np.floor(tris[:, :, :2].min(axis=(0, 1))).astype(int)
    high = np.ceil(tris[:, :, :2].max(axis=(0, 1))).astype(int)
    w, h = high - low + 1
    depth = np.full((h, w), -np.inf)
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    tris = tris.copy()
    tris[:, :, :2] -= low
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    normals /= np.maximum(1e-14, np.linalg.norm(normals, axis=1, keepdims=True))
    light = unit(np.array([-.4, -.65, .8]))
    shades = (.48 + .52 * np.abs(normals @ light))[:, None] * np.sqrt(color) * 255
    for tri, shade in zip(tris, shades):
        a, b, c = tri
        dx, dy, dz = b - a
        ex, ey, ez = c - a
        det = dx * ey - dy * ex
        if abs(det) < 1e-8:
            continue
        x0, y0 = np.ceil(tri[:, :2].min(axis=0)).astype(int)
        x1, y1 = np.floor(tri[:, :2].max(axis=0)).astype(int)
        if x1 < x0 or y1 < y0:
            continue
        y, x = np.ogrid[y0:y1+1, x0:x1+1]
        u = ((x-a[0])*ey - (y-a[1])*ex) / det
        v = (dx*(y-a[1]) - dy*(x-a[0])) / det
        z = a[2] + u*dz + v*ez
        tile = depth[y0:y1+1, x0:x1+1]
        mask = (u >= -1e-9) & (v >= -1e-9) & (u+v <= 1+1e-9) & (z > tile)
        tile[mask] = z[mask]
        rgb[y0:y1+1, x0:x1+1][mask] = shade
    return low, depth, rgb


def render(root, manifest, file, out):
    model, meshes = load_model(root, manifest, file)
    fractions = (1 - np.cos(np.linspace(0, 2*np.pi, FRAMES))) / 2
    frames = [model.frame(float(t)) for t in fractions]
    base = frames[0][0]
    # World Z is up. The orthographic view shows the rails and the tool face.
    eye = unit(np.array([1., -.38, .31]))
    right = unit(np.cross([0, 0, 1], eye))
    view = np.array([right, -np.cross(eye, right), eye]).T
    projected = []
    bounds = []
    for body, path, points, color in meshes:
        pose = base[body]
        tri = (points @ pose[:3, :3].T + pose[:3, 3]) @ view
        projected.append((body, tri, color))
        delta = (frames[FRAMES//2][0][body][:3, 3]-pose[:3, 3]) @ view
        bounds.extend([tri.min(axis=(0, 1)), tri.max(axis=(0, 1)),
                       tri.min(axis=(0, 1))+delta, tri.max(axis=(0, 1))+delta])
    lo, hi = np.min(bounds, axis=0), np.max(bounds, axis=0)
    scale = min(426/(hi[0]-lo[0]), 550/(hi[1]-lo[1]))
    center = (lo+hi)/2
    layers = [(body, *raster((tri-center)*scale + [255,410,0], color))
              for body, tri, color in projected]
    stem = Path(file).stem
    movie = out/(stem+".mp4")
    cmd = ["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s","540x960",
           "-r",str(FPS),"-i","-","-c:v","libx264","-threads","2","-crf","17","-pix_fmt","yuv420p",
           "-metadata","comment=Adapted visualization of Source Robotics CAD, CC BY 4.0. "
           "https://github.com/Source-Robotics/robot_descriptions https://creativecommons.org/licenses/by/4.0/",
           str(movie)]
    font = lambda n: ImageFont.truetype("DejaVuSans.ttf", n)
    title, caption, credit = font(32), font(22), font(16)
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as encoder:
        for poses, values, _, _ in frames:
            rgb = np.full((SIZE[1], SIZE[0], 3), [17,31,44], dtype=np.uint8)
            depth = np.full(rgb.shape[:2], -np.inf)
            for body, low, z, pixels in layers:
                delta = (poses[body][:3, 3]-base[body][:3, 3]) @ view * scale
                x, y = low + np.rint(delta[:2]).astype(int)
                h, w = z.shape
                region = depth[y:y+h, x:x+w]
                front = z + delta[2] > region
                region[front] = z[front] + delta[2]
                rgb[y:y+h, x:x+w][front] = pixels[front]
            image = Image.fromarray(rgb)
            draw = ImageDraw.Draw(image)
            draw.text((48,102),stem.replace("_solid","").upper(),font=title,fill="white")
            travel = abs(values[model.driver]-frames[0][1][model.driver])*1000
            draw.text((48,712),f"Curso de uma mandíbula   {travel:.1f} mm".replace(".",","),font=caption,fill="#f4cf63")
            draw.text((48,768),"CAD: Source Robotics · CC BY 4.0",font=credit,fill="#bed0df")
            encoder.stdin.write(image.tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError("encoding failed")
    return dict(model=file, video=movie.name, sha256=hashlib.sha256(movie.read_bytes()).hexdigest(),
                frames=FRAMES, max_residual_m=max(f[2] for f in frames), min_rank=min(f[3] for f in frames),
                bindings=[dict(body=b, mesh=p, triangles=len(t)) for b,p,t,_ in meshes],
                joints={name:{k:np.asarray(v).tolist() for k,v in j.items()} for name,j in model.joints.items()},
                publish=False, visual_approved=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads(Path("benchmarks/e15_cad_sources.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    for file in manifest["sha256"]:
        checked(args.source/file, args.source, manifest)
    for file in ("LICENSE", "ATTRIBUTION.md"):
        shutil.copyfile(args.source/file, args.output/file)
    reports = [render(args.source, manifest, file, args.output) for file in manifest["models"]]
    (args.output/"QA.json").write_text(json.dumps(dict(source=manifest, models=reports),indent=2))


if __name__ == "__main__":
    main()
