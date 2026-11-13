"""EQUIVALÊNCIAS DERIVADAS (V2.1): contextualizar um número SEM inventar comparação.

Só conversões exatas de unidade + referências de tamanho conhecidas (capacidades.REFERENCIAS_M, fonte Wikipédia).
Ex.: 200 milhões de litros = 200.000 m³ = um cubo de ≈ 58,5 m de lado (mais alto que o Cristo Redentor com pedestal,
38 m). A piscina olímpica entra só pelo volume NOMINAL (50 × 25 × 2 m = 2.500 m³) e é rotulada assim.
"""
from __future__ import annotations

import re

from src.v2.capacidades import REFERENCIAS_M

MULT = {'mil': 1e3, 'milhao': 1e6, 'milhoes': 1e6, 'milhão': 1e6, 'milhões': 1e6, 'bilhao': 1e9, 'bilhoes': 1e9, 'bilhão': 1e9, 'bilhões': 1e9}
PISCINA_M3 = 2500.0     # nominal: 50 × 25 × 2 m


def _num_unidade(valor: float, unidade: str) -> tuple[float, str]:
    u = (unidade or '').lower().strip()
    fator = 1.0
    for k, f in MULT.items():
        if re.search(rf'\b{k}\b', u):
            fator = f
            u = re.sub(rf'\b{k}\b( de)?', '', u).strip()
            break
    return float(valor) * fator, u


def volume_m3(valor: float, unidade: str) -> float | None:
    v, u = _num_unidade(valor, unidade)
    if re.search(r'\b(litros?|l)\b', u):
        return v / 1000
    if re.search(r'm³|m3|metros? c[úu]bicos?', u):
        return v
    return None


def equivalencia(valor: float, unidade: str) -> dict | None:
    """Parâmetro `equivalencia` do numero.animado (tipo 'cubo') para volumes; None se a unidade não for volume."""
    m3 = volume_m3(valor, unidade)
    if not m3:
        return None
    lado = round(m3 ** (1 / 3), 1)
    ref = min(REFERENCIAS_M, key=lambda r: abs(r[1] - lado))
    piscinas = m3 / PISCINA_M3
    txt = f'um cubo de ≈ {int(lado + .5)} m de lado'
    return {'tipo': 'cubo', 'lado_m': round(lado, 1), 'ref': {'nome': ref[0], 'altura_m': ref[1], 'forma': ref[2]},
            'texto': txt, 'apoio': f'≈ {piscinas:,.0f} piscinas olímpicas (volume nominal 50×25×2 m)'.replace(',', '.'),
            'calculo': f'{m3:,.0f}'.replace(',', '.') + f' m³ = ({lado:.1f} m)³'.replace('.', ',')}
