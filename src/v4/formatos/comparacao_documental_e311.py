"""E311: qualitative comparison by consecutive full-evidence shots.
Do not infer dates, scale, causation, or identity from two matching topics.
An independently reviewed explicit packet is required; ordinary shots survive
if it is absent or stale. No automatic montage from an LLM label alone.
"""
import re

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
        reports.append({'id':pair.get('id'),'estado':'PAR_QUALITATIVO_MONTADO_PRIVADO','necessidades':[a,b],
            'criterio':criterion,'rotulos':labels,'escala_comparavel':False,'publicar':False,'aprovacao_editorial':False})
    return reports
