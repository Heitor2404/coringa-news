"""Renderiza o vídeo: página HTML animada → quadros (Playwright) → ffmpeg.

Os quadros são divididos entre vários navegadores em paralelo (um por núcleo),
cada um gera um trecho de vídeo, e no fim os trechos são unidos e a narração é mixada.
"""
import base64, json, os, re, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TEMPLATE = Path(__file__).with_name('template.html')
FPS = 30
# Composição por software (rápida). ATENÇÃO: '--use-angle=swiftshader' deixava
# a página inteira 4–5x mais lenta (1 s por quadro em vez de 0,2 s) — não usar.
NAVEGADOR = ['--disable-gpu', '--enable-unsafe-swiftshader', '--allow-file-access-from-files', '--force-color-profile=srgb']


def _pagina(trabalho: Path) -> Path:
    html = TEMPLATE.read_text(encoding='utf-8')
    html = html.replace('../../node_modules', (RAIZ / 'node_modules').as_uri())
    html = html.replace('src="data.js"', f'src="{(trabalho / "data.js").as_uri()}"')
    p = trabalho / 'index.html'
    p.write_text(html, encoding='utf-8')
    return p


def _trecho(args):
    pagina, ini, fim, saida = args
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        nav = p.chromium.launch(args=NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(Path(pagina).as_uri())
        pg.wait_for_function('window.READY===true', timeout=60000)
        cdp = pg.context.new_cdp_session(pg)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', str(FPS), '-i', '-',
                               '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', str(saida)],
                              stdin=subprocess.PIPE)
        for i in range(ini, fim):
            pg.evaluate(f'seek({i / FPS})')
            r = cdp.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 94})
            ff.stdin.write(base64.b64decode(r['data']))
        ff.stdin.close(); ff.wait()
        nav.close()
    return saida


DADOS = ('numero', 'cards', 'lista', 'escala', 'mapa', 'citacao', 'revelacao', 'fechamento', 'linha_tempo', 'comparacao')
TRS = ['corte', 'corte', 'zoom', 'corte', 'chicote', 'corte']   # igual ao template.html


def _norm(p: str) -> str:
    import unicodedata
    p = unicodedata.normalize('NFD', p.lower())
    return ''.join(ch for ch in p if ch.isalnum() and not unicodedata.combining(ch))


def _marcar_viradas(dados: dict):
    """Na revelação, o cartão vira no instante em que o Coringa FALA a resposta (não antes, para não dar spoiler)."""
    for sc in dados['scenes']:
        if sc.get('tipo') != 'revelacao' or sc.get('virada'):
            continue
        alvo = [_norm(w) for w in str(sc.get('resposta', '')).split() if len(_norm(w)) > 2]
        for c in dados.get('captions', []):
            for w in c['words']:
                t0 = w.get('s', c['start'])
                if sc['start'] <= t0 <= sc['end'] and alvo and _norm(w['w']) in alvo:
                    sc['virada'] = round(max(sc['start'] + 0.5, t0 - 0.12), 3)
                    break
            if sc.get('virada'):
                break


def _transicao(sc: dict, i: int) -> str:
    return sc.get('transicao') or ('zoom' if sc.get('tipo') in DADOS else TRS[i % len(TRS)])


SEM_NUMERO = {'gancho', 'numero', 'linha_tempo', 'comparacao', 'cards', 'escala', 'lista', 'revelacao', 'fechamento', 'mapa', 'citacao'}


def _numeros(dados: dict) -> list[dict]:
    """Datas e números ditos na narração aparecem GRANDES na tela por um instante (no máximo 1 a cada 2,5 s,
    e nunca em cena que já mostra números ou no gancho)."""
    out, ult = [], -9.0
    for c in dados.get('captions', []):
        for w in c['words']:
            txt = str(w.get('w', '')).strip(' .,;:!?"\'')
            num = re.sub(r'\D', '', txt)
            ano = len(num) == 4 and 1000 <= int(num) <= 2100
            if not num or ano or int(num) < 100:             # números grandes; ano NÃO (já vai no selo e na legenda: virava 3x "2006")
                continue
            s = w.get('s', c['start'])
            cena = next((sc for sc in dados['scenes'] if sc['start'] <= s < sc['end']), None)
            if cena and num in re.sub(r'\D', '', str(cena.get('lugar') or '') + str(cena.get('destaque') or '')):
                continue                                     # a cena já escreve esse número na tela
            if not cena or cena.get('tipo') in SEM_NUMERO or cena.get('moldura') or s - ult < 2.5 or s - cena['start'] < 0.25:
                continue
            out.append({'s': round(s, 3), 'w': txt.upper()})
            ult = s
    return out


def _efeitos(cenas: list[dict], dur: float, pasta: Path, pops: list[float] | None = None, numeros: list | None = None) -> Path:
    """Trilha de efeitos sintetizados (sem direitos autorais): impacto na abertura, whoosh nas transições rápidas,
    'pop' nas palavras-chave, flash = batida, salto no tempo = grave, e subida de tensão + explosão na revelação."""
    def sint(nome, expr):
        arq = pasta / f'{nome}.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', expr, str(arq)], check=True)
        return arq
    whoosh = sint('whoosh', 'anoisesrc=c=pink:d=0.55:a=0.6:r=48000,highpass=f=700,lowpass=f=7000,'
                            'afade=t=in:d=0.3:curve=exp,afade=t=out:st=0.3:d=0.25,volume=0.3')
    impacto = sint('impacto', 'sine=f=70:d=0.9:r=48000,afade=t=out:d=0.9:curve=exp,volume=1.6')
    pop = sint('pop', "aevalsrc='sin(2*PI*(900-5000*t)*t)*exp(-28*t)':s=48000:d=0.12,volume=0.4")
    batida = sint('batida', "aevalsrc='(sin(2*PI*(160-120*t)*t)*0.9+0.25*(random(0)*2-1)*exp(-40*t))*exp(-9*t)':s=48000:d=0.5,volume=1.1")
    grave = sint('grave', "aevalsrc='sin(2*PI*48*t)*exp(-3*t)':s=48000:d=1.2,volume=1.2")
    riser = sint('riser', "aevalsrc='(0.6*sin(2*PI*(200*t+300*t*t))+0.4*(random(0)*2-1))*(t/1.6)^2':s=48000:d=1.6,"
                          "highpass=f=300,volume=0.35")
    explosao = sint('explosao', "aevalsrc='(sin(2*PI*55*t)+0.5*(random(0)*2-1)*exp(-6*t))*exp(-2.5*t)':s=48000:d=1.6,volume=1.3")
    swish = sint('swish', 'anoisesrc=c=pink:d=0.3:a=0.5:r=48000,highpass=f=1500,lowpass=f=9000,'
                          'afade=t=in:d=0.12,afade=t=out:st=0.12:d=0.18,volume=0.16')
    soco = sint('soco', "aevalsrc='sin(2*PI*(110-60*t)*t)*exp(-14*t)':s=48000:d=0.35,volume=0.9")
    marcas = [(0.0, impacto)]
    for i, sc in enumerate(cenas):
        if sc.get('soco'):                    # "soco" de câmera no meio de um plano longo
            marcas.append((sc['soco'], soco))
        if i == 0:
            continue
        tr = _transicao(sc, i)
        if tr in ('zoom', 'chicote'):
            marcas.append((max(0.0, sc['start'] - 0.25), whoosh))
        elif tr == 'flash':
            marcas.append((sc['start'], batida))
        elif tr == 'preto':
            marcas.append((max(0.0, sc['start'] - 0.1), grave))
        else:                                 # todo corte tem um "swish" leve: o ouvido acompanha a troca de imagem
            marcas.append((max(0.0, sc['start'] - 0.08), swish))
        if sc.get('tipo') in ('numero', 'linha_tempo', 'comparacao') or sc.get('destaque'):
            marcas.append((sc['start'] + 0.3, batida))      # mini-revelação: impacto
        if sc.get('tipo') == 'revelacao':     # o cartão vira cedo (no máximo 1 s depois de a cena começar), igual ao template
            virada = min(sc.get('virada') or 1e9, sc['start'] + 1.0)
            marcas += [(max(0.0, virada - 1.2), riser), (virada, explosao)]
    for n in numeros or []:                   # número/data grande na tela
        marcas.append((n['s'], pop))
    ent, fil = [], []
    for k, (t, arq) in enumerate(marcas):
        ent += ['-i', str(arq)]
        fil.append(f'[{k}:a]adelay={int(t * 1000)}|{int(t * 1000)}[i{k}]')
    fil.append(''.join(f'[i{k}]' for k in range(len(marcas))) +
               f'amix=inputs={len(marcas)}:normalize=0,apad=whole_dur={dur},atrim=0:{dur}[s]')
    saida = pasta / 'sfx.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ent, '-filter_complex', ';'.join(fil), '-map', '[s]', '-ac', '1', str(saida)], check=True)
    return saida


PASSO_FISCAL = 0.2      # a cada 0,2 s o fiscal mede a tela
PERSISTE = 3            # choque que dura 3 medições seguidas (≈0,6 s) é erro; um instante de animação não é


def _medir(pagina: Path, dur: float) -> list[tuple[float, dict]]:
    """Abre a página (sem tirar foto de nenhum quadro: é rápido) e devolve [(segundo, problema)] em toda a duração."""
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p:
        nav = p.chromium.launch(args=NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(Path(pagina).as_uri())
        pg.wait_for_function('window.READY===true', timeout=60000)
        t = 0.0
        while t < dur:
            pg.evaluate(f'seek({t:.3f})')
            for pb in pg.evaluate(f'inspecionar({t:.3f})'):
                out.append((round(t, 2), pb))
            t += PASSO_FISCAL
        nav.close()
    return out


def _persistentes(medidas: list[tuple[float, dict]]) -> list[dict]:
    """Junta o mesmo problema em medições seguidas num trecho [ini, fim]; descarta o que não dura PERSISTE medições."""
    trechos: dict[tuple, list] = {}
    for t, pb in medidas:
        chave = (pb['tipo'], pb['txt'])
        lst = trechos.setdefault(chave, [])
        if lst and t - lst[-1]['fim'] <= PASSO_FISCAL * 1.5:
            lst[-1]['fim'] = t; lst[-1]['n'] += 1
        else:
            lst.append({**pb, 'ini': t, 'fim': t, 'n': 1})
    return sorted((x for lst in trechos.values() for x in lst if x['n'] >= PERSISTE), key=lambda x: x['ini'])


def _escrever_pagina(dados: dict, trabalho: Path) -> Path:
    (trabalho / 'data.js').write_text('window.DATA=' + json.dumps(dados, ensure_ascii=False) + ';', encoding='utf-8')
    return _pagina(trabalho)


def fiscal_tela(dados: dict, trabalho: Path) -> list[str]:
    """FISCAL DA TELA (sem IA, sem crédito): mede a posição real de cada texto ao longo do vídeo.
    1) legenda batendo em outro texto → a legenda desce para a faixa de reserva naquele trecho (conserto automático);
    2) etiqueta da foto ainda batendo em outro texto → ela some naquele trecho (conserto automático);
    3) mede de novo; o que sobrar (texto sobre texto, texto fora da tela) volta como lista de erros graves.
    `dados` precisa estar pronto para o template (caminhos já em file://). Grava dados['cap_baixo'] e dados['etq_some']."""
    dados['cap_baixo'] = []
    dados['etq_some'] = []
    pagina = _escrever_pagina(dados, trabalho)
    achados = _persistentes(_medir(pagina, dados['duration']))
    da_legenda = [p for p in achados if p['cap'] and p['tipo'] == 'choque']
    if da_legenda:
        dados['cap_baixo'] = [[round(p['ini'] - 0.3, 2), round(p['fim'] + 0.3, 2)] for p in da_legenda]
        print(f'  [fiscal da tela] legenda desce em {len(da_legenda)} trecho(s) para não cobrir outro texto:')
        for p in da_legenda:
            print(f"     {p['ini']:.1f}–{p['fim']:.1f}s ({p['cena']}): {p['txt']}")
        pagina = _escrever_pagina(dados, trabalho)
        achados = _persistentes(_medir(pagina, dados['duration']))
    # 12/11: etiqueta da foto ("FOTO · 1902") batendo em outro texto → some naquele trecho (conserto automático)
    da_etiqueta = [p for p in achados if p.get('etq')]
    if da_etiqueta:
        dados['etq_some'] = [[round(p['ini'] - 0.3, 2), round(p['fim'] + 0.3, 2)] for p in da_etiqueta]
        print(f'  [fiscal da tela] etiqueta da foto some em {len(da_etiqueta)} trecho(s) para não cobrir outro texto:')
        for p in da_etiqueta:
            print(f"     {p['ini']:.1f}–{p['fim']:.1f}s ({p['cena']}): {p['txt']}")
        pagina = _escrever_pagina(dados, trabalho)
        achados = _persistentes(_medir(pagina, dados['duration']))
    erros = [f"{p['ini']:.1f}s ({p['cena']}): {p['txt']}" for p in achados]
    for e in erros:
        print('  [fiscal da tela] ✘', e)
    if not erros:
        print('  [fiscal da tela] ✔ nenhum texto em cima de outro nem fora da tela')
    return erros


def legibilidade(dados: dict, trabalho: Path) -> list[str]:
    """Plano-mestre F (só registro e testes; NÃO entra no porteiro): texto menor que o mínimo da identidade ou dentro
    das zonas dos botões do Reels/TikTok. `dados` já preparados (file://)."""
    from playwright.sync_api import sync_playwright
    pagina = _escrever_pagina(dados, trabalho)
    medidas = []
    with sync_playwright() as p:
        nav = p.chromium.launch(args=NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(Path(pagina).as_uri())
        pg.wait_for_function('window.READY===true', timeout=60000)
        t = 0.0
        while t < dados['duration']:
            pg.evaluate(f'seek({t:.3f})')
            medidas += [(round(t, 2), pb) for pb in pg.evaluate(f'legibilidade({t:.3f})')]
            t += PASSO_FISCAL
        nav.close()
    return [f"{x['ini']:.1f}s ({x['cena']}): {x['txt']}" for x in _persistentes(medidas)]


def preparar(dados: dict) -> dict:
    """Completa os dados para o template (mascote, mapa, viradas, números, caminhos file://). Não altera o original."""
    dados = json.loads(json.dumps(dados, default=str))
    dados['mascote'] = (RAIZ / 'assets' / 'mascote.svg').read_text(encoding='utf-8')
    pasta3d = RAIZ / 'assets' / 'mascote3d'
    dados['mascote3d'] = {p.stem: p.resolve().as_uri() for p in pasta3d.glob('*.png')} if pasta3d.exists() else {}
    dados['world'] = json.loads((RAIZ / 'node_modules' / 'world-atlas' / 'countries-50m.json').read_text())
    _marcar_viradas(dados)
    dados['numeros'] = _numeros(dados)
    for sc in dados['scenes']:
        for campo in ('img', 'rec', 'img_fundo'):
            if sc.get(campo) and not str(sc[campo]).startswith('file:'):
                sc[campo] = Path(sc[campo]).resolve().as_uri()
        if sc.get('video') and 'dir' in sc['video']:
            sc['video'] = {'base': Path(sc['video']['dir']).resolve().as_uri() + '/f_', 'n': sc['video']['n']}
    return dados


def renderizar(dados: dict, audio: Path, saida: Path, trabalho: Path, musica: Path | None = None, workers: int | None = None):
    """dados: dicionário com meta, scenes, captions (ver template.html).
    Depois de montar, dados['problemas_tela'] traz o que o fiscal da tela não conseguiu consertar (lista vazia = tudo certo)."""
    trabalho.mkdir(parents=True, exist_ok=True)
    original = dados
    dados = preparar(dados)
    original['problemas_tela'] = fiscal_tela(dados, trabalho)
    original['cap_baixo'] = dados['cap_baixo']
    pagina = _escrever_pagina(dados, trabalho)
    return _montar(dados, pagina, audio, saida, trabalho, musica, workers)


def _montar(dados, pagina, audio, saida, trabalho, musica, workers):

    n = int(dados['duration'] * FPS)
    workers = workers or max(1, min(4, os.cpu_count() or 1))
    passo = -(-n // workers)
    partes = [(str(pagina), i, min(n, i + passo), str(trabalho / f'parte{k}.mp4'))
              for k, i in enumerate(range(0, n, passo))]
    with ProcessPoolExecutor(len(partes)) as ex:
        list(ex.map(_trecho, partes))
    lista = trabalho / 'partes.txt'
    lista.write_text(''.join(f"file '{p[3]}'\n" for p in partes))
    video = trabalho / 'video.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lista), '-c', 'copy', str(video)], check=True)

    pops, ult = [], -9.0
    for c in dados.get('captions', []):
        for w in c['words']:
            t0 = w.get('s', c['start'])
            if w.get('hl') and t0 - ult > 0.6:
                pops.append(t0); ult = t0
    sfx = _efeitos(dados['scenes'], dados['duration'], trabalho, pops, dados.get('numeros'))
    # 13/11 (polvo: −16,3 LUFS, pico +0,9 dBTP, 96 kHz): a mistura sai crua (48 kHz) e a MASTERIZAÇÃO é separada e medida
    entradas = ['-i', str(audio), '-i', str(sfx)]
    if musica and musica.exists():
        entradas += ['-stream_loop', '-1', '-i', str(musica)]
        filtro = ('[0:a]asplit=2[v][vk];[2:a]volume=0.28[m0];[m0][vk]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[m];[1:a]volume=0.35[fx];'
                  '[v][fx][m]amix=inputs=3:normalize=0:duration=first,aresample=48000[a]')   # música abaixa sozinha quando o Coringa fala
    else:
        filtro = '[1:a]volume=0.35[fx];[0:a][fx]amix=inputs=2:normalize=0:duration=first,aresample=48000[a]'
    mix, master = trabalho / 'mix.wav', trabalho / 'master.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *entradas, '-filter_complex', filtro, '-map', '[a]',
                    '-t', f"{dados['duration']:.3f}", '-c:a', 'pcm_s16le', str(mix)], check=True)
    masterizar(mix, master)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(master),
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000',
                    '-shortest', '-movflags', '+faststart', str(saida)], check=True)
    return saida


ALVO_LUFS, ALVO_TP = -14.0, -1.5
LIMITE_AMOSTRA = 0.75       # ≈ −2,5 dBFS por amostra: folga para o pico verdadeiro e para o AAC (alvo final ≤ −1 dBTP)
LIMITADOR_MAX_DB = 4.0      # o limitador pode segurar até ~4 dB de pico; mais que isso, a mistura fica baixa (não esmaga)


def masterizar(entrada: Path, saida: Path) -> dict:
    """Duas passadas com o MESMO medidor do diagnóstico (ebur128): 1ª mede loudness e pico verdadeiro; 2ª aplica um
    ganho fixo (linear: não muda a dinâmica da fala) + 48 kHz + limitador de pico. Antes: loudnorm em uma passada
    (dinâmico, não chegava no alvo nem garantia o pico depois do AAC: −16,3 LUFS e +0,9 dBTP no polvo) e 96 kHz."""
    from src.fiscal import medir_audio
    try:
        m = medir_audio(entrada)
    except Exception:                               # silêncio ("-inf"): nada a medir, só reamostra e limita
        m = {}
    i, tp = m.get('lufs'), m.get('pico')
    ganho = 0.0
    if i is not None and i > -70:
        ganho = ALVO_LUFS - i
        if tp is not None:
            ganho = min(ganho, ALVO_TP + LIMITADOR_MAX_DB - tp)     # não empurra o pico além do que o limitador segura
    filtro = f'volume={ganho:.2f}dB,aresample=48000,alimiter=limit={LIMITE_AMOSTRA}:attack=2:release=50:level=false'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(entrada), '-af', filtro, '-ar', '48000', '-c:a', 'pcm_s16le',
                    str(saida)], check=True)
    return {'entrada': m, 'ganho_db': round(ganho, 2)}


if __name__ == '__main__':
    # uso: python -m src.render.render dados.json audio.wav saida.mp4
    d = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    renderizar(d, Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[3]).with_suffix(''))


def renderizar_capa(capa: dict, saida: Path, trabalho: Path):
    """Desenha a capa do post (título dentro do recorte 3:4 do perfil; só o nome @coringa.explica, sem logo)."""
    from playwright.sync_api import sync_playwright
    trabalho.mkdir(parents=True, exist_ok=True)
    capa = dict(capa)
    capa['mascote'] = (RAIZ / 'assets' / 'mascote.svg').read_text(encoding='utf-8')
    pose = RAIZ / 'assets' / 'mascote3d' / ('apontando.png' if capa.get('tipo') == 'noticia' else 'surpreso.png')
    if pose.exists():
        capa['mascote_img'] = pose.resolve().as_uri()
    if capa.get('img') and not str(capa['img']).startswith('file:'):
        capa['img'] = Path(capa['img']).resolve().as_uri()
    (trabalho / 'capa_data.js').write_text('window.CAPA=' + json.dumps(capa, ensure_ascii=False) + ';', encoding='utf-8')
    html = Path(__file__).with_name('capa.html').read_text(encoding='utf-8')
    html = html.replace('../../node_modules', (RAIZ / 'node_modules').as_uri())
    html = html.replace('src="data.js"', f'src="{(trabalho / "capa_data.js").as_uri()}"')
    pagina = trabalho / 'capa.html'
    pagina.write_text(html, encoding='utf-8')
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(pagina.as_uri())
        pg.wait_for_function('window.READY===true', timeout=60000)
        pg.screenshot(path=str(saida), type='jpeg', quality=92)
        nav.close()
    return saida
