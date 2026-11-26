"""Full private render of authenticated E348 editorial timeline with current renderer.
Assisted replay, not a newly researched or autonomous documentary."""
import json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_integracao_e345 as Q,qa_abertura_e339 as A
from src.v3.pacote_biblioteca import sha
ROOT=Path('stage_documental/e348')
PUBLIC=Path('motor4/remotion/public')
def read(n):return json.loads((ROOT/n).read_text())
def write(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
def main():
    p=read('props-candidate.json');proof=read('proof.json')
    A.check(p.get('private_review_only') is True and p.get('preview') is True,'E376-PRIVATE')
    A.check(proof['total_frames']>=1800 and Q.video_frames(ROOT/'filme.mp4')==proof['total_frames'],'E376-FRAMES')
    A.check(Q.audio_packets(ROOT/'filme.mp4')[0]==proof['audio_packet_fingerprint'],'E376-AUDIO')
    old=json.loads(Path('qa_e289/props.json').read_text())
    A.check([w for g in p['documentary_captions'] for w in g['words']]==[w for g in old['documentary_captions'] for w in g['words']],'E376-CAPTIONS')
    assets=[]
    for shot in p['shots']:
        name=shot.get('asset')
        if not name:continue
        f=PUBLIC/name
        A.check(f.resolve().is_relative_to(PUBLIC.resolve()) and f.is_file(),'E376-MISSING '+name)
        # Content-addressed originals are validated before render.
        h=f.stem
        if len(h)==64:A.check(sha(f)==h,'E376-SHA '+name)
        assets.append(name)
    write('integral-audit.json',dict(status='READY_PRIVATE',publish=False,semantic_approval=False,visual_approval=False,route='ASSISTED_E348_REPLAY_CURRENT_RENDERER',
       new_ai=0,new_tts=0,total_frames=proof['total_frames'],duration_s=proof['total_frames']/30,source_assets=sorted(set(assets)),shots=len(p['shots'])))
def finish():
    p=read('props-candidate.json');proof=read('proof.json');audit=read('integral-audit.json')
    base=ROOT/'filme.mp4';raw=ROOT/'filme-render.mp4';out=ROOT/'filme-integral-preto.mp4'
    A.check(Q.video_frames(raw)==proof['total_frames'],'E376-RAW-FRAMES')
    A.ff('-i',raw,'-i',base,'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',out)
    A.check(Q.video_frames(out)==proof['total_frames'] and Q.audio_packets(base)==Q.audio_packets(out),'E376-MUX')
    rows=[]
    for shot in p['shots']:
        a,b=shot['start'],shot['end']
        images=[A.frame(out,a+(b-a)*f,width=270) for f in (.18,.5,.82)]
        rows.append((shot,images))
    for i in range(0,len(rows),3):
        batch=rows[i:i+3];board=Image.new('RGB',(810,504*len(batch)),'#111111');d=ImageDraw.Draw(board)
        for k,(s,ims) in enumerate(batch):
            for j,im in enumerate(ims):
                board.paste(im,(270*j,504*k+24))
                d.text((270*j+4,504*k+4),f"{s['id']} {s['type']} {(.18,.5,.82)[j]:.2f}",fill='white')
        board.save(ROOT/f'integral-contato-{i//3:02d}.jpg',quality=87)
    audit.update(status='RENDERED_PRIVATE_FULL',sha256=sha(out),bytes=out.stat().st_size,audio_packets_identical=True,
        source_rights_review='PENDING',ui_review='PENDING',full_documentary=True,autonomous_acquisition_proven=False,
        composition_dimensions=[540,960],rendered_shots=len(rows))
    write('integral-audit.json',audit)
    print('E376_FULL',audit['duration_s'],audit['rendered_shots'],audit['audio_packets_identical'],flush=True)
if __name__=='__main__':
    import sys
    (finish if '--finish' in sys.argv else main)()
