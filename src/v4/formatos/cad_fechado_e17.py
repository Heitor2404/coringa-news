"""Import registered STEP solids and bind coaxial face pairs to E1 planar constraints."""
import hashlib
import itertools
import math
from pathlib import Path

import cadquery as cq
import numpy as np
from . import solver_restricoes_e1 as solver


def verify(path, digest):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
        raise ValueError("source digest mismatch")


def aligned(a, b):
    return abs(abs(np.dot(a,b))-1) < 1e-8


def round_axes(solid, plane):
    normal = np.cross(*plane)
    axes = []
    for face in solid.Faces():
        if face.geomType() not in {"CONE","CYLINDER"}:
            continue
        axis = face._geomAdaptor().Position().Axis()
        if aligned(axis.Direction().Coord(),normal):
            axes.append(plane @ axis.Location().Coord())
    return np.unique(np.round(axes,8),axis=0)


def register_pin(a, b, plane):
    candidates = [(x,y) for x,y in itertools.product(round_axes(a,plane),round_axes(b,plane))
                  if np.linalg.norm(x-y) < 1e-5]
    if len(candidates) != 1:
        raise ValueError("missing or ambiguous coaxial joint")
    return candidates[0]


def guide_normals(solid, direction):
    normals = []
    for face in solid.Faces():
        if face.geomType() == "PLANE":
            n = np.asarray(face.normalAt().toTuple())
            if abs(n @ direction) < 1e-8:
                normals.append(n)
    return normals


def register_guide(a, b, direction):
    normals = [n for n in guide_normals(a,direction)
               if any(aligned(n,m) for m in guide_normals(b,direction))]
    if not normals or np.linalg.matrix_rank(normals,tol=1e-6) != 2:
        raise ValueError("no two independent guide-plane normals")


def load(manifest, step, license_file):
    verify(step,manifest["files"]["step"][1])
    verify(license_file,manifest["files"]["license"][1])
    solids = {}
    for shape, path, loc, _ in cq.Assembly.load(str(step)):
        prefix, name = path.rsplit("/",1)
        if prefix != manifest["assembly"] or name in solids or len(shape.Solids()) != 1:
            raise ValueError("unexpected STEP part identity")
        solids[name] = shape.moved(loc)
    plane = np.array([manifest["horizontal"],manifest["vertical"]],dtype=float)
    if not np.allclose(plane@plane.T,np.eye(2)):
        raise ValueError("invalid projection frame")
    pins, origins = [], {}
    for a,b in manifest["pin_pairs"]:
        pa,pb = register_pin(solids[a],solids[b],plane)
        origins.setdefault(a,pa)
        origins.setdefault(b,pb)
        pins.append((a,b,pa,pb))
    joints = [dict(kind="pin",a=a,b=b,pa=((pa-origins[a])/1000).tolist(),
                   pb=((pb-origins[b])/1000).tolist()) for a,b,pa,pb in pins]
    a,b = manifest["slider_pair"]
    direction = np.asarray(manifest["guide_direction"],dtype=float)
    if abs(np.linalg.norm(plane@direction)-1)>1e-8 or not np.isclose(np.linalg.norm(direction),1):
        raise ValueError("guide outside motion plane")
    register_guide(solids[a],solids[b],direction)
    joints.append(dict(kind="slider",a=a,b=b,pa=((origins[b]-origins[a])/1000).tolist(),
                       pb=[0.,0.],axis_a=(plane@direction).tolist(),angle_offset=0.))
    ground = manifest["ground"]
    pose = lambda n: [*(origins[n]/1000).tolist(),0.]
    spec = dict(schema=solver.SCHEMA,units="m",ground=dict(id=ground,pose=pose(ground)),
                bodies=[dict(id=n,seed=pose(n),shapes=[]) for n in solids if n!=ground],
                joints=joints,driver=dict(body=manifest["driver"],theta0=0.,speed=math.tau/4),
                duration_s=4.,publish=False,visual_approved=False)
    solver.validate(spec,cad_bodies=solids)
    return solids, plane, origins, pins, spec


def placement(plane, origin, pose):
    """Move the as-supplied assembled solid about its registered local origin."""
    axis = np.cross(*plane)
    start = plane.T @ origin
    displacement = plane.T @ (np.asarray(pose[:2])*1000-origin)
    return (cq.Location(cq.Vector(*(start+displacement))) *
            cq.Location(cq.Vector(),cq.Vector(*axis),math.degrees(pose[2])) *
            cq.Location(cq.Vector(*-start)))


def audit(manifest, solids, plane, origins, pins, frames):
    name = manifest["measurement_body"]
    direction = plane @ manifest["guide_direction"]
    positions = np.array([np.asarray(f["poses"][name][:2]) @ direction for f in frames])*1000
    stroke = float(np.ptp(positions))
    if abs(stroke-manifest["reference_stroke_mm"]) > .03:
        raise ValueError(f"source stroke mismatch: {stroke}")
    max_error = max_volume = 0.
    checks = 0
    for i,f in enumerate(frames):
        transforms = {n:placement(plane,origins[n],p) for n,p in f["poses"].items()}
        def moved_point(body, xy):
            v = cq.Vertex.makeVertex(*(plane.T@xy)).moved(transforms[body])
            return np.array(v.Center().toTuple())
        for a,b,pa,pb in pins:
            max_error = max(max_error,float(np.linalg.norm(moved_point(a,pa)-moved_point(b,pb))))
        if i % 4 == 0:
            posed = [s.moved(transforms[n]) for n,s in solids.items()]
            for a,b in itertools.combinations(posed,2):
                max_volume = max(max_volume,abs(a.intersect(b).Volume()))
                checks += 1
    if max_error>1e-4 or max_volume>1e-5:
        raise ValueError(f"registration/contact error {max_error} mm, {max_volume} mm3")
    return dict(frames=len(frames),stroke_mm=stroke,source_stroke_mm=manifest["reference_stroke_mm"],
                max_pin_error_mm=max_error,max_overlap_mm3=max_volume,solid_pair_checks=checks,
                min_jacobian_rank=min(f["jacobian_rank"] for f in frames))
