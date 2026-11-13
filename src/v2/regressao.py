"""REGRESSÃO VISUAL V2 (Playwright, sem serviço externo).

Cada composição do catálogo é renderizada com o seu exemplo em instantes fixos e comparada com a referência gravada
em tests/v2_referencias/<id>@<t>.webp (144×256, WebP sem perda, ~25 KB). As referências usam só imagens do próprio repositório
(CORINGA_AUDITORIA ignorado), então o teste roda igual no CI.

Comparação: diferença média por pixel (0–255) e fração de pixels que mudaram mais de 40. Reprovado se
média > 4,0 ou fração > 2,5%. Atualizar de propósito: python -m src.v2.regressao --atualizar [--so id]
"""
from __future__ import annotations

import argparse
import base64
import io
import os
from pathlib import Path

import numpy as np
from PIL import Image

from src.v2 import galeria, palco

REF = palco.RAIZ / 'tests' / 'v2_referencias'
TAM = (144, 256)
LIM_MEDIA, LIM_FRACAO = 4.0, 0.025
FRACOES = (0.35, 0.85)


DIAG = {}   # diagnóstico do ambiente (fontes, imagens, navegador) por composição, impresso quando a regressão falha


def _midia_repo():
    os.environ['CORINGA_AUDITORIA'] = '/nao-existe'       # só imagens do repositório
    galeria.AUD = Path('/nao-existe')


def quadros(meta: dict, trabalho: Path) -> dict[float, Image.Image]:
    _midia_repo()
    d = galeria.dados_exemplo(meta)
    out = {}
    with palco.abrir(palco.preparar(d), trabalho / meta['id']) as pg:
        DIAG[meta['id']] = pg.evaluate("""(()=>{const f=[...document.fonts].map(x=>x.family+' '+x.weight+' '+x.status);
            const im=[...document.images].map(i=>(i.src.split('/').pop()||'').slice(0,40)+' '+i.complete+' '+i.naturalWidth);
            return {ua:navigator.userAgent, fontes:f, imagens:im}})()""")
        for f in FRACOES:
            t = round(d['duration'] * f, 2)
            pg.evaluate(f'seek({t})')
            png = pg.screenshot(type='png')
            out[t] = Image.open(io.BytesIO(png)).convert('RGB').resize(TAM, Image.LANCZOS)
    return out


def comparar(a: Image.Image, b: Image.Image) -> dict:
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    d = np.abs(x - y).max(axis=2)
    r = {'media': round(float(d.mean()), 3), 'fracao': round(float((d > 40).mean()), 4)}
    r['ok'] = r['media'] <= LIM_MEDIA and r['fracao'] <= LIM_FRACAO
    return r


def arquivo(cid: str, t: float) -> Path:
    return REF / f'{cid}@{t:05.2f}.webp'


def verificar(metas: list[dict], trabalho: Path) -> list[dict]:
    res = []
    for m in metas:
        for t, im in quadros(m, trabalho).items():
            ref = arquivo(m['id'], t)
            if not ref.exists():
                res.append({'id': m['id'], 't': t, 'ok': False, 'motivo': 'sem referência'})
                continue
            r = {'id': m['id'], 't': t, **comparar(im, Image.open(ref).convert('RGB'))}
            if not r['ok']:   # para diagnosticar diferença de ambiente (CI): o quadro produzido vai junto, pequeno
                buf = io.BytesIO(); im.save(buf, 'WEBP', quality=80)
                r['produzido_webp_b64'] = base64.b64encode(buf.getvalue()).decode()
                r['ambiente'] = DIAG.get(m['id'])
            res.append(r)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--atualizar', action='store_true')
    ap.add_argument('--so', default='')
    a = ap.parse_args(argv)
    trabalho = palco.RAIZ / 'saida' / '_regressao'
    metas = galeria.catalogo(trabalho / '_cat')
    if a.so:
        metas = [m for m in metas if m['id'] in a.so.split(',')]
    if a.atualizar:
        REF.mkdir(parents=True, exist_ok=True)
        for m in metas:
            for t, im in quadros(m, trabalho).items():
                im.save(arquivo(m['id'], t), lossless=True, method=6)
                print('referência', arquivo(m['id'], t).name)
        return
    for r in verificar(metas, trabalho):
        print(('OK   ' if r['ok'] else 'FALHA'), r)


if __name__ == '__main__':
    main()
