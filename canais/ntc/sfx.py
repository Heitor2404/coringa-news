"""Efeitos sonoros do canal, SINTETIZADOS por código (sem direitos de terceiros). python sfx.py → sfx/*.wav"""
import numpy as np, wave, pathlib
R = 44100
def t(d): return np.linspace(0, d, int(R * d), endpoint=False)
def env(x, a=0.01, r=0.2):
    n = len(x); e = np.ones(n); na, nr = int(R * a), int(R * r)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return x * e
def ruido(d): return np.random.default_rng(1).uniform(-1, 1, int(R * d))
def saw(f, x): return 2 * ((f * x) % 1) - 1
S = {}
x = t(0.12); S['pop'] = env(np.sin(2 * np.pi * (900 - 5000 * x) * x), 0.002, 0.08)
x = t(0.45); n = ruido(0.45); S['whoosh'] = env(n * np.sin(np.pi * x / 0.45) ** 2, 0.01, 0.1) * 0.6
x = t(0.7); S['buzina'] = env(sum(saw(f, x) for f in (440, 554, 659)) / 3, 0.01, 0.15) * 0.7
x = t(1.2); S['festa'] = np.concatenate([S['buzina'], env(ruido(0.5) * 0.3, 0.001, 0.4)])
x = t(1.5); S['mosca'] = env(saw(190 + 25 * np.sin(2 * np.pi * 7 * x), x) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * x)), 0.1, 0.3) * 0.35
x = t(0.18); g = env(np.sin(2 * np.pi * (2600 + 1800 * np.sin(2 * np.pi * 30 * x)) * x), 0.005, 0.06)
S['rato'] = np.concatenate([g, np.zeros(int(R * 0.06)), g * 0.8, np.zeros(int(R * 0.05)), g * 0.6]) * 0.5
x = t(0.06); c = env(np.sin(2 * np.pi * 4200 * x), 0.002, 0.03)
S['grilo'] = np.concatenate([np.concatenate([c, np.zeros(int(R * 0.03))]) for _ in range(3)] + [np.zeros(int(R * 0.4))] + [np.concatenate([c, np.zeros(int(R * 0.03))]) for _ in range(3)]) * 0.4
x = t(0.6); S['boing'] = env(np.sin(2 * np.pi * (180 + 120 * np.sin(2 * np.pi * 9 * x) * np.exp(-4 * x)) * x), 0.002, 0.3) * 0.8
x = t(0.9); S['ding'] = (np.sin(2 * np.pi * 1320 * x) + 0.5 * np.sin(2 * np.pi * 2640 * x)) * np.exp(-5 * x) * 0.6
def acorde(fs, d):
    x = t(d); return env(sum(saw(f, x) * 0.5 + np.sin(2 * np.pi * f * x) for f in fs) / len(fs), 0.01, 0.2)
S['tchan'] = np.concatenate([acorde((196, 233, 294), 0.25), np.zeros(int(R * 0.08)), acorde((185, 220, 277), 0.25), np.zeros(int(R * 0.08)), acorde((175, 208, 262), 0.9)]) * 0.5
x = t(0.35); S['scratch'] = env(ruido(0.35) * np.sin(2 * np.pi * (60 + 300 * x) * x), 0.005, 0.1) * 0.7
x = t(0.8); S['explosao'] = env(np.convolve(ruido(0.8), np.ones(40) / 40, 'same') * np.exp(-4 * x), 0.001, 0.2) * 2.5
x = t(0.35); S['plim'] = np.concatenate([np.sin(2 * np.pi * 1568 * t(0.1)) * np.exp(-20 * t(0.1)), np.sin(2 * np.pi * 2093 * x) * np.exp(-8 * x)]) * 0.5
x = t(0.5); S['apito'] = env(np.sin(2 * np.pi * 2200 * x + 3 * np.sin(2 * np.pi * 40 * x)), 0.01, 0.1) * 0.4
x = t(0.9); S['triste'] = np.concatenate([env(np.sin(2 * np.pi * f * t(0.3)) * 0.6, 0.01, 0.1) for f in (392, 370, 349)] + [env(np.sin(2 * np.pi * 330 * x) * (1 + 0.3 * np.sin(2 * np.pi * 6 * x)) * 0.5, 0.01, 0.4)])
x = t(0.7); S['vomito'] = env(np.convolve(ruido(0.7), np.ones(15) / 15, 'same') * saw(110 - 40 * x, x), 0.02, 0.2) * 1.2
LISTA = sorted(S)
if __name__ == '__main__':
    pasta = pathlib.Path(__file__).parent / 'sfx'; pasta.mkdir(exist_ok=True)
    for n, a in S.items():
        a = np.clip(a / max(1e-9, np.abs(a).max()) * 0.9, -1, 1)
        with wave.open(str(pasta / f'{n}.wav'), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(R); w.writeframes((a * 32767).astype('<i2').tobytes())
    print(len(S), 'efeitos:', ', '.join(LISTA))
