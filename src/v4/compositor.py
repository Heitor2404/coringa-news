"""Compositor final V4: clipes de QUALQUER backend → uma linha do tempo (1080×1920, 30 fps), cortes limpos por padrão,
dissolve só quando o contrato justificou; camada única de identidade/legendas (Remotion `Camada`, com alfa) por cima de
tudo; áudio masterizado. Gera a linha do tempo de auditoria (cena → backend → componente → arquivo → medidas).
"""
from __future__ import annotations

import json
from pathlib import Path

from src.v4.util import FPS, rodar, sondar

DISSOLVE = 0.35


def concatenar(clipes: list[dict], trab: Path, saida: Path) -> Path:
    """clipes = [{arq, dur, transicao}] já normalizados. Dissolve sem encurtar a linha do tempo: o clipe anterior ganha
    DISSOLVE s do próprio último quadro (tpad) e o xfade consome exatamente esse acréscimo."""
    if all((c.get('transicao') or {}).get('tipo', 'corte') == 'corte' for c in clipes[1:]):
        lista = trab / 'concat.txt'
        lista.write_text(''.join(f"file '{Path(c['arq']).resolve()}'\n" for c in clipes))
        rodar(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', saida], log=trab / 'concat.log')
        return saida
    ent, fil = [], []
    for c in clipes:
        ent += ['-i', str(c['arq'])]
    for i, c in enumerate(clipes):
        prox = clipes[i + 1] if i + 1 < len(clipes) else None
        dis = prox and (prox.get('transicao') or {}).get('tipo') == 'dissolve'
        lab = f'[p{i}]'
        fil.append(f'[{i}:v]' + (f'tpad=stop_mode=clone:stop_duration={DISSOLVE}' if dis else 'null') + f',settb=1/{FPS}{lab}')
    cur = '[p0]'
    acum = clipes[0]['dur']
    for i in range(1, len(clipes)):
        tipo = (clipes[i].get('transicao') or {}).get('tipo', 'corte')
        out = f'[x{i}]'
        if tipo == 'dissolve':
            fil.append(f'{cur}[p{i}]xfade=transition=fade:duration={DISSOLVE}:offset={acum:.3f},settb=1/{FPS}{out}')
        else:
            fil.append(f'{cur}[p{i}]concat=n=2:v=1:a=0,settb=1/{FPS}{out}')
        acum += clipes[i]['dur']
        cur = out
    rodar(['ffmpeg', '-v', 'error', '-y', *ent, '-filter_complex', ';'.join(fil), '-map', cur, '-c:v', 'libx264', '-preset', 'medium',
           '-crf', '17', '-pix_fmt', 'yuv420p', '-r', str(FPS), saida], timeout=3600, log=trab / 'concat.log')
    return saida


def final(video: Path, camada: Path | None, audio: Path, saida: Path, trab: Path) -> dict:
    ent = ['-i', str(video)] + (['-c:v', 'libvpx', '-i', str(camada)] if camada else []) + ['-i', str(audio)]
    if camada:
        fc = '[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]'
        mapas = ['-map', '[v]', '-map', '2:a']
    else:
        fc = '[0:v]format=yuv420p[v]'
        mapas = ['-map', '[v]', '-map', '1:a']
    rodar(['ffmpeg', '-v', 'error', '-y', *ent, '-filter_complex', fc, *mapas, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
           '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', saida],
          timeout=3600, log=trab / 'final.log')
    corrigir_pico_aac(saida, audio, trab)
    return sondar(saida)


PICO_MAX = -1.0


def corrigir_pico_aac(mp4: Path, audio: Path, trab: Path, medir=None) -> dict:
    """o AAC sobe o pico verdadeiro (master −1,4 dBTP virou −0,1 no MP4, execução 43972774128): mede NO MP4 e, se passar de
    −1 dBTP, recodifica só o áudio com o ganho que falta (mais 0,3 dB de folga). O vídeo é copiado, não recodificado."""
    if medir is None:
        from src.fiscal import medir_audio as medir
    m = medir(mp4)
    pico = m.get('pico')
    if pico is None or pico <= PICO_MAX:
        return {'corrigido': False, 'pico': pico}
    excesso = pico - (medir(audio).get('pico') or PICO_MAX)         # quanto o AAC acrescenta ao pico do master
    teto_db = PICO_MAX - max(excesso, 0.0) - 0.3                     # limitador só nos picos: a loudness fica
    tmp = trab / 'final_pico.mp4'
    rodar(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-i', str(audio), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
           '-af', f'aresample=192000,alimiter=limit={10 ** (teto_db / 20):.4f}:attack=1:release=50:level=false,aresample=48000',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', tmp],
          timeout=1200, log=trab / 'final_pico.log')
    tmp.replace(mp4)
    depois = medir(mp4)
    return {'corrigido': True, 'pico_antes': pico, 'teto_limitador_db': round(teto_db, 2), 'pico_depois': depois.get('pico'), 'lufs_depois': depois.get('lufs')}


def linha_do_tempo(ep: dict, registros: list[dict], saida: Path) -> list[dict]:
    lt = []
    for c, r in zip(ep['cenas'], registros):
        lt.append({'cena': c['id'], 'ini': c['ini'], 'fim': c['fim'], 'modalidade': c['modalidade'], 'componente': c['componente'],
                   'backend': r.get('backend'), 'versao': r.get('versao'), 'estado': r.get('estado'), 'segundos_render': r.get('segundos'),
                   'camera': c.get('camera'), 'transicao': c.get('transicao'), 'asset': (c.get('params') or {}).get('asset'),
                   'fala': c.get('fala'), 'o_que_precisa_aparecer': c.get('o_que_precisa_aparecer'), 'detalhes': {k: v for k, v in r.items() if k not in ('cmd',)}})
    saida.write_text(json.dumps(lt, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return lt
