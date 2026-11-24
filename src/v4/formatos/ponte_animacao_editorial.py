"""E213 — common private bridge for registered animation assets, no new mechanism geometry."""
from __future__ import annotations
import hashlib
import json
import math
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from . import politica_animacao as PA

SCHEMA='coringa.animation.clip.private.v1'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def verificar(renderer, src):
    entry=PA.POLICY['external_candidates'].get(renderer,{})
    p=Path(src)
    if entry.get('status')!='CANDIDATO' or not p.is_file() or p.is_symlink():
        raise ValueError('E213-ORIGEM')
    digest=sha(p)
    if digest!=entry.get('reference_sha256'):
        raise ValueError('E213-HASH')
    r=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(p)]))
    ss=r['streams']
    if len(ss)!=1 or ss[0]['codec_type']!='video':
        raise ValueError('E213-STREAMS')
    s=ss[0]
    n=int(s['nb_read_frames']); fps=Fraction(s['avg_frame_rate'])
    if n!=entry['frames'] or fps!=entry['fps'] or [s['width'],s['height']]!=entry['dimensions'] or s['width']*16!=s['height']*9:
        raise ValueError('E213-FORMATO')
    return {'schema':SCHEMA,'renderer':renderer,'sha256':digest,'run':entry['reference_run'],
            'frames':n,'fps':float(fps),'dimensions':entry['dimensions'],'duration_s':float(n/fps),
            'status':'CANDIDATO','publish':False,'viewport':'INTEGRAL_SEM_CROP',
            'geometry_approval':'PENDENTE','source':entry['source']}

def preparar(renderer,src,public_root,*,cid,acao,lacuna,motivo_lacuna,midia_adequada,start=0.):
    # A missing file is not a licence to use animation. This is a private
    # review route for a specific explanatory need, not a production approval.
    if PA.decidir_complemento(midia_adequada=midia_adequada,acao=acao,lacuna=lacuna,
            motivo_lacuna=motivo_lacuna,renderer='animation_clip:'+SCHEMA)!='ANIMACAO_COMPLEMENTAR_EM_QA_PRIVADA':
        raise ValueError('E213-SEM-NECESSIDADE')
    if not math.isfinite(start) or start<0 or abs(start*30-round(start*30))>1e-6:
        raise ValueError('E213-INICIO-FRAME')
    proof=verificar(renderer,src)
    asset='animation_e213/'+proof['sha256']+'.mp4'
    root=Path(public_root).resolve(); dst=(root/asset).resolve()
    if not dst.is_relative_to(root):
        raise ValueError('E213-CAMINHO')
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    if sha(dst)!=proof['sha256']:
        raise ValueError('E213-COPIA')
    proof.update(acao=acao,lacuna=lacuna,motivo_lacuna=motivo_lacuna,midia_adequada=False)
    end=(round(start*30)+math.ceil(proof['duration_s']*30-1e-8))/30
    entry=PA.POLICY['external_candidates'][renderer]
    shot={'id':cid,'type':'animation_clip','start':start,'end':end,'asset':asset,
          'animation_proof':proof,'evidence':'explainer','source':entry['source'],
          'source_display':entry['credit'],'lead':'Ilustração explicativa',
          'headline':acao,'subject':acao,'cues':[]}
    PA.exigir([shot],privado=True)
    return shot

def inserir(props, shot, pos, public_root):
    """Insert a verified clip between existing documentary scenes, never replace
    a real scene automatically, preserve source-in times and avoid compressing action."""
    if props.get('preview') is not True or props.get('animation_policy_mode')==PA.LEGACY:
        raise ValueError('E213-PRIVADO')
    if any(props.get(k) for k in ('scene_narration_asset','cad_narration_asset','documentary_captions')):
        raise ValueError('E213-RETIMAR-VOZ-PRIMEIRO')
    ss=props['shots']
    if not 0<=pos<=len(ss) or any(s['id']==shot['id'] for s in ss):
        raise ValueError('E213-POSICAO')
    p=shot['animation_proof']; verified=verificar(p['renderer'],Path(public_root)/shot['asset'])
    if any(p.get(k)!=v for k,v in verified.items()):
        raise ValueError('E213-PROVA')
    from copy import deepcopy
    out=deepcopy(props); shots=out['shots']
    start=shots[pos]['start'] if pos<len(shots) else out['duracao']
    if abs(shot['start']-start)>1e-6:
        raise ValueError('E213-CORTE')
    dur=shot['end']-shot['start']
    for s in shots[pos:]:
        s['start']=round((s['start']+dur)*30)/30
        s['end']=round((s['end']+dur)*30)/30
    shots.insert(pos,deepcopy(shot))
    out.update(duracao=round((out['duracao']+dur)*30)/30,private_review_only=True,preview=True)
    PA.exigir(shots,privado=True)
    return out
