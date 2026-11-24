"""Real-source proof of E30, without rendering or reimplementing a solver.

The output is a factual evidence packet for the future narrative director.
It describes observed relative movement and verified connectivity, not
a force/dynamics claim, a machine-specific script or a production approval.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from . import grafo_cinematica_e30 as G


def observacoes(graph):
    if (graph.get("schema")!="coringa.cinematica.observada.v1"
            or graph.get("inferencia_causal")!="NAO_INFERIDA"
            or graph.get("publish") is not False):
        raise ValueError("E32-GRAFO")
    mov={x["junta"]:x for x in graph["movimentos"]}
    if len(mov)!=len(graph["movimentos"]):
        raise ValueError("E32-JUNTAS_AMBIGUAS")
    nomes={"rotacao_relativa":"rotação relativa","translacao_relativa":"translação relativa"}
    out=[]
    for r in graph["relacoes"]:
        a,b=mov[r["entrada"]],mov[r["movimento"]]
        if (a.get("papel")!="entrada_prescrita" or b.get("papel")!="movimento_observado"
                or r.get("prova_forca_ou_dinamica") is not False or not r.get("caminho")):
            raise ValueError("E32-RELACAO")
        if a["tipo"] not in nomes or b["tipo"] not in nomes:
            continue
        out.append(dict(tipo="conectividade_com_movimento_observado",
            afirmacao=f"Observa-se {nomes[a['tipo']]} na entrada e {nomes[b['tipo']]} na junta conectada.",
            entrada=a,saida=b,caminho=r["caminho"],
            evidencia="coordenadas de juntas e restrições do modelo",
            limitacao="não é prova de força, carga ou causalidade dinâmica"))
    return out


def step(manifesto,root):
    from . import cad_fechado_e17 as E17
    from . import adaptador_step_e23 as A
    m=json.loads(Path(manifesto).read_text())
    root=Path(root)
    solids,P,origins,pins,s=E17.load(m,root/"loop.step",root/"LICENSE.md")
    angles=np.linspace(0,math.tau,97)
    old=E17.solver.trajectory(s,97,cad_bodies=solids)
    mont,traj,solver=A.resolver(solids,P,s,angles)
    comparison=A.comparar_planar(mont,traj,P,old)
    acion={nome:{int(k):float(c) for k,c in enumerate(linha) if c!=0}
           for nome,linha in zip(solver.nomes,solver.linhas)}
    graph=G.extrair(mont,[q for q,_ in traj],acion)
    return dict(fonte=dict(url=m["source"],arquivos=m["files"],licenca=m["license_name"]),
                comparacao=comparison,grafo=graph,observacoes=observacoes(graph))


def urdf(manifesto,root,modelo_id):
    from . import filme_e18 as F
    from . import multicorpo_e18 as M
    man=json.loads(Path(manifesto).read_text())
    found=[m for m in man["modelos"] if m["id"]==modelo_id]
    if len(found)!=1:
        raise ValueError("E32-ID")
    modelo=found[0]
    m,mont,lidos=F.carregar(modelo,root)
    cache={}
    acion,alvos,q0=F.plano_movimento(mont,modelo,cache,m)
    traj,_=M.trajetoria(mont,acion,alvos,q0)
    qs=[q for q,_ in traj]
    graph=G.extrair(mont,qs,acion)
    serie=np.array([F.medir(mont,q,modelo["medida"],cache["eixo"],qs[0]) for q in qs])
    oracle=modelo["oraculo"]
    if oracle["tipo"]!="curso_mm":
        raise ValueError("E32-ORACULO_NAO_CURSO")
    curso=float(np.ptp(serie)*1000)
    if abs(curso-oracle["valor_mm"])>oracle["tolerancia_mm"]:
        raise ValueError("E32-REFERENCIA_EXTERNA")
    return dict(fonte=dict(man["fonte"],licenca=modelo["licenca"],arquivos_conferidos=lidos),
                comparacao=dict(curso_mm=curso,referencia_mm=oracle["valor_mm"],
                                tolerancia_mm=oracle["tolerancia_mm"]),
                grafo=graph,observacoes=observacoes(graph))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("tipo",choices=["step","urdf"])
    p.add_argument("manifesto")
    p.add_argument("raiz")
    p.add_argument("saida")
    p.add_argument("--id")
    a=p.parse_args()
    r=step(a.manifesto,a.raiz) if a.tipo=="step" else urdf(a.manifesto,a.raiz,a.id)
    if not r["observacoes"]:
        raise ValueError("E32-SEM_OBSERVACAO")
    r.update(publish=False,visual_approved=False)
    Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2))
    print("E32-REAL",json.dumps(dict(tipo=a.tipo,comparacao=r["comparacao"],
          movimentos=r["grafo"]["movimentos"],observacoes=r["observacoes"]),ensure_ascii=False))
