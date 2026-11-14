"""Evidência visual da centralização (V2.2): mesmos instantes no código antigo e no novo, com o eixo x = 540 desenhado.

  capturar <saida>   (rodar com cwd = checkout a medir) grava quadros 1080×1920 + medidas (pixels da legenda e, se o
                     palco tiver V2.medirCentros, caixas e glifos do DOM)
  montar <antes> <depois> <saida>   desenha eixo, caixas e centros e monta pares lado a lado
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, os.getcwd())

CASOS_LEG = ['GRAVIDADE', 'DOIS OCEANOS', 'A ÁGUA DESCE DO LAGO E ENCHE A CÂMARA INTEIRA', 'US$ 5,3 MILHÕES', 'ESCHERICHIA COLI', '— E AGORA?!']
COMPS = [('revelacao.surpresa', [.3, .6]), ('titulo.capitulo', [.7]), ('forcas.vetores', [.8]), ('foto.documental', [.6]),
         ('abertura.pergunta', [.7]), ('numero.animado', [.8]), ('encerramento.editorial', [.8]), ('banner.importante', [.6]),
         ('foto.historica', [.3, .85]), ('mapa.territorio', [.95])]   # galeria V2.2: foto de 1913 e rótulos de mar


def capturar(saida: Path):
    from PIL import Image
    from src.v2 import galeria, palco
    saida.mkdir(parents=True, exist_ok=True)
    res = {}

    def um(pg, nome, t):
        arq = saida / f'{nome}.png'
        palco.capturar(pg, t, arq)
        dom = pg.evaluate('V2.medirCentros ? V2.medirCentros() : null')
        est = pg.evaluate(f'estadoV2({t:.3f})')
        res[nome] = {'t': t, 'dom': dom, 'topo_legenda': est.get('topo') or 1240}

    cat = {m['id']: m for m in galeria.catalogo(saida / '_cat')}
    for cid, fr in COMPS:
        d = galeria.dados_exemplo(cat[cid])
        with palco.abrir(palco.preparar(d), saida / '_tr' / cid) as pg:
            for f in fr:
                um(pg, f'{cid}@{f}', round(d['duration'] * f, 2))
    # legendas de tamanhos diferentes sobre fundo escuro
    img = saida / 'preto.png'; Image.new('RGB', (1080, 1920), (8, 8, 10)).save(img)
    caps, t = [], .2
    for txt in CASOS_LEG:
        ws = txt.split(); caps.append({'start': t, 'end': t + .9, 'words': [{'w': w, 'hl': i == len(ws) - 1, 's': t + i * .05} for i, w in enumerate(ws)]}); t += 1
    d = {'duration': t, 'meta': {'motor': 'v2'}, 'captions': caps, 'scenes': [{'comp': 'foto.documental', 'start': 0, 'end': t, 'params': {'img': str(img)}, 'legenda': 'livre'}]}
    with palco.abrir(palco.preparar(d), saida / '_tr' / 'legendas') as pg:
        for i, c in enumerate(caps):
            um(pg, f'legenda_{i}', round(c['start'] + .6, 2))
        palco.previa(pg, 0, d['duration'], saida / 'legendas_previa.mp4', fps=20)
    (saida / 'medidas.json').write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')


def _anotar(arq: Path, med: dict, rotulo: str):
    from PIL import Image, ImageDraw, ImageFont
    from src.v2 import centros
    im = Image.open(arq).convert('RGB'); dr = ImageDraw.Draw(im, 'RGBA')
    f = ImageFont.truetype('DejaVuSans-Bold.ttf', 34)
    dr.line([(540, 0), (540, 1920)], fill=(255, 0, 255, 230), width=3)
    linhas = [rotulo]
    for m in med.get('dom') or []:
        if not (m.get('declarado') or (m.get('alinhamento') == 'centro' and not m.get('intencao'))):
            continue
        y = m['linhas'][0]['y'] - 6
        dr.rectangle([m['caixa']['x0'], y, m['caixa']['x1'], y + 6], fill=(0, 220, 255, 200))
        dr.line([(m['glifos']['centro'], y - 26), (m['glifos']['centro'], y + 30)], fill=(0, 255, 120, 255), width=5)
        linhas.append(f"{m['g'][:10]}: caixa {m['desvio_caixa']:+.0f} · glifos {m['desvio_glifos']:+.0f} px")
    topo = med['topo_legenda']
    p = centros.centro_pixels(im.crop((0, 0, 1080, 1920)), topo, topo + 260)
    if p:
        dr.rectangle([p['x0'], topo - 4, p['x1'], topo], fill=(255, 210, 31, 220))
        dr.line([(p['centro'], topo - 30), (p['centro'], topo + 260)], fill=(255, 210, 31, 255), width=4)
        linhas.append(f"legenda (pixels): {p['desvio']:+.0f} px")
    y = 1560
    dr.rectangle([0, y - 10, 1080, y + 46 * len(linhas) + 10], fill=(0, 0, 0, 190))
    for i, l in enumerate(linhas):
        dr.text((30, y + i * 46), l, fill=(255, 255, 255), font=f)
    return im


def montar(antes: Path, depois: Path, saida: Path):
    from PIL import Image
    saida.mkdir(parents=True, exist_ok=True)
    ma = json.loads((antes / 'medidas.json').read_text()); md = json.loads((depois / 'medidas.json').read_text())
    for nome in md:
        a = _anotar(antes / f'{nome}.png', ma[nome], 'ANTES (V2.1)') if nome in ma else None
        b = _anotar(depois / f'{nome}.png', md[nome], 'DEPOIS (V2.2)')
        W = 540
        im = Image.new('RGB', (W * 2 + 12, 960), (30, 30, 34))
        if a: im.paste(a.resize((W, 960), Image.LANCZOS), (0, 0))
        im.paste(b.resize((W, 960), Image.LANCZOS), (W + 12, 0))
        im.save(saida / f'{nome}.jpg', quality=84)
    print(len(md), 'pares em', saida)


if __name__ == '__main__':
    if sys.argv[1] == 'capturar':
        capturar(Path(sys.argv[2]).resolve())
    else:
        montar(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
