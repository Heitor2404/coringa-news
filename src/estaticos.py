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
"""
import subprocess
from pathlib import Path

import numpy as np

FPS = 10
LARG, ALT = 72, 128
FAIXA_LEGENDA = (0.55, 0.74)     # fração da altura onde fica a legenda do Coringa
ESTATICO_S = 4.0                 # mais que isso sem mudança = trecho estático
CORTE_FRAC = 0.30                # fração da tela com mudança forte num só quadro = corte
ELEMENTO_FRAC = (0.02, 0.30)     # fração menor, de repente (antes calmo) = elemento entrando
MUDANCA_FORTE = 20.0             # diferença (0–255) de um bloco 8×8 que conta como mudança forte
MESMA_IMAGEM = 0.90              # correlação de cores acima disso = mesma imagem (reenquadrada)


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
    return {'duracao': round(dur, 1), 'mudancas': len(marcos) - 2, 'troca_media': round(dur / max(1, len(gaps)), 2),
            'estaticos': est, 'frac_estatica': round(sum(g[2] for g in est) / dur, 3) if dur else 0.0,
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


def medir_cenas(cenas: list[dict], estatico_s: float = ESTATICO_S) -> dict:
    """Dentro do motor: cada plano sabe a imagem que usa. Mudança = imagem diferente da anterior, ou plano de
    infográfico/mapa (elemento novo). Mesma imagem com outro enquadramento NÃO é mudança."""
    if not cenas:
        return _trechos([], 0.0, estatico_s) | {'imagens': 0}
    graf = ('numero', 'mapa', 'linha_tempo', 'comparacao', 'cards', 'lista', 'escala', 'citacao', 'revelacao')
    marcos, ant, ant_graf = [], None, False
    for c in cenas:
        chave = c.get('imagem') or c.get('img') or f"{c.get('tipo')}-{c.get('grupo')}"   # 'imagem' = id da mídia (vídeo ou foto)
        e_graf = c.get('tipo') in graf
        if ant is not None and (chave != ant or e_graf or ant_graf):     # gráfico entrando OU saindo também é mudança
            marcos.append(float(c['start']))
        ant, ant_graf = chave, e_graf
    dur = float(cenas[-1]['end'])
    return _trechos(marcos, dur, estatico_s) | {'imagens': len({c.get('img') for c in cenas if c.get('img')})}


def resumo(m: dict) -> str:
    base = f"🎞 ritmo: imagem nova a cada {m['troca_media']:.1f}s em média"
    if not m['estaticos']:
        return base + '; nenhum trecho parado'
    pior = sorted(m['estaticos'], key=lambda x: -x[2])[:3]
    return (base + f"; {round(100 * m['frac_estatica'])}% do vídeo com a mesma imagem por mais de {ESTATICO_S:.0f}s: "
            + ', '.join(f'{a:.0f}–{b:.0f}s' for a, b, _ in sorted(pior)))
