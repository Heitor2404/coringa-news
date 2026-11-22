"""Extrai deslocamento de uma referência ANIMADA mediante marcador anotado.

Não identifica válvulas nem etapas: só extrai articulação e geometria visual
de GIF real com SHA-256, correlação, repetição e ajuste cinemático. O ROI é
anotado manualmente por REFERÊNCIA; nenhum cálculo depende de 'motor'/'pistão'.
Sem Gemini e sem acesso à rede. Requer opencv-python-headless, numpy e scipy.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy.optimize import least_squares


def digest(path: Path) -> str:
    hash_obj = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            hash_obj.update(part)
    return hash_obj.hexdigest()


def modelo(params, indices, total, giros):
    raio, biela, eixo_y, fase = params
    theta = 2 * math.pi * giros * np.asarray(indices) / total + fase
    return eixo_y - raio * np.cos(theta) - np.sqrt(
        biela ** 2 - raio ** 2 * np.sin(theta) ** 2
    )


def extrair(arquivo: Path, config: dict) -> dict:
    arquivo = Path(arquivo)
    if not arquivo.is_file() or arquivo.suffix.lower() != ".gif":
        raise ValueError("F-REFERENCIA-GIF-LOCAL")
    sha = digest(arquivo)
    if sha != config.get("sha256"):
        raise ValueError("F-REFERENCIA-ORIGEM-NAO-CONFERE")

    roi = config["search_roi"]
    box = config["template_bbox"]
    if not (len(roi) == 4 and len(box) == 4 and
            all(type(q) is int for q in roi + box)):
        raise ValueError("F-ANOTACAO-REGIAO")
    left, top, right, bottom = roi
    x1, y1, x2, y2 = box
    if not (left <= x1 < x2 <= right and top <= y1 < y2 <= bottom):
        raise ValueError("F-ANOTACAO-FORA-DA-REGIAO")

    frames, durations = [], []
    with Image.open(arquivo) as img:
        if img.format != "GIF" or img.n_frames < 24 or img.n_frames > 300:
            raise ValueError("F-ANIMACAO-INSUFICIENTE")
        width, height = img.size
        if not (100 <= width <= 2048 and 100 <= height <= 2048 and
                right <= width and bottom <= height):
            raise ValueError("F-RESOLUCAO-OU-ROI")
        for i in range(img.n_frames):
            img.seek(i)
            frames.append(cv2.cvtColor(
                np.asarray(img.convert("RGB")), cv2.COLOR_RGB2GRAY))
            durations.append(float(img.info.get("duration") or 100) / 1000.0)

    anchor = config.get("keyframe", 0)
    if not isinstance(anchor, int) or not 0 <= anchor < len(frames):
        raise ValueError("F-KEYFRAME")
    template = frames[anchor][y1:y2, x1:x2]
    if template.std() < 6:
        raise ValueError("F-REFERENCIA-MARCADOR-SEM-TEXTURA")

    correlations, positions = [], []
    for frame in frames:
        correlation = cv2.matchTemplate(
            frame[top:bottom, left:right], template, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(correlation)
        positions.append([
            round(left + loc[0] + (x2 - x1) / 2.0, 3),
            round(top + loc[1] + (y2 - y1) / 2.0, 3),
        ])
        correlations.append(float(score))
    threshold = float(config.get("min_correlation", .75))
    if min(correlations) < threshold:
        raise ValueError("F-MARCADOR-PERDIDO")

    xs = np.array([p[0] for p in positions])
    ys = np.array([p[1] for p in positions])
    total = len(ys)
    if max(xs) - min(xs) > 3:
        raise ValueError("F-MARCADOR-NAO-CENTRALIZADO")
    curso = float(max(ys) - min(ys))
    if curso < 16:
        raise ValueError("F-PISTAO-SEM-CURSO")

    giros = config.get("revolutions")
    if type(giros) is not int or not 1 <= giros <= 4:
        raise ValueError("F-REVOLUCOES-NAO-VERIFICADAS")
    init = [curso / 2.0, curso * 2.0, float(np.median(ys) + curso * 2.4), 0.0]
    fit = least_squares(
        lambda p: modelo(p, np.arange(total), total, giros) - ys,
        init,
        bounds=([4.0, curso * .6, 100.0, -.7],
                [curso, 300.0, 700.0, .7]),
        max_nfev=1200,
    )
    raio, biela, eixo_y, fase = [float(x) for x in fit.x]
    if biela <= raio * 1.25:
        raise ValueError("F-BIELA-MENOR-QUE-CURSO")
    errors = np.abs(modelo(fit.x, np.arange(total), total, giros) - ys)
    mae = float(errors.mean())
    if mae > float(config.get("max_fit_mae_px", 1.5)) or errors.max() > 4.0:
        raise ValueError("F-MOVIMENTO-NAO-REPRESENTAVEL-POR-SLIDER-CRANK")

    for stroke in range(giros * 2):
        start = round(stroke * total / (giros * 2))
        stop = round((stroke + 1) * total / (giros * 2))
        delta = ys[min(stop, total - 1)] - ys[start]
        if abs(delta) < curso * .58 or (delta > 0) != (stroke % 2 == 0):
            raise ValueError("F-FASES-CINEMATICAS-INVALIDAS")

    return {
        "schema": "reference-first-measured-motion-v1",
        "origem_sha256": sha,
        "referencia_id": config["referencia_id"],
        "processo_declarado": config["processo"],
        "proveniencia": "MEDICAO_TEMPLATE_CV2_COM_ROI_ANOTADA_MANUALMENTE",
        "quadros": total,
        "duracao_s": round(sum(durations), 3),
        "frames_por_giro": total / giros,
        "revolucoes": giros,
        "marcador": {"bbox": box, "busca": roi, "frame_origem": anchor},
        "x_medio": round(float(xs.mean()), 3),
        "posicoes_y_px": list(map(float, ys)),
        "qualidade_correlacao": {
            "min": round(min(correlations), 4),
            "media": round(float(np.mean(correlations)), 4),
        },
        "ajuste_geometrico": {
            "raio_px": round(raio, 4),
            "biela_px": round(biela, 4),
            "eixo_y_px": round(eixo_y, 4),
            "fase_rad": round(fase, 6),
            "erro_medio_px": round(mae, 4),
            "erro_max_px": round(float(errors.max()), 4),
        },
        "sinais_somente_mecanicos": True,
        "valvulas_validadas": False,
        "reconstrucao_original": False,
        "publicar": False,
    }


def executar(arquivo: Path, config: dict, saida: Path) -> dict:
    result = extrair(arquivo, config)
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    Path(saida).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
    )
    return result


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("arquivo")
    p.add_argument("config_json")
    p.add_argument("saida")
    args = p.parse_args()
    result = executar(Path(args.arquivo),
                      json.loads(Path(args.config_json).read_text()),
                      Path(args.saida))
    print(json.dumps({
        "quadros": result["quadros"],
        "mae": result["ajuste_geometrico"]["erro_medio_px"],
        "estado": "MEDIDO",
    }, ensure_ascii=False))
