"""Evidence from actual joint coordinates and explicit constraints.

Builds a directed graph of downstream joints plus explicit equality links.
A common fixed base is NOT evidence that two joints are coupled.
Paths describe kinematic connectivity, never force, torque, causality
under load or an inferred mechanism from a topic name.
"""
from collections import deque
import numpy as np


def fail(code):
    raise ValueError("E30-"+code)


def extrair(mont,qs,acion,fps=30,indices=None):
    q=np.asarray(qs,float)
    if (q.ndim!=2 or q.shape[1]!=mont.nq or len(q)<2
            or not np.isfinite(q).all() or not np.isfinite(fps) or fps<=0):
        fail("TRAJETORIA")
    if indices is None:
        indices=np.arange(len(q))
    ix=np.asarray(indices)
    if (ix.ndim!=1 or ix.dtype.kind not in "iu" or len(ix)<2
            or ix[0]<0 or ix[-1]>=len(q) or (np.diff(ix)<=0).any()):
        fail("FRAMES")
    q=q[ix]
    by_body={}
    for i,j in enumerate(mont.juntas):
        by_body.setdefault(j.corpo,[]).append(i)
    def nearest(b,include=True):
        seen=set()
        if not include:
            b=mont.pai[b]
        while b>=0:
            if b in seen or b>=len(mont.corpos):
                fail("ARVORE")
            seen.add(b)
            if b in by_body:
                return by_body[b]
            b=mont.pai[b]
        return []
    adj={i:[] for i in range(len(mont.juntas))}
    def edge(a,b,t,bi=False):
        if a==b:
            return
        item=(b,t)
        if item not in adj[a]:
            adj[a].append(item)
        if bi and (a,t) not in adj[b]:
            adj[b].append((a,t))
    for i,j in enumerate(mont.juntas):
        for p in nearest(j.corpo,False):
            edge(p,i,"descendente_na_arvore")
    # Multiple coordinates on the same moving body: simultaneous attachment,
    # not an inference about which coordinate drives another.
    for group in by_body.values():
        for a in group:
            for b in group:
                edge(a,b,"mesmo_corpo")
    for e in mont.igualdades:
        if e.tipo=="joint":
            a,b=mont.coords[e.a].junta,mont.coords[e.b].junta
            edge(a,b,"igualdade_de_juntas",True)
        elif e.tipo in ("connect","weld"):
            for a in nearest(e.a):
                for b in nearest(e.b):
                    edge(a,b,"fechamento_"+e.tipo,True)
        else:
            fail("IGUALDADE")
    entradas={}
    for nome,coefs in acion.items():
        if not isinstance(nome,str) or not isinstance(coefs,dict):
            fail("ACIONADOR")
        for k,coef in coefs.items():
            if (not isinstance(k,(int,np.integer)) or not 0<=k<mont.nq
                    or not np.isfinite(coef)):
                fail("ACIONADOR_COORDENADA")
            if coef!=0:
                entradas.setdefault(mont.coords[k].junta,[]).append(nome)
    if not entradas:
        fail("SEM_ENTRADA")
    movimentos={}
    nao_classificados=[]
    for i,j in enumerate(mont.juntas):
        if j.tipo=="hinge":
            v=q[:,j.adr]-q[0,j.adr]
            unidade,classe,eps="rad","rotacao_relativa",1e-6
        elif j.tipo=="slide":
            v=(q[:,j.adr]-q[0,j.adr])*1000
            unidade,classe,eps="mm","translacao_relativa",1e-3
        elif j.tipo=="ball":
            # Rotation-vector components are not independent hinge angles.
            nao_classificados.append(dict(junta=j.nome,motivo="rotacao_3d_sem_eixo_unico"))
            continue
        else:
            fail("TIPO_JUNTA")
        amplitude=float(np.ptp(v))
        if amplitude<=eps:
            continue
        kmin,kmax=int(np.argmin(v)),int(np.argmax(v))
        movimentos[i]=dict(junta=j.nome,corpo=mont.corpos[j.corpo],
            tipo=classe,unidade=unidade,minimo=float(v[kmin]),maximo=float(v[kmax]),
            amplitude=amplitude,frame_min=kmin,frame_max=kmax,
            tempo_min_s=kmin/fps,tempo_max_s=kmax/fps,
            acionadores=sorted(set(entradas.get(i,[]))),
            papel="entrada_prescrita" if i in entradas else "movimento_observado")
    relacoes=[]
    for origem in sorted(entradas):
        if origem not in movimentos:
            continue
        caminhos={origem:[]}
        fila=deque([origem])
        while fila:
            a=fila.popleft()
            for b,t in sorted(adj[a]):
                if b not in caminhos:
                    caminhos[b]=caminhos[a]+[dict(de=mont.juntas[a].nome,
                         para=mont.juntas[b].nome,tipo=t)]
                    fila.append(b)
        for alvo in sorted(movimentos):
            if alvo in entradas or alvo not in caminhos:
                continue
            path=caminhos[alvo]
            relacoes.append(dict(entrada=movimentos[origem]["junta"],
                movimento=movimentos[alvo]["junta"],caminho=path,
                classe="conectividade_cinematica_com_movimento_observado",
                prova_forca_ou_dinamica=False))
    return dict(schema="coringa.cinematica.observada.v1",fps=float(fps),quadros=len(q),
                indices_pose=ix.tolist(),movimentos=list(movimentos.values()),
                relacoes=relacoes,juntas_nao_classificadas=nao_classificados,
                inferencia_causal="NAO_INFERIDA",publish=False,visual_approved=False)
