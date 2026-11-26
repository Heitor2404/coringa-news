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


def gate_sincronia(root,gate,sync,duration):
    """A failed or missing measured result cannot authorize any private render."""
    write(root/'sincronia-medida.json',sync)
    if sync.get('ok') is not True:
        (root/'props.json').unlink(missing_ok=True)
        write(root/'integral.json',{**gate,'motivo':'SINCRONIA_MEDIDA_REPROVADA',
            'duracao_voz':duration,'pronto_para_render_privado':False,'publicar':False})
        return False
    return True


def gate_direcao_short(root,gate,plan,*,phase):
    from src.v4.formatos.direcao_short_e306 import diagnosticar
    diagnostic=diagnosticar(plan)
    write(root/('direcao-short-'+phase+'.json'),diagnostic)
    if not diagnostic['pronto_para_analise_visual']:
        (root/'props.json').unlink(missing_ok=True)
        write(root/'integral.json',{**gate,'motivo':'REPLANEJAR_DIRECAO_SHORT',
            'pronto_para_tts':False,'pronto_para_render_privado':False,'publicar':False})
        return False
    return True


def main():
    root=Path(sys.argv[1]);report=json.loads((root/'revisao.json').read_text())
    # A retry cannot inherit ready-to-render props from an earlier run.
    (root/'props.json').unlink(missing_ok=True)
    case=report['case']
    evidence=root/'entregas_verificadas.json'
    entregas=json.loads(evidence.read_text()) if evidence.is_file() else {}
    chosen,gate=P.preparar_cobertura(report,case,atlas=entregas.get('atlas'),progressao=entregas.get('progressao'))
    write(root/'integral.json',{**gate,'pronto_para_render_privado':False,'publicar':False})
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
    if not gate_direcao_short(root,gate,pre,phase='preflight'):return
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
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-ar','48000','-ac','1',str(audio)],check=True)
    with wave.open(str(audio)) as f:duration=f.getnframes()/f.getframerate()
    total=math.ceil(duration*30)
    if duration<60 or len(tempos)!=len(case['chapters']):
        write(root/'integral.json',{**gate,'motivo':'TEMPO_REAL_INSUFICIENTE','duracao_voz':duration,'pronto_para_render':False});return
    ends=[round(b*30) for a,b in tempos[:-1]]+[total]
    try:plan=P.plano(case,chosen,ends)
    except ValueError as e:
        write(root/'integral.json',{**gate,'motivo':str(e),'duracao_voz':duration,'pronto_para_render':False});return
    write(root/'plano.json',plan)
    check=F.avaliar(plan);write(root/'preflight-real.json',check)
    if not check['pronto']:
        write(root/'integral.json',{**gate,'motivo':'PREFLIGHT_REAL','bloqueios':check['bloqueios'],'pronto_para_render':False});return
    if not gate_direcao_short(root,gate,plan,phase='real'):return
    result=F.preparar(plan,root/'documental',PUBLIC)
    props=json.loads(Path(result['props']).read_text())
    props['private_review_only']=True
    words=D.palavras_de_caps(caps);groups=[]
    contexto = {'titulo': case.get('tema'), 'narracao': {'fatos': case.get('fatos', [])}}
    words = LS.destacar_atlas(words, contexto, maximo=3)
    words,alignment=LS.alinhar_documental(words,audio,maximo=3)
    write(root/'realinhamento.json',alignment)
    h=P.sha(audio)
    write(root/'narracao.json',{'audio_sha256':h,'duration_s':duration,'words':words,'publish':False})
    sync=LS.conferir(root/'narracao.json',audio,maximo=3)
    if not gate_sincronia(root,gate,sync,duration):return
    for g in LS.grupos(words,maximo=3):
        ws=words[g['i0']:g['i0']+g['n']]
        a=max(0,g['ini']);b=min(duration,g['fim'])
        if groups:a=max(a,groups[-1]['end'])
        if b>a:groups.append({'start':a,'end':b,'words':[{'w':w['w'],'hl':w['hl']} for w in ws]})
    asset='e202/'+h+'.wav'
    (PUBLIC/'e202').mkdir(exist_ok=True);shutil.copyfile(audio,PUBLIC/asset)
    props=D.anexar_audio_documental(props,asset,groups,PUBLIC,'PALAVRAS_MEDIDAS')
    write(root/'props.json',props)
    write(root/'integral.json',{**gate,'pronto_para_render_privado':True,'duracao_voz':duration,'sincronia_medida_ok':True,'publicar':False})
if __name__=='__main__':main()
