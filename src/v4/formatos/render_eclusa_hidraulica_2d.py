"""LAB PRIVADO — eclusa hidráulica grande em 2D, sem desenho legado.

Primitivas reutilizáveis de canal, câmara, portão, conduto, água e embarcação.
A sequência de sete ações deriva do SceneGraph existente; geometria editorial
e mecanismos pertencem a esta família hidráulica, não a um vídeo/episódio.
Vista lateral simplificada, fora de escala: portões de mitra são ilustrados
como uma barreira que fecha/abre, SEM alegar translação real vertical.
Câmera estável com mesmo solver do compressor e Otto; publicação bloqueada.
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

from src.v4.formatos import camera_causal_svg, grafo_causal, realce_causal_svg, biblioteca_componentes_fisicos

WIDTH, HEIGHT = 540, 960
DURATION = 12.6
LOW = 607.0
HIGH = 429.0
FLOOR = 766.0
LEFT_GATE = 147.0
RIGHT_GATE = 396.0
CHAMBER_CENTER = 268.0
PHASES = (
    ("enter", 0.0, 1.65, "NAVIO ENTRA", "O barco chega ao nível inferior.", "#71D9E6"),
    ("seal", 1.65, 2.80, "PORTÃO FECHA", "A câmara fica isolada.", "#F5C267"),
    ("valves", 2.80, 4.0, "VÁLVULA ABRE", "O conduto libera água.", "#77DDE4"),
    ("rise", 4.0, 7.65, "ÁGUA SOBE", "O navio flutua com o nível da água.", "#6BE2E5"),
    ("equalize", 7.65, 8.85, "NÍVEIS IGUAIS", "A água alcança o canal superior.", "#88DAE3"),
    ("open", 8.85, 10.0, "SAÍDA LIBERADA", "O portão superior abre.", "#F4C168"),
    ("exit", 10.0, 12.6, "NAVIO SAI", "O barco segue no nível alto.", "#80D9E3"),
)


def _ease(t: float) -> float:
    p=max(0.,min(1.,t))
    return p*p*(3-2*p)


@dataclass(frozen=True)
class EstadoEclusa:
    tempo: float
    fase: str
    titulo: str
    descricao: str
    cor: str
    fase_indice: int
    fase_fracao: float
    fase_inicio: float
    agua_y: float
    navio_x: float
    navio_y: float
    portao_entrada_fechado: float
    portao_saida_aberto: float
    valvula_aberta: float
    fluxo_ativo: float


def estado(tempo_s:float,duracao:float=DURATION)->EstadoEclusa:
    if (type(tempo_s) not in (int,float) or not math.isfinite(tempo_s) or
        type(duracao) not in (int,float) or not math.isfinite(duracao) or
        duracao<=0 or tempo_s<0 or tempo_s>duracao+1e-8):
        raise ValueError("F-ECLUSA-TEMPO-INVALIDO")
    u=min(DURATION,tempo_s/duracao*DURATION)
    i=next((idx for idx,(_,start,end,*_) in enumerate(PHASES)
            if start<=u<end),len(PHASES)-1)
    action,start,end,title,detail,color=PHASES[i]
    entry=_ease((u-0.07)/1.48)
    seal=_ease((u-1.65)/.98)
    valve=_ease((u-2.80)/.83)
    up=_ease((u-4.0)/3.65)
    opened=_ease((u-8.85)/.94)
    exiting=_ease((u-10.0)/2.48)
    flow=valve*(1-_ease((u-7.65)/.60))
    water=LOW+(HIGH-LOW)*up
    ship_x=83+185*entry+196*exiting
    # Relação hidrostática e flutuação: altura do navio = nível da água.
    return EstadoEclusa(
        tempo_s,action,title,detail,color,i+1,max(0.,min(1.,(u-start)/(end-start))),
        start/DURATION*duracao,water,ship_x,water,
        seal,opened,valve,flow)


def _ship(x:float,y:float)->str:
    """Desenho único do cargueiro; a transformação translada o ator completo."""
    return f'''<g id="role-ship" transform="translate({x:.3f} {y:.3f})">
      <ellipse cx="3" cy="14" rx="54" ry="8" fill="#123E57" opacity=".23"/>
      <path d="M -62 -16 H 66 L 47 16 H -42 Z"
         fill="#F0F6F4" stroke="#254E63" stroke-width="5"/>
      <path d="M -50 4 H 53 L 47 16 H -42 Z" fill="#4B7B91"/>
      <path d="M -54 -21 H 53" stroke="#88B0BD" stroke-width="7"/>
      <rect x="-43" y="-54" width="24" height="33" rx="2" fill="#E2AD6C" stroke="#A8784A" stroke-width="2"/>
      <rect x="-17" y="-54" width="24" height="33" rx="2" fill="#57A4B3" stroke="#397E94" stroke-width="2"/>
      <rect x="9" y="-54" width="24" height="33" rx="2" fill="#C67F61" stroke="#91614D" stroke-width="2"/>
      <rect x="-35" y="-21" width="75" height="5" rx="2" fill="#5F8191"/>
      <rect x="36" y="-69" width="23" height="47" rx="3" fill="#E3F1F1" stroke="#547785" stroke-width="3"/>
      <rect x="40" y="-64" width="16" height="10" rx="2" fill="#4D849B"/>
      <path d="M 47 -70 V -87" stroke="#42677C" stroke-width="3"/>
      <path d="M 41 -85 H 57" stroke="#42677C" stroke-width="2"/>
      <path d="M -38 -8 H 47" stroke="#A7D5DA" stroke-width="2"/>
    </g>'''


def _stage(s:EstadoEclusa, *, realce:bool)->str:
    """Palco técnico único; sem texto editorial e sem transições de câmera."""
    wave=s.agua_y
    shut=s.portao_entrada_fechado
    out=s.portao_saida_aberto
    flowing=s.fluxo_ativo
    highlight=""
    if realce and s.fase in ("valves","rise") and s.valvula_aberta>.001:
        highlight=realce_causal_svg.renderizar(
            "lock_cycle_standalone",s.fase,s.fase_fracao,
            fisica_confirma=s.valvula_aberta>0.001)
    # A linha do conduto coincide com o traçado curado no realce. A água
    # high-side só alcança a câmara por esse conduto após abrir válvula.
    dash=-s.tempo*42
    return f'''<g id="lock-stage">
      <g id="role-lower_channel">
        <path d="M 16 582 H 140 V 778 H 16Z" fill="#547487"/>
        <rect x="17" y="{LOW}" width="{123+17*(1-shut):.2f}" height="{FLOOR-LOW+9}" fill="url(#water)"/>
        <path d="M 19 {LOW:.2f} H {138+20*(1-shut):.2f}" stroke="#D3FFFF" stroke-width="4"/>
        <path d="M 18 594 H 135" stroke="#678D9E" stroke-width="8"/>
      </g>
      <g id="role-upper_channel">
        <path d="M 407 411 H 527 V 778 H 407Z" fill="#577989"/>
        <rect x="{408-17*out:.2f}" y="{HIGH}" width="{121+17*out:.2f}" height="{FLOOR-HIGH+9}" fill="url(#water)"/>
        <path d="M {409-17*out:.2f} {HIGH:.2f} H 528" stroke="#D6FFFF" stroke-width="4"/>
        <path d="M 409 419 H 527" stroke="#91A9B2" stroke-width="8"/>
      </g>
      <!-- Conduto à frente das águas laterais para o fluxo real ser visível.
           Continua ATRÁS da câmara: nenhuma água "mágica" atravessa parede. -->
      <g id="role-conduit">
        <path d="M 461 566 V 809 H 314 V 754" stroke="#294F62" stroke-width="32"
          stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <path d="M 461 566 V 809 H 314 V 754" stroke="#102F45" stroke-width="17"
          stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <path d="M 461 566 V 809 H 314 V 754" stroke="#7BDAE5" stroke-width="8"
          stroke-dasharray="12 21" stroke-dashoffset="{dash:.2f}"
          opacity="{.75*flowing:.3f}" fill="none" stroke-linecap="round"/>
        {highlight}
      </g>
      <g id="role-chamber">
        <rect x="149" y="415" width="244" height="354" rx="6" fill="#E2EEF0"/>
        <path d="M 149 415 H 393 M 149 770 H 393"
          stroke="#4A7082" stroke-width="10"/>
        <!-- A barreira cede em projeção lateral, sem parede fantasma. -->
        <path d="M 149 415 V 770" stroke="#4A7082" stroke-width="9"
          opacity="{shut:.3f}"/>
        <path d="M 393 415 V 770" stroke="#4A7082" stroke-width="9"
          opacity="{1-out:.3f}"/>
        <rect x="158" y="429" width="227" height="327" fill="#31576A"/>
        <g id="role-water">
          <rect x="{158-16*(1-shut):.2f}" y="{wave:.3f}"
            width="{227+16*(1-shut)+20*out:.2f}" height="{FLOOR-wave}"
            fill="url(#water)"/>
          <path d="M {158-16*(1-shut):.2f} {wave:.3f} H {385+20*out:.2f}" stroke="#D5FFFF" stroke-width="5"/>
          <path d="M 174 {wave+26:.2f} h46 M 263 {wave+37:.2f} h52
            M 334 {wave+24:.2f} h36" stroke="#B9F6F4" stroke-width="3"
            opacity=".58"/>
        </g>
        <path d="M 161 758 H 386" stroke="#23485C" stroke-width="14"/>
      </g>
      <path d="M 150 414 V 776" stroke="#264D62" stroke-width="16" opacity="{shut:.3f}"/>
      <path d="M 396 414 V 777" stroke="#264D62" stroke-width="16" opacity="{1-out:.3f}"/>
      <g id="role-inlet_gate">
        <rect x="139" y="421" width="16" height="348" rx="3"
          fill="#DFE8E8" stroke="#668695" stroke-width="3"
          opacity="{.11+.89*shut:.3f}"/>
        <path d="M 147 429 V 756" stroke="#456677" stroke-width="3"
          stroke-dasharray="13 10" opacity="{1-.78*shut:.3f}"/>
      </g>
      <g id="role-outlet_gate">
        <rect x="389" y="421" width="16" height="348" rx="3"
          fill="#DFE8E8" stroke="#668695" stroke-width="3"
          opacity="{.97-.85*out:.3f}"/>
        <path d="M 396 429 V 756" stroke="#4B7186" stroke-width="3"
          stroke-dasharray="13 10" opacity="{.1+.82*out:.3f}"/>
      </g>
      {_ship(s.navio_x,s.navio_y)}
      <g id="role-valve">
        <circle cx="461" cy="800" r="15" fill="#2C5469"
          stroke="{'#F5C368' if s.valvula_aberta>.8 else '#CADFE1'}" stroke-width="4"/>
        <path d="M 451 800 L 471 800" stroke="#F2C97B" stroke-width="4"
          transform="rotate({90*s.valvula_aberta:.2f} 461 800)"/>
      </g>
      <path d="M 160 778 H 388" stroke="#668995" stroke-width="10"/>
    </g>'''


def frame_svg(tempo_s:float,*,duracao:float=DURATION,
              camera_causal:bool=True, realce_causal:bool=True)->str:
    s=estado(tempo_s,duracao)
    # Sempre usar o grafo causal do sistema já existente, não uma lista
    # paralela de eventos soltos escolhidos pelo título do vídeo.
    actions=tuple(e[0] for e in PHASES)
    graph=grafo_causal.montar("lock_cycle_standalone",actions)
    if graph["eventos"][s.fase_indice-1]["acao"]!=s.fase:
        raise ValueError("F-ECLUSA-DIVERGENCIA-GRAFO")
    if camera_causal:
        pose=camera_causal_svg.calcular(
            "lock_cycle_standalone",s.fase,tempo_s,s.fase_inicio,duracao)
        if not camera_causal_svg.verificar_pose("lock_cycle_standalone",pose):
            raise ValueError("F-ECLUSA-CAMERA-CORTE")
        transform=pose.transform_svg(0)
    else:
        transform="translate(0 0)"
    # Cabeçalho e rodapé externos: zoom nunca altera os textos.
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}"
      height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
      <defs>
        <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
          <stop stop-color="#63D7E1"/><stop offset=".2" stop-color="#3999B1"/>
          <stop offset="1" stop-color="#1A577C"/>
        </linearGradient>
        <linearGradient id="body" x1="0" y1="0" x2="0" y2="1">
          <stop stop-color="#F3FAFB"/><stop offset="1" stop-color="#D7EAF0"/>
        </linearGradient>
        <pattern id="grid" width="38" height="38" patternUnits="userSpaceOnUse">
          <path d="M 38 0 H 0 V 38" stroke="#C7DCE5"
            stroke-width=".9" opacity=".62" fill="none"/>
        </pattern>
      </defs>
      <rect width="540" height="960" fill="url(#body)"/>
      <rect x="0" y="215" width="540" height="699" fill="url(#grid)"/>
      <rect width="540" height="205" fill="#112F43"/>
      <rect x="34" y="28" width="165" height="24" rx="6" fill="#FFCC69"/>
      <text x="46" y="45" font-family="DejaVu Sans" font-size="12"
        font-weight="900" fill="#183647">CORINGA EXPLICA</text>
      <text x="34" y="105" font-family="DejaVu Sans" font-size="27"
        font-weight="900" fill="#F9FCFB">ECLUSA HIDRÁULICA</text>
      <text x="34" y="146" font-family="DejaVu Sans" font-size="22"
        font-weight="900" fill="{s.cor}">{escape(s.titulo)}</text>
      <text x="34" y="177" font-family="DejaVu Sans" font-size="14"
        fill="#DAE9EF">{escape(s.descricao)}</text>
      <rect x="34" y="191" width="473" height="5" rx="3" fill="#476578"/>
      <rect x="34" y="191" width="{(s.tempo/duracao)*473:.2f}" height="5"
        rx="3" fill="{s.cor}"/>
      <rect x="35" y="221" width="470" height="38" rx="9" fill="#E1EDF0"
        stroke="#B8D2D9" stroke-width="2"/>
      <text x="52" y="245" font-size="13" font-family="DejaVu Sans"
        font-weight="900" fill="#426478">PRINCÍPIO FÍSICO</text>
      <text x="319" y="245" font-size="13" font-family="DejaVu Sans"
        font-weight="900" fill="#426478">VISTA LATERAL</text>
      <text x="38" y="317" fill="#456B7F" font-size="14"
        font-family="DejaVu Sans" font-weight="900">CANAL BAIXO</text>
      <text x="227" y="317" fill="#355F76" font-size="14"
        font-family="DejaVu Sans" font-weight="900">CÂMARA</text>
      <text x="414" y="317" fill="#456B7F" font-size="13"
        font-family="DejaVu Sans" font-weight="900">CANAL ALTO</text>
      <g id="machine-stage" transform="{transform}">
        {_stage(s,realce=realce_causal)}
      </g>
      <text x="38" y="866" font-size="14" fill="#477081"
        font-family="DejaVu Sans" font-weight="900">NÍVEL BAIXO</text>
      <text x="352" y="866" font-size="14" fill="#477081"
        font-family="DejaVu Sans" font-weight="900">NÍVEL ALTO</text>
      <path d="M 34 902 H 506" stroke="#ABC4CF" stroke-width="2"/>
      <text x="34" y="930" font-size="11.5" fill="#56768A"
        font-family="DejaVu Sans" font-weight="900">PROVA PRIVADA · CORTE ESQUEMÁTICO</text>
      <text x="464" y="930" font-size="13" fill="#456C7E"
        font-family="DejaVu Sans" font-weight="900">{s.fase_indice:02d}/07</text>
    </svg>'''
    return biblioteca_componentes_fisicos.etiquetar_svg("lock_cycle_standalone",svg)


def renderizar(arquivo:Path,*,fps:int=24,duracao:float=DURATION,
              camera_causal:bool=True,realce_causal:bool=True)->dict:
    if fps not in (24,30) or not 10<=duracao<=25:
        raise ValueError("F-ECLUSA-VIDEO-INVALIDO")
    arquivo=Path(arquivo)
    arquivo.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-video_size",
         "540x960","-r",str(fps),"-i","-","-c:v","libx264",
         "-preset","veryfast","-crf","22","-pix_fmt","yuv420p",
         "-movflags","+faststart",str(arquivo)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(round(duracao*fps)):
            svg=frame_svg(i/fps,duracao=duracao,camera_causal=camera_causal,
                          realce_causal=realce_causal)
            png=cairosvg.svg2png(bytestring=svg.encode("utf8"))
            with Image.open(io.BytesIO(png)) as im:
                frame=im.convert("RGB").tobytes()
            if proc.stdin is None:
                raise ValueError("F-ECLUSA-FFMPEG-STDIN")
            proc.stdin.write(frame)
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait()!=0 or not arquivo.is_file() or arquivo.stat().st_size<45_000:
        raise ValueError("F-ECLUSA-VIDEO-INVALIDO")
    out={
        "schema":"hydraulic-lock-reusable-family-v1",
        "status":"LAB_VISUAL_NAO_HOMOLOGADO",
        "processo":"lock_cycle_standalone",
        "origem_fisica":"MESMAS_SETE_ACOES_CAUSAIS_DO_REPOSITÓRIO",
        "geometria":"PRIMITIVAS_2D_HIDRAULICAS_AUTORAIS",
        "estilo":"MECANISMO_GRANDE_FUNDO_CLARO_CONTRASTE",
        "advertencia":"PORTOES_DE_MITRA_SIMPLIFICADOS_NA_LATERAL_FORA_DE_ESCALA",
        "camera":{"ativa":camera_causal,"politica":"plano_geral_travado"},
        "realce":{"ativo":realce_causal,"origem":"grafo_causal + conduto real"},
        "etapas":[{"acao":x[0],"inicio_s":x[1]*duracao/DURATION,
                   "fim_s":x[2]*duracao/DURATION} for x in PHASES],
        "atuadores_3d":False,"reconstrucao_livre_de_tema":False,
        "publicar":False,"telegram":False,"revisao_humana":"PENDENTE",
        "fps":fps,"duracao_s":duracao,"dimensoes":[WIDTH,HEIGHT],
        "sha256":hashlib.sha256(arquivo.read_bytes()).hexdigest()
    }
    arquivo.with_suffix(".json").write_text(json.dumps(
        out,ensure_ascii=False,indent=2),encoding="utf8")
    return out


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("arquivo_mp4")
    parser.add_argument("--fps",type=int,default=24)
    parser.add_argument("--duracao",type=float,default=DURATION)
    parser.add_argument("--sem-realce",action="store_true")
    parser.add_argument("--sem-camera",action="store_true")
    args=parser.parse_args()
    print(json.dumps(renderizar(Path(args.arquivo_mp4),fps=args.fps,
        duracao=args.duracao,camera_causal=not args.sem_camera,
        realce_causal=not args.sem_realce),ensure_ascii=False))
