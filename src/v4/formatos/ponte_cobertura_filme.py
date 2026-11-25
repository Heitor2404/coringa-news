"""E254: bridge reviewed originals to the existing FilmeEditorial.
Private proof, not automatic editorial approval. Never stretch a reviewed window,
repeat an original or claim that a representative photo proves a specific event.
"""
import math,json
from . import ponte_mapa_atlas as B, tempo_natural as T
from pathlib import Path
from src.v3.pacote_biblioteca import sha
from src.v4.formatos import filme_editorial as F

def preparar_cobertura(report,case,*,atlas=None,progressao=None,minimo_s=60):
    if report.get('publish') is not False:raise ValueError('E254-PRIVADO')
    tri={n['id']:n for n in report['triagem']}
    rows={r['necessidade_id']:r for r in report['cobertura']}
    chosen={};issues=[];pages=set();hashes=set();video_ranges={};video_pages={}
    atlas=atlas or {};progressao=progressao or {}
    ids=[i for ch in case['chapters'] for i in ch['needs']]
    if len(ids)!=len(set(ids)) or set(ids)!=set(tri):raise ValueError('E254-NECESSIDADES')
    for i in ids:
        n=tri[i];r=rows.get(i) or {}
        if r.get('estado')=='DELEGAR_ATLAS' and n.get('necessidade')=='territorio':
            m=atlas.get(i) or {}
            if m.get('necessidade_id')!=i or m.get('fatos')!=n['fatos'] or m.get('mostrar')!=n['mostrar'] or m.get('origem')!='CURADORIA_GEOGRAFICA_VERIFICADA':
                issues.append({'id':i,'motivo':'ATLAS_SEM_VINCULO_GEOGRAFICO'});continue
            errors=B.validar_comprovante(m)
            if errors:
                issues.append({'id':i,'motivo':'ATLAS_SEM_COMPROVANTE','erros':errors});continue
            proof=json.loads(Path(m['atlas_proof']).read_text(encoding='utf8'))
            span=proof.get('duracao_s')
            if type(span) not in (int,float) or not math.isfinite(span) or not 1.4<=span<=8 or abs(span*30-round(span*30))>.1 or m['expected_sha256'] in hashes:
                issues.append({'id':i,'motivo':'ATLAS_TEMPO_OU_REPETICAO'});continue
            hashes.add(m['expected_sha256'])
            chosen[i]={'need':n,'kind':'atlas_map','cap':round(span*30)/30,'min':round(span*30)/30,'atlas':m}
            continue
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
        reused=c['pagina'] in pages or a['sha256'] in hashes
        if reused and (c.get('tipo')!='video' or video_pages.get(c['pagina'])!=a['sha256'] or a['sha256'] not in video_ranges):
            issues.append({'id':i,'motivo':'REPETICAO'});continue
        kind='photo' if c['tipo']=='foto' else 'video' if c['tipo']=='video' else None
        if not kind or min(a['width'],a['height'])<(600 if kind=='photo' else 700):
            issues.append({'id':i,'motivo':'QUALIDADE_INSUFICIENTE'});continue
        if kind=='photo' and n.get('evidencia_visual')=='movimento':
            issues.append({'id':i,'motivo':'FOTO_NAO_PROVA_MOVIMENTO'});continue
        window=c.get('selecao_janela') or {}
        cap=3.8 if kind=='photo' else min(3.8,float(window.get('duracao_s') or 0))
        framing=None
        if kind=='video' and window.get('revisao_id')==d.get('revisao_id') and window.get('video_framing'):
            trial={'type':'video','start':0,'end':cap,'source_in_seconds':window.get('source_in_seconds'),'video_zoom':1,'video_framing':window['video_framing']}
            try:
                F.resolver_relacao_video(trial,{'expected_sha256':a['sha256']},(a['width'],a['height']),adaptativo=True)
                framing=window['video_framing']
            except (ValueError,TypeError,KeyError):pass
        progression=None
        pgr=progressao.get(i) or {}
        if kind=='video' and pgr.get('necessidade_id')==i and pgr.get('revisao_id')==d.get('revisao_id'):
            # External observation packet may extend capacity only within the
            # actually reviewed original window, with the existing temporal gate.
            proposed=float(window.get('duracao_s') or 0)
            ini=window.get('source_in_seconds')
            if proposed>3.8 and ini is not None:
                trial={'type':'video','start':0,'end':proposed,'source_in_seconds':ini,'progressao_visual':pgr.get('progressao_visual')}
                if not T.validar_janela_origem(trial,a['duration_s']) and not T.validar_progressao_video(trial,proposed,{'expected_sha256':a['sha256']}):
                    # Fixed long clip preserves its observed event timing.
                    cap=math.floor(proposed*30+1e-6)/30
                    if not T.validar_progressao_video(trial,cap,{'expected_sha256':a['sha256']}):
                        progression=pgr['progressao_visual']
                    else:cap=min(3.8,proposed)
        if kind=='video' and progression is None:
            seq=T.progressao_amostrada(n,c,inicio=window.get('source_in_seconds'))
            if seq:
                trial={'type':'video','evidence':'representative','start':0,'end':seq['duracao_s'],'source_in_seconds':seq['inicio_s'],'progressao_visual':seq}
                if not T.validar_janela_origem(trial,a['duration_s']) and not T.validar_progressao_video(trial,seq['duracao_s'],{'expected_sha256':a['sha256']}):
                    cap=seq['duracao_s'];progression=seq;framing=None
                    window={**window,'source_in_seconds':seq['inicio_s'],'duracao_s':cap}
        if cap<1.4 or (kind=='video' and p.suffix.lower() not in ('.mp4','.webm')):
            issues.append({'id':i,'motivo':'JANELA_INSUFICIENTE'});continue
        if kind=='video':
            ini=window.get('source_in_seconds')
            if not isinstance(ini,(int,float)) or not math.isfinite(ini) or ini<0 or ini+cap>a['duration_s']+.001:
                issues.append({'id':i,'motivo':'JANELA_FORA_ORIGEM'});continue
            ranges=video_ranges.setdefault(a['sha256'],[])
            if any(max(ini,b)<min(ini+cap,e)-.001 or set(n['fatos'])&set(facts) for b,e,facts in ranges):
                issues.append({'id':i,'motivo':'JANELA_REPETIDA_OU_MESMO_FATO'});continue
            ranges.append((ini,ini+cap,n['fatos']));video_pages[c['pagina']]=a['sha256']
        pages.add(c['pagina']);hashes.add(a['sha256'])
        chosen[i]={'need':n,'candidate':c,'kind':kind,'cap':cap,'min':cap if progression else 1.4,'window':window,'progressao':progression,'framing':framing}
    capacity=sum(x['cap'] for x in chosen.values())
    if capacity<minimo_s:issues.append({'id':'filme','motivo':'CAPACIDADE_MENOR_MINIMO','segundos':capacity,'minimo_s':minimo_s})
    return chosen,{'pronto_para_tts':not issues,'total':len(ids),'cobertos':len(chosen),
                  'capacidade_s':round(capacity,3),'lacunas':issues,'publicar':False}

def plano(case,chosen,tempos):
    shots=[];media={};start=0;maps=[]
    for ch,end in zip(case['chapters'],tempos,strict=True):
        ids=ch['needs'];length=end-start
        # Distribute actual measured chapter time in whole frames; no speed change.
        caps=[math.floor(chosen[i]['cap']*30+1e-6) for i in ids]
        mins=[math.ceil(chosen[i].get('min',1.4)*30-1e-6) for i in ids]
        if not sum(mins)<=length<=sum(caps):raise ValueError('E254-TEMPO-CAPITULO '+ch['title'])
        frames=mins.copy()
        for _ in range(length-sum(frames)):
            j=min((j for j in range(len(ids)) if frames[j]<caps[j]),key=lambda j:frames[j])
            frames[j]+=1
        for i,count in zip(ids,frames):
            x=chosen[i];n=x['need']
            if x['kind']=='atlas_map':
                m=x['atlas'];span=count/30
                shots.append({'id':i,'type':'atlas_map','start':start/30,'end':(start+count)/30,
                    'headline':n['sujeito'],'lead':ch['title'] if i==ids[0] else '',
                    'cues':[{'at':min(1.1,span*.45),'label':n['sujeito']}]})
                maps.append((i,m));start+=count;continue
            c=x['candidate'];a=c['aquisicao'];mid='m-'+a['sha256'][:12]
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
            if x.get('framing') and all(p['at']<span for p in x['framing']['pontos']):
                shot['video_framing']=x['framing']
            if x.get('progressao'):shot['progressao_visual']=x['progressao']
            shots.append(shot);start+=count
    result={'formato':'filme_editorial','tipo':'PROVA_VISUAL_PRIVADA','publicar':False,
            'titulo':case['tema'],'duracao':start/30,'media':media,'shots':shots,'documentary_framing':'ADAPTIVE_REVIEW_V1'}
    for i,m in maps:
        result=B.inserir_no_filme(result,i,Path(m['local_source']),Path(m['atlas_proof']),m.get('intencao','localizar'))
    return result
