"""Prova privada de STEP registrado no solver E18 e seu renderer compartilhado.

Sem MuJoCo como parser de STEP. A prova antiga E1 é oráculo de regressão;
as poses novas passam também pelo audit de sólidos e pinos do CAD original.
Não é narração ATLAS nem homologação visual.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from . import multicorpo_e18 as M
from . import adaptador_step_e23 as A
from . import filme_e18 as F
from . import cad_fechado_e17 as E17
from . import metrologia_e22 as D


def frames_planar(mont, traj, plane, solver, angles):
    frames=[]
    for (q,info),angle in zip(traj,angles):
        poses={}
        X=mont.poses(q)
        for nome in mont.corpos[1:]:
            T=X[mont.indice_corpo(nome)]
            p=plane@T[:3,3]
            r=plane@T[:3,:3]@plane.T
            poses[nome]=[float(p[0]),float(p[1]),float(np.arctan2(r[1,0],r[0,0]))]
        J=M.jacobiano(lambda x:solver.restricoes(x,[angle]),q)
        rank=int(np.linalg.matrix_rank(J,tol=1e-8))
        if rank!=mont.nq:
            raise ValueError("E25-POSTO_INSUFICIENTE")
        frames.append(dict(poses=poses,jacobian_rank=rank))
    return frames


def gerar(manifesto_path, step, license_file, saida):
    manifesto=json.loads(Path(manifesto_path).read_text())
    solids,P,origins,pins,spec=E17.load(manifesto,step,license_file)
    # A cadência é de laboratório. As 97 poses são as mesmas da prova E17.
    angles=np.linspace(0,math.tau,97)
    if spec["driver"].get("theta0")!=0 or spec["duration_s"]!=4:
        raise ValueError("E25-PERFIL_NAO_SUPORTADO")
    old=E17.solver.trajectory(spec,len(angles),cad_bodies=solids)
    mont,traj,solver=A.resolver(solids,P,spec,angles)
    qa=A.comparar_planar(mont,traj,P,old)
    frames=frames_planar(mont,traj,P,solver,angles)
    qa["auditoria_solidos_step"]=E17.audit(manifesto,solids,P,origins,pins,frames)
    qs=[q for q,_ in traj]
    direction=np.asarray(manifesto["guide_direction"],float)
    idx=mont.indice_corpo(manifesto["measurement_body"])
    coord=np.array([mont.poses(q)[idx][:3,3]@direction for q in qs])
    serie=coord-coord[0]
    medida=dict(tipo="deslocamento",rotulo="Deslocamento em relação à pose inicial")
    qa.update(id="step_e25",mobilidade_max=max(info["mobilidade"] for _,info in traj),
              referencia_projeto=dict(fonte=manifesto["source"],
                  curso_mm=manifesto["reference_stroke_mm"],tolerancia_mm=.03,
                  curso_medido_mm=float(np.ptp(serie)*1000)),
              metrologia_e22=D.diagnostico(mont,qs,medida,serie),
              natureza="Montagem STEP de projeto; sem ensaio físico em bancada",
              validacao_cad="AMOSTRAL",homologacao_visual="NAO_HOMOLOGADO",
              publish=False,visual_approved=False)
    modelo=dict(id="step_e25",titulo=manifesto["title"],
                credito="Projeto CAD: "+manifesto["credit"],
                licenca=manifesto["license_name"],
                natureza="STEP verificado · prévia técnica de projeto")
    # Exatamente o renderer E18–E24, sem uma arte por tipo de máquina.
    qa=F.renderizar_trajetoria(mont,{nome:{int(k):float(c) for k,c in enumerate(linha) if c!=0}
                      for nome,linha in zip(solver.nomes,solver.linhas)},
        qs,medida,serie,qa,modelo,Path(saida),varrido="entrada")
    Path(saida,"QA.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2))
    print("E25-STEP",json.dumps(qa,ensure_ascii=False))
    return qa


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifesto")
    p.add_argument("step")
    p.add_argument("license")
    p.add_argument("saida")
    a=p.parse_args()
    gerar(a.manifesto,a.step,a.license,a.saida)
