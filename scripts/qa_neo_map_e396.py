"""E396: private cartographic benchmark, existing MapLibre stage; no Neo pixels.
All route geometry is existing sourced Panama OSM; timing is illustrative, not a tracked ship.
"""
import hashlib,json,math,shutil
from pathlib import Path
from scripts import formatos_raster as R
from src.v4.formatos import plano as A, atlas_ref
ROOT=Path('qa_neo_map_e396');PUBLIC=Path('motor4/remotion/public/_formato/raster')
CENTER=(-79.77,9.14)
PROFILES={'wide':(1280,640),'portrait':(720,1280)}
START,END,DETAIL=2.3,9.5,10.35
ROUTE_START,ROUTE_END=10.,13.5
ROUTE_BOUNDS=[-79.92618426184262,8.942864428644286,-79.56466564665647,9.311548115481155]
def envelope(z,w,h):
    o,s,l,n=ROUTE_BOUNDS
    boxes=[viewport(z,w,h,c) for c in [(o,s),(l,n),CENTER]]
    return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
def viewport(z,w,h,center=CENTER):
    x,y=A.merc(*center);world=512*2**z
    lon=lambda v:360*v-180
    lat=lambda v:math.degrees(math.atan(math.sinh(math.pi*(1-2*v))))
    return [lon(x-w/2/world),lat(y+h/2/world),lon(x+w/2/world),lat(y-h/2/world)]
def specs():
    result=[]
    for z in range(5,12):
        de=z-1.15 if z<11 else 10.05
        bbox=viewport(de-.5,1280,1280) if z<11 else envelope(de-.5,1280,1280)
        x0,y0=R.tile_xy(bbox[0],bbox[3],z);x1,y1=R.tile_xy(bbox[2],bbox[1],z)
        count=(int(x1)-int(x0)+1)*(int(y1)-int(y0)+1)
        if count>100:raise ValueError('E396-TILE-BUDGET')
        result.append({'name':'neo_e396_panama_z'+str(z),'bbox':bbox,'z':z,'de':de,'tiles':count,'dataset':'bmng' if z<=8 else 's2_2016'})
    return result
def validate_coverage(layers):
    # At every 1/30s, require full viewport coverage for every visible new layer.
    # Require a fully opaque background and a topmost raster <=2x upscale after each blend.
    for i in range(420):
        t=i/30
        q=min(1,max(0,(t-1)/9))
        e=4*q**3 if q<.5 else 1-(-2*q+2)**3/2
        z=START+(END-START)*e
        follow=max(0,min(1,(t-ROUTE_START)/(ROUTE_END-ROUTE_START)))
        u=4*follow**3 if follow<.5 else 1-(-2*follow+2)**3/2
        z+= (DETAIL-END)*u
        for w,h in PROFILES.values():
            view=envelope(z,w,h) if t>=ROUTE_START else viewport(z,w,h);active=[]
            for r,m in layers:
                op=A.opacidade_raster(z,r.get('de'))
                if op>1e-8:
                    if r.get('de') is not None and not A.cobre(m,view):raise ValueError(('E396-COVERAGE',i,r['nome']))
                    if A.cobre(m,view):active.append((op,m))
            if not active or not any(op>=.999 for op,m in active):raise ValueError(('E396-BASE',i))
            # Effective top layer contributes >=50% and meets the source-resolution gate.
            if not any(op>=.5 and m['nitido_ate']+1e-6>=z for op,m in active):raise ValueError(('E396-RESOLUTION',i,z))
def main():
    ROOT.mkdir(exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    layers=[({'nome':'ne2_mundo'},A.raster_info('ne2_mundo'))]
    for s in specs():
        R.registrar_base_regional(s['name'],s['bbox'],s['z'],s['dataset'],oceano='batimetria' if s['dataset']=='s2_2016' else None)
        layers.append(({'nome':s['name'],'de':s['de']},A.raster_info(s['name'])))
    validate_coverage(layers)
    ds=atlas_ref.datasets();rasters=[]
    for r,m in layers:
        f=A.RASTER_DIR/m['arquivo']
        if hashlib.sha256(f.read_bytes()).hexdigest()!=m['sha256'] or not ds[m['dataset']]['uso_comercial']:raise ValueError('E396-SOURCE')
        shutil.copyfile(f,PUBLIC/f.name)
        # Neutral dark wide map; retain actual orbital color in regional imagery.
        grade={'saturacao':-.68 if m['dataset']=='ne2_raster' else -.42,'contraste':.08,'brilho_min':.025,'brilho_max':.84}
        rasters.append({**r,'dataset':m['dataset'],'src':'_formato/raster/'+f.name,'cantos':m['cantos'],'atribuicao':m['atribuicao'],'tipo':m['tipo'],'ajuste':grade,**({'datasets_extra':['bmng']} if m.get('oceano') else {})})
    geo=json.loads(Path('motor4/formatos/dados/panama.topo.json').read_text())
    if not geo.get('topo',{}).get('objects',{}).get('rota') or 'Natural Earth' not in ' '.join(geo['meta']['atribuicao']):raise ValueError('E396-GEO')
    # Check the declared conservative route envelope against the actual topology, not guessed path.
    topo=geo['topo'];g=topo['objects']['rota']['geometries'][0];a=g['arcs'][0];assert len(g['arcs'])==1 and a>=0
    x=y=0;points=[];tr=topo['transform']
    for dx,dy in topo['arcs'][a]:
        x+=dx;y+=dy;points.append((x*tr['scale'][0]+tr['translate'][0],y*tr['scale'][1]+tr['translate'][1]))
    assert all(ROUTE_BOUNDS[0]-1e-9<=x<=ROUTE_BOUNDS[2]+1e-9 and ROUTE_BOUNDS[1]-1e-9<=y<=ROUTE_BOUNDS[3]+1e-9 for x,y in points)
    tokens=A.tokens_canal(A.canal('coringa'));tokens['palco']['mapa'].update(destaque='#D4473F',mar='#25292B')
    for name,(w,h) in PROFILES.items():
        cam=lambda z:{'foco':list(CENTER),'ancora':[w/2,h/2],'zoom':z}
        p={'neo_benchmark':True,'neo_follow':{'start':ROUTE_START,'end':ROUTE_END,'zoom':DETAIL},'duracao':14,'formato':'atlas','tokens':tokens,'geo':geo,'rasters':rasters,
           'palco':[{'t':0,'tipo':'mapa','camera':cam(START),'veu':'nenhum','deriva':0},{'t':1,'tipo':'mapa','camera':cam(END),'dur_camera':9,'veu':'nenhum','deriva':0}],
           'camadas':[],'rotas':[{'t0':ROUTE_START,'t1':ROUTE_END,'cor':'destaque','largura':4}],
           'rotulos':[{'nome':'AMÉRICA CENTRAL','lonlat':[-88,15],'t0':0,'t1':3.5,'estilo':'area'},{'nome':'PANAMÁ','lonlat':[-79.77,9.14],'t0':4.8,'t1':9,'estilo':'area'},{'nome':'MAR DO CARIBE','lonlat':[-79.77,9.72],'t0':7.2,'t1':9.6,'estilo':'oceano'},{'nome':'OCEANO PACÍFICO','lonlat':[-79.65,8.52],'t0':7.2,'t1':9.6,'estilo':'oceano'},{'nome':'COLÓN','lonlat':[-79.90,9.36],'t0':9.8,'t1':11.25,'estilo':'area'},{'nome':'LAGO GATÚN','lonlat':[-79.88,9.17],'t0':10.7,'t1':12.4,'estilo':'lago'},{'nome':'PANAMÁ','lonlat':[-79.52,8.98],'t0':12.1,'t1':14,'estilo':'area'}],
           'creditos':{'datasets':{k:v['atribuicao_exigida']+(' · CC BY 4.0 · cores ajustadas' if k=='s2_2016' else '') for k,v in ds.items() if v.get('atribuicao_exigida')},'obrigatorias':[k for k,v in ds.items() if v.get('obrigatoria')],'caixa':[20,h-86,w-40,74],'px':16,'linha':19},
           'seguro':{'esq':24,'topo':28,'base':h-96,'direita':[],'dir_max':w-24}}
        (ROOT/(name+'.json')).write_text(json.dumps({'map':p},ensure_ascii=False))
    (ROOT/'manifest.json').write_text(json.dumps({'publish':False,'review':'PENDING','route':'OSM Canal do Panamá; animação ilustrativa, não AIS','profiles':PROFILES,'coverage_frames':420,'revision':'E396B','route_camera':'same progress as OSM line; illustrative, not vessel track','native_source_limit':'Sentinel-2 optical bands 10m; z11 tiles not 10m/pixel','sources':[m for r,m in layers],'reference':'Neo 0–34s, técnicas; sem material de terceiros no render'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
