"""APROVAÇÃO NO TELEGRAM antes de montar: nada é montado sem o OK de uma pessoa.

Depois do roteiro e das fotos (e antes da voz e do render, que são a parte demorada), chega no Telegram:
  1. UMA imagem: o gancho e cada frase ao lado da imagem escolhida (com a marca FOTO / VÍDEO / IA / REPETE e os avisos),
     e embaixo as RESERVAS (fotos/vídeos do acervo que sobraram), com letras A, B, C...
  2. O roteiro inteiro em texto, com os botões ✅ Montar e 🔁 Outro tema.
Respostas (responder À MENSAGEM do bot — em grupo o bot só enxerga respostas e botões):
  ok / sim / monta          → monta o vídeo
  3=B 7=A                   → a frase 3 usa a reserva B, a 7 usa a A (e chega uma prévia nova)
  trocar 3 7                → troca pelas melhores reservas que sobraram (e chega uma prévia nova)
  12: texto novo            → reescreve a frase 12 inteira (uma por linha; dá para juntar com 3=B). A voz e a legenda
                              são feitas depois da aprovação, então já saem com o texto novo. A imagem continua a mesma.
  titulo: texto novo        → troca o título
  outro tema / não          → descarta e tenta outro tema
Sem resposta no tempo → NÃO monta (avisa no Telegram).
"""
import io
import json
import os
import re
import time
import unicodedata
from pathlib import Path

import requests

RODADAS_MAX = 6
TIPOS_COR = {'FOTO': (46, 160, 67), 'VÍDEO': (35, 110, 220), 'IA': (220, 120, 20), 'REPETE': (200, 40, 40)}


# ───────────────────────── Telegram ─────────────────────────
def _api(metodo: str, arquivo: tuple[str, bytes] | None = None, **dados):
    tok = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f'https://api.telegram.org/bot{tok}/{metodo}'
    if arquivo:
        r = requests.post(url, data=dados, files={arquivo[0]: ('previa.jpg', arquivo[1])}, timeout=120)
    else:
        r = requests.post(url, json=dados, timeout=60)
    j = r.json() if r.content else {}
    if not j.get('ok'):
        raise RuntimeError(f"{metodo}: {r.status_code} {str(j.get('description') or r.text)[:150]}")
    return j.get('result')


def _chat() -> str:
    return str(os.getenv('TELEGRAM_CHAT_ID') or '')


def disponivel() -> bool:
    return bool(os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'))


# ───────────────────────── o que vai na tela ─────────────────────────
def ideias(v: dict) -> list[dict]:
    """As frases numeradas da prévia (1 = gancho). Planos extras da mesma ideia e o fechamento não entram."""
    return [c for c in v['cenas'] if c['tipo'] not in ('fechamento', 'mapa') and not c.get('sub')]


def _limpo(s) -> str:
    return re.sub(r'\s+', ' ', str(s or '').replace('*', '')).strip()


def _fala(c: dict) -> str:
    """A frase INTEIRA (frase longa vira vários planos e cada plano só guarda o seu pedaço em 'fala')."""
    return c.get('fala_ideia') or c.get('fala') or ''


def midia_de(c: dict, reais: dict, imgs: dict) -> tuple[str, Path | None]:
    """(tipo, miniatura) da imagem que a frase vai mostrar."""
    iid = c.get('imagem')
    m = reais.get(iid)
    if m:
        if m['tipo'] == 'video':
            return 'VÍDEO', Path(m['thumb']) if m.get('thumb') else None
        return 'FOTO', Path(m['arq'])
    if imgs.get(iid):
        return 'IA', Path(imgs[iid])
    if c.get('midia') == 'cartao':           # 12/11: sem imagem que mostre o fato → palavras da narração na tela
        return 'CARTÃO', None
    if c.get('midia') == 'evento':           # 12/11: imagem de outra frase do MESMO acontecimento, reenquadrada
        return 'MESMO FATO', None
    return 'REPETE', None


def reservas(v: dict) -> list[dict]:
    """Fotos/vídeos do acervo que nenhuma frase usa, das melhores para as piores (específicas antes de genéricas)."""
    usados = {c.get('foto') for c in v['cenas'] if c.get('foto')}
    sobra = [x for x in (v.get('acervo') or []) if x.get('id') not in usados and x.get('arq')]
    sobra.sort(key=lambda x: (not x.get('video'), bool(x.get('generica')), -float(x.get('nota') or 0)))   # clipes primeiro
    return sobra[:8]


def avisos(v: dict, reais: dict, imgs: dict) -> list[str]:
    out = []
    if v.get('_reserva'):
        out.append('⚠ Gemini sobrecarregado: parte do roteiro saiu do modelo reserva (' + ', '.join(sorted(set(v['_reserva']))) + ') — leia com atenção')
    tipos = [midia_de(c, reais, imgs)[0] for c in ideias(v)]
    if tipos.count('IA'):
        out.append(f"• {tipos.count('IA')} imagem(ns) de IA")
    if tipos.count('REPETE'):
        out.append(f"• {tipos.count('REPETE')} frase(s) sem imagem própria (repete a foto vizinha)")
    if tipos.count('CARTÃO'):
        out.append(f"• {tipos.count('CARTÃO')} frase(s) sem imagem do fato: vão como cartão com as palavras da narração")
    if tipos.count('MESMO FATO'):
        out.append(f"• {tipos.count('MESMO FATO')} frase(s) com a imagem de outra frase do mesmo acontecimento")
    contagem: dict = {}
    for c in ideias(v):
        if c.get('foto'):
            contagem[c['foto']] = contagem.get(c['foto'], 0) + 1
    rep = sum(1 for n in contagem.values() if n > 1)
    if rep:
        out.append(f'• {rep} foto(s) usada(s) em 2 frases')
    return out


def _fonte(tam: int, negrito: bool = False):
    from PIL import ImageFont
    nomes = (['DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if negrito else
             ['DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'])
    for n in nomes:
        try:
            return ImageFont.truetype(n, tam)
        except Exception:
            pass
    return ImageFont.load_default(size=tam)


def _quebrar(d, txt: str, fonte, largura: int, linhas: int) -> list[str]:
    out, cur = [], ''
    for w in txt.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=fonte) <= largura:
            cur = t
        else:
            out.append(cur); cur = w
            if len(out) == linhas:
                break
    if cur and len(out) < linhas:
        out.append(cur)
    if len(out) == linhas and ' '.join(out) != txt:
        out[-1] = out[-1].rstrip('.,;') + '…'
    return out


def _miniatura(arq: Path | None, w: int, h: int):
    from PIL import Image, ImageOps
    try:
        return ImageOps.fit(Image.open(arq).convert('RGB'), (w, h), Image.LANCZOS)
    except Exception:
        return Image.new('RGB', (w, h), (60, 60, 60))


def desenhar(v: dict, reais: dict, imgs: dict) -> bytes:
    """A prévia: cabeçalho (título, gancho, avisos), as frases numeradas com a imagem de cada uma, e as reservas."""
    from PIL import Image, ImageDraw
    W, COL, MW, MH = 1260, 3, 400, 225
    gap = (W - COL * MW) // (COL + 1)
    lista, res = ideias(v), reservas(v)
    av = avisos(v, reais, imgs)
    f_tit, f_txt, f_num, f_pq = _fonte(34, True), _fonte(19), _fonte(30, True), _fonte(16)
    cab = 150 + 30 * len(av)
    linhas_grade = -(-len(lista) // COL)
    cel = MH + 112
    alt_res = (60 + 175 * (-(-len(res) // 6))) if res else 0
    H = cab + linhas_grade * (cel + gap) + alt_res + 30
    im = Image.new('RGB', (W, H), (16, 18, 24))
    d = ImageDraw.Draw(im)
    g = lista[0] if lista else {}
    d.text((gap, 24), _limpo(g.get('titulo') or v.get('titulo'))[:70], font=f_tit, fill=(255, 210, 31))
    d.text((gap, 72), 'Gancho: ' + _limpo(_fala(g))[:110], font=f_txt, fill=(230, 230, 230))
    d.text((gap, 104), f"{len(lista)} frases · RESPONDER na mensagem do roteiro: ok  |  3=B (frase 3 usa a reserva B)  |  trocar 3 7",
           font=f_pq, fill=(150, 160, 175))
    for k, a in enumerate(av):
        d.text((gap, 140 + 30 * k), a, font=f_txt, fill=(255, 170, 90))
    for k, c in enumerate(lista):
        x, y = gap + (k % COL) * (MW + gap), cab + (k // COL) * (cel + gap)
        tipo, arq = midia_de(c, reais, imgs)
        im.paste(_miniatura(arq, MW, MH), (x, y))
        d.rectangle([x, y, x + 54, y + 44], fill=(0, 0, 0))
        d.text((x + 8, y + 5), str(k + 1), font=f_num, fill=(255, 255, 255))
        cor = TIPOS_COR[tipo]
        tw = d.textlength(tipo, font=f_pq) + 16
        d.rectangle([x + MW - tw, y, x + MW, y + 26], fill=cor)
        d.text((x + MW - tw + 8, y + 4), tipo, font=f_pq, fill=(255, 255, 255))
        for j, ln in enumerate(_quebrar(d, _limpo(c.get('fala')), f_txt, MW, 4)):
            d.text((x, y + MH + 8 + j * 25), ln, font=f_txt, fill=(235, 235, 235))
    if res:
        y0 = cab + linhas_grade * (cel + gap) + 10
        d.text((gap, y0), 'RESERVAS (para trocar, responda por exemplo 3=B):', font=f_txt, fill=(255, 210, 31))
        rw, rh = 190, 107
        for k, x_ in enumerate(res):
            x, y = gap + (k % 6) * (rw + 12), y0 + 40 + (k // 6) * 175
            im.paste(_miniatura(Path(x_['arq']), rw, rh), (x, y))
            d.rectangle([x, y, x + 34, y + 34], fill=(255, 210, 31))
            d.text((x + 9, y + 4), chr(65 + k), font=f_num, fill=(0, 0, 0))
            if x_.get('video'):
                d.rectangle([x + rw - 60, y, x + rw, y + 22], fill=TIPOS_COR['VÍDEO'])
                d.text((x + rw - 54, y + 3), 'VÍDEO', font=f_pq, fill=(255, 255, 255))
            for j, ln in enumerate(_quebrar(d, _limpo(x_.get('mostra')), f_pq, rw, 3)):
                d.text((x, y + rh + 4 + j * 19), ln, font=f_pq, fill=(190, 190, 190))
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=86)
    return buf.getvalue()


def texto(v: dict) -> str:
    linhas = [f"📝 PRÉVIA — {_limpo(v.get('titulo'))}", '']
    for k, c in enumerate(ideias(v)):
        linhas.append(f'{k + 1}. {_limpo(_fala(c))}')
    linhas += ['FINAL: Segue o @coringa.explica (cartão com o botão SEGUIR, automático)', '',
               '👉 Use os BOTÕES abaixo, ou toque em RESPONDER nesta mensagem e escreva: ok · 3=B · trocar 3 7 · outro tema',
               '✏️ Corrigir texto: responda com uma linha por frase, ex.: 12: A vítima tem parentes vivos até hoje.  (ou titulo: ...)',
               '(em grupo, o bot só enxerga respostas a ele e os botões — mensagem solta não chega)']
    return '\n'.join(linhas)[:4000]


# ───────────────────────── respostas ─────────────────────────
def _norm(s: str) -> str:
    s = unicodedata.normalize('NFD', str(s or '').lower())
    return ''.join(ch for ch in s if not unicodedata.combining(ch)).strip()


def interpretar(txt: str) -> tuple[str, dict] | None:
    """'ok' → ('ok', {}); 'outro tema' → ('outro', {}); '3=B 7=a' → ('trocar', {3: 'B', 7: 'A'});
    'trocar 3 7' → ('trocar', {3: None, 7: None}); qualquer outra coisa → None."""
    t = _norm(txt).lstrip('/')
    t = re.sub(r'@\w+', '', t).strip()                      # "/ok@meubot"
    if re.fullmatch(r'(ok|okay|sim|s|pode|monta|montar|aprovado|aprovo|manda|vai|bora|beleza|blz)[.! ]*', t):
        return 'ok', {}
    if re.fullmatch(r'(outro|outro tema|nao|n|descarta|descartar|pula|pular|refaz|refazer)[.! ]*', t):
        return 'outro', {}
    ed = _edicao(txt)
    if ed:
        return 'editar', ed
    trocas = {int(n): l.upper() for n, l in re.findall(r'\b(\d{1,2})\s*[=:\-]\s*([a-h])\b', t)}
    if trocas:
        return 'trocar', trocas
    m = re.fullmatch(r'(?:trocar|troca|troque|mudar|muda)\s+([\d ,e]+)', t)
    if m:
        return 'trocar', {int(n): None for n in re.findall(r'\d{1,2}', m.group(1))}
    return None


def _edicao(txt: str) -> dict | None:
    """Correção de texto: uma linha por frase — '12: novo texto', 'frase 12 = novo texto', 'titulo: novo título'.
    Pode vir junto com trocas de imagem na mesma mensagem ('3=B' numa linha). Devolve {'textos': {12: '...'},
    'trocas': {3: 'B'}, 'titulo': '...'} ou None se não houver nenhuma correção de texto."""
    textos, trocas, titulo = {}, {}, None
    for linha in str(txt or '').splitlines():
        lin = linha.strip()
        if not lin:
            continue
        m = re.fullmatch(r'/?\s*t[ií]tulo\s*[:=]\s*(.+)', lin, re.I)
        if m:
            titulo = m.group(1).strip()
            continue
        if re.fullmatch(r'(?:\s*\d{1,2}\s*[=:\-]\s*[a-hA-H](?![\w])[\s,]*(?:e\s+)?)+', lin):   # só trocas de imagem: 7=F 10=C
            trocas.update({int(n): l.upper() for n, l in re.findall(r'(\d{1,2})\s*[=:\-]\s*([a-hA-H])', lin)})
            continue
        m = re.fullmatch(r'/?\s*(?:texto|frase)?\s*(\d{1,2})\s*[:=]\s*(.+)', lin, re.I)
        if m and len(m.group(2).split()) >= 2:              # texto novo: pelo menos 2 palavras
            textos[int(m.group(1))] = m.group(2).strip()
            continue
        return None                                          # linha que não é correção: não é uma edição
    if not textos and not titulo:
        return None
    return {'textos': textos, 'trocas': trocas, 'titulo': titulo}


def aplicar_textos(v: dict, textos: dict, titulo: str | None) -> list[str]:
    """Reescreve frases inteiras: a frase é dividida de novo em planos (mesmas regras do roteiro) e todos os planos
    continuam com a MESMA imagem e enquadramentos da frase original."""
    from .roteiro import CAMERAS_SUB, INFOGRAFICOS, MAX_INFOGRAFICO, MAX_PALAVRAS, _pedacos
    feitas = []
    if titulo:
        v['titulo'] = titulo[:80]
        feitas.append(f'título → {titulo[:80]}')
    lista = ideias(v)
    for n, novo in sorted(textos.items()):
        if not 1 <= n <= len(lista):
            feitas.append(f'frase {n} não existe'); continue
        c = lista[n - 1]
        g = c.get('grupo')
        velhos = [x for x in v['cenas'] if x is c or (g is not None and x.get('grupo') == g and x.get('sub'))]
        limite = 9 if c['tipo'] == 'gancho' else MAX_INFOGRAFICO if c['tipo'] in INFOGRAFICOS else MAX_PALAVRAS
        ped = _pedacos(novo, limite)
        if len(ped) == 1:
            novas = [{k: val for k, val in c.items() if k not in ('sub', 'n_sub', 'fala_ideia', 'fala_tts')} | {'fala': novo}]
        else:
            cam0 = c.get('camera') or CAMERAS_SUB[(g or 0) % len(CAMERAS_SUB)]
            novas = []
            for k, pd in enumerate(ped):
                if k < len(velhos):
                    base = {key: val for key, val in velhos[k].items() if key != 'fala_tts'}
                else:                                        # plano a mais: mesma imagem, outro movimento de câmera
                    base = {key: c[key] for key in ('cenario', 'busca', 'midia', 'prompt_imagem', 'usa_personagem', 'ano_max',
                                                    'grupo', 'foto', 'imagem') if key in c}
                    base |= {'tipo': 'historia', 'transicao': 'corte',
                             'camera': CAMERAS_SUB[(CAMERAS_SUB.index(cam0) + 2 * k) % len(CAMERAS_SUB)] if cam0 in CAMERAS_SUB else 'aproxima'}
                novas.append(base | {'fala': pd, 'sub': k, 'n_sub': len(ped), 'fala_ideia': novo})
        i0 = next(i for i, x in enumerate(v['cenas']) if x is c)
        ids = {id(x) for x in velhos}
        v['cenas'] = [x for x in v['cenas'][:i0] if id(x) not in ids] + novas + [x for x in v['cenas'][i0:] if id(x) not in ids]
        feitas.append(f'frase {n} → {novo[:70]}')
    return feitas


def _base_offset() -> int:
    """Descarta o que já estava na fila do bot (respostas de dias anteriores não valem)."""
    r = _api('getUpdates', offset=-1, timeout=0)
    return (r[-1]['update_id'] + 1) if r else 0


def esperar(chave: str, ids_msg: set[int], ate: float, offset: int) -> tuple[tuple[str, dict] | None, int]:
    """Espera uma resposta válida até o horário `ate`. Vale: botão desta prévia, ou texto no chat (em grupo, respondendo
    à mensagem do bot). Devolve (resposta ou None se acabou o tempo, novo offset)."""
    while time.time() < ate:
        espera = int(max(1, min(25, ate - time.time())))
        try:
            ups = _api('getUpdates', offset=offset, timeout=espera, allowed_updates=['message', 'channel_post', 'callback_query'])
        except RuntimeError as e:
            if '409' in str(e):
                raise                                     # webhook configurado: getUpdates não funciona
            time.sleep(3); continue
        except requests.RequestException:
            time.sleep(3); continue
        for u in ups or []:
            offset = u['update_id'] + 1
            cq = u.get('callback_query')
            if cq:
                if str(((cq.get('message') or {}).get('chat') or {}).get('id')) != _chat():
                    continue
                try:
                    _api('answerCallbackQuery', callback_query_id=cq['id'])
                except Exception:
                    pass
                acao, _, ch = str(cq.get('data') or '').partition(':')
                if ch == chave and acao in ('ok', 'outro'):
                    return (acao, {}), offset
                continue
            m = u.get('message') or u.get('channel_post') or {}     # grupo/conversa ou canal
            if str((m.get('chat') or {}).get('id')) != _chat() or not m.get('text'):
                continue
            r = interpretar(m['text'])
            if r:
                return r, offset
            if (m.get('reply_to_message') or {}).get('message_id') in ids_msg:
                _avisar('Não entendi. Responda: ok · 3=B · trocar 3 7 · 12: texto novo · outro tema')
    return None, offset


def _avisar(txt: str):
    try:
        _api('sendMessage', chat_id=_chat(), text=txt[:4000])
    except Exception as e:
        print(f'  [aprovação] não consegui avisar: {str(e)[:100]}')


# ───────────────────────── o ciclo ─────────────────────────
def aplicar_trocas(v: dict, trocas: dict, reais: dict, imgs: dict, midia_de_item) -> list[str]:
    """Troca a imagem das frases pedidas. `midia_de_item(x)` baixa/prepara o item do acervo e devolve a entrada de `reais`."""
    lista, res = ideias(v), reservas(v)
    por_letra = {chr(65 + k): x for k, x in enumerate(res)}
    feitas = []
    for n, letra in sorted(trocas.items()):
        if not 1 <= n <= len(lista):
            feitas.append(f'frase {n} não existe'); continue
        c = lista[n - 1]
        x = por_letra.get(letra) if letra else next((r for r in reservas(v) if r['id'] != c.get('foto')), None)
        if not x:
            feitas.append(f'frase {n}: não há reserva {letra or "sobrando"}'); continue
        try:
            entrada = midia_de_item(x)
        except Exception as e:
            feitas.append(f'frase {n}: não consegui usar a reserva ({str(e)[:60]})'); continue
        iid = c.get('imagem') or f'troca{n}'
        c['imagem'] = iid
        for cena in v['cenas']:                       # a frase e os planos extras dela
            if cena is c or (c.get('grupo') is not None and cena.get('grupo') == c.get('grupo') and cena.get('sub')):
                cena['foto'], cena['imagem'], cena['midia'] = x['id'], iid, 'foto'
        reais[iid] = entrada
        imgs.pop(iid, None)
        feitas.append(f"frase {n} → {letra or 'reserva'}: {_limpo(x.get('mostra'))[:50]}")
    return feitas


def aprovar(v: dict, reais: dict, imgs: dict, midia_de_item, minutos: float) -> str:
    """'ok' (pode montar) · 'outro' (descartar o tema) · 'sem_resposta' (não montar) · 'indisponivel' (Telegram não
    responde: monta como antes e o resumo avisa que foi sem aprovação)."""
    if not disponivel():
        return 'indisponivel'
    try:
        offset = _base_offset()
    except Exception as e:
        print(f'  [aprovação] Telegram indisponível ({str(e)[:120]}); sigo sem aprovação')
        return 'indisponivel'
    ate = time.time() + minutos * 60
    for rodada in range(RODADAS_MAX):
        chave = f'{int(time.time())}'
        try:
            foto = _api('sendPhoto', ('photo', desenhar(v, reais, imgs)), chat_id=_chat(),
                        caption=f"Prévia {rodada + 1} — {_limpo(v.get('titulo'))}"[:1000])
            teclado = {'inline_keyboard': [[{'text': '✅ Montar', 'callback_data': f'ok:{chave}'},
                                            {'text': '🔁 Outro tema', 'callback_data': f'outro:{chave}'}]]}
            msg = _api('sendMessage', chat_id=_chat(), text=texto(v), reply_markup=teclado)
        except Exception as e:
            print(f'  [aprovação] não consegui mandar a prévia ({str(e)[:120]}); sigo sem aprovação')
            return 'indisponivel'
        print(f'  [aprovação] prévia {rodada + 1} enviada; esperando resposta até {minutos:.0f} min')
        try:
            r, offset = esperar(chave, {foto['message_id'], msg['message_id']}, ate, offset)
        except RuntimeError as e:
            print(f'  [aprovação] getUpdates recusado ({str(e)[:120]}); sigo sem aprovação')
            return 'indisponivel'
        if r is None:
            _avisar(f"⏰ Sem resposta em {minutos:.0f} min: NÃO montei \"{_limpo(v.get('titulo'))}\". "
                    'Rode de novo em Actions → Gerar vídeos do dia quando puder responder.')
            return 'sem_resposta'
        acao, trocas = r
        print(f'  [aprovação] resposta: {acao} {trocas or ""}')
        if acao == 'ok':
            _avisar('✅ Aprovado. Montando o vídeo (≈10 min).')
            return 'ok'
        if acao == 'outro':
            _avisar('🔁 Ok, descarto este tema.')
            return 'outro'
        if acao == 'editar':
            feitas = aplicar_textos(v, trocas['textos'], trocas.get('titulo'))
            if trocas.get('trocas'):
                feitas += aplicar_trocas(v, trocas['trocas'], reais, imgs, midia_de_item)
            _avisar('Correções:\n' + '\n'.join(feitas) + '\n\nMando a prévia nova…')
            continue
        feitas = aplicar_trocas(v, trocas, reais, imgs, midia_de_item)
        _avisar('Trocas:\n' + '\n'.join(feitas) + '\n\nMando a prévia nova…')
    _avisar('Muitas rodadas de troca: monto com a última prévia? Responda ok, ou outro tema.')
    try:
        r, _ = esperar('fim', set(), ate, offset)
    except RuntimeError:
        return 'indisponivel'
    return r[0] if r and r[0] in ('ok', 'outro') else 'sem_resposta'
