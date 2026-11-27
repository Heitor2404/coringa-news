"""Reusable private benchmark planner: thematic inputs are data, not code.
Mercator bounds are explicit; antimeridian/polar split is not certified.
No invented raster resolution, no unlicensed automatic fallback.
"""
import math,re,json,hashlib,copy,shutil
from pathlib import Path
from scripts import formatos_raster as R
from src.v4.formatos import plano as A,atlas_ref
PROFILES={'wide':(1280,640),'portrait':(720,1280)}
GEO=Path('motor4/formatos/dados')
PUBLIC=Path('motor4/remotion/public/_formato/raster')
def cruise(q,r=.16):
    q=max(0,min(1,q))
    return q*q/(2*r*(1-r)) if q<r else 1-(1-q)**2/(2*r*(1-r)) if q>1-r else (q-r/2)/(1-r)
def inverse_y(y):return math.degrees(math.atan(math.sinh(math.pi*(1-2*y))))
def viewport(z,w,h,center):
    x,y=A.merc(*center);s=512*2**z
    return [(x-w/2/s)*360-180,inverse_y(y+h/2/s),(x+w/2/s)*360-180,inverse_y(y-h/2/s)]
def union(boxes):return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
def valid_bbox(b):
    return len(b)==4 and all(math.isfinite(v) for v in b) and -180<b[0]<b[2]<180 and -85<b[1]<b[3]<85
def route_bounds(geo):
    t=geo['topo'];g=t['objects']['rota']['geometries']
    if len(g)!=1 or g[0]['type']!='LineString':raise ValueError('GLOBAL-ROUTE-GEOMETRY')
    pts=[];tr=t.get('transform')
    for ix in g[0]['arcs']:
        a=t['arcs'][ix if ix>=0 else ~ix]
        x=y=0;part=[]
        for dx,dy in a:
            if tr:
                x+=dx;y+=dy;part.append((x*tr['scale'][0]+tr['translate'][0],y*tr['scale'][1]+tr['translate'][1]))
            else:part.append((dx,dy))
        if ix<0:part.reverse()
        if pts and pts[-1]!=part[0]:raise ValueError('GLOBAL-ROUTE-DISCONTINUITY')
        pts.extend(part)
    if len(pts)<2:raise ValueError('GLOBAL-ROUTE-EMPTY')
    return [min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]
def plan(case,geo):
    if not re.fullmatch('[a-z0-9_]{1,30}',case['id']) or not case['source'].startswith('https://'):raise ValueError('GLOBAL-CASE')
    b=case['roi'];route=case.get('route') is True
    if not valid_bbox(b):raise ValueError('GLOBAL-ROI-ANTIMERIDIAN-OR-POLAR')
    rb=route_bounds(geo) if route else None
    if rb and not A.cobre({'bbox':b},rb):raise ValueError('GLOBAL-ROUTE-ROI')
    x0,y0=A.merc(b[0],b[3]);x1,y1=A.merc(b[2],b[1])
    center=[(x0+x1)*180-180,inverse_y((y0+y1)/2)]
    end=min(10.0,math.log2(min(720*.78/(512*(x1-x0)),640*.78/(512*(y1-y0)))))
    if route:end=min(end,9.5)
    start=2.3
    # Choose a valid context viewport, without a black/wrapped raster edge.
    while start<4.01 and not valid_bbox(viewport(start,1280,1280,center)):start=round(start+.05,3)
    if start>4 or end<start+.5:raise ValueError('GLOBAL-CONTEXT-NEEDS-WRAPPED-OR-WIDER-BASE')
    detail=min(10.35,end+.55) if route else end
    return {'center':center,'start':start,'end':end,'detail':detail,'route_bounds':rb,'duration':24 if route else 14,'arrival':8.5 if route else 10.5,'follow_start':12.,'follow_end':23.5,'route':route}
def envelope(p,z,w,h,following):
    centers=[p['center']]
    if following and p['route_bounds']:
        o,s,l,n=p['route_bounds'];centers.extend([(o,s),(l,n)])
    return union([viewport(z,w,h,c) for c in centers])
def camera_zoom(p,t):
    z=p['start']+(p['end']-p['start'])*cruise((t-.05)/(p['arrival']-.05))
    if p['route']:z+=(p['detail']-p['end'])*cruise((t-p['follow_start'])/(p['follow_end']-p['follow_start']))
    return z
def specs(case,p):
    rows=[]
    for z in range(5,math.ceil(p['detail'])+1):
        de=z-1.15
        if z==11:de=10.05
        # Skip never-visible levels, and cover the entire route envelope where needed.
        if de-.5>=p['detail']:continue
        low=max(p['start'],de-.5)
        b=envelope(p,low,1280,1280,p['route'])
        if not valid_bbox(b):raise ValueError('GLOBAL-TILE-FOOTPRINT')
        x0,y0=R.tile_xy(b[0],b[3],z);x1,y1=R.tile_xy(b[2],b[1],z)
        count=(int(x1)-int(x0)+1)*(int(y1)-int(y0)+1)
        if count>100:raise ValueError(('GLOBAL-TILE-BUDGET',z,count))
        rows.append({'nome':'global_d_'+case['id']+'_z'+str(z),'bbox':b,'z':z,'de':de,'tiles':count,'dataset':'bmng' if z<=8 else 's2_2016'})
    return rows
def check(p,layers):
    for i in range(p['duration']*30):
        t=i/30;z=camera_zoom(p,t)
        for w,h in PROFILES.values():
            view=envelope(p,z,w,h,p['route'] and t>=p['follow_start']);active=[]
            for r,m in layers:
                op=A.opacidade_raster(z,r.get('de'))
                if op>1e-8:
                    if not A.cobre(m,view):raise ValueError(('GLOBAL-COVERAGE',i,r['nome']))
                    active.append((op,m))
            if not any(op>=.999 for op,m in active) or not any(op>=.5 and m['nitido_ate']+1e-6>=z for op,m in active):raise ValueError(('GLOBAL-NITIDEZ',i,z))
def theoretical_layers(rows):
    layers=[({'nome':'ne2_mundo'},{'bbox':[-180,-85,180,85],'nitido_ate':math.log2(12*360/512)+1})]
    for r in rows:
        z=r['z'];b=r['bbox'];x0,y0=R.tile_xy(b[0],b[3],z);x1,y1=R.tile_xy(b[2],b[1],z)
        nw=R.tile_lonlat(int(x0),int(y0),z);se=R.tile_lonlat(int(x1)+1,int(y1)+1,z)
        layers.append((r,{'bbox':[nw[0],se[1],se[0],nw[1]],'nitido_ate':z}))
    return layers
def prepare(case,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    if Path(case['geo']).name!=case['geo']:raise ValueError('GLOBAL-GEO')
    geo=json.loads((GEO/case['geo']).read_text());p=plan(case,geo)
    if 'Natural Earth' not in ' '.join(geo['meta']['atribuicao']):raise ValueError('GLOBAL-ATTRIBUTION')
    rows=specs(case,p);check(p,theoretical_layers(rows))
    layers=[({'nome':'ne2_mundo'},A.raster_info('ne2_mundo'))]
    for s in rows:
        R.registrar_base_regional(s['nome'],s['bbox'],s['z'],s['dataset'],oceano='batimetria_costeira' if case.get('coast') and s['dataset']=='s2_2016' else None)
        layers.append((s,A.raster_info(s['nome'])))
    check(p,layers)
    ds=atlas_ref.datasets();rasters=[]
    for r,m in layers:
        f=A.RASTER_DIR/m['arquivo']
        if not ds[m['dataset']]['uso_comercial'] or hashlib.sha256(f.read_bytes()).hexdigest()!=m['sha256']:raise ValueError('GLOBAL-RASTER-RIGHTS')
        shutil.copyfile(f,PUBLIC/f.name)
        # Natural colors, not the Neo grayscale identity. Mild common grade.
        grade={'saturacao':-.12,'contraste':.035,'brilho_min':.01,'brilho_max':.98}
        rasters.append({'nome':r['nome'],'de':r.get('de'),'dataset':m['dataset'],'src':'_formato/raster/'+f.name,'cantos':m['cantos'],'atribuicao':m['atribuicao'],'tipo':m['tipo'],'ajuste':grade,**({'datasets_extra':['bmng']} if m.get('oceano') else {})})
    tokens=copy.deepcopy(A.tokens_canal(A.canal('coringa')));tokens['palco']['mapa'].update(destaque='#E7DFCC',mar='#253E4F')
    labels=[]
    for l in case['labels']:
        if not 0<=l['from']<l['to']<=1 or not -180<=l['coord'][0]<=180 or not -85<=l['coord'][1]<=85:raise ValueError('GLOBAL-LABEL')
        labels.append({'nome':l['name'],'lonlat':l['coord'],'t0':l['from']*p['duration'],'t1':l['to']*p['duration'],'estilo':l.get('style','area')})
    for name,(w,h) in PROFILES.items():
        cam=lambda z:{'foco':p['center'],'ancora':[w/2,h/2],'zoom':z}
        props={'neo_benchmark':True,'neo_global_style':True,'duracao':p['duration'],'formato':'atlas','tokens':tokens,'geo':geo,'rasters':rasters,'palco':[{'t':0,'tipo':'mapa','camera':cam(p['start']),'veu':'nenhum','deriva':0},{'t':.05,'tipo':'mapa','camera':cam(p['end']),'dur_camera':p['arrival']-.05,'camera_curve':'cruise','veu':'nenhum','deriva':0}],'camadas':[],'rotas':[],'rotulos':labels,
        'creditos':{'datasets':{k:v['atribuicao_exigida']+(' · CC BY 4.0 · cores ajustadas' if k=='s2_2016' else '') for k,v in ds.items() if v.get('atribuicao_exigida')},'obrigatorias':[k for k,v in ds.items() if v.get('obrigatoria')],'caixa':[20,h-86,w-40,74],'px':16,'linha':19},'seguro':{'esq':24,'topo':28,'base':h-96,'direita':[],'dir_max':w-24}}
        if p['route']:
            props.update(neo_follow={'start':p['follow_start'],'end':p['follow_end'],'zoom':p['detail'],'from':.12,'to':.48,'ship':True},neo_route_overview=True,rotas=[{'t0':8.5,'t1':11.,'cor':'destaque','largura':5}])
        (out/(name+'.json')).write_text(json.dumps({'map':props},ensure_ascii=False))
    (out/'manifest.json').write_text(json.dumps({'publish':False,'review':'PENDING','revision':'E396D','case':case,'camera':p,'profiles':PROFILES,'coverage_frames':p['duration']*30,'sources':[m for r,m in layers],'tile_requests':rows,'route_note':'OSM, trecho ilustrativo 12–48%, sem AIS ou escala física do símbolo' if p['route'] else None,'limits':'Mercator; antimeridiano e polos requerem tratamento; resolução orbital depende da fonte'},ensure_ascii=False,indent=2))
