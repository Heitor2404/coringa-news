"""Prévia dos componentes editoriais (Etapa 3, frente B): quadros, folha de contato e MP4 curto. Sem IA, sem rede.

    python prototipos/editorial/previa.py specs/mapa.json [--quadros 1,2.5] [--sem-video] [--zonas]
"""
import argparse, json, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI.parent / 'esquema'))
from previa import folha  # noqa: E402  (mesma folha de contato do esquema)
FPS = 30


def abrir(pw, spec, zonas=False):
    nav = pw.chromium.launch(); pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
    erros = []; pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto((AQUI / 'pagina.html').as_uri()); pg.evaluate('document.fonts.ready')
    if spec['componente'] == 'mapa':        # mesmo dado que o template já usa (Natural Earth via world-atlas)
        pg.evaluate('m => window.MUNDO = m', json.loads((RAIZ / 'node_modules/world-atlas/countries-50m.json').read_text()))
    if zonas: pg.evaluate("document.body.classList.add('zonas')")
    pg.evaluate('s => EDITORIAL.carregar(s)', spec); pg.evaluate('document.fonts.ready')
    pg.wait_for_timeout(200)              # imagens de fundo
    return nav, pg, erros


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--quadros', default='')
    ap.add_argument('--sem-video', action='store_true'); ap.add_argument('--zonas', action='store_true')
    a = ap.parse_args()
    p = Path(a.spec); p = p if p.is_absolute() else (AQUI / p if (AQUI / p).exists() else Path.cwd() / p)
    spec = json.loads(p.read_text(encoding='utf-8')); nome = 'ed_' + p.stem
    pasta = RAIZ / 'saida' / 'prototipos' / nome; pasta.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    tempos = [float(x) for x in a.quadros.split(',') if x] or [round(spec['duracao'] * k, 2) for k in (.15, .35, .6, .9)]
    with sync_playwright() as pw:
        nav, pg, erros = abrir(pw, spec, a.zonas); fotos = []
        for t in tempos:
            pg.evaluate(f'seek({t})'); f = pasta / f'q_{t:05.2f}.png'; pg.screenshot(path=str(f)); fotos.append(f)
        if not a.sem_video:
            tmp = pasta / '_q'; tmp.mkdir(exist_ok=True)
            for i in range(int(spec['duracao'] * FPS) + 1):
                pg.evaluate(f'seek({i / FPS})'); pg.screenshot(path=str(tmp / f'{i:05d}.jpg'), type='jpeg', quality=92)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(tmp / '%05d.jpg'), '-c:v', 'libx264',
                            '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', str(pasta / f'{nome}.mp4')], check=True)
            for f in tmp.glob('*.jpg'): f.unlink()
            tmp.rmdir()
        nav.close()
    if erros: raise RuntimeError('erros de JS: ' + '; '.join(erros))
    folha(fotos, pasta / 'folha.png')
    print('ok', pasta)


if __name__ == '__main__':
    sys.exit(main())
