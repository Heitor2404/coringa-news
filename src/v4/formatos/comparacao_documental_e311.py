"""E311: qualitative comparison by consecutive full-evidence shots.
Do not infer dates, scale, causation, or identity from two matching topics.
An independently reviewed explicit packet is required; ordinary shots survive
if it is absent or stale. No automatic montage from an LLM label alone.
"""
import re,math

def recorte_painel(box,w,h):
    if not isinstance(box,list) or len(box)!=4 or any(type(v) not in (float,int) or not math.isfinite(v) for v in box):return None
    x,y,r,b=box
    if not (0<=x<r<=1 and 0<=y<b<=1 and w>0 and h>0):return None
    dx,dy=.12*(r-x),.12*(b-y)
    x,r=max(0,x-dx),min(1,r+dx)
    y,b=max(0,y-dy),min(1,b+dy)
    aspect=2.7
    cw=max((r-x)*w,(b-y)*h*aspect);ch=cw/aspect
    if cw>w+1e-6 or ch>h+1e-6 or cw<600:return None
    left=max(0,min(w-cw,(x+r)*w/2-cw/2));top=max(0,min(h-ch,(y+b)*h/2-ch/2))
    if left>x*w+1e-6 or top>y*h+1e-6 or left+cw<r*w-1e-6 or top+ch<b*h-1e-6:return None
    return [left/w,top/h,(left+cw)/w,(top+ch)/h]

def aplicar(case,chosen,plan):
    shots=plan['shots'];byid={s['id']:s for s in shots}
    ids=[s['id'] for s in shots]
    pairs=case.get('comparacoes_revisadas') or []
    reports=[];used=set()
    if not isinstance(pairs,list):return [{'estado':'PACOTE_INVALIDO','publicar':False}]
    chapters={i:j for j,ch in enumerate(case['chapters']) for i in ch['needs']}
    for pair in pairs:
        def refuse(reason):
            reports.append({'id':pair.get('id') if isinstance(pair,dict) else None,
                            'estado':reason,'publicar':False,'aprovacao_editorial':False})
        if not isinstance(pair,dict) or pair.get('publicar') is not False or pair.get('direitos_aprovados') is not False or pair.get('origem') not in ('CURADORIA_HUMANA','INSPECAO_ASSISTIDA_PRIVADA'):
            refuse('REVISAO_INDEPENDENTE_PENDENTE');continue
        members=pair.get('membros');criterion=pair.get('criterio')
        if (pair.get('tipo')!='qualitativa' or pair.get('escala_comparavel') is not False or
            pair.get('inferir_causalidade') is not False or pair.get('inferir_cronologia') is not False or
            not isinstance(criterion,str) or not 3<=len(criterion.strip())<=35 or
            not isinstance(members,list) or len(members)!=2 or not all(isinstance(m,dict) for m in members)):
            refuse('CRITERIO_OU_ESCOPO_INVALIDO');continue
        a,b=[m.get('necessidade_id') for m in members]
        if not all(isinstance(i,str) for i in (a,b)) or a not in byid or b not in byid or a in used or b in used or ids.index(b)!=ids.index(a)+1 or chapters[a]!=chapters[b]:
            refuse('PAR_NAO_ADJACENTE_OU_REPETIDO');continue
        valid=True;hashes=set();pages=set();labels=[]
        for member,i in zip(members,(a,b)):
            x=chosen[i];n=x['need'];c=x.get('candidate') or {};d=c.get('decisao') or {};sha=(c.get('aquisicao') or {}).get('sha256')
            label=member.get('rotulo')
            if (x['kind']!='photo' or n.get('papel_visual')!='comparacao' or n.get('evidencia_visual')=='movimento' or
                member.get('fatos')!=n['fatos'] or member.get('mostrar')!=n['mostrar'] or
                not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha) or member.get('sha256')!=sha or
                d.get('estado')!='PERTINENTE_PRIVADO' or not d.get('revisao_id') or member.get('revisao_id')!=d['revisao_id'] or
                member.get('criterio_observado')!=criterion or not isinstance(label,str) or not 3<=len(label.strip())<=32 or
                not c.get('pagina') or d.get('publicar') is not False or d.get('direitos_aprovados') is not False):
                valid=False;break
            hashes.add(sha);pages.add(c['pagina']);labels.append(label.strip())
        if not valid or len(hashes)!=2 or len(pages)!=2 or len(set(labels))!=2:
            refuse('PAR_SEM_VINCULO_OU_FONTES_DISTINTAS');continue
        # Keep original shots, timing, citations and full source geometry.
        # The existing section text channel names the common criterion and
        # each observed variant. No wipe/scale match, no invented before/after.
        for i,label in zip((a,b),labels):
            s=byid[i]
            s['lead']=criterion.strip()+' · '+label
            s.pop('photo_roi_candidate',None)
            s['photo_framing']='integral'
        used.update((a,b))
        report={'id':pair.get('id'),'estado':'PAR_QUALITATIVO_MONTADO_PRIVADO','necessidades':[a,b],
            'criterio':criterion,'rotulos':labels,'escala_comparavel':False,'publicar':False,'aprovacao_editorial':False}
        if pair.get('apresentacao')=='painel_observado':
            report['painel_candidato']=[{k:m.get(k) for k in ('necessidade_id','sha256','revisao_id','roi_observada','rotulo')} for m in members]
        reports.append(report)
    return reports

def preparar_paineis(plan,medias):
    if plan.get('tipo')!='PROVA_VISUAL_PRIVADA' or plan.get('publicar') is not False:return {}
    shots=plan['shots'];ids=[s['id'] for s in shots];out={}
    for pair in plan.get('comparacoes_documentais') or []:
        members=pair.get('painel_candidato')
        if pair.get('estado')!='PAR_QUALITATIVO_MONTADO_PRIVADO' or pair.get('publicar') is not False or pair.get('escala_comparavel') is not False or not isinstance(members,list) or len(members)!=2:continue
        a,b=pair['necessidades']
        if a not in ids or b not in ids or ids.index(b)!=ids.index(a)+1:continue
        second=shots[ids.index(b)];span=second['end']-second['start']
        # Keep both original establishing views; if there is insufficient
        # time for the comparison, leave the existing edit unchanged.
        if span<2.8:continue
        panels=[]
        for i,m in zip((a,b),members):
            s=shots[ids.index(i)];asset=medias.get(s.get('asset')) or {}
            roi=m.get('roi_observada')
            if (s['type']!='photo' or m.get('necessidade_id')!=i or m.get('sha256')!=asset.get('sha256') or
                not isinstance(roi,dict) or roi.get('sha256')!=m.get('sha256') or roi.get('revisao_id')!=m.get('revisao_id') or
                not m.get('revisao_id') or roi.get('origem')!='OBSERVACAO_PRIVADA' or
                not isinstance(m.get('rotulo'),str) or not 3<=len(m['rotulo'])<=32):break
            crop=recorte_painel(roi.get('bbox'),asset['width'],asset['height'])
            if not crop:break
            panels.append({'asset':asset['asset'],'sha256':asset['sha256'],'crop':crop,'label':m['rotulo'],
                           'credit':asset['credit'],'dimensions':[asset['width'],asset['height']]})
        if len(panels)==2 and panels[0]['sha256']!=panels[1]['sha256']:
            out[b]={'schema':'coringa.comparison.panel.private.v1','publish':False,'criterion':pair['criterio'],
                    'scale_comparable':False,'at':span/2,'panels':panels}
    return out
