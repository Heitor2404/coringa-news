"""Parâmetros do ATLAS derivados da engenharia reversa da referência (atlas_parametros.json, entregue pelo Heitor) e da
conferência própria da câmera (atlas_camera_verificada.json). Só o que a cópia 512×910 permite medir: nada de fonte,
traço SVG, curva de easing ou zoom de tile "originais". Também concentra o manifesto de atribuição cartográfica.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
PAR = json.loads((AQUI / 'atlas_parametros.json').read_text(encoding='utf-8'))
CAM = json.loads((AQUI / 'atlas_camera_verificada.json').read_text(encoding='utf-8'))
MANIFESTO = json.loads((RAIZ / 'motor4' / 'formatos' / 'dados' / 'atribuicoes.json').read_text(encoding='utf-8'))


def porta(caixa_512: list[float]) -> list[int]:
    """[x0, y0, x1, y1] da cópia 512×910 → [x, y, w, h] em 1080×1920 (escala do relatório)"""
    sx, sy = PAR['port_scale_to_1080x1920']['x'], PAR['port_scale_to_1080x1920']['y']
    x0, y0, x1, y1 = caixa_512
    return [round(x0 * sx), round(y0 * sy), round((x1 - x0) * sx), round((y1 - y0) * sy)]


def legenda_centro_ref() -> int:
    a, b = PAR['pixel_regions_512x910_estimates']['caption_y']
    return round((a + b) / 2 * PAR['port_scale_to_1080x1920']['y'])


# câmera: zoom/s do MapLibre a partir da escala por segundo medida (zoom +1 = 2×)
DERIVA = {
    'aproxima': round(math.log2(CAM['aproximacao_escala_por_s_mediana']), 4),   # ≈ +0,034 zoom/s (≈ +2,4 %/s)
    'fixo': 0.0,                                                               # a referência PARA a câmera quando o dado muda
    'recua': round(math.log2(CAM['recuo_final_escala_por_s_mediana']), 4),     # ≈ −0,067 zoom/s (fecho volta ao largo)
}


def deriva(movimento: str | None) -> float:
    return DERIVA.get(movimento or 'fixo', 0.0)


def proibido(texto: str) -> str | None:
    t = (texto or '').lower()
    return next((p for p in MANIFESTO['proibidos']['padroes'] if p.lower() in t), None)


def datasets() -> dict:
    return MANIFESTO['datasets']
