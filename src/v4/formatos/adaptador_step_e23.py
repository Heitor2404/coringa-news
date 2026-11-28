"""Ponte de montagens STEP planares registradas para o núcleo multicorpo E18.

O STEP sozinho não prova mates: recebe o registro E17 já verificado por hash,
com pares curados e eixos extraídos de faces analíticas. Não infere topologia
por nome. Limites: plano único, pose de referência angular zero, pivôs
revolutos, guias prismáticas em árvore, fechamento por pino. Não redistribui CAD.
"""
from __future__ import annotations
import numpy as np
from . import multicorpo_e18 as M


def fail(reason):
    raise ValueError("E23-" + reason)


def montar(solids, plane, spec):
    P = np.asarray(plane, float)
    if (P.shape != (2, 3) or not np.isfinite(P).all()
            or not np.allclose(P @ P.T, np.eye(2), atol=1e-8, rtol=0)):
        fail("PLANO")
    n = np.cross(*P)
    ground = spec["ground"]["id"]
    driver = spec["driver"]["body"]
    seeds = {ground: spec["ground"]["pose"]}
    for body in spec["bodies"]:
        if body["id"] in seeds:
            fail("CORPO_DUPLICADO")
        seeds[body["id"]] = body["seed"]
    if set(seeds) != set(solids) or ground == driver or driver not in seeds:
        fail("IDENTIDADE_CAD")
    for key, val in seeds.items():
        a = np.asarray(val, float)
        if a.shape != (3,) or not np.isfinite(a).all() or abs(a[2]) > 1e-10:
            fail("POSE_REFERENCIA")
        seeds[key] = P.T @ a[:2]
    edges = spec["joints"]
    for e in edges:
        if (e["a"] not in seeds or e["b"] not in seeds or e["a"] == e["b"]
                or e["kind"] not in ("pin", "slider")):
            fail("JUNTA")
        for k in ("pa", "pb"):
            a = np.asarray(e[k], float)
            if a.shape != (2,) or not np.isfinite(a).all():
                fail("ANCORA")
        if e["kind"] == "slider":
            axis = np.asarray(e["axis_a"], float)
            if (axis.shape != (2,) or not np.isfinite(axis).all()
                    or abs(np.linalg.norm(axis)-1)>1e-8
                    or abs(e.get("angle_offset", 0))>1e-10):
                fail("GUIA")
        da = seeds[e["a"]] + P.T @ np.asarray(e["pa"], float)
        db = seeds[e["b"]] + P.T @ np.asarray(e["pb"], float)
        if np.linalg.norm(da-db) > 1e-7:
            fail("ANCORAS_NAO_COINCIDENTES_NA_REFERENCIA")
    entradas = [i for i,e in enumerate(edges) if e["kind"]=="pin"
                and {e["a"],e["b"]} == {ground,driver}]
    if len(entradas) != 1:
        fail("ENTRADA_NAO_E_PINO_DIRETO_A_BASE")
    # Prioridade da entrada e das guias impede transformar slider em connect.
    ordem = sorted(range(len(edges)), key=lambda i:
                   (0 if i==entradas[0] else 1 if edges[i]["kind"]=="slider" else 2, i))
    nomes = ["__e23_world__", ground]
    if nomes[0] in seeds:
        fail("NOME_RESERVADO")
    pais = [-1,0]
    locais = [np.eye(4), M.pose(np.eye(3),seeds[ground])]
    juntas, igualdades, usados = [], [], set()
    entrada = None
    while len(nomes) < len(seeds)+1:
        for i in ordem:
            if i in usados:
                continue
            e = edges[i]
            a,b=e["a"],e["b"]
            if (a in nomes) == (b in nomes):
                continue
            p,c,k = (a,b,"pb") if a in nomes else (b,a,"pa")
            idx=len(nomes)
            nomes.append(c)
            pais.append(nomes.index(p))
            locais.append(M.pose(np.eye(3),seeds[c]-seeds[p]))
            ponto = P.T @ np.asarray(e[k],float)
            axis = n if e["kind"]=="pin" else P.T @ np.asarray(e["axis_a"],float)
            if e["kind"]=="slider" and p!=a:
                axis = -axis
            j=M.Junta(nome=f"edge_{i}",corpo=idx,
                      tipo="hinge" if e["kind"]=="pin" else "slide",
                      eixo=axis,ponto=ponto,limite=None,rigidez=0.,
                      mola_ref=0.,q0=0.)
            if i==entradas[0]:
                entrada=len(juntas)
            juntas.append(j)
            usados.add(i)
            break
        else:
            fail("GRAFO_DESCONECTADO")
    for i,e in enumerate(edges):
        if i in usados:
            continue
        if e["kind"]!="pin":
            fail("FECHAMENTO_PRISMATICO_NAO_SUPORTADO")
        igualdades.append(M.Igualdade("connect",nomes.index(e["a"]),
                          nomes.index(e["b"]),
                          np.r_[P.T@np.asarray(e["pa"]),P.T@np.asarray(e["pb"])]))
    if entrada is None:
        fail("SEM_ENTRADA")
    visuais=[]
    for nome in nomes[1:]:
        vertices, faces=solids[nome].tessellate(0.10,0.15)
        v=np.asarray([p.toTuple() for p in vertices],float)/1000 - seeds[nome]
        f=np.asarray(faces,dtype=int)
        if (v.ndim!=2 or v.shape[1]!=3 or not len(v) or not np.isfinite(v).all()
                or f.ndim!=2 or f.shape[1]!=3 or not len(f)
                or f.min()<0 or f.max()>=len(v)):
            fail("TESSELACAO")
        visuais.append(M.Visual(nomes.index(nome),nome,np.eye(4),v,f,
                                np.array([.72,.76,.79,1.])))
    mont=M.Montagem(nomes,pais,locais,juntas,igualdades,visuais)
    acion={"entrada":{entrada:1.}}
    return mont, acion


def resolver(solids, plane, spec, angles):
    mont, acion=montar(solids,plane,spec)
    alvos=np.asarray(angles,float)
    if alvos.ndim!=1 or not len(alvos) or not np.isfinite(alvos).all():
        fail("ALVOS")
    traj, solver=M.trajetoria(mont,acion,alvos[:,None],mont.q_referencia())
    return mont,traj,solver


def comparar_planar(mont, traj, plane, frames_e1):
    """Oráculo legado independente do E18, sobre a mesma geometria CAD."""
    P=np.asarray(plane,float)
    if not traj or len(traj)!=len(frames_e1):
        fail("QUADROS")
    pos,ang,res=0.,0.,0.
    for (q,info), f in zip(traj,frames_e1):
        X=mont.poses(q)
        for nome, expected in f["poses"].items():
            T=X[mont.indice_corpo(nome)]
            p=P@T[:3,3]
            r=P@T[:3,:3]@P.T
            angle=np.arctan2(r[1,0],r[0,0])
            diff=angle-expected[2]
            pos=max(pos,float(np.linalg.norm(p-np.asarray(expected[:2]))))
            ang=max(ang,abs(float(np.arctan2(np.sin(diff),np.cos(diff)))))
        res=max(res,info["residuo"])
    if pos>1e-6 or ang>1e-5 or res>1e-7:
        fail("DIVERGENCIA_E1")
    return dict(quadros=len(traj),erro_posicao_mm=pos*1000,
                erro_angular_rad=ang,residuo_max=res,
                publish=False,visual_approved=False)
