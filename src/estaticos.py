"""DETECTOR DE TRECHOS ESTÁTICOS (Fase 0 da auditoria do Coringa, 12/11/2026) — só mede, não muda o vídeo.

O que cansa quem assiste não é pixel parado: é a MESMA IMAGEM na tela por muito tempo, mesmo reenquadrada (no Ötzi a
mesma montanha era cortada para outro enquadramento a cada 2 s e continuava a mesma montanha). Então:
  - "mudança" = troca para OUTRA imagem, ou um elemento novo entrando (número, etiqueta, linha de ficha);
  - reenquadrar a mesma foto, zoom lento ou câmera andando num clipe NÃO contam como mudança.
Duas formas de medir:
  - `medir(video)`: no arquivo pronto (serve para o Ötzi e para as referências). Corta em planos pelos pixels e junta
    planos seguidos com as mesmas cores (a mesma foto reenquadrada tem as mesmas cores).
  - `medir_cenas(cenas)`: dentro do motor, com o dado exato de qual imagem cada plano usa.
A faixa da legenda fica de fora (ela troca a cada palavra e esconderia uma imagem parada).

Duas réguas, sempre separadas (12/11):
  - "parado" (frac_estatica): a duração INTEIRA de cada trecho com mais de 4 s sem mudança. É a que entra na nota de ritmo.
  - "excedente": só o tempo que passou de 4 s em cada trecho (um plano de 4,3 s conta 0,3 s).

12/11 (Torre Eiffel): a imagem é identificada pelo que está NA TELA (arquivo da foto + assinatura visual), não pelo id da
ideia. Antes, um plano que reaproveitava a foto da vizinha (cena sem imagem própria, plano longo quebrado, revelação)
ficava com o id da SUA ideia: a foto repetida contava como imagem nova (e nunca como "voltando"), e o plano longo
quebrado com OUTRA foto contava como a mesma imagem.
"""
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

import numpy as np

FPS = 10
LARG, ALT = 72, 128
FAIXA_LEGENDA = (0.55, 0.74)     # fração da altura onde fica a legenda do Coringa
ESTATICO_S = 4.0                 # mais que isso sem mudança = trecho estático
CORTE_FRAC = 0.30                # fração da tela com mudança forte num só quadro = corte
ELEMENTO_FRAC = (0.02, 0.30)     # fração menor, de repente (antes calmo) = elemento entrando
MUDANCA_FORTE = 20.0             # diferença (0–255) de um bloco 8×8 que conta como mudança forte
MESMA_IMAGEM = 0.90              # correlação de cores acima disso = mesma imagem (reenquadrada)
MESMA_ASSINATURA = 6             # assinatura visual 8×8: até 6 de 64 bits diferentes = a mesma foto (outro arquivo)


def _ler(video: Path, faixa) -> np.ndarray:
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-vf', f'fps={FPS},scale={LARG}:{ALT}',
                        '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'], capture_output=True, check=True)
    q = np.frombuffer(r.stdout, np.uint8).reshape(-1, ALT, LARG, 3).astype(np.float32)
    if faixa:
        a, b = int(ALT * faixa[0]), int(ALT * faixa[1])
        q = np.concatenate([q[:, :a], q[:, b:]], axis=1)
    return q


def _hist(qs: np.ndarray) -> np.ndarray:
    h = np.concatenate([np.histogram(qs[..., c], bins=16, range=(0, 256))[0] for c in range(3)]).astype(np.float64)
    return h / (h.sum() or 1)


def _sim(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) or 1))


def _trechos(marcos: list[float], dur: float, estatico_s: float) -> dict:
    marcos = sorted(set([0.0] + [m for m in marcos if 0 < m < dur] + [dur]))
    gaps = [(a, b, round(b - a, 1)) for a, b in zip(marcos, marcos[1:])]
    est = [g for g in gaps if g[2] > estatico_s]
    parado = round(sum(b - a for a, b, _ in est), 2)
    exced = round(sum(b - a - estatico_s for a, b, _ in est), 2)
    return {'duracao': round(dur, 1), 'mudancas': len(marcos) - 2, 'troca_media': round(dur / max(1, len(gaps)), 2),
            'estaticos': est, 'parado_s': parado, 'frac_estatica': round(parado / dur, 3) if dur else 0.0,
            'excedente_s': exced, 'frac_excedente': round(exced / dur, 3) if dur else 0.0,
            'maior': max([g[2] for g in est] or [0.0])}


def medir(video: Path, faixa=FAIXA_LEGENDA, estatico_s: float = ESTATICO_S) -> dict:
    """No arquivo pronto. Devolve {'duracao','mudancas','troca_media','estaticos':[(ini,fim,dur)],'frac_estatica','maior',
    'cortes','elementos','imagens'}."""
    q = _ler(video, faixa)
    dur = len(q) / FPS
    if len(q) < 3:
        return _trechos([], dur, estatico_s) | {'cortes': 0, 'elementos': 0, 'imagens': 1}
    g = q.mean(axis=3)
    H, W = g.shape[1] // 8 * 8, g.shape[2] // 8 * 8
    blocos = g[:, :H, :W].reshape(len(g), H // 8, 8, W // 8, 8).mean(axis=(2, 4))
    forte = (np.abs(np.diff(blocos, axis=0)) > MUDANCA_FORTE).mean(axis=(1, 2))    # forte[i]: entre o quadro i e i+1
    cortes, elementos = [], []
    for i, f in enumerate(forte):
        t = round((i + 1) / FPS, 1)
        antes = forte[max(0, i - 3):i]
        if f >= CORTE_FRAC and not (cortes and t - cortes[-1] < 0.4):
            cortes.append(t)
        elif ELEMENTO_FRAC[0] <= f < ELEMENTO_FRAC[1] and (len(antes) == 0 or antes.max() < ELEMENTO_FRAC[0]) \
                and not (elementos and t - elementos[-1] < 0.5):
            elementos.append(t)
    # junta planos com as mesmas cores (mesma imagem reenquadrada): só conta o corte que troca de imagem
    limites = [0.0] + cortes + [dur]
    planos = [(a, b) for a, b in zip(limites, limites[1:]) if b - a >= 0.15]
    hs = [_hist(q[int(a * FPS):max(int(a * FPS) + 1, int(b * FPS))]) for a, b in planos]
    trocas = [planos[k][0] for k in range(1, len(planos)) if _sim(hs[k], hs[k - 1]) < MESMA_IMAGEM]
    marcos = trocas + [e for e in elementos if all(abs(e - c) > 0.4 for c in cortes)]
    return _trechos(marcos, dur, estatico_s) | {'cortes': len(cortes), 'elementos': len(elementos), 'imagens': len(trocas) + 1}


_ASSIN: dict = {}


def _arquivo(img) -> Path | None:
    s = str(img or '')
    if not s:
        return None
    p = Path(unquote(urlparse(s).path)) if s.startswith('file:') else Path(s)
    return p if p.is_file() else None


def _assinatura(img) -> int | None:
    """Assinatura visual (média 8×8 em cinza): a mesma foto salva em dois arquivos tem a mesma assinatura."""
    p = _arquivo(img)
    if p is None:
        return None
    if p not in _ASSIN:
        try:
            from PIL import Image
            with Image.open(p) as im:
                q = list(im.convert('L').resize((8, 8)).tobytes())
            m = sum(q) / 64
            _ASSIN[p] = sum(1 << k for k, x in enumerate(q) if x > m)
        except Exception:
            _ASSIN[p] = None
    return _ASSIN[p]


def chaves_visuais(cenas: list[dict]) -> list[str]:
    """Uma chave por plano = a imagem que está NA TELA. Vídeo: o clipe (o 2º plano da mesma ideia continua o mesmo
    clipe). Foto: o arquivo; dois arquivos com a mesma assinatura visual viram a mesma chave."""
    vistas: list[tuple[int, str]] = []
    out = []
    for c in cenas:
        if c.get('video'):
            out.append('clipe:' + str(c.get('imagem') or c.get('img')))
            continue
        img = c.get('img')
        if not img:
            out.append(f"{c.get('tipo')}-{c.get('grupo')}-{c.get('imagem')}")
            continue
        chave = 'img:' + str(unquote(urlparse(str(img)).path) if str(img).startswith('file:') else img)
        h = _assinatura(img)
        if h is not None:
            igual = next((k for hh, k in vistas if bin(hh ^ h).count('1') <= MESMA_ASSINATURA), None)
            if igual:
                chave = igual
            else:
                vistas.append((h, chave))
        out.append(chave)
    return out


def medir_cenas(cenas: list[dict], estatico_s: float = ESTATICO_S) -> dict:
    """Dentro do motor: cada plano sabe a imagem que usa. Mudança = imagem diferente da anterior NA TELA, ou plano de
    infográfico/mapa (elemento novo). Mesma imagem com outro enquadramento NÃO é mudança."""
    if not cenas:
        return _trechos([], 0.0, estatico_s) | {'imagens': 0}
    graf = ('numero', 'mapa', 'linha_tempo', 'comparacao', 'cards', 'lista', 'escala', 'citacao', 'revelacao')
    chaves = chaves_visuais(cenas)
    marcos, ant, ant_graf = [], None, False
    for c, chave in zip(cenas, chaves):
        e_graf = c.get('tipo') in graf
        if ant is not None and (chave != ant or e_graf or ant_graf):     # gráfico entrando OU saindo também é mudança
            marcos.append(float(c['start']))
        ant, ant_graf = chave, e_graf
    dur = float(cenas[-1]['end'])
    return _trechos(marcos, dur, estatico_s) | {'imagens': len({k for c, k in zip(cenas, chaves) if c.get('img')})}


# ───────── 12/11 (Torre Eiffel 4): imagem IMÓVEL × movimento de câmera que de fato muda o que se vê ─────────
# A régua acima conta a mesma foto como "parada" mesmo com a câmera passeando por ela. Esta conta como mudança o
# movimento que MUDA A VISTA, sem premiar movimento à toa. Só conta quando, tudo junto:
#   - a parte da foto que está na tela mudou de verdade: sobreposição (IoU) com a vista do último marco < MUDA_VISTA
#     (zoom lento de 8% ou panorâmica de 30 px sozinhos NÃO chegam lá);
#   - o movimento tem propósito: câmera escolhida para a cena (roteiro / _dar_movimento: aproxima no retrato, afasta no
#     fato, panorâmica no lugar) ou reenquadramento do MESMO acontecimento; a câmera automática de rodízio e o tremor não
#     contam;
#   - passou pelo menos MOV_INTERVALO desde a última mudança (corte nervoso não ganha nada);
#   - a mesma foto está na tela há no máximo MOV_MAX_MESMA: dali em diante é parado, com ou sem câmera.
# Clipe de vídeo é movimento real dentro da imagem: conta a cada MOV_INTERVALO, também até MOV_MAX_MESMA.
# Os números da câmera são os do template (src/render/template.html); um teste confere que continuam iguais.
TELA = (1080, 1920)
CAMS = ['aproxima', 'esquerda', 'afasta', 'direita', 'sobe', 'aproxima', 'desce']
CAM = {'aproxima': [1.0, 1.08, 0, 0, 0, 0], 'afasta': [1.08, 1.0, 0, 0, 0, 0], 'esquerda': [1.04, 1.04, 30, -30, 0, 0],
       'direita': [1.04, 1.04, -30, 30, 0, 0], 'sobe': [1.04, 1.04, 0, 0, 30, -30], 'desce': [1.04, 1.04, 0, 0, -30, 30],
       'tremor': [1.03, 1.07, 0, 0, 0, 0]}
SUB = [[1.1, 1.15, -30, -20, -30, -20], [1.1, 1.15, 30, 20, 30, 20], [1.14, 1.2, 0, 0, -35, -25]]
FOCOS = [[50, 40], [30, 30], [70, 62], [35, 68], [66, 28]]
MUDA_VISTA = 0.75            # IoU abaixo disso = pelo menos ~25% do que se vê é outro pedaço da foto
MOV_INTERVALO = 2.0
MOV_MAX_MESMA = 8.0
GRAF = ('numero', 'mapa', 'linha_tempo', 'comparacao', 'cards', 'lista', 'escala', 'citacao', 'revelacao')


def _eio(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def _vista(c: dict, t: float, i: int) -> tuple[float, float, float, float]:
    """Retângulo da foto que aparece na tela no instante t (0–1 em x e y), como o template desenha."""
    a, b = float(c['start']), float(c['end'])
    k = min(1.0, max(0.0, (t - a + .2) / (b - a + .4)))
    if c.get('moldura'):                                # moverFoto: zoom em torno de um foco dentro da foto
        e = k * .6 + _eio(k) * .4
        fx, fy = (v / 100 for v in FOCOS[(c.get('sub') or 0) % len(FOCOS)])
        z = (1.28 + .12 * e) if c.get('sub') else (1.0 + .12 * e)
        return fx - fx / z, fy - fy / z, fx + (1 - fx) / z, fy + (1 - fy) / z
    e = k * .7 + _eio(k) * .3                           # CAMERA: scale(z) translate(x, y) sobre a tela cheia
    if c.get('zoom_detalhe') and not c.get('video'):     # DETALHE do template (plano-mestre G)
        z0 = float(c['zoom_detalhe'])
        f = FOCOS[(c.get('sub') or 1) % len(FOCOS)]
        lim = lambda v: max(-(540 - 540 / z0), min(540 - 540 / z0, v))
        x, y = lim(-(f[0] / 100 - .5) * 1080), lim(-(f[1] / 100 - .5) * 1080)
        cam = [z0, z0 * 1.03, x, x, y, y]
    else:
        cam = SUB[(c['sub'] - 1) % len(SUB)] if c.get('sub') and not c.get('video') else \
            (CAM.get(c.get('camera')) or CAM[CAMS[i % len(CAMS)]])
    z = cam[0] + (cam[1] - cam[0]) * e
    cx = .5 - (cam[2] + (cam[3] - cam[2]) * e) / TELA[0]
    cy = .5 - (cam[4] + (cam[5] - cam[4]) * e) / TELA[1]
    m = .5 / z
    return cx - m, cy - m, cx + m, cy + m


def _iou(p, q) -> float:
    ix = max(0.0, min(p[2], q[2]) - max(p[0], q[0]))
    iy = max(0.0, min(p[3], q[3]) - max(p[1], q[1]))
    inter = ix * iy
    ap, aq = (p[2] - p[0]) * (p[3] - p[1]), (q[2] - q[0]) * (q[3] - q[1])
    return inter / (ap + aq - inter) if inter else 0.0


def _com_proposito(c: dict) -> bool:
    if c.get('camera') == 'tremor':
        return False
    if c.get('zoom_detalhe'):
        return True                                     # detalhe que a montagem só cria quando a resolução deixa
    if c.get('sub'):
        return bool(c.get('evento'))                    # reenquadramento do mesmo acontecimento
    return c.get('camera') in CAM                       # câmera escolhida (sem ela, o rodízio automático não conta)


def medir_movimento(cenas: list[dict], estatico_s: float = ESTATICO_S) -> dict:
    """Como medir_cenas, mais as mudanças de VISTA com propósito dentro da mesma foto (regras acima).
    Devolve o mesmo formato + 'movimento' (quantas mudanças vieram da câmera/clipe) e 'mesma_imagem' (a régua antiga)."""
    antigo = medir_cenas(cenas, estatico_s)
    if not cenas:
        return antigo | {'movimento': 0, 'mesma_imagem': antigo}
    chaves = chaves_visuais(cenas)
    marcos, mov = [], []
    ant, ant_graf, ini, ult, ref = None, False, 0.0, 0.0, None
    for i, (c, chave) in enumerate(zip(cenas, chaves)):
        a, b = float(c['start']), float(c['end'])
        e_graf = c.get('tipo') in GRAF
        if ant is None or chave != ant or e_graf or ant_graf:
            if ant is not None:
                marcos.append(a)
            ini, ult, ref = a, a, None
        ant, ant_graf = chave, e_graf
        if e_graf or not c.get('img'):
            continue
        if c.get('video'):
            t = ult + MOV_INTERVALO
            while t < b and t - ini <= MOV_MAX_MESMA:
                if t >= a:
                    mov.append(round(t, 2)); ult = t
                t += MOV_INTERVALO
            continue
        if ref is None:
            ref = _vista(c, a, i)
        if not _com_proposito(c):
            continue
        t = a
        while t < b:
            w = _vista(c, t, i)
            if t - ult >= MOV_INTERVALO and t - ini <= MOV_MAX_MESMA and _iou(ref, w) < MUDA_VISTA:
                mov.append(round(t, 2)); ult, ref = t, w
            t += 1 / FPS
    dur = float(cenas[-1]['end'])
    # três tipos de mudança, separados (plano-mestre G): semântica (outra imagem/gráfico), geométrica (a vista da MESMA
    # foto mudou de verdade, com propósito) e nenhuma (imagem idêntica: os trechos parados)
    return _trechos(marcos + mov, dur, estatico_s) | {'imagens': antigo['imagens'], 'movimento': len(mov),
                                                        'semanticas': len(marcos), 'mesma_imagem': antigo}


def _s(x: float) -> str:
    return f'{x:.1f}'.replace('.', ',')


def resumo(m: dict) -> str:
    """Texto para o Telegram: total de trechos parados, os 3 maiores e a duração acumulada (inteira e só o excedente)."""
    if 'mesma_imagem' in m:                          # régua nova (câmera que muda a vista conta) + a antiga ao lado
        mi = m['mesma_imagem']
        antiga = (f"   sem contar a câmera: imagem nova a cada {_s(mi['troca_media'])}s; {len(mi['estaticos'])} trecho(s) "
                  f"com a mesma foto por mais de {ESTATICO_S:.0f}s ({round(100 * mi['frac_estatica'])}% do vídeo)")
        novo = resumo({k: v for k, v in m.items() if k != 'mesma_imagem'})
        novo = novo.replace('🎞 ritmo: imagem nova', '🎞 ritmo (câmera com propósito conta): mudança de vista', 1) \
                   .replace('com a mesma imagem', 'parado de verdade', 1)
        return novo + f" · {m.get('movimento', 0)} mudança(s) vieram da câmera/clipe\n" + antiga
    base = f"🎞 ritmo: imagem nova a cada {_s(m['troca_media'])}s em média"
    est = m['estaticos']
    if not est:
        return base + '; nenhum trecho parado'
    parado = m.get('parado_s', sum(g[2] for g in est))
    exced = m.get('excedente_s', sum(max(0.0, g[2] - ESTATICO_S) for g in est))
    dur = m.get('duracao') or 1
    pior = sorted(est, key=lambda x: -x[2])[:3]
    rot = 'os 3 maiores' if len(est) > 3 else 'todos'
    return (base + f"; {len(est)} trecho(s) com a mesma imagem por mais de {ESTATICO_S:.0f}s, somando {_s(parado)}s "
            f"({round(100 * parado / dur)}% do vídeo)\n"
            f"{rot}: " + ', '.join(f'{_s(a)}–{_s(b)}s ({_s(b - a)}s)' for a, b, _ in pior)
            + f"; só o que passou de {ESTATICO_S:.0f}s: {_s(exced)}s ({round(100 * exced / dur)}%)")
