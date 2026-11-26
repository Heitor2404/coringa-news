"""E327: reuse the exact static observation in the general documentary bridge.
No extra model call, new source, inferred event, or automatic editorial approval.
"""
import hashlib,json,math,re
from pathlib import Path
from PIL import Image
from . import revisao_documental as R, reuso_documental as RE, progressao_estatica_e322 as S

ROLES={'detalhe','estrutura','mecanismo','consequencia'}

def candidato(shot,need,c,media):
    if (shot.get('type')!='photo' or need.get('papel_visual') not in ROLES
        or need.get('evidencia_visual')!='estatica' or need.get('exigir_evidencia_direta') is not True):
        return None
    d=c.get('decisao') or {};q=c.get('revisao') or {};raw=q.get('resposta') or {}
    label=raw.get('rotulo_detalhe');obs=raw.get('inspecao');digest=media.get('expected_sha256')
    if not isinstance(label,str) or not 3<=len(label.strip())<=34 or not label.strip().isprintable():return None
    label=label.strip()
    if label.casefold() in {str(v or '').strip().casefold() for v in (need.get('sujeito'),shot.get('lead'),shot.get('headline'))}:return None
    if not isinstance(obs,str) or len(obs.strip())<35:return None
    if (d.get('estado')!='PERTINENTE_PRIVADO' or d.get('publicar') is not False or d.get('direitos_aprovados') is not False
        or q.get('publicar') is not False or q.get('necessidade_id')!=need.get('id') or q.get('mostrar')!=need.get('mostrar')
        or d.get('revisao_id')!=q.get('revisao_id') or q.get('sha256_origem')!=digest
        or not re.fullmatch('[a-f0-9]{64}',str(digest or ''))):return None
    try:
        decision=R.decidir(need,c,q,tipo='foto')
        roi=decision.get('evidencia_direta_normalizada') or {}
        if decision['estado']!='PERTINENTE_PRIVADO' or roi!=d.get('evidencia_direta_normalizada') or roi.get('escala_origem') not in ('xy_0_1','xy_0_1000'):return None
        base={k:q[k] for k in ('sha256_origem','necessidade_id','mostrar','pixels_sha256','px')}
        rid=hashlib.sha256(json.dumps(base,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if rid!=q['revisao_id']:return None
        path=Path(media['local_source'])
        if path.is_absolute() or not path.is_file() or path.parts[:1]!=('stage_documental',) or '..' in path.parts or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:return None
        with Image.open(path) as im:
            if list(im.size)!=[media['width'],media['height']] or RE.reproduzir_amostra_foto(im,q) is None:return None
        span=shot['end']-shot['start']
        if span<2.4:return None
        # Scene-relative midpoint, not a claim about a measured spoken word.
        at=math.floor(span*30/2)/30
        packet={'schema':'coringa.static.reveal.private.v1','publicar':False,'shot':shot['id'],
            'sha256':digest,'review_ref':rid,'at':at,'label':label,'bbox':roi['bbox'],'observation':obs.strip()}
        trial={**shot,'static_fact_reveal':packet,'cues':[{'at':.2,'label':shot.get('lead') or need['sujeito']},{'at':at,'label':label}]}
        trial.pop('photo_roi_candidate',None)
        S.validar(trial,media,digest,private=True)
        # Only use the two-panel mode where the gain is materially useful;
        # E325's marginal 1.16x gain shrank the overview too much.
        zoom={**packet,'detail_zoom':True}
        try:
            if S.validar({**trial,'static_fact_reveal':zoom},media,digest,private=True)['detail_gain']>=1.5:
                trial['static_fact_reveal']=zoom
        except ValueError:pass
        return trial
    except (ValueError,TypeError,KeyError,OSError,AttributeError):return None

def aplicar(case,chosen,plan):
    if plan.get('publicar') is not False or plan.get('tipo')!='PROVA_VISUAL_PRIVADA':return []
    paired={i for p in plan.get('comparacoes_documentais',[]) if p.get('estado')=='PAR_QUALITATIVO_MONTADO_PRIVADO' for i in p['necessidades']}
    reports=[]
    for i,shot in enumerate(plan['shots']):
        if shot['id'] in paired:continue
        x=chosen[shot['id']]
        if x['kind']!='photo':continue
        trial=candidato(shot,x['need'],x['candidate'],plan['media'][shot['asset']])
        if trial is None:continue
        plan['shots'][i]=trial
        reports.append({'necessidade_id':shot['id'],'revisao_id':trial['static_fact_reveal']['review_ref'],
            'sha256':trial['static_fact_reveal']['sha256'],'fatos':x['need']['fatos'],'mostrar':x['need']['mostrar'],
            'modo':'DETALHE_AMPLIADO' if trial['static_fact_reveal'].get('detail_zoom') else 'DESTAQUE_INTEGRAL',
            'tempo':'METADE_DA_CENA_NAO_ANCORA_DE_FALA','publicar':False,'aprovacao_editorial':False})
    return reports
