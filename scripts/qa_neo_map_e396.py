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
START,END=2.3,9.5
def viewport(z,w,h,center=CENTER):
    x,y=A.merc(*center);world=512*2**z
    lon=lambda v:360*v-180
    lat=lambda v:math.degrees(math.atan(math.sinh(math.pi*(1-2*v))))
    return [lon(x-w/2/world),lat(y+h/2/world),lon(x+w/2/world),lat(y-h/2/world)]
def specs():
    result=[]
    for z in range(5,11):
        de=z-1.15
        bbox=viewport(de-.5,1280,1280)
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
        for w,h in PROFILES.values():
            view=viewport(z,w,h);active=[]
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
        R.registrar_base_regional(s['name'],s['bbox'],s['z'],s['dataset'])
        layers.append(({'nome':s['name'],'de':s['de']},A.raster_info(s['name'])))
    validate_coverage(layers)
    ds=atlas_ref.datasets();rasters=[]
    for r,m in layers:
        f=A.RASTER_DIR/m['arquivo']
        if hashlib.sha256(f.read_bytes()).hexdigest()!=m['sha256'] or not ds[m['dataset']]['uso_comercial']:raise ValueError('E396-SOURCE')
        shutil.copyfile(f,PUBLIC/f.name)
        # Neutral dark wide map; retain actual orbital color in regional imagery.
        grade={'saturacao':-.91,'contraste':.12,'brilho_min':.06,'brilho_max':.65} if m['dataset']=='ne2_raster' else {'saturacao':-.25 if m['dataset']=='bmng' else -.08,'contraste':.12,'brilho_min':.02,'brilho_max':.94}
        rasters.append({**r,'dataset':m['dataset'],'src':'_formato/raster/'+f.name,'cantos':m['cantos'],'atribuicao':m['atribuicao'],'tipo':m['tipo'],'ajuste':grade})
    geo=json.loads(Path('motor4/formatos/dados/panama.topo.json').read_text())
    if not geo.get('topo',{}).get('objects',{}).get('rota') or 'Natural Earth' not in ' '.join(geo['meta']['atribuicao']):raise ValueError('E396-GEO')
    tokens=A.tokens_canal(A.canal('coringa'));tokens['palco']['mapa'].update(destaque='#D4473F',mar='#25292B')
    for name,(w,h) in PROFILES.items():
        cam=lambda z:{'foco':list(CENTER),'ancora':[w/2,h/2],'zoom':z}
        p={'neo_benchmark':True,'duracao':14,'formato':'atlas','tokens':tokens,'geo':geo,'rasters':rasters,
           'palco':[{'t':0,'tipo':'mapa','camera':cam(START),'veu':'nenhum','deriva':0},{'t':1,'tipo':'mapa','camera':cam(END),'dur_camera':9,'veu':'nenhum','deriva':0}],
           'camadas':[],'rotas':[{'t0':9.5,'t1':13.5,'cor':'destaque','largura':4}],
           'rotulos':[{'nome':'AMÉRICA CENTRAL','lonlat':[-88,15],'t0':0,'t1':3.5,'estilo':'area'},{'nome':'PANAMÁ','lonlat':[-79.77,9.14],'t0':4.8,'t1':9,'estilo':'area'}],
           'creditos':{'datasets':{k:v['atribuicao_exigida'] for k,v in ds.items() if v.get('atribuicao_exigida')},'obrigatorias':[k for k,v in ds.items() if v.get('obrigatoria')],'caixa':[20,h-76,w-40,64],'px':15,'linha':18},
           'seguro':{'esq':24,'topo':28,'base':h-85,'direita':[],'dir_max':w-24}}
        (ROOT/(name+'.json')).write_text(json.dumps({'map':p},ensure_ascii=False))
    (ROOT/'manifest.json').write_text(json.dumps({'publish':False,'review':'PENDING','route':'OSM Canal do Panamá; animação ilustrativa, não AIS','profiles':PROFILES,'coverage_frames':420,'sources':[m for r,m in layers],'reference':'Neo 0–34s, técnicas; sem material de terceiros no render'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
