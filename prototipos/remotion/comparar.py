"""Mesmo trabalho no palco V2 (HTML + seek(t) + Playwright + ffmpeg, 2 processos) para comparar com render.mjs.
Uso (da raiz): python prototipos/remotion/comparar.py"""
import json, subprocess, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.render import render
from src.v2 import galeria

pico = 0
def amostrar(parar):
    global pico
    while not parar.is_set():
        out = subprocess.run("ps -eo rss,comm | grep -Ei 'chrom|python|ffmpeg' | awk '{s+=$1} END {print s}'", shell=True, capture_output=True, text=True).stdout.strip()
        pico = max(pico, int(out or 0)); time.sleep(.25)

trab = Path('saida/_bench_v2').resolve(); trab.mkdir(parents=True, exist_ok=True)
meta = next(m for m in galeria.catalogo(trab / 'cat') if m['id'] == 'numero.animado')
d = galeria.dados_exemplo(meta); d['meta']['motor'] = 'v2'; d['captions'] = []
audio = trab / 'mudo.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', str(d['duration']), str(audio)], check=True)
parar = threading.Event(); th = threading.Thread(target=amostrar, args=(parar,)); th.start()
t0 = time.time(); render.renderizar(d, audio, trab / 'numero_v2.mp4', trab / 'tr', workers=2); t1 = time.time()
parar.set(); th.join()
print(json.dumps({'render_s': round(t1 - t0, 2), 'quadros': int(d['duration'] * 30), 'pico_rss_mb': pico // 1024}))
