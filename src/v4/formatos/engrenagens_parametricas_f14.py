"""F14 — núcleo de engrenagens cilíndricas externas com perfis involutos.

Fórmulas padronizadas de módulo / número de dentes / círculos primitivos,
extraídas somente como CONHECIMENTO técnico (não arte/copiar CAD).
Flancos usam involuta do círculo base, linha de raiz radial aproximada
SEM fillet trocoidal nem tolerância fabril: não certificar fabricação.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from xml.sax.saxutils import escape

ANGLE=math.radians(20)
INV_P=math.tan(ANGLE)-ANGLE
SOURCE="https://khkgears.net/new/gear_knowledge/gear_technical_reference/calculation_gear_dimensions.html"
RIGHTS="PRINCIPIO_MECANICO_NAO_LICENCA_IMAGEM"

def fail(code): raise ValueError("F14-GEAR-"+code)

def num(v,minimum,maximum):
    if type(v) not in (int,float) or not math.isfinite(v) or not minimum<=v<=maximum:
        fail("PARAMETRO")
    return float(v)

def teeth(v):
    if type(v) is not int or not 18<=v<=48:
        fail("DENTES")
    return v

@dataclass(frozen=True)
class Gear:
    z:int
    module:float
    pitch:float
    base:float
    root:float
    tip:float

def gear(z,m):
    z=teeth(z)
    m=num(m,3.0,7.0)
    pitch=z*m/2.
    return Gear(z,m,pitch,pitch*math.cos(ANGLE),pitch-1.25*m,pitch+m)

@dataclass(frozen=True)
class Pair:
    driving:Gear
    driven:Gear
    cx1:float
    cx2:float
    cy:float
    center_distance:float
    ratio:float

def pair(z1,z2,module,cx,cy):
    a,b=gear(z1,module),gear(z2,module)
    x=num(cx,100,235);y=num(cy,350,650)
    spacing=a.pitch+b.pitch
    if spacing<=a.tip+b.root-3 or spacing<=a.root+b.tip-3:
        # Formas involutas precisam engrenar, não dois discos inteiros.
        fail("SEM_ENGRENAMENTO")
    x2=x+spacing
    if x-a.tip<72 or x2+b.tip>480 or y-max(a.tip,b.tip)<305 or y+max(a.tip,b.tip)>740:
        fail("MAQUINA_FORA_PALCO")
    return Pair(a,b,x,x2,y,spacing,b.z/a.z)

def state(p:Pair,t,duration_s,turns=1):
    dur=num(duration_s,7,13); t=num(t,0,dur)
    turns=num(turns,.3,2)
    angle1=2*math.pi*turns*t/dur
    # Escolher engrenagem 1 com dente centrado na linha de centros.
    # A segunda tem o VAO centrado na linha de centros.
    phase2=math.pi+math.pi/p.driven.z
    angle2=phase2-angle1*p.driving.z/p.driven.z
    tangential_error=abs(p.driving.pitch*angle1+p.driven.pitch*(angle2-phase2))
    if tangential_error>1e-7:fail("RAZAO")
    return {
      "driver_angle_rad":angle1,
      "driven_angle_rad":angle2,
      "driver_angle_deg":math.degrees(angle1),
      "driven_angle_deg":math.degrees(angle2),
      "speed_ratio":p.ratio,
      "opposite_rotation":True,
      "pitch_tangential_error":tangential_error,
      "driver_teeth":p.driving.z,"driven_teeth":p.driven.z,
      "center_distance":p.center_distance,
      "elapsed_s":t
    }

def _polar(r,a):
    return (r*math.cos(a),r*math.sin(a))

def outline(g:Gear):
    """Pontos 2D dos dentes involutos, sem raio de filete industrial.

    Espessura na circunferência primitiva = pi*m/2.
    Flanco positivo: angular_half = pi/(2*z)+inv(alpha_ref)-inv(alpha_r)
    Raiz inferior ao círculo base ligada radialmente, de forma DIDÁTICA.
    """
    points=[]
    step=2*math.pi/g.z
    for k in range(g.z):
        center=k*step
        half_base=math.pi/(2*g.z)+INV_P
        # Raiz entre dois dentes, com folga radial e arco curto.
        points.append(_polar(g.root,center-step*.46))
        points.append(_polar(g.root,center-half_base))
        points.append(_polar(g.base,center-half_base))
        for j in range(1,9):
            r=g.base+(g.tip-g.base)*j/8
            alpha=math.acos(g.base/r)
            half=math.pi/(2*g.z)+INV_P-(math.tan(alpha)-alpha)
            if half<=0:fail("PONTA_INVERTIDA")
            points.append(_polar(r,center-half))
        tip_half=math.pi/(2*g.z)+INV_P-(
            math.tan(math.acos(g.base/g.tip))-math.acos(g.base/g.tip))
        points.append(_polar(g.tip,center))
        for j in range(7,-1,-1):
            r=g.base+(g.tip-g.base)*j/8
            alpha=math.acos(g.base/r)
            half=math.pi/(2*g.z)+INV_P-(math.tan(alpha)-alpha)
            points.append(_polar(r,center+half))
        points.append(_polar(g.root,center+half_base))
        points.append(_polar(g.root,center+step*.46))
    return points

def gear_svg(g:Gear,x,y,angle_deg,*,role,color,reflected=False):
    """Uma engrenagem reaproveitável, orgânica SVG, 1 ator por peça."""
    x=num(x,0,540);y=num(y,0,960);a=num(angle_deg,-9999,9999)
    if role not in ("input_gear","output_gear"):fail("ROLE")
    if color not in ("silver","blue"):fail("ACABAMENTO")
    pts=outline(g)
    path="M "+" L ".join(f"{u:.3f} {v:.3f}" for u,v in pts)+" Z"
    fill="url(#f14_silver)" if color=="silver" else "url(#f14_blue)"
    bolts=[]
    for i in range(6):
        ang=2*math.pi*i/6
        rr=max(12,g.root*.51)
        xx,yy=_polar(rr,ang)
        bolts.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="3.3" fill="#BFD8DE" stroke="#244456" stroke-width="1.5"/>')
    flange=max(16,g.root*.30)
    return (
      f'<g id="role-{role}" data-primitive="gear_spur_external" '
      f'data-teeth="{g.z}" data-module="{g.module:g}" '
      'data-profile="involute_no_root_fillet_lab" '
      'data-industrial-identity="PENDENTE" '
      f'transform="translate({x:.3f} {y:.3f}) rotate({a:.5f})">'
      f'<path d="{path}" fill="{fill}" stroke="#203A4A" stroke-width="2.2" stroke-linejoin="round"/>'
      f'<circle r="{g.root*.81:.2f}" fill="none" stroke="#CADDE3" stroke-width="2.6" opacity=".68"/>'
      f'<circle r="{g.pitch:.2f}" fill="none" stroke="#9FD6E4" stroke-width="1.3" '
      'stroke-dasharray="7 7" opacity=".56"/>'
      f'<circle r="{flange:.2f}" fill="#28495D" stroke="#D3E3E9" stroke-width="3"/>'
      f'<circle r="{flange*.58:.2f}" fill="#142E40" stroke="#89AEBE" stroke-width="2"/>'
      + "".join(bolts)+
      f'<path d="M {-flange*.23:.2f} 0 H {flange*.23:.2f} M 0 {-flange*.23:.2f} V {flange*.23:.2f}" stroke="#E8F3F6" stroke-width="2" opacity=".8"/>'
      '</g>'
    )

def svg_actors_check(xml):
    from xml.etree import ElementTree as ET
    try: root=ET.fromstring(xml)
    except ET.ParseError as exc: raise ValueError("F14-GEAR-SVG") from exc
    expected={"role-input_gear","role-output_gear"}
    found=[e.get("id") for e in root.iter() if (e.get("id") or "").startswith("role-")]
    if len(found)!=len(expected) or set(found)!=expected:
        fail("ATOR_DUPLICADO_AUSENTE")
    return True
