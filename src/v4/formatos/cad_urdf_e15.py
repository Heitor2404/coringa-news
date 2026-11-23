"""Rigid CAD visual meshes and constrained joint coordinates from a pinned URDF tree."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation
from .solver_restricoes_e1 import solve_constraints


def vector(raw, size):
    values = np.array([float(x) for x in raw.split()])
    if values.shape != (size,) or not np.isfinite(values).all():
        raise ValueError("invalid URDF vector")
    return values


def origin(node):
    pose = np.eye(4)
    item = node.find("origin")
    if item is not None:
        pose[:3, 3] = vector(item.get("xyz", "0 0 0"), 3)
        pose[:3, :3] = Rotation.from_euler("xyz", vector(item.get("rpy", "0 0 0"), 3)).as_matrix()
    return pose


def checked(path, root, manifest):
    key = path.resolve().relative_to(root.resolve()).as_posix()
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest["sha256"][key]:
        raise ValueError(f"source digest mismatch: {key}")
    return data


def triangles(data):
    count = int.from_bytes(data[80:84], "little")
    if not count or len(data) != 84 + 50 * count:
        raise ValueError("expected binary triangle STL")
    dtype = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])
    vertices = np.frombuffer(data, dtype, offset=84)["vertices"].astype(float)
    if not np.isfinite(vertices).all():
        raise ValueError("non-finite mesh")
    return vertices


class Assembly:
    def __init__(self, xml):
        self.links = [l.attrib["name"] for l in xml.findall("link")]
        self.joints = {}
        self.moving = []
        children = set()
        for j in xml.findall("joint"):
            name = j.attrib["name"]
            kind = j.attrib["type"]
            parent = j.find("parent").attrib["link"]
            child = j.find("child").attrib["link"]
            if (kind not in {"fixed", "prismatic"} or child in children or name in self.joints
                    or parent not in self.links or child not in self.links):
                raise ValueError("unsupported joint or invalid tree")
            children.add(child)
            entry = dict(parent=parent, child=child, origin=origin(j))
            if kind == "prismatic":
                axis = vector(j.find("axis").attrib["xyz"], 3)
                if abs(np.linalg.norm(axis) - 1) > 1e-7:
                    raise ValueError("invalid axis")
                limit = j.find("limit")
                low, high = (float(limit.attrib[k]) for k in ("lower", "upper"))
                if not np.isfinite([low, high]).all() or low >= high:
                    raise ValueError("invalid travel")
                entry.update(axis=axis, low=low, high=high)
                mimic = j.find("mimic")
                if mimic is not None:
                    entry.update(source=mimic.attrib["joint"], factor=float(mimic.get("multiplier", 1)),
                                 offset=float(mimic.get("offset", 0)))
                self.moving.append(name)
            self.joints[name] = entry
        roots = set(self.links) - children
        if len(roots) != 1 or len(set(self.links)) != len(self.links):
            raise ValueError("invalid root or duplicate link")
        self.root = roots.pop()
        drivers = [n for n in self.moving if "source" not in self.joints[n]]
        if len(drivers) != 1:
            raise ValueError("expected one independent linear driver")
        self.driver = drivers[0]
        self.matrix = np.eye(len(self.moving))
        self.offset = np.zeros(len(self.moving))
        for row, name in enumerate(self.moving):
            j = self.joints[name]
            if "source" in j:
                self.matrix[row, self.moving.index(j["source"])] -= j["factor"]
                self.offset[row] = j["offset"]
        if not np.isfinite(self.matrix).all() or not np.isfinite(self.offset).all():
            raise ValueError("invalid mimic")

    def frame(self, fraction):
        drive = self.joints[self.driver]
        target = self.offset.copy()
        target[self.moving.index(self.driver)] = drive["low"] + fraction * (drive["high"] - drive["low"])
        result, error, rank = solve_constraints(lambda q: self.matrix @ q - target, np.zeros(len(target)))
        values = dict(zip(self.moving, result.x))
        poses = {self.root: np.eye(4)}
        pending = dict(self.joints)
        while pending:
            before = len(pending)
            for name, j in list(pending.items()):
                if j["parent"] not in poses:
                    continue
                local = j["origin"].copy()
                if name in values:
                    q = values[name]
                    if not j["low"] - 1e-10 <= q <= j["high"] + 1e-10:
                        raise ValueError("joint limit exceeded")
                    local[:3, 3] += local[:3, :3] @ (j["axis"] * q)
                poses[j["child"]] = poses[j["parent"]] @ local
                del pending[name]
            if before == len(pending):
                raise ValueError("unreachable links")
        return poses, values, error, rank


def load_model(root, manifest, filename):
    path = root / filename
    xml = ET.fromstring(checked(path, root, manifest))
    model = Assembly(xml)
    meshes = []
    for link in xml.findall("link"):
        for visual in link.findall("visual"):
            mesh = visual.find("geometry/mesh")
            if mesh is None:
                raise ValueError("expected sourced mesh")
            file = path.parent / mesh.attrib["filename"]
            points = triangles(checked(file, root, manifest)) * vector(mesh.get("scale", "1 1 1"), 3)
            pose = origin(visual)
            color = visual.find("material/color")
            rgb = vector(color.attrib["rgba"], 4)[:3] if color is not None else np.array([.65]*3)
            meshes.append((link.attrib["name"], file.relative_to(root).as_posix(),
                           points @ pose[:3, :3].T + pose[:3, 3], rgb))
    return model, meshes
