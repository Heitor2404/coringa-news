"""Check the encoded movies and compare STEP landmarks in the manufacturer's mesh frame."""
import json
import subprocess
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

from .cad_urdf_e15 import checked, triangles, load_model


def step_landmarks(root, lock, registration):
    config_path = root / registration["registration"]
    config = json.loads(checked(config_path, root, lock))
    step = config_path.parent / config["source"]
    checked(step, root, lock)
    if config["source_units"] != "mm" or lock["sha256"][str(step.relative_to(root))] != config["source_sha256"]:
        raise ValueError("STEP unit or digest")
    solid = cq.importers.importStep(str(step)).solids().vals()[config["solid_ids"]["finger"]-1]
    points = np.array([v.Center().toTuple() for v in solid.Vertices()])
    local = points*.001 @ np.array(config["source_to_left_finger_rotation"]).T + config["source_to_left_finger_translation_m"]
    mesh = triangles(checked(root/registration["mesh"], root, lock))
    distances = cKDTree(mesh.reshape(-1,3)).query(local)[0]*1000
    if distances.max() > config["maximum_mesh_deviation_mm"]:
        raise ValueError("STEP landmarks outside mesh tolerance")
    return dict(count=len(points), max_vertex_to_vertex_mm=float(distances.max()), mesh=registration["mesh"])


def pivot_rings(root, lock, case):
    """Find CAD vertex rings about the URDF axis; fit centers without forcing them onto it."""
    model, meshes = load_model(root, lock, case["file"], case["joint"])
    j = model.joints[case["joint"]]
    axis = j["axis"]
    u = np.eye(3)[np.argmin(abs(axis))]
    u = u - axis*(u @ axis)
    u /= np.linalg.norm(u)
    basis = np.stack([u, np.cross(axis,u), axis],axis=1)
    rings = {}
    for body, file, tris, _ in meshes:
        points = np.unique(tris.reshape(-1,3),axis=0)
        if body == j["parent"]:
            points = (points-j["origin"][:3,3]) @ j["origin"][:3,:3]
        points = points @ basis
        radial = np.linalg.norm(points[:,:2],axis=1)
        bins = np.rint(np.column_stack((radial,points[:,2]))/1e-5).astype(int)
        keys, group, counts = np.unique(bins,axis=0,return_inverse=True,return_counts=True)
        for idx in np.flatnonzero(counts>=16):
            xy = points[group==idx,:2]
            angles = np.sort(np.arctan2(xy[:,1],xy[:,0]))
            gap = np.degrees(np.diff(np.r_[angles,angles[0]+2*np.pi]).max())
            if gap > 30 or keys[idx,0] < 100:
                continue
            design = np.column_stack((2*xy,np.ones(len(xy))))
            solution = np.linalg.lstsq(design,np.sum(xy**2,axis=1),rcond=None)[0]
            center = solution[:2]
            if body not in rings or gap < rings[body]["max_gap_deg"]:
                rings[body] = dict(mesh=file, vertices=len(xy), max_gap_deg=float(gap),
                                   radius_mm=float(np.linalg.norm(xy-center,axis=1).mean()*1000),
                                   axis_offset_mm=float(np.linalg.norm(center)*1000))
    if set(rings) != {j["parent"], j["child"]} or max(v["axis_offset_mm"] for v in rings.values()) > .05:
        raise ValueError("pivot axis lacks matching CAD rings on both sides")
    return rings


def inspect(movie, expected):
    probe = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-of","json",str(movie)]))
    stream, = probe["streams"]
    if (stream["codec_type"], stream["width"], stream["height"], stream["r_frame_rate"]) != ("video",540,960,"24/1"):
        raise ValueError("unexpected stream")
    data = subprocess.check_output(["ffmpeg","-v","error","-i",str(movie),"-vf","scale=270:480",
                                    "-f","rawvideo","-pix_fmt","rgb24","-"])
    frames = np.frombuffer(data,np.uint8).reshape(-1,480,270,3)
    if len(frames) != expected:
        raise ValueError("unexpected frame count")
    roi = frames[:, 78:350, 12:254].astype(np.int16)
    def changed(i,j):
        return int((np.abs(roi[i]-roi[j]).max(axis=2)>18).sum())
    mid = len(roi)//2
    motion, closure = changed(0,mid), changed(0,-1)
    if motion < 350 or closure > motion*.08:
        raise ValueError(f"decoded motion or return: {motion}, {closure}")
    board = Image.fromarray(np.concatenate(frames[[0,mid//2,mid,mid+mid//2,-1]],axis=1))
    board.save(movie.with_suffix(".jpg"),quality=92)
    return dict(decoded_frames=len(frames), excursion_changed_pixels=motion, return_changed_pixels=closure)


if __name__ == "__main__":
    root, out = map(Path,sys.argv[1:])
    path = out/"QA.json"
    report = json.loads(path.read_text())
    lock = report["source"]
    report["step_landmarks"] = step_landmarks(root, lock, lock["step_registration"])
    report["pivot_rings"] = {h["joint"]:pivot_rings(root,lock,h) for h in lock.get("hinges",[])}
    for m in report["models"]:
        m["decoded"] = inspect(out/m["video"], m["frames"])
        print(m["video"],m["decoded"])
    print(report["step_landmarks"])
    path.write_text(json.dumps(report,indent=2))
