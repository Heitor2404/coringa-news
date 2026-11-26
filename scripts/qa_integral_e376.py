"""Full private render of authenticated E348 editorial timeline with current renderer.
Assisted replay, not a newly researched or autonomous documentary."""
import json,subprocess,re,shutil
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_integracao_e345 as Q,qa_abertura_e339 as A
from src.v3.pacote_biblioteca import sha
from scripts.qa_fala_visual_e338 import read as archived
ROOT=Path('stage_documental/e348')
PUBLIC=Path('motor4/remotion/public')
def read(n):return json.loads((ROOT/n).read_text())
def write(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
def bind_atlas(p,current,old_receipt,new_receipt,public=PUBLIC):
    """Rebind the same geographic scene to its newly authenticated binary."""
    before=[s for s in p['shots'] if s['type']=='atlas_map']
    after=[s for s in current['shots'] if s['type']=='atlas_map']
    A.check(len(before)==len(after)==1,'E379-ATLAS-SCOPE')
    a,b=before[0],after[0]
    for key in ('id','type','start','end','headline','lead','atlas_direcao','direcao_evento','evidence','source','source_in_seconds','documentary_atlas_layout'):
        A.check(a.get(key)==b.get(key),'E379-ATLAS-IDENTITY '+key)
    for r,s in ((old_receipt,a),(new_receipt,b)):
        A.check(r.get('renderer')=='ATLAS/Formato/PalcoMapa/MapLibre' and r.get('status')=='PRONTO_PARA_REVISAO_HUMANA' and r.get('publicado') is False and r.get('aprovacao_humana')=='PENDENTE','E379-ATLAS-RECEIPT')
        A.check(r.get('fps')==30 and r.get('quadro_alvo')==[1080,1920] and r.get('documentary_layout') is True and abs(r['duracao_s']-(s['end']-s['start']))<.001 and r.get('quadros_decodificados')==round(r['duracao_s']*30),'E379-ATLAS-TIME')
        A.check(s.get('asset')=='film_editorial/'+r['video_sha256']+'.mp4','E379-ATLAS-HASH-LINK')
        A.check(r.get('quadros_reais') and r['mapeamento'].get('rasters_ativos'),'E379-ATLAS-EVIDENCE')
    for key in ('roi','beat','palco','rasters_ativos','origem_geografica'):
        A.check(old_receipt['mapeamento'].get(key)==new_receipt['mapeamento'].get(key),'E379-ATLAS-GEO '+key)
    f=public/b['asset']
    A.check(f.resolve().is_relative_to(public.resolve()) and f.is_file() and sha(f)==new_receipt['video_sha256'] and f.stat().st_size==new_receipt['video_bytes'],'E379-ATLAS-BYTES')
    previous=a['asset'];a['asset']=b['asset']
    return dict(shot=a['id'],old_asset=previous,new_asset=a['asset'],old_atlas_sha256=old_receipt['atlas_sha256'],new_atlas_sha256=new_receipt['atlas_sha256'],frames=new_receipt['quadros_decodificados'],editorial_review='PENDING')

def restore_exact_asset(name,records,public=PUBLIC):
    """Restore a missing historical shot only from verified local source bytes."""
    f=public/name
    A.check(f.resolve().is_relative_to(public.resolve()) and re.fullmatch(r'[a-f0-9]{64}',f.stem) is not None,'E379-ASSET-PATH '+name)
    if f.is_file():
        A.check(sha(f)==f.stem,'E376-SHA '+name)
        return False
    A.check(f.parent==public/'film_editorial','E379-RESTORE-SCOPE '+name)
    matches=[m for m in records if m.get('expected_sha256')==f.stem and m.get('local_source')]
    for m in matches:
        src=Path(m['local_source'])
        if not src.resolve().is_relative_to(Path('stage_documental').resolve()) or not src.is_file() or src.suffix.lower()!=f.suffix.lower():continue
        A.check(sha(src)==f.stem,'E379-SOURCE-SHA '+name)
        f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,f)
        A.check(sha(f)==f.stem,'E379-COPY-SHA '+name)
        return True
    raise ValueError('E376-MISSING '+name)

def main():
    p=read('props-candidate.json');proof=read('proof.json')
    A.check(p.get('private_review_only') is True and p.get('preview') is True,'E376-PRIVATE')
    A.check(proof['total_frames']>=1800 and Q.video_frames(ROOT/'filme.mp4')==proof['total_frames'],'E376-FRAMES')
    A.check(Q.audio_packets(ROOT/'filme.mp4')[0]==proof['audio_packet_fingerprint'],'E376-AUDIO')
    old=json.loads(Path('qa_e289/props.json').read_text())
    A.check([w for g in p['documentary_captions'] for w in g['words']]==[w for g in old['documentary_captions'] for w in g['words']],'E376-CAPTIONS')
    new_receipt=json.loads(Path('qa_e289/comprovante_atlas.json').read_text())
    binding=bind_atlas(p,old,archived('comprovante_atlas.json'),new_receipt)
    current_plan=json.loads(Path('qa_e289/plano.json').read_text())
    current_acervo=json.loads(Path('qa_e289/acervo-restaurado.json').read_text())
    A.check(current_plan.get('publicar') is False and current_acervo.get('publish') is False,'E379-PRIVATE-SOURCES')
    records=[*current_plan['media'].values(),*current_acervo['acquired'].values(),*archived('plano.json')['media'].values()]
    assets=[];restored=[]
    for shot in p['shots']:
        for key in ('asset','assetB','reference_asset'):
            name=shot.get(key)
            if not name:continue
            if restore_exact_asset(name,records):restored.append(name)
            assets.append(name)
    name=p['scene_narration_asset']
    A.check(not restore_exact_asset(name,[]),'E379-AUDIO-RESTORE')
    assets.append(name)
    write('props-candidate.json',p)
    write('integral-audit.json',dict(status='READY_PRIVATE',publish=False,semantic_approval=False,visual_approval=False,route='ASSISTED_E348_REPLAY_CURRENT_RENDERER',
       new_ai=0,new_tts=0,total_frames=proof['total_frames'],duration_s=proof['total_frames']/30,source_assets=sorted(set(assets)),shots=len(p['shots']),atlas_binding=binding,restored_assets=restored))
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
