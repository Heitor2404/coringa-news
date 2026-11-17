"""TRECHO ANIMADO curto (5–8 s) de um plano JÁ preflightado — sem episódio completo.

Renderiza só os quadros [a, b] do Formato + Camada (legenda/marca), encaixa o clipe aprovado se o trecho o cruza, e
põe o som do PADRÃO do canal (narração + trilha + efeitos dos acontecimentos, master do episódio recortado). Opcional:
lado a lado com um trecho da referência PRIVADA (fica fora do repositório).
uso: python scripts/formatos_trecho.py <saida_preflight> <nome> <a> <b> [ref.mp4 ra rb]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.v4 import som  # noqa: E402
from src.v4.backends import js  # noqa: E402
from src.v4.formatos import plano as P, produzir as Z  # noqa: E402
from src.v4.util import rodar  # noqa: E402

FPS = 30


def trecho(S: Path, nome: str, a: float, b: float, ref: tuple | None = None) -> dict:
    pl, meta, imgs = Z._ler(S / 'plano_resolvido.json'), Z._ler(S / 'narracao.json'), Z._ler(S / 'ativos.json')
    can = P.canal(pl.get('canal', 'coringa'))
    tokens = {k: can[k] for k in ('cores', 'fontes', 'tempo', 'palco', 'cartao', 'pino', 'cta') if k in can}
    geo = Z._ler(RAIZ / pl['geo']) if pl.get('geo') else None
    trab = (S / 'trechos' / nome).resolve()
    trab.mkdir(parents=True, exist_ok=True)
    qa, qb = int(round(a * FPS)), int(round(b * FPS)) - 1
    base = trab / 'formato.mp4'
    js.remotion('Formato', P.props(pl, tokens, geo, imgs), base, trab / 'f', quadros=(qa, qb))
    partes, t = [], a
    for k, c in enumerate(sorted(pl.get('clipes') or [], key=lambda c: c['t0'])):
        if c['t1'] <= a or c['t0'] >= b:
            continue
        if c['t0'] > t:
            partes.append(trab / f'p{len(partes)}.mp4'); Z._trecho(base, t - a, c['t0'] - a, partes[-1])
        inteiro = trab / f'clipe{k}.mp4'
        Z._clipe(c, can, trab / f'clipe{k}', inteiro)
        partes.append(trab / f'c{len(partes)}.mp4')
        Z._trecho(inteiro, max(0, t - c['t0']), min(b, c['t1']) - c['t0'], partes[-1])
        t = min(b, c['t1'])
    if t < b:
        partes.append(trab / f'p{len(partes)}.mp4'); Z._trecho(base, t - a, b - a, partes[-1])
    from src.v4 import compositor
    video = compositor.concatenar([{'arq': p} for p in partes], trab, trab / 'video.mp4') if len(partes) > 1 else partes[0]
    cam = P.props_camada(pl, meta)
    camada = trab / 'camada.webm'
    js.remotion('Camada', cam, camada, trab / 'c', alfa=True, quadros=(qa, qb))
    # som do PADRÃO: mistura do episódio inteiro (barata) e recorte do trecho — igual ao que o episódio teria
    master = trab / 'master.wav'
    musicas = sorted((RAIZ / 'assets' / 'musica' / 'explica').glob('*.mp3'))
    musica = musicas[sum(map(ord, pl['video_id'])) % len(musicas)] if musicas else None
    voz = S / 'voz.wav'
    if 'SINTÉTICA' in str(meta.get('origem', '')):          # teste de reuso sem TTS: só trilha + efeitos (sem tom sintético)
        voz = som.silencio(pl['duracao'], trab / 'voz_muda.wav')
    reg = som.mixar(voz, pl['duracao'], Z.sfx_do_plano(pl), musica, trab / 'som', master, preset=can.get('som'))
    out = S / 'trechos' / f'{nome}.mp4'
    rodar(['ffmpeg', '-v', 'error', '-y', '-i', video, '-c:v', 'libvpx', '-i', camada, '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', master,
           '-filter_complex', '[0:v][1:v]overlay=0:0:format=auto[v]', '-map', '[v]', '-map', '2:a', '-c:v', 'libx264', '-preset', 'veryfast',
           '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out])
    res = {'trecho': str(out), 'a': a, 'b': b, 'efeitos_no_trecho': [e for e in reg['efeitos'] if a <= e['t'] <= b]}
    if ref:
        rf, ra, rb = ref
        lado = S / 'trechos' / f'{nome}_lado_a_lado.mp4'
        dur = min(b - a, rb - ra)
        rodar(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ra:.3f}', '-t', f'{dur:.3f}', '-i', rf, '-t', f'{dur:.3f}', '-i', out, '-filter_complex',
               '[0:v]scale=540:960,setsar=1,drawtext=text=REFERENCIA:x=12:y=12:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.6[l];'
               '[1:v]scale=540:960,setsar=1,drawtext=text=CORINGA:x=12:y=12:fontsize=26:fontcolor=0xFFD21F:box=1:boxcolor=black@0.6[r];'
               '[l][r]hstack=inputs=2[v]', '-map', '[v]', '-map', '1:a?', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
               '-pix_fmt', 'yuv420p', '-c:a', 'aac', lado])
        res['lado_a_lado'] = str(lado)
    (S / 'trechos' / f'{nome}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False))
    return res


if __name__ == '__main__':
    a = sys.argv
    trecho(Path(a[1]), a[2], float(a[3]), float(a[4]), (a[5], float(a[6]), float(a[7])) if len(a) > 7 else None)
