"""Manim Community 0.19 — cenas de PRECISÃO do Coringa (dados e relações físicas). Parâmetros por JSON (env CORINGA_PARAMS).
dados.escala: uma altura medida (ex.: 26 m) ao lado de referências de escala com altura declarada; régua em metros exata.
Sem LaTeX (Text/Pango com as fontes da identidade). 1080×1920, 30 fps.

uso: CORINGA_PARAMS=params.json manim -r 1080,1920 --fps 30 -o saida.mp4 --media_dir DIR cenas.py EscalaAltura
"""
import json
import os

from manim import (DOWN, LEFT, RIGHT, UP, Create, DashedLine, FadeIn, GrowFromEdge, Line, Rectangle, Scene, Text,
                   VGroup, config, linear, rate_functions)

P = json.load(open(os.environ['CORINGA_PARAMS'])) if os.environ.get('CORINGA_PARAMS') else {}
config.background_color = P.get('fundo', '#0B0F17')
# quadro 9:16 em unidades (sem isso o Manim mantém a largura de paisagem e a cena vira um cartão pequeno no meio)
config.frame_height, config.frame_width = 16.0, 9.0
# 1 unidade = 120 px. Áreas seguras: texto entre y=+4.5 (420 px) e y=-2.3 (topo da faixa de legendas, 1240 px)
AM, BR, AG, CZ = '#FFD21F', '#FFFFFF', '#2F8FD8', '#8A929E'
FT, FD = 'Montserrat', 'JetBrains Mono'


class EscalaAltura(Scene):
    def construct(self):
        dur = float(P.get('duracao', 6))
        alvo = P.get('alvo', {'nome': 'eclusa', 'altura_m': 26})
        refs = P.get('referencias', [])                 # [{nome, altura_m, fonte}] — altura DECLARADA (com fonte)
        topo_m = max([alvo['altura_m']] + [r['altura_m'] for r in refs]) * 1.12
        y0, y1 = -2.0, 3.3
        esc = (y1 - y0) / topo_m
        x_r = -3.0
        titulo = Text(P.get('titulo', 'QUANTO O NAVIO SOBE'), font=FT, weight='HEAVY', color=BR).scale(1.25)
        titulo.scale_to_fit_width(min(titulo.width, 7.6)).move_to(UP * 4.2)   # nunca transborda a largura
        regua = Line([x_r, y0, 0], [x_r, y1, 0], color=CZ, stroke_width=4)
        marcas = VGroup()
        passo = P.get('passo_m', 5)
        m = 0
        while m <= topo_m:
            y = y0 + m * esc
            marcas.add(Line([x_r - .18, y, 0], [x_r + .18, y, 0], color=CZ, stroke_width=4))
            marcas.add(Text(f'{m:g} m', font=FD, color=CZ).scale(.5).next_to([x_r - .18, y, 0], LEFT, buff=.12))
            m += passo
        chao = Line([-3.4, y0, 0], [4.2, y0, 0], color=CZ, stroke_width=3)
        self.add(titulo)
        self.play(Create(regua), Create(chao), FadeIn(marcas), run_time=min(1.0, dur * .15))
        # coluna do alvo: água subindo até a altura exata
        h = alvo['altura_m'] * esc
        col = Rectangle(width=2.1, height=h, color=AG, fill_color=AG, fill_opacity=.9, stroke_width=0).move_to([-1.4, y0 + h / 2, 0])
        lab = Text(f"{alvo['altura_m']:g} m", font=FT, weight='HEAVY', color=AM).scale(1.5).next_to(col, UP, buff=.2)
        nome = Text(alvo['nome'].upper(), font=FD, color=BR).scale(.52).next_to(col, DOWN, buff=.22)
        self.play(GrowFromEdge(col, DOWN), run_time=max(1.0, dur * .3), rate_func=rate_functions.ease_in_out_cubic)
        self.play(FadeIn(lab), FadeIn(nome), run_time=.4)
        topo = DashedLine([-2.6, y0 + h, 0], [4.2, y0 + h, 0], color=AM, dash_length=.2, stroke_width=5)
        self.play(Create(topo), run_time=.4)
        # referências de escala (blocos com andares, se dito)
        x = 1.4
        for r in refs[:2]:
            hr = r['altura_m'] * esc
            bloco = VGroup(Rectangle(width=1.9, height=hr, color=BR, fill_color='#3B4350', fill_opacity=1, stroke_width=2).move_to([x, y0 + hr / 2, 0]))
            for k in range(1, int(r.get('andares', 0))):
                yy = y0 + hr * k / r['andares']
                bloco.add(Line([x - .95, yy, 0], [x + .95, yy, 0], color='#5B6472', stroke_width=3))
            rot = Text(r['nome'], font=FD, color=BR).scale(.46).next_to(bloco, DOWN, buff=.22)
            self.play(GrowFromEdge(bloco, DOWN), FadeIn(rot), run_time=max(.6, dur * .12))
            x += 2.4
        resto = dur - self.renderer.time
        if resto > 0:
            self.wait(resto)
