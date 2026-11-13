"""Prévia do protótipo ESQUEMA (Etapa 3): quadros PNG, folha de contato e MP4 curto (sem áudio, sem IA).

    python prototipos/esquema/previa.py specs/cromatoforo.json [--quadros 1.5,4.5,...] [--sem-video] [--zonas]

Saída em saida/prototipos/<id>/ (fora do git). Usa o mesmo caminho do render principal: Playwright + seek(t) + ffmpeg.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
FPS = 30


def abrir(pw, spec: dict, legenda=True, zonas=False):
    nav = pw.chromium.launch()
    pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto((AQUI / 'pagina.html').as_uri())
    pg.evaluate('document.fonts.ready')
    if zonas:
        pg.evaluate("document.body.classList.add('zonas')")
    pg.evaluate('([s, o]) => ESQUEMA.carregar(s, o)', [spec, {'legenda': legenda}])
    pg.evaluate('document.fonts.ready')
    return nav, pg, erros


def quadros(spec: dict, tempos: list[float], pasta: Path, zonas=False) -> list[Path]:
    from playwright.sync_api import sync_playwright
    pasta.mkdir(parents=True, exist_ok=True)
    out = []
    with sync_playwright() as pw:
        nav, pg, erros = abrir(pw, spec, zonas=zonas)
        for t in tempos:
            pg.evaluate(f'seek({t})')
            f = pasta / f"q_{t:05.2f}.png"
            pg.screenshot(path=str(f))
            out.append(f)
        nav.close()
    if erros:
        raise RuntimeError('erros de JS: ' + '; '.join(erros))
    return out


def folha(fotos: list[Path], saida: Path, colunas=4):
    """Folha de contato (miniaturas 360×640) com o tempo de cada quadro."""
    from PIL import Image, ImageDraw
    w, h = 360, 640
    lin = (len(fotos) + colunas - 1) // colunas
    img = Image.new('RGB', (colunas * w + (colunas + 1) * 12, lin * (h + 40) + 12), (18, 20, 26))
    d = ImageDraw.Draw(img)
    for i, f in enumerate(fotos):
        x, y = 12 + (i % colunas) * (w + 12), 12 + (i // colunas) * (h + 40)
        img.paste(Image.open(f).convert('RGB').resize((w, h), Image.LANCZOS), (x, y))
        d.text((x + 4, y + h + 8), f"t = {f.stem[2:]} s", fill=(255, 210, 31))
    img.save(saida)


def video(spec: dict, saida: Path, ini=0.0, fim=None):
    from playwright.sync_api import sync_playwright
    fim = fim if fim is not None else spec['duracao']
    tmp = saida.parent / '_quadros'
    tmp.mkdir(parents=True, exist_ok=True)
    for f in tmp.glob('*.jpg'):
        f.unlink()
    with sync_playwright() as pw:
        nav, pg, erros = abrir(pw, spec)
        n = int((fim - ini) * FPS)
        for i in range(n + 1):
            pg.evaluate(f'seek({ini + i / FPS})')
            pg.screenshot(path=str(tmp / f'{i:05d}.jpg'), type='jpeg', quality=92)
        nav.close()
    if erros:
        raise RuntimeError('erros de JS: ' + '; '.join(erros))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(tmp / '%05d.jpg'),
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', str(saida)], check=True)
    for f in tmp.glob('*.jpg'):
        f.unlink()
    tmp.rmdir()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('--quadros', default='')
    ap.add_argument('--sem-video', action='store_true')
    ap.add_argument('--zonas', action='store_true')
    a = ap.parse_args()
    p = Path(a.spec)
    p = p if p.is_absolute() else (AQUI / p if (AQUI / p).exists() else Path.cwd() / p)
    spec = json.loads(p.read_text(encoding='utf-8'))
    pasta = RAIZ / 'saida' / 'prototipos' / spec['id']
    tempos = [float(x) for x in a.quadros.split(',') if x] or \
             [round((s['de'] + s['ate']) / 2 + .35, 2) for s in spec.get('passos', [])] or [spec['duracao'] / 2]
    fotos = quadros(spec, tempos, pasta, zonas=a.zonas)
    folha(fotos, pasta / 'folha.png')
    print('quadros:', *[str(f) for f in fotos], sep='\n  ')
    if not a.sem_video:
        video(spec, pasta / f"{spec['id']}.mp4")
        print('vídeo:', pasta / f"{spec['id']}.mp4")


if __name__ == '__main__':
    sys.exit(main())
