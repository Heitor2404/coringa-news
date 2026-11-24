"""Regional Blue Marble proof with the EXISTING ATLAS renderer; no TTS.
Generated rasters remain in the ephemeral runner and have a source manifest.
"""
import hashlib,json,math,subprocess
from pathlib import Path
from scripts import formatos_raster as R
from scripts import qa_documentario_geografia_e219 as E

def regional_base(name,bbox,z):
    # Existing NASA GIBS source and existing registered commercial-use dataset.
    if not 4<=z<=8:raise ValueError('zoom fora do produto NASA')
    x0,y0=R.tile_xy(bbox[0],bbox[3],z)
    x1,y1=R.tile_xy(bbox[2],bbox[1],z)
    if (int(x1)-int(x0)+1)*(int(y1)-int(y0)+1)>100:
        raise ValueError('região de teste excede orçamento de tiles')
    im,corners=R.mosaico(R.BMNG_BATI,bbox,z,'RGB')
    out=E.A.RASTER_DIR;out.mkdir(parents=True,exist_ok=True)
    img=out/(name+'.jpg')
    im.save(img,quality=94)
    meta={'nome':name,'tipo':'satelite','cantos':corners,'px':list(im.size),
          'px_por_grau_fonte':256*2**z/360,'arquivo':img.name,'dataset':'bmng',
          'atribuicao':'Imagem: NASA Blue Marble',
          'fonte':{'url':R.BMNG_BATI,'licenca':'Domínio público (NASA)','zoom_tiles':z,'bbox_pedido':bbox},
          'sha256':E.sha(img)}
    E.write(out/(name+'.json'),meta)
    return meta

def main():
    out=Path('qa_atlas_regional');out.mkdir(exist_ok=True)
    # Canonical longitude avoids ambiguous wide-world image geometry.
    meta=regional_base('bmng_regional_havai',[-162,14,-150,26],7)
    ch={'title':'Oceano Pacífico','atlas':{'roi':[-156.3,18.8,-154.4,20.4],
        'label':'Ilha do Havaí','lonlat':[-155.5,19.6],'raster':meta['nome']}}
    E.MAP=out
    clip,proof=E.mapclip(ch,5.5)
    # Compare the actual geographic viewport away from labels, not global
    # frame variance which can be satisfied by text on an empty background.
    from PIL import Image
    import io
    import numpy as np
    img=Image.open(io.BytesIO(subprocess.check_output(['ffmpeg','-v','error','-ss','2.2','-i',str(clip),
        '-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1']))).convert('RGB')
    arr=np.asarray(img,dtype=float)
    region=arr[450:1100,100:900]
    color=region.max(axis=2)-region.min(axis=2)
    report={'regional_color_fraction':float((color>20).mean()),
            'regional_luminance_std':float(region.mean(axis=2).std()),'visual_approval':'PENDING',
            'source':meta,'note':'Pixel diagnostics only; not proof that island is correctly visible.'}
    E.write(out/'regional_pixels.json',report)
    print('REGIONAL PIXELS',report['regional_color_fraction'],report['regional_luminance_std'],flush=True)
    img.save(out/'quadro.png')
if __name__=='__main__':main()
