"""E254: bridge reviewed originals to the existing FilmeEditorial.
Private proof, not automatic editorial approval. Never stretch a reviewed window,
repeat an original or claim that a representative photo proves a specific event.
"""
import math
from pathlib import Path
from src.v3.pacote_biblioteca import sha
from src.v4.formatos import filme_editorial as F

def preparar_cobertura(report,case):
    if report.get('publish') is not False:raise ValueError('E254-PRIVADO')
    tri={n['id']:n for n in report['triagem']}
    rows={r['necessidade_id']:r for r in report['cobertura']}
    chosen={};issues=[];pages=set();hashes=set()
    ids=[i for ch in case['chapters'] for i in ch['needs']]
    if len(ids)!=len(set(ids)) or set(ids)!=set(tri):raise ValueError('E254-NECESSIDADES')
    for i in ids:
        n=tri[i];r=rows.get(i) or {}
        selected=r.get('selecionado')
        if r.get('estado')!='CANDIDATO_PRIVADO_REVISADO' or not selected:
            issues.append({'id':i,'motivo':r.get('estado','SEM_COBERTURA')});continue
        candidates=[c for round_ in r['rodadas'] for c in round_['pesquisa']['candidatos']
                    if [c.get('fonte'),c.get('source_id') or c.get('url')]==list(selected)
                    and (c.get('decisao') or {}).get('estado')=='PERTINENTE_PRIVADO']
        if not candidates:issues.append({'id':i,'motivo':'SEM_CANDIDATO_VINCULADO'});continue
        c=candidates[-1];a=c.get('aquisicao') or {};d=c['decisao']
        p=Path(c.get('local_source') or '.')
        direct=n.get('exigir_evidencia_direta') is True
        if d.get('necessidade_id')!=i or not d.get('revisao_id') or not direct or d.get('publicar') is not False or d.get('direitos_aprovados') is not False or not p.is_file() or p.parts[:1]!=('stage_documental',) or sha(p)!=a.get('sha256'):
            issues.append({'id':i,'motivo':'REVISAO_OU_BYTES_SEM_VINCULO'});continue
        if c.get('licenca') not in F.LICENCAS or not c.get('pagina') or not c.get('credito'):
            issues.append({'id':i,'motivo':'PROCEDENCIA_PENDENTE_COMPATIBILIDADE_FILME'});continue
        if c['pagina'] in pages or a['sha256'] in hashes:
            issues.append({'id':i,'motivo':'REPETICAO'});continue
        kind='photo' if c['tipo']=='foto' else 'video' if c['tipo']=='video' else None
        if not kind or min(a['width'],a['height'])<(600 if kind=='photo' else 700):
            issues.append({'id':i,'motivo':'QUALIDADE_INSUFICIENTE'});continue
        if kind=='photo' and n.get('evidencia_visual')=='movimento':
            issues.append({'id':i,'motivo':'FOTO_NAO_PROVA_MOVIMENTO'});continue
        window=c.get('selecao_janela') or {}
        cap=3.8 if kind=='photo' else min(3.8,float(window.get('duracao_s') or 0))
        if cap<1.4 or (kind=='video' and p.suffix.lower() not in ('.mp4','.webm')):
            issues.append({'id':i,'motivo':'JANELA_INSUFICIENTE'});continue
        pages.add(c['pagina']);hashes.add(a['sha256'])
        chosen[i]={'need':n,'candidate':c,'kind':kind,'cap':cap,'window':window}
    capacity=sum(x['cap'] for x in chosen.values())
    if capacity<60:issues.append({'id':'filme','motivo':'CAPACIDADE_MENOR_60S','segundos':capacity})
    return chosen,{'pronto_para_tts':not issues,'total':len(ids),'cobertos':len(chosen),
                  'capacidade_s':round(capacity,3),'lacunas':issues,'publicar':False}

def plano(case,chosen,tempos):
    shots=[];media={};start=0
    for ch,end in zip(case['chapters'],tempos,strict=True):
        ids=ch['needs'];length=end-start
        # Distribute actual measured chapter time in whole frames; no speed change.
        caps=[math.floor(chosen[i]['cap']*30+1e-6) for i in ids]
        if not 42*len(ids)<=length<=sum(caps):raise ValueError('E254-TEMPO-CAPITULO '+ch['title'])
        frames=[42]*len(ids)
        for _ in range(length-sum(frames)):
            j=min((j for j in range(len(ids)) if frames[j]<caps[j]),key=lambda j:frames[j])
            frames[j]+=1
        for i,count in zip(ids,frames):
            x=chosen[i];c=x['candidate'];a=c['aquisicao'];n=x['need'];mid='m-'+a['sha256'][:12]
            media[mid]={'id':mid,'local_source':c['local_source'],'expected_sha256':a['sha256'],
                        'width':a['width'],'height':a['height'],'duration_s':a['duration_s'],'media_type':x['kind'],
                        'page':c['pagina'],'credit':c['credito'],'license':c['licenca'],'rights_status':'REVIEW_PENDING'}
            span=count/30
            shot={'id':i,'type':x['kind'],'asset':mid,'start':start/30,'end':(start+count)/30,
                  'subject':n['sujeito'],'headline':n['sujeito'],'lead':ch['title'] if i==ids[0] else '',
                  'source_display':c['credito'],'evidence':'representative','focus':[.5,.5],
                  'cues':[{'at':min(1.1,span*.45),'label':n['sujeito']}]}
            if x['kind']=='photo':shot['photo_framing']='integral'
            else:
                shot.update(source_in_seconds=x['window']['source_in_seconds'],video_zoom=1,video_context_layout='cena_integral')
            shots.append(shot);start+=count
    return {'formato':'filme_editorial','tipo':'PROVA_VISUAL_PRIVADA','publicar':False,
            'titulo':case['tema'],'duracao':start/30,'media':media,'shots':shots}
