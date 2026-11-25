"""E254: attempt a narrated >=60s private film only after real coverage."""
import json,math,shutil,subprocess,sys,wave
from pathlib import Path
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F,diretor_visual_e202 as D,legenda_sync as LS
from scripts.qa_documentario_curado_e218 import write,PUBLIC

def prever_tempos(case,chosen,*,minimo_s=60):
    """A feasible private preflight schedule, not a prediction of speech.
    Prefer ordinary cuts but never shorten reviewed evidence or reject a
    feasible duration simply because the provisional preferred cuts are short.
    """
    ids=[i for ch in case['chapters'] for i in ch['needs']]
    mins={i:math.ceil(chosen[i].get('min',1.4)*30-1e-6) for i in ids}
    caps={i:math.floor(chosen[i]['cap']*30+1e-6) for i in ids}
    if any(mins[i]>caps[i] for i in ids):raise ValueError('E254-TEMPO-PREFLIGHT')
    frames={i:max(mins[i],min(caps[i],108)) for i in ids}
    target=math.ceil(minimo_s*30-1e-6)
    if sum(caps.values())<target:raise ValueError('E254-CAPACIDADE-PREFLIGHT')
    # Only use remaining verified capacity, distributing across eligible cuts.
    while sum(frames.values())<target:
        i=min((i for i in ids if frames[i]<caps[i]),key=lambda i:frames[i])
        frames[i]+=1
    ends=[];total=0
    for ch in case['chapters']:
        total+=sum(frames[i] for i in ch['needs']);ends.append(total)
    return ends


FATOR_MAX=1.08
DESLOCAMENTO_MAX_S=1.2


def ajustar_cortes(case,chosen,ends,total):
    """Visual chapter cuts may lead/lag the spoken boundary by <=1.2 s (J/L-cut) so a chapter whose speech is a bit
    longer than its verified evidence borrows slack from its neighbours. No image is held beyond its reviewed capacity
    and none is repeated. Returns new end frames or None when infeasible."""
    lim=[(sum(math.ceil(chosen[i].get('min',1.4)*30-1e-6) for i in ch['needs']),
          sum(math.floor(chosen[i]['cap']*30+1e-6) for i in ch['needs'])) for ch in case['chapters']]
    d=round(DESLOCAMENTO_MAX_S*30);n=len(ends)
    # Feasible interval of each cumulative cut, forward then backward (interval propagation).
    lo=[0]*n;hi=[0]*n;a=b=0
    for k,(mn,mx) in enumerate(lim):
        a,b=a+mn,b+mx
        lo[k],hi[k]=max(a,ends[k]-d),min(b,ends[k]+d)
        if k==n-1:lo[k],hi[k]=max(lo[k],total),min(hi[k],total)
        if lo[k]>hi[k]:return None
        a,b=lo[k],hi[k]
    out=[0]*n;nxt=None
    for k in range(n-1,-1,-1):
        mn_next,mx_next=lim[k+1] if k+1<n else (0,0)
        l,h=lo[k],hi[k]
        if nxt is not None:l,h=max(l,nxt-mx_next),min(h,nxt-mn_next)
        if l>h:return None
        out[k]=min(max(ends[k],l),h);nxt=out[k]
    return out


PAUSA_MAX_S=.35


def compactar_pausas(wav,saida,*,limiar_db=-38.,minimo_s=.5,manter_s=PAUSA_MAX_S):
    """Shorten only long silences between phrases (TTS pauses vary run to run). Speech samples are untouched.
    Returns (duration, mapping) where mapping(t) converts an original time to the compacted timeline."""
    import numpy as np
    out=subprocess.run(['ffmpeg','-v','info','-nostats','-i',str(wav),'-af',f'silencedetect=n={limiar_db}dB:d={minimo_s}','-f','null','-'],
                       capture_output=True,text=True).stderr
    ini=[float(x.split('silence_start: ')[1].split()[0]) for x in out.splitlines() if 'silence_start: ' in x]
    fim=[float(x.split('silence_end: ')[1].split()[0]) for x in out.splitlines() if 'silence_end: ' in x]
    with wave.open(str(wav)) as f:
        prm=f.getparams();raw=f.readframes(f.getnframes())
    if prm.sampwidth!=2:
        shutil.copyfile(wav,saida);return prm.nframes/prm.framerate,(lambda t:t)
    a=np.frombuffer(raw,np.int16).reshape(-1,prm.nchannels);sr=prm.framerate;dur=len(a)/sr
    cortes=[]
    for x,y in zip(ini,fim):
        if x<=.05 or y>=dur-.05:continue          # keep leading/trailing handling of voz.py
        if y-x>manter_s:
            c0=x+manter_s/2;c1=y-manter_s/2;cortes.append((c0,c1))
    keep=[];pos=0.
    for c0,c1 in cortes:keep.append(a[int(pos*sr):int(c0*sr)]);pos=c1
    keep.append(a[int(pos*sr):])
    b=np.concatenate(keep) if keep else a
    with wave.open(str(saida),'wb') as f:
        f.setparams(prm);f.writeframes(b.tobytes())
    def mapa(t):
        r=0.
        for c0,c1 in cortes:
            if t>=c1:r+=c1-c0
            elif t>c0:r+=t-c0
        return t-r
    return len(b)/sr,mapa


def ritmo_necessario(case,chosen,tempos,dur):
    """Smallest uniform speech-tempo factor so every chapter fits its verified visual capacity (>=1)."""
    caps=[sum(math.floor(chosen[i]['cap']*30+1e-6) for i in ch['needs'])/30 for ch in case['chapters']]
    bounds=[b for a,b in tempos[:-1]]+[dur]
    starts=[0.]+bounds[:-1]
    f=1.0
    for (a,b),cap in zip(zip(starts,bounds),caps):
        f=max(f,(b-a)/max(cap,1e-6))
    return f


def main():
    root=Path(sys.argv[1]);report=json.loads((root/'revisao.json').read_text())
    case=report['case']
    evidence=root/'entregas_verificadas.json'
    entregas=json.loads(evidence.read_text()) if evidence.is_file() else {}
    if '--sem-atlas-automatico' not in sys.argv[2:]:
        # E284: territorial needs reach the native ATLAS through two-source verification, no manual curation.
        from src.v4.formatos import atlas_automatico as AA
        entregas,atlas_log=AA.completar_entregas(report,entregas,root/'atlas')
        if atlas_log:write(root/'atlas_automatico.json',{'entregas':atlas_log,'publicar':False})
    chosen,gate=P.preparar_cobertura(report,case,atlas=entregas.get('atlas'),progressao=entregas.get('progressao'))
    write(root/'integral.json',gate)
    if not gate['pronto_para_tts']:
        print('E254 COBERTURA INSUFICIENTE',gate,flush=True);return
    # Test the existing structural gate before spending TTS.
    try:
        predicted=prever_tempos(case,chosen)
        pre=P.plano(case,chosen,predicted)
    except ValueError as e:
        write(root/'integral.json',{**gate,'pronto_para_tts':False,'motivo':str(e)});return
    check=F.avaliar(pre)
    write(root/'preflight.json',check)
    if pre['duracao']<60 or not check['pronto']:
        write(root/'integral.json',{**gate,'pronto_para_tts':False,'motivo':'PREFLIGHT_FILME','bloqueios':check['bloqueios']})
        return
    if '--somente-preflight' in sys.argv[2:]:
        write(root/'integral.json',{**gate,'somente_preflight':True,
            'tempo_provisorio_s':pre['duracao'],'pronto_para_render_privado':False,
            'voz_gerada':False,'publicar':False})
        return
    from src.v3 import previa_telegram
    previa_telegram.chat_autorizado()
    from src import voz
    wav,tempos,caps,dur=voz.narrar([{'fala':ch['speech']} for ch in case['chapters']],root/'voz',exigir_gemini=True)
    audio=root/'narracao48k.wav'
    # E284: measured speech slightly longer than the verified evidence of a chapter. Never stretch, repeat or hold
    # images beyond their reviewed capacity: if the overflow is small, tighten the narration tempo uniformly
    # (pitch preserved) and scale every measured word/chapter time by the same factor; otherwise replan the speech.
    def buscar_fator(tempos,dur):
        # Smallest uniform tempo (<=8%) that lets the cut solver fit every chapter and keeps >=60 s; None if none.
        for k in range(0,int(round((FATOR_MAX-1)*200))+1):
            f=1+k/200
            e=[round(b/f*30) for a,b in tempos[:-1]]+[math.ceil(dur/f*30)]
            if dur/f<60:return None
            if ajustar_cortes(case,chosen,e,e[-1]):return f
        return None
    fator=buscar_fator(tempos,dur)
    if fator is None:
        # Only then shorten long TTS pauses (speech untouched), remapping every measured time.
        compacto=root/'voz_compacta.wav'
        dur2,mapa=compactar_pausas(wav,compacto)
        if dur2<dur-.05:
            t2=[(mapa(a),mapa(b)) for a,b in tempos]
            f2=buscar_fator(t2,dur2)
            if f2 is not None:
                tempos=t2
                caps=[{**bl,**({'start':mapa(bl['start'])} if 'start' in bl else {}),'end':mapa(bl['end']),
                       'words':[{**w,'s':mapa(float(w['s'])),**({'e':mapa(float(w['e']))} if 'e' in w else {})} for w in bl['words']]} for bl in caps]
                write(root/'pausas_compactadas.json',{'duracao_original_s':dur,'duracao_s':dur2,'pausa_max_s':PAUSA_MAX_S,'publicar':False})
                wav,dur,fator=compacto,dur2,f2
    if fator is None:
        fator=max(ritmo_necessario(case,chosen,tempos,dur),FATOR_MAX+1e-3)
    filtro=['-af',f'atempo={fator:.5f}'] if fator>1.0005 else []
    if fator>FATOR_MAX:
        write(root/'integral.json',{**gate,'motivo':'FALA_EXCEDE_EVIDENCIA_REPLANEJAR','fator_necessario':round(fator,4),
                                    'duracao_voz':dur,'pronto_para_render':False});return
    if filtro:
        tempos=[(a/fator,b/fator) for a,b in tempos]
        caps=[{**bl,'start':bl.get('start',0)/fator if 'start' in bl else bl.get('start'),'end':bl['end']/fator,
               'words':[{**w,'s':float(w['s'])/fator,**({'e':float(w['e'])/fator} if 'e' in w else {})} for w in bl['words']]} for bl in caps]
        write(root/'ajuste_ritmo.json',{'fator_atempo':round(fator,5),'duracao_original_s':dur,'motivo':'FALA_LIGEIRAMENTE_MAIOR_QUE_EVIDENCIA','publicar':False})
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),*filtro,'-ar','48000','-ac','1',str(audio)],check=True)
    with wave.open(str(audio)) as f:duration=f.getnframes()/f.getframerate()
    total=math.ceil(duration*30)
    if duration<60 or len(tempos)!=len(case['chapters']):
        write(root/'integral.json',{**gate,'motivo':'TEMPO_REAL_INSUFICIENTE','duracao_voz':duration,'pronto_para_render':False});return
    ends=[round(b*30) for a,b in tempos[:-1]]+[total]
    ajustados=ajustar_cortes(case,chosen,ends,total)
    if ajustados and ajustados!=ends:
        write(root/'ajuste_cortes.json',{'cortes_fala':ends,'cortes_imagem':ajustados,'deslocamento_max_s':DESLOCAMENTO_MAX_S,'publicar':False})
        ends=ajustados
    try:plan=P.plano(case,chosen,ends)
    except ValueError as e:
        write(root/'integral.json',{**gate,'motivo':str(e),'duracao_voz':duration,'pronto_para_render':False});return
    write(root/'plano.json',plan)
    check=F.avaliar(plan);write(root/'preflight-real.json',check)
    if not check['pronto']:
        write(root/'integral.json',{**gate,'motivo':'PREFLIGHT_REAL','bloqueios':check['bloqueios'],'pronto_para_render':False});return
    result=F.preparar(plan,root/'documental',PUBLIC)
    props=json.loads(Path(result['props']).read_text())
    props['private_review_only']=True
    words=LS.alinhar_inicios_a_fala(D.palavras_de_caps(caps),audio);groups=[]
    contexto = {'titulo': case.get('tema'), 'narracao': {'fatos': case.get('fatos', [])}}
    words = LS.destacar_atlas(words, contexto, maximo=3)
    for g in LS.grupos(words,maximo=3):
        ws=words[g['i0']:g['i0']+g['n']]
        a=max(0,g['ini']);b=min(duration,g['fim'])
        if groups:a=max(a,groups[-1]['end'])
        if b>a:groups.append({'start':a,'end':b,'words':[{'w':w['w'],'hl':w['hl']} for w in ws]})
    h=P.sha(audio);asset='e202/'+h+'.wav'
    (PUBLIC/'e202').mkdir(exist_ok=True);shutil.copyfile(audio,PUBLIC/asset)
    props=D.anexar_audio_documental(props,asset,groups,PUBLIC,'PALAVRAS_MEDIDAS')
    write(root/'props.json',props)
    write(root/'narracao.json',{'audio_sha256':h,'duration_s':duration,'words':words,'publish':False})
    sinc=LS.conferir(root/'narracao.json', audio, maximo=3)
    write(root/'sincronia-medida.json', sinc)
    if not sinc['ok']:
        # E284: measured caption/speech sync is a render precondition, not an after-the-fact note.
        write(root/'integral.json',{**gate,'motivo':'SINCRONIA_MEDIDA_REPROVADA','sincronia':{k:sinc[k] for k in ('atraso_s','n_palavras_sem_fala','fala_sem_legenda','trocas_bruscas')},
                                    'duracao_voz':duration,'pronto_para_render':False});return
    write(root/'integral.json',{**gate,'pronto_para_render_privado':True,'duracao_voz':duration,'publicar':False})
if __name__=='__main__':main()
