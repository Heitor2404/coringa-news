"""Distributed local sampling for the existing documentary video reviewer.
Bounded work, no new AI dependency, no assertion of semantic coverage.
"""
import math
import re
import shutil
import subprocess
from pathlib import Path
from PIL import ImageChops, ImageStat
from . import direcao_eventos as DE

# ---------------------------------------------------------------------------
# Varredura temporal local (gratuita) antes de qualquer visão externa.
# Uma passada FFmpeg em baixa resolução cobre o arquivo INTEIRO: detecta cortes,
# separa movimento global da câmera (afim estimada do fluxo óptico) do movimento
# residual do referente e devolve planos. São PISTAS de ranking: não provam a
# ação pedida nem a ausência dela (E281.2: três janelas uniformes de um arquivo
# de 496 s caíram em planos sem a decolagem).
# ---------------------------------------------------------------------------

def sondar_video(caminho,*,timeout=120):
    """Real duration and dimensions from the container AND a demux-only packet pass.

    Declared metadata can be wrong (truncated uploads, broken containers). The
    packet pass reads timestamps only (no decoding), streamed line by line, so
    memory stays constant for any length. Returns None when nothing is readable.
    """
    import json as _json
    if not shutil.which('ffprobe'):return None
    p=str(caminho)
    try:
        info=_json.loads(subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries',
            'stream=width,height,duration,avg_frame_rate,r_frame_rate:format=duration','-of','json',p],capture_output=True,text=True,timeout=60).stdout or '{}')
    except (subprocess.SubprocessError,OSError,ValueError):
        return None
    st=(info.get('streams') or [{}])[0]
    w,h=st.get('width'),st.get('height')
    def num(v):
        try:
            v=float(v);return v if math.isfinite(v) and v>0 else None
        except (TypeError,ValueError):return None
    declarada=num(st.get('duration')) or num((info.get('format') or {}).get('duration'))
    t0=t1=None;n=0
    try:
        pr=subprocess.Popen(['ffprobe','-v','error','-select_streams','v:0','-show_entries','packet=pts_time',
                             '-of','csv=p=0',p],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        try:
            for line in pr.stdout:
                v=num(line.strip().split(',')[0]) if line.strip() not in ('','N/A') else None
                if v is None and line.strip().startswith('0'):v=0.
                if v is None:continue
                n+=1;t0=v if t0 is None else min(t0,v);t1=v if t1 is None else max(t1,v)
            pr.wait(timeout=timeout)
        finally:
            if pr.poll() is None:pr.kill()
    except (subprocess.SubprocessError,OSError):
        pass
    observada=(t1-(t0 or 0.))+1/30 if t1 is not None and n>1 else None
    if observada is None:observada=duracao_por_demux(p)
    if not (isinstance(w,int) and isinstance(h,int) and w>0 and h>0):return None
    def taxa(v):
        try:
            a,b=str(v).split('/');r=float(a)/float(b);return r if math.isfinite(r) and r>0 else None
        except (ValueError,ZeroDivisionError):return None
    fps_origem=taxa(st.get('avg_frame_rate')) or taxa(st.get('r_frame_rate'))
    if not fps_origem and n>1 and observada:fps_origem=n/observada
    return {'largura':w,'altura':h,'fps_origem':fps_origem,'duracao_declarada':declarada,'duracao_observada':observada,'pacotes':n,
            'inconsistente':bool(declarada and observada and abs(declarada-observada)>max(1.,.05*observada))}


def duracao_por_demux(caminho,*,timeout=300):
    """Last resort: copy-demux the video stream (no decoding) and read FFmpeg's progress clock."""
    t=None
    try:
        pr=subprocess.Popen(['ffmpeg','-v','error','-nostats','-i',str(caminho),'-map','0:v:0','-c','copy','-f','null','-',
                             '-progress','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        try:
            for line in pr.stdout:
                if line.startswith('out_time_us='):
                    try:t=max(t or 0.,int(line.split('=')[1])/1e6)
                    except ValueError:pass
            pr.wait(timeout=timeout)
        finally:
            if pr.poll() is None:pr.kill()
    except (subprocess.SubprocessError,OSError):
        return None
    return t if t and t>0 else None


def _dims_varredura(w0,h0,largura):
    """Scan size for ANY aspect ratio: long side bounded, both sides >=16 and even."""
    r=h0/w0
    if r<=1:w=int(largura);h=int(round(w*r/2))*2
    else:h=int(largura);w=int(round(h/r/2))*2
    return max(16,w),max(16,h)


def _metricas_par(a,b,dt,w,h,pts,cv2,np):
    ha=np.bincount(a.ravel()>>3,minlength=32)/a.size
    hb=np.bincount(b.ravel()>>3,minlength=32)/b.size
    hist=float(np.abs(ha-hb).sum()/2)
    dif=float(np.abs(a.astype(np.int16)-b.astype(np.int16)).mean())
    flow=cv2.calcOpticalFlowFarneback(a,b,None,.5,4,21,3,5,1.1,0)
    vec=flow[pts[:,1].astype(int),pts[:,0].astype(int)]
    try:
        M,_=cv2.estimateAffinePartial2D(pts,pts+vec,method=cv2.RANSAC,ransacReprojThreshold=1.0)
    except cv2.error:
        M=None
    glob=np.zeros_like(vec) if M is None else pts@M[:,:2].T+M[:,2]-pts
    res=np.linalg.norm(vec-glob,axis=1)
    cam=float(np.linalg.norm(glob,axis=1).mean())
    # Difference left after compensating the estimated camera motion. A pan
    # or zoom is explained by the affine model; a cut is not (new content).
    if M is not None:
        warp=cv2.warpAffine(a,M.astype(np.float32),(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        m8=max(2,min(w,h)//16)
        comp=float(np.abs(warp[m8:-m8,m8:-m8].astype(np.int16)-b[m8:-m8,m8:-m8].astype(np.int16)).mean())
    else:
        comp=dif
    # Pixel units at the scan size, converted to fraction of the long side per second.
    # p99 keeps a small moving referent visible against a static frame.
    k=1/(dt*max(w,h))
    return {'corte':bool(hist>.42 or (comp>22 and comp>.55*dif)),'dif_compensada':round(comp,3),
            'referente':round(float(np.percentile(res,99))*k,5),'area_referente':round(float((res>1.).mean()),4),
            'camera':round(cam*k,5),'dif':round(dif,3),'textura':round(float(a.std()),2)}


def _descritor(fr,cv2):
    return [int(v) for v in cv2.resize(fr,(8,8),interpolation=cv2.INTER_AREA).ravel()]


def distancia_descritores(a,b):
    """Mean absolute difference of 8x8 luminance layouts, 0..1 (appearance novelty hint)."""
    if not a or not b or len(a)!=len(b):return 1.
    return sum(abs(x-y) for x,y in zip(a,b))/(255.*len(a))


def _ordem_hierarquica(k):
    """Coarse-to-fine order (van der Corput): any prefix spans the WHOLE file."""
    def vdc(i):
        x,d=0.,.5
        while i:
            if i&1:x+=d
            i>>=1;d/=2
        return x
    return sorted(range(k),key=lambda i:(vdc(i),i))


def varrer(caminho,duracao,*,largura_origem=None,altura_origem=None,largura=160,max_quadros=720,
           tempo_max_s=240.,timeout=600):
    """Bounded local scan of the WHOLE file; compact per-pair motion series, or None.

    Two strategies with the same output contract and a HARD cap of max_quadros
    decoded frames, whatever the length or declared metadata:
    - continuous: one streamed FFmpeg pass at fps=min(4, cap/duration) when that
      still gives >=1 fps; frames are consumed one at a time (constant memory);
    - hierarchical anchors: for longer files, cap//2 short frame pairs spread over
      the observed duration in coarse-to-fine order; a time budget can stop it
      early but every prefix still spans the whole file (coverage is reported).
    """
    import time as _time
    import numpy as np
    try:
        import cv2
    except ImportError:
        return None
    p=Path(str(caminho))
    if not p.is_file() or not shutil.which('ffmpeg'):return None
    if type(max_quadros) is not int or max_quadros<4:raise ValueError('E283-VARREDURA-LIMITE')
    probe=sondar_video(p)
    w0=(probe or {}).get('largura') or largura_origem or 16
    h0=(probe or {}).get('altura') or altura_origem or 9
    candidatos=[x for x in ((probe or {}).get('duracao_observada'),duracao if isinstance(duracao,(int,float)) and math.isfinite(duracao) else None,
                            (probe or {}).get('duracao_declarada')) if x]
    if not candidatos:return None
    dur=float(candidatos[0])
    if dur<1.55:return None
    w,h=_dims_varredura(w0,h0,largura)
    tam=w*h
    mx,my=max(4,w//8),max(4,h//8)
    ys,xs=np.mgrid[my:h-my:3,mx:w-mx:3]
    pts=np.stack([xs.ravel(),ys.ravel()],1).astype(np.float32)
    vf=f'scale={w}:{h},format=gray'
    pares=[];inicio=_time.monotonic();decodificados=0
    fps=min(4.,max_quadros/dur,(probe or {}).get('fps_origem') or 4.)
    modo='continuo' if fps>=min(1.,(probe or {}).get('fps_origem') or 1.) and max_quadros/dur>=1. else 'ancoras'
    if modo=='continuo':
        try:
            pr=subprocess.Popen(['ffmpeg','-v','error','-i',str(p),'-an','-vf',f'fps={fps:.5f},{vf}','-f','rawvideo','-pix_fmt','gray','-'],
                                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        except OSError:
            return None
        prev=None;i=0
        try:
            while True:
                buf=pr.stdout.read(tam)
                if len(buf)<tam:break
                decodificados+=1
                if decodificados>max_quadros:break   # wrong metadata: never exceed the cap
                fr=np.frombuffer(buf,np.uint8).reshape(h,w)
                if prev is not None:
                    q=_metricas_par(prev,fr,1/fps,w,h,pts,cv2,np)
                    pares.append({'t':round((i-.5)/fps,3),**q,'descritor':_descritor(fr,cv2)})
                prev=fr;i+=1
                if _time.monotonic()-inicio>timeout:break
        finally:
            if pr.poll() is None:pr.kill()
            pr.wait()
        if decodificados>max_quadros:
            # Real duration far above the declared/probed one: measure it without
            # decoding and switch to anchors spanning the WHOLE real stream.
            real=duracao_por_demux(p)
            if not real or real<=dur:return None
            dur=float(real);pares=[];decodificados=0;modo='ancoras'
            if probe is not None:probe['inconsistente']=True
    if modo=='ancoras':
        k=max(2,max_quadros//2)
        # Two DISTINCT source frames per anchor: never resample above the source rate
        # (duplicated frames would hide real motion).
        fps_par=min(4.,(probe or {}).get('fps_origem') or 4.)
        dt=1/fps_par
        fim=max(.0,dur-2*dt-.1)
        tempos=[fim*(j+.5)/k for j in range(k)]
        for j in _ordem_hierarquica(k):
            if _time.monotonic()-inicio>tempo_max_s:break
            t=tempos[j]
            try:
                raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',str(p),'-an','-frames:v','2','-vf',f'fps={fps_par:.4f},{vf}',
                                    '-f','rawvideo','-pix_fmt','gray','-'],capture_output=True,timeout=60).stdout
            except (subprocess.SubprocessError,OSError):
                continue
            if len(raw)<2*tam:continue
            decodificados+=2
            a=np.frombuffer(raw[:tam],np.uint8).reshape(h,w);b=np.frombuffer(raw[tam:2*tam],np.uint8).reshape(h,w)
            q=_metricas_par(a,b,dt,w,h,pts,cv2,np)
            pares.append({'t':round(t+dt/2,3),**q,'descritor':_descritor(b,cv2),'ancora':True})
        pares.sort(key=lambda q:q['t'])
        # Between sparse anchors a shot change is only inferred from appearance.
        for x,y in zip(pares,pares[1:]):
            if distancia_descritores(x['descritor'],y['descritor'])>.18:y['corte_inferido']=True
    if len(pares)<1:return None
    limite=lambda q:q['corte'] or q.get('corte_inferido')
    planos=[];ini=0.
    for q in pares:
        if limite(q):
            planos.append([ini,q['t']]);ini=q['t']
    planos.append([ini,dur])
    # Consecutive cut flags in under ~0.8 s are one gradual transition (dissolve,
    # wipe, flash), not several shots; they are reported separately.
    transicoes=[[round(a,3),round(b,3)] for a,b in planos if b-a<.8 and a>0 and b<dur]
    planos=[[round(a,3),round(b,3)] for a,b in planos if b-a>=.8 or len(planos)==1]
    _segmentar_eventos(pares,planos)
    cobertos=sorted(q['t'] for q in pares)
    lacuna=max([cobertos[0],*(b-a for a,b in zip(cobertos,cobertos[1:])),dur-cobertos[-1]])
    return {'modo':modo,'fps':round(fps,4) if modo=='continuo' else None,'largura':w,'altura':h,
            'quadros':decodificados,'limite_quadros':max_quadros,'pares':pares,'planos':planos,'transicoes':transicoes,
            'cortes':sum(bool(limite(q)) for q in pares),'duracao_varrida_s':round(dur,3),
            'maior_lacuna_s':round(lacuna,3),'metadados_inconsistentes':bool((probe or {}).get('inconsistente')),
            'duracao_declarada_s':(probe or {}).get('duracao_declarada'),'prova_semantica':False}


def _segmentar_eventos(pares,planos):
    """Split shots into temporally distinct events: activity onsets and gradual
    appearance drift. A long fixed-camera shot can hold several happenings."""
    if not pares:return
    refs=sorted(q['referente'] for q in pares)
    ativo_min=max(.004,3*refs[len(refs)//2])
    ev=-1;plano_atual=None;base=None;ativo=None
    for q in pares:
        pl=next((i for i,(x,y) in enumerate(planos) if x<=q['t']<y),len(planos)-1)
        at=q['referente']>=ativo_min
        novo=pl!=plano_atual or base is None or (at and not ativo) or distancia_descritores(base,q['descritor'])>.06
        if novo:
            ev+=1;base=q['descritor']
        q['evento']=ev;plano_atual=pl;ativo=at


_MARCA=re.compile(r'(?<![\d:])(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?![\d:])')

def marcas_temporais(texto,duracao,termos=()):
    """Timestamps declared in metadata (chapters, shot lists). Relevance = shared terms with the need, never proof."""
    if not isinstance(texto,str) or not texto.strip():return []
    words=lambda v:{w for w in re.findall(r'[a-zà-ÿ0-9]{4,}',str(v).lower())}
    alvo=set()
    for t in termos or ():alvo|=words(t)
    out=[]
    for m in _MARCA.finditer(texto):
        hh,mm,ss=int(m.group(1) or 0),int(m.group(2)),int(m.group(3))
        if ss>59 or (m.group(1) and mm>59):continue
        t=hh*3600+mm*60+ss
        if not 0<=t<duracao:continue
        fim=texto.find('\n',m.end())
        trecho=texto[m.end():fim if fim>=0 else m.end()+160][:160]
        comum=sorted(words(trecho)&alvo)
        out.append({'t':float(t),'trecho':trecho.strip(),'termos_comuns':comum})
    return out


def _janela_movimento(varredura,a,span):
    pares=[q for q in varredura['pares'] if a<=q['t']<=a+span]
    if not pares:return None
    # Robust to a single pair where flow/RANSAC fails (duplicated or dropped frames).
    ordenar=lambda k:sorted(q[k] for q in pares)
    cam=ordenar('camera')[len(pares)//2]
    ref=ordenar('referente')[min(len(pares)-1,(3*len(pares))//4)]
    meio=min(pares,key=lambda q:abs(q['t']-(a+span/2)))
    plano=next((i for i,(x,y) in enumerate(varredura['planos']) if x<=a+span/2<y),None)
    dominante=bool(cam>2.5*max(ref,1e-4) and cam>.02)
    corte=any(q['corte'] for q in pares)
    return {'referente':round(ref,5),'pico_referente':round(max(q['referente'] for q in pares),5),'camera':round(cam,5),
            'camera_dominante':dominante,
            # Camera FOLLOWING a referent: global motion explained by the background while a
            # compact region keeps residual motion (a pure pan over a static scene has ~none).
            'acompanhada':bool(dominante and not corte and ref>=.15*cam and ref>.01),
            'corte_na_janela':corte,'plano':plano,'evento':meio.get('evento'),'descritor':meio.get('descritor'),
            # Appearance drift only means a gradual transformation when the camera is still.
            'deriva':round(distancia_descritores(pares[0].get('descritor'),pares[-1].get('descritor')),4) if len(pares)>1 and not dominante and not corte else 0.,
            'parado':bool(max(q['dif'] for q in pares)<.6),'prova_semantica':False}


def _inicios_por_planos(varredura,dur,span,max_janelas,marcas):
    """Windows inside shots (never straddling a detected cut): best window of each
    distinct EVENT (not only each shot), metadata marks, then temporal coverage."""
    end=max(0.,dur-span-.05)
    starts=set()
    for i,(x,y) in enumerate(varredura['planos']):
        if y-x<span+.1:continue
        a=x+.05
        while a+span<=y-.05+1e-9 and a<=end+1e-9:
            starts.add(round(a,3));a+=max(span/2,.5)
    for q in varredura['pares']:          # sparse anchors: windows centred on observed samples
        starts.add(round(min(max(0.,q['t']-span/2),end),3))
    cand=[]
    for a in sorted(starts):
        mv=_janela_movimento(varredura,a,span)
        if mv and not mv['corte_na_janela']:cand.append((a,mv))
    escolhidos=[]
    def add(a):
        a=round(min(max(0.,a),end),3)
        if all(abs(a-b)>=span*.6 for b in escolhidos):escolhidos.append(a)
    # 1) declared metadata marks relevant to the need
    for mk in sorted(marcas,key=lambda m:-len(m['termos_comuns'])):
        if mk['termos_comuns'] and len(escolhidos)<max_janelas//3:add(mk['t'])
    # 2) best window of each event: subject motion, gradual drift or followed action
    best={}
    for a,mv in cand:
        sc=max(mv['referente']*(.35 if mv['camera_dominante'] and not mv['acompanhada'] else 1.),mv['deriva']*.5)
        k=(mv['plano'],mv['evento'])
        if k not in best or sc>best[k][0]:best[k]=(sc,a)
    for sc,a in sorted(best.values(),reverse=True):
        if len(escolhidos)>=max_janelas*3//4:break
        add(a)
    # 3) temporal coverage so quiet or slow actions remain reachable
    k=max_janelas-len(escolhidos)
    for j in range(max(0,k)*3):
        if len(escolhidos)>=max_janelas:break
        add(end*((j*0.61803398875)%1.))
    if not escolhidos:add(0.)
    return sorted(escolhidos)


def explorar(midia,extrair,*,max_janelas=12,largura=240,varredura=None,marcas=None):
    dur=midia['duration_s']
    if not isinstance(dur,(int,float)) or not math.isfinite(dur) or dur<1.55:raise ValueError('E257-DURACAO')
    if not 3<=max_janelas<=24:raise ValueError('E257-LIMITE')
    span=min(3.8,dur-.15)
    end=max(0,dur-span-.05)
    if varredura is None and midia.get('varredura_local',True):
        varredura=varrer(midia.get('local_source'),dur,largura_origem=midia.get('width'),altura_origem=midia.get('height'))
    marcas=marcas if marcas is not None else marcas_temporais(midia.get('metadados_texto'),dur,midia.get('termos_necessidade') or ())
    if varredura and varredura.get('duracao_varrida_s') and varredura['duracao_varrida_s']+.05<dur:
        # Declared duration longer than the decodable stream: never place windows past the real end.
        end=max(0,min(end,varredura['duracao_varrida_s']-span-.05))
    if varredura and end>=.5:
        starts=_inicios_por_planos(varredura,min(dur,end+span+.05),span,max_janelas,marcas)
    else:
        count=1 if end<.5 else min(max_janelas,max(1,math.ceil(end/max(span*.65,1))+1))
        starts=[end*i/max(1,count-1) for i in range(count)]
    rows=[]
    for a in starts:
        try:
            frames=[extrair(midia['local_source'],a+span*f,width=largura) for f in (0,.5,.9)]
            diag=DE.diagnosticar_janela(frames)
            # Difference is a hint, not semantic motion (camera and cuts may dominate).
            diffs=[ImageStat.Stat(ImageChops.difference(x.convert('RGB'),y.convert('RGB'))).mean for x,y in zip(frames,frames[1:])]
            change=sum(sum(d)/3 for d in diffs)/max(1,len(diffs))
            contrast=min(ImageStat.Stat(im.convert('L')).stddev[0] for im in frames)
            row={'inicio_s':a,'duracao_s':span,'diagnostico':diag,
                 'pares_alterados':sum(any(d) for d in diffs),
                 'mudanca_px':round(change,3),'contraste_min':round(contrast,3)}
            mv=_janela_movimento(varredura,a,span) if varredura else None
            if mv:row['movimento_local']=mv
            mk=[m for m in marcas if m['termos_comuns'] and a-.5<=m['t']<=a+span]
            if mk:row['marca_metadado']=mk[0]
            rows.append(row)
        except Exception as e:
            rows.append({'inicio_s':a,'duracao_s':span,'falha':type(e).__name__})
    out={'duracao_origem_s':dur,'janelas':rows,'amostragem_distribuida':True,
         'cobertura_semantica_integral':False,'publicar':False}
    if varredura:
        out['varredura_local']={k:varredura.get(k) for k in ('modo','fps','quadros','limite_quadros','cortes','duracao_varrida_s',
                                'maior_lacuna_s','metadados_inconsistentes','duracao_declarada_s')}
        out['varredura_local'].update(planos=varredura['planos'][:200],transicoes=varredura.get('transicoes',[])[:100],
                                      eventos=len({q.get('evento') for q in varredura['pares']}),prova_semantica=False)
    elif midia.get('varredura_local',True):
        out['varredura_local']={'estado':'INDISPONIVEL','recuperacao':'GRADE_UNIFORME_HISTORICA','prova_semantica':False}
    if marcas:out['marcas_metadado']=marcas[:20]
    return out

def selecionar(exploracao,*,limite=3,priorizar_movimento=False):
    rows=[x for x in exploracao['janelas'] if 'diagnostico' in x]
    if not rows:return []
    # Prefer one candidate per temporal region, not three nearby early windows.
    # Dark/quiet real footage remains eligible; motion is only a ranking hint.
    local=all('movimento_local' in r for r in rows)
    def rank(r):
        if local and priorizar_movimento:
            mv=r['movimento_local']
            # Subject motion after removing the camera's global motion; a cut or
            # a pure pan/zoom is not the referent's action (pixel change is not semantics).
            return (r['diagnostico']['quadros_grafismo_suspeito'],
                    r['contraste_min']<5,
                    not r.get('marca_metadado'),
                    mv['corte_na_janela'] or (mv['parado'] and mv.get('deriva',0)<.02),
                    mv['camera_dominante'] and not mv.get('acompanhada'),
                    -max(mv['referente'],mv.get('deriva',0)*.5))
        return (r['diagnostico']['quadros_grafismo_suspeito'],
                r['contraste_min']<5,
                -r.get('pares_alterados', 0) if priorizar_movimento else 0,
                -r['mudanca_px'] if priorizar_movimento else -r['contraste_min'])
    result=[]
    dur=exploracao['duracao_origem_s']
    if local:
        # Diversity across distinct EVENTS (a long fixed shot can hold several),
        # not fixed thirds of the timeline nor one window per shot.
        vistos=[]
        for r in sorted(rows,key=rank):
            mv=r['movimento_local'];p=(mv['plano'],mv.get('evento'))
            if p in vistos:continue
            vistos.append(p);result.append(r)
            if len(result)>=limite:break
    else:
        for j in range(limite):
            region=[r for r in rows if min(limite-1,int((r['inicio_s']+r['duracao_s']/2)/dur*limite))==j]
            if region:result.append(min(region,key=rank))
    for r in sorted(rows,key=rank):
        if len(result)>=limite:break
        if r not in result:result.append(r)
    return sorted(result,key=lambda r:r['inicio_s'])

def preparar_lote(midia,necessidade,extrair,*,exploracao=None,excluir=(),priorizar_cache=(),inicios_exatos=None):
    exploration=exploracao if exploracao is not None else explorar(midia,extrair)
    if priorizar_cache:
        # Reuse must not depend on the exploration grid: a previously reviewed
        # start absent from the current grid is re-added at its exact time, so
        # the same pixels regenerate the same revision ID. The ID hashes the
        # EXACT start, so the stored float is used, never its rounded key.
        dur=exploration['duracao_origem_s'];span=min(3.8,dur-.15)
        # Rounded keys may collide (two exact starts < 0.5e-4 s apart): each exact
        # start is restored on its own; a grid row only counts if it is EXACTLY equal.
        have={x['inicio_s'] for x in exploration['janelas']}
        exatos=inicios_exatos or {}
        pendentes=[]
        for chave in sorted(set(priorizar_cache)):
            vals=exatos.get(chave,[chave])
            vals=vals if isinstance(vals,(list,tuple,set)) else [vals]
            pendentes+=[float(v) for v in vals if round(float(v),4)==chave and float(v) not in have]
        for a in sorted(set(pendentes)):
            if not 0<=a<=dur-span:continue
            try:
                frames=[extrair(midia['local_source'],a+span*f,width=240) for f in (0,.5,.9)]
                diffs=[ImageStat.Stat(ImageChops.difference(x.convert('RGB'),y.convert('RGB'))).mean for x,y in zip(frames,frames[1:])]
                exploration['janelas'].append({'inicio_s':a,'duracao_s':span,'diagnostico':DE.diagnosticar_janela(frames),
                    'pares_alterados':sum(any(d) for d in diffs),'mudanca_px':round(sum(sum(d)/3 for d in diffs)/max(1,len(diffs)),3),
                    'contraste_min':round(min(ImageStat.Stat(im.convert('L')).stddev[0] for im in frames),3),'origem':'checkpoint'})
            except Exception as e:
                exploration['janelas'].append({'inicio_s':a,'duracao_s':span,'falha':type(e).__name__,'origem':'checkpoint'})
        exploration['janelas'].sort(key=lambda x:x['inicio_s'])
    remaining={**exploration,'janelas':[x for x in exploration['janelas'] if round(x['inicio_s'],4) not in excluir]}
    selected=selecionar(remaining,priorizar_movimento=necessidade.get('evidencia_visual')=='movimento')
    if priorizar_cache:
        # Cache starts are hints only: the caller must regenerate each
        # observation and verify the full revision ID and original SHA.
        preferred=set(priorizar_cache)
        candidates=[x for x in remaining['janelas'] if 'diagnostico' in x and round(x['inicio_s'],4) in preferred]
        selected_cached=[x for x in selected if x in candidates]
        other_cached=[x for x in candidates if x not in selected_cached]
        selected=(selected_cached+other_cached+[x for x in selected if x not in selected_cached])[:3]
        selected.sort(key=lambda x:x['inicio_s'])
    windows=[]
    for x in selected:
        a=x['inicio_s'];span=x['duracao_s']
        try:
            frames=[extrair(midia['local_source'],a+span*f,width=min(768,midia['width'])) for f in (0,.5,.9)]
            p=DE.pacote_observacao(midia,a,span,frames,fato_id=necessidade['fatos'][0],
                necessidade=necessidade['mostrar'],fracoes=(0,.5,.9))
            p['diagnostico_tecnico']=DE.diagnosticar_janela(frames)
            windows.append((p,frames))
        except Exception as e:
            x['falha_amostra_visao']=type(e).__name__
    exploration['selecionadas_s']=[p['inicio_s'] for p,_ in windows]
    return exploration,windows


def consolidar_janelas(anteriores, atuais):
    """Preserve invalid observations across restarts without replacing a decision."""
    rows = {}
    for row in (*anteriores, *atuais):
        key = (row.get('pacote') or {}).get('revisao_id')
        if not key:
            continue
        if row.get('decisao') or ('resposta_invalida' in row and not rows.get(key, {}).get('decisao')):
            rows[key] = row
    return list(rows.values())


def ha_janelas_promissoras(exploracao,vistos,*,priorizar_movimento=False,gratuitas=()):
    """Whether another batch on the SAME file is worth more than a new candidate.

    Without a local scan, keep the historical rule (any unseen window). With a
    scan and a motion need, an unseen window justifies another look when it lies
    in an EVENT not yet observed (same shot allowed: a fixed camera can record
    several happenings) and shows a local signal: subject motion comparable to
    what was seen, gradual appearance drift (slow/low-intensity change), a
    followed action, or a relevant metadata mark. Absent such signals, a new
    candidate is preferred (E281.2: two batches on one 496 s clip). These are
    ranking hints, never semantic proof nor proof of absence.
    """
    rows=[x for x in exploracao.get('janelas',[]) if 'diagnostico' in x]
    unseen=[x for x in rows if round(x['inicio_s'],4) not in vistos]
    if not unseen:return False
    # An unseen window with a stored private analysis costs no new call.
    if any(round(x['inicio_s'],4) in set(gratuitas) for x in unseen):return True
    if not priorizar_movimento or not all('movimento_local' in x for x in rows):return True
    seen=[x for x in rows if round(x['inicio_s'],4) in vistos]
    eventos_vistos={(x['movimento_local']['plano'],x['movimento_local'].get('evento')) for x in seen}
    ref_vista=max([x['movimento_local']['referente'] for x in seen] or [0.])
    for x in unseen:
        mv=x['movimento_local']
        if x.get('marca_metadado'):return True
        if mv['corte_na_janela']:continue
        if any(abs(x['inicio_s']-y['inicio_s'])<x['duracao_s']*.6 for y in seen):continue
        if (mv['plano'],mv.get('evento')) in eventos_vistos and mv.get('evento') is not None:continue
        if mv.get('evento') is None and mv['plano'] in {y['movimento_local']['plano'] for y in seen}:continue
        if mv.get('acompanhada') or mv.get('deriva',0)>=.02:return True
        if not mv['parado'] and not (mv['camera_dominante'] and not mv.get('acompanhada')) and mv['referente']>=.5*ref_vista:return True
    return False
