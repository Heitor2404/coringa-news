"""MÓDULO OPCIONAL MANIM (MIT) — animações científicas quando HTML/SVG não bastam (geometria exata, transformações,
trajetórias calculadas quadro a quadro). Não é usado para tudo: o palco V2 já cobre diagramas, forças e órbitas.

Saída: sequência de quadros JPG 1080×1920 (mesma prancheta da V2, sem texto: a tipografia fica com o palco, para a
identidade não mudar), consumida pela composição `animacao.quadros`.
Dependências do sistema: Cairo + Pango (Ubuntu: libpango1.0-dev, libcairo2-dev). Sem elas, `disponivel()` é False e
a montagem não escolhe esta composição.

Uso: python -m src.v2.manim_cenas lancamento saida/manim/lancamento --angulo 50 --v 1 --dur 4
"""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

FUNDO = '#0C2A33'
CIANO, AMARELO, VERMELHO, BRANCO = '#3FD0E0', '#FFD21F', '#FF4D3D', '#FFFFFF'


def disponivel() -> bool:
    try:
        import manim  # noqa: F401
        return shutil.which('ffmpeg') is not None
    except Exception:
        return False


def _cena_lancamento(angulo: float, dur: float):
    from manim import (Arrow, Axes, Dot, DashedLine, Scene, TracedPath, ValueTracker, always_redraw, linear, config)
    a = math.radians(angulo)

    class Lancamento(Scene):
        """Lançamento oblíquo: trajetória parabólica com o vetor velocidade e suas componentes (vx constante, vy muda)."""
        def construct(self):
            g, v0 = 9.8, 1.0
            T = 2 * v0 * math.sin(a) / g
            esc = 6.2 / (v0 ** 2 * math.sin(2 * a) / g)        # alcance = 6,2 unidades do eixo
            # mesma escala nos dois eixos (parábola sem distorção); área útil do palco: y ≈ 590–1090 px
            eixos = Axes(x_range=[0, 7, 1], y_range=[0, 4.6, 1], x_length=5.6, y_length=3.68, tips=False,
                         axis_config={'color': '#7FA3B8', 'stroke_width': 3, 'include_ticks': False}).shift([0, .88, 0])
            t = ValueTracker(0)
            def pos(tt):
                x, y = v0 * math.cos(a) * tt * esc, (v0 * math.sin(a) * tt - g * tt * tt / 2) * esc
                return eixos.c2p(x, y)
            bola = always_redraw(lambda: Dot(pos(t.get_value()), radius=.16, color=BRANCO))
            rastro = TracedPath(bola.get_center, stroke_color=AMARELO, stroke_width=6)
            def vel():
                tt = t.get_value(); p = pos(tt)
                L = 1.5                                                  # |v0| desenhado com 1,5 unidade
                vx, vy = L * math.cos(a), L * (math.sin(a) - g * tt / v0)
                out = [Arrow(p, p + [vx, 0, 0], buff=0, color=CIANO, stroke_width=8, max_tip_length_to_length_ratio=.2)]
                if abs(vy) > .06:
                    out.append(Arrow(p, p + [0, vy, 0], buff=0, color=VERMELHO, stroke_width=8, max_tip_length_to_length_ratio=.2))
                out.append(Arrow(p, p + [vx, vy, 0], buff=0, color=BRANCO, stroke_width=6, max_tip_length_to_length_ratio=.18))
                return out
            vetores = always_redraw(lambda: __import__('manim').VGroup(*vel()))
            topo = always_redraw(lambda: DashedLine(eixos.c2p(0, (v0 * math.sin(a)) ** 2 / (2 * g) * esc), eixos.c2p(7, (v0 * math.sin(a)) ** 2 / (2 * g) * esc), color='#7FA3B8', stroke_width=2, dash_length=.12))
            self.add(eixos, topo, rastro, bola, vetores)
            self.play(t.animate.set_value(T), run_time=dur, rate_func=linear)
    return Lancamento


CENAS = {'lancamento': _cena_lancamento}


def renderizar(nome: str, pasta: Path, dur: float = 4.0, fps: int = 30, **kw) -> dict:
    """Renderiza a cena e grava pasta/f_0001.jpg… Retorna {'dir', 'n', 'fps'} (formato de vídeo do motor)."""
    from manim import config, tempconfig
    pasta.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        with tempconfig({'pixel_width': 1080, 'pixel_height': 1920, 'frame_width': 8.0, 'frame_height': 8.0 * 1920 / 1080,
                         'frame_rate': fps, 'background_color': FUNDO, 'media_dir': tmp, 'disable_caching': True,
                         'output_file': nome, 'verbosity': 'ERROR', 'progress_bar': 'none'}):
            cls = CENAS[nome](dur=dur, **kw)
            cena = cls()
            cena.render()
            mp4 = Path(cena.renderer.file_writer.movie_file_path)
        for f in pasta.glob('f_*.jpg'):
            f.unlink()
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-q:v', '3', str(pasta / 'f_%04d.jpg')], check=True)
    n = len(list(pasta.glob('f_*.jpg')))
    return {'dir': str(pasta), 'n': n, 'fps': fps}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('nome', choices=list(CENAS))
    ap.add_argument('pasta')
    ap.add_argument('--angulo', type=float, default=50)
    ap.add_argument('--dur', type=float, default=4)
    a = ap.parse_args()
    print(renderizar(a.nome, Path(a.pasta), dur=a.dur, angulo=a.angulo))
