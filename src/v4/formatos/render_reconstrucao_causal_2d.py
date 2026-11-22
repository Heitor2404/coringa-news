"""Reconstrução 2D original orientada por movimento medido de referência real.

Não copia pixels. Requer medição de tracking CV2 vinculada a SHA da fonte
e grafo de acontecimentos REVISADOS (válvulas/fluxos ainda não extraídos
automaticamente por IA). O mesmo renderer distingue PROCESSO e faz válvulas,
gases, ignição e escape sincronizados. Bloqueia compressor sem prova própria.
SVG animado -> CairoSVG -> FFmpeg, privado, sem narração ou postagem.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

import cairosvg
from PIL import Image

WIDTH, HEIGHT = 540, 960
CX, CY = 267., 790.

SEQUENCIAS = {
    "motor_otto_4t": [
        "admissao_mistura", "compressao_mistura",
        "ignicao_expansao", "escape_gases",
    ],
    "compressor_alternativo": [
        "admissao_ar", "compressao_ar", "descarga_ar",
    ],
}


def validar(mov: dict, scene: dict) -> None:
    if (mov.get("schema") != "reference-first-measured-motion-v1" or
            scene.get("schema") != "reference-first-reviewed-scene-v1"):
        raise ValueError("F-SEM-GRAFO-OU-MEDICAO-VALIDOS")
    if (mov.get("origem_sha256") != scene.get("origem_sha256") or
            mov.get("referencia_id") != scene.get("referencia_id")):
        raise ValueError("F-REFERENCIA-DIVERGENTE")
    if (scene.get("publicar") is not False or
            scene.get("revisao_humana") != "REVISADA_NA_FONTE" or
            not scene.get("creditos")):
        raise ValueError("F-CENA-NAO-REVISADA")
    if scene.get("processo") != mov.get("processo_declarado"):
        raise ValueError("F-PROCESSO-INVALIDO")
    if not isinstance(mov.get("posicoes_y_px"), list) or len(mov["posicoes_y_px"]) < 24:
        raise ValueError("F-MOVIMENTO-INCOMPLETO")
    fit = mov.get("ajuste_geometrico") or {}
    corr = mov.get("qualidade_correlacao") or {}
    if (corr.get("min", 0) < .73 or fit.get("erro_medio_px", 99) > 1.0 or
            fit.get("biela_px", 0) <= fit.get("raio_px", 999)):
        raise ValueError("F-MEDICAO-INADEQUADA")

    if scene.get("processo") not in SEQUENCIAS:
        raise ValueError("F-PROCESSO-NAO-IMPLEMENTADO")
    strokes = scene.get("ciclo")
    if (not isinstance(strokes, list) or
            [x.get("tipo") for x in strokes if isinstance(x, dict)]
            != SEQUENCIAS[scene["processo"]]):
        raise ValueError("F-CICLO-DIFERENTE-DO-PROCESSO")
    if (scene["processo"] == "motor_otto_4t" and mov.get("revolucoes") != 2):
        raise ValueError("F-OTTO-EXIGE-DOIS-GIROS")
    if (scene["processo"] == "compressor_alternativo" and
            mov.get("revolucoes") != 1):
        raise ValueError("F-COMPRESSOR-UM-GIRO")

    evidencias = scene.get("evidencia_eventos")
    if not isinstance(evidencias, list) or len(evidencias) != len(strokes):
        raise ValueError("F-EVENTOS-SEM-EVIDENCIA-ANOTADA")
    starts = [x.get("quadro_inicio") for x in strokes]
    if starts[0] != 0 or starts != sorted(set(starts)):
        raise ValueError("F-ETAPAS-FORA-DE-ORDEM")
    if any(type(k) is not int or k < 0 or k >= mov["quadros"] for k in starts):
        raise ValueError("F-ETAPA-FORA-DA-REFERENCIA")
    for evidence, stage in zip(evidencias, strokes):
        if (not isinstance(evidence, dict) or
                evidence.get("tipo") != stage.get("tipo") or
                not isinstance(evidence.get("quadro_comprovacao"), list) or
                len(evidence["quadro_comprovacao"]) < 2 or
                any(type(q) is not int or q < 0 or q >= mov["quadros"]
                    for q in evidence["quadro_comprovacao"]) or
                not evidence.get("metodo")):
            raise ValueError("F-EVIDENCIA-ETAPA-NAO-TEM-PAR")
    if (scene.get("render_em_privado") is not True or
            scene.get("licenca_origem_verificada") is not True):
        raise ValueError("F-PRIVACIDADE-OU-LICENCA")


def pose(t: float, mov: dict) -> dict:
    """Escala r/L/fase MEDIDOS em frames reais; juntas fisicamente conectadas."""
    fit = mov["ajuste_geometrico"]
    scale = 64. / fit["raio_px"]
    r, L = 64., fit["biela_px"] * scale
    theta = 2 * math.pi * mov["revolucoes"] * t + fit["fase_rad"]
    dx = r * math.sin(theta)
    y_crank = CY - r * math.cos(theta)
    piston_y = y_crank - math.sqrt(L * L - dx * dx)
    return {
        "theta": theta, "piston_y": piston_y,
        "crank_x": CX + dx, "crank_y": y_crank,
        "rod_distance": math.hypot(dx, y_crank - piston_y),
        "rod_nominal": L,
        "piston_min_y": CY - r - L,
        "piston_max_y": CY + r - L,
    }


def svg_frame(mov: dict, scene: dict, t: float) -> str:
    s = pose(t, mov)
    position = t * mov["quadros"]
    stage = max(i for i, x in enumerate(scene["ciclo"])
                if position >= x["quadro_inicio"])
    beat = scene["ciclo"][stage]
    end = (scene["ciclo"][stage + 1]["quadro_inicio"]
           if stage + 1 < len(scene["ciclo"]) else mov["quadros"])
    phase = (position - beat["quadro_inicio"]) / max(
        1, end - beat["quadro_inicio"])
    is_intake = beat["tipo"] in ("admissao_mistura", "admissao_ar")
    is_compress = beat["tipo"] in ("compressao_mistura", "compressao_ar")
    is_ignition = beat["tipo"] == "ignicao_expansao"
    is_exhaust = beat["tipo"] in ("escape_gases", "descarga_ar")

    crown = s["piston_y"] - 54
    chamber = max(4., crown - 394)
    in_open = 15 if is_intake else 0
    out_open = 15 if is_exhaust else 0
    gas = ("#A3EAE4" if is_intake else
           "#F7CF76" if is_compress else
           "#F3A875" if is_ignition else "#B8C6CB")
    gas_opacity = .38 if is_intake else .68 if is_compress else .76 if is_ignition else .46
    spark = ""
    if is_ignition and phase < .60:
        pulse = math.sin(min(1, phase * 3.5) * math.pi) ** 2
        radius = 12 + 32 * pulse
        spark = f"""<g transform="translate(267 386)">
          <circle r="{radius:.2f}" fill="url(#fire)"
            opacity="{.35 + .45 * pulse:.3f}"/>
          <path d="M -8 -11 L -1 -34 L 5 -8 L 22 -17 L 12 0
            L 34 8 L 9 9 L 15 29 L -2 13 L -20 29
            L -10 5 L -35 -1 L -10 -7 Z" fill="#FF6C32"
            stroke="#D94B2A" stroke-width="3"
            opacity="{.4 + .6 * pulse:.3f}"/>
          <circle r="5" fill="#FFF2C0"/></g>"""
    flow = ""
    if is_intake:
        shift = 15 * (phase % 1)
        flow = f"""<path d="M 76 312 H 163 Q 190 312 200 341 L 209 392"
          fill="none" stroke="#1CA6B6" stroke-width="8"
          stroke-linecap="round" stroke-dasharray="11 23"
          stroke-dashoffset="{-shift:.1f}"/>
          <polygon points="200,385 213,398 222,383" fill="#089CAA"/>"""
    elif is_exhaust:
        shift = 28 * (phase % 1)
        flow = f"""<path d="M 323 393 L 340 331 Q 346 309 375 309 H 485"
          fill="none" stroke="#D77F4B" stroke-width="8"
          stroke-linecap="round" stroke-dasharray="12 20"
          stroke-dashoffset="{-shift:.1f}"/>
          <polygon points="467,298 488,309 467,320" fill="#C16A3D"/>"""
    elif is_compress:
        flow = f"""<g opacity=".75">
          <path d="M 219 {crown-12:.1f} L 219 {crown-38:.1f}
            M 267 {crown-12:.1f} L 267 {crown-36:.1f}
            M 313 {crown-12:.1f} L 313 {crown-38:.1f}"
            stroke="#C77D25" stroke-width="5" stroke-linecap="round"/>
          <path d="M 211 {crown-25:.1f} l 8 -13 l 8 13
            M 259 {crown-24:.1f} l 8 -13 l 8 13
            M 305 {crown-25:.1f} l 8 -13 l 8 13"
            fill="none" stroke="#C77D25" stroke-width="4"/>
          </g>"""

    title = escape(scene.get("titulo", "COMO FUNCIONA")[:31])
    step_title = escape(beat["titulo"].upper())
    explanation = escape(beat["detalhe"][:57])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="540"
      height="960" viewBox="0 0 540 960">
    <defs>
      <linearGradient id="bg" x1="0" x2="0" y1="0" y2="1">
        <stop stop-color="#F9FCFB"/>
        <stop offset="1" stop-color="#DCE9E8"/></linearGradient>
      <linearGradient id="metal" x1="0" x2="1">
        <stop stop-color="#7A96A4"/><stop offset=".17" stop-color="#DFE7EA"/>
        <stop offset=".48" stop-color="#9EB3BE"/>
        <stop offset=".78" stop-color="#E4F2F2"/>
        <stop offset="1" stop-color="#8299A6"/></linearGradient>
      <linearGradient id="piston" x1="0" x2="1">
        <stop stop-color="#5D7B8B"/>
        <stop offset=".15" stop-color="#D7E4E8"/>
        <stop offset=".45" stop-color="#FFFFFF"/>
        <stop offset=".78" stop-color="#BACDD3"/>
        <stop offset="1" stop-color="#63808F"/></linearGradient>
      <linearGradient id="fire" x1="0" x2="0" y1="0" y2="1">
        <stop stop-color="#FFF7B0"/>
        <stop offset=".48" stop-color="#FF922F" stop-opacity=".85"/>
        <stop offset="1" stop-color="#ED502D" stop-opacity="0"/></linearGradient>
      <linearGradient id="copper" x1="0" x2="1">
        <stop stop-color="#805336"/><stop offset=".5" stop-color="#DAB779"/>
        <stop offset="1" stop-color="#845A3A"/></linearGradient>
      <pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse">
        <path d="M 34 0 H 0 V 34" fill="none"
          stroke="#C5D6D8" stroke-width=".7" opacity=".45"/>
      </pattern>
      <filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="6"
        flood-color="#214256" flood-opacity=".22"/></filter>
      <clipPath id="chamber"><rect x="187" y="395"
        width="158" height="290" rx="7"/></clipPath>
    </defs>
    <rect width="540" height="960" fill="url(#bg)"/>
    <rect y="205" width="540" height="755" fill="url(#grid)"/>
    <rect width="540" height="215" fill="#0F2636"/>
    <rect x="42" y="30" width="196" height="26" rx="7" fill="#F1BE55"/>
    <text x="56" y="48" fill="#192E3B" font-size="13" font-weight="900"
      font-family="DejaVu Sans">CORINGA EXPLICA</text>
    <text x="42" y="110" fill="#FFFFFF" font-size="32" font-weight="900"
      font-family="DejaVu Sans">{title}</text>
    <text x="42" y="159" fill="#F5C354" font-size="24" font-weight="900"
      font-family="DejaVu Sans">{step_title}</text>
    <text x="43" y="191" fill="#C4D9E1" font-size="14"
      font-family="DejaVu Sans">{explanation}</text>
    <rect x="42" y="227" width="457" height="6" rx="3" fill="#D2DDE0"/>
    <rect x="42" y="227" width="{int(457*t)}" height="6" rx="3" fill="#0B8198"/>
    <!-- Cutaway: caixa, cabeçote e dutos em geometria INDEPENDENTE do GIF -->
    <g filter="url(#shadow)">
      <path d="M 163 345 L 378 345 L 401 374 L 407 688
        L 432 729 L 432 856 L 110 856 L 110 735 L 135 684 L 135 376 Z"
        fill="#718A9A" stroke="#203B49" stroke-width="9"
        stroke-linejoin="round"/>
      <rect x="139" y="677" width="264" height="172" rx="46"
        fill="#D3E1E4" stroke="#3B5967" stroke-width="8"/>
      <path d="M 133 747 Q 128 708 155 695 H 376 Q 415 715 408 752"
        fill="none" stroke="#FFFFFF" stroke-width="8" opacity=".62"/>
      <rect x="143" y="365" width="253" height="303" rx="19"
        fill="url(#metal)" stroke="#345568" stroke-width="7"/>
      <rect x="174" y="392" width="192" height="300" rx="9"
        fill="#F6FBFB" stroke="#476171" stroke-width="11"/>
      <rect x="185" y="397" width="169" height="290" fill="#E9F2F1"/>
      <path d="M 152 339 L 381 339 L 393 365 L 381 389
        L 153 389 L 141 365 Z" fill="url(#metal)"
        stroke="#345567" stroke-width="8"/>
      <path d="M 159 353 H 376" stroke="#E8F9FA" stroke-width="7"/>
      <rect x="153" y="341" width="233" height="12" rx="4" fill="#4E6D7C"/>
      <path d="M 38 309 H 144 Q 177 309 183 335 L 191 353"
        fill="none" stroke="#435F70" stroke-width="43"
        stroke-linecap="round"/>
      <path d="M 38 309 H 144 Q 177 309 183 335 L 191 353"
        fill="none" stroke="#C5E5E5" stroke-width="27"
        stroke-linecap="round"/>
      <path d="M 341 353 L 352 329 Q 360 309 396 309 H 502"
        fill="none" stroke="#435F70" stroke-width="43"
        stroke-linecap="round"/>
      <path d="M 341 353 L 352 329 Q 360 309 396 309 H 502"
        fill="none" stroke="#D3DFDB" stroke-width="27"
        stroke-linecap="round"/>
      <rect x="152" y="830" width="232" height="35" rx="12"
        fill="#6B8A9C" stroke="#304D60" stroke-width="6"/>
    </g>
    <!-- Volume de gás ligado ao topo real do pistão -->
    <g clip-path="url(#chamber)"><rect x="185" y="394"
      width="169" height="{chamber:.2f}"
      fill="{gas}" opacity="{gas_opacity}"/></g>
    <!-- Válvulas com estados DISCRETOS de processo -->
    <g>
      <rect x="206" y="277" width="12" height="{111+in_open}"
        rx="5" fill="#7A99A9" stroke="#2C4E61" stroke-width="3"/>
      <path d="M 189 {389+in_open}
        Q 213 {377+in_open} 235 {389+in_open}
        L 235 {395+in_open} H 189 Z"
        fill="#4E92A6" stroke="#244858" stroke-width="3"/>
      <rect x="327" y="277" width="12" height="{111+out_open}"
        rx="5" fill="#7A99A9" stroke="#2C4E61" stroke-width="3"/>
      <path d="M 311 {389+out_open}
        Q 334 {377+out_open} 354 {389+out_open}
        L 354 {395+out_open} H 311 Z"
        fill="#DAA06D" stroke="#6D5549" stroke-width="3"/>
      <path d="M 267 306 V 377"
        stroke="#617F90" stroke-width="12" stroke-linecap="round"/>
      <path d="M 267 328 V 372"
        stroke="#E7F5F5" stroke-width="5" stroke-linecap="round"/>
      <path d="M 257 382 L 267 392 L 277 382"
        fill="none" stroke="#9DAEBC" stroke-width="6"/>
    </g>
    {spark}
    <!-- Volante e pino excêntrico acionados pelo MESMO theta -->
    <g transform="translate({CX:.2f} {CY:.2f})
      rotate({s['theta']*180/math.pi:.4f})">
      <circle r="92" fill="#92A7B3" stroke="#344E60" stroke-width="10"/>
      <circle r="75" fill="#D9E5E7" stroke="#5B7C8C" stroke-width="12"/>
      <circle r="54" fill="#829BAA" stroke="#2B4C5C" stroke-width="7"/>
      <path d="M 0 -57 V -82 M 57 0 H 82
        M 0 57 V 82 M -57 0 H -82" stroke="#35576A"
        stroke-width="8" stroke-linecap="round"/>
      <circle r="20" fill="#E6F0F1" stroke="#29485D" stroke-width="7"/>
    </g>
    <line x1="{CX:.3f}" y1="{s['piston_y']:.3f}"
      x2="{s['crank_x']:.3f}" y2="{s['crank_y']:.3f}"
      stroke="#253F4E" stroke-width="35" stroke-linecap="round"/>
    <line x1="{CX:.3f}" y1="{s['piston_y']:.3f}"
      x2="{s['crank_x']:.3f}" y2="{s['crank_y']:.3f}"
      stroke="url(#copper)" stroke-width="25" stroke-linecap="round"/>
    <line x1="{CX:.3f}" y1="{s['piston_y']:.3f}"
      x2="{s['crank_x']:.3f}" y2="{s['crank_y']:.3f}"
      stroke="#EAC99A" opacity=".58" stroke-width="5"/>
    <!-- Pistão é ator ligado ao pino, não outro elemento temporal solto -->
    <g transform="translate(0 {crown:.3f})">
      <rect x="188" y="0" width="158" height="95" rx="15"
        fill="url(#piston)" stroke="#264858" stroke-width="7"/>
      <rect x="189" y="0" width="156" height="20" rx="7"
        fill="#DDE8E9" stroke="#2F5468" stroke-width="4"/>
      <line x1="193" y1="25" x2="341" y2="25"
        stroke="#4F6472" stroke-width="6"/>
      <line x1="193" y1="35" x2="341" y2="35"
        stroke="#4F6472" stroke-width="6"/>
      <path d="M 199 49 L 205 85 M 335 49 L 329 85"
        stroke="#A0BAC2" stroke-width="9"/>
    </g>
    <circle cx="{s['crank_x']:.3f}" cy="{s['crank_y']:.3f}"
      r="25" fill="#2A4355" stroke="#D3E0E3" stroke-width="8"/>
    <circle cx="{s['crank_x']:.3f}" cy="{s['crank_y']:.3f}"
      r="13" fill="#7F9AA8" stroke="#2A4655" stroke-width="4"/>
    <circle cx="{CX:.3f}" cy="{s['piston_y']:.3f}"
      r="22" fill="#B4CAD1" stroke="#2A4655" stroke-width="8"/>
    <circle cx="{CX:.3f}" cy="{s['piston_y']:.3f}"
      r="9" fill="#4E7382" stroke="#2A4655" stroke-width="3"/>
    <path d="M 177 392 V 680 M 359 392 V 680"
      fill="none" stroke="#496676" stroke-width="14"/>
    <path d="M 164 406 V 657 M 373 406 V 657"
      fill="none" stroke="#B8D1D5" stroke-width="8"/>
    {flow}
    <rect x="0" y="919" width="540" height="41" fill="#0F2636"/>
    <text x="26" y="943" fill="#D1DEE2" font-size="12"
      font-family="DejaVu Sans">PROVA 2D PRIVADA · RECONSTRUÇÃO VETORIAL</text>
    <text x="458" y="943" fill="#F1BE55" font-size="12"
      font-weight="900" font-family="DejaVu Sans">
      {stage+1:02d}/0{len(scene['ciclo'])}</text>
  </svg>"""


def renderizar(mov: dict, scene: dict, saida: Path,
               fps: int = 24, duracao: float = 8.) -> dict:
    validar(mov, scene)
    if fps not in (24, 30) or not 4 <= duracao <= 30:
        raise ValueError("F-DURACAO-PRIVADA-INVALIDA")
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pixel_format", "rgb24",
           "-video_size", "540x960", "-framerate", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(saida)]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(round(duracao * fps)):
            svg = svg_frame(mov, scene, i / (duracao * fps))
            png = cairosvg.svg2png(bytestring=svg.encode())
            with Image.open(io.BytesIO(png)) as image:
                frame = image.convert("RGB").tobytes()
            if process.stdin is None:
                raise ValueError("F-FFMPEG-SEM-PIPE")
            process.stdin.write(frame)
    finally:
        if process.stdin is not None:
            process.stdin.close()
    if (process.wait() != 0 or not saida.is_file() or
            saida.stat().st_size < 40_000):
        raise ValueError("F-VIDEO-NAO-RENDERIZADO")
    result = {
        "estado": "PROVA_2D_ORIGINAL_ANIMADA_REVISADA_NAO_AUTOMATICA",
        "origem_sha256": mov["origem_sha256"],
        "processo": scene["processo"],
        "renderizador": "RECONSTRUCAO_2D_CINEMATICA_MEDIDA",
        "publicar": False,
        "proveniencia": "raio/biela/fase ajustados a frames originais, sem copiar pixels",
        "dados_valvulas": "EVENTOS_REVISADOS_MANUALMENTE",
        "arquivo": str(saida),
        "sha256": hashlib.sha256(saida.read_bytes()).hexdigest(),
        "duracao_s": duracao,
        "fps": fps,
        "dimensoes": [WIDTH, HEIGHT],
        "revisao_estetica": "PENDENTE",
    }
    saida.with_suffix(".json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("medicao_json")
    parser.add_argument("cena_json")
    parser.add_argument("saida_mp4")
    args = parser.parse_args()
    motion = json.loads(Path(args.medicao_json).read_text(encoding="utf8"))
    scene = json.loads(Path(args.cena_json).read_text(encoding="utf8"))
    print(json.dumps(renderizar(motion, scene, Path(args.saida_mp4)),
                     ensure_ascii=False))
