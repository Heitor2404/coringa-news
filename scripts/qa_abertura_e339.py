"""E339: same measured opening, two source changes, no fresh AI or full render."""
import hashlib,json,subprocess,shutil
from pathlib import Path
from PIL import Image,ImageDraw
from scripts.recuperar_checkpoints_documentais import api,listar_releases,REPO
from scripts.qa_fala_visual_e338 import read as archived
from scripts.qa_documentario_geografia_e219 import frame,probe
from src.v3.pacote_biblioteca import sha
from src.v4.formatos.auditoria_fala_visual_e338 import organizar
from src.v4.formatos.reedicao_fala_e339 import edit
ROOT=Path('stage_documental/e339')
FILM='review-e326-45870900796-1'
BASE='review-e287-45685353176-1'
PHOTO='review-e320-45860199613-1'
END=260/30
def write(name,v): (ROOT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2))
def read(name):return json.loads((ROOT/name).read_text())
def check(ok,reason):
    if not ok:raise ValueError(reason)
def ff(*args):subprocess.run(['ffmpeg','-v','error','-y',*map(str,args)],check=True,timeout=120)
def download(releases,tag,name,folder,expected,limit):
    rel=releases[tag];check(rel['draft'] is True,'E339-RELEASE')
    a=next(a for a in rel['assets'] if a['name']==name)
    check(a['digest']=='sha256:'+expected and 0<a['size']<=limit,'E339-ASSET-META')
    folder.mkdir(parents=True,exist_ok=True);p=folder/name
    if not p.exists():subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',name,'--dir',str(folder)],check=True,timeout=300)
    check(p.stat().st_size==a['size'] and sha(p)==expected,'E339-SHA')
    return p
def prepare():
    ROOT.mkdir(parents=True,exist_ok=False)
    m=api('');check(m['private'] is True and m['id']==1454059520,'E339-COFRE')
    releases={r['tag_name']:r for r in listar_releases(100)}
    original=download(releases,FILM,'filme.mp4',ROOT,'e188c4f7b91e426d71f6ff3c6e331f8a79243342d7ca67128c28f20f65a20aba',30_000_000)
    download(releases,FILM,'props.json',ROOT,'db2c33f187531841197128775668fb3c3843d9e19fe84422a302a23157ee9c55',100_000)
    p=read('props.json');plan=archived('plano.json');q=organizar(plan,archived('obrigacoes-visuais.json'))
    variant,rows=edit(p,q,{'c0-0':{'donor':'c4-2','lead':'LAVA E OCEANO'},'c0-1':{'donor':'c4-3','lead':'BAÍA DE KAPOHO'}},END)
    public=Path('motor4/remotion/public')
    for s,r in zip(variant['shots'],rows,strict=True):
        name=Path(s['asset']).name
        # E326 plan retains the original source metadata, not a new receipt.
        med=next(x for x in plan['media'].values() if x['expected_sha256']==r['source_sha256'])
        check(med['license']=='Public domain' and med['page'].startswith('https://www.usgs.gov/media/'),'E339-RECEIPT')
        f=download(releases,PHOTO if s['type']=='photo' else BASE,name,public/'film_editorial',r['source_sha256'],250_000_000)
        if s['type']=='video':
            w,h,d=probe(f);check([w,h]==s['source_dimensions'] and r['source_out']<=d,'E339-PROBE')
            r['samples']=[{'t':t,'sha256_pixels':hashlib.sha256(frame(f,t,width=768).tobytes()).hexdigest()} for t in (r['source_in']+.1,(r['source_in']+r['source_out'])/2,r['source_out']-.1)]
        else:
            with Image.open(f) as im:check(list(im.size)==s['source_dimensions'],'E339-PHOTO-DIM')
        r['rights_status']='REVIEW_PENDING'
    # Re-use the already rendered mix from the exact original film. A/B uses
    # the same decoded 48kHz audio input; no claim of sample equality after AAC.
    audio=ROOT/'same-mix.wav'
    ff('-i',original,'-vn','-t',END,'-ar',48000,'-c:a','pcm_s16le',audio)
    name=sha(audio)+'.wav';(public/'e202').mkdir(exist_ok=True);shutil.copyfile(audio,public/'e202'/name)
    variant['scene_narration_asset']='e202/'+name
    write('variant.json',variant)
    ff('-i',original,'-t',END,'-map','0:v:0','-map','0:a:0','-c:v','libx264','-crf',20,'-c:a','aac',ROOT/'baseline.mp4')
    write('comparison.json',{'publish':False,'semantic_approval':False,'full_documentary':False,'new_ai':0,'new_tts':0,'duration_s':END,'audio_input_sha256':sha(audio),'original_film_sha256':sha(original),'changes':rows,'status':'PREPARED_PRIVATE'})
def finish():
    r=read('comparison.json');files=[ROOT/'baseline.mp4',ROOT/'variant.mp4'];items=[]
    for f in files:
        w,h,d=probe(f);check((w,h)==(540,960) and abs(d-END)<.15,'E339-RENDER')
        items.append({'file':f.name,'sha256':sha(f),'duration_s':d,'dimensions':[w,h]})
    for i,t in enumerate((.5,2.2,3.6,5.5,7.4)):
        sheet=Image.new('RGB',(540,504),'#111111');draw=ImageDraw.Draw(sheet)
        for j,f in enumerate(files):
            im=frame(f,t,width=270);sheet.paste(im,(270*j,24));draw.text((270*j+6,5),f'{f.stem} {t:.1f}s',fill='white')
        sheet.save(ROOT/f'pair-{i}.jpg',quality=90)
    r.update(status='RENDERED_PRIVATE_COMPARISON',videos=items,editorial_review='PENDING',audio_output_equality_verified=False)
    write('comparison.json',r);print('E339',items,flush=True)
if __name__=='__main__':
    import sys
    (finish if '--finish' in sys.argv else prepare)()
