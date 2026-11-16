"""Fiscal AUDIOVISUAL (V3) — segunda avaliação, sobre o MP4 renderizado e o storyboard, com evidência por tempo.

Mede o que dá para medir sem IA (não julga arte; a aprovação estética continua humana):
  movimento    energia de mudança entre quadros (10 qps) na área útil (fora da faixa de legenda) → trechos parados
  vazio        fração da área útil (y 330–1150) quase sem detalhe → fundo vazio / elemento pequeno
  texto        fração da área útil coberta por texto grande (pelo palco: caixas de texto das composições)
  repeticao    a mesma foto em planos seguidos; a mesma transição muitas vezes seguidas
  pergunta     todo acontecimento marcado como crítico no storyboard tem plano renderizado (não foi retirado)
  direcao      critérios do contrato que o diretor registrou como não cumpridos (limitações)

Uso: python -m src.v2.fiscal_av <video.mp4> [cenas.json] [direcao.json]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PARADO_LIMIAR = 1.6          # média de |Δ| por pixel (0–255) abaixo disso = imagem praticamente parada
PARADO_MIN_S = 2.5           # trecho parado contínuo que vira achado
VAZIO_LIMIAR = .55           # mais da metade da área útil sem detalhe


def _quadros(mp4: Path, fps: int = 10, w: int = 108, h: int = 192):
    import numpy as np
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-vf', f'fps={fps},scale={w}:{h},format=gray', '-f', 'rawvideo', '-'],
                       capture_output=True, check=True)
    a = np.frombuffer(r.stdout, dtype='uint8')
    return a.reshape(-1, h, w).astype('float32'), fps


def medir(mp4: Path) -> dict:
    import numpy as np
    q, fps = _quadros(mp4)
    h = q.shape[1]
    # área útil: y 330–1180 (acima da legenda) em 1920 → linhas proporcionais
    y0, y1 = int(h * 330 / 1920), int(h * 1180 / 1920)
    util = q[:, y0:y1, :]
    dif = np.abs(np.diff(util, axis=0)).mean(axis=(1, 2))                    # por intervalo de quadro
    por_s = [float(dif[i * fps:(i + 1) * fps].mean()) for i in range(int(len(dif) / fps))]
    # detalhe: desvio local (blocos 6×6) — bloco quase liso = vazio
    from numpy.lib.stride_tricks import sliding_window_view as sw
    vaz = []
    for k in range(0, len(util), fps):
        f = util[k]
        b = sw(f, (6, 6))[::6, ::6].reshape(-1, 36)
        vaz.append(float((b.std(axis=1) < 4).mean()))
    return {'duracao': round(len(q) / fps, 2), 'movimento_por_s': [round(x, 2) for x in por_s], 'vazio_por_s': [round(x, 3) for x in vaz]}


def avaliar(mp4: Path, cenas: list[dict] | None = None, direcao: list[dict] | None = None, criticos: list[str] | None = None) -> dict:
    m = medir(mp4)
    ach = []
    # trechos parados
    ini = None
    for i, v in enumerate(m['movimento_por_s'] + [99]):
        if v < PARADO_LIMIAR and ini is None:
            ini = i
        elif v >= PARADO_LIMIAR and ini is not None:
            if i - ini >= PARADO_MIN_S:
                ach.append({'codigo': 'AV-PARADO', 'inicio': ini, 'fim': i, 'evidencia': f'mudança média {min(m["movimento_por_s"][ini:i]):.2f}–{max(m["movimento_por_s"][ini:i]):.2f} (limiar {PARADO_LIMIAR})'})
            ini = None
    # vazio
    for i, v in enumerate(m['vazio_por_s']):
        if v > VAZIO_LIMIAR:
            ach.append({'codigo': 'AV-VAZIO', 'inicio': i, 'fim': i + 1, 'evidencia': f'{v:.0%} da área útil sem detalhe'})
    # repetição e transições
    if cenas:
        for a, b in zip(cenas, cenas[1:]):
            ia = (a.get('params') or {}).get('img') or (a.get('fundo') or {}).get('img')
            ib = (b.get('params') or {}).get('img') or (b.get('fundo') or {}).get('img')
            if ia and ia == ib:
                ach.append({'codigo': 'AV-REPETE', 'inicio': a['start'], 'fim': b['end'], 'evidencia': f'mesma foto em planos seguidos ({Path(str(ia)).name})'})
        tr = [c.get('transicao') or 'corte' for c in cenas[1:]]
        for i in range(len(tr) - 3):
            if len(set(tr[i:i + 4])) == 1 and tr[i] != 'corte':
                ach.append({'codigo': 'AV-TRANSICAO', 'inicio': cenas[i + 1]['start'], 'fim': cenas[i + 4]['end'], 'evidencia': f'4 transições "{tr[i]}" seguidas'})
                break
        comps = [c.get('comp') for c in cenas]
        cartoes = sum(1 for c in comps if c in ('numero.animado', 'processo.etapas', 'banner.discreto', 'editorial.frase', 'abertura.pergunta'))
        m['planos'] = len(cenas)
        m['cartoes'] = cartoes
    if criticos is not None and cenas is not None:
        feitos = {(c.get('direcao') or {}).get('evento_id') for c in cenas}
        for e in criticos:
            if e not in feitos:
                ach.append({'codigo': 'AV-PERGUNTA', 'inicio': None, 'fim': None, 'evidencia': f'acontecimento crítico {e} sem plano: a pergunta central fica sem resposta'})
    for r in direcao or []:
        for l in r.get('limitacoes') or []:
            ach.append({'codigo': 'AV-DIRECAO', 'inicio': (r.get('tempo') or [None])[0], 'fim': (r.get('tempo') or [None, None])[1], 'evidencia': f"{r.get('evento_id')}: {l}"})
    mov = m['movimento_por_s']
    resumo = {'parado_s': sum(1 for v in mov if v < PARADO_LIMIAR), 'parado_pct': round(100 * sum(1 for v in mov if v < PARADO_LIMIAR) / max(1, len(mov))),
              'movimento_medio': round(sum(mov) / max(1, len(mov)), 2), 'vazio_medio_pct': round(100 * sum(m['vazio_por_s']) / max(1, len(m['vazio_por_s'])))}
    bloqueia = any(a['codigo'] == 'AV-PERGUNTA' for a in ach)
    return {'medidas': m, 'resumo': resumo, 'achados': ach, 'bloqueia': bloqueia,
            'nota': 'medidas objetivas; não julgam qualidade artística — a aprovação estética é humana'}


if __name__ == '__main__':
    mp4 = Path(sys.argv[1])
    cen = json.loads(Path(sys.argv[2]).read_text())['scenes'] if len(sys.argv) > 2 else None
    dr = json.loads(Path(sys.argv[3]).read_text()).get('registro') if len(sys.argv) > 3 else None
    print(json.dumps(avaliar(mp4, cen, dr), ensure_ascii=False, indent=1))
