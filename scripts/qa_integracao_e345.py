"""E345: preserve baseline frames except local rerenders; copy original audio packets."""
import json,subprocess,shutil,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_abertura_e339 as A
from scripts.qa_fala_visual_e338 import read as archived
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v3.pacote_biblioteca import sha
from src.v4.formatos.auditoria_fala_visual_e338 import organizar
from src.v4.formatos.integracao_incremental_e343 import integrar
ROOT=Path('stage_documental/e345')
def write(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
def read(n):return json.loads((ROOT/n).read_text())
def check(v,msg):A.check(v,msg)
def probe(p,args):
    return json.loads(subprocess.check_output(['ffprobe','-v','error',*args,'-of','json',str(p)],timeout=120))
def video_frames(p):
    s=probe(p,['-select_streams','v:0','-count_frames','-show_streams'])['streams'][0]
    check(s['r_frame_rate']=='30/1' and (s['width'],s['height'])==(540,960),'E345-VIDEO-FORMAT')
    return int(s['nb_read_frames'])
def audio_packets(p):
    packets=probe(p,['-select_streams','a:0','-show_packets','-show_data_hash','sha256'])['packets']
    check(bool(packets) and all(x.get('data_hash') for x in packets),'E345-AUDIO-PACKETS')
    return hashlib.sha256(json.dumps([(x['data_hash'],x.get('pts_time'),x.get('duration_time')) for x in packets],separators=(',',':')).encode()).hexdigest(),len(packets)

def prepare():
    ROOT.mkdir(parents=True,exist_ok=False);m=api('');check(m['private'] is True and m['id']==1454059520,'E345-COFRE')
    rel={r['tag_name']:r for r in listar_releases(100)}
    original=A.download(rel,A.FILM,'filme.mp4',ROOT,'e188c4f7b91e426d71f6ff3c6e331f8a79243342d7ca67128c28f20f65a20aba',30_000_000)
    p=json.loads(A.download(rel,A.FILM,'props.json',ROOT,'db2c33f187531841197128775668fb3c3843d9e19fe84422a302a23157ee9c55',100_000).read_text())
    n=json.loads(A.download(rel,A.FILM,'narracao.json',ROOT,'19ed0d467b16de361c2c9e378ac162729f8ff79fad9fdc3ac1c51fa46b766a0d',100_000).read_text())
    plan=archived('plano.json');q=organizar(plan,archived('obrigacoes-visuais.json'))
    config=json.loads(Path('benchmarks/e345/integracao.json').read_text());data=json.loads(Path('benchmarks/e342/dados.json').read_text())
    check(data['publish'] is False,'E345-DATA')
    out,proof=integrar(p,q,n['words'],config,data['entries'])
    check(video_frames(original)==proof['total_frames'],'E345-BASE-FRAMES')
    proof.update(status='PREPARED_PRIVATE',new_ai=0,new_tts=0,original_film_sha256=sha(original),audio_packet_fingerprint=audio_packets(original)[0])
    public=Path('motor4/remotion/public');changed=set(proof['changed_shots'])
    # Keep complete props/timeline so absolute caption times and progress bar
    # match the original. Restore only assets used in changed frame ranges.
    for s in out['shots']:
        if s['id'] not in changed:continue
        name=Path(s['asset']).name;h=name.split('.')[0]
        med=next(x for x in plan['media'].values() if x.get('expected_sha256')==h)
        check(med['license']=='Public domain' and med['page'].startswith('https://www.usgs.gov/media/'),'E345-RECEIPT')
        tags=[A.BASE,A.PHOTO,'review-e323-45864804065-1']
        tag=next(t for t in tags if any(x['name']==name for x in rel[t]['assets']))
        f=A.download(rel,tag,name,public/'film_editorial',h,250_000_000)
        if s['type']=='video':
            w,hh,d=A.probe(f);check([w,hh]==s['source_dimensions'] and s['source_in_seconds']+s['end']-s['start']<=d,'E345-WINDOW')
        else:
            with Image.open(f) as im:check(list(im.size)==s['source_dimensions'],'E345-PHOTO')
    # Renderer receives measured captions and original mix, but fragments
    # are muted. Final MP4 copies the original AAC stream, no audio synthesis.
    mix=ROOT/'original-mix.wav';A.ff('-i',original,'-vn','-ar',48000,'-c:a','pcm_s16le',mix)
    name=sha(mix)+'.wav';(public/'e202').mkdir(exist_ok=True);shutil.copyfile(mix,public/'e202'/name)
    out['scene_narration_asset']='e202/'+name
    out['documentary_text_probe']=False
    write('props-candidate.json',out);write('proof.json',proof)

def finish():
    proof=read('proof.json');base=ROOT/'filme.mp4';dest=ROOT/'filme-integrado.mp4'
    args=['-i',str(base)];filters=[];labels=[];i=0
    for j,r in enumerate(proof['parts']):
        if r['changed']:
            f=ROOT/f'fragment-{j}.mp4';check(video_frames(f)==r['end']-r['start'],'E345-FRAGMENT-FRAMES')
            args+=['-i',str(f)];i+=1
            src=f'[{i}:v]';trim=f'trim=end_frame={r["end"]-r["start"]}'
        else:src='[0:v]';trim=f'trim=start_frame={r["start"]}:end_frame={r["end"]}'
        filters.append(f'{src}{trim},setpts=PTS-STARTPTS[v{j}]');labels.append(f'[v{j}]')
    filters.append(''.join(labels)+f'concat=n={len(labels)}:v=1:a=0[v]')
    A.ff(*args,'-filter_complex',';'.join(filters),'-map','[v]','-map','0:a:0','-c:v','libx264','-crf',20,'-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',dest)
    check(video_frames(dest)==proof['total_frames'],'E345-FINAL-FRAMES')
    check(audio_packets(base)==audio_packets(dest),'E345-AUDIO-NOT-IDENTICAL')
    p=read('props-candidate.json');rows=[]
    for s in p['shots']:
        t=(s['start']+s['end'])/2;im=A.frame(dest,t,width=270);rows.append((s['id'],t,im))
    for i in range(0,len(rows),3):
        batch=rows[i:i+3];board=Image.new('RGB',(810,504),'#111111');d=ImageDraw.Draw(board)
        for k,(sid,t,im) in enumerate(batch):board.paste(im,(270*k,24));d.text((270*k+5,5),f'{sid} {t:.1f}s',fill='white')
        board.save(ROOT/f'filme-contato-{i//3:02d}.jpg',quality=88)
    times=[.5,2.2,3.6,34.5,56.7,66.3,73.53]
    for i,t in enumerate(times):
        board=Image.new('RGB',(540,504),'#111111');d=ImageDraw.Draw(board)
        for k,f in enumerate((base,dest)):board.paste(A.frame(f,t,width=270),(270*k,24));d.text((270*k+5,5),f'{"base" if k==0 else "novo"} {t:.2f}s',fill='white')
        board.save(ROOT/f'pair-{i}.jpg',quality=90)
    proof.update(status='RENDERED_PRIVATE_INTEGRAL',duration_s=proof['total_frames']/30,final_sha256=sha(dest),audio_packets_identical=True,unmodified_scene_content_reused=True,unmodified_pixels_bit_identical=False,rights_review='PENDING',ui_review='PENDING')
    write('proof.json',proof);print('E345',proof['total_frames'],proof['changed_shots'],proof['audio_packets_identical'],flush=True)
if __name__=='__main__':
    import sys
    (finish if '--finish' in sys.argv else prepare)()
