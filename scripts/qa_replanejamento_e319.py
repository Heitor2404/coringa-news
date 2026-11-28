"""E319: bounded, private replan from verified originals and exact E318 obligations.
No new origin downloads, AI, or automatic semantic approval.
"""
import json, math, hashlib, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.recuperar_checkpoints_documentais import api,listar_releases,REPO
from scripts.qa_documentario_geografia_e219 import frame,probe,sha
from scripts.restaurar_piloto_e289 import validar_acervo

def alternatives(duration,span,reserved,limit=5):
    if not all(math.isfinite(x) for x in (duration,span)) or span<1.4 or duration<span:return []
    end=duration-span-.15
    if end<0:return []
    # Coverage throughout the original, not repeated early grid windows.
    candidates=sorted({round(end*f,2) for f in (0,.12,.26,.4,.55,.7,.85,1)})
    free=[t for t in candidates if not any(t<b and t+span>a for a,b in reserved)]
    if len(free)<=limit:return free
    return [free[round(i*(len(free)-1)/(limit-1))] for i in range(limit)]

def main():
    root=Path('stage_documental/e319');root.mkdir(parents=True,exist_ok=True)
    meta=api('')
    if meta.get('private') is not True or meta.get('id')!=1454059520:raise ValueError('E319-COFRE')
    releases={r['tag_name']:r for r in listar_releases(100) if r.get('draft') is True}
    original='review-e287-45685353176-1';proof='review-e318-45852963938-1'
    def download(tag,name,limit):
        a=next(a for a in releases[tag]['assets'] if a['name']==name)
        if not 0<a['size']<=limit:raise ValueError('E319-LIMITE')
        folder=root/tag;folder.mkdir(exist_ok=True);p=folder/name
        subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',name,'--dir',str(folder)],check=True,timeout=300)
        if p.stat().st_size!=a['size'] or a.get('digest')!='sha256:'+sha(p):raise ValueError('E319-SHA')
        return p
    acervo=json.loads(download(original,'acervo.json',2_000_000).read_text())
    obligations=json.loads(download(proof,'obrigacoes-visuais.json',2_000_000).read_text())
    if acervo['publish'] is not False or obligations['publish'] is not False:raise ValueError('E319-PRIVADO')
    selected_ids=[
        'kilauea-volcano-kapoho-bay','kilauea-volcano-video-compilation-kapoho-bay-ocean-entry',
        'kilauea-volcano-video-compilation-lower-east-rift-zone','kilauea-lower-east-rift-zone',
        'kilauea-volcano-ocean-entry-kapoho-bay','july-14-2018-kilauea-fissure-8-video-captured-uas',
    ]
    rows=[];sources=[]
    for i,ident in enumerate(selected_ids):
        m=acervo['acquired'][ident];h=m['expected_sha256']
        p=download(original,h+'.mp4',250_000_000)
        verified,_=validar_acervo({'publish':False,'acquired':{ident:m}},[(ident,m['label'])],p.parent)
        m=verified[ident]
        spans=[(o['source_in'],o['source_out']) for o in obligations['shots'] if o['source_sha256']==h]
        starts=alternatives(m['duration_s'],3.8,spans)
        if not starts:continue
        board=Image.new('RGB',(960,205*len(starts)),'#191919');draw=ImageDraw.Draw(board)
        for k,t in enumerate(starts):
            samples=[]
            for j,f in enumerate((.12,.5,.86)):
                at=t+3.8*f;im=frame(p,at,width=320)
                samples.append({'time':at,'pixels_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'size':list(im.size)})
                draw.text((j*320+5,k*205+4),f'{ident[:18]} {at:.2f}s',fill='white')
                im.thumbnail((320,180));board.paste(im,(j*320,k*205+22))
            rows.append({'source':ident,'sha256':h,'window_start':t,'window_duration':3.8,'samples':samples,'status':'REVIEW_REQUIRED'})
        name=f'fonte-{i:02d}.jpg';board.save(root/name,quality=88)
        sources.append({'source':ident,'sha256':h,'page':m['page'],'label':m['label'],'sheet':name,'reserved':spans})
    report={'publish':False,'assisted':True,'new_ai':0,'sources':sources,'windows':rows,
            'target_obligations':[o for o in obligations['shots'] if o['shot'] in ('c3-2','c3-3','c4-3','c6-0','c6-1','c6-2','c6-3')],
            'semantic_approval':False}
    (root/'replanejamento.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    assert rows
    print('E319_JANELAS_PARA_REVISAO',len(rows),flush=True)

if __name__=='__main__':main()
