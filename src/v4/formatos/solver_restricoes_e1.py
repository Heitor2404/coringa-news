"""E1 — solver planar de corpos/juntas genéricos. EXPERIMENTAL, NÃO produção.

Independentemente do mecanismo: poses SE(2), pin (2 equações), slider (2),
slot/pino na ranhura (1), rack_pinion/rolamento ideal (1), driver angular (1), ground fixo.
Unidades são METROS, sem qualquer limite vinculado ao formato do vídeo. Usa scipy.optimize.least_squares.
Não simula dinâmica, contato, fricção, pressão, forças ou segurança industrial.
"""
from __future__ import annotations

import math
import re
import numpy as np
from scipy.optimize import least_squares

SCHEMA="coringa-mechanism-spec-planar-v0"
KINDS={"pin":2,"slider":2,"slot":1,"rack_pinion":1}
NAME=re.compile(r"^[a-z][a-z0-9_]{0,39}$")

def fail(reason):raise ValueError("E1-SOLVER-"+reason)

def vec(x,n):
    if not isinstance(x,(list,tuple)) or len(x)!=n:
        fail("VETOR")
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in x):
        fail("NUMERO")
    return np.array(x,dtype=float)

def _id(x):
    if not isinstance(x,str) or not NAME.fullmatch(x):fail("ID")
    return x

def validate(spec):
    if not isinstance(spec,dict) or spec.get("schema")!=SCHEMA or spec.get("units")!="m":
        fail("CONTRATO")
    if spec.get("publish") is not False or spec.get("visual_approved") is not False:
        fail("PUBLICACAO")
    g=spec.get("ground")
    if not isinstance(g,dict) or set(g)!={"id","pose"}:fail("GROUND")
    gid=_id(g["id"]); vec(g["pose"],3)
    bodies=spec.get("bodies")
    if not isinstance(bodies,list) or not 2<=len(bodies)<=12:fail("CORPOS")
    ids=[gid]
    for b in bodies:
        if not isinstance(b,dict) or set(b)!={"id","seed","shapes"}:
            fail("CORPO")
        ident=_id(b["id"])
        if ident in ids:fail("ID_DUPLICADO")
        ids.append(ident); vec(b["seed"],3)
        if not isinstance(b["shapes"],list) or not b["shapes"]:
            fail("FORMA")
        for shape in b["shapes"]:
            if not isinstance(shape,dict) or shape.get("kind") not in ("segment","slotted_link","disc","gear","rack"):
                fail("FORMA")
            if shape["kind"] in ("segment","slotted_link"):
                if set(shape)!={"kind","a","b","thickness"}:fail("FORMA")
                vec(shape["a"],2);vec(shape["b"],2)
                if not 0<float(shape["thickness"])<1:fail("ESPESSURA")
            if shape["kind"]=="disc":
                if set(shape)!={"kind","center","radius"}:fail("FORMA")
                vec(shape["center"],2)
                if not 0<float(shape["radius"])<5:fail("RAIO")
            if shape["kind"]=="gear":
                if set(shape)!={"kind","center","pitch_radius_m","teeth","tooth_height_m"}:
                    fail("FORMA")
                vec(shape["center"],2)
                if type(shape["teeth"]) is not int or not 8<=shape["teeth"]<=120:
                    fail("DENTES")
                if any(type(shape[x]) not in (int,float) or not math.isfinite(shape[x])
                       for x in ("pitch_radius_m","tooth_height_m")):
                    fail("FORMA")
                if not .02<shape["pitch_radius_m"]<5 or not 0<shape["tooth_height_m"]<.2:
                    fail("FORMA")
            if shape["kind"]=="rack":
                if set(shape)!={"kind","a","b","tooth_pitch_m","tooth_height_m","thickness","tooth_side"}:
                    fail("FORMA")
                a=vec(shape["a"],2);b=vec(shape["b"],2)
                if float(np.linalg.norm(a-b))<.1:fail("FORMA")
                if any(type(shape[x]) not in (int,float) or not math.isfinite(shape[x])
                       for x in ("tooth_pitch_m","tooth_height_m","thickness")):
                    fail("FORMA")
                if not .025<shape["tooth_pitch_m"]<1 or not 0<shape["tooth_height_m"]<.2:
                    fail("FORMA")
                if not 0<shape["thickness"]<.5:fail("FORMA")
                if type(shape["tooth_side"]) is not int or shape["tooth_side"] not in (-1,1):
                    fail("FORMA")
                if float(np.linalg.norm(a-b))/shape["tooth_pitch_m"]>160:
                    fail("DENTES")
    joints=spec.get("joints")
    if not isinstance(joints,list) or not 2<=len(joints)<=40:
        fail("JUNTAS")
    pairs=set();nc=0
    for j in joints:
        if not isinstance(j,dict) or j.get("kind") not in KINDS:
            fail("JUNTA_NAO_SUPORTADA")
        kind=j["kind"]
        expected={"kind","a","b","pa","pb"}
        if kind=="slider":expected|={"axis_a","angle_offset"}
        if kind=="slot":expected|={"axis_b"}
        if kind=="rack_pinion":expected|={"axis_b","pitch_radius_m","pitch_side","phase_m"}
        if set(j)!=expected:fail("CONTRATO_JUNTA")
        if j["a"] not in ids or j["b"] not in ids or j["a"]==j["b"]:
            fail("REFERENCIA_JUNTA")
        vec(j["pa"],2);vec(j["pb"],2)
        if kind=="slider":
            axis=vec(j["axis_a"],2)
            if abs(np.linalg.norm(axis)-1)>1e-7:fail("EIXO_UNITARIO")
            if not math.isfinite(j["angle_offset"]):fail("ANGULO")
        if kind=="slot":
            axis=vec(j["axis_b"],2)
            if abs(np.linalg.norm(axis)-1)>1e-7:fail("EIXO_UNITARIO")
        if kind=="rack_pinion":
            axis=vec(j["axis_b"],2)
            if abs(np.linalg.norm(axis)-1)>1e-7:fail("EIXO_UNITARIO")
            radius=j["pitch_radius_m"];phase=j["phase_m"]
            if type(radius) not in (int,float) or not math.isfinite(radius) or not .02<radius<5:
                fail("RAIO_PRIMITIVO")
            if type(phase) not in (int,float) or not math.isfinite(phase):
                fail("FASE")
            if type(j["pitch_side"]) is not int or j["pitch_side"] not in (-1,1):
                fail("LADO_CONTATO")
        nc+=KINDS[kind]
    dr=spec.get("driver")
    if not isinstance(dr,dict) or set(dr) not in (
        {"body","theta0","speed"},{"body","theta0","speed","profile"}):
        fail("ACIONADOR")
    if dr["body"]==gid or dr["body"] not in ids:fail("ACIONADOR")
    if any(type(dr[x]) not in (int,float) or not math.isfinite(dr[x])
           for x in ("theta0","speed")):fail("ACIONADOR")
    if not .01<=abs(dr["speed"])<=25:fail("ACIONADOR")
    if "profile" in dr:
        profile=dr["profile"]
        if (not isinstance(profile,dict)
            or set(profile)!={"kind","range_min_rad","range_max_rad","phase_rad"}
            or profile["kind"]!="oscillating"):
            fail("PERFIL_ACIONADOR")
        for key in ("range_min_rad","range_max_rad","phase_rad"):
            if type(profile[key]) not in (int,float) or not math.isfinite(profile[key]):
                fail("PERFIL_NUMERO")
        low=profile["range_min_rad"];high=profile["range_max_rad"]
        if not (-2*math.pi<=low<high<=2*math.pi and .001<high-low<math.pi):
            fail("PERFIL_INTERVALO")
        if not -2*math.pi<=profile["phase_rad"]<=2*math.pi:
            fail("PERFIL_FASE")
        # A source's current pose must be exactly the first frame.
        start=(low+high)/2+(high-low)/2*math.cos(profile["phase_rad"])
        if abs(start-dr["theta0"])>1e-6:
            fail("PERFIL_POSE_INICIAL_DIVERGE")
    duration=spec.get("duration_s")
    if type(duration) not in (int,float) or not 2<=duration<=12:fail("TEMPO")
    # With prescribed driver angle, 3 vars/body must be matched by constraint count.
    # This is a topology diagnostic, not a proof of independent constraints.
    n=3*len(bodies)
    if nc+1!=n:
        fail("RESTRICOES_CONTAGEM")
    return tuple(ids)

def rotate(p,theta):
    c=math.cos(theta);s=math.sin(theta)
    return np.array((c*p[0]-s*p[1],s*p[0]+c*p[1]))

def world(pose,local):
    return np.array(pose[:2])+rotate(local,pose[2])

def residual(q,spec,t,names):
    state={spec["ground"]["id"]:vec(spec["ground"]["pose"],3)}
    state.update({n:np.asarray(q[3*k:3*k+3])
                  for k,n in enumerate(names[1:])})
    out=[]
    for j in spec["joints"]:
        a=state[j["a"]];b=state[j["b"]]
        pa=world(a,j["pa"]);pb=world(b,j["pb"])
        if j["kind"]=="pin":
            out.extend(pa-pb)
        elif j["kind"]=="slider":
            axis=rotate(j["axis_a"],a[2])
            delta=pb-pa
            out.append(axis[0]*delta[1]-axis[1]*delta[0])
            out.append(b[2]-a[2]-j["angle_offset"])
        elif j["kind"]=="slot":
            axis=rotate(j["axis_b"],b[2])
            delta=pa-pb
            out.append(axis[0]*delta[1]-axis[1]*delta[0])
        else:  # rack_pinion: pitch-line rolling; NO collision / tooth contact.
            axis=rotate(j["axis_b"],b[2])
            delta=pb-pa
            along=float(np.dot(delta,axis))
            # The pitch_side sets which side of the rack faces the pinion.
            out.append(along+j["pitch_side"]*j["pitch_radius_m"]*
                       (a[2]-b[2])-j["phase_m"])
    d=spec["driver"]
    if "profile" in d:
        profile=d["profile"]
        lo=profile["range_min_rad"];hi=profile["range_max_rad"]
        target=(lo+hi)/2+(hi-lo)/2*math.cos(
            profile["phase_rad"]+d["speed"]*t)
    else:
        target=d["theta0"]+d["speed"]*t
    out.append(state[d["body"]][2]-target)
    return np.asarray(out,dtype=float)

def solve_constraints(equations, q, args=()):
    """Common numeric closure and rank check, independent of coordinate chart."""
    result=least_squares(equations,q,args=args,method="lm",
          xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=400)
    err=float(np.max(np.abs(result.fun)))
    if not result.success or err>1e-7:fail("FECHAMENTO")
    # Jacobian rank at solution: count alone can hide underconstraint/singularity.
    rank=int(np.linalg.matrix_rank(result.jac,tol=1e-8))
    if rank<len(result.x):fail("SINGULAR_OU_SUBDETERMINADO")
    return result,err,rank

def solve_one(spec,t,previous=None):
    names=validate(spec)
    if type(t) not in (float,int) or not math.isfinite(t) or not 0<=t<=spec["duration_s"]:
        fail("INSTANTE")
    q=np.concatenate([vec(b["seed"],3) for b in spec["bodies"]]) if previous is None else np.array(previous,dtype=float)
    if len(q)!=3*len(spec["bodies"]) or not np.isfinite(q).all():
        fail("ESTADO")
    result,err,rank=solve_constraints(residual,q,(spec,t,names))
    states={names[0]:vec(spec["ground"]["pose"],3).tolist()}
    states.update({b["id"]:result.x[3*k:3*k+3].tolist()
                   for k,b in enumerate(spec["bodies"])})
    # A rolling equation alone could "work" with the rack far from its wheel.
    # Enforce pitch-line tangency independently, without adding a redundant
    # constraint to the optimization. The slider must preserve this geometry.
    for j in spec["joints"]:
        if j["kind"]!="rack_pinion":continue
        a=states[j["a"]];b=states[j["b"]]
        axis=rotate(j["axis_b"],b[2])
        delta=world(b,j["pb"])-world(a,j["pa"])
        normal=float(axis[0]*delta[1]-axis[1]*delta[0])
        expected=j["pitch_side"]*j["pitch_radius_m"]
        if abs(normal-expected)>1e-6:fail("RACK_SEM_TANGENCIA")
    return {"t":float(t),"poses":states,"max_residual_m":err,
            "jacobian_rank":rank,"jacobian_size":len(result.x),
            "iterations":int(result.nfev),"q":result.x.tolist()}

def trajectory(spec,samples=121):
    validate(spec)
    if type(samples) is not int or not 3<=samples<=500:fail("AMOSTRAS")
    output=[];prior=None
    for t in np.linspace(0,float(spec["duration_s"]),samples):
        frame=solve_one(spec,float(t),prior)
        if prior is not None:
            jump=np.abs(np.array(frame["q"])-np.array(prior))
            if float(np.max(jump))>.8:
                fail("SALTO_DE_RAMO")
        prior=frame["q"]
        output.append(frame)
    return output
