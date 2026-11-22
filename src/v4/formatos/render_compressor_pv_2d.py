"""Animação vetorial autoral de compressor: motor visual dirigido por pressão.

O operador não depende de nome de episódio. A geometria da familia slider-
crank é gerada por fórmula, pressão por modelo P-V politrópico e válvulas são
AUTOATUADAS. Não há ignição, válvula de escape de combustão ou fases Otto.
Referências de engenharia explicam processo; esta prova NÃO foi reconstruída
de um vídeo específico do compressor e NÃO recebe status 'reference approved'.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import subprocess
from dataclasses import asdict
from pathlib import Path
from xml.sax.saxutils import escape

import cairosvg
from PIL import Image

from src.v4.formatos.compressor_pv_core import (
    CompressorSpec, CompressorState, estado, limites_fases, REFERENCIAS,
)

SIZE = (540,960)
STATE_STYLE = {
    "REEXPANSAO_RESIDUAL": ("01","AR RESIDUAL EXPANDE",
        "A pressão cai antes da admissão.", "#70B8C8"),
    "ADMISSAO_AR": ("02","O AR ENTRA",
        "A válvula de sucção abre sozinha.", "#3FCECF"),
    "COMPRESSAO_AR": ("03","O VOLUME DIMINUI",
        "As duas válvulas ficam fechadas.", "#EAA84C"),
    "DESCARGA_PRESSURIZADA": ("04","AR SOB PRESSÃO SAI",
        "A válvula de descarga se abre.", "#FF9D56"),
}


def color_blend(start: tuple[int,int,int],end: tuple[int,int,int],t:float) -> str:
    t=max(0,min(1,t))
    rgb=tuple(round(a*(1-t)+b*t) for a,b in zip(start,end))
    return "#%02X%02X%02X"%rgb


def draw_svg(t: float, spec: CompressorSpec = CompressorSpec()) -> str:
    s=estado(t,spec)
    _,label,description,accent=STATE_STYLE[s.estado]
    piston_top=s.pistao_y-43
    chamber_height=max(3.0,piston_top-371)
    ratio=(s.pressao_relativa-1)/(spec.pressao_saida_relativa-1)
    gas=color_blend((63,198,212),(248,153,82),ratio)
    pressure_num=f"{s.pressao_relativa:.1f}"
    bar=round(140*ratio)
    intake_y=12 if s.admissao_aberta else 0
    discharge_y=-12 if s.descarga_aberta else 0
    arrow_dots=""
    travel=(t*8)%1
    if s.admissao_aberta:
        positions=[(70+i*27+travel*26,337) for i in range(6)]
        positions += [(205,385+j*21+travel*19) for j in range(2)]
        arrow_dots="".join(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5+i%3}" fill="#168EA6" opacity=".85"/>'
            for i,(x,y) in enumerate(positions))
        arrow_dots+=('<path d="M 167 327 l 18 11 l -18 11" '
                     'fill="none" stroke="#0C8FA7" stroke-width="6" stroke-linejoin="round"/>')
    elif s.descarga_aberta:
        positions=[(330,389-j*23-travel*18) for j in range(2)]
        positions += [(370+i*22+travel*20,341) for i in range(6)]
        arrow_dots="".join(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5+i%3}" fill="#D97936" opacity=".87"/>'
            for i,(x,y) in enumerate(positions))
        arrow_dots+=('<path d="M 450 330 l 18 11 l -18 11" '
                     'fill="none" stroke="#B86A35" stroke-width="6" stroke-linejoin="round"/>')

    heat_waves=""
    if s.estado=="COMPRESSAO_AR":
        for x in (217,258,299):
            heat_waves+=(
                f'<path d="M {x} {piston_top-9:.1f} '
                f'l -7 -14 l 7 -13" fill="none" stroke="#C47731" '
                f'stroke-width="4" stroke-linecap="round"/>')
    # Posição das bielas usa MESMAS coordenadas que o pistão e crankshaft.
    rod_a=(spec.eixo_x,s.pistao_y)
    rod_b=(s.crank_x,s.crank_y)
    wheel_rot=math.degrees(s.angulo)
    trend=("DESCENDO" if s.sentido_pistao=="DESCENDO" else "SUBINDO")
    sequence_keys=list(STATE_STYLE)
    current_index=sequence_keys.index(s.estado)
    progress=round(454*t)
    stage_bars="".join(
        f'<rect x="{43+i*115}" y="202" width="103" height="7" rx="3" '
        f'fill="{accent if i==current_index else "#527086"}"/>'
        for i in range(4))
    # P-V plot: texto/valores na esquerda baixa, não no overlay de rede.
    # Medida de vazão/pressão não representa pressão absoluta em bar.
    pressure_lights="".join(
        f'<rect x="{393+i*14}" y="553" width="10" height="26" rx="4" '
        f'fill="{accent if i/10<=ratio else "#BFCFD2"}"/>'
        for i in range(10))
    pressure_color=("#6DCBD0" if s.pressao_relativa<2
                    else "#F1C174" if s.pressao_relativa<4 else "#E78B54")
    tank_valve=("#F1A55F" if s.descarga_aberta else "#658392")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="540"
      height="960" viewBox="0 0 540 960">
    <defs>
      <linearGradient id="back" x1="0" x2="0" y1="0" y2="1">
        <stop stop-color="#EDF7F7"/><stop offset="1" stop-color="#C6DEE2"/>
      </linearGradient>
      <linearGradient id="steel" x1="0" x2="1">
        <stop stop-color="#29485A"/>
        <stop offset=".20" stop-color="#91AEBB"/>
        <stop offset=".45" stop-color="#E4F1EF"/>
        <stop offset=".76" stop-color="#8CA6B6"/>
        <stop offset="1" stop-color="#3B5665"/>
      </linearGradient>
      <linearGradient id="piston" x1="0" x2="1">
        <stop stop-color="#577787"/>
        <stop offset=".25" stop-color="#E6F0F0"/>
        <stop offset=".63" stop-color="#A3BAC4"/>
        <stop offset="1" stop-color="#547485"/>
      </linearGradient>
      <linearGradient id="yellow" x1="0" x2="1">
        <stop stop-color="#93643D"/><stop offset=".5" stop-color="#E5C58A"/>
        <stop offset="1" stop-color="#9B7348"/>
      </linearGradient>
      <pattern id="grid" width="37" height="37" patternUnits="userSpaceOnUse">
        <path d="M 37 0 H 0 V 37" fill="none" stroke="#9CBCC5" stroke-width=".6" opacity=".35"/>
      </pattern>
      <clipPath id="volume">
        <rect x="196" y="369" width="143" height="238" rx="4"/>
      </clipPath>
    </defs>
    <rect width="540" height="960" fill="url(#back)"/>
    <rect x="0" y="218" width="540" height="702" fill="url(#grid)"/>
    <rect width="540" height="221" fill="#112C41"/>
    <rect x="44" y="18" width="177" height="26" rx="6" fill="#F3C45C"/>
    <text x="55" y="36" font-family="DejaVu Sans" font-size="13"
      font-weight="900" fill="#1E3242">CORINGA EXPLICA</text>
    <text x="44" y="93" font-family="DejaVu Sans" font-size="30"
      font-weight="900" fill="#FFFFFF">COMPRESSOR DE AR</text>
    <text x="44" y="137" font-family="DejaVu Sans" font-size="22"
      font-weight="900" fill="{accent}">{escape(label)}</text>
    <text x="44" y="171" font-family="DejaVu Sans" font-size="15"
      fill="#D8E7EB">{escape(description)}</text>
    {stage_bars}
    <!-- Tubulação lateral: válvula de entrada e de saída distintas -->
    <path d="M 36 337 H 184 Q 203 337 205 356" fill="none"
      stroke="#3F6479" stroke-width="38" stroke-linecap="round"/>
    <path d="M 36 337 H 184 Q 203 337 205 356" fill="none"
      stroke="#C2E4E8" stroke-width="22" stroke-linecap="round"/>
    <path d="M 328 358 Q 333 337 359 337 H 502" fill="none"
      stroke="#516C80" stroke-width="38" stroke-linecap="round"/>
    <path d="M 328 358 Q 333 337 359 337 H 502" fill="none"
      stroke="#EADDC9" stroke-width="22" stroke-linecap="round"/>
    <text x="43" y="298" font-family="DejaVu Sans" font-size="16"
      fill="#1E7990" font-weight="900">ENTRADA</text>
    <text x="407" y="296" font-family="DejaVu Sans" font-size="16"
      fill="#9B633D" font-weight="900">SAÍDA</text>
    <!-- Carcaça e bloco do compressor, cortados pelo centro -->
    <path d="M 158 349 H 372 L 392 381 V 630 L 418 662
      V 876 H 116 V 662 L 143 630 V 381 Z"
      fill="#587A8D" stroke="#223F53" stroke-width="10"
      stroke-linejoin="round"/>
    <path d="M 133 696 H 400 V 853 Q 385 874 364 874 H 169
      Q 133 859 133 830 Z" fill="#DAE4E7" stroke="#37576A"
      stroke-width="7"/>
    <path d="M 145 706 H 391" stroke="#FAFFFF" stroke-width="11" opacity=".8"/>
    <rect x="168" y="362" width="200" height="270" rx="10"
      fill="url(#steel)" stroke="#345467" stroke-width="9"/>
    <rect x="193" y="370" width="149" height="249" rx="3"
      fill="#E6F3F1" stroke="#446778" stroke-width="11"/>
    <g clip-path="url(#volume)">
      <rect x="196" y="370" width="143" height="{chamber_height:.3f}"
        fill="{gas}" opacity="{.44+.20*ratio:.3f}"/>
      {heat_waves}
    </g>
    <!-- Cabeçote: válvulas são reeds com deslocamento por pressão,
         NAO recebem movimento de um comando de válvulas Otto -->
    <rect x="170" y="327" width="196" height="47" rx="11"
      fill="url(#steel)" stroke="#284D60" stroke-width="7"/>
    <path d="M 181 341 H 355" stroke="#E7F6F4" stroke-width="7"/>
    <path d="M 209 302 V 372" stroke="#4F7A8D" stroke-width="10"/>
    <path d="M 208 {372+intake_y} l -17 10 l 34 0 Z"
      fill="#2D98AB" stroke="#20586C" stroke-width="4"/>
    <path d="M 330 302 V 371" stroke="#637F8D" stroke-width="10"/>
    <path d="M 329 {372+discharge_y} l -17 10 l 34 0 Z"
      fill="#CF9369" stroke="#6D5B50" stroke-width="4"/>
    <rect x="256" y="283" width="21" height="49" rx="8"
      fill="#819DAF" stroke="#33556A" stroke-width="5"/>
    <path d="M 258 299 H 274" stroke="#F9FFFF" stroke-width="4"/>
    <!-- Pistão com geometria deslizante derivada da biela -->
    <rect x="195" y="{piston_top:.3f}" width="144" height="86" rx="15"
      fill="url(#piston)" stroke="#27495F" stroke-width="8"/>
    <rect x="196" y="{piston_top+3:.3f}" width="143" height="20" rx="9"
      fill="#E8F4F2" stroke="#587F91" stroke-width="4"/>
    <path d="M 201 {piston_top+29:.3f} H 334
      M 201 {piston_top+38:.3f} H 334"
      stroke="#597383" stroke-width="5"/>
    <!-- Volante com raio e biela sincronizados pela mesma manivela -->
    <g transform="translate({spec.eixo_x:.2f} {spec.eixo_y:.2f})
      rotate({math.degrees(s.angulo):.3f})">
      <circle r="91" fill="#5A7588" stroke="#263F52" stroke-width="10"/>
      <circle r="78" fill="#D6E6E8" stroke="#294F62" stroke-width="11"/>
      <circle r="55" fill="#6D899C" stroke="#466577" stroke-width="6"/>
      <path d="M -69 0 H 69 M 0 -69 V 69"
        stroke="#B5C9D0" stroke-width="11"/>
      <circle r="20" fill="#D1E3E4" stroke="#355568" stroke-width="6"/>
    </g>
    <line x1="{spec.eixo_x:.3f}" y1="{s.pistao_y:.3f}"
      x2="{s.crank_x:.3f}" y2="{s.crank_y:.3f}"
      stroke="#253B4C" stroke-width="35" stroke-linecap="round"/>
    <line x1="{spec.eixo_x:.3f}" y1="{s.pistao_y:.3f}"
      x2="{s.crank_x:.3f}" y2="{s.crank_y:.3f}"
      stroke="url(#yellow)" stroke-width="25" stroke-linecap="round"/>
    <line x1="{spec.eixo_x:.3f}" y1="{s.pistao_y:.3f}"
      x2="{s.crank_x:.3f}" y2="{s.crank_y:.3f}"
      stroke="#F3E2C5" stroke-width="4" opacity=".6"/>
    <circle cx="{s.crank_x:.3f}" cy="{s.crank_y:.3f}"
      r="23" fill="#93B0BA" stroke="#28495A" stroke-width="8"/>
    <circle cx="{spec.eixo_x:.3f}" cy="{s.pistao_y:.3f}"
      r="22" fill="#D7E6E8" stroke="#325267" stroke-width="8"/>
    <path d="M 184 375 V 627 M 350 375 V 627"
      stroke="#476678" stroke-width="12"/>
    <path d="M 167 381 V 611 M 369 381 V 611"
      stroke="#A9C3CA" stroke-width="7"/>
    {arrow_dots}
    <!-- Pressão e volume são variáveis de processo, não legendas decorativas -->
    <rect x="17" y="613" width="107" height="125" rx="12"
      fill="#13364C" opacity=".93"/>
    <text x="25" y="638" font-family="DejaVu Sans" font-weight="900"
      font-size="14" fill="#BDDEE8">PRESSÃO</text>
    <text x="26" y="671" font-family="DejaVu Sans" font-weight="900"
      font-size="30" fill="{pressure_color}">{pressure_num}×</text>
    <text x="27" y="696" font-family="DejaVu Sans" font-size="12"
      fill="#D5EAF0">relativa</text>
    <rect x="27" y="707" width="{80*ratio:.2f}" height="8" rx="4"
      fill="{accent}"/>
    <!-- Reservatório sugere função diferente de um motor a combustão -->
    <rect x="419" y="656" width="94" height="203" rx="44"
      fill="#3E7189" stroke="#24465C" stroke-width="8"/>
    <rect x="429" y="665" width="72" height="176" rx="34"
      fill="#C9DDE1" stroke="#6D96A8" stroke-width="5"/>
    <path d="M 449 659 V 624 H 492"
      stroke="#547D91" stroke-width="12" fill="none" stroke-linecap="round"/>
    <circle cx="450" cy="655" r="13" fill="{tank_valve}" stroke="#365366" stroke-width="5"/>
    <text x="432" y="747" font-family="DejaVu Sans" font-size="11"
      font-weight="900" fill="#36556A">RESER-</text>
    <text x="432" y="764" font-family="DejaVu Sans" font-size="11"
      font-weight="900" fill="#36556A">VATÓRIO</text>
    <text x="43" y="920" fill="#466A7E" font-family="DejaVu Sans"
      font-size="13" font-weight="800">FÍSICA P–V · SIMULAÇÃO DIDÁTICA PRIVADA</text>
    <text x="480" y="920" fill="#3B7189" font-family="DejaVu Sans"
      font-size="15" font-weight="900">{current_index+1:02d}/04</text>
  </svg>'''


def renderizar(destino: Path, spec: CompressorSpec = CompressorSpec(), *,
              fps: int = 24, duracao: float = 8.0) -> dict:
    spec.validar()
    if fps not in (24,30) or not 6 <= duracao <= 20:
        raise ValueError("F-RENDER-DURACAO")
    destino = Path(destino)
    destino.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pixel_format","rgb24",
         "-video_size","540x960","-framerate",str(fps),"-i","-",
         "-c:v","libx264","-preset","veryfast","-crf","21",
         "-pix_fmt","yuv420p","-movflags","+faststart",str(destino)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(round(fps*duracao)):
            svg=draw_svg(i/(fps*duracao),spec)
            pixels=cairosvg.svg2png(bytestring=svg.encode())
            with Image.open(io.BytesIO(pixels)) as img:
                data=img.convert("RGB").tobytes()
            if not proc.stdin:
                raise ValueError("F-FFMPEG-SEM-PIPE")
            proc.stdin.write(data)
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not destino.is_file() or destino.stat().st_size<50_000:
        raise ValueError("F-COMPRESSOR-RENDER-INVALIDO")
    report={
        "schema":"compressor-physics-private-v1",
        "estado":"VIDEO_FISICA_COMPRESSOR_PV_RENDERIZADO_NAO_REFERENCE_RECONSTRUCTED",
        "publicar":False,
        "capacidade":"COMPRESSOR_COM_VALVULAS_DE_PRESSAO_E_FLUXO",
        "fonte_modelo":"FORMULAS_TERMO_PV_NAO_MOTION_EXTERNAL",
        "referencias_de_engenharia":list(REFERENCIAS),
        "referencia_compressor_animada_medida":False,
        "fases_por_pressao":limites_fases(spec),
        "configuracao":asdict(spec),
        "duracao_s":duracao,"fps":fps,"resolucao":list(SIZE),
        "arquivo_sha256":hashlib.sha256(destino.read_bytes()).hexdigest(),
        "analise_estetica":"PENDENTE",
        "nota":"P/Pin normalizada, pressao real pode variar; sem CFD. Valvulas simplificadas.",
    }
    destino.with_suffix(".json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("arquivo_mp4")
    a=p.parse_args()
    print(json.dumps(renderizar(Path(a.arquivo_mp4)),ensure_ascii=False))
