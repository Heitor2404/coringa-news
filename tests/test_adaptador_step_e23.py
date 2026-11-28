import json
import math
import os
from pathlib import Path
import unittest
import numpy as np
from src.v4.formatos.adaptador_step_e23 import montar, resolver, comparar_planar


class SolidStub:
    def tessellate(self, *args):
        class V:
            def __init__(self, p): self.p=p
            def toTuple(self): return self.p
        return [V((0,0,0)),V((1,0,0)),V((0,1,0))],[(0,1,2)]


def fixture():
    # Fixture analítica: biela 60 mm, manivela 15 mm. Não é CAD industrial.
    g="base"; a="input"; b="link"; c="output"
    solids={k:SolidStub() for k in (g,a,b,c)}
    spec=dict(ground=dict(id=g,pose=[0,0,0]),
        bodies=[dict(id=a,seed=[0,0,0]),dict(id=b,seed=[0,.015,0]),
                dict(id=c,seed=[.060,.015,0])],
        driver=dict(body=a),
        joints=[dict(kind="pin",a=g,b=a,pa=[0,0],pb=[0,0]),
                dict(kind="pin",a=a,b=b,pa=[0,.015],pb=[0,0]),
                dict(kind="pin",a=b,b=c,pa=[.060,0],pb=[0,0]),
                dict(kind="slider",a=g,b=c,pa=[.060,.015],pb=[0,0],axis_a=[1,0],angle_offset=0)])
    return solids,np.array([[1,0,0],[0,0,1]],float),spec


class E23(unittest.TestCase):
    def test_full_turn(self):
        solids,P,s=fixture()
        angles=np.linspace(0,math.tau,97)
        m,traj,_=resolver(solids,P,s,angles)
        self.assertEqual(len(m.igualdades),1)
        self.assertEqual(len(m.juntas),3)
        self.assertEqual(len(m.visuais),4)
        for t,(q,info) in zip(angles,traj):
            x=-.015*np.sin(t)+np.sqrt(.060**2-(.015-.015*np.cos(t))**2)
            p=P@m.poses(q)[m.indice_corpo("output")][:3,3]
            np.testing.assert_allclose(p,[x,.015],atol=1e-7,rtol=0)
            self.assertLess(info["residuo"],1e-7)

    def test_missing_cad(self):
        solids,P,s=fixture()
        del solids["link"]
        with self.assertRaisesRegex(ValueError,"IDENTIDADE_CAD"):
            montar(solids,P,s)

    def test_bad_anchor(self):
        solids,P,s=fixture()
        s["joints"][1]["pa"]=[0,.020]
        with self.assertRaisesRegex(ValueError,"ANCORAS"):
            montar(solids,P,s)

    def test_plane_invalid(self):
        solids,P,s=fixture()
        with self.assertRaisesRegex(ValueError,"PLANO"):
            montar(solids,P*2,s)


@unittest.skipUnless(os.environ.get("E17_CAD_DIR"), "fonte STEP verificada somente no CI")
class E23Real(unittest.TestCase):
    def test_source_against_e1(self):
        from src.v4.formatos.cad_fechado_e17 import load, solver
        root=Path(os.environ["E17_CAD_DIR"])
        manifest=json.loads(Path("benchmarks/e17_closed_step.json").read_text())
        solids,P,origins,pins,s=load(manifest,root/"loop.step",root/"LICENSE.md")
        old=solver.trajectory(s,97,cad_bodies=solids)
        m,traj,_=resolver(solids,P,s,np.linspace(0,math.tau,97))
        result=comparar_planar(m,traj,P,old)
        direction=np.asarray(manifest["guide_direction"],float)
        idx=m.indice_corpo(manifest["measurement_body"])
        stroke=np.ptp([m.poses(q)[idx][:3,3]@direction for q,_ in traj])*1000
        self.assertAlmostEqual(stroke,manifest["reference_stroke_mm"],delta=.03)
        print("E23-REAL",json.dumps(dict(result,curso_mm=float(stroke))))
