"""F13 — texto ESSENCIAL no bolso lateral livre do mecanismo F12.

Os resultados F11/F12 indicaram o erro de aproximar diretriz de ANÚNCIO
como se fosse sobreposição visível de vídeo orgânico. O novo layout mantém
a pose/escala HERO da F12 e reposiciona somente título, fase e explicação,
abaixo das abas orgânicas observadas, numa coluna que não intercepta o
cilindro. As fontes externas são apenas evidência de UI, não assets.
"""
from __future__ import annotations

from xml.etree import ElementTree as ET
from PIL import ImageFont

NS="{http://www.w3.org/2000/svg}"
X=35
WIDTH=169
TITLE_Y=160
TITLE_STEP=24
PHASE_Y=222
DETAIL_Y=246
DETAIL_STEP=17
MAX_Y=298

def _fail(name):
    raise ValueError("F13-HOOK-"+name)

def _font(size:int,bold=False):
    return ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
         if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",size)

def _wrap(value,width,size,bold,maximum):
    if not isinstance(value,str) or len(value)<5 or len(value)>85:
        _fail("TEXTO_INVALIDO")
    font=_font(size,bold)
    words=value.split()
    if not words:
        _fail("TEXTO_VAZIO")
    lines=[]
    current=""
    for word in words:
        option=(current+" "+word).strip()
        if font.getlength(option)>width:
            if not current:
                _fail("PALAVRA_MAIOR_QUE_BOLSO")
            lines.append(current)
            current=word
        else:
            current=option
    if current: lines.append(current)
    if len(lines)>maximum or any(font.getlength(line)>width for line in lines):
        _fail("LINHAS_NAO_CABEM")
    return lines

def _find(root,x,y):
    matches=[n for n in root if n.tag==NS+"text"
             and n.get("x")==str(x) and n.get("y")==str(y)]
    if len(matches)!=1: _fail("EVIDENCIA_F12_AUSENTE")
    return matches[0]

def _node(parent,ident,lines,*,size,color,y,spacing,strong):
    elt=ET.SubElement(parent,NS+"text",{
        "id":ident,"x":str(X),"y":str(y),"font-family":"DejaVu Sans",
        "font-size":str(size),"fill":color,
        "font-weight":"900" if strong else "500"
    })
    for i,line in enumerate(lines):
        t=ET.SubElement(elt,NS+"tspan",{
            "x":str(X),"y":str(y+i*spacing)})
        t.text=line
    return elt

def aplicar(svg:str)->tuple[str,dict]:
    try: root=ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError("F13-HOOK-SVG") from exc
    if root.get("data-layout")!="hero_elevado_f12":
        _fail("EXIGE_F12")
    if root.find(f"./{NS}g[@id='f13-essential-pocket']") is not None:
        _fail("APLICADO_DUAS_VEZES")
    stage=root.find(f"./{NS}g[@id='machine-stage']")
    if stage is None or not stage.get("data-layout-lift-px"):
        _fail("MECANICA_AUSENTE")
    title=_find(root,34,59)
    phase=_find(root,35,88)
    detail=_find(root,35,107)
    subtitle=_find(root,35,121)
    t=title.text or ""
    p=phase.text or ""
    d=detail.text or ""
    title_lines=_wrap(t,WIDTH,21,True,2)
    phase_lines=_wrap(p,WIDTH,16,True,1)
    detail_lines=_wrap(d,WIDTH,11,False,3)
    if DETAIL_Y+(len(detail_lines)-1)*DETAIL_STEP>MAX_Y:
        _fail("TEXTO_SAIU_AREA")
    # F13b: o topo escuro da F12 ficava 134px com quase nenhum conteúdo
    # essencial (encoberto pela UI). Reduzir a faixa sem tocar no palco físico.
    header=[node for node in root if node.tag==NS+"rect"
            and node.get("width")=="540" and node.get("height")=="134"]
    grid=[node for node in root if node.tag==NS+"rect"
          and node.get("y")=="134" and node.get("height")=="780"]
    progress=[node for node in root if node.tag==NS+"rect"
              and node.get("x")=="35" and node.get("y")=="127" and node.get("height")=="4"]
    if len(header)!=1 or len(grid)!=1 or len(progress)!=2:
        _fail("CABECALHO_F12_INCOMPATIVEL")
    header[0].set("height","105")
    grid[0].set("y","105")
    grid[0].set("height","809")
    for bar in progress:
        bar.set("y","99")
    for item in (title,phase,detail,subtitle):
        root.remove(item)
    pocket=ET.SubElement(root,NS+"g",{
       "id":"f13-essential-pocket","data-geometry":"lateral_superior_esquerdo",
       "data-safe-zone":"ORGANICO_TERCEIROS_NAO_CALIBRADO"
    })
    _node(pocket,"f13-essential-title",title_lines,
          size=21,color="#17394F",y=TITLE_Y,spacing=TITLE_STEP,strong=True)
    _node(pocket,"f13-essential-phase",phase_lines,
          size=16,color="#9C5416",y=PHASE_Y,spacing=18,strong=True)
    _node(pocket,"f13-essential-detail",detail_lines,
          size=11,color="#355D70",y=DETAIL_Y,spacing=DETAIL_STEP,strong=False)
    root.set("data-layout","hero_lateral_f13")
    ET.register_namespace("",NS[1:-1])
    return ET.tostring(root,encoding="unicode"),{
       "layout":"hero_lateral_f13",
       "same_mechanical_stage":True,
       "stage_transform_preserved":stage.get("transform"),
       "title_lines":len(title_lines),
       "detail_lines":len(detail_lines),
       "pocket":[X,142,X+WIDTH,MAX_Y+9],
       "decorative_header_px":105,
       "scale_reduced":False,
       "publish":False,
       "observed_ui_only":True,
       "device_ui_calibrated":False
    }
