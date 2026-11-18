"""Base cartográfica do palco a partir de um mosaico COLETADO (formatos_raster.py, no Actions): aplica a GRADE de cor do
canal (canal.palco.raster.grade_satelite — calibrada contra a referência A: só a transformação de cor, nenhum pixel da
referência) e grava o raster + manifesto no formato do motor (motor4/formatos/dados/raster).
uso: python scripts/formatos_base.py <dir_coleta_raster> <nome_regiao> <nome_base> <dataset> [--sem-grade]
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
DEST = RAIZ / 'motor4' / 'formatos' / 'dados' / 'raster'


def feats(x: np.ndarray) -> np.ndarray:
    x = x / 255.
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    return np.stack([r, g, b, r * r, g * g, b * b, r * g, r * b, g * b, np.ones_like(r)], -1)


def graduar(a: np.ndarray, coef) -> np.ndarray:
    C = np.asarray(coef, dtype=np.float32)
    out = np.empty_like(a, dtype=np.uint8)
    for i in range(0, a.shape[0], 256):                 # em faixas: o mosaico continental tem ~30 Mpx
        bl = a[i:i + 256].astype(np.float32)
        out[i:i + 256] = (np.clip(feats(bl) @ C, 0, 1) * 255).astype(np.uint8)
    return out


def main(coleta: Path, regiao: str, nome: str, dataset: str, grade: bool = True):
    Image.MAX_IMAGE_PIXELS = None
    meta = json.loads((coleta / f'{regiao}.json').read_text())
    a = np.asarray(Image.open(coleta / f'{regiao}_bruto.jpg').convert('RGB'))
    can = json.loads((RAIZ / 'src' / 'v4' / 'formatos' / 'canais' / 'coringa.json').read_text())
    g = ((can['palco'].get('raster') or {}).get('grade_satelite') or {}) if grade else {}
    if g.get('coef'):
        a = graduar(a, g['coef'])
    DEST.mkdir(parents=True, exist_ok=True)
    arq = DEST / f'{nome}.jpg'
    Image.fromarray(a).save(arq, quality=90, optimize=True, progressive=True)
    (o, n), (l, s) = meta['cantos'][0], meta['cantos'][2]
    z = meta['zoom_tiles']
    ppg = 256 * 2 ** min(z, 8) / 360            # resolução REAL da fonte (tiles GIBS até nível 8)
    m = {'nome': nome, 'tipo': 'satelite', 'cantos': meta['cantos'], 'px': list(Image.open(arq).size), 'px_por_grau_fonte': round(ppg, 3),
         'arquivo': arq.name, 'dataset': dataset, 'atribuicao': 'Imagem: NASA Blue Marble' if dataset == 'bmng' else dataset,
         'fonte': {'coleta': regiao, 'fontes': meta.get('fontes'), 'sha256_bruto': meta.get('sha256', {}),
                   'licenca': 'Domínio público (NASA)' if dataset == 'bmng' else None},
         'grade': {'modelo': g.get('modelo'), 'origem': g.get('origem')} if g.get('coef') else None,
         'sha256': hashlib.sha256(arq.read_bytes()).hexdigest(), 'gerado': time.strftime('%Y-%m-%d')}
    (DEST / f'{nome}.json').write_text(json.dumps(m, ensure_ascii=False, indent=1))
    print(nome, m['px'], m['px_por_grau_fonte'], o, n, l, s)


if __name__ == '__main__':
    a = sys.argv
    main(Path(a[1]), a[2], a[3], a[4], '--sem-grade' not in a)
