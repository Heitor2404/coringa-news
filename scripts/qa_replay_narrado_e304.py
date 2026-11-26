"""Replay a completed private documentary from authenticated vault assets.
No new research, model calls, TTS, changes to the story or publication.
Audio is decoded from the archived MP4, NOT the original lossless TTS.
"""
import base64,json,re,shutil,subprocess,sys
from pathlib import Path
from src.v3 import pacote_biblioteca as P
from src.v4.formatos import filme_editorial as F,legenda_sync as LS,diretor_visual_e202 as D
from scripts.recuperar_checkpoints_documentais import api,listar_releases,verified_download,REPO

def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,obj):Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')

def validar_historico(plan,props,narr,qa):
    if plan.get('publicar') is not False or plan.get('tipo')!='PROVA_VISUAL_PRIVADA' or qa.get('publish') is not False or narr.get('publish') is not False or props.get('private_review_only') is not True or props.get('preview') is not True:
        raise ValueError('E304-PRIVADO')
    if not 60<=plan['duracao']<=180 or abs(plan['duracao']-qa['duration'])>.001 or abs(plan['duracao']-props['duracao'])>.001 or not qa['narrado'] or not qa['audio']:
        raise ValueError('E304-DURACAO')
    if props['scene_narration_asset']!='e202/'+narr['audio_sha256']+'.wav' or abs(narr['duration_s']-plan['duracao'])>.1:
        raise ValueError('E304-VOZ-VINCULO')
    if [(s['id'],s['start'],s['end'],s['type']) for s in plan['shots']]!=[(s['id'],s['start'],s['end'],s['type']) for s in props['shots']]:
        raise ValueError('E304-MONTAGEM')
    if any(s['type']!='photo' for s in plan['shots']) or not 1<=len(plan['media'])<=36:
        raise ValueError('E304-ESCOPO-FOTOS')
    for s,p in zip(plan['shots'],props['shots']):
        h=plan['media'][s['asset']]['expected_sha256']
        if not re.fullmatch('[a-f0-9]{64}',h) or not re.fullmatch('film_editorial/'+h+r'\.(jpg|png|webp)',p['asset']):
            raise ValueError('E304-FONTE-VINCULO')
    if [w['w'] for g in props['documentary_captions'] for w in g['words']]!=[w['w'] for w in narr['words']]:
        raise ValueError('E304-LEGENDAS')

def main():
    cfg=read(sys.argv[1]);root=Path(sys.argv[2]);root.mkdir(parents=True,exist_ok=False)
    if cfg.get('publish') is not False or not re.fullmatch('review-[a-z0-9-]+',cfg['tag']) or not re.fullmatch('[a-f0-9]{40}',cfg['ref']) or not re.fullmatch(r'revisoes/[a-z0-9-]+',cfg['folder']):
        raise ValueError('E304-CONFIG')
    meta=api('')
    if meta.get('private') is not True or meta.get('id')!=1454059520:raise ValueError('E304-COFRE')
    tag=cfg['tag'];ref=cfg['ref'];folder=cfg['folder']
    rel=next(r for r in listar_releases(300) if r['tag_name']==tag and r['draft'] is True)
    assets={a['name']:a for a in rel['assets']}
    old=root/'historico';old.mkdir()
    for name in ('plano.json','props.json','narracao.json','qa.json','sincronia-medida.json'):
        item=api('/contents/'+folder+'/'+name+'?ref='+ref)
        if item.get('encoding')!='base64' or not 0<item['size']<=1_000_000:raise ValueError('E304-METADADOS')
        raw=base64.b64decode(item['content'])
        if len(raw)!=item['size']:raise ValueError('E304-BYTES')
        (old/name).write_bytes(raw)
    plan,props,narr,qa=(read(old/n) for n in ('plano.json','props.json','narracao.json','qa.json'))
    validar_historico(plan,props,narr,qa)
    if not read(old/'sincronia-medida.json')['ok']:raise ValueError('E304-SINCRONIA-HISTORICA')
    a=assets['filme.mp4'];film=old/'filme.mp4'
    if not 0<a['size']<=100_000_000 or a.get('digest')!='sha256:'+qa['sha256']:raise ValueError('E304-MP4-RECIBO')
    subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern','filme.mp4','--dir',str(old)],check=True,timeout=180)
    if film.stat().st_size!=a['size'] or P.sha(film)!=qa['sha256']:raise ValueError('E304-MP4-SHA')
    # Restore only exact originals needed by this previously prepared plan.
    packages=Path('stage_documental/e304')/root.name/'pacotes';packages.mkdir(parents=True,exist_ok=False)
    names={f"cm-{m['expected_sha256'][:12]}.zip" for m in plan['media'].values()}
    if sum(assets[n]['size'] for n in names)>300_000_000:raise ValueError('E304-LIMITE')
    receipts=[]
    for m in plan['media'].values():
        h=m['expected_sha256'];name='cm-'+h[:12]+'.zip';a=assets[name]
        if not 0<a['size']<=P.MAX_TOTAL+10_000_000:raise ValueError('E304-PACOTE-LIMITE')
        z=verified_download(tag,a,packages)
        dest=P.extrair_checkpoint(z,packages/name[:-4],expected_sha256=a['digest'][7:])
        idx=read(dest/'index.json')
        if idx.get('schema')!='coringa.v3.originals.private.v1' or idx.get('publicar') is not False or idx.get('direitos_aprovados') is not False or P.sha(dest/'manifesto.jsonl')!=idx['manifesto_sha256']:
            raise ValueError('E304-INDICE')
        row=next(x for x in idx['arquivos'] if x['sha256']==h and x['id']=='cm-'+h[:12])
        if not re.fullmatch(h+r'\.(jpg|jpeg|png|webp)',row['arquivo']):raise ValueError('E304-NOME')
        src=dest/row['arquivo']
        if P.sha(src)!=h or src.stat().st_size!=row['bytes']:raise ValueError('E304-ORIGINAL')
        m['local_source']=str(src);receipts.append({'sha256':h,'bytes':row['bytes'],'package':name})
    write(root/'restauracao.json',{'publish':False,'historical_tag':tag,'historical_ref':ref,'originals':receipts,'audio_origin':'DECODED_ARCHIVED_MP4_NOT_RAW_TTS','historical_mp4_sha256':qa['sha256'],'raw_voice_sha256_historical':narr['audio_sha256']})
    # Check the CURRENT structural and rendering contracts, not old props.
    public=Path('motor4/remotion/public')
    write(root/'plano.json',plan)
    prepared=F.preparar(plan,root/'documental',public)
    new=read(prepared['props'])
    if [(s['id'],s['start'],s['end'],s['type'],s['asset']) for s in new['shots']]!=[(s['id'],s['start'],s['end'],s['type'],s['asset']) for s in props['shots']]:
        raise ValueError('E304-MONTAGEM-ALTERADA')
    audio=root/'narracao-decodificada.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(film),'-map','0:a:0','-ar','48000','-ac','1','-c:a','pcm_s16le',str(audio)],check=True,timeout=120)
    words,align=LS.alinhar_documental(narr['words'],audio,maximo=3)
    write(root/'realinhamento.json',align)
    if not align['final']['ok']:raise ValueError('E304-SINCRONIA-DECODE')
    import wave
    with wave.open(str(audio),'rb') as f:duration=f.getnframes()/f.getframerate()
    if abs(duration-new['duracao'])>.15:raise ValueError('E304-AUDIO-DURACAO')
    groups=[]
    for g in LS.grupos(words,maximo=3):
        ws=words[g['i0']:g['i0']+g['n']];hi=max(range(len(ws)),key=lambda i:len(ws[i]['w']))
        a=max(0,g['ini'],groups[-1]['end'] if groups else 0);b=min(duration,g['fim'],new['duracao'])
        if b>a:groups.append({'start':a,'end':b,'words':[{'w':w['w'],'hl':bool(w.get('hl',i==hi))} for i,w in enumerate(ws)]})
    h=P.sha(audio);asset='e202/'+h+'.wav';(public/'e202').mkdir(exist_ok=True);shutil.copyfile(audio,public/asset)
    new=D.anexar_audio_documental(new,asset,groups,public,'PALAVRAS_MEDIDAS')
    write(root/'props.json',new)
    write(root/'narracao.json',{'audio_sha256':h,'duration_s':duration,'words':words,'publish':False,'origin':'DECODED_ARCHIVED_MP4'})
    sync=LS.conferir(root/'narracao.json',audio,maximo=3);write(root/'sincronia-medida.json',sync)
    if not sync['ok']:raise ValueError('E304-SINCRONIA')
    print('E304 READY',new['duracao'],len(new['shots']),flush=True)

if __name__=='__main__':main()
