"""Marcos editoriais: fonte declarada não equivale a verificação factual."""
import math

def numero(x):
    return type(x) in (int,float) and math.isfinite(x)

def validar_marcos(marcos,modo,t0,t1):
    if modo not in ("degrau","linear_ilustrativa"):
        raise ValueError("E200-INTERPOLACAO")
    if not numero(t0) or not numero(t1) or t0>=t1:
        raise ValueError("E200-INTERVALO")
    if not isinstance(marcos,list) or not 2<=len(marcos)<=100:
        raise ValueError("E200-MARCOS")
    prev=None
    for m in marcos:
        if not isinstance(m,dict) or not numero(m.get("t")) or not numero(m.get("fracao")):
            raise ValueError("E200-MARCO")
        if not 0<=m["fracao"]<=1 or not t0<=m["t"]<=t1:
            raise ValueError("E200-LIMITES")
        if not isinstance(m.get("fonte"),str) or not m["fonte"].strip():
            raise ValueError("E200-FONTE")
        if prev and (m["t"]<=prev["t"] or m["fracao"]<prev["fracao"]):
            raise ValueError("E200-ORDEM")
        prev=m
    if (abs(marcos[0]["t"]-t0)>1e-8 or abs(marcos[-1]["t"]-t1)>1e-8 or
        marcos[0]["fracao"]!=0 or marcos[-1]["fracao"]!=1):
        raise ValueError("E200-EXTREMOS")
    return True
