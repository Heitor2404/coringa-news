"""Select evidence-backed alternative representations; never relabel an
invalid CAD simulation as a valid industrial mechanism.

This is a private planning gate, not a geometry generator or publication gate.
No model names, no inference from titles, no external execution.
"""
import re
import math

HASH=re.compile(r"[a-f0-9]{64}\Z")
KINDS=("cad_real","parametrico_fundamentado","esquema_cinematico_2d")

def _sha(x):
    return isinstance(x,str) and bool(HASH.fullmatch(x))

def avaliar(c):
    if not isinstance(c,dict) or c.get("tipo") not in KINDS:
        return "TIPO_DESCONHECIDO"
    if c.get("identidade_verificada") is not True:
        return "IDENTIDADE_NAO_VERIFICADA"
    if not _sha(c.get("fonte_sha256")) or not isinstance(c.get("fonte_url"),str) or not c["fonte_url"].startswith("https://"):
        return "PROCEDENCIA_INSUFICIENTE"
    if c.get("licenca_candidata") not in ("permissiva","reciproca"):
        return "LICENCA_INSUFICIENTE"
    if c.get("juntas_fundamentadas") is not True or c.get("movimento_fundamentado") is not True:
        return "RELACOES_INSUFICIENTES"
    if c.get("tipo")=="cad_real":
        if c.get("estado")!="VALIDADO_TECNICAMENTE_SEM_HOMOLOGACAO_VISUAL":
            return "CAD_SEM_VALIDACAO_TECNICA"
        if c.get("verificacao_contato") not in ("SEM_INTERFERENCIA_BREP_NA_AMOSTRA","SEM_COLISAO_NOVA_NA_AMOSTRA"):
            return "CAD_CONTATO_NAO_VERIFICADO"
        if c.get("sobreposicao_inicial_fonte") is not False:
            return "CAD_ORIGEM_NAO_VERIFICADA"
    else:
        if c.get("apenas_principio") is not True:
            return "REPRESENTACAO_NAO_DECLARADA"
        if c.get("tipo")=="parametrico_fundamentado" and c.get("dimensoes_fundamentadas") is not True:
            return "DIMENSOES_INSUFICIENTES"
        if c.get("solver_verificado") is not True:
            return "SOLVER_NAO_VERIFICADO"
    return "ELEGIVEL_APENAS_REVISAO_PRIVADA"

def planejar(candidatos,exige_contorno_industrial=False,*,alvo):
    if not isinstance(candidatos,list) or type(exige_contorno_industrial) is not bool:
        raise ValueError("E40-CONTRATO")
    if not isinstance(alvo,str) or not alvo.strip() or len(alvo)>150:
        raise ValueError("E40-ALVO")
    rows=[]
    for i,c in enumerate(candidatos):
        status=avaliar(c)
        if isinstance(c,dict) and c.get("alvo")!=alvo:
            status="ALVO_DIFERENTE_OU_NAO_IDENTIFICADO"
        tipo=c.get("tipo") if isinstance(c,dict) else None
        if status.startswith("ELEGIVEL") and exige_contorno_industrial and tipo!="cad_real":
            status="PRINCIPIO_NAO_SUBSTITUI_CONTORNO_INDUSTRIAL"
        rows.append(dict(indice=i,tipo=tipo,status=status))
    eligible=[r for r in rows if r["status"]=="ELEGIVEL_APENAS_REVISAO_PRIVADA"]
    choice=min(eligible,key=lambda r:KINDS.index(r["tipo"])) if eligible else None
    return dict(schema="coringa.rota.explicativa.v1",alvo=alvo,decisao=choice,
        candidatos=rows,resultado="REVISAO_PRIVADA" if choice else "SEM_REPRESENTACAO_FUNDAMENTADA",
        publish=False,visual_approved=False,direitos_publicacao="NAO_AVALIADOS")
