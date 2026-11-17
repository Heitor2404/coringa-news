"""Som do motor V4, igual para todos os backends: narração + trilha (CC0, abaixada sob a voz) + efeitos com INTENÇÃO,
masterizados com a mesma rotina medida do canal (−14 LUFS integrado, pico verdadeiro ≤ −1 dBTP, 48 kHz).

Efeitos são ORIGINAIS (sintetizados com FFmpeg lavfi): nenhum arquivo de terceiros, nenhuma licença a rastrear.
Cada efeito precisa de um acontecimento na cena (o contrato registra a justificativa).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from src.v4.util import IDENT, rodar

# receitas lavfi (duração em s, filtro); volume relativo é ajustado na mistura
SFX = {
    'agua_fluxo': (3.0, "anoisesrc=color=brown:amplitude=0.6:d={d},lowpass=f=900,highpass=f=80,afade=t=in:d=0.6,afade=t=out:st={fo}:d=0.8"),
    'comporta': (1.6, "sine=f=55:d={d},volume=1.4,afade=t=out:st=0.2:d=1.3[a];anoisesrc=color=pink:amplitude=0.3:d={d},bandpass=f=420:w=200,afade=t=out:st=0.05:d=0.6[b];[a][b]amix=inputs=2:normalize=0"),
    'valvula': (0.9, "anoisesrc=color=white:amplitude=0.25:d={d},bandpass=f=2400:w=900,afade=t=in:d=0.05,afade=t=out:st=0.3:d=0.55"),
    'impacto': (1.8, "sine=f=42:d={d},volume=1.8,afade=t=in:d=0.01,afade=t=out:st=0.08:d=1.6"),
    'tique': (0.35, "sine=f=1650:d={d},volume=0.6,afade=t=in:d=0.004,afade=t=out:st=0.01:d=0.3,highpass=f=700"),
    'traco': (1.1, "anoisesrc=color=pink:amplitude=0.22:d={d},bandpass=f=1800:w=1400,afade=t=in:d=0.25,afade=t=out:st=0.5:d=0.6"),
    'sopro': (0.8, "anoisesrc=color=pink:amplitude=0.35:d={d},highpass=f=600,lowpass=f=5000,afade=t=in:d=0.35,afade=t=out:st=0.4:d=0.4"),
}


def gerar_sfx(nome: str, saida: Path, dur: float | None = None) -> Path:
    d0, f = SFX[nome]
    d = dur or d0
    filtro = f.format(d=f'{d:.2f}', fo=f'{max(0.1, d - 0.8):.2f}')
    rodar(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=mono:d={d:.2f}', '-filter_complex',
           f'{filtro}[s];[0][s]amix=inputs=2:normalize=0,alimiter=limit=0.5:level=false,aformat=sample_rates=48000:channel_layouts=mono', '-t', f'{d:.2f}', saida])
    return saida


def mixar(narracao: Path, duracao: float, sfx: list[dict], musica: Path | None, trab: Path, saida: Path, preset: dict | None = None) -> dict:
    """sfx = [{id, t, ganho_db, dur}] em tempo do episódio. Trilha com sidechain da voz. Depois: masterização medida."""
    from src.render.render import masterizar
    trab.mkdir(parents=True, exist_ok=True)
    preset = preset or {}
    ent = ['-i', str(narracao)]
    # padrão do canal: voz com compressão de fala (referência LRA ≈ 2 LU; picos de TTS de +1 dBTP roubavam o ganho do master)
    vc = ',acompressor=threshold=-26dB:ratio=3:attack=4:release=90:makeup=4,alimiter=limit=0.7:attack=1:release=40:level=false' if (preset or {}).get('lufs') is not None else ''
    fil = [f'[0:a]aresample=48000,aformat=channel_layouts=mono{vc},apad=whole_dur={duracao:.3f}[voz]']
    k = 1
    mus_db = preset.get('musica_db', IDENT['som']['musica_db_sob_voz'])
    dk = {'threshold': .03, 'ratio': 6, 'attack_ms': 20, 'release_ms': 300, **(preset.get('ducking') or {})}
    if musica and Path(musica).exists():
        ent += ['-stream_loop', '-1', '-i', str(musica)]
        fil.append(f'[{k}:a]aresample=48000,aformat=channel_layouts=mono,atrim=0:{duracao:.3f},volume={mus_db}dB,'
                   f'afade=t=in:d=1.0,afade=t=out:st={max(0, duracao - 2.0):.2f}:d=2.0[mus0]')
        fil.append('[voz]asplit=2[voz][sc]')
        fil.append(f"[mus0][sc]sidechaincompress=threshold={dk['threshold']}:ratio={dk['ratio']}:attack={dk['attack_ms']}:release={dk['release_ms']}[mus]")
        k += 1
    efeitos = []
    for j, s in enumerate(sfx):
        arq = gerar_sfx(s['id'], trab / f"sfx_{j}_{s['id']}.wav", s.get('dur'))
        ent += ['-i', str(arq)]
        ms = int(max(0, s['t']) * 1000)
        fil.append(f"[{k}:a]volume={s.get('ganho_db', -16)}dB,adelay={ms}|{ms}[e{j}]")
        efeitos.append(f'[e{j}]')
        k += 1
    rot = ['[voz]'] + (['[mus]'] if musica and Path(musica).exists() else []) + efeitos
    fil.append(''.join(rot) + f'amix=inputs={len(rot)}:normalize=0:duration=first,atrim=0:{duracao:.3f}[mix]')
    bruto = trab / 'mix_bruto.wav'
    rodar(['ffmpeg', '-v', 'error', '-y', *ent, '-filter_complex', ';'.join(fil), '-map', '[mix]', '-ac', '1', '-ar', '48000', bruto],
          log=trab / 'mix.log')
    # pré-normalização (−16 LUFS, pico −2): a mistura chegava com +1,2 dBFS e o master parava em −15,2 (execução 43956541084)
    pre = trab / 'mix_pre.wav'
    rodar(['ffmpeg', '-v', 'error', '-y', '-i', bruto, '-af', 'loudnorm=I=-16:TP=-2:LRA=11,aresample=48000', '-ar', '48000', '-ac', '1', pre], log=trab / 'pre.log')
    rel = master_canal(bruto, saida, trab, preset) if preset.get('lufs') is not None else masterizar(pre, saida)
    return {'master': rel, 'efeitos': [{'id': s['id'], 't': s['t'], 'justificativa': s.get('justificativa')} for s in sfx],
            'musica': str(musica.name) if musica else None}


def master_canal(bruto: Path, saida: Path, trab: Path, preset: dict) -> dict:
    """master do PADRÃO SONORO do canal (formatos): ganho LINEAR até o alvo (não muda a distância fala × pausas da mistura;
    o master antigo achatava as pausas 15 → 11,8 dB) + limitador de pico VERDADEIRO (superamostrado a 192 kHz), medido
    e corrigido no máximo 3 vezes. Alvo e teto vêm do canal (−14 LUFS, ≤ −1 dBTP)."""
    from src.fiscal import medir_audio
    alvo, tp = float(preset.get('lufs', -14)), float(preset.get('true_peak', -1.0))
    # o AAC do MP4 sobe o pico verdadeiro ~1 dB (medido: −1,5 no WAV → −0,5 no AAC): o WAV fica 1,2 dB abaixo do teto
    lim = 10 ** ((tp - 1.2 - .3) / 20)
    atual, fonte, med = None, bruto, {}
    for k in range(3):
        med0 = medir_audio(fonte) if atual is None else med
        g = alvo - med0['lufs']
        dst = trab / f'master_{k}.wav'
        rodar(['ffmpeg', '-v', 'error', '-y', '-i', fonte, '-af', f'volume={g:.2f}dB,aresample=192000,alimiter=limit={lim:.4f}:attack=1:release=60:level=false,aresample=48000',
               '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', dst])
        med = medir_audio(dst)
        fonte, atual = dst, k
        if abs(med['lufs'] - alvo) <= .3 and med.get('pico', 0) <= tp - 1.2:
            break
    Path(fonte).replace(saida)
    return {'arquivo': str(saida), 'medido': med, 'alvo': {'lufs': alvo, 'true_peak': tp}, 'cadeia': 'ganho linear → limitador de pico verdadeiro (192 kHz), medido'}


def silencio(dur: float, saida: Path) -> Path:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=mono', '-t', f'{dur:.3f}', str(saida)], check=True)
    return saida
