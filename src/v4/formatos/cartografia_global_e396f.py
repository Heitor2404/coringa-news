"""Reusable private benchmark planner: thematic inputs are data, not code.
Mercator bounds are explicit; antimeridian/polar split is not certified.
No invented raster resolution, no unlicensed automatic fallback.
"""
import math,re,json,hashlib,copy,shutil
from PIL import Image
import numpy as np
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
ZOOM_PER_SECOND=1.05
ROUTE_SECONDS_MIN=5.5
ROUTE_SECONDS_MAX=8.0

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
    # Same average log2-scale speed; neither fixed duration nor pixel speed.
    arrival=round(.05+max(2.8,(end-start)/ZOOM_PER_SECOND),2)
    follow_start=round(arrival+1.8,2)
    length=float(geo.get('meta',{}).get('rota_km') or 0) if route else 0
    if route and not 0<length<=2000:raise ValueError('GLOBAL-ROUTE-LENGTH')
    # Editorial time, not physical vessel speed. Full route; never silently truncate.
    follow_end=round(follow_start+min(ROUTE_SECONDS_MAX,max(ROUTE_SECONDS_MIN,math.log1p(length)*1.55)),2) if route else follow_start
    terrain=case.get('terrain') is True
    if terrain and route:raise ValueError('GLOBAL-TERRAIN-ROUTE-SEPARATE')
    duration=math.ceil(follow_end+1.2 if route else arrival+(5 if terrain else 2.4))
    return {'center':center,'start':start,'end':end,'detail':detail,'route_bounds':rb,'duration':duration,'arrival':arrival,'follow_start':follow_start,'follow_end':follow_end,'route':route,'route_km':length,'terrain':terrain,'zoom_per_second':ZOOM_PER_SECOND}
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
        if p['terrain']:b=union([b,envelope(p,p['end'],2560,2560,False)])
        if not valid_bbox(b):raise ValueError('GLOBAL-TILE-FOOTPRINT')
        x0,y0=R.tile_xy(b[0],b[3],z);x1,y1=R.tile_xy(b[2],b[1],z)
        count=(int(x1)-int(x0)+1)*(int(y1)-int(y0)+1)
        if count>100:raise ValueError(('GLOBAL-TILE-BUDGET',z,count))
        rows.append({'nome':'global_f_'+case['id']+'_z'+str(z),'bbox':b,'z':z,'de':de,'tiles':count,'dataset':'bmng' if z<=8 else 's2_2016'})
    return rows
def check(p,layers):
    for i in range(p['duration']*30):
        t=i/30;z=camera_zoom(p,t)
        for w,h in PROFILES.values():
            view=envelope(p,z,w,h,p['route'] and t>=p['follow_start']);active=[]
            if p['terrain'] and t>=p['arrival']:view=envelope(p,z,w*2,h*2,False)
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
def align_color(previous,current,meta_prev,meta,out):
    # Compare the SAME geographic footprint in both images, not independent
    # histograms. Bounded offset only; retain terrain texture and original files.
    o,s,l,n=meta['bbox'];a,b,c,d=meta_prev['bbox']
    if not (a<=o<l<=c and b<=s<n<=d):return current,{'offset_rgb':[0,0,0],'reason':'no full overlap'}
    x0,y0=A.merc(a,d);x1,y1=A.merc(c,b);u0,v0=A.merc(o,n);u1,v1=A.merc(l,s)
    with Image.open(previous) as im:
        w,h=im.size;ref=im.crop(((u0-x0)/(x1-x0)*w,(v0-y0)/(y1-y0)*h,(u1-x0)/(x1-x0)*w,(v1-y0)/(y1-y0)*h)).resize((96,96),Image.Resampling.BILINEAR)
    with Image.open(current) as im:
        img=im.convert('RGB');q=np.asarray(img.resize((96,96),Image.Resampling.BILINEAR),dtype=np.float32)
        diff=np.asarray(ref.convert('RGB'),dtype=np.float32)-q
        offset=np.clip(np.median(diff,axis=(0,1))*.55,-14,14)
        arr=np.asarray(img,dtype=np.float32);out.parent.mkdir(parents=True,exist_ok=True)
        Image.fromarray(np.clip(arr+offset,0,255).astype(np.uint8)).save(out,quality=95)
    return out,{'offset_rgb':[round(float(v),2) for v in offset],'reason':'registered geographic overlap; bounded median adjustment'}
def terrain_tiles(case,p):
    if not p['terrain']:return None
    # Offline, fixed zoom, actual Terrarium height samples. Use the same
    # licensed AWS Terrain Tiles provider as ATLAS hillshade.
    ds=atlas_ref.datasets()['terrain_tiles']
    if not ds['uso_comercial']:raise ValueError('TERRAIN-LICENSE')
    z=max(4,min(10,math.ceil(p['end'])))
    bbox=envelope(p,p['end'],2560,2560,False)
    a,b=R.tile_xy(bbox[0],bbox[3],z);c,d=R.tile_xy(bbox[2],bbox[1],z)
    # One tile halo for DEM mesh stitching. Fail instead of using remote tiles.
    xs=range(max(0,int(a)-1),min(2**z,int(c)+2));ys=range(max(0,int(b)-1),min(2**z,int(d)+2))
    if len(xs)*len(ys)>144:raise ValueError('TERRAIN-BUDGET')  # separate bounded DEM halo (max 12×12)
    root=PUBLIC.parent/'terrain'/case['id'];records=[];lo=float('inf');hi=-float('inf')
    for x in xs:
        for y in ys:
            path=root/str(z)/str(x)/(str(y)+'.png');path.parent.mkdir(parents=True,exist_ok=True)
            im=R.baixar(R.DEM.format(z=z,x=x,y=y))
            if im is None or im.size!=(256,256):raise ValueError('TERRAIN-MISSING')
            im=im.convert('RGB');e=R.elevacao(im);lo=min(lo,float(e.min()));hi=max(hi,float(e.max()));im.save(path)
            records.append({'tile':[z,x,y],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    if not math.isfinite(lo) or hi-lo<10:raise ValueError('TERRAIN-RELIEF')
    nw=R.tile_lonlat(xs.start,ys.start,z);se=R.tile_lonlat(xs.stop,ys.stop,z)
    return {'src':'_formato/terrain/'+case['id'],'zoom':z,'bounds':[nw[0],se[1],se[0],nw[1]],'start':p['arrival']+.1,'end':p['arrival']+3.5,'pitch':24,'bearing':-8,'exaggeration':1,'source':R.DEM,'license':ds['licenca'],'tiles':records,'elevation_range_m':[lo,hi]}
def discovery(case,out):
    # A catalogue result is not approval. No uncontrolled imagery download.
    import requests
    report={'status':'UNAVAILABLE','candidates':[]}
    try:
        res=requests.get('https://api.imagery.hotosm.org/stac/search',params={'bbox':','.join(map(str,case['roi'])),'limit':20},timeout=20);res.raise_for_status()
        for f in res.json()['features']:
            v=f.get('properties',{});report['candidates'].append({'id':f.get('id'),'gsd':v.get('gsd'),'license':v.get('license'),'collection':f.get('collection'),'review':'PENDING'})
        report['status']='CANDIDATES' if report['candidates'] else 'NO_RESULTS'
    except Exception as e:report['error_type']=type(e).__name__
    (out/'detail-discovery.json').write_text(json.dumps(report,indent=2))

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
    ds=atlas_ref.datasets();rasters=[];color_receipts=[];prev=None
    terrain=terrain_tiles(case,p)
    discovery(case,out)
    for r,m in layers:
        f=A.RASTER_DIR/m['arquivo']
        if not ds[m['dataset']]['uso_comercial'] or hashlib.sha256(f.read_bytes()).hexdigest()!=m['sha256']:raise ValueError('GLOBAL-RASTER-RIGHTS')
        dest=PUBLIC/f.name
        shutil.copyfile(f,dest)
        if prev:
            derived=PUBLIC/(f.stem+'_matched.jpg')
            dest,report=align_color(prev[0],dest,prev[1],m,derived)
            color_receipts.append({'raster':m['nome'],'source_sha256':m['sha256'],'render_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),**report})
        prev=(dest,m)
        # Natural colors, not the Neo grayscale identity. Mild common grade.
        grade={'saturacao':-.12,'contraste':.035,'brilho_min':.01,'brilho_max':.98}
        rasters.append({'nome':r['nome'],'de':r.get('de'),'dataset':m['dataset'],'src':'_formato/raster/'+dest.name,'cantos':m['cantos'],'atribuicao':m['atribuicao'],'tipo':m['tipo'],'ajuste':grade,**({'datasets_extra':['bmng']} if m.get('oceano') else {})})
    tokens=copy.deepcopy(A.tokens_canal(A.canal('coringa')));tokens['palco']['mapa'].update(destaque='#E7DFCC',mar='#253E4F')
    labels=[]
    for l in case['labels']:
        if not 0<=l['from']<l['to']<=1 or not -180<=l['coord'][0]<=180 or not -85<=l['coord'][1]<=85:raise ValueError('GLOBAL-LABEL')
        labels.append({'nome':l['name'],'lonlat':l['coord'],'t0':l['from']*(p['arrival']+3) if not p['route'] else l['from']*p['duration'],'t1':l['to']*p['duration'],'estilo':l.get('style','area')})
    for name,(w,h) in PROFILES.items():
        cam=lambda z:{'foco':p['center'],'ancora':[w/2,h/2],'zoom':z}
        props={'neo_benchmark':True,'neo_global_style':True,'duracao':p['duration'],'formato':'atlas','tokens':tokens,'geo':geo,'rasters':rasters,'palco':[{'t':0,'tipo':'mapa','camera':cam(p['start']),'veu':'nenhum','deriva':0},{'t':.05,'tipo':'mapa','camera':cam(p['end']),'dur_camera':p['arrival']-.05,'camera_curve':'cruise','veu':'nenhum','deriva':0}],'camadas':[],'rotas':[],'rotulos':labels,
        'creditos':{'datasets':{k:v['atribuicao_exigida']+(' · CC BY 4.0 · cores ajustadas' if k=='s2_2016' else '') for k,v in ds.items() if v.get('atribuicao_exigida')},'obrigatorias':[k for k,v in ds.items() if v.get('obrigatoria')],'caixa':[20,h-86,w-40,74],'px':16,'linha':19},'seguro':{'esq':24,'topo':28,'base':h-96,'direita':[],'dir_max':w-24}}
        props['neo_e396e']=True
        props['neo_e396f']=True
        if name=='portrait':
            from src.v4.formatos.qa_area_segura import carregar
            x,y,r,b=[round(v*2/3) for v in carregar()['universal']]
            props['creditos'].update(caixa=[x,b-75,r-x,75],px=13,linha=15)
            props['seguro']={'esq':x,'topo':y,'base':b-80,'direita':[],'dir_max':r}
        if terrain:props['neo_terrain']={k:terrain[k] for k in ('src','zoom','bounds','start','end','pitch','bearing','exaggeration')}
        if case.get('territory'):
            target=case['territory']
            if not any(g.get('properties',{}).get('name')==target for g in geo['topo']['objects']['paises']['geometries']):raise ValueError('GLOBAL-TERRITORY')
            props['destaques']=[{'fonte':'paises','nome':target,'cor':'destaque','t0':p['arrival']-.8,'t1':p['duration']}]
        if case.get('connections'):
            props['rotas']=[{'arco':c['endpoints'],'t0':.35+i*.5,'t1':min(p['arrival']*.55,2.5+i*.5),'some':p['arrival']*.65,'cor':'destaque' if i==0 else 'destaque2','largura':4} for i,c in enumerate(case['connections'])]
            props['neo_connections_until']=p['arrival']*.65
        if p['route']:
            props.update(neo_follow={'start':p['follow_start'],'end':p['follow_end'],'zoom':p['detail'],'from':0.,'to':1.,'ship':True},neo_route_overview=True,rotas=[{'t0':p['arrival'],'t1':p['follow_start']-.35,'cor':'destaque','largura':5}])
        (out/(name+'.json')).write_text(json.dumps({'map':props},ensure_ascii=False))
    (out/'manifest.json').write_text(json.dumps({'publish':False,'review':'PENDING','revision':'E396F','case':case,'camera':p,'profiles':PROFILES,'coverage_frames':p['duration']*30,'sources':[m for r,m in layers],'tile_requests':rows,'color_matching':color_receipts,'terrain':terrain,'route_note':'OSM, travessia ilustrativa completa 0–100%, sem AIS ou escala física do símbolo' if p['route'] else None,'credit_policy':'Only mandatory on-media attribution; voluntary credits and complete provenance retained in manifest; not a publication approval','limits':'Mercator; antimeridiano e polos requerem tratamento; resolução orbital depende da fonte'},ensure_ascii=False,indent=2))
