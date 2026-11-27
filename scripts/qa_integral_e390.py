"""E390: consolidate the approved visual baseline, full compositor render.
Historical E376 preparation is only a source/ATLAS restoration dependency.
No old-film pixels are used as video input in the new composition."""
import copy,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_integral_e376 as I,qa_abertura_e339 as A,qa_integracao_e345 as Q
from scripts import qa_motion_e3885 as speed,qa_motion_e3887 as areas
from scripts.qa_fala_visual_e338 import read as archived
from src.v3.pacote_biblioteca import sha
ROOT=Path('stage_documental/e390')
PUBLIC=Path('motor4/remotion/public')
def write(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
def read(n):return json.loads((ROOT/n).read_text())
def prepare():
    ROOT.mkdir(parents=True,exist_ok=True)
    original=I.read('props-candidate.json');audit=I.read('integral-audit.json')
    A.check(audit['status']=='READY_PRIVATE' and audit['atlas_binding'] and audit['total_frames']==2492,'E390-ATLAS-AUTHENTICATED')
    A.check(original['preview'] is True and original['private_review_only'] is True and original['documentary_caption_origin']=='PALAVRAS_MEDIDAS','E390-PRIVATE')
    speed.main();areas.main()
    speed_chart=json.loads((speed.ROOT/'c3-2.json').read_text())['shots'][0]
    area_charts=json.loads((areas.ROOT/'pair.json').read_text())['shots']
    replacements={s['id']:s for s in [speed_chart,*area_charts]}
    A.check(set(replacements)=={'c3-2','c6-0','c6-1'},'E390-THREE-GRAPHS')
    p=copy.deepcopy(original);p['documentary_text_probe']=False
    records={m['expected_sha256']:m for m in archived('plano.json')['media'].values() if m.get('expected_sha256')}
    attribution=[];routes=[]
    for i,s in enumerate(p['shots']):
        before=original['shots'][i]
        if s['id'] in replacements:
            chart=copy.deepcopy(replacements[s['id']]);chart.update(start=s['start'],end=s['end'])
            # Preserve the literal source in the pre-anchor context and the
            # preceding/adjacent original evidence. Never relabel source.
            if s['id']=='c3-2':
                h=Path(s['asset']).stem
                chart['documentary_chart_context']={'schema':'coringa.motion.context.private.v1','publish':False,'asset':s['asset'],'sha256':h,'kind':s['type'],'sourceIn':s.get('source_in_seconds',0),'credit':s.get('source_display') or s['source']}
            A.check(chart['documentary_chart_context']['asset']==s['asset'],'E390-CONTEXT')
            p['shots'][i]=chart;route='APPROVED_NARRATED_GRAPH'
        elif s['type']=='atlas_map':
            route='AUTHENTICATED_ATLAS'
        elif s['type'] in ('photo','video'):
            s['documentary_taiwan_typography_trial']=True
            if s.get('documentary_static_reveal') or s.get('documentary_comparison_panel'):
                route='PROTECTED_DETAIL_CURRENT_TYPOGRAPHY'
            else:
                credit=s.get('source_display') or s['source']
                s['documentary_clean_credit']={'placement':'POST_DESCRIPTION','private_only':True,'credit':credit}
                if s.get('evidence')=='representative':s['documentary_clean_credit']['context_label']='CONTEXTO'
                s['documentary_overlay_trial']=60
                route='TAIWAN_CURRENT_OVERLAY'
        else:raise ValueError('E390-UNKNOWN-ROUTE '+s['id'])
        h=Path(before['asset']).stem
        src=PUBLIC/before['asset']
        A.check(src.is_file() and sha(src)==h,'E390-ASSET '+before['id'])
        attribution.append({'id':before['id'],'asset':before['asset'],'source':before.get('source'),'source_display':before.get('source_display'),'evidence':before['evidence'],'archived_source_record':records.get(h),'rights_status':'REVIEW_PENDING','route':route})
        routes.append({'id':before['id'],'route':route,'start':before['start'],'end':before['end'],'original_asset':before['asset']})
    A.check(p['duracao']==original['duracao'] and p['documentary_captions']==original['documentary_captions'] and p['scene_narration_asset']==original['scene_narration_asset'],'E390-TIMELINE')
    A.check(all((s['id'],s['start'],s['end'])==(t['id'],t['start'],t['end']) for s,t in zip(p['shots'],original['shots'],strict=True)),'E390-SHOTS')
    A.check(all(p['shots'][i]==s or s['id'] in replacements or all(p['shots'][i].get(k)==v for k,v in s.items()) for i,s in enumerate(original['shots'])),'E390-ORIGINAL-PROTECTION')
    write('props-current.json',p)
    write('attribution-manifest.json',{'publish':False,'rights_approved':False,'items':attribution})
    write('consolidation.json',{'schema':'coringa.current.documentary.private.v1','publish':False,'status':'PREPARED','old_visual_model_retired':True,'fresh_full_render':False,'routes':routes,'total_frames':2492,'duration_s':p['duracao'],'atlas_binding':audit['atlas_binding'],'editorial_review':'PENDING','autonomous_acquisition_proven':False,'causal_2d_approved':False})
def finish():
    proof=read('consolidation.json');qa=read('review.json');p=read('props-current.json')
    A.check(not qa['errors'] and len(qa['shots'])==len(p['shots'])==24,'E390-VISUAL-QA')
    base=I.ROOT/'filme.mp4';raw=ROOT/'current-render.mp4';out=ROOT/'CORINGA-EXPLICA-KILAUEA-ATUAL-E390.mp4'
    A.check(Q.video_frames(raw)==proof['total_frames'],'E390-ALL-FRAMES')
    A.ff('-i',raw,'-i',base,'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',out)
    A.check(Q.video_frames(out)==proof['total_frames'] and Q.audio_packets(base)==Q.audio_packets(out),'E390-AUDIO')
    for i in range(0,len(p['shots']),4):
        batch=p['shots'][i:i+4];board=Image.new('RGB',(810,504*len(batch)),'#111111');d=ImageDraw.Draw(board)
        for k,s in enumerate(batch):
            for j,f in enumerate((.18,.5,.82)):
                t=s['start']+(s['end']-s['start'])*f
                board.paste(A.frame(out,t,width=270),(270*j,504*k+24));d.text((270*j+4,504*k+4),f"{s['id']} {f:.2f}",fill='white')
        board.save(ROOT/f'current-contact-{i//4:02d}.jpg',quality=88)
    proof.update(status='RENDERED_CURRENT_PRIVATE',fresh_full_render=True,audio_packets_identical=True,sha256=sha(out),bytes=out.stat().st_size,rendered_shots=len(p['shots']))
    write('consolidation.json',proof)
if __name__=='__main__':
    import sys
    (finish if '--finish' in sys.argv else prepare)()
