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

def varrer(caminho,duracao,*,largura_origem=None,altura_origem=None,largura=160,max_quadros=720,timeout=600):
    """Return compact per-pair motion series for the whole file, or None if unavailable."""
    import numpy as np
    try:
        import cv2
    except ImportError:
        return None
    p=Path(str(caminho))
    if not p.is_file() or not shutil.which('ffmpeg'):return None
    if not isinstance(duracao,(int,float)) or not math.isfinite(duracao) or duracao<1.55:return None
    fps=max(.5,min(4.,max_quadros/float(duracao)))
    w=int(largura)
    ratio=(altura_origem/largura_origem) if largura_origem and altura_origem else 9/16
    h=max(16,int(round(w*ratio/2))*2)
    try:
        raw=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-an','-vf',f'fps={fps:.4f},scale={w}:{h},format=gray',
                            '-f','rawvideo','-pix_fmt','gray','-'],capture_output=True,timeout=timeout,check=True).stdout
    except (subprocess.SubprocessError,OSError):
        return None
    n=len(raw)//(w*h)
    if n<2:return None
    fr=np.frombuffer(raw[:n*w*h],np.uint8).reshape(n,h,w)
    # Interior grid only: content entering at the borders during a pan is not referent motion.
    mx,my=max(4,w//8),max(4,h//8)
    ys,xs=np.mgrid[my:h-my:3,mx:w-mx:3]
    pts=np.stack([xs.ravel(),ys.ravel()],1).astype(np.float32)
    pares=[]
    for i in range(n-1):
        a,b=fr[i],fr[i+1]
        ha=np.bincount(a.ravel()>>3,minlength=32)/a.size
        hb=np.bincount(b.ravel()>>3,minlength=32)/b.size
        hist=float(np.abs(ha-hb).sum()/2)
        dif=float(np.abs(a.astype(np.int16)-b.astype(np.int16)).mean())
        flow=cv2.calcOpticalFlowFarneback(a,b,None,.5,4,21,3,5,1.1,0)
        vec=flow[pts[:,1].astype(int),pts[:,0].astype(int)]
        dst=pts+vec
        M,_=cv2.estimateAffinePartial2D(pts,dst,method=cv2.RANSAC,ransacReprojThreshold=1.0)
        if M is None:
            glob=np.zeros_like(vec)
        else:
            glob=pts@M[:,:2].T+M[:,2]-pts
        res=np.linalg.norm(vec-glob,axis=1)
        cam=float(np.linalg.norm(glob,axis=1).mean())
        textura=float(a.std())
        # Difference left after compensating the estimated camera motion. A pan
        # or zoom is explained by the affine model; a cut is not (new content).
        if M is not None:
            warp=cv2.warpAffine(a,M.astype(np.float32),(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            m8=max(2,w//16)
            comp=float(np.abs(warp[m8:-m8,m8:-m8].astype(np.int16)-b[m8:-m8,m8:-m8].astype(np.int16)).mean())
        else:
            comp=dif
        corte=bool(hist>.42 or (comp>22 and comp>.55*dif))
        # Pixel units at the scan width, converted to fraction of width per second.
        # p99 keeps a small moving referent visible against a static frame.
        k=fps/w
        pares.append({'t':round((i+.5)/fps,3),'corte':corte,'dif_compensada':round(comp,3),
                      'referente':round(float(np.percentile(res,99))*k,5),
                      'area_referente':round(float((res>1.).mean()),4),
                      'camera':round(cam*k,5),'dif':round(dif,3),'textura':round(textura,2)})
    planos=[];ini=0.
    for q in pares:
        if q['corte']:
            planos.append([ini,q['t']]);ini=q['t']
    planos.append([ini,float(duracao)])
    # Consecutive cut flags in under ~0.8 s are one gradual transition (dissolve,
    # wipe, flash), not several shots; they are reported separately.
    transicoes=[[round(a,3),round(b,3)] for a,b in planos if b-a<.8 and a>0 and b<duracao]
    planos=[[round(a,3),round(b,3)] for a,b in planos if b-a>=.8 or len(planos)==1]
    return {'fps':round(fps,4),'largura':w,'quadros':n,'pares':pares,'planos':planos,'transicoes':transicoes,
            'cortes':sum(q['corte'] for q in pares),'prova_semantica':False}


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
    plano=next((i for i,(x,y) in enumerate(varredura['planos']) if x<=a+span/2<y),None)
    return {'referente':round(ref,5),'camera':round(cam,5),
            'camera_dominante':bool(cam>2.5*max(ref,1e-4) and cam>.02),
            'corte_na_janela':any(q['corte'] for q in pares),'plano':plano,
            'parado':bool(max(q['dif'] for q in pares)<.6),'prova_semantica':False}


def _inicios_por_planos(varredura,dur,span,max_janelas,marcas):
    """Windows inside shots (never straddling a detected cut), best local motion first, plus coverage."""
    end=max(0.,dur-span-.05)
    cand=[]
    for i,(x,y) in enumerate(varredura['planos']):
        if y-x<span+.1:
            continue
        a=x+.05
        while a+span<=y-.05+1e-9 and a<=end+1e-9:
            mv=_janela_movimento(varredura,a,span)
            if mv:cand.append((a,i,mv))
            a+=max(span/2,.5)
    escolhidos=[]
    def add(a):
        a=round(min(max(0.,a),end),3)
        if all(abs(a-b)>=span*.6 for b in escolhidos):escolhidos.append(a)
    # 1) declared metadata marks relevant to the need
    for mk in sorted(marcas,key=lambda m:-len(m['termos_comuns'])):
        if mk['termos_comuns'] and len(escolhidos)<max_janelas//3:add(mk['t'])
    # 2) best subject-motion window of each shot (distinct shots first)
    best={}
    for a,i,mv in cand:
        sc=mv['referente']*(.35 if mv['camera_dominante'] else 1.)
        if i not in best or sc>best[i][0]:best[i]=(sc,a)
    for sc,a in sorted(best.values(),reverse=True):
        if len(escolhidos)>=max_janelas*2//3:break
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
    if varredura and end>=.5:
        starts=_inicios_por_planos(varredura,dur,span,max_janelas,marcas)
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
        out['varredura_local']={'fps':varredura['fps'],'quadros':varredura['quadros'],'cortes':varredura['cortes'],
                                'planos':varredura['planos'][:200],'transicoes':varredura.get('transicoes',[])[:100],
                                'prova_semantica':False}
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
                    mv['corte_na_janela'] or mv['parado'],
                    mv['camera_dominante'],
                    -mv['referente'])
        return (r['diagnostico']['quadros_grafismo_suspeito'],
                r['contraste_min']<5,
                -r.get('pares_alterados', 0) if priorizar_movimento else 0,
                -r['mudanca_px'] if priorizar_movimento else -r['contraste_min'])
    result=[]
    dur=exploracao['duracao_origem_s']
    if local:
        # Diversity across distinct shots, not fixed thirds of the timeline: an
        # action concentrated in one part of a long file must stay reachable.
        planos=[]
        for r in sorted(rows,key=rank):
            p=r['movimento_local']['plano']
            if p in planos:continue
            planos.append(p);result.append(r)
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
        have={round(x['inicio_s'],4) for x in exploration['janelas']}
        exatos=inicios_exatos or {}
        for chave in sorted(set(priorizar_cache)-have):
            a=exatos.get(chave,chave)
            if round(a,4)!=chave:continue
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
    scan and a motion need, only unseen windows in shots not yet observed, not
    stationary, not dominated by camera motion and with subject motion comparable
    to what was already seen justify insisting on this file (E281.2: two batches
    were spent on one 496 s clip). Absence in samples is never absence in the file.
    """
    rows=[x for x in exploracao.get('janelas',[]) if 'diagnostico' in x]
    unseen=[x for x in rows if round(x['inicio_s'],4) not in vistos]
    if not unseen:return False
    # An unseen window with a stored private analysis costs no new call.
    if any(round(x['inicio_s'],4) in set(gratuitas) for x in unseen):return True
    if not priorizar_movimento or not all('movimento_local' in x for x in rows):return True
    seen=[x for x in rows if round(x['inicio_s'],4) in vistos]
    planos_vistos={x['movimento_local']['plano'] for x in seen}
    ref_vista=max([x['movimento_local']['referente'] for x in seen] or [0.])
    for x in unseen:
        mv=x['movimento_local']
        if x.get('marca_metadado'):return True
        if mv['plano'] in planos_vistos or mv['parado'] or mv['camera_dominante'] or mv['corte_na_janela']:continue
        if mv['referente']>=.5*ref_vista:return True
    return False
