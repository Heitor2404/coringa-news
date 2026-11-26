"""E322: factual static reveal, bound to reviewed source pixels and a real
visible label/bracket. Never claims motion or approves publication."""
import math,re

def validar(shot,media,sha,*,private):
    p=shot.get('static_fact_reveal')
    if p is None:return None
    span=shot['end']-shot['start']
    if (not private or not isinstance(p,dict) or shot.get('type')!='photo' or shot.get('photo_framing')!='integral'
        or shot.get('photo_roi_candidate') or media.get('original_graphic')
        or p.get('schema')!='coringa.static.reveal.private.v1' or p.get('publicar') is not False
        or p.get('shot')!=shot.get('id') or p.get('sha256')!=sha or media.get('expected_sha256')!=sha
        or not re.fullmatch('[a-f0-9]{64}',str(sha)) or not p.get('review_ref')
        or not isinstance(p.get('observation'),str) or len(p['observation'])<35):
        raise ValueError('E322-VINCULO')
    at=p.get('at');label=p.get('label');b=p.get('bbox')
    if (type(at) not in (int,float) or not math.isfinite(at) or not .8<=at<=span-.8 or span-at>2.8+1e-6
        or not isinstance(label,str) or not 3<=len(label)<=34 or not label.isprintable()
        or label.strip().upper()==str(shot.get('lead','')).strip().upper()
        or not isinstance(b,list) or len(b)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in b)):
        raise ValueError('E322-MARCO')
    x,y,r,d=b
    if not (0<x<r<1 and 0<y<d<1) or (r-x)*(d-y)>.45:raise ValueError('E322-REGIAO')
    w,h=media.get('width'),media.get('height')
    if not all(type(v) is int and v>=600 for v in (w,h)) or w<=h:raise ValueError('E322-DIMENSOES')
    scale=min(1080/w,900/h);sw=w*scale;sh=h*scale
    # Same full-source geometry and bracket margin as centeredLandscape/E309.
    if min(x*sw,y*sh,(1-r)*sw,(1-d)*sh)<19 or min((r-x)*sw,(d-y)*sh)<36:
        raise ValueError('E322-REGIAO-ILEGIVEL')
    if not any(c.get('label')==label and c.get('at')==at for c in shot.get('cues',[])):
        raise ValueError('E322-MARCO-SEM-CUE')
    result={'at':at,'label':label,'bbox':b,'sha256':sha,'revisao_id':p['review_ref'],'status':'PRIVATE_STATIC_REVEAL_PENDING'}
    if 'detail_zoom' in p:
        if p['detail_zoom'] is not True:raise ValueError('E325-DETAIL-FLAG')
        # Genuine detail magnification vs the established full-image stage,
        # not merely vs a reduced overview. Same two contain rectangles as TS.
        dw,dh=(r-x)*w,(d-y)*h
        detail_scale=min(620/dw,340/dh)
        overview_scale=min(620/w,290/h)
        gain=detail_scale/scale
        if gain<1.1 or min(dw*detail_scale,dh*detail_scale)<100:
            raise ValueError('E325-DETAIL-SEM-GANHO')
        result['detail_zoom']=True
        result['detail_gain']=round(gain,3)
        result['overview_gain']=round(detail_scale/overview_scale,3)
    return result
