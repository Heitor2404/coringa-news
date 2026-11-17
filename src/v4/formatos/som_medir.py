"""Medidas do ACABAMENTO SONORO de um MP4 final (sem separar faixas — isso não se recupera de uma mixagem):
loudness integrado, pico verdadeiro, LRA (ebur128) e a distribuição do nível em janelas de 400 ms (p10 ≈ o que fica
nas pausas da fala: trilha/efeitos; p90 ≈ fala). Serve para comparar o Coringa com a referência com números reais."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np


def medir(arq: Path) -> dict:
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(arq), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True, timeout=300)
    t = r.stderr[r.stderr.rfind('Summary:'):]
    g = lambda pat: float(re.search(pat, t).group(1)) if re.search(pat, t) else None
    out = {'lufs': g(r'I:\s*(-?[\d.]+) LUFS'), 'lra': g(r'LRA:\s*(-?[\d.]+) LU'), 'pico_dbtp': g(r'Peak:\s*(-?[\d.]+) dBFS')}
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(arq), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True)
    x = np.frombuffer(p.stdout, np.int16).astype(np.float32) / 32768
    n = 6400
    x = x[: len(x) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((x ** 2).mean(axis=1)) + 1e-9)
    db = db[db > -70]
    if len(db):
        p10, p50, p90 = np.percentile(db, [10, 50, 90])
        out.update({'janela_db_p10': round(float(p10), 1), 'janela_db_p50': round(float(p50), 1), 'janela_db_p90': round(float(p90), 1),
                    'pausas_abaixo_da_fala_db': round(float(p90 - p10), 1)})
    return out
