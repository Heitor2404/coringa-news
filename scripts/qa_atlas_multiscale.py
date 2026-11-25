"""Plan and render private multi-scale map candidates with native ATLAS.
No topic-specific renderer, no TTS, no historical-state or route reconstruction.
"""
import math,re
from pathlib import Path
from scripts import formatos_raster as R
from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import plano as A, direcao_eventos as DE

def escalas(roi, delta=1.6, *, fonte_continua=False):
    """Select tile levels and bounding boxes from the existing camera geometry.
    The start of each level covers the full vertical viewport, with overlap.
    No downloaded tile or visual quality is asserted by this planner.
    """
    if len(roi)!=4 or not all(math.isfinite(v) for v in roi):
        raise ValueError('GEO-ROI')
    o,s,l,n=roi
    if not -180<o<l<180 or not -84<s<n<84 or not .2<=delta<=1.8:
        raise ValueError('GEO-ROI')
    c=A.COMP['atlas.abertura']
    cam=A.camera_roi(roi,c['quadro'],12,.86,c.get('centro_intencao'))
    end=cam['zoom']
    start=max(4.,end-delta)
    if end-start<.2:raise ValueError('GEO-ESCALA: usar mapa normal')
    fx,fy=A.merc(*cam['foco'])
    result=[]
    for z in range(math.ceil(start),math.ceil(end)+1):
        low=max(start,z-1)
        # At most one level of oversampling for the request, not the renderer.
        # The opacity ramp begins at de-.5 = low-.05. Acquire the full
        # viewport at low-.06, before any new raster becomes visible.
        # Prevent rectangular seams while the camera is still zoomed out.
        view=A.tela_lonlat(A._restringir({**cam,'fx':fx,'fy':fy,'zoom':low-.06}))
        w,ss,e,nn=view
        bbox=[min(w,o),min(ss,s),max(e,l),max(nn,n)]
        if not -180<bbox[0]<bbox[2]<180 or not -85<=bbox[1]<bbox[3]<=85:
            raise ValueError('GEO-COBERTURA')
        x0,y0=R.tile_xy(bbox[0],bbox[3],z);x1,y1=R.tile_xy(bbox[2],bbox[1],z)
        count=(int(x1)-int(x0)+1)*(int(y1)-int(y0)+1)
        if count>100:raise ValueError('GEO-ORCAMENTO')
        result.append({'bbox':bbox,'zoom':z,'dataset':'s2_2016' if z>8 or (fonte_continua and math.ceil(end)>8) else 'bmng',
                       'tiles':count,'de':None if not result else low+.45})
    return result

def adquirir_bases(caso):
    """Acquire once, independently of narration duration; all geometry is sourced.
    A caller must supply an already researched region, not coordinates invented by AI.
    """
    name=caso['id']
    if not re.fullmatch(r'[a-z0-9_]{1,40}',name):raise ValueError('GEO-ID')
    q=caso['atlas'];source=caso['fonte_localizacao']
    if not isinstance(source,str) or not source.startswith('https://'):
        raise ValueError('GEO-FONTE')
    if not isinstance(q.get('label'),str) or not q['label'].strip():
        raise ValueError('GEO-ROTULO')
    o,s,l,n=q['roi']
    lon,lat=q['lonlat']
    if not o<=lon<=l or not s<=lat<=n:
        raise ValueError('GEO-MARCADOR')
    specs=escalas(q['roi'],caso.get('delta',1.6),fonte_continua=caso.get('fonte_continua') is True)
    bases=[]; metas=[]
    for spec in specs:
        m=R.registrar_base_regional(name+'_z'+str(spec['zoom']),spec['bbox'],spec['zoom'],spec['dataset'])
        metas.append(m)
        bases.append({'nome':m['nome'],**({'de':spec['de']} if spec['de'] is not None else {})})
    return {'bases':bases,'metas':metas,'specs':specs}

def resolver(caso, adquirido, span):
    """Reuse acquired rasters with measured speech duration, no further network."""
    q=caso['atlas'];bases=adquirido['bases']
    ch={**caso,'atlas':{**q,'raster':bases[0]['nome']}}
    p,report=DE.plano_entrada_geografica(E.mapplan(ch,span),roi_destino=q['roi'],
        bases=bases,rotulo=q['label'],lonlat=q['lonlat'],fonte_localizacao=caso['fonte_localizacao'],
        zoom_desejado=caso.get('delta',1.6))
    return ch,p,report

def preparar(caso):
    adquirido=adquirir_bases(caso)
    ch,p,report=resolver(caso,adquirido,5.5)
    return ch,p,report,adquirido['metas'],adquirido['specs']

def main():
    import sys
    spec=E.read(sys.argv[1])
    if spec.get('publish') is not False:raise ValueError('GEO-PRIVADO')
    cases=[c for c in spec['cases'] if len(sys.argv)<3 or c['id']==sys.argv[2]]
    if not cases:raise ValueError('GEO-CASO')
    for caso in cases:
        E.MAP=Path('qa_atlas_multiscale')/caso['id']
        E.MAP.mkdir(parents=True,exist_ok=True)
        ch,p,report,metas,specs=preparar(caso)
        E.write(E.MAP/'planejamento.json',{'camera':report,'bases':metas,'solicitacoes':specs,
            'fonte_localizacao':caso['fonte_localizacao'],'visual_review':'PENDING','publish':False})
        clip,proof=E.mapclip(ch,5.5,plano_resolvido=p)
        print('E236 MAPA',caso['id'],report,E.sha(clip),flush=True)

if __name__=='__main__':main()
