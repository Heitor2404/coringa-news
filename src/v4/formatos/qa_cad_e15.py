"""Check the encoded movies and compare STEP landmarks in the manufacturer's mesh frame."""
import json
import subprocess
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

from .cad_urdf_e15 import checked, triangles


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
    for m in report["models"]:
        m["decoded"] = inspect(out/m["video"], m["frames"])
        print(m["video"],m["decoded"])
    print(report["step_landmarks"])
    path.write_text(json.dumps(report,indent=2))
