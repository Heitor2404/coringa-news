"""BBoxes de peça no QUADRO, distintas do envelope de movimento da câmera.

Os papéis da câmera têm caixas de todos os possíveis estados do ciclo
e NÃO devem ser confundidos com detecção de imagem no frame. Este módulo
usa geometria e transformações do SVG já gerado para rastrear 3 atores.
Sem OCR, rede, VLM nem licença de terceiros.
"""
from __future__ import annotations
import json,math,re
from pathlib import Path
from xml.etree import ElementTree as ET
from src.v4.formatos import camera_causal_svg as C

MAP=json.loads(Path(__file__).with_name('rastreador_componentes_svg.json').read_text('utf8'))
FLOAT=r'[-+]?(?:\d+\.?\d*|\.\d+)'
TRANS=re.compile(r'^translate\(('+FLOAT+r') ('+FLOAT+r')\)$')
STAGE=re.compile(
    r'^translate\(('+FLOAT+r') ('+FLOAT+r')\) '
    r'scale\(('+FLOAT+r')\) translate\(0 ('+FLOAT+r')\)$'
)

def _err(x):
    raise ValueError(x)

def _find(root,tag):
    result=[e for e in root.iter() if e.get('id')==tag]
    if len(result)!=1:
        _err('F-BBOX-ATOR-SVG-INEXISTENTE-OUDUPLICADO')
    return result[0]

def bbox_instante(family:str,role:str,svg:str)->dict:
    if MAP.get('schema')!='coringa-dynamic-role-bbox-v1' or MAP.get('publication_approved') is not False:
        _err('F-BBOX-CONTRATO')
    spec=MAP.get('tracked',{}).get(family,{}).get(role)
    if not isinstance(spec,dict):
        _err('F-BBOX-SEM-RASTREADOR')
    try:
        root=ET.fromstring(svg)
    except ET.ParseError:
        _err('F-BBOX-SVG-INVALIDO')
    stage=_find(root,spec['stage'])
    actor=_find(root,'role-'+role)
    m=STAGE.fullmatch(stage.get('transform',''))
    if not m:
        _err('F-BBOX-CAMERA-INCOMPATIVEL')
    tx,ty,scale,shift=map(float,m.groups())
    if not all(math.isfinite(x) for x in (tx,ty,scale,shift)) or scale<1 or scale>1.30:
        _err('F-BBOX-CAMERA-INVALIDA')
    ax=ay=0.
    if actor.get('transform'):
        m=TRANS.fullmatch(actor.get('transform',''))
        if not m:
            _err('F-BBOX-TRANSFORM-ATOR-INVALIDO')
        ax,ay=map(float,m.groups())
    kind=spec['method']
    if kind=='first_svg_rect':
        rectangles=[e for e in actor if e.tag.endswith('rect')]
        if not rectangles:
            _err('F-BBOX-SEM-PRIMITIVA')
        rect=rectangles[0]
        try:
            x,y,w,h=[float(rect.get(k,'')) for k in ('x','y','width','height')]
        except ValueError:
            _err('F-BBOX-PRIMITIVA-INVALIDA')
        margin=spec['margin']
        bounds=[x-margin,y-margin,x+w+margin,y+h+margin]
    elif kind=='group_local_bbox':
        bounds=spec['local_bbox']
    else:
        _err('F-BBOX-METODO-NAO-IMPLEMENTADO')
    if (len(bounds)!=4 or
        any(type(v) not in (int,float) or not math.isfinite(v) for v in bounds)
        or bounds[0]>=bounds[2] or bounds[1]>=bounds[3]):
        _err('F-BBOX-LIMITES-INVALIDOS')
    x1,y1,x2,y2=bounds
    result=[
      round(tx+scale*(ax+x1),3),
      round(ty+scale*(ay+y1+shift),3),
      round(tx+scale*(ax+x2),3),
      round(ty+scale*(ay+y2+shift),3)
    ]
    if not (0<=result[0]<result[2]<=C.CAMERAS['familias'][family]['width']
        and 0<=result[1]<result[3]<=C.CAMERAS['familias'][family]['height']):
        _err('F-BBOX-ATOR-FORA-TELA')
    return {
       'family':family,'actor':role,'pixel_bbox':result,
       'scope':spec['scope'],'source':'SVG_PRIMITIVA_JA_RENDERIZADA',
       'detected_from_external_image':False,'visual_identity_approved':False
    }
