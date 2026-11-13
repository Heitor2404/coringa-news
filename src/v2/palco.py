"""PALCO V2: monta a página (src/render/v2/palco.html) para um conjunto de cenas V2 e captura quadros/prévias.

A página tem a mesma interface do template antigo (window.DATA, seek(t), READY, inspecionar), então
src/render/render.py renderiza um vídeo V2 com o mesmo código de quadros + ffmpeg (meta.motor == 'v2').
"""
from __future__ import annotations

import base64
import json
import subprocess
from contextlib import contextmanager
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA = RAIZ / 'src' / 'render' / 'v2'
NAVEGADOR = ['--disable-gpu', '--enable-unsafe-swiftshader', '--allow-file-access-from-files', '--force-color-profile=srgb',
             '--use-gl=angle', '--use-angle=swiftshader-webgl']
ORDEM = ['base', 'aberturas', 'banners', 'dados', 'graficos', 'mapas', 'tempo', 'fotos', 'ciencia', 'mecanismos', 'editorial']


def composicoes() -> list[Path]:
    arqs = sorted((PASTA / 'comp').glob('*.js'), key=lambda p: (ORDEM.index(p.stem) if p.stem in ORDEM else 99, p.stem))
    return arqs


def _wh(arq: Path) -> list[int] | None:
    try:
        from PIL import Image
        with Image.open(arq) as im:
            return list(im.size)
    except Exception:
        return None


def _uri(x: str | Path) -> str:
    s = str(x)
    return s if s.startswith(('file:', 'data:', 'http')) else Path(s).resolve().as_uri()


def preparar(dados: dict) -> dict:
    """Completa as cenas para a página: caminhos file://, tamanho das fotos, recorte geográfico dos mapas, mascote."""
    from src.v2 import geo
    d = json.loads(json.dumps(dados, default=str))
    d.setdefault('meta', {})
    d.setdefault('captions', [])
    m3 = RAIZ / 'assets' / 'mascote3d'
    d['meta']['mascote'] = {p.stem: p.resolve().as_uri() for p in m3.glob('*.png')}
    from src.v2 import acervo_v2
    for sc in d['scenes']:
        f = sc.get('fundo')
        if f and f.get('img') and (f.get('de') == 'auto' or f.get('para') == 'auto') and not str(f['img']).startswith(('file:', 'data:')):
            e = acervo_v2.enquadramento(f['img'], sc['end'] - sc['start'])
            if e['modo'] == 'cobrir':
                f.update({k: e[k] for k in ('de', 'para', 'wh')})
                if f.get('variante'):          # 2º uso da mesma foto na mesma ideia: outro canto, mais fechado
                    f['de'] = [1 - f['de'][0], f['de'][1], 1.1]
                    f['para'] = [min(.85, max(.15, 1 - f['para'][0])), f['para'][1], 1.18]
            else:
                f.update({'modo': 'moldura', 'de': [.5, .5, 1], 'para': [e['foco'][0], e['foco'][1], 1.08]})
        p0 = sc.get('params') or {}
        if p0.get('img') and p0.get('recorte') == 'auto' and not str(p0['img']).startswith(('file:', 'data:')):
            p0['recorte'] = acervo_v2.recorte_conteudo(p0['img'])
            if not p0.get('foco'):
                p0['foco'] = list(acervo_v2.foco(p0['img'], p0['recorte']))
        if f and f.get('img'):
            if not f.get('wh') and not str(f['img']).startswith(('file:', 'data:')):
                f['wh'] = _wh(Path(f['img']))
            f['img'] = _uri(f['img'])
        p = sc.setdefault('params', {})
        for k in ('img', 'img_a', 'img_b', 'img_depois', 'img_antes'):
            if p.get(k) and isinstance(p[k], str):
                if not p.get(k + '_wh') and not p[k].startswith(('file:', 'data:')):
                    p[k + '_wh'] = _wh(Path(p[k]))
                p[k] = _uri(p[k])
        for lst in ('fotos', 'itens'):
            for it in p.get(lst) or []:
                if isinstance(it, dict) and it.get('img'):
                    if not it.get('wh') and not str(it['img']).startswith(('file:', 'data:')):
                        it['wh'] = _wh(Path(it['img']))
                    it['img'] = _uri(it['img'])
        q = p.get('quadros')
        if isinstance(q, dict) and q.get('manim'):
            from src.v2 import manim_cenas
            if manim_cenas.disponivel():
                kw = {k: v for k, v in q.items() if k not in ('manim', 'n', 'fps', 'dir', 'base')}
                pasta = RAIZ / 'saida' / 'manim_cache' / ('_'.join([q['manim']] + [f'{k}{v}' for k, v in sorted(kw.items())]) + f"_{sc['end'] - sc['start']:.2f}")
                if not (pasta / 'f_0001.jpg').exists():
                    manim_cenas.renderizar(q['manim'], pasta, dur=sc['end'] - sc['start'], **kw)
                q['dir'], q['n'], q['fps'] = str(pasta), len(list(pasta.glob('f_*.jpg'))), 30
        if isinstance(q, dict) and q.get('dir'):
            q['base'] = Path(q['dir']).resolve().as_uri() + '/f_'
        if str(sc.get('comp', '')).startswith('mapa.'):
            pts = [(float(x['lon']), float(x['lat'])) for x in p.get('pontos') or [] if 'lon' in x]
            pts += [(float(a), float(b)) for a, b in p.get('rota') or []]
            alvo = geo.pais(p['pais']) if p.get('pais') else None
            if alvo:
                bb = alvo['_bb']
                pts += [(bb[0], bb[1]), (bb[2], bb[3])]
                p['pais_geo'] = {'type': 'Feature', 'properties': alvo['properties'], 'geometry': alvo['geometry']}
                p.setdefault('pais_nome', alvo['properties'].get('name_pt') or alvo['properties'].get('name'))
            if not pts:
                pts = [(-60, -30), (60, 60)]
            bb = geo.caixa_de(pts, folga=p.get('folga', 0.35), minimo=p.get('minimo', 0.8))
            p['bbox'] = bb
            p['geo'] = geo.recorte(bb, extra=p.get('extra', 1.6))
    return d


def pagina(dados: dict, trabalho: Path) -> Path:
    """Escreve data.js + index.html (palco) em `trabalho`. `dados` já preparados."""
    trabalho = Path(trabalho).resolve()
    trabalho.mkdir(parents=True, exist_ok=True)
    (trabalho / 'data.js').write_text('window.DATA=' + json.dumps(dados, ensure_ascii=False) + ';', encoding='utf-8')
    html = (PASTA / 'palco.html').read_text(encoding='utf-8')
    html = html.replace('../../../node_modules', (RAIZ / 'node_modules').as_uri())
    html = html.replace('href="estilo.css"', f'href="{(PASTA / "estilo.css").as_uri()}"')
    html = html.replace('src="nucleo.js"', f'src="{(PASTA / "nucleo.js").as_uri()}"')
    html = html.replace('src="data.js"', f'src="{(trabalho / "data.js").as_uri()}"')
    html = html.replace('<!--COMPOSICOES-->', '\n'.join(f'<script src="{p.as_uri()}"></script>' for p in composicoes()))
    # o estilo.css usa caminhos relativos às fontes: reescreve num arquivo local
    css = (PASTA / 'estilo.css').read_text(encoding='utf-8').replace('../../../node_modules', (RAIZ / 'node_modules').as_uri())
    (trabalho / 'estilo.css').write_text(css, encoding='utf-8')
    html = html.replace(f'href="{(PASTA / "estilo.css").as_uri()}"', f'href="{(trabalho / "estilo.css").as_uri()}"')
    p = trabalho / 'index.html'
    p.write_text(html, encoding='utf-8')
    return p


@contextmanager
def abrir(dados_prontos: dict, trabalho: Path, escala: float = 1.0):
    """Abre o palco num Chromium sem janela e entrega a página pronta (READY)."""
    from playwright.sync_api import sync_playwright
    pag = pagina(dados_prontos, trabalho)
    with sync_playwright() as p:
        nav = p.chromium.launch(args=NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=escala)
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)))
        pg.goto(pag.as_uri())
        pg.wait_for_function('window.READY===true', timeout=180000)
        erro = pg.evaluate('window.ERRO_V2||null')
        if erro:
            erros.append(erro)
        pg.erros = erros
        try:
            yield pg
        finally:
            nav.close()


def capturar(pg, t: float, saida: Path, qualidade: int = 90) -> Path:
    pg.evaluate(f'seek({t:.3f})')
    saida.parent.mkdir(parents=True, exist_ok=True)
    if saida.suffix.lower() == '.png':
        pg.screenshot(path=str(saida), type='png')
    else:
        pg.screenshot(path=str(saida), type='jpeg', quality=qualidade)
    return saida


def previa(pg, ini: float, fim: float, saida: Path, fps: int = 24, largura: int = 540) -> Path:
    """Prévia animada curta (mp4 H.264, metade da resolução) de [ini, fim]."""
    cdp = pg.context.new_cdp_session(pg)
    saida.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', str(fps), '-i', '-',
                           '-vf', f'scale={largura}:-2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
                           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(saida)], stdin=subprocess.PIPE)
    n = int((fim - ini) * fps)
    for i in range(n):
        pg.evaluate(f'seek({ini + i / fps:.4f})')
        r = cdp.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 85})
        ff.stdin.write(base64.b64decode(r['data']))
    ff.stdin.close()
    ff.wait()
    return saida


def medir(pg, dur: float, passo: float = 0.25) -> list[dict]:
    """Problemas geométricos ao longo da duração (texto sobre texto, fora do quadro, zona da interface, letra pequena)."""
    out = []
    t = 0.0
    while t < dur:
        pg.evaluate(f'seek({t:.3f})')
        for pb in pg.evaluate(f'inspecionar({t:.3f})'):
            out.append({**pb, 't': round(t, 2)})
        t += passo
    return out
