"""ACERVO V2: imagem certa para a fala certa, sem repetição, bem enquadrada e com licença conferida.

Sem rede e sem IA: tudo aqui roda sobre o que o acervo atual (src/acervo.py) já baixou e descreveu (campos titulo,
desc, mostra, lugar, pessoas, ano, generica, credito, w, h). O que muda em relação ao motor atual:
  - relevancia(): nota 0–1 da imagem PARA A CENA (acontecimento + fala), com motivos — não só "tem a palavra";
  - rejeita a genérica quando a cena exige representação específica (pessoa, documento, lugar exato, ano);
  - duplicadas(): hash perceptual (DCT 8×8) pega a mesma foto em arquivos/tamanhos diferentes;
  - recorte_conteudo(): tira cartão/borda de scanner (a foto de 1913 do Panamá era uma faixa num cartão preto);
  - enquadramento(): foco visual (energia de bordas) + limite de zoom pela resolução → fundo.de/para do palco V2;
  - licenca(): só licenças compatíveis com canal monetizado; atribuição pronta.
"""
from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image

VAZIAS = set('a o as os de da do das dos e em no na nos nas um uma que se por para com ao the of and in on at to with from by'.split())


def _norm(s) -> str:
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def _tok(s) -> set[str]:
    return {t for t in re.findall(r'[a-z0-9]{3,}', _norm(s)) if t not in VAZIAS}


# sinônimos PT/EN que o acervo mistura (as descrições vêm em inglês do Commons e em português do catalogador)
SIN = {'navio': {'ship', 'vessel', 'boat', 'barco', 'cargueiro'}, 'eclusa': {'lock', 'locks', 'eclusas', 'esclusa'},
       'lago': {'lake', 'lago'}, 'comporta': {'gate', 'gates', 'comportas'}, 'camara': {'chamber', 'camara'},
       'construcao': {'construction', 'obra', 'building'}, 'canal': {'canal'}, 'agua': {'water'}, 'mapa': {'map'},
       'rio': {'river'}, 'represa': {'dam', 'barragem'}, 'seca': {'drought', 'estiagem'}}
_EXP = {}
for k, vs in SIN.items():
    for v in vs | {k}:
        _EXP.setdefault(v, set()).update(vs | {k})


def _expandir(ts: set[str]) -> set[str]:
    out = set(ts)
    for t in ts:
        out |= _EXP.get(t, set())
        if t.endswith('s'):
            out |= _EXP.get(t[:-1], set()) | {t[:-1]}
    return out


def _ano_de(c: dict) -> int | None:
    a = c.get('ano')
    try:
        return int(a) if a else None
    except (TypeError, ValueError):
        m = re.search(r'(1[5-9]\d\d|20\d\d)', str(a))
        return int(m.group(1)) if m else None


def exige_especifica(cena: dict) -> bool:
    """A cena pede uma representação específica (não serve 'qualquer foto do tema')?"""
    ac = cena.get('acontecimento') or {}
    return ac.get('recurso') in ('foto', 'documento', 'jornal', 'retrato', 'objeto', 'lugar', 'video') and bool(ac.get('quem') or ac.get('quando'))


def relevancia(item: dict, cena: dict) -> dict:
    """Nota 0–1 da imagem para a cena, com motivos legíveis. Pesos: acontecimento (quem/onde) 45%, o que a cena quer
    mostrar 25%, fala 15%, época 15%; penalidades: genérica quando a cena é específica, resolução baixa, ano incompatível."""
    ac = cena.get('acontecimento') or {}
    img = _expandir(_tok(' '.join(str(item.get(k, '')) for k in ('titulo', 'desc', 'mostra', 'lugar', 'legenda'))) |
                    _tok(' '.join(item.get('pessoas') or [])))
    def cob(txt):
        ts = _expandir(_tok(txt))
        return (len(ts & img) / max(1, min(len(ts), 6))) if ts else None
    partes, motivos = [], []
    for nome, txt, peso in (('acontecimento', f"{ac.get('quem', '')} {ac.get('onde', '')}", .45), ('mostrar', cena.get('mostrar', ''), .25),
                            ('fala', re.sub(r'\*', '', cena.get('fala', '')), .15)):
        c = cob(txt)
        if c is not None:
            partes.append((min(1.0, c), peso))
            motivos.append(f'{nome} {min(1.0, c):.0%}')
    ano, quando = _ano_de(item), _ano_de({'ano': ac.get('quando')})
    if quando:
        ok = 1.0 if ano and abs(ano - quando) <= 3 else (.4 if ano and abs(ano - quando) <= 15 else (0.0 if ano else .3))
        partes.append((ok, .15))
        motivos.append(f'época {"ok" if ok >= 1 else "próxima" if ok >= .4 else "sem data" if not ano else "errada"} ({ano or "?"} × {quando})')
    tot = sum(p for _, p in partes) or 1
    nota = sum(v * p for v, p in partes) / tot
    if item.get('generica') and exige_especifica(cena):
        nota *= .45
        motivos.append('genérica para cena específica (×0,45)')
    lado = max(int(item.get('w') or 0), int(item.get('h') or 0))
    if lado and lado < 900:
        nota *= .8
        motivos.append(f'resolução baixa ({lado}px)')
    if item.get('util') is False:
        nota *= .3
        motivos.append('catalogador marcou como inútil')
    return {'nota': round(nota, 3), 'motivos': motivos}


LIMIAR = 0.34


def escolher(cenas: list[dict], acervo: list[dict], hashes: dict | None = None) -> list[dict]:
    """Uma imagem por cena que precisa de foto, sem repetir (id nem hash perceptual), maior relevância primeiro.
    Cena sem imagem acima do limiar recebe {'img': None, 'limitacao': ...} — nunca uma foto qualquer."""
    hashes = hashes or {}
    usados_id, usados_h = set(), []
    pares = sorted(((relevancia(it, c)['nota'], i, j) for i, c in enumerate(cenas) for j, it in enumerate(acervo)), reverse=True)
    escolha = {}
    for nota, i, j in pares:
        if i in escolha or nota < LIMIAR:
            continue
        it = acervo[j]
        if it.get('id') in usados_id:
            continue
        h = hashes.get(it.get('id'))
        if h is not None and any(distancia(h, u) <= 10 for u in usados_h):
            continue
        escolha[i] = (j, nota)
        usados_id.add(it.get('id'))
        if h is not None:
            usados_h.append(h)
    out = []
    for i, c in enumerate(cenas):
        if i in escolha:
            j, nota = escolha[i]
            out.append({'cena': i, 'img': acervo[j].get('id'), 'nota': nota, 'motivos': relevancia(acervo[j], c)['motivos']})
        else:
            melhor = max((relevancia(it, c)['nota'] for it in acervo), default=0)
            out.append({'cena': i, 'img': None, 'nota': melhor,
                        'limitacao': f'nenhuma imagem do acervo representa "{(c.get("acontecimento") or {}).get("quem") or c.get("mostrar") or c.get("fala", "")[:40]}" (melhor nota {melhor:.2f} < {LIMIAR})'})
    return out


# ---------------- hash perceptual ----------------
def _dct_mat(n: int) -> np.ndarray:
    m = np.array([[math.cos(math.pi * (2 * j + 1) * i / (2 * n)) for j in range(n)] for i in range(n)])
    m[0] /= math.sqrt(2)
    return m * math.sqrt(2 / n)


_D32 = _dct_mat(32)


def phash(arq: str | Path) -> int:
    with Image.open(arq) as im:
        g = np.asarray(im.convert('L').resize((32, 32), Image.LANCZOS), dtype=float)
    d = _D32 @ g @ _D32.T
    b = d[:8, :8].flatten()[1:]
    bits = b > np.median(b)
    return int(''.join('1' if x else '0' for x in bits), 2)


def distancia(a: int, b: int) -> int:
    return bin(a ^ b).count('1')


def duplicadas(arqs: list[str | Path], limiar: int = 10) -> list[tuple[str, str, int]]:
    hs = [(str(a), phash(a)) for a in arqs]
    return [(hs[i][0], hs[j][0], distancia(hs[i][1], hs[j][1])) for i in range(len(hs)) for j in range(i + 1, len(hs))
            if distancia(hs[i][1], hs[j][1]) <= limiar]


# ---------------- recorte do conteúdo (scanner/cartão) ----------------
def recorte_conteudo(arq: str | Path) -> list[float]:
    """[x0, y0, x1, y1] (0–1) da FOTO dentro do arquivo, descartando margem de scanner, cartão liso e etiquetas.
    Textura por blocos de 6×6 px (desvio padrão): cartão e margem são lisos, a foto tem textura; a maior faixa
    contínua de linhas texturizadas (e depois de colunas, dentro dela) é a foto. Etiqueta pequena não forma faixa."""
    with Image.open(arq) as im:
        im = im.convert('L')
        esc = 600 / max(im.size)
        g = np.asarray(im.resize((max(1, int(im.width * esc)), max(1, int(im.height * esc)))), dtype=float)
    B = 6
    h, w = (g.shape[0] // B) * B, (g.shape[1] // B) * B
    blocos = g[:h, :w].reshape(h // B, B, w // B, B).std(axis=(1, 3))
    mascara = blocos > 7

    def faixa(frac, lim=.45):
        on = frac > lim
        melhor, ini = (0, 0, 0), None
        for i, v in enumerate(list(on) + [False]):
            if v and ini is None:
                ini = i
            if not v and ini is not None:
                if i - ini > melhor[0]:
                    melhor = (i - ini, ini, i)
                ini = None
        return melhor[1], melhor[2]
    y0, y1 = faixa(mascara.mean(axis=1))
    if y1 <= y0:
        return [0.0, 0.0, 1.0, 1.0]
    x0, x1 = faixa(mascara[y0:y1].mean(axis=0), .3)
    nh, nw = mascara.shape
    r = [x0 / nw, y0 / nh, x1 / nw, y1 / nh]
    if (r[2] - r[0]) * (r[3] - r[1]) > .85 or (r[2] - r[0]) < .1 or (r[3] - r[1]) < .05:
        return [0.0, 0.0, 1.0, 1.0]
    # foto montada em cartão/scanner tem margem nos QUATRO lados; céu ou mar liso numa foto comum, não
    if min(r[0], r[1], 1 - r[2], 1 - r[3]) < .025:
        return [0.0, 0.0, 1.0, 1.0]
    # correção do piloto: foto colada em cartão ocupa ao menos METADE do arquivo numa direção (cartão de teste: 83% da
    # largura; panorâmica de 1913: 90%). Mancha pequena nas duas direções é textura local — satélite de deserto (39% × 4%)
    # e diagrama em papel (38% × 3%) viravam "foto" de faixa de 69 px
    if max(r[2] - r[0], r[3] - r[1]) < .5:
        return [0.0, 0.0, 1.0, 1.0]
    m = 1.0 / max(nw, nh)                          # um bloco de folga para dentro (tira o fio da borda)
    return [round(r[0] + m, 4), round(r[1] + m, 4), round(r[2] - m, 4), round(r[3] - m, 4)]


# ---------------- foco e enquadramento ----------------
def foco(arq: str | Path, rc: list[float] | None = None) -> tuple[float, float]:
    """Centro de interesse (0–1 no recorte): centro de massa da energia de bordas suavizada, puxado para o centro."""
    with Image.open(arq) as im:
        im = im.convert('L')
        if rc and rc != [0, 0, 1, 1]:
            W, H = im.size
            im = im.crop((int(rc[0] * W), int(rc[1] * H), int(rc[2] * W), int(rc[3] * H)))
        g = np.asarray(im.resize((96, max(8, int(96 * im.height / im.width)))), dtype=float)
    e = np.abs(np.diff(g, axis=0, prepend=g[:1])) + np.abs(np.diff(g, axis=1, prepend=g[:, :1]))
    e = e ** 1.5
    if e.sum() <= 0:
        return (.5, .5)
    ys, xs = np.mgrid[0:e.shape[0], 0:e.shape[1]]
    cx, cy = (xs * e).sum() / e.sum() / e.shape[1], (ys * e).sum() / e.sum() / e.shape[0]
    return (round(.5 + (cx - .5) * .7, 3), round(.5 + (cy - .5) * .7, 3))


def enquadramento(arq: str | Path, dur: float = 4.0, alvo=(1080, 1920)) -> dict:
    """Decide como a foto entra no palco V2. Retorna o `fundo` (cobrir com câmera de foco a foco) ou indica que ela
    precisa de moldura/varredura (foto.historica) — nunca uma faixa fina no meio da tela."""
    with Image.open(arq) as im:
        w, h = im.size
    rc = recorte_conteudo(arq)
    cw, ch = (rc[2] - rc[0]) * w, (rc[3] - rc[1]) * h
    asp = cw / ch
    fx, fy = foco(arq, rc)
    cobre = max(alvo[0] / cw, alvo[1] / ch)                # ampliação para cobrir a tela
    visivel = (alvo[0] / alvo[1]) / asp                    # fração da largura que aparece em tela cheia
    if rc != [0.0, 0.0, 1.0, 1.0] or asp > 1.9 or visivel < .3:
        return {'modo': 'historica', 'recorte': rc, 'foco': [fx, fy], 'aspecto': round(asp, 2),
                'motivo': 'recorte de scanner' if rc != [0.0, 0.0, 1.0, 1.0] else 'panorâmica: tela cheia mostraria só %d%% da foto' % round(visivel * 100)}
    z1 = 1.0 + min(.12, max(0.0, (1.5 / cobre) - 1) + .04)   # aproxima pouco, e menos ainda se a foto já está ampliada
    return {'modo': 'cobrir', 'wh': [w, h], 'de': [.5 + (fx - .5) * .4, .5 + (fy - .5) * .4, 1.0], 'para': [fx, fy, round(z1, 3)],
            'ampliacao': round(cobre, 2), 'alerta_resolucao': cobre > 2.2}


# ---------------- licença ----------------
_OK = ('cc0', 'public domain', 'domínio público', 'dominio publico', 'pd-', 'pd ', 'cc by ', 'cc by-sa', 'cc-by', 'cc by 2', 'cc by 3', 'cc by 4',
       'no restrictions', 'sem restrições', 'nasa', 'usgov', 'us gov')
_NAO = ('-nc', ' nc ', 'noncommercial', 'non-commercial', '-nd', ' nd ', 'noderivs', 'all rights reserved', 'todos os direitos')


def licenca(item: dict) -> dict:
    """Compatível com canal monetizado? NC (não comercial) e ND (sem derivação: o vídeo recorta e anima) ficam de fora."""
    t = ' ' + _norm(f"{item.get('licenca', '')} {item.get('credito', '')}") + ' '
    if any(x in t for x in _NAO):
        return {'ok': False, 'motivo': 'licença não comercial ou sem derivação'}
    if any(x in t for x in _OK):
        return {'ok': True, 'atribuicao': str(item.get('credito') or '').strip()}
    return {'ok': False, 'motivo': 'licença não identificada no crédito'}


def historica(item: dict, arq: str | Path | None = None) -> bool:
    a = _ano_de(item)
    if a and a < 1960:
        return True
    if arq:
        with Image.open(arq) as im:
            x = np.asarray(im.convert('RGB').resize((64, 64)), dtype=float)
        return float(np.abs(x[..., 0] - x[..., 1]).mean() + np.abs(x[..., 1] - x[..., 2]).mean()) < 6   # quase PB
    return False


ESC_MAX = 1.5          # ampliação máxima tolerada sobre os pixels reais (acima disso a foto "derrete")
PROTAGONISTA_MIN = 300 # altura mínima (px no vídeo 1080×1920) para uma foto de arquivo ser a protagonista da cena


def adequacao_historica(wh: tuple | list, recorte: list | None = None) -> dict:
    """V2.2: o enquadramento de uma foto de arquivo depende da resolução e da proporção REAIS da área útil.
    Espelha a regra de foto.historica (comp/fotos.js). modo: 'inteira' (cabe grande), 'varredura' (panorâmica com
    pixels para uma janela alta) ou 'insuficiente' (vira faixa fina ou exige ampliação destrutiva → não pode ser
    protagonista: buscar o original/outra foto autêntica, ou outra composição)."""
    rc = recorte or [0, 0, 1, 1]
    cw, ch = (rc[2] - rc[0]) * wh[0], (rc[3] - rc[1]) * wh[1]
    asp = cw / max(ch, 1)
    L = 1000 if asp >= .9 else max(420, min(1000, round(860 * asp)))
    A1 = min(L / asp, 860)
    esc_inteira = L / cw
    if asp > 2.0:
        A2 = min(560, ch * ESC_MAX)
        modo = 'varredura' if A2 >= PROTAGONISTA_MIN and esc_inteira <= ESC_MAX else 'insuficiente'
        altura = max(A1, A2)
    else:
        altura = A1
        modo = 'inteira' if A1 >= PROTAGONISTA_MIN and esc_inteira <= ESC_MAX else 'insuficiente'
    motivo = '' if modo != 'insuficiente' else (
        f'{round(cw)}×{round(ch)} px úteis: ' + ('vira faixa de ' + str(round(altura)) + ' px' if altura < PROTAGONISTA_MIN else
                                                 f'exigiria ampliar {esc_inteira:.1f}× (máx. {ESC_MAX}×)'))
    return {'modo': modo, 'util_px': [round(cw), round(ch)], 'proporcao': round(asp, 2), 'largura_tela': L, 'altura_tela': round(altura),
            'ampliacao_inteira': round(esc_inteira, 2), 'motivo': motivo}
