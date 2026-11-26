"""E330: exact historical coverage replay through the CURRENT general bridge.
Fragments from independent topics, not a new film or new semantic approval.
No external source download, vision, generated narration or publication.
"""
import base64,hashlib,json,math,re,shutil,wave
from pathlib import Path
from PIL import Image
from src.v3 import pacote_biblioteca as P
from src.v4.formatos import ponte_cobertura_filme as B,filme_editorial as F,revisao_documental as R,reuso_documental as RE,direcao_eventos as DE
from scripts.recuperar_checkpoints_documentais import api,listar_releases,verified_download
from scripts.qa_documentario_geografia_e219 import frame

def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2))
def check(ok,reason):
    if not ok:raise ValueError(reason)

def revalidate(n,c,src):
    a=c['aquisicao'];d=c['decisao'];rid=d['revisao_id'];h=a['sha256']
    check(P.sha(src)==h and src.stat().st_size==a['bytes'],'E330-ORIGINAL')
    if c['tipo']=='foto':
        q=c['revisao']
        with Image.open(src) as im:
            check(list(im.size)==[a['width'],a['height']],'E330-DIMENSOES')
            check(RE.reproduzir_amostra_foto(im,q) is not None,'E330-PIXELS-FOTO')
        check(q['mostrar']==n['mostrar'] and q['necessidade_id']==n['id'],'E330-ESCOPO-FOTO')
        base={k:q[k] for k in ('sha256_origem','necessidade_id','mostrar','pixels_sha256','px')}
        check(hashlib.sha256(json.dumps(base,sort_keys=True,ensure_ascii=False).encode()).hexdigest()==rid,'E330-ID-FOTO')
        samples=[q['pixels_sha256']]
    else:
        w=c['selecao_janela']
        p=next(x['pacote'] for x in c['janelas'] if x['pacote']['revisao_id']==rid)
        q=p['revisao_assistida']
        check(p['publicar'] is False and p['sha256_origem']==h and p['fato_id']==n['fatos'][0] and p['necessidade']==n['mostrar'] and p['inicio_s']==w['source_in_seconds'],'E330-ESCOPO-VIDEO')
        base={k:p[k] for k in ('sha256_origem','inicio_s','duracao_s','fato_id','necessidade','amostras')}
        check(hashlib.sha256(json.dumps(base,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==rid,'E330-ID-VIDEO')
        check(len(p['amostras'])==3,'E330-AMOSTRAS')
        for s in p['amostras']:
            im=frame(src,s['fonte_s'],width=s['px'][0])
            check(list(im.size)==s['px'] and hashlib.sha256(im.tobytes()).hexdigest()==s['pixels_sha256'],'E330-PIXELS-VIDEO')
        v=DE.aceitar_observacao(p,q['resposta_observada'])
        check(v['veredito']=='pertinente' and v['video_framing']==w.get('video_framing'),'E330-ENQUADRAMENTO')
        samples=[s['pixels_sha256'] for s in p['amostras']]
    fresh=R.decidir(n,c,q,tipo=c['tipo'])
    check(fresh['estado']=='PERTINENTE_PRIVADO' and fresh['revisao_id']==rid and fresh.get('evidencia_direta_normalizada')==d.get('evidencia_direta_normalizada'),'E330-REVISAO-INCOMPATIVEL')
    return samples

def run_one(row,ref,releases,root,*,diagnostic_only=False):
    folder=root/row['id'];folder.mkdir()
    h=row['sha256'];name='cm-'+h[:12]+'.zip'
    item=api('/contents/revisoes/'+row['folder']+'/revisao.json?ref='+ref)
    check(item['sha']==row['report_blob'] and item['encoding']=='base64' and 0<item['size']<=1_000_000,'E330-RELATORIO')
    raw=base64.b64decode(item['content'])
    check(len(raw)==item['size'] and hashlib.sha1(('blob '+str(len(raw))).encode()+bytes(1)+raw).hexdigest()==row['report_blob'],'E330-BLOB')
    report=json.loads(raw);check(report['publish'] is False,'E330-PRIVADO')
    n=next(x for x in report['triagem'] if x['id']==row['need'])
    rr=next(x for x in report['cobertura'] if x['necessidade_id']==row['need'])
    negative=diagnostic_only and row.get('expected_negative') is True
    check(rr['estado']==('LACUNA_PENDENTE' if negative else 'CANDIDATO_PRIVADO_REVISADO'),'E330-COBERTURA')
    if negative:
        c=next(x for x in reversed([x for r in rr['rodadas'] for x in r['pesquisa']['candidatos']]) if x.get('aquisicao',{}).get('sha256')==h and x.get('janelas'))
    else:
        c=next(x for x in reversed([x for r in rr['rodadas'] for x in r['pesquisa']['candidatos']]) if [x.get('fonte'),x.get('source_id') or x.get('url')]==rr['selecionado'] and x.get('aquisicao',{}).get('sha256')==h and x.get('decisao',{}).get('estado')=='PERTINENTE_PRIVADO')
    rel=releases[row['tag']];check(rel['draft'] is True,'E330-RELEASE')
    a=next(x for x in rel['assets'] if x['name']==name)
    check(a['digest']=='sha256:'+row['package_digest'] and 0<a['size']<=25_000_000,'E330-PACOTE')
    z=verified_download(row['tag'],a,folder)
    dest=P.extrair_checkpoint(z,folder/'original',expected_sha256=row['package_digest'])
    idx=read(dest/'index.json')
    check(idx['schema']=='coringa.v3.originals.private.v1' and idx['publicar'] is False and idx['direitos_aprovados'] is False and P.sha(dest/'manifesto.jsonl')==idx['manifesto_sha256'],'E330-INDICE')
    m=next(x for x in idx['arquivos'] if x['sha256']==h and x['id']=='cm-'+h[:12])
    check(re.fullmatch(h+r'[.](jpg|jpeg|png|webp|mp4|webm)',m['arquivo']) is not None,'E330-NOME')
    src=dest/m['arquivo'];check(src.stat().st_size==m['bytes'],'E330-BYTES')
    c={**c,'local_source':str(src)}
    from src.v4.formatos import recuperacao_cache_e333 as RC
    if negative:
        proof=[]
        for window in c['janelas']:
            p=window['pacote'];q=p.get('revisao_assistida') or {}
            if q.get('veredito')!='insuficiente':continue
            candidate={**c,'decisao':{'revisao_id':p['revisao_id']},
                'selecao_janela':{'revisao_id':p['revisao_id'],'source_in_seconds':p['inicio_s'],'duracao_s':p['duracao_s'],'video_framing':q.get('video_framing')}}
            try:
                result=RC.revalidar(n,candidate,frame,somente_diagnostico=True);proof.append(result)
            except Exception as exc:
                proof.append({'review_id':p['revisao_id'],'status':'REVALIDACAO_PENDENTE','reason':str(exc)[:200]})
        write(folder/'diagnostic.json',proof)
        check(len(proof)==row['expected_windows'] and all(x.get('status')=='PIXELS_REVALIDATED' and x.get('decisao_atual')=='INSUFICIENTE' and x.get('veredito_amostral')=='insuficiente' for x in proof),'E335-NEGATIVAS-NAO-PRESERVADAS')
        return {'id':row['id'],'status':'DIAGNOSTICO_REAL_PRIVADO','amostras':proof,'lacuna_preservada':True,'semantic_approval':False,'publish':False}
    from src.v4.formatos import replanejamento_e308 as RP, reserva_janelas_e313 as RJ
    case={'tema':n['sujeito'],'chapters':[{'title':n['sujeito'],'needs':[n['id']]}],'composicao_documental':'PRIVATE_V2'}
    old={'necessidade_id':n['id'],'estado':rr['estado'],'selecionado':rr['selecionado'],'rodadas':[{'pesquisa':{'candidatos':[c]}}]}
    replay={'publish':False,'triagem':[n],'cobertura':[old]}
    prepare=lambda report:B.preparar_cobertura(report,case,minimo_s=1.4)
    before,gate=prepare(replay)
    check(not before and not gate['pronto_para_tts'] and gate['replanejamento_por_fato'][0]['motivo']=='REVISAR_ACAO_ESPECIFICA','E333-RECUSA')
    if diagnostic_only:
        proof=[]
        def diagnose(need,candidate):
            try:
                r=RC.revalidar(need,candidate,frame);proof.append(r);return r
            except Exception as exc:
                proof.append({'review_id':candidate['decisao']['revisao_id'],'status':'REVALIDACAO_PENDENTE','reason':str(exc)[:200]});return None
        initial=diagnose(n,c)
        historical=RC.alternativa(n,c,diagnose)
        strict=RC.recuperar_reservada(n,old,frame,lambda *a:False,diagnosticos=proof)
        write(folder/'diagnostic.json',proof)
        check(initial is not None and historical is not None,'E334-DIAGNOSTICO-REAL')
        check(strict is None,'E334-RESERVA-NAO-AUTORIZADA')
        return {'id':row['id'],'status':'DIAGNOSTICO_REAL_PRIVADO','amostras':proof,'alternativa_historica':historical['rodadas'][0]['pesquisa']['candidatos'][0]['decisao']['revisao_id'],'recuperacao_estrita_sem_reserva':False,'semantic_approval':False,'publish':False}
    attempts=[]
    def validate(need,candidate):
        try:
            samples=revalidate(need,candidate,src)
            attempts.append({'review_id':candidate['decisao']['revisao_id'],'samples':samples,'status':'PIXELS_REVALIDATED'})
            return samples
        except Exception as exc:
            attempts.append({'review_id':candidate['decisao']['revisao_id'],'status':'BLOCKED','reason':str(exc)[:200]})
            return None
    final=[]
    logs=RP.reparar_acoes(replay,prepare,lambda need:RC.alternativa(need,c,validate),final.append)
    write(folder/'recovery.json',{'publish':False,'before':gate,'attempts':attempts,'logs':logs,'accepted':final,'semantic_approval':False})
    chosen,gate=prepare(replay)
    check(final==[True] and gate['pronto_para_tts'] and n['id'] in chosen,'E333-RECUPERACAO')
    c=chosen[n['id']]['candidate']
    samples=next(x['samples'] for x in attempts if x['review_id']==c['decisao']['revisao_id'] and x['status']=='PIXELS_REVALIDATED')
    check(c['decisao']['revisao_id']!=old['rodadas'][0]['pesquisa']['candidatos'][0]['decisao']['revisao_id'],'E333-REPETICAO')
    x=chosen[n['id']]
    end=math.floor(x['cap']*30+1e-6)
    plan=B.plano(case,chosen,[end])
    check(not plan['revelacoes_documentais'],'E330-ROTULO-HISTORICO-INVENTADO')
    write(folder/'plano.json',plan)
    public=Path('motor4/remotion/public')
    F.preparar(plan,folder,public,fragmento_misto=True)
    props=read(folder/'props.json')
    check(props['private_review_only'] and props['preview'] and props['documentary_media_preview'] and props['shots'][0]['documentary_composition_v2'],'E330-PROPS')
    audio=folder/'silence.wav'
    with wave.open(str(audio),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(bytes(end*1600*2))
    audio_name='e202/'+P.sha(audio)+'.wav'
    (public/'e202').mkdir(exist_ok=True);shutil.copyfile(audio,public/audio_name)
    props.update(scene_narration_asset=audio_name,documentary_captions=[{'start':.2,'end':plan['duracao']-.1,'words':[{'w':'AMOSTRA'},{'w':'DE'},{'w':'REVISÃO','hl':True}]}],documentary_caption_origin='FRASES_MEDIDAS_LAB',documentary_text_probe=True)
    write(folder/'props.json',props)
    return {'id':row['id'],'status':'READY_PRIVATE_FRAGMENT','sha256':h,'need':n['id'],'mostrar':n['mostrar'],'fatos':n['fatos'],'source_type':c['tipo'],'samples':samples,'review_id':c['decisao']['revisao_id'],'framing':plan['shots'][0].get('video_framing'),'photo_roi':plan['shots'][0].get('photo_roi_candidate'),'duration':plan['duracao'],'publish':False,'semantic_approval':False}

def main():
    import sys
    diagnostic_only='--diagnostic-only' in sys.argv[1:]
    cfg=read('benchmarks/e335/replay.json' if diagnostic_only else 'benchmarks/e330/replay.json');root=Path('stage_documental/e334' if diagnostic_only else 'stage_documental/e333');root.mkdir(parents=True,exist_ok=False)
    meta=api('');check(meta['private'] is True and meta['id']==1454059520 and cfg['publish'] is False,'E330-COFRE')
    releases={r['tag_name']:r for r in listar_releases(300)}
    result={'publish':False,'new_ai':0,'new_tts':0,'semantic_approval':False,'full_documentary':False,'records':[]}
    for row in cfg['cases']:
        if not diagnostic_only and row['id']!='lava':continue
        try:result['records'].append(run_one(row,cfg['ref'],releases,root,diagnostic_only=diagnostic_only))
        except Exception as e:
            p=root/row['id']/'diagnostic.json'
            result['records'].append({'id':row['id'],'status':'BLOCKED','reason':str(e)[:1000],'amostras':read(p) if p.is_file() else [],'publish':False})
        write(root/'replay.json',result)
    print('E334' if diagnostic_only else 'E333',[(r['id'],r['status']) for r in result['records']],flush=True)
    if diagnostic_only and (not result['records'] or any(r['status']!='DIAGNOSTICO_REAL_PRIVADO' for r in result['records'])):raise ValueError('E334-PROVA-PENDENTE')
if __name__=='__main__':main()
