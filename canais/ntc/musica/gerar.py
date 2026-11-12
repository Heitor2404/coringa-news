"""Gera as trilhas cômicas do Ninguém Te Contou (tudo sintetizado aqui: sem licença de terceiros).
Uso: python canais/ntc/musica/gerar.py   → cria trilha_1..5.mp3 nesta pasta (loop de ~32 s)."""
import subprocess, wave
from pathlib import Path
import numpy as np

SR = 44100
PASTA = Path(__file__).resolve().parent
NOTAS = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}


def hz(nota: str) -> float:
    n, o = nota[:-1], int(nota[-1])
    return 440.0 * 2 ** ((NOTAS[n] + 12 * (o - 4) - 9) / 12)


def env(n, a=.005, d=.25):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def pluck(f, dur, d=.18):          # pizzicato/ukulele: som curtinho e "pulado"
    t = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * f * t) + .45 * np.sin(4 * np.pi * f * t) + .2 * np.sin(6 * np.pi * f * t)
    return x * env(len(t), .003, d)


def xilo(f, dur):                  # xilofone/marimba
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t / .03)) * env(len(t), .002, .22)


def tuba(f, dur):                  # baixo "oom-pah"
    t = np.arange(int(dur * SR)) / SR
    x = np.sign(np.sin(2 * np.pi * f * t)) * .5 + np.sin(2 * np.pi * f * t)
    return np.tanh(x) * env(len(t), .01, .16)


def bumbo(dur=.25):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * (55 + 90 * np.exp(-t / .03)) * t) * np.exp(-t / .12)


def caixa(dur=.15):
    t = np.arange(int(dur * SR)) / SR
    return np.random.default_rng(1).uniform(-1, 1, len(t)) * np.exp(-t / .04) * .6


def trilha(bpm, tom, prog, melodia, timbre, swing=0.0, seed=0):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    compassos = 16
    total = int(compassos * 4 * beat * SR) + SR
    out = np.zeros(total)
    def poe(sinal, t, vol):
        i = int(t * SR); j = min(total, i + len(sinal)); out[i:j] += sinal[:j - i] * vol
    raiz = hz(tom + '2')
    for c in range(compassos):
        grau = prog[c % len(prog)]
        fb = raiz * 2 ** (grau / 12)
        for b in range(4):
            t = (c * 4 + b) * beat
            poe(tuba(fb if b % 2 == 0 else fb * 1.5, beat * .9), t, .35)          # oom-pah
            poe(bumbo(), t, .55 if b % 2 == 0 else 0)
            if b % 2 == 1:
                poe(caixa(), t, .35)
            for meio in (0, .5):                                                 # melodia em colcheias
                k = (c * 8 + b * 2 + int(meio * 2))
                passo = melodia[k % len(melodia)]
                if passo is None or (k % 16 in (7, 15) and rng.random() < .5):
                    continue
                f = hz(tom + '4') * 2 ** ((grau + passo) / 12)
                ts = t + meio * beat + (swing * beat * .5 if meio else 0)
                poe(timbre(f, beat * .5), ts, .28)
    out /= np.max(np.abs(out)) + 1e-9
    return (out * .85 * 32767).astype(np.int16)


def salvar(arr, nome):
    wav = PASTA / f'{nome}.wav'
    with wave.open(str(wav), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(arr.tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-b:a', '96k', str(PASTA / f'{nome}.mp3')], check=True)
    wav.unlink()


TRILHAS = [
    (118, 'C', [0, 5, 7, 0], [0, 4, 7, 4, 9, 7, 4, None, 5, 9, 12, 9, 7, 4, 2, None], pluck, .25),
    (126, 'F', [0, 0, 5, 7], [7, None, 4, 7, 9, None, 7, 4, 2, 4, 5, None, 4, 2, 0, None], xilo, .2),
    (104, 'G', [0, 7, 5, 7], [0, 2, 4, 7, 4, 2, 0, None, 7, 9, 7, 4, 2, None, 0, None], pluck, .33),
    (132, 'D', [0, 5, 0, 7], [12, 7, 4, 7, 12, None, 11, 9, 7, 4, 7, None, 5, 4, 2, None], xilo, .15),
    (112, 'A#', [0, 3, 5, 7], [0, None, 3, 5, 7, None, 5, 3, 0, 3, 5, 7, 10, None, 7, None], pluck, .28),
]

if __name__ == '__main__':
    for k, (bpm, tom, prog, mel, timbre, sw) in enumerate(TRILHAS, 1):
        salvar(trilha(bpm, tom, prog, mel, timbre, sw, k), f'trilha_{k}')
        print('trilha', k)
    # som do contador: tic-tic-tic acelerando (0,9 s) + "pum" no fim
    n = int(1.6 * SR); x = np.zeros(n)
    for i, tt in enumerate(np.cumsum([.09] * 4 + [.07] * 4 + [.05] * 5)):
        if tt > .9: break
        s = xilo(1800 + i * 40, .05)[:int(.05 * SR)]; j = int(tt * SR); x[j:j + len(s)] += s * .5
    p = bumbo(.4) + .5 * pluck(hz('C3'), .4, .1); j = int(.95 * SR); x[j:j + len(p)] += p
    x /= np.max(np.abs(x)); salvar((x * .9 * 32767).astype(np.int16), 'contagem')
