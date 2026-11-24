"""Evidence-bound transmission summaries and process-local B-rep reuse.

Never claim manufacturer validation; angle ratio is observed on the solver
trajectory. Contact audit remains separate and blocks production.
"""
import math
import re

def formas(leitura,ids):
    corpos=leitura["corpos"]
    result={}
    for i in set(ids):
        if type(i) is not int or not 0<=i<len(corpos):
            raise ValueError("E42-SOLIDO")
        c=corpos[i]
        if c.indice!=i or c.forma is None:
            raise ValueError("E42-ORDEM_SOLIDO")
        result[i]=c.forma
    return result

def transmissao(entrada,saida,razao,fps):
    import numpy as np
    a,b=np.asarray(entrada,float),np.asarray(saida,float)
    if (a.ndim!=1 or b.shape!=a.shape or len(a)<3 or not np.isfinite(a).all()
            or not np.isfinite(b).all() or not math.isfinite(razao) or abs(razao)<1e-12
            or fps!=30):
        raise ValueError("E42-TRAJETORIA")
    a=a-a[0];b=b-b[0]
    if abs(a[-1])<1e-8 or np.max(np.abs(b-razao*a))>1e-7:
        raise ValueError("E42-RAZAO_NAO_REPRODUZIDA")
    return dict(schema="coringa.transmissao.observada.v1",fps=fps,quadros=len(a),
        entrada_rad=float(a[-1]),saida_rad=float(b[-1]),razao=float(b[-1]/a[-1]),
        max_residuo_razao_rad=float(np.max(np.abs(b-razao*a))),
        natureza="relacao_observada_na_trajetoria_do_modelo",
        publish=False)

def cues(t,n):
    if (not isinstance(t,dict) or t.get("schema")!="coringa.transmissao.observada.v1"
            or t.get("publish") is not False or t.get("fps")!=30 or t.get("quadros")!=n
            or t.get("natureza")!="relacao_observada_na_trajetoria_do_modelo"):
        raise ValueError("E42-CONTRATO")
    a,b,k,e=(t.get(x) for x in ("entrada_rad","saida_rad","razao","max_residuo_razao_rad"))
    if any(type(x) not in (float,int) or not math.isfinite(x) for x in (a,b,k,e)):
        raise ValueError("E42-MEDIDA")
    if abs(a)<1e-8 or abs(b)<1e-8 or not 0<=e<=1e-7 or abs(b-k*a)>1e-7:
        raise ValueError("E42-RAZAO")
    f=lambda x,d:format(x,f".{d}f").replace(".",",")
    ratio=abs(a/b)
    # These are totals for the entire simulation, not claims at a given frame.
    rotulo=f"Redução observada: {f(ratio,1)}:1" if ratio>=1 else f"Multiplicação: {f(1/ratio,1)}:1"
    return [dict(at=0,label=rotulo,kind="fact"),
            dict(at=(n//2)/30,label=f"Totais: {f(a/(2*math.pi),1)} voltas → {f(math.degrees(b),1)}°",kind="fact")]
