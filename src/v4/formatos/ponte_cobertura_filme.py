"""E254: bridge reviewed originals to the existing FilmeEditorial.
Private proof, not automatic editorial approval. Never stretch a reviewed window,
repeat an original or claim that a representative photo proves a specific event.
"""
import math,json
from . import ponte_mapa_atlas as B, tempo_natural as T
from pathlib import Path
from src.v3.pacote_biblioteca import sha
from src.v4.formatos import filme_editorial as F

def origem_documental(c,a):
    """Keep acquisition receipts across the existing bridge, including V3 replay."""
    provider=c.get('fonte')
    source=c
    if provider=='biblioteca_v3':
        source=c.get('recibo_restaurado') or {}
        if (source.get('aquisicao') or {}).get('sha256')!=a.get('sha256') or source.get('pagina')!=c.get('pagina'):
            return None
        provider=source.get('fonte')
        source=source.get('recibos') or {}
    key={'nasa':'recibo_nasa','nasa_video':'recibo_nasa','archive_video':'recibo_archive','usgs_pagina':'recibo_usgs'}.get(provider)
    if key is None:return None
    receipt=source.get(key)
    if not isinstance(receipt,dict):return None
    return {'provedor':provider,'sha256_origem':a['sha256'],'url_adquirida':a.get('url_adquirida'),
            'bytes':a.get('bytes'),'recibo':receipt,'publicar':False,'direitos_aprovados':False}


def licenca_documental(c,a):
    lic={'CC0 1.0':'CC0','Public Domain':'Public domain'}.get(c.get('licenca'),c.get('licenca'))
    receipt=origem_documental(c,a)
    if receipt and receipt['provedor'] in ('nasa','nasa_video'):lic='REVIEW_PENDING'
    asset={'license':lic,'page':c.get('pagina'),'credit':c.get('credito'),
           'expected_sha256':a.get('sha256'),'rights_status':'REVIEW_PENDING'}
    if receipt:asset['documentary_receipt']=receipt
    # New provider evidence must arrive with its own receipt. A named
    # license alone is insufficient for an unfamiliar documentary host.
    from urllib.parse import urlsplit
    host=urlsplit(str(c.get('pagina') or '')).hostname
    if (host in ('images.nasa.gov','archive.org') or c.get('fonte')=='usgs_pagina' or (c.get('recibo_restaurado') or {}).get('fonte')=='usgs_pagina') and not F.recibo_documental_valido(asset):return None
    if lic not in F.LICENCAS and not (receipt and F.recibo_documental_valido(asset)):return None
    if not asset['page'] or not asset['credit']:return None
    return asset


def duracao_minima_revisada(c,window,cap,framing=None):
    """Keep the last reviewed sample inside the actual cut, not just inside
    the acquisition window. Without a matched review do not shorten it.
    """
    from . import direcao_eventos as DE
    rid=window.get('revisao_id')
    if not rid:return cap if cap>=1.4 else None
    for row in c.get('janelas',[]):
        pk=row.get('pacote') or {}
        if pk.get('revisao_id')!=rid or pk.get('sha256_origem')!=(c.get('aquisicao') or {}).get('sha256') or pk.get('inicio_s')!=window.get('source_in_seconds'):continue
        try:
            obs=DE.aceitar_observacao(pk,pk['revisao_assistida']['resposta_observada'])
            if obs['veredito']!='pertinente':continue
            times=[a['at'] for a in pk['amostras']]
            if framing:times.extend(pt['at'] for pt in framing['pontos'])
            if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in times):continue
            # The final displayed frame must be at or after the last sample;
            # the end-exclusive timestamp is one frame beyond that frame.
            minimum=max(1.4,(math.ceil(max(times)*30-1e-6)+1)/30)
            return minimum if minimum<=cap+1e-6 else None
        except (ValueError,TypeError,KeyError,AttributeError):continue
    return cap if cap>=1.4 else None


def preparar_cobertura(report,case,*,atlas=None,progressao=None,animacoes=None,minimo_s=60):
    if report.get('publish') is not False:raise ValueError('E254-PRIVADO')
    tri={n['id']:n for n in report['triagem']}
    rows={r['necessidade_id']:r for r in report['cobertura']}
    chosen={};issues=[];pages=set();hashes=set();video_ranges={};video_pages={}
    atlas=atlas or {};progressao=progressao or {};animacoes=animacoes or {}
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
        if r.get('estado')=='LACUNA_PENDENTE' and i in animacoes:
            from . import complemento_integral_e314 as E
            try:
                clip=E.entrega(n,r,animacoes[i]);digest=clip['animation_proof']['sha256']
                if digest in hashes:raise ValueError('E314-REPETICAO')
                hashes.add(digest);span=clip['end']
                chosen[i]={'need':n,'kind':'animation_clip','cap':span,'min':span,'clip':clip}
                continue
            except (ValueError,KeyError,TypeError,OSError) as exc:
                issues.append({'id':i,'motivo':'COMPLEMENTO_NAO_VALIDADO','erro':str(exc)[:200]});continue
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
        rights=licenca_documental(c,a)
        if rights is None:
            issues.append({'id':i,'motivo':'PROCEDENCIA_PENDENTE_COMPATIBILIDADE_FILME'});continue
        reused=c['pagina'] in pages or a['sha256'] in hashes
        if reused and (c.get('tipo')!='video' or video_pages.get(c['pagina'])!=a['sha256'] or a['sha256'] not in video_ranges):
            issues.append({'id':i,'motivo':'REPETICAO'});continue
        kind='photo' if c['tipo']=='foto' else 'video' if c['tipo']=='video' else None
        if not kind or min(a['width'],a['height'])<(600 if kind=='photo' else F.MIN_VIDEO_COMPOSITION_PX):
            issues.append({'id':i,'motivo':'QUALIDADE_INSUFICIENTE'});continue
        if kind=='photo' and n.get('evidencia_visual')=='movimento':
            issues.append({'id':i,'motivo':'FOTO_NAO_PROVA_MOVIMENTO'});continue
        window=c.get('selecao_janela') or {}
        cap=3.8 if kind=='photo' else min(3.8,float(window.get('duracao_s') or 0))
        framing=None
        if kind=='video' and window.get('revisao_id')==d.get('revisao_id') and window.get('video_framing'):
            trial={'type':'video','start':0,'end':cap,'source_in_seconds':window.get('source_in_seconds'),'video_zoom':1,'video_framing':window['video_framing']}
            try:
                if window['video_framing'].get('modo')=='fonte_integral':
                    F.proteger_fonte_integral(trial,{'expected_sha256':a['sha256']},(a['width'],a['height']))
                else:
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
        if kind=='video':
            cap=math.floor(cap*30+1e-6)/30
            minimum=cap if progression else duracao_minima_revisada(c,window,cap,framing)
        else:minimum=1.4
        if minimum is None or cap<1.4 or (kind=='video' and p.suffix.lower() not in ('.mp4','.webm')):
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
        chosen[i]={'need':n,'candidate':c,'kind':kind,'cap':cap,'min':minimum,'window':window,'progressao':progression,'framing':framing,'rights':rights}
    capacity=sum(x['cap'] for x in chosen.values())
    if capacity<minimo_s:issues.append({'id':'filme','motivo':'CAPACIDADE_MENOR_MINIMO','segundos':capacity,'minimo_s':minimo_s})
    return chosen,{'pronto_para_tts':not issues,'total':len(ids),'cobertos':len(chosen),
                  'capacidade_s':round(capacity,3),'lacunas':issues,'publicar':False}

def credito_em_tela(credito):
    """Use the actual attribution suffix of the Commons catalogue format
    (title — author (license), Wikimedia Commons), never truncate the author
    or invent attribution. Full credit and source page remain in media.
    """
    if not isinstance(credito,str):return credito
    if credito.endswith((', Wikimedia Commons',', via Wikimedia Commons')) and ' — ' in credito:
        title,author=credito.rsplit(' — ',1)
        if title.strip() and author.strip():return author
    return credito


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
            if x['kind']=='animation_clip':
                clip={**x['clip'],'start':start/30,'end':(start+count)/30}
                if count!=round(x['cap']*30):raise ValueError('E314-SEM-RETIMAR')
                shots.append(clip);start+=count;continue
            if x['kind']=='atlas_map':
                m=x['atlas'];span=count/30
                shots.append({'id':i,'type':'atlas_map','start':start/30,'end':(start+count)/30,
                    'headline':n['sujeito'],'lead':ch['title'] if i==ids[0] else '',
                    'cues':[{'at':min(1.1,span*.45),'label':n['sujeito']}]})
                maps.append((i,m));start+=count;continue
            c=x['candidate'];a=c['aquisicao'];mid='m-'+a['sha256'][:12]
            media[mid]={'id':mid,'local_source':c['local_source'],'expected_sha256':a['sha256'],
                        'width':a['width'],'height':a['height'],'duration_s':a['duration_s'],'media_type':x['kind'],
                        **x.get('rights',{'page':c['pagina'],'credit':c['credito'],'license':c['licenca'],'rights_status':'REVIEW_PENDING'})}
            span=count/30
            shot={'id':i,'type':x['kind'],'asset':mid,'start':start/30,'end':(start+count)/30,
                  'subject':n['sujeito'],'headline':n['sujeito'],'lead':ch['title'] if i==ids[0] else '',
                  'source_display':credito_em_tela(c['credito']),'evidence':'representative','focus':[.5,.5],
                  'cues':[{'at':min(1.1,span*.45),'label':n['sujeito']}]}
            if x['kind']=='photo':
                shot['photo_framing']='integral'
                if n.get('papel_visual')=='detalhe':shot['documentary_detail_intent']=True
                # Opt-in private comparison; existing replay semantics remain unchanged.
                if case.get('avaliar_recorte_foto') is not False:
                    decision=c.get('decisao') or {}
                    roi=decision.get('evidencia_direta_normalizada') or {}
                    if decision.get('revisao_id') and roi.get('escala_origem') in ('xy_0_1','xy_0_1000'):
                        shot['photo_roi_candidate']={**roi,'sha256':a['sha256'],'revisao_id':decision['revisao_id']}
            else:
                shot.update(source_in_seconds=x['window']['source_in_seconds'],video_zoom=1,video_context_layout='cena_integral')
                from . import observacao_temporal_e315 as O
                observed=O.candidato(n,c,x['window'],span)
                if observed:shot['observacao_temporal_candidata']=observed
            if x.get('framing') and (x['framing'].get('modo')=='fonte_integral' or all(p['at']<span for p in x['framing']['pontos'])):
                shot['video_framing']=x['framing']
            if x.get('progressao'):shot['progressao_visual']=x['progressao']
            shots.append(shot);start+=count
    result={'formato':'filme_editorial','tipo':'PROVA_VISUAL_PRIVADA','publicar':False,
            'titulo':case['tema'],'duracao':start/30,'media':media,'shots':shots,'documentary_framing':'ADAPTIVE_REVIEW_V1',
            'necessidades_direcao':[{'id':i,'fatos':chosen[i]['need']['fatos'],'mostrar':chosen[i]['need']['mostrar'],'papel_visual':chosen[i]['need'].get('papel_visual','a_definir'),'evidencia_visual':chosen[i]['need'].get('evidencia_visual'),'preferencia_midia':chosen[i]['need'].get('preferencia_midia','adequada_ao_fato')} for i in (s['id'] for s in shots)]}
    for i,m in maps:
        result=B.inserir_no_filme(result,i,Path(m['local_source']),Path(m['atlas_proof']),m.get('intencao','localizar'))
    from . import comparacao_documental_e311 as C
    result['comparacoes_documentais']=C.aplicar(case,chosen,result)
    return result
