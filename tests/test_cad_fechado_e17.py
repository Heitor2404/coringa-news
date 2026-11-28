import json
import math
import os
import unittest
from pathlib import Path

import numpy as np
from src.v4.formatos.cad_fechado_e17 import load, register_pin, solver, verify


@unittest.skipUnless(os.environ.get("E17_CAD_DIR"), "requires verified STEP from design publisher")
class TestClosedCAD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ["E17_CAD_DIR"])
        cls.manifest = json.loads(Path("benchmarks/e17_closed_step.json").read_text())
        cls.step = root/"loop.step"
        cls.solids,cls.plane,cls.origins,cls.pins,cls.spec = load(cls.manifest, cls.step, root/"LICENSE.md")
        cls.frames = solver.trajectory(cls.spec,97,cad_bodies=cls.solids)

    def test_independent_offset_slider_solution(self):
        # Design sheet: throw 15 mm, rod 60 mm, slider 15 mm below main pivot.
        for angle, frame in zip(np.linspace(0,math.tau,97),self.frames):
            px = 15*math.sin(angle)
            dz = 15*(math.cos(angle)-1)
            x = px + math.sqrt(60**2-dz**2)
            pos = np.array(frame["poses"]["slider"][:2])*1000
            np.testing.assert_allclose(pos,[x,7],atol=1e-6,rtol=0)
            self.assertEqual(frame["jacobian_rank"],9)
        for name in self.solids:
            a = np.array(self.frames[0]["poses"][name])
            b = np.array(self.frames[-1]["poses"][name])
            np.testing.assert_allclose(a[:2],b[:2],atol=1e-9)
            self.assertAlmostEqual(math.cos(b[2]-a[2]),1.)

    def test_unrelated_solids_rejected(self):
        with self.assertRaisesRegex(ValueError,"coaxial"):
            register_pin(self.solids["frame"],self.solids["slider"],self.plane)

    def test_incomplete_cad_registration(self):
        with self.assertRaises(ValueError):
            solver.validate(self.spec,cad_bodies={"crank","frame","rod"})

    def test_source_change_rejected(self):
        with self.assertRaisesRegex(ValueError,"digest"):
            verify(self.step,"0"*64)
