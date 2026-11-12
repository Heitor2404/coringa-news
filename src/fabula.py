"""Canal NINGUÉM TE CONTOU (@ninguemtecontou.tv): "E se…?" em animação 2D com a Valdirene (confeiteira, 45 anos, dramática).

Fluxo: tema → pesquisa (Wikipédia) → roteiro do Claude (JSON com cena, pose, balão, narração, efeito, painel e objetos)
→ prévia no Telegram (o roteiro no formato do Heitor + um quadro de cada cena) → aprovação → voz → montagem (Chrome +
ffmpeg, com efeitos sonoros e música) → Telegram.
Tudo é desenhado por código no estilo vetorial "boneco de tubo" (canais/ntc/vetor: cenários, Val articulada, objetos); a montagem é canais/ntc/vetor/fabula.html.
Os textos para a IA ficam no cofre privado (PROMPT_FABULA_TEMA, PROMPT_FABULA).
"""
import json, os, random, re, shutil, subprocess, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import cofre, gemini

RAIZ = Path(__file__).resolve().parents[1]
CANAL = RAIZ / 'canais' / 'ntc'
HIST = RAIZ / 'data' / 'historico_ntc.json'
BRT = timezone(timedelta(hours=-3))
NOME = 'NINGUÉM TE CONTOU'

CENARIOS = ['cozinha', 'rua', 'rua_destruida', 'floresta', 'horta', 'lab', 'sala', 'mercado', 'praia', 'hospital', 'espaco', 'fazenda']
VETOR = CANAL / 'vetor'
LUZES = ['dia', 'por_do_sol', 'noite', 'holofote']
POSES = ['neutra', 'comemora', 'explica', 'susto', 'brava', 'desesperada']
# largura na tela (px) e proporção altura/largura de cada desenho (iguais aos de vetor/kit_objetos.js; todos olham para a direita)
OBJETOS = {'barata': 150, 'rato': 210, 'passaro': 160, 'lixo': 260, 'folhas': 240, 'chinelo': 150, 'murcha': 190,
           'globo': 230, 'mosca': 90, 'dinheiro': 180, 'pao': 190, 'gota': 90, 'fogo': 230, 'lagarto': 230,
           'celular': 110, 'nuvem': 320, 'sol': 220, 'lua': 200, 'terra': 260, 'vela': 70, 'lanterna': 170}
PROPORCAO = {'barata': .55, 'rato': .6, 'passaro': .8, 'lixo': .7, 'folhas': .45, 'chinelo': .35, 'murcha': 1, 'globo': 1.05,
             'mosca': .7, 'dinheiro': .55, 'pao': .45, 'gota': 1.4, 'fogo': 1.5, 'lagarto': .4, 'celular': 1.7, 'nuvem': .5,
             'sol': 1, 'lua': 1, 'terra': 1, 'vela': 1.6, 'lanterna': .6}
OLHA_ESQ: set[str] = set()
SOLTOS = {'folhas', 'lixo', 'dinheiro', 'pao', 'chinelo', 'murcha'}   # coisas jogadas: ângulo e lado variados
VOAM = {'passaro', 'mosca', 'nuvem', 'sol', 'lua', 'terra', 'gota', 'dinheiro'}   # só estes podem ficar no ar
ACOES = ['corre', 'foge', 'some', 'cai', 'pula', 'balanca', 'cresce', 'aparece']
# linha dos pés da Val (px no quadro 1080x1920); o chão de todos os cenários começa em 1340
CHAO = {c: 1720 for c in CENARIOS}
# tampo de bancada/mesa: (altura, x inicial, x final) — iguais a BANCADAS em vetor/kit_cenarios.js
BANCADA = {'cozinha': (1060, 0, 440), 'lab': (1120, 500, 1060)}
VAL_X = {'esquerda': 300, 'direita': 780, 'centro': 560}
VOZ = {'voz_gemini': os.getenv('NTC_VOZ', 'Puck'), 'velocidade_gemini': float(os.getenv('NTC_VELOCIDADE', '1.12')),
       'estilo_gemini': 'narrador brasileiro jovem de vídeo viral de internet: rápido, irônico, debochado e animado, '
                        'como quem conta uma fofoca absurda, mas falando claro'}
FPS = 30

PROMPT_TEMA = cofre.prompt('PROMPT_FABULA_TEMA')
PROMPT = cofre.prompt('PROMPT_FABULA')


# ───────────────────────── roteiro ─────────────────────────
def historico() -> list[str]:
    try:
        return json.loads(HIST.read_text(encoding='utf-8'))
    except Exception:
        return []


def escolher_tema(pedido: str = '') -> dict:
    r = gemini.json_(PROMPT_TEMA.format(pedido=pedido or '(nenhum: escolha você)', feitos='\n'.join(historico()[-60:]) or '(nenhum)'),
                     leve=True)
    if isinstance(r, list):
        r = r[0] if r else {}
    if not r.get('tema'):
        raise ValueError('o Claude não devolveu tema')
    return r


def pesquisar(tema: dict) -> str:
    from . import wiki
    termos = [t for t in (tema.get('buscas_wikipedia') or []) if t][:4] or [tema['tema']]
    try:
        txt, _ = wiki.pesquisar(termos, max_artigos=3, chars=3500)
    except Exception as e:
        print(f'  [ntc] pesquisa falhou ({str(e)[:80]}); sigo só com o que o Claude sabe')
        txt = ''
    return txt


def validar(r: dict) -> dict:
    cenas = [c for c in (r.get('cenas') or []) if isinstance(c, dict) and str(c.get('narracao') or '').strip()]
    if len(cenas) < 8:
        raise ValueError(f'roteiro curto demais ({len(cenas)} cenas)')
    for c in cenas:
        c['cenario'] = c.get('cenario') if c.get('cenario') in CENARIOS else 'cozinha'
        c['pose'] = c.get('pose') if c.get('pose') in POSES or c.get('pose') == 'fora' else 'neutra'
        c['sfx'] = c.get('sfx') if c.get('sfx') in SFX else None
        c['luz'] = c.get('luz') if c.get('luz') in LUZES else None
        try:
            c['cor'] = max(0, min(100, int(c.get('cor', 100))))
        except (TypeError, ValueError):
            c['cor'] = 100
        c['objetos'] = [o for o in (c.get('objetos') or []) if isinstance(o, dict) and o.get('tipo') in OBJETOS][:3]
        c['balao'] = str(c.get('balao') or '')[:40]
    r['cenas'] = cenas
    return r


def escrever(tema: dict, fatos: str) -> dict:
    prompt = PROMPT.format(tema=tema['tema'], fatos=fatos[:12000] or '(sem pesquisa: use só fatos que você tem certeza)',
                           cenarios=', '.join(CENARIOS), poses=', '.join(POSES), objetos=', '.join(OBJETOS),
                           acoes=', '.join(ACOES), sfx=', '.join(SFX))
    erro = None
    for _ in range(2):
        try:
            r = gemini.json_(prompt)
            if isinstance(r, list):
                r = r[0] if r else {}
            return validar(r)
        except Exception as e:
            erro = e
            prompt += f'\n\nATENÇÃO: a resposta anterior falhou ({str(e)[:120]}). Siga o formato JSON exatamente.'
    raise RuntimeError(f'roteiro do Ninguém Te Contou falhou: {erro}')


def texto_previa(r: dict) -> str:
    """O roteiro no formato que o Heitor usa para ler e aprovar."""
    L = ['[INÍCIO DO ROTEIRO]', f"TEMA: {r.get('tema', '')}", '']
    for k, c in enumerate(r['cenas'], 1):
        dia = (c.get('painel') or {}).get('valor')
        L.append(f"Cena {k}" + (f" ({(c.get('painel') or {}).get('rotulo', 'Dia')}: {dia})" if dia is not None else '') + ':')
        L.append(f"Cenário: {c['cenario']} · cor {c['cor']}% · pose: {c['pose']}"
                 + (f" · {', '.join(str(o.get('quantidade', 1)) + ' ' + o['tipo'] + ' ' + str(o.get('acao', '')) for o in c['objetos'])}" if c['objetos'] else ''))
        if c['balao']:
            L.append(f'Balão: "{c["balao"]}"')
        L.append(f"Narração: {c['narracao']}")
        if c['sfx']:
            L.append(f"SFX: {c['sfx']}")
        L.append('')
    L += ['Encerramento:', f"Texto na tela: {r.get('cta_tela', '')}", f"Narração: {r.get('cta_narracao', '')}", '[FIM DO ROTEIRO]']
    return '\n'.join(L)


# ───────────────────────── montagem ─────────────────────────
SFX = sorted(p.stem for p in (CANAL / 'sfx').glob('*.wav')) or ['pop', 'whoosh']


def _proporcao(nome: str) -> float:
    return PROPORCAO[nome]


def _objetos(c: dict) -> list[dict]:
    """Converte 'objetos' do roteiro (tipo, quantidade, ação, lugar) em posições na tela (y = base do objeto)."""
    out = []
    cen = c['cenario']
    chao = CHAO[cen]
    for o in c['objetos']:
        t = o['tipo']
        w, ar = OBJETOS[t], _proporcao(t)
        n = max(1, min(8, int(o.get('quantidade') or 1)))
        acao = o.get('acao') if o.get('acao') in ACOES else 'aparece'
        lugar = str(o.get('lugar') or 'chao')
        if lugar in ('ceu', 'meio') and t not in VOAM:
            lugar = 'chao'                                   # lixo, folhas, planta etc. não flutuam: ficam no chão
        if t in ('sol', 'lua', 'terra', 'nuvem') and lugar != 'ceu':
            lugar = 'ceu'
        banc = BANCADA.get(cen) if lugar == 'bancada' else None
        x0, x1 = (banc[1] + 20, banc[2] - 20) if banc else (60, 1020)
        base = {'t': t, 'w': w, 'ar': ar, 'anim': acao, 'ceu': lugar == 'ceu', 'atras': bool(banc) or lugar == 'ceu'}
        for i in range(n):
            if banc:
                y = banc[0] + (i % 2) * 14
            elif lugar == 'ceu':
                y = 1060 + (i % 2) * 60                      # céu: abaixo do painel e da legenda, atrás da Val
            elif lugar == 'meio':
                y = 1250
            else:
                y = chao - 10 + ((i * 53) % 4) * 50             # espalha na profundidade do chão (na frente da Val)
            if acao in ('corre', 'foge'):
                vai_dir = acao == 'corre'
                x = x0 - w - 20 if vai_dir else x1 + 20
                out.append({**base, 'x': x, 'y': y, 'de': round(0.2 + 0.32 * i, 2), 'vel': (1 if vai_dir else -1) * (520 + (i * 71) % 180),
                            'flip': (t in OLHA_ESQ) == vai_dir, 'lim': [x0, x1] if banc else None})
            else:
                rr = random.Random(f"{t}{i}{cen}{n}")         # espalhado de forma natural (nada de fileira certinha)
                if n == 1:
                    x = {'esquerda': x0 + 20, 'direita': x1 - w - 20}.get(lugar, (x0 + x1) / 2 - w / 2)
                else:
                    x = x0 + (x1 - x0 - w) * (i / (n - 1)) + rr.uniform(-.35, .35) * (x1 - x0 - w) / (n - 1)
                    x = max(x0 - w * .3, min(x1 - w * .7, x))
                    if not banc and lugar not in ('ceu', 'meio'):
                        y = chao - 60 + rr.uniform(0, 1) * 200
                esc = rr.uniform(.75, 1.2) if n > 1 else 1
                out.append({**base, 'x': int(x), 'y': int(y), 'w': int(w * esc), 'de': round(0.3 + 0.18 * i + rr.uniform(0, .15), 2),
                            'rot': round(rr.uniform(-12, 12) if t in SOLTOS else 0, 1), 'flip': rr.random() < .5 and t in SOLTOS})
        if t == 'folhas' and lugar not in ('ceu', 'meio') and not banc:   # folhas soltas espalhadas em volta dos montes
            rr = random.Random(f"fs{cen}{n}")
            out += [{**base, 'w': int(w * rr.uniform(.25, .4)), 'x': int(rr.uniform(x0, x1 - 60)), 'y': int(chao - 60 + rr.uniform(0, 200)),
                     'anim': 'aparece', 'de': round(rr.uniform(.2, 1.2), 2), 'rot': round(rr.uniform(-40, 40), 1), 'flip': rr.random() < .5}
                    for _ in range(5)]
    out.sort(key=lambda p: p['y'])                             # quem está mais perto da câmera fica na frente
    return out


def dados_template(r: dict, tempos: list, caps: list, total: float) -> dict:
    cenas, painel_ant = [], {}
    for k, (c, (a, b)) in enumerate(zip(r['cenas'], tempos)):
        s = {'a': round(a, 3), 'b': round(b, 3), 'cen': c['cenario'], 'chao': CHAO[c['cenario']],
             'cinza': round(1 - c['cor'] / 100, 2), 'noite': bool(c.get('noite')) or c.get('luz') == 'noite', 'luz': c.get('luz'), 'props': _objetos(c)}
        if c['cenario'] == 'espaco':
            c['pose'] = 'fora'                              # no espaço só o planeta/o que a cena mostra, sem a Val
        if c['cenario'] == 'rua_destruida' and not any(o['tipo'] == 'fogo' for o in c['objetos']):
            s['props'] = s['props'] + [{'t': 'fogo', 'w': w, 'ar': 1.5, 'anim': 'aparece', 'ceu': False, 'atras': atras, 'x': x, 'y': y, 'de': de}
                                       for x, y, w, atras, de in ((40, 1300, 230, True, .1), (840, 1290, 210, True, .2), (330, 1190, 130, True, .3),
                                                                  (640, 1180, 120, True, .35), (-40, 1880, 300, False, .15), (900, 1900, 280, False, .25))]
            # fogo de verdade (animado) na rua destruída: atrás nas casas, no meio e grande na frente, nos cantos
        if c['pose'] != 'fora':
            lado = str(c.get('posicao') or 'centro')
            if lado == 'centro' and any(o.get('lugar') == 'bancada' for o in c['objetos']) and c['cenario'] in BANCADA:
                lado = 'direita' if BANCADA[c['cenario']][1] < 300 else 'esquerda'   # não tampar o que acontece na bancada
            s['val'] = {'pose': c['pose'], 'x': VAL_X.get(lado, VAL_X['centro']), 's': 1 if lado == 'centro' else 0.95}
        if c['balao']:
            s['balao'] = c['balao']
        p = c.get('painel') or {}
        if p.get('rotulo') and p.get('valor') is not None:
            try:
                v = float(str(p['valor']).replace('.', '').replace(',', '.'))
                s['painel'] = {'rot': str(p['rotulo']).upper()[:26], 'de': painel_ant.get(p['rotulo'], 0), 'para': v,
                               'fmt': str(p.get('formato') or '{}')}
                painel_ant[p['rotulo']] = v
            except ValueError:
                pass
        if k == 0 and r.get('titulo_tela'):
            s['titulo'] = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', r['titulo_tela'])
        cenas.append(s)
    # encerramento: a última cena ganha a placa da parte 2 / comentário
    ult = cenas[-1]
    ult['b'] = round(total, 3)
    ult['fim'] = {'de': max(0.5, (ult['b'] - ult['a']) - 2.8, 2.6 if ult.get('balao') else 0),   # o balão da última cena aparece antes da placa
                   'p': str(r.get('cta_placa') or 'PARTE 2 AMANHÃ')[:28],
                  'c': re.sub(r'\*([^*]+)\*', r'<span style="color:#F2C14E">\1</span>', str(r.get('cta_tela') or ''))[:90]}
    return {'cenas': cenas, 'captions': caps, 'duration': total}


def _pagina(dados: dict, trab: Path) -> Path:
    trab.mkdir(parents=True, exist_ok=True)
    (trab / 'fontes').mkdir(exist_ok=True)                  # fontes do próprio repositório (o GitHub não tem Poppins)
    fs = RAIZ / 'node_modules' / '@fontsource'
    for nome, orig in (('m800', 'montserrat/files/montserrat-latin-800-normal.woff2'), ('m900', 'montserrat/files/montserrat-latin-900-normal.woff2'),
                       ('jbm700', 'jetbrains-mono/files/jetbrains-mono-latin-700-normal.woff2')):
        if (fs / orig).exists():
            shutil.copy(fs / orig, trab / 'fontes' / f'{nome}.woff2')
    for arq in VETOR.glob('*'):
        if arq.suffix in ('.html', '.js') and not arq.name.startswith('teste'):
            shutil.copy(arq, trab / arq.name)
    (trab / 'data.js').write_text('window.DATA=' + json.dumps(dados, ensure_ascii=False) + ';', encoding='utf-8')
    return trab / 'fabula.html'


def quadros_previa(r: dict, trab: Path) -> bytes:
    """Um quadro do meio de cada cena (tempo estimado) numa folha só, para a prévia do Telegram."""
    from PIL import Image
    from playwright.sync_api import sync_playwright
    est = [(k * 6.0, k * 6.0 + 6.0) for k in range(len(r['cenas']))]
    caps = [{'start': a + 0.2, 'end': b, 'words': [{'w': w.upper(), 'hl': False} for w in c['narracao'].split()[:4]]}
            for c, (a, b) in zip(r['cenas'], est)]
    pag = _pagina(dados_template(r, est, caps, est[-1][1]), trab / 'previa')
    fotos = []
    with sync_playwright() as p:
        nav = p.chromium.launch(args=['--allow-file-access-from-files'])
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(pag.as_uri()); pg.wait_for_function('window.READY===true', timeout=60000)
        for k, (a, b) in enumerate(est):
            pg.evaluate(f'seek({a + 2.2:.2f})')
            arq = trab / 'previa' / f'q{k:02d}.jpg'
            pg.screenshot(path=str(arq), type='jpeg', quality=70)
            fotos.append(arq)
        nav.close()
    cols, w, h = 5, 216, 384
    linhas = -(-len(fotos) // cols)
    folha = Image.new('RGB', (cols * w, linhas * h), '#111')
    for i, f in enumerate(fotos):
        folha.paste(Image.open(f).resize((w, h)), ((i % cols) * w, (i // cols) * h))
    import io
    buf = io.BytesIO(); folha.save(buf, 'JPEG', quality=80)
    return buf.getvalue()


def renderizar(dados: dict, voz_wav: Path, saida: Path, trab: Path, r: dict):
    from playwright.sync_api import sync_playwright
    pag = _pagina(dados, trab / 'render')
    qd = trab / 'quadros'; qd.mkdir(parents=True, exist_ok=True)
    n = int(dados['duration'] * FPS)
    with sync_playwright() as p:
        nav = p.chromium.launch(args=['--allow-file-access-from-files'])
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(pag.as_uri()); pg.wait_for_function('window.READY===true', timeout=60000)
        for i in range(n):
            pg.evaluate(f'seek({i / FPS:.4f})')
            pg.screenshot(path=str(qd / f'{i:05d}.jpg'), type='jpeg', quality=90)
        nav.close()
    # áudio: voz + música baixinha + efeitos no começo de cada cena
    musicas = sorted((CANAL / 'musica').glob('*.mp3')) or sorted((RAIZ / 'assets' / 'musica' / 'explica').glob('*.mp3'))   # trilhas cômicas próprias
    musica = random.Random(r.get('tema', '')).choice(musicas) if musicas else None
    ent = ['-i', str(voz_wav)]                     # entrada 0 = quadros; 1 = voz; 2 = música; depois os efeitos
    fil, mix = [], ['[1:a]']
    if musica:
        ent += ['-stream_loop', '-1', '-i', str(musica)]
        fil.append(f"[2:a]volume=0.13,afade=t=out:st={max(0, dados['duration'] - 2):.2f}:d=2[m]"); mix.append('[m]')
    k0 = 3 if musica else 2
    efs = [(c['a'] + 0.12, rc['sfx']) for c, rc in zip(dados['cenas'], r['cenas']) if rc.get('sfx')]
    efs.insert(0, (0.05, 'whoosh'))
    efs += [(c['a'] + 0.2, 'contagem') for c in dados['cenas'] if c.get('painel') and c['painel'].get('de') != c['painel'].get('para')]   # tic-tic-pum do contador
    for j, (t0, nome) in enumerate(efs):
        arq = CANAL / 'sfx' / f'{nome}.wav'
        if not arq.exists():
            continue
        ent += ['-i', str(arq)]
        idx = k0 + j
        ms = int(t0 * 1000)
        fil.append(f'[{idx}:a]volume=0.55,adelay={ms}|{ms}[e{j}]'); mix.append(f'[e{j}]')
    fil.append(''.join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,apad=whole_dur={dados['duration']:.2f}[a]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(qd / '%05d.jpg'), *ent,
                    '-filter_complex', ';'.join(fil), '-map', '0:v', '-map', '[a]', '-t', f"{dados['duration']:.2f}",
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', str(saida)], check=True)


# ───────────────────────── aprovação ─────────────────────────
def aprovar(r: dict, trab: Path, minutos: float) -> str:
    from . import aprovacao as ap
    if not ap.disponivel():
        return 'indisponivel'
    try:
        offset = ap._base_offset()
        chave = f'n{int(time.time())}'
        foto = ap._api('sendPhoto', ('photo', quadros_previa(r, trab)), chat_id=ap._chat(),
                       caption=f"🎬 {NOME} — prévia: {r.get('tema', '')}"[:1000])
        teclado = {'inline_keyboard': [[{'text': '✅ Montar', 'callback_data': f'ok:{chave}'},
                                        {'text': '🔁 Outro tema', 'callback_data': f'outro:{chave}'}]]}
        txt = texto_previa(r)
        msgs = [ap._api('sendMessage', chat_id=ap._chat(), text=txt[i:i + 3900]) for i in range(0, len(txt), 3900)]
        fim = ap._api('sendMessage', chat_id=ap._chat(), text=f'{NOME}: aprova? (botão, ou RESPONDA a esta mensagem com "ok" / "outro tema")',
                      reply_markup=teclado)
    except Exception as e:
        print(f'  [ntc] não consegui mandar a prévia ({str(e)[:120]}); sigo sem aprovação')
        return 'indisponivel'
    print(f'  [aprovação] prévia do {NOME} enviada; esperando até {minutos:.0f} min')
    resp, _ = ap.esperar(chave, {foto['message_id'], fim['message_id'], *[m['message_id'] for m in msgs]},
                         time.time() + minutos * 60, offset)
    if resp is None:
        ap._avisar(f'⏰ {NOME}: sem resposta em {minutos:.0f} min, não montei.')
        return 'sem_resposta'
    acao = resp[0]
    print(f'  [aprovação] resposta: {acao}')
    if acao == 'ok':
        ap._avisar(f'✅ {NOME}: aprovado. Montando (≈10 min).')
    return acao if acao in ('ok', 'outro') else 'ok'


# ───────────────────────── tudo junto ─────────────────────────
def fazer(pedido: str = '', minutos: float | None = None) -> Path | None:
    from . import voz
    hoje = datetime.now(BRT).strftime('%Y-%m-%d')
    trab = RAIZ / 'saida' / hoje / 'ntc'
    trab.mkdir(parents=True, exist_ok=True)
    minutos = minutos if minutos is not None else float(os.getenv('APROVACAO_MIN', '40'))
    for tentativa in range(2):
        tema = escolher_tema(pedido if tentativa == 0 else '')
        print(f"  [ntc] tema: {tema['tema']}")
        r = escrever(tema, pesquisar(tema))
        r.setdefault('tema', tema['tema'])
        r.setdefault('titulo_tela', tema.get('titulo_tela', tema['tema']))
        print(f"  [ntc] roteiro: {len(r['cenas'])} cenas · {sum(len(c['narracao'].split()) for c in r['cenas'])} palavras")
        res = aprovar(r, trab, minutos) if os.getenv('APROVACAO', '1') != '0' else 'indisponivel'
        if res == 'outro':
            pedido = ''
            continue
        if res == 'sem_resposta':
            return None
        break
    else:
        return None
    falas = [{'fala': c['narracao']} for c in r['cenas']]
    if r.get('cta_narracao'):
        falas[-1]['fala'] = falas[-1]['fala'].rstrip() + ' ' + r['cta_narracao']
    wav, tempos, caps, total = voz.narrar(falas, trab / 'voz', cfg=VOZ)
    total = max(total, tempos[-1][1]) + 2.5                      # respiro para a placa final
    dados = dados_template(r, tempos, caps, total)
    saida = RAIZ / 'saida' / hoje / f"ntc-{re.sub(r'[^a-z0-9]+', '-', r['tema'].lower())[:50].strip('-')}.mp4"
    renderizar(dados, wav, saida, trab, r)
    HIST.write_text(json.dumps(historico() + [r['tema']], ensure_ascii=False, indent=1), encoding='utf-8')
    legenda = (f"{r.get('legenda_post') or r['tema']}\n\n{' '.join(r.get('hashtags') or ['#curiosidades', '#esse', '#valdirene'])}")
    import main as _m
    if _m._tg('sendVideo', {'caption': f"🎬 {NOME}\n{r['tema']}\n⏱ {total:.0f}s"[:1000], 'supports_streaming': 'true'},
              ('video', _m._versao_telegram(saida))):
        _m._tg('sendMessage', {'text': f'📋 Legenda para as redes ({NOME}):\n\n{legenda}'[:4000]})
    print(f'  [ntc] pronto: {saida.name} ({total:.0f}s)')
    return saida
