"""Contrato de IDENTIDADE VISUAL, separado da física do mecanismo.

As simulações podem estar fisicamente coerentes e visualmente representar
a máquina ERRADA. Este gate verifica a configuração externa e as relações
do conjunto; não certifica reconhecimento visual a partir de pixels.

Configuração específica: compressor de ar alternativo, elétrico,
com correia e reservatório horizontal. Nem todos os compressores têm tanque.
"""
from __future__ import annotations

from typing import Any

CONFIGURACOES = {
    "compressor_ar_eletrico_tanque_horizontal_correia": {
        "processo": "compressor_alternativo",
        "familia": "compressor_air_tank_belt_drive",
        "required_roles": [
            "receiver_horizontal",
            "electric_motor",
            "compressor_head",
            "finned_cylinder",
            "crankcase",
            "intake_filter",
            "pump_flywheel",
            "motor_pulley",
            "drive_belt",
            "discharge_pipe",
            "suction_valve",
            "discharge_valve",
            "piston_cutaway",
        ],
        "links": [
            ("electric_motor", "drive_belt", "drives"),
            ("drive_belt", "pump_flywheel", "drives"),
            ("intake_filter", "compressor_head", "feeds"),
            ("compressor_head", "discharge_pipe", "exits"),
            ("discharge_pipe", "receiver_horizontal", "feeds"),
            ("crankcase", "receiver_horizontal", "mounted_on"),
            ("electric_motor", "receiver_horizontal", "mounted_on"),
            ("compressor_head", "finned_cylinder", "mounted_on"),
            ("finned_cylinder", "crankcase", "mounted_on"),
        ],
    },
}


def _bbox(raw: Any):
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    if any(type(v) not in (int, float) for v in raw):
        return None
    x, y, w, h = raw
    if not (0 <= x <= 1 and 0 <= y <= 1 and
            0 < w <= 1 and 0 < h <= 1 and
            x + w <= 1.001 and y + h <= 1.001):
        return None
    return (float(x), float(y), float(w), float(h))


def verificar(manifesto: dict) -> dict:
    """Gate conservador: estrutura declarada != pixels analisados."""
    failed = []
    if not isinstance(manifesto, dict):
        return {"gate": "BLOQUEADO", "erros": ["F-SEM-MANIFESTO"]}
    config_id = manifesto.get("configuracao")
    conf = CONFIGURACOES.get(config_id)
    if conf is None:
        return {"gate": "BLOQUEADO", "erros": ["F-CONFIGURACAO-NAO-CADASTRADA"]}
    if manifesto.get("processo") != conf["processo"]:
        failed.append("F-PROCESSO-VISUAL-DIFERENTE")
    if manifesto.get("publicar") is not False:
        failed.append("F-PUBLICACAO-BLOQUEADA")
    parts = manifesto.get("pecas")
    if not isinstance(parts, list):
        return {"gate": "BLOQUEADO", "erros": ["F-SEM-PECAS"]}
    by_id = {}
    by_role = {}
    for part in parts:
        if (not isinstance(part, dict)
                or not isinstance(part.get("id"), str)
                or not isinstance(part.get("papel"), str)
                or part["id"] in by_id
                or part["papel"] in by_role
                or _bbox(part.get("bbox")) is None):
            failed.append("F-PECA-INVALIDA-OU-DUPLICADA")
            continue
        by_id[part["id"]] = part
        by_role[part["papel"]] = part
    missing = sorted(set(conf["required_roles"]) - set(by_role))
    if missing:
        failed.append("F-IDENTIDADE-SEM-COMPONENTES-OBRIGATORIOS")
    links = manifesto.get("ligacoes")
    if not isinstance(links, list):
        failed.append("F-SEM-LIGACOES")
        links = []
    edges = set()
    for connection in links:
        if not isinstance(connection, dict):
            failed.append("F-LIGACAO-INVALIDA")
            continue
        a, b, kind = (connection.get("a"), connection.get("b"),
                      connection.get("tipo"))
        if (not isinstance(a, str) or not isinstance(b, str)
                or not isinstance(kind, str) or
                a not in by_id or b not in by_id):
            failed.append("F-LIGACAO-SEM-PECAS")
            continue
        edges.add((by_id[a]["papel"], by_id[b]["papel"], kind))
    missing_edges = sorted(set(conf["links"]) - edges)
    if missing_edges:
        failed.append("F-CAMINHO-MECANICO-INCOMPLETO")
    # Uma garrafa minúscula colada de lado não é reservatório horizontal.
    if {"receiver_horizontal", "electric_motor", "finned_cylinder",
        "compressor_head", "crankcase"}.issubset(by_role):
        tank = _bbox(by_role["receiver_horizontal"]["bbox"])
        motor = _bbox(by_role["electric_motor"]["bbox"])
        cylinder = _bbox(by_role["finned_cylinder"]["bbox"])
        head = _bbox(by_role["compressor_head"]["bbox"])
        crankcase = _bbox(by_role["crankcase"]["bbox"])
        if tank and motor and cylinder and head and crankcase:
            if not (tank[2] >= cylinder[2] * 2.0 and
                    tank[2] > tank[3] * 1.8 and
                    tank[1] > crankcase[1] + crankcase[3] * .65):
                failed.append("F-RESERVATORIO-SEM-PROPORCAO-OUPOSICAO")
            if not (head[1] <= cylinder[1] and
                    cylinder[1] + cylinder[3] * .55 < tank[1] and
                    motor[0] + motor[2] < head[0] + head[2]):
                failed.append("F-CONJUNTO-MONTADO-INCOERENTE")
    errors = list(dict.fromkeys(failed))
    if errors:
        return {
            "gate": "BLOQUEADO",
            "erros": errors,
            "pecas_faltantes": missing,
            "ligacoes_faltantes": [list(x) for x in missing_edges],
            "publicar": False,
        }
    return {
        "gate": "ESTRUTURA_DECLARADA_OK_VISUAL_NAO_CERTIFICADO",
        "erros": [],
        "pecas_faltantes": [],
        "ligacoes_faltantes": [],
        "validacao_por_pixels": "NAO_REALIZADA",
        "licenca": "NAO_CHECADA_POR_ESTE_GATE",
        "revisao_humana": "PENDENTE",
        "publicar": False,
    }
