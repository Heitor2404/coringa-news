"""Diagnóstico da borda de textura Sentinel-2 (E284): raster bruto × mosaico × render.

Para cada base s2_2016/bmng adquirida no caso ATLAS: baixa de novo os tiles brutos (limitado), grava a grade com as
divisas dos tiles anotadas, mede por tile a fração de pixels quase pretos/brancos/uniformes, detecta no mosaico regiões
contíguas de "sem dado" e mede a curvatura da sua fronteira; extrai quadros do MP4 nos instantes em que cada base entra
na rampa de opacidade. Só evidência para decidir a causa; não altera nem mascara nada.
Uso: python -m scripts.diagnostico_s2_e284 <caso.json> <pasta_mapa> <saida>
"""
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scripts import formatos_raster as R
from src.v4.formatos import plano as A


def _semdado(a):
    lum = a.mean(axis=2)
    escuro = lum < 8
    branco = lum > 250
    sat = a.max(axis=2) - a.min(axis=2)
    return escuro | branco, sat


def _curvatura(mask):
    """Fronteira da maior região sem dado: desvio de uma reta (px) — curva grande indica limite de faixa/órbita."""
    ys, xs = np.nonzero(mask)
    if len(xs) < 50:
        return None
    borda = []
    for y in range(mask.shape[0]):
        row = np.nonzero(mask[y])[0]
        if 0 < len(row) < mask.shape[1]:
            borda.append((y, row.max() if row.min() == 0 else row.min()))
    if len(borda) < 10:
        return None
    b = np.array(borda, float)
    coef = np.polyfit(b[:, 0], b[:, 1], 1)
    res = b[:, 1] - np.polyval(coef, b[:, 0])
    coef2 = np.polyfit(b[:, 0], b[:, 1], 2)
    return {'pontos': len(b), 'desvio_reta_px': round(float(np.abs(res).max()), 2), 'quadratico': round(float(coef2[0]), 6)}


def main(caso_path, mapa, saida):
    caso = json.loads(Path(caso_path).read_text()); mapa, saida = Path(mapa), Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    plan = json.loads((mapa / 'planejamento.json').read_text())
    rel = {'caso': caso['id'], 'bases': [], 'quadros': [], 'publicar': False}
    for meta in plan['bases']:
        modelo = meta['fonte']['url']; z = meta['fonte']['zoom_tiles']; o, s, l, n = meta['fonte']['bbox_pedido']
        x0, y0 = R.tile_xy(o, n, z); x1, y1 = R.tile_xy(l, s, z)
        xs, ys = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
        grade = Image.new('RGB', (256 * len(xs), 256 * len(ys)), (255, 0, 255))
        d = ImageDraw.Draw(grade); tiles = []
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                im = R.baixar(modelo.format(z=z, x=x, y=y))
                info = {'x': x, 'y': y, 'z': z, 'ausente': im is None}
                if im is not None:
                    info['tamanho_bruto'] = list(im.size)
                    a = np.asarray(im.convert('RGB').resize((256, 256)))
                    sd, sat = _semdado(a)
                    info.update(semdado=round(float(sd.mean()), 4), saturacao_media=round(float(sat.mean()), 2),
                                lum_media=round(float(a.mean()), 2))
                    grade.paste(Image.fromarray(a), (i * 256, j * 256))
                tiles.append(info)
                d.rectangle([i * 256, j * 256, i * 256 + 255, j * 256 + 255], outline=(255, 255, 0))
        mosaico_arq = A.RASTER_DIR / meta['arquivo']
        bruto_vs_mosaico = None
        if mosaico_arq.is_file():
            mos = np.asarray(Image.open(mosaico_arq).convert('RGB'))
            g = np.asarray(grade)
            if mos.shape == g.shape:
                bruto_vs_mosaico = round(float(np.abs(mos.astype(int) - g.astype(int)).mean()), 3)
            sd, _ = _semdado(mos)
            curva = _curvatura(sd)
        else:
            curva = None
        nome = f"grade-{meta['nome']}.jpg"
        g2 = grade.copy(); g2.thumbnail((1800, 1800)); g2.save(saida / nome, quality=88)
        rel['bases'].append({'nome': meta['nome'], 'dataset': meta['dataset'], 'zoom': z, 'tiles': tiles, 'folha': nome,
                             'bruto_vs_mosaico_mae': bruto_vs_mosaico, 'fronteira_semdado_mosaico': curva,
                             'tiles_com_semdado': sum(1 for t in tiles if t.get('semdado', 0) > .02)})
    mp4 = mapa / 'mapa.mp4'
    if mp4.is_file():
        dur = float(json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(mp4)]))['format']['duration'])
        for k in range(12):
            t = dur * (k + .5) / 12
            png = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', str(mp4), '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'])
            im = Image.open(io.BytesIO(png)).convert('RGB')
            sd, _ = _semdado(np.asarray(im))
            nome = f'quadro-{k:02d}.jpg'; im.save(saida / nome, quality=90)
            rel['quadros'].append({'t': round(t, 3), 'arquivo': nome, 'semdado': round(float(sd.mean()), 4), 'curva': _curvatura(sd)})
    (saida / 'diagnostico_s2.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1))
    print('DIAG_S2', json.dumps([{k: b[k] for k in ('nome', 'dataset', 'zoom', 'tiles_com_semdado', 'bruto_vs_mosaico_mae', 'fronteira_semdado_mosaico')} for b in rel['bases']], ensure_ascii=False))


if __name__ == '__main__':
    main(*sys.argv[1:4])
