"""E21 — classificação de QA independente de código de render e de nomes de máquinas.

O solver convergir, um oráculo externo estar correto e um vídeo estar
homologado são perguntas distintas. Nunca promover um resultado numérico
a "aprovado para publicar". O critério externo é sempre o registrado na
fonte; a função não pode alterar ou aumentar tolerâncias.
"""
from __future__ import annotations

import math
from numbers import Real

SCHEMA = "coringa-e21-gates-independentes-v1"


def _finito(x):
    return not isinstance(x, bool) and isinstance(x, Real) and math.isfinite(float(x))


def classificar(qa):
    """Retorna novo dicionário; não edita nem arredonda medidas originais."""
    if not isinstance(qa, dict):
        raise ValueError("E21-QA-OBJETO")
    r = dict(qa)
    video = r.get("verificacao_video")
    executado = (
        "motivo" not in r
        and _finito(r.get("residuo_max"))
        and 0 <= float(r["residuo_max"]) <= 1e-7
        and isinstance(video, dict)
        and type(video.get("quadros")) is int and video["quadros"] >= 3
        and type(video.get("pico_pixels_mudados")) is int
        and video["pico_pixels_mudados"] >= 300
    )
    r["estado_execucao"] = "PASS" if executado else "BLOCKED"

    oracle = r.get("oraculo_fabricante")
    if oracle is None:
        external = "SEM_REFERENCIA"
    elif not isinstance(oracle, dict):
        external = "INDETERMINADO"
    elif type(oracle.get("dentro_da_tolerancia")) is not bool:
        external = "INDETERMINADO"
    else:
        external = "APROVADO" if oracle["dentro_da_tolerancia"] else "REPROVADO"

    # Não considerar "sem novos contatos" equivalente a prova de contato
    # industrial: interseções já existentes na origem são reportadas à parte.
    interferencias = r.get("interferencias")
    if not executado or not isinstance(interferencias, dict):
        contact = "NAO_VERIFICADO"
    elif any(not isinstance(v, list) for v in interferencias.values()):
        contact = "NAO_VERIFICADO"
    elif any(v for v in interferencias.values()):
        contact = "COLISAO_NOVA_DETECTADA"
    else:
        contact = "SEM_COLISAO_NOVA_NA_AMOSTRA"

    if not executado:
        state = "BLOQUEADO_NA_EXECUCAO"
    elif contact == "COLISAO_NOVA_DETECTADA":
        state = "REPROVADO_CONTATO_NOVO"
    elif external == "REPROVADO":
        state = "REPROVADO_REFERENCIA_EXTERNA"
    elif external == "INDETERMINADO":
        state = "BLOQUEADO_ORACULO_INVALIDO"
    elif external == "SEM_REFERENCIA":
        state = "SEM_REFERENCIA_EXTERNA"
    else:
        state = "VALIDADO_TECNICAMENTE_SEM_HOMOLOGACAO_VISUAL"

    # A geração E18 é um laboratório. Campo "visual_approved" eventualmente
    # marcado true por outro código nunca é suficiente para publicidade.
    r["schema_gates"] = SCHEMA
    r["validacao_externa"] = external
    r["verificacao_contato"] = contact
    r["sobreposicao_inicial_fonte"] = bool(
        r.get("sobreposicao_na_referencia_da_fonte"))
    r["homologacao_visual"] = "NAO_HOMOLOGADO"
    r["homologacao_documental"] = "NAO_AVALIADO_60S_NARRACAO"
    r["publish"] = False
    r["visual_approved"] = False
    r["liberado_para_publicacao"] = False
    r["estado"] = state
    return r


def resumo(modelos):
    """Qualidade externa separada da saúde do pipeline."""
    if not isinstance(modelos, list):
        raise ValueError("E21-RELATORIO")
    contagem = {k: sum(m.get("validacao_externa") == k for m in modelos)
                for k in ("APROVADO", "REPROVADO", "SEM_REFERENCIA", "INDETERMINADO")}
    return {
        "schema": SCHEMA,
        "total": len(modelos),
        "execucoes_tecnicas_concluidas": sum(
            m.get("estado_execucao") == "PASS" for m in modelos),
        "oraculos_externos": contagem,
        "qualidade_externa_100pct": contagem["APROVADO"] == len(modelos),
        "bloqueados_por_oraculo": [
            {"id": m.get("id"), "medido_mm": m.get("oraculo_fabricante", {}).get("medido_mm"),
             "referencia_mm": m.get("oraculo_fabricante", {}).get("valor_mm"),
             "tolerancia_mm": m.get("oraculo_fabricante", {}).get("tolerancia_mm")}
            for m in modelos if m.get("validacao_externa") == "REPROVADO"],
        "todos_visualmente_homologados": False,
        "publish": False,
    }
