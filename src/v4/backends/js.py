"""Backends JS/Python de render paramétrico: Remotion (mapa, 3D, tipografia+Lottie, camada de identidade),
Revideo/Motion Canvas (mecanismos 2D) e Manim (dados de precisão). Todos recebem `params` do contrato e devolvem um MP4
1080×1920 (ou WebM com alfa, no caso da camada)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.v4.util import CHROME, MOTOR4, VENV_MANIM, FalhaBackend, rodar

REMOTION = MOTOR4 / 'remotion'


def remotion(comp: str, props: dict, saida: Path, trab: Path, alfa: bool = False) -> dict:
    trab, saida = Path(trab).resolve(), Path(saida).resolve()
    trab.mkdir(parents=True, exist_ok=True)
    pj = trab / f'props_{comp}.json'
    pj.write_text(json.dumps(props, ensure_ascii=False))
    fmt = ['--codec=vp8', '--pixel-format=yuva420p', '--image-format=png'] if alfa else ['--codec=h264', '--crf=16']
    reg = rodar(['npx', '--prefix', MOTOR4, 'remotion', 'render', 'src/index.ts', comp, saida, f'--props={pj}', '--gl=swangle',
                 f'--browser-executable={CHROME}', f'--public-dir={REMOTION / "public"}', '--concurrency=1', '--timeout=120000', *fmt],
                cwd=REMOTION, timeout=3600, log=trab / f'remotion_{comp}.log')
    if not saida.exists():
        raise FalhaBackend(f'remotion não gerou {saida.name}')
    return {**reg, 'backend': 'remotion', 'composicao': comp, 'versao': '4.0.544'}


def revideo(params: dict, saida: Path, trab: Path) -> dict:
    trab, saida = Path(trab).resolve(), Path(saida).resolve()
    trab.mkdir(parents=True, exist_ok=True)
    pj = trab / 'params_revideo.json'
    pj.write_text(json.dumps(params, ensure_ascii=False))
    reg = rodar(['node', MOTOR4 / 'revideo' / 'render.mjs', pj, saida], cwd=MOTOR4, timeout=1800, log=trab / 'revideo.log')
    if not saida.exists():
        raise FalhaBackend('revideo não gerou o vídeo')
    return {**reg, 'backend': 'revideo', 'cena': params.get('cena', 'nivel_vasos'), 'versao': '0.11.0', 'api': 'Motion Canvas 2D'}


def manim(cena: str, params: dict, saida: Path, trab: Path) -> dict:
    trab, saida = Path(trab).resolve(), Path(saida).resolve()
    trab.mkdir(parents=True, exist_ok=True)
    pj = trab / f'params_manim_{cena}.json'
    pj.write_text(json.dumps(params, ensure_ascii=False))
    media = trab / 'manim_media'
    reg = rodar([VENV_MANIM / 'bin' / 'manim', '-r', '1080,1920', '--fps', '30', '-o', 'saida.mp4', '--media_dir', media, '--disable_caching',
                 '-v', 'WARNING', MOTOR4 / 'manim' / 'cenas.py', cena], env={'CORINGA_PARAMS': str(pj)}, timeout=1800, log=trab / f'manim_{cena}.log')
    f = next(media.rglob('saida.mp4'), None)
    if not f:
        raise FalhaBackend('manim não gerou o vídeo')
    shutil.move(str(f), saida)
    return {**reg, 'backend': 'manim', 'cena': cena, 'versao': '0.19.0'}
