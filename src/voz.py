"""Narração com Edge TTS (grátis) + tempo de cada palavra para as legendas.

Cada cena é narrada separadamente; as falas são unidas com uma pausa curta.
Palavras marcadas com *asteriscos* no roteiro ficam amarelas na legenda.
"""
import time, asyncio, difflib, json, os, re, subprocess, unicodedata, wave
from pathlib import Path

VOZ = os.getenv('VOZ', 'pt-BR-AntonioNeural')
VELOCIDADE = os.getenv('VOZ_VELOCIDADE', '+10%')
TOM = os.getenv('VOZ_TOM', '+0Hz')          # ex.: -6Hz deixa a voz mais grave

# siglas que em português se LEEM como palavra (as outras a voz soletra, o que já está certo)
SIGLAS = {'PEC': 'péqui', 'PIX': 'píquis', 'ONU': 'ônu', 'OTAN': 'ótan', 'FIFA': 'fífa', 'NASA': 'nása',
          'IBAMA': 'ibâma', 'ENEM': 'enêm', 'SUS': 'sús', 'MEC': 'méqui', 'COP': 'cópi', 'BRICS': 'bríquis',
          'FUNAI': 'funái', 'PETROBRAS': 'petrobrás', 'ANVISA': 'anvísa', 'DETRAN': 'detrân', 'UNICEF': 'unicéfi',
          'OPEP': 'opépi', 'MERCOSUL': 'mercossúl', 'FIESP': 'fiéspi', 'SENAI': 'senái', 'SESC': 'séssi'}


def pronuncia(texto: str) -> str:
    texto = texto.replace('*', '')
    for sig, fala in SIGLAS.items():
        texto = re.sub(rf'\b{sig}s?\b', fala, texto)
    return texto
PAUSA = 0.28   # entre cenas
INICIO = 0.05  # a voz começa já no 1º quadro


def _norm(w: str) -> str:
    w = unicodedata.normalize('NFKD', w.lower())
    return re.sub(r'[^a-z0-9%]', '', ''.join(c for c in w if not unicodedata.combining(c)))


ESTILO_PADRAO = 'tom sério e confiante de apresentador de telejornal brasileiro, ritmo ágil, sem pausas longas'


def _rest_tts(modelo: str, texto: str, voz: str, formato: str, chave: str = '') -> bytes:
    """Chamada direta à API (sem a biblioteca), em dois formatos de configuração de voz: o antigo e o novo."""
    import base64, requests
    vc = {'prebuiltVoiceConfig': {'voiceName': voz}} if formato == 'antigo' else {'voice': voz}
    corpo = {'contents': [{'role': 'user', 'parts': [{'text': texto}]}],
             'generationConfig': {'responseModalities': ['AUDIO'], 'speechConfig': {'voiceConfig': vc}}}
    r = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent',
                      headers={'x-goog-api-key': chave or os.getenv('GEMINI_API_KEY', '')}, json=corpo, timeout=300)
    if r.status_code >= 400:
        raise RuntimeError(f'{r.status_code} {r.text[:160]}')
    return base64.b64decode(r.json()['candidates'][0]['content']['parts'][0]['inlineData']['data'])


def gemini_tts(texto: str, wav: Path, voz: str = 'Charon', estilo: str = ESTILO_PADRAO):
    """Voz do Gemini. Tenta vários modelos e dois jeitos de chamar (a API muda de formato de vez em quando);
    em sobrecarga, espera e tenta de novo. Só desiste depois de tudo isso (aí entra a voz do Edge)."""
    from google.genai import types
    from .gemini import cliente
    # instrução curta e separada por uma linha marcada: quanto menor, menos chance de a voz ler a instrução em voz alta
    pedido = f'Narre em português do Brasil ({_estilo(estilo)}). Leia SOMENTE o texto abaixo da linha.\n---\n{pronuncia(texto)}'
    erros = []
    from . import gemini as _g
    for ch in range(max(1, len(_g.CHAVES))):          # 2ª chave do Gemini, se a cota da 1ª acabar
        _g._chave = ch
        for modelo in ('gemini-3.8-flash-tts', 'gemini-3.8-flash-lite-tts', 'gemini-3.1-flash-tts-preview', 'gemini-2.5-flash-preview-tts'):
            jeitos = [('sdk', None), ('rest', 'antigo'), ('rest', 'novo')]
            for jeito, formato in jeitos:
                for tentativa in range(3):
                    try:
                        if jeito == 'sdk':
                            r = cliente().models.generate_content(
                                model=modelo, contents=pedido,
                                config=types.GenerateContentConfig(
                                    response_modalities=['AUDIO'],
                                    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voz)))))
                            pcm = r.candidates[0].content.parts[0].inline_data.data
                        else:
                            pcm = _rest_tts(modelo, pedido, voz, formato, _g.CHAVES[ch] if _g.CHAVES else '')
                        with wave.open(str(wav), 'wb') as w:
                            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
                        print(f'  [voz] Gemini ok ({modelo}, {jeito}{"/" + formato if formato else ""})')
                        return wav
                    except Exception as e:
                        msg = str(e)
                        erros.append(f'{modelo}/{jeito}: {msg[:90]}')
                        if ('503' in msg or 'UNAVAILABLE' in msg or '500' in msg) and tentativa < 2:
                            time.sleep(20 * (tentativa + 1))
                            continue
                        break
    print('  [voz] tentativas do Gemini:\n     ' + '\n     '.join(erros[-6:]))
    raise RuntimeError(erros[-1] if erros else 'sem resposta')


def _estilo(e: str) -> str:
    """Aceita tanto o estilo curto quanto o antigo 'Leia em português...:' do config.json."""
    e = re.sub(r'^\s*(leia|diga|fale)\s+em\s+portugu[eê]s\s+do\s+brasil,?\s*(com\s+)?', '', e.strip(), flags=re.I)
    return e.rstrip(': ').strip() or ESTILO_PADRAO


def destaques(texto: str) -> set[str]:
    out = set()
    for trecho in re.findall(r'\*(.+?)\*', texto):
        out |= {_norm(w) for w in trecho.split() if _norm(w)}
    return out


async def _edge(texto: str, mp3: Path, voz: str | None = None, tom: str | None = None, vel: str | None = None):
    import edge_tts
    com = edge_tts.Communicate(texto, voz or VOZ, rate=vel or VELOCIDADE, pitch=tom or TOM, boundary='WordBoundary')
    palavras = []
    with open(mp3, 'wb') as f:
        async for ch in com.stream():
            if ch['type'] == 'audio':
                f.write(ch['data'])
            elif ch['type'] == 'WordBoundary':
                ini = ch['offset'] / 1e7
                palavras.append({'w': ch['text'], 'start': ini, 'end': ini + ch['duration'] / 1e7})
    return palavras


def _duracao(arq: Path) -> float:
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(arq)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _estimar(texto: str, dur: float):
    """Usado só no modo de teste offline: espalha as palavras pela duração do áudio."""
    ws = texto.split()
    pesos = [len(w) + 2 + (6 if re.search(r'[.!?:]$', w) else 3 if w.endswith(',') else 0) for w in ws]
    tot, acc, out = sum(pesos), 0, []
    for w, p in zip(ws, pesos):
        a = 0.05 + (dur - 0.2) * acc / tot; acc += p
        out.append({'w': w.strip('.,:;!?'), 'start': a, 'end': 0.05 + (dur - 0.2) * acc / tot - 0.05})
    return out


def _piper(texto: str, wav: Path):
    import sys
    subprocess.run([sys.executable, '-m', 'piper', '-m', os.environ['PIPER_MODEL'], '-f', str(wav), '--length-scale', '0.85'],
                   input=texto.encode(), check=True, capture_output=True)


_ESP = '[ \u00a0\u202f\u2009]'


def numeros_juntos(t: str) -> str:
    """Número nunca se parte na legenda: '3 000' → '3.000' (o modelo às vezes escreve milhar com espaço, padrão francês)
    e '20 %' / '50 °C' → '20%' / '50°C' (antes saía 'CERCA DE 3' numa legenda e '000 HABITANTES' na outra)."""
    t = re.sub(rf'(?<![\d.,])(\d{{1,3}}){_ESP}(\d{{3}})(?![\d])', r'\1.\2', t)
    t = re.sub(rf'(?<![\d.,])(\d{{1,3}}\.\d{{3}}){_ESP}(\d{{3}})(?![\d])', r'\1.\2', t)    # 1 000 000
    return re.sub(rf'(\d){_ESP}+(%|°)', r'\1\2', t)


def alinhar(pal: list[dict], texto: str) -> list[dict]:
    """A voz pode ler uma versão 'falada' (ex.: 'Píquéquis'). Aqui trocamos pelas palavras do texto
    escrito, mantendo os tempos da voz, para a legenda mostrar a grafia certa."""
    exib = [w for w in numeros_juntos(texto.replace('*', '')).split() if _norm(w)]
    if not pal:
        return []
    A, B = [_norm(p['w']) for p in pal], [_norm(w) for w in exib]
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if j1 == j2:
            continue                                   # palavra só da versão falada
        if i1 == i2:                                   # palavra só do texto escrito: encaixa no tempo vizinho
            ref = pal[min(i1, len(pal) - 1)]
            t = out[-1]['end'] if out else ref['start']
            for w in exib[j1:j2]:
                out.append({'w': w, 'start': t, 'end': t + 0.05})
            continue
        a, b = pal[i1]['start'], pal[i2 - 1]['end']
        pesos = [len(w) + 1 for w in exib[j1:j2]]
        tot, acc = sum(pesos), 0
        for w, pw in zip(exib[j1:j2], pesos):
            ini = a + (b - a) * acc / tot; acc += pw
            out.append({'w': w, 'start': ini, 'end': a + (b - a) * acc / tot})
    for o in out:
        o['raw'] = o['w']
        o['w'] = o['w'].strip('.,:;"“”()')
    return out


# palavras que não podem terminar um bloco de legenda ("ATÉ", "DO WADI EL", "OS" sozinhos)
FRACAS = set('''a o as os um uma uns umas de da do das dos em no na nos nas num numa por pelo pela pelos pelas pra pro
para com sem sob sobre entre e ou mas que se ao aos à às como até mais muito muita seu sua seus suas meu minha
este esta esse essa isso isto aquele aquela cada outro outra quase tão já não nem quando onde qual quem'''.split())
MAX_PAL, MAX_CAR = 4, 24
_FRACAS_N = {_norm(x) for x in FRACAS}


def _fraca(p) -> bool:
    return _norm(p['w']) in _FRACAS_N



def legendas(palavras, hl: set[str]):
    """Blocos de 2 a 4 palavras, cortando onde a fala respira (pontuação ou pausa).
    Nunca termina em artigo/preposição e evita bloco de 1 palavra só."""
    if not palavras:
        return []
    # 1) trechos: corte duro em pontuação ou pausa longa
    trechos, cur = [], []
    for i, p in enumerate(palavras):
        cur.append(p)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        raw = p.get('raw', p['w'])
        if prox is None or re.search(r'[.!?:;,]$', raw) or prox['start'] - p['end'] > 0.35:
            trechos.append(cur); cur = []
    # 2) dentro de cada trecho, blocos equilibrados de até 4 palavras / 24 letras
    car = lambda x: sum(len(y['w']) + 1 for y in x)
    grupos = []
    for t in trechos:
        n = len(t)
        k = max(1, -(-n // MAX_PAL), -(-car(t) // (MAX_CAR + 1)))
        alvo = n / k
        g = []

        def fecha(g):
            leva = []
            while len(g) > 1 and _fraca(g[-1]):         # palavra fraca vai para o começo do próximo bloco
                leva.insert(0, g.pop())
            grupos.append(g)
            return leva
        for j, p in enumerate(t):
            if g and (len(g) >= MAX_PAL or car(g + [p]) > MAX_CAR + 2):   # não cabe: fecha antes de pôr a palavra
                g = fecha(g)
            g.append(p)
            resta = n - j - 1
            if resta >= 2 and len(g) >= alvo - 0.01:
                g = fecha(g)
        if g:
            grupos.append(g)
    # 3) bloco de 1 palavra junta com o vizinho do mesmo trecho, se couber
    fim_trecho = {id(t[-1]) for t in trechos if re.search(r'[.!?:;]$', t[-1].get('raw', t[-1]['w']))}   # fim de frase
    i = 0
    while i < len(grupos):
        g = grupos[i]
        if len(g) == 1 and len(grupos) > 1:
            ant = grupos[i - 1] if i > 0 and id(grupos[i - 1][-1]) not in fim_trecho else None
            pos = grupos[i + 1] if i + 1 < len(grupos) and id(g[-1]) not in fim_trecho else None
            if pos and car(g + pos) <= MAX_CAR + 6:
                grupos[i:i + 2] = [g + pos]; continue
            if ant and car(ant + g) <= MAX_CAR + 6:
                grupos[i - 1:i + 1] = [ant + g]; i -= 1; continue
        i += 1
    blocos = []
    for k, g in enumerate(grupos):
        prox = grupos[k + 1][0] if k + 1 < len(grupos) else None
        colado = prox is not None and prox['start'] - g[-1]['end'] <= 0.35
        blocos.append({'start': round(g[0]['start'], 3),
                       'end': round(prox['start'] if colado else g[-1]['end'] + 0.15, 3),
                       'words': [{'w': x['w'].upper(), 'hl': _norm(x['w']) in hl, 's': round(x['start'], 3)} for x in g]})
    return blocos


def config() -> dict:
    p = Path(__file__).resolve().parents[1] / 'config.json'
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _palavras_do_audio(wav: Path) -> list[dict]:
    """'Escuta' o áudio e devolve cada palavra com o tempo em que foi falada (Whisper, roda no próprio GitHub)."""
    from faster_whisper import WhisperModel
    modelo = WhisperModel(os.getenv('WHISPER_MODELO', 'base'), device='cpu', compute_type='int8')
    # decodifica com o ffmpeg e entrega o áudio pronto (evita o leitor de áudio interno, que quebra em versões novas)
    import numpy as np
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(wav), '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    segs, _ = modelo.transcribe(audio, language='pt', word_timestamps=True, beam_size=1)
    out = []
    for sg in segs:
        for w in (sg.words or []):
            if w.word.strip():
                out.append({'w': w.word.strip(), 'start': float(w.start), 'end': float(w.end)})
    return out


def _tempos_por_cena(pal: list[dict], falas: list[str], dur: float):
    """Alinha as palavras ouvidas com o roteiro inteiro e descobre onde começa cada cena."""
    alinhadas = alinhar(pal, ' '.join(falas))
    cont = [len([w for w in f.replace('*', '').split() if _norm(w)]) for f in falas]
    por_cena, k = [], 0
    for n in cont:
        por_cena.append(alinhadas[k:k + n]); k += n
    inicios = []
    for i, ws in enumerate(por_cena):
        t = ws[0]['start'] if ws else (inicios[-1] + 1.0 if inicios else 0.0)
        inicios.append(max(0.0, t - 0.12) if i else 0.0)
    tempos = [(inicios[i], inicios[i + 1] if i + 1 < len(inicios) else dur) for i in range(len(inicios))]
    return tempos, por_cena


def _conferir_fala(pal: list[dict], falas: list[str], dur: float) -> str:
    """O que a voz falou bate com o roteiro? Devolve '' se sim, ou o motivo do problema.
    Pega a voz lendo a instrução de tom ("voz séria..."), pulando ou repetindo trecho, ou falando devagar demais."""
    roteiro = [_norm(w) for f in falas for w in f.replace('*', '').split() if _norm(w)]
    ouvido = [_norm(p['w']) for p in pal if _norm(p['w'])]
    if not roteiro or not ouvido:
        return 'não ouvi nada'
    sm = difflib.SequenceMatcher(None, ouvido, roteiro, autojunk=False)
    certas = sum(b.size for b in sm.get_matching_blocks())
    faltou = 1 - certas / len(roteiro)
    # o que foi FALADO A MAIS: trechos do áudio entre pontos firmes (2+ palavras iguais seguidas) maiores que o trecho
    # correspondente do roteiro. Palavra ouvida trocada por outra (erro normal do "ouvido") não conta.
    firmes = [b for b in sm.get_matching_blocks() if b.size >= 2] + [difflib.Match(len(ouvido), len(roteiro), 0)]
    extras, a0, b0 = [], 0, 0
    for b in firmes:
        extras.append(max(0, (b.a - a0) - (b.b - b0)))
        a0, b0 = b.a + b.size, b.b + b.size
    if faltou > 0.3:
        return f'faltou {faltou:.0%} do roteiro na fala'
    if extras and max(extras) >= 6:                     # um trecho inteiro fora do roteiro (ex.: leu a instrução de tom)
        return f'a voz leu um trecho de {max(extras)} palavras fora do roteiro'
    if sum(extras) > 6 + 0.08 * len(roteiro):
        return f'a voz falou {sum(extras)} palavras fora do roteiro'
    if dur > len(roteiro) / 1.9 + 6:                  # ~2,6 palavras/s é o normal; 1,9 já é arrastado
        return f'fala lenta demais ({len(roteiro)} palavras em {dur:.0f}s)'
    pausas = [b['start'] - a['end'] for a, b in zip(pal, pal[1:])]
    if pausas and max(pausas) > 2.2:
        return f'pausa de {max(pausas):.1f}s no meio da fala'
    return ''


def _narrar_gemini(cenas: list[dict], pasta: Path, cfg: dict):
    falas = [c['fala'] for c in cenas]
    # pedaços da mesma frase (planos da mesma ideia) seguem juntos, sem a pausa de parágrafo no meio da frase
    texto = ''
    for k, c in enumerate(cenas):
        sep = '' if k == 0 else (' ' if c.get('sub') else '\n\n')
        texto += sep + pronuncia(c.get('fala_tts') or c['fala'])
    motivo = ''
    for tentativa in range(2):                         # grava; se não bater com o roteiro, grava de novo; depois desiste
        bruto = pasta / f'gemini{tentativa}.wav'
        gemini_tts(texto, bruto, cfg.get('voz_gemini', 'Charon'), cfg.get('estilo_gemini', ESTILO_PADRAO))
        vel = float(cfg.get('velocidade_gemini', 1.1))
        rapido = pasta / f'gemini_rapido{tentativa}.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(bruto), '-af', f'atempo={vel}', '-ac', '1', str(rapido)], check=True)
        pal = _palavras_do_audio(rapido)
        if len(pal) < 0.6 * sum(len(f.split()) for f in falas):
            motivo = 'não consegui ouvir as palavras direito'
            print(f'  [voz] gravação {tentativa + 1}: {motivo}')
            continue
        # se a voz leu alguma instrução antes do roteiro, corta tudo o que vem antes da 1ª palavra do roteiro
        roteiro = [_norm(w) for f in falas for w in f.replace('*', '').split() if _norm(w)]
        ouvido = [_norm(p['w']) for p in pal]
        blocos = [b for b in difflib.SequenceMatcher(None, ouvido, roteiro, autojunk=False).get_matching_blocks() if b.size >= 2]
        i0 = blocos[0].a if blocos and blocos[0].b <= 2 else 0
        corte = max(0.0, pal[i0]['start'] - 0.08) if i0 > 0 else 0.0
        pal = [dict(p, start=p['start'] - corte + INICIO, end=p['end'] - corte + INICIO) for p in pal[i0:]]
        wav = pasta / 'voz.wav'
        ms = int(INICIO * 1000)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{corte:.3f}', '-i', str(rapido), '-af',
                        f'adelay={ms}|{ms},aresample=48000,apad=pad_dur=0.6', '-ac', '1', str(wav)], check=True)
        dur = _duracao(wav)
        motivo = _conferir_fala(pal, falas, dur)
        if motivo:
            print(f'  [voz] gravação {tentativa + 1} não bate com o roteiro: {motivo}')
            continue
        if corte:
            print(f'  [voz] cortei {corte:.1f}s do começo (a voz leu algo fora do roteiro)')
        tempos, por_cena = _tempos_por_cena(pal, falas, dur)
        caps = []
        for f, ws in zip(falas, por_cena):
            caps += legendas(ws, destaques(f))
        return wav, tempos, caps, round(dur, 3)
    raise RuntimeError(f'voz do Gemini reprovada 2 vezes ({motivo})')


def narrar(cenas: list[dict], pasta: Path, teste: bool = False, cfg: dict | None = None):
    """cfg: troca a voz/estilo/velocidade (ex.: o canal Ninguém Te Contou usa outra voz que o Coringa)."""
    pasta.mkdir(parents=True, exist_ok=True)
    cfg = {**config(), **(cfg or {})}
    if not teste and cfg.get('voz_motor', 'gemini') == 'gemini' and os.getenv('GEMINI_API_KEY'):
        try:
            r = _narrar_gemini(cenas, pasta, cfg)
            print(f"  [voz] Gemini ({cfg.get('voz_gemini', 'Charon')})")
            return r
        except Exception as e:
            print(f'  [voz] Gemini indisponível ({str(e)[:120]}); usando a voz do Edge')
    return _narrar_edge(cenas, pasta, teste)


def _narrar_edge(cenas: list[dict], pasta: Path, teste: bool = False):
    """Recebe as cenas (com 'fala'); devolve (audio_wav, tempos_das_cenas, legendas, duracao)."""
    pasta.mkdir(parents=True, exist_ok=True)
    t, tempos, caps, faixas = INICIO, [], [], []
    for i, c in enumerate(cenas):
        fala = c['fala']
        limpo = fala.replace('*', '')
        falada = pronuncia(c.get('fala_tts') or limpo)   # sem asterisco e com siglas faladas como palavra
        if teste:
            arq = pasta / f'c{i}.wav'; _piper(falada, arq); dur = _duracao(arq)
            pal = _estimar(limpo, dur)
        else:
            arq = pasta / f'c{i}.mp3'
            pal = asyncio.run(_edge(falada, arq))
            dur = _duracao(arq)
        pal = alinhar(pal, fala)
        for p in pal:
            p['start'] += t; p['end'] += t
        caps += legendas(pal, destaques(fala))
        faixas.append((arq, t))
        pausa = 0.04 if i + 1 < len(cenas) and cenas[i + 1].get('sub') else PAUSA
        tempos.append((t, t + dur + pausa))
        t += dur + pausa
    total = t + 0.5
    tempos[-1] = (tempos[-1][0], total)
    ent, fil = [], []
    for k, (arq, ini) in enumerate(faixas):
        ent += ['-i', str(arq)]
        ms = int(ini * 1000)
        fil.append(f'[{k}:a]aresample=48000,aformat=channel_layouts=mono,adelay={ms}|{ms}[a{k}]')
    fil.append(''.join(f'[a{k}]' for k in range(len(faixas))) + f'amix=inputs={len(faixas)}:normalize=0,apad=whole_dur={total}[s]')
    wav = pasta / 'voz.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ent, '-filter_complex', ';'.join(fil), '-map', '[s]', str(wav)], check=True)
    return wav, tempos, caps, round(total, 3)
