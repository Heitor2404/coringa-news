"""F6: primitivas SVG paramétricas de mecanismo, sem card ou câmera.

São peças desenháveis e não apenas IDs: mesmo conduto, válvula, barreira,
reservatório e água podem servir a cenas físicas distintas. Geometria
deve ser explícita e validada; nenhuma URL ou SVG externo é importado.
NÃO equivale a modelo 3D, reconstrução por foto ou aprovação estética.
"""
from __future__ import annotations

import math
import re
from xml.sax.saxutils import escape

_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_COLOR = re.compile(r"^#[A-Fa-f0-9]{6}$")
_PATH = re.compile(r"^[MHLVQCZ0-9., +\-]+$")
_ALLOWED = {"conduit", "valve", "gate", "reservoir", "fluid_body"}
_PUBLICATION = False


def _num(value, minimum=None, maximum=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("F-PRIMITIVA-NUMERO")
    v=float(value)
    if minimum is not None and v < minimum:
        raise ValueError("F-PRIMITIVA-LIMITE")
    if maximum is not None and v > maximum:
        raise ValueError("F-PRIMITIVA-LIMITE")
    return v


def _hex(value):
    if not isinstance(value,str) or not _COLOR.fullmatch(value):
        raise ValueError("F-PRIMITIVA-COR")
    return value


def _path(value):
    if (not isinstance(value,str) or len(value)>700 or len(value)<5
            or not value.startswith("M ") or not _PATH.fullmatch(value)):
        raise ValueError("F-PRIMITIVA-TRACADO")
    return escape(value)


def _fmt(v):
    return f"{v:g}"


def conduto(path, *, vazao=0.0, deslocamento=0.0,
            largura=32.0, miolo=17.0, fio=8.0,
            cor_corpo="#294F62", cor_interna="#102F45",
            cor_agua="#7BDAE5"):
    """Traçado de fluido de geometria parametrizada, fluxo zero invisível.

    O contorno NÃO se altera ao mudar o estado hidráulico; muda apenas
    a luminância do traço interno. Nunca inventa novos conectores.
    """
    d=_path(path)
    q=_num(vazao,0,1)
    offset=_num(deslocamento,-100000,100000)
    width=_num(largura,8,80)
    liner=_num(miolo,2,width-2)
    flow=_num(fio,1,liner-1)
    colors=[_hex(x) for x in (cor_corpo,cor_interna,cor_agua)]
    return (
      f'<path d="{d}" stroke="{colors[0]}" stroke-width="{_fmt(width)}" '
      'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
      f'<path d="{d}" stroke="{colors[1]}" stroke-width="{_fmt(liner)}" '
      'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
      f'<path d="{d}" stroke="{colors[2]}" stroke-width="{_fmt(flow)}" '
      f'stroke-dasharray="12 21" stroke-dashoffset="{offset:.2f}" '
      f'opacity="{.75*q:.3f}" fill="none" stroke-linecap="round"/>'
    )


def valvula(x,y,abertura,*,raio=15,
            cor_corpo="#2C5469",cor_ativa="#F5C368",
            cor_inativa="#CADFE1"):
    """Volante de uma válvula genérica: 0=fechada, 1=aberta."""
    x=_num(x,0,540); y=_num(y,0,960); open_=_num(abertura,0,1)
    r=_num(raio,7,40)
    _hex(cor_corpo); _hex(cor_ativa); _hex(cor_inativa)
    return (
      f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(r)}" '
      f'fill="{cor_corpo}" stroke="{cor_ativa if open_>.8 else cor_inativa}" '
      'stroke-width="4"/>'
      f'<path d="M {_fmt(x-10)} {_fmt(y)} L {_fmt(x+10)} {_fmt(y)}" '
      'stroke="#F2C97B" stroke-width="4" '
      f'transform="rotate({90*open_:.2f} {_fmt(x)} {_fmt(y)})"/>'
    )


def barreira(x,topo,base,abertura,*,cor="#264D62",largura=16):
    """Portão em projeção lateral: não representar rotação 3D real."""
    _num(x,0,540);_num(topo,0,960);_num(base,topo+2,960)
    op=_num(abertura,0,1)
    w=_num(largura,2,30);_hex(cor)
    return (f'<path d="M {_fmt(x)} {_fmt(topo)} V {_fmt(base)}" '
            f'stroke="{cor}" stroke-width="{_fmt(w)}" '
            f'opacity="{1-op:.3f}"/>')


def reservatorio(x,y,largura,altura,*,cor="#D9E9EE",borda="#35566D"):
    """Tanque aberto visto em corte (U), não equipamento industrial específico."""
    x=_num(x,0,530);y=_num(y,230,860)
    w=_num(largura,70,290);h=_num(altura,180,510)
    if x+w>540 or y+h>875:
        raise ValueError("F-PRIMITIVA-FORA-PALCO")
    _hex(cor);_hex(borda)
    return (
      f'<rect x="{x+7:.2f}" y="{y+5:.2f}" width="{w-14:.2f}" '
      f'height="{h-10:.2f}" fill="{cor}"/>'
      f'<path d="M {x:.2f} {y:.2f} V {y+h:.2f} H {x+w:.2f} V {y:.2f}" '
      f'fill="none" stroke="{borda}" stroke-width="13" '
      'stroke-linejoin="round" stroke-linecap="round"/>'
      f'<path d="M {x+14:.2f} {y+25:.2f} V {y+h-14:.2f} '
      f'M {x+w-14:.2f} {y+25:.2f} V {y+h-14:.2f}" '
      'stroke="#FFFFFF" stroke-opacity=".58" stroke-width="3" fill="none"/>'
    )


def agua_no_tanque(x,y,largura,base,*,cor="#379BAF",superficie="#C9FAFA"):
    """Volume em 2D: deslocamento da superfície muda a altura do fluido."""
    x=_num(x,0,540);y=_num(y,0,960)
    w=_num(largura,1,540);bottom=_num(base,y+1,960)
    if x+w>540:
        raise ValueError("F-PRIMITIVA-FORA-PALCO")
    _hex(cor);_hex(superficie)
    return (
      f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" '
      f'height="{bottom-y:.2f}" fill="{cor}"/>'
      f'<path d="M {x:.2f} {y:.2f} H {x+w:.2f}" '
      f'stroke="{superficie}" stroke-width="5"/>'
      f'<path d="M {x+12:.2f} {y+22:.2f} H {x+min(w-12,52):.2f}" '
      'stroke="#B2ECED" stroke-width="3" stroke-opacity=".55"/>'
    )




# F7: os três tipos mecânicos também são SVGs realmente desenháveis.
def rotor(cx,cy,raio,angulo_graus,*,corpo="#365A6D",borda="#1B3E4F",raios=5):
    """Polia/volante rotativo parametrizado: a rotação move o grupo inteiro."""
    x=_num(cx,0,540);y=_num(cy,0,960);r=_num(raio,18,110)
    theta=_num(angulo_graus,-1e7,1e7)
    if type(raios) is not int or not 3<=raios<=10:
        raise ValueError("F-PRIMITIVA-ROTOR")
    _hex(corpo);_hex(borda)
    spokes=[]
    for i in range(raios):
        a=2*math.pi*i/raios
        spokes.append(
            f'<line x1="0" y1="0" x2="{r*.78*math.cos(a):.2f}" '
            f'y2="{r*.78*math.sin(a):.2f}" stroke="#C6D9DF" '
            'stroke-width="10" stroke-linecap="round"/>'
        )
    return (f'<g transform="translate({x:.2f} {y:.2f}) rotate({theta:.3f})">'
          f'<circle r="{r:.2f}" fill="{corpo}" stroke="{borda}" stroke-width="7"/>'
          f'<circle r="{r-10:.2f}" fill="#4D7082" stroke="#C4D7DC" stroke-width="5"/>'
          + "".join(spokes)+
          '<circle r="13" fill="#DDE8E9" stroke="#1D4354" stroke-width="5"/></g>')


def pistao(x,y,largura,altura,*,cor="#C3D9E0",borda="#294D63",topo="#E9F4F6"):
    """Corpo sólido, sem biela falsa."""
    x=_num(x,0,540);y=_num(y,0,960)
    w=_num(largura,40,240);h=_num(altura,30,125)
    if x+w>540 or y+h>930:
        raise ValueError("F-PRIMITIVA-PISTAO-FORA")
    for color in (cor,borda,topo):_hex(color)
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" '
       f'height="{h:.2f}" rx="12" fill="{cor}" stroke="{borda}" stroke-width="7"/>'
       f'<rect x="{x+3:.2f}" y="{y+2:.2f}" width="{w-6:.2f}" '
       f'height="16" rx="5" fill="{topo}" opacity=".93"/>'
       f'<path d="M {x+9:.2f} {y+24:.2f} H {x+w-9:.2f} '
       f'M {x+9:.2f} {y+34:.2f} H {x+w-9:.2f}" '
       f'stroke="{borda}" stroke-width="2.6" opacity=".52"/>'
       f'<circle cx="{x+w/2:.2f}" cy="{y+h-19:.2f}" r="10" '
       'fill="#D5E9EC" stroke="#416A7D" stroke-width="3"/>')


def biela(x1,y1,x2,y2,*,largura=21,cor="#D5A76C",
          contorno="#294A5D",reflexo="#F6D7A0"):
    """Biela entre duas juntas reais; nunca articula por texto de roteiro."""
    ax=_num(x1,0,540);ay=_num(y1,0,960)
    bx=_num(x2,0,540);by=_num(y2,0,960)
    w=_num(largura,6,45)
    for color in (cor,contorno,reflexo):_hex(color)
    if math.hypot(ax-bx,ay-by)<10 or math.hypot(ax-bx,ay-by)>650:
        raise ValueError("F-PRIMITIVA-BIELA-DEGENERADA")
    return (f'<line x1="{ax:.3f}" y1="{ay:.3f}" '
        f'x2="{bx:.3f}" y2="{by:.3f}" stroke="{contorno}" '
        f'stroke-width="{w+8:g}" stroke-linecap="round"/>'
        f'<line x1="{ax:.3f}" y1="{ay:.3f}" '
        f'x2="{bx:.3f}" y2="{by:.3f}" stroke="{cor}" '
        f'stroke-width="{w:g}" stroke-linecap="round"/>'
        f'<line x1="{ax:.3f}" y1="{ay:.3f}" '
        f'x2="{bx:.3f}" y2="{by:.3f}" stroke="{reflexo}" '
        'stroke-width="3" opacity=".78"/>'
        f'<circle cx="{bx:.3f}" cy="{by:.3f}" r="10" '
        f'fill="#D8EBED" stroke="{contorno}" stroke-width="4"/>'
        f'<circle cx="{ax:.3f}" cy="{ay:.3f}" r="11" '
        f'fill="#D8EBED" stroke="{contorno}" stroke-width="4"/>')


def transmissao_correia(x1,y1,r1,x2,y2,r2,*,
                        cor="#223F52",filete="#8CAFB9",largura=10):
    """Correia aberta ao longo de tangentes EXTERNAS das duas polias."""
    x1=_num(x1,0,540);y1=_num(y1,0,960)
    x2=_num(x2,0,540);y2=_num(y2,0,960)
    r1=_num(r1,10,110);r2=_num(r2,10,110)
    w=_num(largura,5,20);_hex(cor);_hex(filete)
    dx=x2-x1;dy=y2-y1;d=math.hypot(dx,dy)
    if d<=r1+r2+8:
        raise ValueError("F-PRIMITIVA-CORREIA-SEM-TANGENCIA")
    ux,uy=dx/d,dy/d
    nx,ny=-uy,ux
    cos=(r1-r2)/d
    sine=math.sqrt(1-cos*cos)
    n1=(cos*ux-sine*nx,cos*uy-sine*ny)
    n2=(cos*ux+sine*nx,cos*uy+sine*ny)
    a=(x1+r1*n1[0],y1+r1*n1[1])
    b=(x2+r2*n1[0],y2+r2*n1[1])
    c=(x2+r2*n2[0],y2+r2*n2[1])
    e=(x1+r1*n2[0],y1+r1*n2[1])
    for px,py in (a,b,c,e):
        if px<-6 or py<230 or px>546 or py>905:
            raise ValueError("F-PRIMITIVA-CORREIA-FORA-PALCO")
    path=(f'M {a[0]:.2f} {a[1]:.2f} L {b[0]:.2f} {b[1]:.2f} '
        f'A {r2:.2f} {r2:.2f} 0 0 1 {c[0]:.2f} {c[1]:.2f} '
        f'L {e[0]:.2f} {e[1]:.2f} '
        f'A {r1:.2f} {r1:.2f} 0 0 1 {a[0]:.2f} {a[1]:.2f}')
    return (f'<path d="{path}" fill="none" stroke="{cor}" '
        f'stroke-width="{w:g}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M {a[0]:.2f} {a[1]:.2f} L {b[0]:.2f} {b[1]:.2f}" '
        f'stroke="{filete}" stroke-width="2.5" opacity=".72"/>')


PRIMITIVAS_DESENHAVEIS=frozenset(_ALLOWED | {'rotor','piston','transmission'})


def verificar_reuso():
    """Nenhuma primitive se auto-certifica sem usar o catálogo F5."""
    from src.v4.formatos import biblioteca_componentes_fisicos as B
    if _PUBLICATION or not PRIMITIVAS_DESENHAVEIS.issubset(B.TIPOS_PERMITIDOS):
        raise ValueError("F-PRIMITIVA-SEM-CONTRATO-F5")
    return sorted(PRIMITIVAS_DESENHAVEIS)
