"""Backend rembg (CPU, ambiente isolado .venv-rembg, modelo em U2NET_HOME — baixado UMA vez, cache no Actions).

recortar(foto) → PNG com alfa + medidas OBJETIVAS da máscara. A máscara só é aceita se:
- cobertura entre 3% e 70% da foto (nem vazio, nem "recortou o fundo junto");
- o maior fragmento tem ≥ 85% da área recortada (sem pedaços soltos);
- borda não serrilhada demais (perímetro²/área abaixo do limite);
- o assunto não encosta em 3 ou 4 bordas da foto (recorte cortado).
Recusa → a cena cai para composição sem recorte (registrado). Nunca "pan/zoom porque recortou".
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from src.v4.util import VENV_REMBG, FalhaBackend, rodar

MODELO = os.environ.get('CORINGA_REMBG_MODELO', 'isnet-general-use')

_SCRIPT = r'''
import sys, json
import numpy as np
from PIL import Image
from rembg import new_session, remove
from scipy import ndimage
ent, sai, modelo = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(ent).convert("RGB")
out = remove(im, session=new_session(modelo), post_process_mask=True)
out.save(sai)
a = np.asarray(out.split()[-1]) > 127
area = int(a.sum()); tot = a.size
lab, n = ndimage.label(a)
maior = int(np.bincount(lab.ravel())[1:].max()) if n else 0
borda = a ^ ndimage.binary_erosion(a)
per = int(borda.sum())
toca = sum(bool(x) for x in (a[0].any(), a[-1].any(), a[:, 0].any(), a[:, -1].any()))
ys, xs = np.nonzero(a)
bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if area else None
print(json.dumps({"cobertura": area / tot, "fragmentos": int(n), "maior_fragmento": maior / max(1, area),
                  "compacidade": per * per / max(1, area), "toca_bordas": toca, "bbox_px": bbox, "wh": list(im.size)}))
'''


def recortar(foto: Path, saida: Path, trab: Path) -> dict:
    trab.mkdir(parents=True, exist_ok=True)
    scr = trab / '_rembg.py'
    scr.write_text(_SCRIPT)
    py = VENV_REMBG / 'bin' / 'python'
    reg = rodar([py, scr, foto, saida, MODELO], timeout=900, log=trab / 'rembg.log')
    m = json.loads((trab / 'rembg.log').read_text().strip().splitlines()[-1])
    motivos = []
    if not .03 <= m['cobertura'] <= .70:
        motivos.append(f"cobertura {m['cobertura']:.0%} fora de 3–70%")
    if m['maior_fragmento'] < .85:
        motivos.append(f"máscara fragmentada (maior pedaço {m['maior_fragmento']:.0%})")
    if m['compacidade'] > 400:
        motivos.append(f"borda serrilhada (compacidade {m['compacidade']:.0f})")
    if m['toca_bordas'] >= 3:
        motivos.append(f"assunto encosta em {m['toca_bordas']} bordas (recorte cortado)")
    return {**reg, 'backend': 'rembg', 'modelo': MODELO, 'medidas': m, 'aceito': not motivos, 'motivos': motivos, 'arquivo': str(saida)}


def exigir(foto: Path, saida: Path, trab: Path) -> dict:
    r = recortar(foto, saida, trab)
    if not r['aceito']:
        raise FalhaBackend('máscara recusada: ' + '; '.join(r['motivos']))
    return r
