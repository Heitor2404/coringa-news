"""V2.5 — cadeia de ESTADOS do pipeline, como produto:
PESQUISA_VALIDADA → ACERVO_VERIFICADO → PLANO_VISUAL_EXECUTAVEL → ROTEIRO_VALIDADO → PREVIA_APROVADA → NARRACAO →
RENDER → FISCAL. Cada transição registra: entradas (sha256), resultado, causa da falha, artefatos reutilizáveis e o
custo acumulado. Fica em v['_estados'] (vai para o checkpoint) e em <pasta>/<nome>-estados.json."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

ORDEM = ['PESQUISA_VALIDADA', 'ACERVO_VERIFICADO', 'PLANO_VISUAL_EXECUTAVEL', 'ROTEIRO_VALIDADO', 'PREVIA_APROVADA',
         'NARRACAO', 'RENDER', 'FISCAL']


def _sha(x) -> str:
    try:
        b = Path(x).read_bytes() if isinstance(x, (str, Path)) and len(str(x)) < 400 and Path(str(x)).is_file() else \
            json.dumps(x, ensure_ascii=False, sort_keys=True, default=str).encode('utf-8')
    except Exception:
        b = repr(x).encode('utf-8')
    return hashlib.sha256(b).hexdigest()[:16]


def _custo() -> float | None:
    try:
        from src import orcamento_video
        return round(float(orcamento_video.gasto()), 4)
    except Exception:
        return None


def registrar(v: dict, estado: str, ok: bool, causa: str = '', entradas: dict | None = None, artefatos=None) -> dict:
    e = {'estado': estado, 'ok': bool(ok), 'causa': causa or None, 'entradas': {k: _sha(x) for k, x in (entradas or {}).items()},
         'artefatos': artefatos, 'custo_acumulado_usd': _custo(), 'quando': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
    v.setdefault('_estados', []).append(e)
    return e


def gravar(v: dict, pasta: Path, nome: str):
    try:
        (Path(pasta) / f'{nome}-estados.json').write_text(json.dumps(v.get('_estados') or [], ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    except Exception:
        pass


def ultimo_ok(v: dict) -> str | None:
    ok = [e['estado'] for e in v.get('_estados') or [] if e['ok']]
    return ok[-1] if ok else None
