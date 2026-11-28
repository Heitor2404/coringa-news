"""Animação de destaque funcional por relações FÍSICAS cadastradas.

Não fabrica relações, não move câmera, nem acrescenta cards ou texto.
As linhas pertencem aos dutos do renderer e contornos seguem peças móveis.
As coordenadas são anotadas por família, não inferidas por palavras livres.
"""
from __future__ import annotations
import json,math
from pathlib import Path
from xml.sax.saxutils import escape
from src.v4.formatos import grafo_causal,camera_causal_svg

REGISTRO=json.loads(Path(__file__).with_name('realce_causal_trajetos.json').read_text('utf8'))

def _fail(code):
    raise ValueError(code)

def _rect(values,outer):
    if (not isinstance(values,(list,tuple)) or len(values)!=4 or
        any(type(v) not in (int,float) or not math.isfinite(v) for v in values)):
        _fail('F-REALCE-GEOMETRIA-INVALIDA')
    x,y,w,h=values
    if (w<=0 or h<=0 or x<outer.x1-2 or y<outer.y1-2 or
        x+w>outer.x2+2 or y+h>outer.y2+2):
        _fail('F-REALCE-FORA-DA-MAQUINA')
    return x,y,w,h

def renderizar(familia:str,acao:str,fracao:float,*,
              dinamicos:dict|None=None,fisica_confirma:bool=True)->str:
    if REGISTRO.get('schema')!='coringa-emphasis-paths-v1' or REGISTRO.get('publicar') is not False:
        _fail('F-REALCE-PRIVACIDADE')
    if type(fracao) not in (int,float) or not math.isfinite(fracao) or not 0<=fracao<=1:
        _fail('F-REALCE-TEMPO-INVALIDO')
    f=grafo_causal.GRAFOS.get(familia)
    if not isinstance(f,dict):
        _fail('F-REALCE-SEM-GRAFO')
    graph=grafo_causal.montar(familia,tuple(e['acao'] for e in f['eventos']))
    event=next((e for e in graph['eventos'] if e['acao']==acao),None)
    if event is None:
        _fail('F-REALCE-ACAO-NAO-CADASTRADA')
    entries=REGISTRO.get('familias',{}).get(familia,{})
    if acao not in entries:
        # Ex.: faísca do Otto já é desenhada por sua própria física.
        return ''
    spec=entries[acao]
    if (not isinstance(spec,dict) or spec.get('kind') not in ('flow','outline') or
        not isinstance(spec.get('edge'),list) or len(spec['edge'])!=3):
        _fail('F-REALCE-OPERADOR-INVALIDO')
    edge=tuple(spec['edge'])
    if edge not in [(r['from'],r['type'],r['to']) for r in event['relacoes_em_foco']]:
        _fail('F-REALCE-SEM-RELACAO-CAUSAL')
    geometry=camera_causal_svg.CAMERAS['familias'].get(familia)
    if not geometry:
        _fail('F-REALCE-SEM-GEOMETRIA')
    if edge[0] not in geometry['roles'] or edge[2] not in geometry['roles']:
        _fail('F-REALCE-ATOR-SEM-GEOMETRIA')
    outer=camera_causal_svg.Caixa.parse(geometry['bounds'])
    color=spec.get('color','')
    if (not isinstance(color,str) or len(color)!=7 or not color.startswith('#') or
        any(c not in '0123456789abcdefABCDEF' for c in color[1:])):
        _fail('F-REALCE-COR')
    if type(fisica_confirma) is not bool or not fisica_confirma:
        _fail('F-REALCE-SEM-EVIDENCIA-FISICA')
    fade=max(0.,min(1.,fracao/0.18,(1.-fracao)/0.18))
    opacity=0.60*fade
    prefix=f'<g id="causal-emphasis" data-event="{escape(acao)}" opacity="{opacity:.3f}" fill="none">'
    if spec['kind']=='flow':
        box=camera_causal_svg.Caixa.parse(spec['bounds'])
        if (box.x1<outer.x1-2 or box.x2>outer.x2+2 or
            box.y1<outer.y1-2 or box.y2>outer.y2+2):
            _fail('F-REALCE-FORA-DA-MAQUINA')
        d=spec.get('path','')
        if not isinstance(d,str) or not d.startswith('M ') or any(c in d for c in '<>{};&'):
            _fail('F-REALCE-CAMINHO-INVALIDO')
        return (prefix+f'<path d="{escape(d)}" stroke="{color}" stroke-width="4" '
            'stroke-linecap="round" stroke-linejoin="round" '
            f'stroke-dasharray="11 17" stroke-dashoffset="{-40*fracao:.2f}"/></g>')
    key=spec.get('dynamic')
    if not isinstance(key,str) or not isinstance(dinamicos,dict) or key not in dinamicos:
        _fail('F-REALCE-SEM-PECA-MOVEL')
    x,y,w,h=_rect(dinamicos[key],outer)
    return (prefix+f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'rx="10" stroke="{color}" stroke-width="3.2"/></g>')
