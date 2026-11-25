"""E219 private documentary: measured narration, USGS footage and native ATLAS.
Data-driven editorial fixture, not an autonomous source/semantic approval.
No footage synthesized; no fallback to mechanical drawings.
"""
import concurrent.futures, hashlib, json, math, re, shutil, subprocess, sys, wave
from pathlib import Path
from urllib.parse import urlsplit,urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageStat,ImageDraw
import io
from scripts.qa_documentario_curado_e218 import get,write,HEADERS,PUBLIC
from src.v4.formatos import filme_editorial as F, diretor_visual_e202 as D, legenda_sync as LS, ponte_mapa_atlas as B, plano as A
from src import voz

STAGE=Path('stage_documental/e219')
MAP=Path('stage_atlas/e219')
HOSTS={'usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com','www.usgs.gov','prd-wret.s3.us-west-2.amazonaws.com'}
def read(p):return json.loads(Path(p).read_text())
def sha(p):return B.sha256(p)
def probe(p):
    q=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height:format=duration','-of','json',str(p)]))
    v=q['streams'][0];return v['width'],v['height'],float(q['format']['duration'])

def acquire(row):
    slug,label=row
    if not re.fullmatch('[a-z0-9-]+',slug):raise ValueError('E219-SLUG')
    page='https://www.usgs.gov/media/videos/'+slug
    html=get(page,{'www.usgs.gov'},5_000_000)
    soup=BeautifulSoup(html,'html.parser');txt=soup.get_text(' ',strip=True)
    if not re.search(r'Sources/Usage\s+Public Domain\b',txt,re.I):raise ValueError('E219-LICENCA')
    h=soup.find('h1')
    if not h:raise ValueError('E219-TITULO')
    urls=[urljoin(page,a['href']) for a in soup.find_all('a',href=True) if 'download video' in a.get_text(' ',strip=True).lower()]
    urls=[u for u in dict.fromkeys(urls) if urlsplit(u).scheme=='https' and urlsplit(u).hostname in HOSTS]
    if not urls:raise ValueError('E219-ORIGINAL')
    u=urls[0];tmp=STAGE/(slug+'.part')
    try:
        with requests.get(u,headers=HEADERS,stream=True,allow_redirects=False,timeout=(15,45)) as r:
            if r.status_code!=200:raise ValueError('HTTP '+str(r.status_code))
            n=0
            with tmp.open('wb') as f:
                for b in r.iter_content(1<<20):
                    n+=len(b)
                    if n>250_000_000:raise ValueError('E219-LIMITE')
                    f.write(b)
        w,h_,dur=probe(tmp)
        if min(w,h_)<700 or dur<9:raise ValueError('E219-RESOLUCAO/DURACAO')
        checksum=sha(tmp);path=STAGE/(checksum+'.mp4')
        tmp.replace(path)
        return {'id':slug,'label':label,'subject':h.get_text(' ',strip=True),
                'page':page,'url_original':u,'page_sha256':hashlib.sha256(html).hexdigest(),
                'credit':'USGS · Hawaiian Volcano Observatory','license':'Public domain',
                'local_source':str(path),'expected_sha256':checksum,'media_type':'video',
                'width':w,'height':h_,'duration_s':dur}
    finally:
        tmp.unlink(missing_ok=True)


def acquire_photo(row):
    """Acquire an individual public-domain USGS photo, with explicit source credit.
    A photo provides static evidence only, not evidence of movement.
    """
    slug,label,credit=row
    if not re.fullmatch('[a-z0-9-]+',slug) or not credit.strip():raise ValueError('E245-FONTE')
    page='https://www.usgs.gov/media/images/'+slug
    raw=get(page,{'www.usgs.gov'},5_000_000)
    soup=BeautifulSoup(raw,'html.parser');txt=soup.get_text(' ',strip=True)
    if not re.search(r'Sources/Usage\s+Public Domain\b',txt,re.I):raise ValueError('E245-LICENCA')
    h=soup.find('h1')
    if not h:raise ValueError('E245-TITULO')
    hosts={'d9-wret.s3.us-west-2.amazonaws.com','prd-wret.s3.us-west-2.amazonaws.com'}
    urls=[]
    for role in ('original','medium'):
        for link in soup.find_all('a',href=True):
            if link.get_text(' ',strip=True).lower()!=role:continue
            u=urljoin(page,link['href'])
            if urlsplit(u).scheme=='https' and urlsplit(u).hostname in hosts:urls.append(u)
    errors=[]
    for u in list(dict.fromkeys(urls))[:4]:
        try:
            data=get(u,hosts,26_000_000)
            with Image.open(io.BytesIO(data)) as im:
                if im.format not in ('JPEG','PNG','WEBP') or min(im.size)<600:raise ValueError('E245-RESOLUCAO')
                w,h_=im.size;ext={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[im.format]
                im.verify()
            checksum=hashlib.sha256(data).hexdigest();path=STAGE/(checksum+ext);path.write_bytes(data)
            return {'id':slug,'label':label,'subject':h.get_text(' ',strip=True),'page':page,
                    'url_original':u,'page_sha256':hashlib.sha256(raw).hexdigest(),'credit':credit,
                    'license':'Public domain','local_source':str(path),'expected_sha256':checksum,
                    'media_type':'photo','width':w,'height':h_,'evidence_scope':'STATIC_ONLY'}
        except Exception as e:errors.append(type(e).__name__+': '+str(e)[:120])
    raise ValueError('E245-SEM-FOTO '+str(errors))

def frame(p,t,*,width=240):
    if type(width) is not int or not 240<=width<=1280:raise ValueError('E244-FRAME-WIDTH')
    z=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-vf',f'scale={width}:-2','-f','image2pipe','-vcodec','png','pipe:1'],timeout=30)
    return Image.open(io.BytesIO(z)).convert('RGB')

def windows(m,span,*,review_technical=False):
    # Samples verify readable bytes/no near-black or uniform frames only.
    # They do NOT prove the semantic action. Short cuts preserve native time.
    out=[];p=m['local_source'];dur=m['duration_s']
    from src.v4.formatos import direcao_eventos as DE
    candidates=[]
    for a in range(2,min(80,int(dur-span-1)),5):
        try:
            ims=[frame(p,a+span*f) for f in (.12,.5,.86)]
            if all(ImageStat.Stat(x.convert('L')).mean[0]>9 and ImageStat.Stat(x.convert('L')).stddev[0]>10 for x in ims):
                out.append((float(a),ims[1]))
                if review_technical:
                    candidates.append({'inicio_s':float(a),'frame':ims[1],
                                       'diagnostico':DE.diagnosticar_janela(ims)})
        except Exception:continue
        if len(out)>=8:break
    if review_technical:
        return [(x['inicio_s'],x['frame']) for x in DE.ordenar_janelas_tecnicas(candidates)]
    return out

def location_title(ch,span):
    """Preserve every word of the geographic label; use channel fonts, never per-episode sizes."""
    q=ch['atlas']
    words=q['label'].upper().split()
    if not words:raise ValueError('E219-MAPA-ROTULO-VAZIO')
    slot=A.caixa({'slot':'pergunta'},'atlas.abertura')
    tokens=A.canal('coringa')['titulo']['pergunta']
    # The same conservative width estimator as the original ATLAS fiscal.
    def wrap(text,size):
        lines=[]
        for word in text.split():
            if A._largura(word,size)>slot['w']:
                raise ValueError('E219-MAPA-PALAVRA-NAO-CABE '+word)
            if lines and A._largura(lines[-1]+' '+word,size)<=slot['w']:
                lines[-1]+=' '+word
            else:
                lines.append(word)
        return lines
    # Reveal a complete first phrase and then the highlighted place name.
    # Single-word places use the chapter's actual title as context.
    prefix=' '.join(words[:-1]) or ch['title'].upper()
    normal=wrap(prefix,tokens['normal'])
    focus=wrap(words[-1],tokens['destaque'])
    if len(normal)+len(focus)>A.REGRAS['titulo_max_linhas']:
        raise ValueError('E219-MAPA-TITULO-LONGO: revisar texto sem reduzir a fonte')
    return ([{'texto':line,'t':.3} for line in normal]+
            [{'texto':line,'t':span/3,'destaque':True} for line in focus])

def marker_time(span):
    # Reveal early for short clips, but preserve actual informational cadence
    # for longer map holds. No artificial event or validator bypass.
    gap=float(A.REGRAS['progressao_max_s'])
    t=max(span*.60,span-gap+.05)
    if t-span/3>gap or span-t>gap:
        raise ValueError('E219-MAPA-PROGRESSAO: dividir conteúdo geográfico')
    return t

def mapplan(ch,span):
    q=ch['atlas']
    p={'formato':'atlas','canal':'coringa','video_id':'e219-location','titulo':ch['title'],'geo':'motor4/formatos/dados/mundo.topo.json',
       'duracao':span,'camera':'roi','rasters':[{'nome':q['raster']}],
       'narracao':{'fatos':[]},'destaques':[],'rotas':[],'clipes':[],
       'rotulos':[{'nome':q['label'],'lonlat':q['lonlat'],'t0':marker_time(span),'t1':span,'estilo':'ponto'}],
       'beats':[{'id':'local','composicao':'atlas.abertura','t':0,'roi':q['roi'],'movimento':'fixo',
                 'prova':'Localização em base cartográfica licenciada; não representa a costa histórica de um evento.',
                 'camadas':[{'id':'local-title','componente':'editorial.titleOrPayoff','slot':'pergunta',
                             't0':.3,'t1':span,'p':{'linhas':location_title(ch,span)}}]}], 'cta':False}
    return A.resolver_tempos(p,[])

def mapclip(ch,span,*,plano_resolvido=None,documentary_layout=False):
    MAP.mkdir(parents=True,exist_ok=True)
    p=plano_resolvido if plano_resolvido is not None else mapplan(ch,span)
    prep=B.preparar(p,0,span,MAP,PUBLIC,documentary_layout=documentary_layout)
    clip=MAP/'mapa.mp4'
    subprocess.run(['npx','--no-install','remotion','render','remotion/src/index.ts','Formato',str(clip.resolve()),
                    '--props='+str((MAP/'props_atlas_formato.json').resolve()),
                    '--frames=0-'+str(prep['frame_fim_inclusivo']),'--codec=h264','--crf=22','--concurrency=1','--public-dir=remotion/public','--log=error'],cwd='motor4',check=True,timeout=420)
    print('E219 MAPA BINARIO',clip.exists(),clip.stat().st_size if clip.exists() else None,flush=True)
    proof=B.confirmar(prep,clip,MAP)
    print('E219 MAPA VALIDADO',proof['duracao_s'],proof['quadros_decodificados'],flush=True)
    return clip,MAP/'comprovante_atlas.json'

def cortes_medidos(inicio,fim,words):
    """Prefer speech boundaries, keeping the existing unverified-action gate.
    Longer shots need real action annotations, never fabricated here.
    """
    minimum,maximum=42,113
    length=fim-inicio
    if length<minimum:raise ValueError('E219-CORTE-CURTO')
    n=math.ceil(length/maximum)
    if length<n*minimum:raise ValueError('E219-CADENCIA-INVIAVEL')
    cuts=[inicio]
    boundaries=sorted({round(w['e']*30) for w in words if inicio<w['e']*30<fim})
    for remaining in range(n-1,0,-1):
        left=cuts[-1]
        lo=max(left+minimum,fim-remaining*maximum)
        hi=min(left+maximum,fim-remaining*minimum)
        target=left+(fim-left)/(remaining+1)
        valid=[b for b in boundaries if lo<=b<=hi]
        chosen=min(valid,key=lambda b:abs(b-target)) if valid else max(lo,min(hi,round(target)))
        cuts.append(chosen)
    cuts.append(fim)
    return cuts

def main():
    spec=read(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);STAGE.mkdir(parents=True,exist_ok=True)
    if spec.get('publish') is not False:raise ValueError('E219-PRIVADO')
    atlas_multiscale={}
    from scripts import qa_atlas_multiscale as G
    for i,ch in enumerate(spec['chapters']):
        q=ch.get('atlas') or {}
        if q.get('multiscale'):
            request=q['multiscale']
            # Explicit, researched location. No model-generated coordinates or rights.
            caso={'id':request['id'],'title':ch['title'],'atlas':q,
                  'fonte_localizacao':request['fonte_localizacao'],'delta':request.get('delta',1.6)}
            acquired_geo=G.adquirir_bases(caso)
            atlas_multiscale[i]=(caso,acquired_geo)
            write(out/('raster-multiescala-'+str(i)+'.json'),acquired_geo)
        elif q.get('regional_base'):
            from scripts.qa_atlas_regional import regional_base
            meta=regional_base(q['raster'],q['regional_base']['bbox'],q['regional_base']['zoom'])
            write(out/'raster-regional.json',meta)
    # Catch structural cartographic errors before spending a voice request.
    for i,ch in enumerate(spec['chapters']):
        if 'atlas' in ch:
            for span in (1.4,3.0,5.5,8.0):
                p=G.resolver(*atlas_multiscale[i],span)[1] if i in atlas_multiscale else mapplan(ch,span)
                B.verificar_plano(p,0,span)
            print('E219 PREFLIGHT ATLAS OK',ch['title'],flush=True)
    rows=[r for ch in spec['chapters'] for r in ch.get('videos',[])]
    acquired={};errors=[]
    if '--acervo-restaurado' in sys.argv[3:]:
        from scripts.restaurar_piloto_e289 import validar_acervo
        acquired,errors=validar_acervo(read(out/'acervo-restaurado.json'),rows,STAGE)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs={pool.submit(acquire,r):r for r in rows}
            for job in concurrent.futures.as_completed(jobs):
                row=jobs[job]
                try:acquired[row[0]]=job.result()
                except Exception as e:errors.append({'id':row[0],'error':str(e)[:300]})
    write(out/'acervo.json',{'acquired':acquired,'errors':errors,'publish':False})
    print('E219 ACERVO',len(acquired),'/',len(rows),flush=True)
    if any(not any(r[0] in acquired for r in ch.get('videos',[])) for ch in spec['chapters'] if 'atlas' not in ch):
        raise ValueError('E219-SEM-REGISTRO-POR-CAPITULO')
    if '--somente-acervo' in sys.argv[3:]:
        # Real sources and candidate windows before voice. This is assisted pilot prep, not semantic approval.
        counts=[];samples=[];rows=[]
        for i,ch in enumerate(spec['chapters']):
            if 'atlas' in ch:
                counts.append({'chapter':ch['title'],'type':'atlas_map','preflight':True})
                continue
            found=[]
            for slug,label in ch.get('videos',[]):
                m=acquired.get(slug)
                if not m:continue
                ww=windows(m,3.8,review_technical=True)
                found.append({'id':slug,'windows':[t for t,_ in ww],'license':m['license']})
                if ww:
                    samples.append(ww[0][1]);rows.append((slug,ww[0][0]))
            counts.append({'chapter':ch['title'],'type':'video','sources':found,'windows':sum(len(f['windows']) for f in found)})
        if samples:
            board=Image.new('RGB',(960,math.ceil(len(samples)/4)*172),'#101c28');draw=ImageDraw.Draw(board)
            for i,im in enumerate(samples):
                im.thumbnail((236,140));x=(i%4)*240;y=(i//4)*172;board.paste(im,(x,y));draw.text((x+4,y+142),rows[i][0][:30],fill='white')
            board.save(out/'fontes-contato.jpg')
        write(out/'preflight-piloto.json',{'publish':False,'narration':False,'semantic_review':'PENDING','direction':'ASSISTED_HISTORICAL','chapters':counts,'sources':len(acquired),'errors':errors})
        if any(x.get('type')=='video' and x['windows']==0 for x in counts):raise ValueError('PILOTO-SEM-JANELAS')
        return
    audio=out/'narracao48k.wav'
    if '--voz-medida-restaurada' in sys.argv[3:]:
        meta=read(out/'voz-original.json')
        if meta.get('publish') is not False or meta.get('script_sha256')!=sha(Path(sys.argv[1])) or meta.get('audio_sha256')!=sha(audio):
            raise ValueError('E289-VOZ-MEDIDA-VINCULO')
        tempos,words=meta['tempos'],meta['words']
    else:
        wav,tempos,caps,dur=voz.narrar([{'fala':c['speech']} for c in spec['chapters']],out/'voz',exigir_gemini=True)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-ar','48000','-ac','1',str(audio)],check=True)
        words=D.palavras_de_caps(caps)
    with wave.open(str(audio),'rb') as f:duration=f.getnframes()/f.getframerate()
    if duration<60 or duration>180 or len(tempos)!=len(spec['chapters']):raise ValueError('E219-DURACAO '+str(duration))
    if '--acervo-restaurado' in sys.argv[3:]:
        # Keep measured voice and its exact script before any map or editorial render.
        write(out/'voz-medida.json',{'publish':False,'script_sha256':sha(Path(sys.argv[1])),
            'audio_sha256':sha(audio),'duration_s':duration,'words':words,'tempos':tempos})
        words,alignment=LS.alinhar_documental(words,audio,maximo=3)
        write(out/'realinhamento.json',alignment)
        # Keep chapter cuts anchored to the same word indices, not a new reading.
        if '--voz-medida-restaurada' in sys.argv[3:]:
            original=meta['words']
            starts=[0.]
            for a,_ in tempos[1:]:
                i=min(range(len(original)),key=lambda i:abs(original[i]['s']-(a+.12)))
                starts.append(max(starts[-1],words[i]['s']-.12))
            tempos=list(zip(starts,starts[1:]+[duration]))
        write(out/'voz-medida.json',{'publish':False,'script_sha256':sha(Path(sys.argv[1])),
            'audio_sha256':sha(audio),'duration_s':duration,'words':words,'tempos':tempos})
        sync=LS.conferir(out/'voz-medida.json',audio,maximo=3)
        write(out/'sincronia-medida.json',sync)
        print('E289 SINCRONIA',alignment,flush=True)
        if not sync['ok']:raise ValueError('E289-SINCRONIA: voz preservada para revisão, não renderizar')
    total=math.ceil(duration*30)/30;start=0;shots=[];media={};maps=[];pics=[];cut_report=[];used_windows={}
    from src.v4.formatos import direcao_eventos as DE
    historico_visual=[];selection_report=[]
    for i,(ch,(a,b)) in enumerate(zip(spec['chapters'],tempos)):
        end=round(b*30) if i+1<len(tempos) else round(total*30)
        frames=end-start
        if 'atlas' in ch:
            span=frames/30
            if not 1.4<=span<=8:raise ValueError('E219-MAPA-DURACAO '+str(span))
            cid='mapa-'+str(i)
            if i in atlas_multiscale:
                map_ch,p,report=G.resolver(*atlas_multiscale[i],span)
                write(out/('camera-multiescala-'+str(i)+'.json'),report)
                clip,proof=mapclip(map_ch,span,plano_resolvido=p)
            else:
                clip,proof=mapclip(ch,span)
            shots.append({'id':cid,'type':'atlas_map','start':start/30,'end':end/30,'headline':ch['atlas']['label'],
                          'lead':ch['title'],'subject':ch['title'],'evidence':'explainer','cues':[{'at':.2,'label':ch['atlas']['label']}]})
            maps.append((cid,clip,proof));start=end;continue
        cuts=cortes_medidos(start,end,words)
        n=len(cuts)-1
        available=[acquired[r[0]] for r in ch['videos'] if r[0] in acquired]
        modes=spec.get('reviewed_source_modes',{})
        available.sort(key=lambda m:m['id'] not in modes)
        for k,(fa,fb) in enumerate(zip(cuts,cuts[1:])):
            s,e=fa/30,fb/30;span=e-s
            if fb-fa<42:raise ValueError('E219-CORTE-CURTO')
            ordered=available[k%len(available):]+available[:k%len(available)]
            selected=None
            if spec.get('perceptual_selection'):
                candidates=[]
                for m in ordered:
                    prev=used_windows.get(m['expected_sha256'],[])
                    for t,im in windows(m,span+.1):
                        if not all(t+span<=a or t>=b for a,b in prev):continue
                        try:
                            samples=[frame(m['local_source'],t+span*f) for f in (.12,.5,.86)]
                            signature=DE.assinatura_janela(samples)
                        except Exception:continue
                        candidates.append({'ordem':len(candidates),'assinatura':signature,'selection':(m,t,im)})
                        # Bound extra decoding; retain two eligible alternatives per source.
                        if sum(c['selection'][0]['id']==m['id'] for c in candidates)>=2:break
                ranked=DE.ordenar_janelas(candidates,historico_visual[-4:])
                if ranked:
                    best=ranked[0];selected=best['selection']
                    score=max((DE.similaridade_janelas(best['assinatura'],h) for h in historico_visual[-4:]),default=0.)
                    historico_visual.append(best['assinatura'])
                    selection_report.append({'chapter':ch['title'],'source':selected[0]['id'],'t':selected[1],
                        'candidate_count':len(ranked),'similarity_recent':round(score,4),'semantic_review':'PENDING'})
            else:
                for m in ordered:
                    prev=used_windows.get(m['expected_sha256'],[])
                    for t,im in windows(m,span+.1):
                        if all(t+span<=a or t>=b for a,b in prev):
                            selected=(m,t,im);break
                    if selected:break
            if not selected:raise ValueError('E219-COBERTURA '+ch['title'])
            m,t,im=selected
            used_windows.setdefault(m['expected_sha256'],[]).append((t,t+span))
            mid=m['id'];media[mid]=m;cid=f'c{i}-{k}'
            shot={'id':cid,'type':'video','asset':mid,'start':s,'end':e,
                  'source_in_seconds':t,'video_zoom':1,'video_context_layout':'cena_integral',
                  'lead':ch['title'] if k==0 else '', 'headline':m['label'],'subject':m['subject'],
                  'source_display':m['credit'],'evidence':'literal','literal_identity':m['subject'],
                  'cues':[{'at':.2,'label':m['label']}]}
            # Reuse the candidate visual grammar of the reviewed source, only
            # for the opening window within the length of the previous proof.
            # This is still private review, NOT observed ROI certification.
            mode=modes.get(mid)
            reference=windows(m,4.6) if mode else []
            if reference and abs(t-reference[0][0])<.01 and span<=4.5:
                if mode=='imersivo':
                    shot.pop('video_context_layout')
                elif mode in ('4:5','1:1'):
                    shot['video_context_layout']='recorte_relacional_seguro'
                    shot['documentary_viewport']=mode
                shot['focus']=[.5,.5]
            shots.append(shot)
            pics.append((cid,m['id'],t,im))
        cut_report.append({'chapter':ch['title'],'start':start/30,'end':end/30,'shots':n})
        start=end
    plan={'formato':'filme_editorial','tipo':'PROVA_VISUAL_PRIVADA','publicar':False,'titulo':spec['title'],
          'duracao':total,'media':media,'shots':shots}
    if '--acervo-restaurado' in sys.argv[3:]:
        plan['documentary_framing']='ADAPTIVE_REVIEW_V1'
    for cid,clip,proof in maps:plan=B.inserir_no_filme(plan,cid,clip,proof)
    write(out/'plano.json',plan)
    if spec.get('perceptual_selection'):write(out/'selecao_perceptiva.json',selection_report)
    result=F.preparar(plan,out/'documental',PUBLIC)
    props=read(result['props']);props['private_review_only']=True;props.pop('safe_area_profile',None)
    groups=[]
    for g in LS.grupos(words,maximo=3):
        ws=words[g['i0']:g['i0']+g['n']];hi=max(range(len(ws)),key=lambda i:len(ws[i]['w']))
        a=max(0,g['ini']);b=min(duration,g['fim'])
        if groups:a=max(a,groups[-1]['end'])
        if b>a:groups.append({'start':a,'end':b,'words':[{'w':w['w'],'hl':i==hi} for i,w in enumerate(ws)]})
    original_sha=sha(audio)
    track=Path('assets/musica/explica/infinite-wonder.mp3')
    if spec.get('review_music'):
        mixed=out/'narracao-com-trilha.wav'
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(audio),'-stream_loop','-1','-i',str(track),
            '-filter_complex',f'[0:a]volume=0.92[v];[1:a]volume=0.055,afade=t=in:d=0.5,afade=t=out:st={max(0,duration-2)}:d=2[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]',
            '-map','[a]','-ar','48000','-ac','1',str(mixed)],check=True,timeout=90)
        write(out/'trilha.json',{'track':str(track),'sha256':sha(track),'voice_sha256':original_sha,'mix_sha256':sha(mixed),'gain_music':.055,'license_manifest':'assets/musica/LEIAME.txt','review':'PENDING'})
        audio=mixed
    h=sha(audio);asset='e202/'+h+'.wav'
    (PUBLIC/'e202').mkdir(exist_ok=True);shutil.copyfile(audio,PUBLIC/asset)
    props=D.anexar_audio_documental(props,asset,groups,PUBLIC,'PALAVRAS_MEDIDAS')
    write(out/'props.json',props);write(out/'narracao.json',{'audio_sha256':h,'voice_sha256':original_sha,'duration_s':duration,'words':words,'chapters':cut_report,'publish':False})
    board=Image.new('RGB',(960,math.ceil(len(pics)/4)*172),'#101c28');draw=ImageDraw.Draw(board)
    for i,(cid,mid,t,im) in enumerate(pics):
        im.thumbnail((236,140));x=(i%4)*240;y=(i//4)*172;board.paste(im,(x,y))
        draw.text((x+4,y+141),cid+' '+str(t)+'s '+mid[:15],fill='white')
    board.save(out/'fontes-contato.jpg')
    for _,clip,proof in maps:shutil.copyfile(proof,out/'comprovante_atlas.json')
    print('E219 PREPARADO',total,len(shots),len(maps),'mapas, Gemini',flush=True)
if __name__=='__main__':main()
