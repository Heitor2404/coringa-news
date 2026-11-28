"""Regression checks against the published frames of both pinned URDF assemblies."""
import json
import os
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation
from src.v4.formatos.cad_urdf_e15 import Assembly, checked, load_model


@unittest.skipUnless(os.getenv("E15_CAD_ROOT"), "requires pinned E15 source checkout")
class TestCAD(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ["E15_CAD_ROOT"])
        self.lock = json.loads(Path("benchmarks/e15_cad_sources.json").read_text())

    def test_independent_tool_frames(self):
        # Source values are in the housing frame. Check translation AND orientation.
        for file, extent, local_origin, yaw in [
            (self.lock["models"][0], .0525, [.02835,0,-.1409], 3.1416),
            (self.lock["models"][1], .0235, [0,0,-.11745], -3.1416),
        ]:
            model, meshes = load_model(self.root, self.lock, file)
            self.assertTrue(all(len(points)>0 for _,_,points,_ in meshes))
            R = Rotation.from_euler("xyz", [-3.1416,0,yaw]).as_matrix()
            parent = model.joints["left_finger_joint"]["parent"]
            for phase in np.linspace(0, 1, 97):
                poses, _, error, rank = model.frame(phase)
                self.assertEqual(rank, 2)
                self.assertLess(error, 1e-9)
                for sign, body in [(1,"left_finger_link"),(-1,"right_finger_link")]:
                    rel = np.linalg.inv(poses[parent]) @ poses[body]
                    expected = local_origin + R @ [0, sign*extent*(1-phase), 0]
                    np.testing.assert_allclose(rel[:3,3],expected,rtol=0,atol=1e-10)
                    np.testing.assert_allclose(rel[:3,:3],R,rtol=0,atol=1e-10)

    def test_hinge_registration_and_measured_rotation(self):
        case = self.lock["hinges"][0]
        model, meshes = load_model(self.root,self.lock,case["file"],case["joint"])
        self.assertEqual({m[0] for m in meshes},{"upper_arm_link","forearm_link"})
        # URDF zero configuration. The child axis stays on the same world line.
        joint0 = Rotation.from_euler("xyz",[np.pi,0,-np.pi/2]).as_matrix()
        for t in np.linspace(0,1,97):
            poses, _, _, _ = model.frame(t)
            pose = poses["forearm_link"]
            np.testing.assert_allclose(pose[:3,3],[0,-.18,0],atol=1e-12)
            q = -1.3 + 3.3*t
            expected = joint0 @ Rotation.from_euler("z",q).as_matrix()
            np.testing.assert_allclose(pose[:3,:3],expected,atol=1e-12)

    def test_reject_unsupported_revolute(self):
        xml = ET.parse(self.root/self.lock["models"][0]).getroot()
        xml.find("joint[@type='prismatic']").set("type","revolute")
        with self.assertRaisesRegex(ValueError,"unsupported"):
            Assembly(xml)

    def test_reject_inconsistent_follower(self):
        xml = ET.parse(self.root/self.lock["models"][0]).getroot()
        xml.find("joint/mimic").set("multiplier","1")
        with self.assertRaisesRegex(ValueError,"limit"):
            Assembly(xml).frame(0)

    def test_changed_source(self):
        file = self.lock["models"][0]
        self.lock["sha256"][file] = "0"*64
        with self.assertRaisesRegex(ValueError,"digest"):
            checked(self.root/file,self.root,self.lock)
