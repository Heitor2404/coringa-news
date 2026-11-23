"""LAB privado — compressor de oficina completo em corte, render vetorial.

SUBTIPO explícito: compressor alternativo de ar com motor elétrico,
correia e reservatório horizontal. Componente da FAMÍLIA, não episódio.
Reaproveita o core físico P-V e exige identidade visual no manifesto.
Não interpreta pixels de referência nem promove vídeo à produção.

Licença de qualquer referência EXTERNA não é transferida à geometria autoral.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import cairosvg
from PIL import Image

from src.v4.formatos.compressor_pv_core import (
    CompressorSpec, estado, limites_fases,
)
from src.v4.formatos.identidade_visual_maquina import verificar as verificar_identidade
from src.v4.formatos.palco_vertical import CaixaVisivel, PalcoVertical
from src.v4.formatos import camera_causal_svg, temporizacao_causal, realce_causal_svg

WIDTH, HEIGHT = 540, 960
CONFIG_ID = "compressor_ar_eletrico_tanque_horizontal_correia"
MANIFESTO_PADRAO = (
    Path(__file__).resolve().parents[3] /
    "docs/v4/formatos/reference_first/"
    "identidade_compressor_oficina_tanque_horizontal.json"
)
FASES = {
    "REEXPANSAO_RESIDUAL": ("AR RESIDUAL EXPANDE",
                           "A pressao diminui antes da entrada.", "#8CD4DF"),
    "ADMISSAO_AR": ("ADMISSÃO",
                    "O filtro recebe ar do ambiente.", "#6CE0DE"),
    "COMPRESSAO_AR": ("COMPRESSÃO",
                      "O volume diminui; as válvulas fecham.", "#F7C56D"),
    "DESCARGA_PRESSURIZADA": ("DESCARGA",
                              "Ar pressurizado vai para o tanque.", "#FFAD72"),
}


@dataclass(frozen=True)
class EditorialHeader:
    """Layout editorial superior reutilizável na família de mecanismos."""
    header_height: int = 202
    title_y: int = 108
    phase_y: int = 148
    detail_y: int = 180
    progress_y: int = 190
    category_y: int = 205
    category_height: int = 30
    category_label_y: int = 225

    def palco(self) -> PalcoVertical:
        # Caixa conservadora curada do desenho: inclui texto FILTRO,
        # manômetro, pés e reservatório. Não é segmentação automática.
        return PalcoVertical(
            largura=WIDTH, altura=HEIGHT,
            caixa=CaixaVisivel(51, 342, 492, 900),
            editorial_termina_y=self.category_y + self.category_height,
            rodape_comeca_y=905, folga_superior=7,
        )

    def max_mechanism_lift_px(self) -> float:
        return self.palco().deslocar()


@dataclass(frozen=True)
class AssemblyLayout:
    # Metadados geográficos e físicos internos desta família, sem ajustes por episódio.
    center_x: float = 294.0
    shaft_y: float = 705.0
    crank_radius: float = 42.0
    connecting_rod: float = 135.0
    tank_left: float = 56.0
    tank_top: float = 774.0
    tank_width: float = 427.0
    tank_height: float = 111.0
    motor_x: float = 141.0
    motor_y: float = 675.0
    pump_wheel_radius: float = 65.0
    motor_pulley_radius: float = 29.0
    # Sobe o conjunto COMPLETO, sem mudar o P-V, escala ou textos seguros.
    # O palco compacto permite subir TUDO, sem alterar física ou escala.
    mechanism_lift_px: float = 100.0

    def spec(self, base: CompressorSpec | None = None) -> CompressorSpec:
        cfg = base or CompressorSpec()
        return CompressorSpec(
            raio=self.crank_radius, biela=self.connecting_rod,
            eixo_y=self.shaft_y, eixo_x=self.center_x,
            folga_relativa=cfg.folga_relativa,
            pressao_saida_relativa=cfg.pressao_saida_relativa,
            expoente_politropico=cfg.expoente_politropico,
        )


def validar_plano(manifesto: dict) -> None:
    if (not isinstance(manifesto, dict) or
            manifesto.get("configuracao") != CONFIG_ID or
            manifesto.get("processo") != "compressor_alternativo" or
            manifesto.get("publicar") is not False):
        raise ValueError("F-CONFIGURACAO-INCORRETA")
    resultado = verificar_identidade(manifesto)
    if resultado["gate"] != "ESTRUTURA_DECLARADA_OK_VISUAL_NAO_CERTIFICADO":
        raise ValueError("F-IDENTIDADE-MAQUINA-" + ",".join(resultado["erros"]))
    if manifesto.get("validacao_visao") != "PENDENTE":
        raise ValueError("F-VISAO-NAO-AUDITADA")
    # NÃO converter gate do manifesto em aprovação estética.


def _spokes(x: float, y: float, radius: float, angle_deg: float, *,
            body: str, stroke: str, count: int = 5) -> str:
    spokes = []
    for i in range(count):
        radians = 2 * math.pi * i / count
        spokes.append(
            f'<line x1="0" y1="0" x2="{radius*.78*math.cos(radians):.2f}" '
            f'y2="{radius*.78*math.sin(radians):.2f}" stroke="#C6D9DF" '
            'stroke-width="10" stroke-linecap="round"/>'
        )
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) rotate({angle_deg:.3f})">'
        f'<circle r="{radius:.2f}" fill="{body}" stroke="{stroke}" stroke-width="7"/>'
        f'<circle r="{radius-10:.2f}" fill="#4D7082" stroke="#C4D7DC" stroke-width="5"/>'
        + "".join(spokes) +
        '<circle r="13" fill="#DDE8E9" stroke="#1D4354" stroke-width="5"/></g>'
    )


def frame_svg(progress: float, manifest: dict, *,
              layout: AssemblyLayout = AssemblyLayout(),
              physics: CompressorSpec | None = None,
              editorial: EditorialHeader = EditorialHeader(),
              camera_causal: bool = False,
              realce_causal: bool = False,
              tempo_s: float | None = None,
              inicio_fase_s: float | None = None,
              duracao_s: float = 8.) -> str:
    validar_plano(manifest)
    try:
        editorial.palco().deslocar(layout.mechanism_lift_px)
    except ValueError as exc:
        raise ValueError("F-LAYOUT-LIFT-AREA-SEGURA") from exc
    s = estado(progress, layout.spec(physics))
    phase, detail, accent = FASES[s.estado]
    chamber_top = 416.0
    piston_top = s.pistao_y - 41.0
    chamber_h = max(2., min(190., piston_top - chamber_top))
    pressure_norm = (
        (s.pressao_relativa - 1) / (layout.spec(physics).pressao_saida_relativa - 1)
    )
    pressure_norm = max(0., min(1., pressure_norm))
    phase_index = list(FASES).index(s.estado) + 1
    # Sucção e descarga são redes separadas e não se confundem com ciclo Otto.
    intake_y = 14 if s.admissao_aberta else 0
    out_y = -14 if s.descarga_aberta else 0
    x, cy = layout.center_x, layout.shaft_y
    shaft_angle = math.degrees(s.angulo)
    motor_angle = shaft_angle * (
        layout.pump_wheel_radius / layout.motor_pulley_radius
    )
    gas_color = (
        "#7DD1D9" if s.admissao_aberta else
        "#F2D17F" if s.estado == "COMPRESSAO_AR" else
        "#F2A978" if s.descarga_aberta else "#97D1D7"
    )
    # Peças reutilizáveis (papéis idênticos ao manifesto de identidade).
    motor_rotor = _spokes(
        layout.motor_x, layout.motor_y, layout.motor_pulley_radius,
        motor_angle, body="#365A6D", stroke="#1B3E4F", count=4)
    wheel = _spokes(
        x, cy, layout.pump_wheel_radius, shaft_angle,
        body="#2F5164", stroke="#18384A")
    belt = (
        '<g id="role-drive_belt">'
        '<path d="M 142 646 L 278 643 A 65 65 0 1 1 278 771 '
        'L 142 704 A 29 29 0 0 1 142 646" '
        'fill="none" stroke="#1E394A" stroke-width="12" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M 142 647 L 278 645" stroke="#71919F" stroke-width="3"/>'
        '</g>'
    )
    filt_particles = ""
    if s.admissao_aberta:
        for i in range(5):
            px = 132 + (i * 13 + progress * 52) % 70
            filt_particles += (
                f'<circle cx="{px:.1f}" cy="381" r="4" fill="#48CFD0"/>'
            )
    discharge_particles = ""
    if s.descarga_aberta:
        for i in range(7):
            phase_pos = (i / 7 + progress * 2.8) % 1
            if phase_pos < .3:
                px, py = 354 + phase_pos / .3 * 90, 390
            elif phase_pos < .85:
                px, py = 444, 390 + (phase_pos - .3) / .55 * 356
            else:
                px, py = 444, 746 + (phase_pos - .85) / .15 * 36
            discharge_particles += (
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" '
                'fill="#FFAF73" opacity=".9"/>'
            )
    vents = "".join(
        f'<rect x="{p}" y="598" width="7" height="101" rx="3" '
        'fill="#7293A3"/>' for p in (94, 111, 128, 145, 162, 179)
    )
    fins = "".join(
        f'<rect x="220" y="{448+i*16}" width="153" height="9" rx="4" '
        'fill="#3B6175" stroke="#99B6C3" stroke-width="2"/>'
        for i in range(11)
    )
    sparks = ""  # COMPRESSOR, NÃO há vela/faísca no processo.
    # A ação física real determina os alvos; o grafo causal determina o foco.
    # A câmera transforma toda a máquina e NUNCA move biela/válvula sozinha.
    stage_transform=f"translate(0 {-layout.mechanism_lift_px:.1f})"
    if camera_causal:
        if (abs(layout.mechanism_lift_px -
                camera_causal_svg.CAMERAS["familias"]["compressor_oficina_pv"]["subida_base_px"])>1e-6):
            raise ValueError("F-CAMERA-BASE-NAO-HOMOLOGADA")
        if tempo_s is None:
            tempo_s=progress*duracao_s
        if inicio_fase_s is None:
            inicio_fase_s=(limites_fases(layout.spec(physics))[s.estado]["de"]*duracao_s)
        camera=camera_causal_svg.calcular(
            "compressor_oficina_pv",s.estado,tempo_s,inicio_fase_s,duracao_s)
        if not camera_causal_svg.verificar_pose("compressor_oficina_pv",camera):
            raise ValueError("F-CAMERA-CORTE-MAQUINA")
        stage_transform=camera.transform_svg(layout.mechanism_lift_px)
    realce_svg=""
    if realce_causal:
        phase_limits=limites_fases(layout.spec(physics))[s.estado]
        relative=(progress-phase_limits["de"])/max(.0001,phase_limits["ate"]-phase_limits["de"])
        realce_svg=realce_causal_svg.renderizar(
            "compressor_oficina_pv",s.estado,max(0.,min(1.,relative)),
            dinamicos={"piston_cutaway":(252.,piston_top,86.,60.)},
            fisica_confirma=(s.admissao_aberta if s.estado=="ADMISSAO_AR"
                             else s.descarga_aberta if s.estado=="DESCARGA_PRESSURIZADA"
                             else True))
    # Cuidado: header e rodapé não sofrem translação da máquina.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="540" height="960"
      viewBox="0 0 540 960">
    <defs>
      <linearGradient id="bg" x1="0" x2="0" y1="0" y2="1">
        <stop stop-color="#F4FBFD"/><stop offset="1" stop-color="#D5E8EE"/>
      </linearGradient>
      <linearGradient id="tank" x1="0" x2="1" y1="0" y2="0">
        <stop stop-color="#184D6B"/><stop offset=".2" stop-color="#5B96AF"/>
        <stop offset=".5" stop-color="#91C4D0"/><stop offset=".82" stop-color="#3F7895"/>
        <stop offset="1" stop-color="#164963"/>
      </linearGradient>
      <linearGradient id="steel" x1="0" x2="1" y1="0" y2="0">
        <stop stop-color="#496A80"/><stop offset=".2" stop-color="#B6CED6"/>
        <stop offset=".5" stop-color="#E7F1F2"/><stop offset=".83" stop-color="#93B2C0"/>
        <stop offset="1" stop-color="#476A7C"/>
      </linearGradient>
      <clipPath id="gasclip"><rect x="242" y="415" width="104" height="181" rx="7"/></clipPath>
      <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">
        <path d="M 36 0 H 0 V 36" fill="none" stroke="#C9DBE1" stroke-width=".8"/>
      </pattern>
    </defs>
    <rect width="540" height="960" fill="url(#bg)"/>
    <rect x="0" y="{editorial.header_height}" width="540" height="{914-editorial.header_height}" fill="url(#grid)"/>
    <rect width="540" height="{editorial.header_height}" fill="#122E43"/>
    <rect x="42" y="28" width="157" height="22" rx="5" fill="#FFCE67"/>
    <text x="53" y="44" font-family="DejaVu Sans" font-size="12"
      font-weight="900" fill="#152D3D">CORINGA EXPLICA</text>
    <text x="42" y="{editorial.title_y}" font-family="DejaVu Sans" font-size="27"
      font-weight="900" fill="white">COMPRESSOR DE AR</text>
    <text x="42" y="{editorial.phase_y}" font-family="DejaVu Sans" font-size="22"
      font-weight="900" fill="{accent}">{escape(phase)}</text>
    <text x="42" y="{editorial.detail_y}" font-family="DejaVu Sans" font-size="14"
      fill="#D5E8F0">{escape(detail)}</text>
    <rect x="42" y="{editorial.progress_y}" width="456" height="6" rx="3" fill="#4E6C7E"/>
    <rect x="42" y="{editorial.progress_y}" width="{int(progress*456)}" height="6" rx="3"
      fill="{accent}"/>
    <rect x="44" y="{editorial.category_y}" width="451" height="{editorial.category_height}" rx="10"
      fill="#E6F1F3" stroke="#A8C8D1" stroke-width="1.8"/>
    <text x="56" y="{editorial.category_label_y}" font-family="DejaVu Sans" font-size="13"
      font-weight="900" fill="#426478">MOTOR ELÉTRICO</text>
    <text x="258" y="{editorial.category_label_y}" font-family="DejaVu Sans" font-size="13"
      font-weight="900" fill="#426478">BOMBA EM CORTE</text>

    <!-- Cena física única. Pistão, motor, tanque, partículas, pressão e
         conduítes se movem juntos em Y. NÃO reposicionar peças isoladas. -->
    <g id="machine-assembly" transform="{stage_transform}">
    <!-- O reservatório é a MAIOR peça. Um compressor de oficina reconhecível. -->
    <g id="role-receiver_horizontal">
      <rect x="{layout.tank_left:.1f}" y="{layout.tank_top:.1f}"
        width="{layout.tank_width:.1f}" height="{layout.tank_height:.1f}"
        rx="55" fill="url(#tank)" stroke="#1B4C64" stroke-width="8"/>
      <path d="M 94 800 C 157 774 376 774 448 801" stroke="#B5DBE1"
        opacity=".45" stroke-width="12" fill="none" stroke-linecap="round"/>
      <rect x="100" y="875" width="58" height="25" rx="9" fill="#3D6476"/>
      <rect x="391" y="875" width="56" height="25" rx="9" fill="#3D6476"/>
      <text x="157" y="843" font-family="DejaVu Sans" font-size="24"
        font-weight="900" fill="#E4F9FC">RESERVATÓRIO</text>
      <text x="184" y="863" font-family="DejaVu Sans" font-size="13"
        font-weight="900" fill="#BCDCE3">AR COMPRIMIDO</text>
    </g>

    <!-- Base do motor + suportes montados acima do tanque -->
    <rect x="85" y="741" width="376" height="30" rx="11"
      fill="#678C9E" stroke="#294C5E" stroke-width="5"/>
    <path d="M 123 740 V 750 M 366 740 V 750" stroke="#244B60" stroke-width="15"/>
    <g id="role-electric_motor">
      <rect x="70" y="602" width="122" height="136" rx="25"
        fill="#547A90" stroke="#24495C" stroke-width="7"/>
      <rect x="80" y="603" width="101" height="130" rx="20"
        fill="#89ABB9" stroke="#476D7F" stroke-width="4"/>
      {vents}
      <rect x="88" y="594" width="88" height="17" rx="7" fill="#305B6F"/>
    </g>

    <!-- Corpo de bomba com aletas: a janela deixa ver o pistão, não é
         um segundo motor Otto fora do conjunto. -->
    <g id="role-crankcase">
      <path d="M 212 623 H 378 L 389 645 V 743 H 201 V 646 Z"
        fill="#365E73" stroke="#22475D" stroke-width="7"/>
      <rect x="220" y="644" width="160" height="89" rx="23"
        fill="#A1BDC7" stroke="#22495D" stroke-width="7"/>
    </g>
    <g id="role-finned_cylinder">
      <rect x="223" y="436" width="141" height="185" rx="18"
        fill="#47758A" stroke="#294C61" stroke-width="9"/>
      {fins}
      <rect x="236" y="439" width="116" height="184" rx="8"
        fill="#244D62" stroke="#A3C2CB" stroke-width="6"/>
      <rect x="243" y="444" width="104" height="172" rx="5"
        fill="#D1E6E8" stroke="#527C91" stroke-width="5"/>
      <g clip-path="url(#gasclip)">
        <rect x="244" y="{chamber_top:.2f}" width="103"
          height="{chamber_h:.2f}" fill="{gas_color}" opacity=".78"/>
      </g>
    </g>
    <g id="role-compressor_head">
      <rect x="231" y="379" width="119" height="57" rx="10"
        fill="url(#steel)" stroke="#34556A" stroke-width="8"/>
      <rect x="235" y="371" width="110" height="17" rx="6"
        fill="#5F7F8F" stroke="#2E4F63" stroke-width="4"/>
    </g>
    <g id="role-intake_filter">
      <rect x="152" y="371" width="56" height="55" rx="10"
        fill="#244D60" stroke="#163849" stroke-width="5"/>
      <path d="M 163 381 V 415 M 175 381 V 415 M 186 381 V 415"
        stroke="#7699A9" stroke-width="6"/>
      <path d="M 207 397 H 230 Q 240 397 242 415"
        stroke="#557E90" stroke-width="16" fill="none"/>
      {filt_particles}
      <text x="150" y="354" fill="#3D6174" font-family="DejaVu Sans"
        font-size="12" font-weight="900">FILTRO</text>
    </g>
    <g id="role-discharge_pipe">
      <path d="M 343 404 H 441 V 778" stroke="#30586D" stroke-width="19"
        fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M 343 404 H 441 V 778" stroke="#F2C596" stroke-width="12"
        fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      {discharge_particles}
      <text x="401" y="384" fill="#AC6842" font-family="DejaVu Sans"
        font-size="12" font-weight="900">SAÍDA</text>
    </g>
    <g id="role-suction_valve">
      <path d="M 264 392 V 418" stroke="#668C9E" stroke-width="7"/>
      <path d="M 254 {420+intake_y} H 273" stroke="#207E91"
        stroke-width="8" stroke-linecap="round"/>
    </g>
    <g id="role-discharge_valve">
      <path d="M 320 391 V 418" stroke="#668C9E" stroke-width="7"/>
      <path d="M 309 {420+out_y} H 331" stroke="#C68151"
        stroke-width="8" stroke-linecap="round"/>
    </g>
    <g id="role-piston_cutaway">
      <rect x="252" y="{piston_top:.3f}" width="86" height="60" rx="11"
        fill="url(#steel)" stroke="#345A6F" stroke-width="6"/>
      <rect x="252" y="{piston_top:.3f}" width="86" height="16" rx="4"
        fill="#DEEDF1" stroke="#4A7485" stroke-width="3"/>
      <circle cx="{x:.3f}" cy="{s.pistao_y:.3f}" r="12"
        fill="#D6E6E8" stroke="#294C60" stroke-width="5"/>
      <line x1="{x:.3f}" y1="{s.pistao_y:.3f}"
        x2="{s.crank_x:.3f}" y2="{s.crank_y:.3f}"
        stroke="#233F53" stroke-width="21" stroke-linecap="round"/>
      <line x1="{x:.3f}" y1="{s.pistao_y:.3f}"
        x2="{s.crank_x:.3f}" y2="{s.crank_y:.3f}"
        stroke="#D9A567" stroke-width="14" stroke-linecap="round"/>
    </g>
    <g id="role-pump_flywheel">{wheel}</g>
    <g id="role-motor_pulley">{motor_rotor}</g>
    {belt}
    <g id="role-receiver_gauge">
      <circle cx="466" cy="719" r="26" fill="#F5FBFD"
        stroke="#31596C" stroke-width="6"/>
      <path d="M 466 719 l 8 -15" stroke="#B56946"
        stroke-width="4" stroke-linecap="round"/>
      <circle cx="466" cy="719" r="4" fill="#466878"/>
    </g>
    <g id="role-check_valve">
      <rect x="438" y="760" width="16" height="22" rx="5"
        fill="#EDB277" stroke="#3B5D6C" stroke-width="3"/>
    </g>
    <g id="pressure_card">
      <rect x="51" y="506" width="142" height="72" rx="12"
        fill="#17384B"/>
      <text x="64" y="532" fill="#C4DFE7" font-family="DejaVu Sans"
        font-size="12" font-weight="900">PRESSÃO CÂMARA</text>
      <text x="64" y="564" fill="{accent}" font-family="DejaVu Sans"
        font-size="27" font-weight="900">{s.pressao_relativa:.1f}×</text>
    </g>
    {realce_svg}
    </g>
    <path d="M 52 905 H 488" stroke="#ADC7D0" stroke-width="2"/>
    <text x="43" y="932" fill="#496A7C" font-family="DejaVu Sans"
      font-size="12" font-weight="900">PROVA PRIVADA · BOMBA E RESERVATÓRIO</text>
    <text x="445" y="932" fill="#496A7C" font-family="DejaVu Sans"
      font-size="12">{phase_index:02d}/04</text>
    {sparks}
  </svg>'''


def renderizar(arquivo: Path, manifest: dict, *,
              layout: AssemblyLayout = AssemblyLayout(),
              physics: CompressorSpec | None = None,
              fps: int = 24, duration: float = 8.,
              camera_causal: bool = False,
              realce_causal: bool = False) -> dict:
    validar_plano(manifest)
    if fps not in (24, 30) or not 5 <= duration <= 20:
        raise ValueError("F-DURACAO-OU-FPS")
    # Ritmo didático só no modo novo: piso por fase, física P-V intacta.
    fisicos=limites_fases(layout.spec(physics))
    trilha=(temporizacao_causal.distribuir(fisicos,duration,1.15)
            if camera_causal else None)
    arquivo = Path(arquivo)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24",
        "-video_size", "540x960", "-framerate", str(fps), "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(arquivo),
    ]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for i in range(int(duration * fps)):
            clock=i/fps
            if trilha:
                phys,action,from_s=temporizacao_causal.mapear(clock,trilha)
                svg=frame_svg(phys,manifest,layout=layout,physics=physics,
                    camera_causal=True,realce_causal=realce_causal,
                    tempo_s=clock,inicio_fase_s=from_s,duracao_s=duration)
            else:
                svg=frame_svg(i/(duration*fps),manifest,layout=layout,physics=physics,
                              realce_causal=realce_causal)
            pixels = cairosvg.svg2png(bytestring=svg.encode())
            with Image.open(io.BytesIO(pixels)) as im:
                content = im.convert("RGB").tobytes()
            if proc.stdin is None:
                raise ValueError("F-FFMPEG-STDIN")
            proc.stdin.write(content)
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait() != 0 or not arquivo.is_file() or arquivo.stat().st_size < 40000:
        raise ValueError("F-FFMPEG-RENDER")
    report = {
        "schema": "compressor-assembly-lab-v1",
        "estado": "RENDER_DE_CONJUNTO_PRIVADO_NAO_REFERENCE_FIRST_AUTOMATICO",
        "configuracao": CONFIG_ID,
        "processo": "compressor_alternativo",
        "publicar": False,
        "origem": "DIRECAO_VETORIAL_PROPRIA_E_FISICA_PV",
        "referencia_3d_importada": False,
        "atores_identificados_por_visao": False,
        "identidade_por_pixels_aprovada": False,
        "revisao_estetica": "PENDENTE",
        "realce_causal": {
            "habilitado":realce_causal,
            "tipo":"TRAJETOS_FISICOS_E_CONTORNO_DE_PECA_MOVEL",
            "aprovacao_humana":"PENDENTE",
        },
        "camera_causal": {
            "habilitada": camera_causal,
            "origem": "grafo_causal.eventos.camera.alvos",
            "geometria": "CAIXAS_CURADAS_POR_RENDERER_SEM_VISAO_AUTOMATICA",
            "motor_reutilizavel": "camera_causal_svg_v2_travada",
            "politica_camera": ("PLANO_GERAL_TRAVADO_SEM_PAN_OU_ZOOM"
                               if camera_causal else "DESLIGADA"),
            "tempo_uniforme": not camera_causal,
            "fases_video": trilha,
            "aprovacao_humana": "PENDENTE",
        },
        "layout": {
            "conjunto_subida_px": layout.mechanism_lift_px,
            "escala_inalterada": not camera_causal,
            "proporcoes_e_fisica_inalteradas": True,
            "zoom_maximo_da_camera": (camera_causal_svg.CAMERAS["familias"]["compressor_oficina_pv"]["zoom_max"] if camera_causal else 1.0),
            "cabecalho_reorganizado": True,
            "cabecalho_altura_px": EditorialHeader().header_height,
            "faixa_categoria_termina_y": EditorialHeader().category_y + EditorialHeader().category_height,
            "rodape_preservado": True,
        },
        "fps": fps, "duracao_s": duration, "dimensoes": [WIDTH, HEIGHT],
        "fases": limites_fases(layout.spec(physics)),
        "sha256_video": hashlib.sha256(arquivo.read_bytes()).hexdigest(),
    }
    arquivo.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="LAB Compressor de oficina 2D")
    p.add_argument("output_mp4")
    p.add_argument("--manifesto", default=str(MANIFESTO_PADRAO))
    p.add_argument("--duracao", type=float, default=8.0)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--camera-causal",action="store_true",help="LAB privado: câmera por atores e retiming de fases")
    p.add_argument("--realce-causal",action="store_true",help="LAB privado: realce sem câmera móvel ou cards")
    args = p.parse_args(argv)
    manifest = json.loads(Path(args.manifesto).read_text(encoding="utf8"))
    result = renderizar(Path(args.output_mp4), manifest, fps=args.fps,
                        duration=args.duracao,camera_causal=args.camera_causal,
                        realce_causal=args.realce_causal)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
