"""Utilidades comuns do motor V4 (caminhos, execução registrada, sondagem de mídia)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MOTOR4 = RAIZ / 'motor4'
IDENT = json.loads((MOTOR4 / 'identidade' / 'identidade.json').read_text(encoding='utf-8'))
W, H, FPS = IDENT['quadro']['w'], IDENT['quadro']['h'], IDENT['quadro']['fps']
CHROME = os.environ.get('CORINGA_CHROME') or shutil.which('google-chrome') or shutil.which('chromium') or '/usr/bin/google-chrome'


def _achar(var: str, nome: str) -> Path:
    """variável de ambiente; senão ~/<nome>; senão ao lado do repositório"""
    if os.environ.get(var):
        return Path(os.environ[var])
    for c in (Path.home() / nome, RAIZ.parent / nome):
        if c.exists():
            return c
    return Path.home() / nome


VENV_MANIM = _achar('CORINGA_VENV_MANIM', '.venv-manim')
VENV_REMBG = _achar('CORINGA_VENV_REMBG', '.venv-rembg')
HF_REGISTRO = _achar('CORINGA_HF_REGISTRO', 'ext/hyperframes')
U2NET_HOME = _achar('U2NET_HOME', '.u2net')
SEM_TELEMETRIA = {'U2NET_HOME': str(U2NET_HOME), 'DO_NOT_TRACK': '1', 'HYPERFRAMES_NO_TELEMETRY': '1', 'DISABLE_TELEMETRY': 'true', 'REMOTION_DISABLE_TELEMETRY': '1'}


class FalhaBackend(RuntimeError):
    """o backend não produziu a cena; a mensagem traz o fim do log (vai para o registro, nunca vira 'aprovado')"""


def rodar(cmd: list, cwd: Path | None = None, env: dict | None = None, timeout: int = 1800, log: Path | None = None) -> dict:
    t0 = time.time()
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, env={**os.environ, **SEM_TELEMETRIA, **(env or {})}, capture_output=True, text=True, timeout=timeout)
    saida = (r.stdout or '') + (r.stderr or '')
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f'$ {" ".join(map(str, cmd))}\n\n{saida}', encoding='utf-8')
    reg = {'cmd': ' '.join(map(str, cmd))[:400], 'rc': r.returncode, 'segundos': round(time.time() - t0, 2)}
    if r.returncode != 0:
        raise FalhaBackend(f"rc={r.returncode} {reg['cmd'][:160]}\n{saida[-1500:]}")
    return reg


def sondar(arq: Path) -> dict:
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height,r_frame_rate,pix_fmt',
                        '-of', 'json', str(arq)], capture_output=True, text=True)
    d = json.loads(r.stdout or '{}')
    v = next((s for s in d.get('streams', []) if s.get('codec_type') == 'video'), {})
    return {'duracao': float((d.get('format') or {}).get('duration') or 0), 'w': v.get('width'), 'h': v.get('height'),
            'fps': v.get('r_frame_rate'), 'pix_fmt': v.get('pix_fmt'), 'audio': any(s.get('codec_type') == 'audio' for s in d.get('streams', []))}


def normalizar_clipe(ent: Path, saida: Path, duracao: float) -> Path:
    """todo clipe de backend entra na linha do tempo como 1080×1920, 30 fps, yuv420p, sem áudio, duração EXATA"""
    rodar(['ffmpeg', '-v', 'error', '-y', '-i', ent, '-vf', f'scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p,tpad=stop_mode=clone:stop_duration=5',
           '-t', f'{duracao:.3f}', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', saida])
    return saida
