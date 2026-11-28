"""Camera semantica vertical: alvo fisico, viewport e limites por geometria.
Duas configuracoes, mesmos controles. O port Python audita a especificacao
matematica (TypeScript e compilado e video REAL renderizado no workflow).
"""
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"motor4/remotion/src/formatos/slider-crank-proofs.json"
CAM=ROOT/"motor4/remotion/src/formatos/MechanismCamera2D.ts"
SCENE=ROOT/"motor4/remotion/src/formatos/SliderCrankProof.tsx"

def smooth(x):
    v=max(0,min(1,x))
    return v*v*(3-2*v)

def lerp(a,b,z):
    return a+(b-a)*z

def cam(t, data, focus, previous, step_at):
    start=data["introViewport"];detail=data["detailViewport"]
    bounds=data["machineBounds"]
    zoom=smooth((t-data["zoomStart"])/data["zoomSeconds"])
    v={x:lerp(start[x],detail[x],zoom) for x in start}
    w=bounds["right"]-bounds["left"]
    h=bounds["bottom"]-bounds["top"]
    scale=min(lerp(1,data["maxScale"],zoom),
              (v["right"]-v["left"])/w,(v["bottom"]-v["top"])/h)
    cx=(v["left"]+v["right"])/2
    cy=(v["top"]+v["bottom"])/2
    mx=(bounds["left"]+bounds["right"])/2
    my=(bounds["top"]+bounds["bottom"])/2
    z=smooth((t-step_at)/.5)
    fx=lerp(previous[0],focus[0],z)
    fy=lerp(previous[1],focus[1],z)
    tx=cx-scale*mx+(mx-fx)*.33*zoom
    ty=cy-scale*my+(my-fy)*.075*zoom
    tx=max(v["left"]-scale*bounds["left"],
           min(tx,v["right"]-scale*bounds["right"]))
    ty=max(v["top"]-scale*bounds["top"],
           min(ty,v["bottom"]-scale*bounds["bottom"]))
    return scale,tx,ty,v

def focus_pos(name, model, t):
    g=model["geometry"]
    r=g["radius"];L=g["rodLength"]
    theta=2*math.pi*min(1,max(0,t/(8.4-.38)))
    dx=r*math.sin(theta)
    crank=(g["centerX"]+dx,g["centerY"]-r*math.cos(theta))
    piston=(g["centerX"],
            g["centerY"]-r*math.cos(theta)-math.sqrt(L*L-dx*dx))
    if name=="piston":return (piston[0],piston[1]-44)
    if name=="rod":return ((piston[0]+crank[0])/2,(piston[1]+crank[1])/2)
    if name=="crank":return (g["centerX"],g["centerY"])
    if name=="intake":return (406,580)
    return (590,580)

def check_bounds(c,data):
    scale,tx,ty,v=c
    b=data["machineBounds"]
    assert scale >= .999
    assert b["left"]*scale+tx >= v["left"]-1e-6
    assert b["right"]*scale+tx <= v["right"]+1e-6
    assert b["top"]*scale+ty >= v["top"]-1e-6
    assert b["bottom"]*scale+ty <= v["bottom"]+1e-6

def test_reutilizacao_de_camera_entre_motor_e_compressor_em_252_frames():
    dat=json.loads(CFG.read_text("utf8"))
    config=dat["camera"]
    all_poses={}
    for name,model in dat["models"].items():
        poses=[]
        for frame in range(252):
            t=frame/30
            step=max(i for i,b in enumerate(model["steps"]) if b["at"]<=t)
            prev=model["steps"][max(step-1,0)]
            current=model["steps"][step]
            pose=cam(t,config,focus_pos(current["focus"],model,t),
                     focus_pos(prev["focus"],model,t),current["at"])
            check_bounds(pose,config)
            if poses:
                last=poses[-1]
                assert abs(pose[0]-last[0]) < .035  # nenhum jump de zoom
                assert abs(pose[1]-last[1]) < 15    # sem pan instantaneo
                assert abs(pose[2]-last[2]) < 15
            poses.append(pose)
        all_poses[name]=poses
        assert poses[0][0]==1.0
        assert poses[-1][0]>1.10
    assert all_poses["motor"]!=all_poses["compressor"]

def test_foco_muda_camera_de_forma_controlada():
    data=json.loads(CFG.read_text("utf8"))["camera"]
    t=6.4
    left=cam(t,data,(406,580),(406,580),4.0)
    right=cam(t,data,(590,580),(590,580),4.0)
    check_bounds(left,data);check_bounds(right,data)
    assert left[1]>right[1] and left[1]-right[1]>15

def test_plano_nao_depende_do_assunto_ou_de_corte_por_video():
    source=CAM.read_text("utf8")
    scene=SCENE.read_text("utf8")
    assert "semanticCamera2D" in source
    assert "F-CAMERA-NAO-CABE" in source
    assert "machine:specs.camera.machineBounds" in scene
    assert "previousFocus=focusAnchor" in scene
    assert "currentFocus=focusAnchor" in scene
    assert "camera.scale" in scene
    assert "titleOpacity" in scene
    assert '<SVGText x={285} y={1208}' in scene
    assert "String(fixture.steps.length).padStart(2,\'0\')" in scene
    assert "focus==='intake'" in scene and "focus==='outlet'" in scene
    assert "if(kind==='motor')" not in scene
    assert "if(kind==='compressor')" not in scene

def test_modelos_preservam_causalidade_e_sincronismo_de_etapas():
    dat=json.loads(CFG.read_text("utf8"))
    assert dat["models"]["compressor"]["steps"][-1]["at"] >= 7.0
    assert dat["camera"]["zoomStart"]>=1.6
    assert dat["camera"]["maxScale"]<=1.20
    assert dat["camera"]["detailViewport"]["bottom"]<=1174
    assert dat["qa"]["publish"] is False and dat["qa"]["visualApproval"]=="PENDING"
