"""E247 private pilot, reuse E246 acquisition and E238-E244 video observations."""
import hashlib,sys,os,json
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_pesquisa_documental_e246 as Q
from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import diretor_visual_e202 as D,direcao_eventos as DE,revisao_documental as R
from src.v3.biblioteca import restaurar_catalogo
from src.v4.aquisicao_documental import Transporte

def main():
    spec=E.read(sys.argv[1]);out=Path(sys.argv[2]);caseid=sys.argv[3]
    if spec.get('publish') is not False:raise ValueError('PRIVATE_ONLY')
    case=next(c for c in spec['cases'] if c['id']==caseid)
    out.mkdir(parents=True,exist_ok=True);assets=out/'originais';assets.mkdir(exist_ok=True)
    progressive='--progressiva' in sys.argv[4:]
    somente_acervo='--somente-acervo' in sys.argv[4:]
    replay='--replay-privado' in sys.argv[4:] or somente_acervo
    revisar_acervo='--revisar-acervo' in sys.argv[4:]
    preview_pending='--pretriagem-pendente' in sys.argv[4:]
    if preview_pending and (not progressive or replay or revisar_acervo):raise ValueError('E275-PRETRIAGEM-ESCOPO')
    preview_report=[]
    review_previews='--revisar-previas' in sys.argv[4:]
    if review_previews and not preview_pending:raise ValueError('E278.1-PRETRIAGEM')
    chain_previews='--encadear-previas' in sys.argv[4:]
    if chain_previews and not review_previews:raise ValueError('E279-REVISAO-PREVIAS')
    preview_observations=[];preview_review_status=[];preview_vision=0;chain_status=[]
    if revisar_acervo and (not progressive or replay):raise ValueError('E264-REVISAO-LOCAL')
    if replay and not progressive:raise ValueError('E259-PROGRESSIVA')
    tri=D.triagem_documental(case['necessidades'],case['fatos'],progressivo=progressive)
    if any(n['evidencia_visual']=='movimento' for n in tri):Q.verificar_dependencias_video()
    lib,rest=restaurar_catalogo(db=out/'biblioteca.sqlite3',armazem=out/'biblioteca')
    from src.v4.formatos import reuso_documental as RE
    raw_needs={n['id']:n for n in case['necessidades']}
    for n in tri:
        n['candidatos_historicos']=RE.historicos({**n,'candidatos_historicos':raw_needs[n['id']].get('candidatos_historicos') or []})
    from src.v3 import pacote_biblioteca as PB
    pack=os.getenv('CORINGA_PACOTE_PRIVADO')
    discovery=os.getenv('CORINGA_CHECKPOINTS_DESCOBERTOS')
    if discovery and progressive:
        packet=json.loads(Path(discovery).read_text())
        if packet.get('publicar') is not False or packet.get('direitos_aprovados') is not False:raise ValueError('E259-CHECKPOINT-PRIVADO')
        pack=os.pathsep.join(([pack] if pack else [])+packet['pacotes']) or None
    if replay and not pack and not somente_acervo:raise ValueError('E259-PACOTE')
    if pack:
        reports_restore=[]
        for directory in pack.split(os.pathsep):
            lib.fechar()
            lib,rest=PB.restaurar(directory,db=out/'biblioteca.sqlite3',armazem=out/'biblioteca',restaurar_analises_privadas=progressive)
            reports_restore.append(rest)
        if len(reports_restore)>1:
            rest={'pacotes':reports_restore,'originais_restaurados':sum(x['originais_restaurados'] for x in reports_restore),
                  'analises_restauradas':sum(x.get('analises_restauradas',0) for x in reports_restore),'direitos_aprovados':False}
    integral='--integral' in sys.argv[4:]
    qualidade='--qualidade' in sys.argv[4:]
    if integral or qualidade:
        for n in tri:
            n['exigir_evidencia_direta']=True
            n['exigir_legibilidade']=True
    t=Transporte(max_http=54 if integral else 14,max_bytes=270_000_000 if integral else 140_000_000,max_wait=30)
    adaptive='--adaptativa' in sys.argv[4:] or progressive
    multi='--multicenas' in sys.argv[4:]
    if multi and not adaptive:raise ValueError('E253-ADAPTATIVA')
    if integral and not multi:raise ValueError('E254-MULTICENAS')
    budget=0 if replay or '--visao-zero' in sys.argv[4:] else min(20,len(tri)+2) if integral else 4 if multi else 2
    if os.getenv('CORINGA_LIMITE_VISAO_DOCUMENTAL') is not None:
        limite=int(os.environ['CORINGA_LIMITE_VISAO_DOCUMENTAL'])
        if not 0<=limite<=budget:raise ValueError('E264-COTA-DOCUMENTAL')
        budget=limite
    if revisar_acervo:
        limite=int(os.getenv('CORINGA_LIMITE_REVISAO_LOCAL',str(budget)))
        if not 1<=limite<=budget:raise ValueError('E264-COTA-LOCAL')
        budget=limite
    from src.v4.pretriagem_documental import reservar_encadeamento
    # An integral production uses the already validated preview path when
    # there is surplus for both observation and formal review. Explicit
    # preview-only modes and archive replay retain their original behavior.
    auto_chain = integral and progressive and not (replay or revisar_acervo or preview_pending)
    if auto_chain and reservar_encadeamento(tri, budget):
        preview_pending = review_previews = chain_previews = True
    total_budget=budget
    reserved=reservar_encadeamento(tri,budget) if chain_previews else set()
    # The normal review path cannot spend the calls reserved for preview +
    # formal inspection. Cache-only processing for those needs stays enabled.
    budget-=2*len(reserved)
    from src.v4.pretriagem_documental import reserva_rede_encadeamento
    global_http,global_bytes=t.max_http,t.max_bytes
    hold_http,hold_bytes=reserva_rede_encadeamento(global_http,global_bytes,len(reserved))
    t.max_http-=hold_http;t.max_bytes-=hold_bytes
    format_repairs=set();telemetry=[];calls=0;boards=[];results=[];acquired={};window_history={};saved_ids=set();cache_hits=0;checkpoint_rows=[];seen_bytes=set();reuses=0;aggregate=None;used_pages=set();used_sha=set()
    def ask(prompt,images):
        nonlocal calls
        if calls>=budget:raise RuntimeError('E247-ORCAMENTO-VISAO')
        calls+=1
        from src import gemini
        return gemini.json_visao(prompt,images,leve=True,telemetria=telemetry if progressive else None)
    from src.v4.formatos import ponte_cobertura_filme as PF,filme_editorial as FE
    def inspect(c,n,*,cache_only=False):
        nonlocal reuses,cache_hits
        c['revisao_adicional_possivel']=False
        if cache_only and c.get('fonte')!='biblioteca_v3':return {'estado':'ORCAMENTO','motivo':'CACHE_ONLY_SEM_REDE'}
        if (replay or revisar_acervo) and c.get('fonte')!='biblioteca_v3':return {'estado':'ORCAMENTO','motivo':'REPLAY_SEM_REDE'}
        if calls>=budget and not (progressive and c.get('fonte')=='biblioteca_v3'):return {'estado':'ORCAMENTO','motivo':'VISAO_ESGOTADA'}
        if integral and c.get('tipo')!='video' and c.get('pagina') in used_pages:return {'estado':'INSUFICIENTE','motivo':'FONTE_JA_SELECIONADA_NO_FILME'}
        if c.get('fonte') not in ('nasa','nasa_video','archive_video','usgs_pagina','biblioteca_v3') and (c.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or not list(Q.variants(c))):
            return {'estado':'INSUFICIENTE','motivo':'PROCEDENCIA_OU_VARIANTE_PENDENTE'}
        try:
            if c.get('fonte')=='biblioteca_v3':
                meta,im,p=RE.amostra(lib,c,probe=E.probe,frame=E.frame);reuses+=1
            else:
                identity=(c.get('fonte'),c.get('source_id') or c.get('url'))
                if progressive and identity in acquired:
                    meta,im,p,receipt=acquired[identity];im=im.copy();c.update(receipt);reuses+=1
                else:
                    meta,im,p=Q.sample(c,assets,t,progressivo=progressive,min_video_px=FE.MIN_VIDEO_COMPOSITION_PX if integral else 360)
                    if progressive:acquired[identity]=(meta,im.copy(),p,{k:c[k] for k in ('recibo_nasa','recibo_archive','recibo_cientifico','recibo_usgs','licenca','credito') if k in c})
        except Exception as e:return {'estado':'FALHA_AQUISICAO','motivo':str(e)[:200]}
        c['aquisicao']=meta
        if hashlib.sha256(p.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('E247-SHA')
        c['local_source']=str(p)
        if integral and c['tipo']=='video' and min(meta['width'],meta['height'])<FE.MIN_VIDEO_COMPOSITION_PX:
            return {'estado':'INSUFICIENTE','motivo':'QUALIDADE_INSUFICIENTE_PARA_COMPOSICAO',
                    'pixels':[meta['width'],meta['height']],'minimo':FE.MIN_VIDEO_COMPOSITION_PX}
        if integral and c.get('tipo')!='video' and meta['sha256'] in used_sha:return {'estado':'INSUFICIENTE','motivo':'BYTES_JA_SELECIONADOS_NO_FILME'}
        if adaptive and not progressive:
            key=(n['id'],meta['sha256'])
            if key in seen_bytes:return {'estado':'INSUFICIENTE','motivo':'BYTES_JA_INSPECIONADOS'}
            seen_bytes.add(key)
        m={'id':c.get('source_id') or meta['sha256'],'expected_sha256':meta['sha256'],
           'width':meta['width'],'height':meta['height'],'duration_s':meta['duration_s'],
           'local_source':str(p)}
        cache_key=None;cached=None
        if progressive:
            from src import gemini
            scope={'contrato':'E258.v1','sujeito':n.get('sujeito'),'mostrar':n['mostrar'],'fatos':n['fatos'],'id':n['id'],
                'evidencia':n['evidencia_visual'],'direta':n.get('exigir_evidencia_direta',False),
                'legibilidade':n.get('exigir_legibilidade',False),'modelos':list(gemini.MODELOS_LEVES)}
            cache_key='documental:'+hashlib.sha256(json.dumps(scope,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            cached=lib.analise(meta['sha256'],cache_key)
            if c.get('fonte')=='biblioteca_v3':
                # Restore declared attribution from the original receipt, not commercial approval.
                recs=[json.loads(r[0]) for r in lib.con.execute("SELECT conteudo FROM analises WHERE sha256=? AND tipo LIKE 'documental:recibo:%'",(meta['sha256'],))]
                for rec in recs:
                    if rec.get('publicar') is False and rec.get('direitos_aprovados') is False and rec.get('pagina')==c.get('pagina') and (rec.get('aquisicao') or {}).get('sha256')==meta['sha256'] and rec.get('fonte')!='biblioteca_v3':
                        c['licenca']=rec.get('licenca_declarada') or c.get('licenca')
                        c['credito']=rec.get('credito_declarado') or c.get('credito')
                        c['recibo_restaurado']=rec;break
            if integral and PF.licenca_documental(c,meta) is None:
                return {'estado':'INSUFICIENTE','motivo':'PROCEDENCIA_PENDENTE_COMPATIBILIDADE_FILME'}
            saved=lib.ingerir(p,{'titulo':c['titulo'],'desc':c.get('descricao',''),
                'url':meta['url_adquirida'],'pagina':c.get('pagina'),'fonte':c['fonte'],
                'wh':[meta['width'],meta['height']],'licenca_prova':'Revisao privada; direitos pendentes'})
            saved_ids.add(saved['id'])
            c['biblioteca_id']=saved['id']
            if c.get('fonte')!='biblioteca_v3':lib.gravar_analise(meta['sha256'],'documental:recibo:'+hashlib.sha256(str(c.get('pagina') or c.get('source_id')).encode()).hexdigest(),
                {'publicar':False,'direitos_aprovados':False,'aquisicao':meta,
                 'fonte':c['fonte'],'pagina':c.get('pagina'),'licenca_declarada':c.get('licenca'),'credito_declarado':c.get('credito'),
                 'recibos':{k:c[k] for k in ('recibo_nasa','recibo_archive','recibo_cientifico','recibo_usgs') if k in c}},origem='E258')
        if c['tipo']=='foto':
            original=im.copy() if progressive else None
            restored_sample=RE.reproduzir_amostra_foto(im,(cached or {}).get('revisao') or {}) if progressive else None
            if restored_sample is not None:im=restored_sample
            else:im.thumbnail((1280,1280) if qualidade or integral else (960,960))
            try:
                negative=RE.negativa_observada(n,c,im)
                if negative:
                    c['observacao_negativa_reutilizada']=negative
                    boards.append((c,[im],n['id']+' INCOMPATIVEL NA AMOSTRA'))
                    return {'estado':'INSUFICIENTE','motivo':'INCOMPATIBILIDADE_NA_AMOSTRA_REVISADA','escopo':'APENAS_AMOSTRA_IDENTIFICADA','publicar':False}
                old=(cached or {}).get('revisao') or {}
                if cache_key and old.get('publicar') is False and old.get('sha256_origem')==meta['sha256'] and old.get('necessidade_id')==n['id'] and old.get('mostrar')==n['mostrar'] and old.get('px')==list(im.size) and old.get('pixels_sha256')==hashlib.sha256(im.convert('RGB').tobytes()).hexdigest():
                    try:
                        q=R.revisar_foto(m,im,n,lambda prompt,images:old['resposta'])
                        cache_hits+=1;c['revisao_reutilizada']=True
                    except (ValueError,KeyError,TypeError):
                        if cache_only or calls>=budget:return {'estado':'ORCAMENTO','motivo':'ANALISE_COMPATIVEL_NAO_DISPONIVEL'}
                        q=R.revisar_foto(m,im,n,ask)
                elif cache_only or calls>=budget:
                    if somente_acervo and (c.get('pista_historica') or c.get('pista_aquisicao_mesmo_escopo')):
                        c['amostra_pendente']={'necessidade_id':n['id'],'sha256_origem':meta['sha256'],'px':list(im.size),'pixels_sha256':hashlib.sha256(im.convert('RGB').tobytes()).hexdigest(),'publicar':False}
                        boards.append((c,[im],n['id']+' PISTA LOCAL - SEM APROVACAO'))
                    return {'estado':'ORCAMENTO','motivo':'ANALISE_COMPATIVEL_NAO_DISPONIVEL'}
                else:q=R.revisar_foto(m,im,n,ask)
            except Exception as e:
                boards.append((c,[im],'FALHA_VISAO'));return {'estado':'FALHA_VISAO','motivo':type(e).__name__}
            c['revisao']=q;dec=R.decidir(n,c,q,tipo='foto')
            if progressive and not replay and dec.get('motivo')=='FORMATO_EVIDENCIA_DIRETA_INVALIDO':
                # Cache-only pass must defer a malformed observation, not mark
                # the media as a semantic negative. Allow one targeted retry
                # per need/file per execution, within the existing budget.
                repair_key=(n['id'],meta['sha256'])
                if cache_only:
                    c['revisao_adicional_possivel']=repair_key not in format_repairs
                elif calls<budget and repair_key not in format_repairs:
                    format_repairs.add(repair_key)
                    try:
                        second=R.revisar_foto(m,im,n,ask)
                        c['reparo_formato']={'anterior':q,'decisao_anterior':dec}
                        q=second;dec=R.decidir(n,c,q,tipo='foto');c['revisao']=q
                    except Exception as e:c['reparo_formato']={'falha':type(e).__name__}
                elif repair_key not in format_repairs:c['revisao_adicional_possivel']=True
            if progressive and not replay and dec.get('motivo')=='DETALHE_PEQUENO_NA_AMOSTRA' and not cache_only and calls<budget and original is not None and max(original.size)>max(im.size):
                refined=original.copy();refined.thumbnail((2560,2560))
                if refined.size!=im.size:
                    boards.append((c,[im],dec['motivo']))
                    try:
                        second=R.revisar_foto(m,refined,n,ask)
                        c['refinamento_foto']={'anterior':q,'decisao_anterior':dec,'modo':'IMAGEM_INTEIRA_MAIOR_RESOLUCAO'}
                        q=second;im=refined;dec=R.decidir(n,c,q,tipo='foto');c['revisao']=q
                    except Exception as e:c['refinamento_foto']={'falha':type(e).__name__}
            if cache_key:lib.gravar_analise(meta['sha256'],cache_key,{'publicar':False,'direitos_aprovados':False,'revisao':q,'decisao':dec,'escopo_pesquisa':{**RE.escopo(n),'consultas_en':(n.get('pesquisa') or {}).get('consultas_en') or []}},origem='E258')
            boards.append((c,[im],dec['motivo']))
            if integral and dec['estado']=='PERTINENTE_PRIVADO':
                used_sha.add(meta['sha256'])
                if c.get('pagina'):used_pages.add(c['pagina'])
            return dec
        if adaptive:
            from src.v4.formatos import amostragem_documental as AD
            key=(n['id'],meta['sha256'])
            history=window_history.setdefault(key,{'exploracao':None,'vistos':set(),'janelas':[]}) if progressive else {'exploracao':None,'vistos':set(),'janelas':[]}
            cached_starts=set()
            if progressive and (cache_only or calls>=budget):
                for old_row in (cached or {}).get('janelas',[]):
                    pk=old_row.get('pacote') or {};old_review=pk.get('revisao_assistida') or {}
                    start=pk.get('inicio_s')
                    if (type(start) in (int,float) and pk.get('sha256_origem')==meta['sha256']
                            and old_review.get('sha256_origem')==meta['sha256']
                            and old_review.get('necessidade_id')==n['id'] and old_review.get('publicar') is False
                            and isinstance(old_review.get('resposta_bruta'),dict)):
                        cached_starts.add(round(start,4))
            if progressive and (cache_only or calls >= budget) and not cached_starts:
                return {'estado': 'ORCAMENTO', 'motivo': 'ANALISE_COMPATIVEL_NAO_DISPONIVEL'}
            exploration,windows=AD.preparar_lote(m,n,E.frame,exploracao=history['exploracao'],excluir=history['vistos'],priorizar_cache=cached_starts)
            history['exploracao']=exploration
            c['exploracao_temporal']=exploration;c['janelas']=history['janelas']
            if not windows:return {'estado':'INSUFICIENTE' if history['vistos'] else 'FALHA_AQUISICAO','motivo':'SEM_JANELAS_NOVAS' if history['vistos'] else 'SEM_AMOSTRAS_DECODIFICADAS'}
            try:
                stored={}
                if cache_key:
                    for row in (cached or {}).get('janelas',[]):
                        pk=row.get('pacote') or {};q0=pk.get('revisao_assistida') or {}
                        if q0.get('publicar') is False and q0.get('sha256_origem')==meta['sha256'] and q0.get('necessidade_id')==n['id'] and isinstance(q0.get('resposta_bruta'),dict):
                            stored[pk.get('revisao_id')]=q0['resposta_bruta']
                entries={};fresh=[]
                for i,(pk,frames) in enumerate(windows):
                    if pk['revisao_id'] in stored:
                        try:
                            q0=DE.revisar_janela_visao(pk,frames,lambda prompt,images:stored[pk['revisao_id']],permitir_chamada=True,evidencia_visual=n['evidencia_visual'],exigir_evidencia_direta=n.get('exigir_evidencia_direta',False))
                            entries[i]={'revisao':{**q0,'chamadas_logicas':0,'provedor':'reuso_privado'},'cache':True}
                            cache_hits+=1
                            continue
                        except (ValueError,TypeError,KeyError,AttributeError):pass
                    fresh.append((i,pk,frames))
                if (cache_only or calls>=budget) and fresh:
                    c['janelas_cache_ausentes']=[pk['revisao_id'] for _,pk,_ in fresh]
                    fresh=[]
                if (cache_only or calls>=budget) and not entries:return {'estado':'ORCAMENTO','motivo':'ANALISE_COMPATIVEL_NAO_DISPONIVEL'}
                fresh_result=DE.revisar_janelas_lote([(pk,frames) for _,pk,frames in fresh],ask,evidencia_visual=n['evidencia_visual'],exigir_evidencia_direta=n.get('exigir_evidencia_direta',False)) if fresh else {'janelas':[],'chamadas_logicas':0,'imagens_enviadas':0}
                for (i,_,_),row in zip(fresh,fresh_result['janelas']):entries[i]=row
                batch={**fresh_result,'janelas':[entries.get(i,{'falha':'CACHE_AUSENTE_SEM_NOVA_IA'}) for i in range(len(windows))]}
            except Exception as e:
                for pack,frames in windows:boards.append((c,frames,'FALHA_VISAO_LOTE'))
                return {'estado':'FALHA_VISAO','motivo':type(e).__name__+':'+str(e)[:100]}
            c['visao_lote']={'chamadas_logicas':batch['chamadas_logicas'],'imagens_enviadas':batch['imagens_enviadas']}
            eligible=[]
            for (pack,frames),row in zip(windows,batch['janelas']):
                if 'falha' in row:
                    c['janelas'].append({'pacote':pack,'falha':row['falha'],
                        **({'resposta_invalida':row['resposta_invalida']} if 'resposta_invalida' in row else {})})
                    boards.append((c,frames,'FALHA_FORMATO_VISAO'));continue
                history['vistos'].add(round(pack['inicio_s'],4))
                q={**row['revisao'],'sha256_origem':meta['sha256'],'necessidade_id':n['id']}
                dec=R.decidir(n,c,q,tipo='video');pack['revisao_assistida']=q
                c['janelas'].append({'pacote':pack,'decisao':dec})
                boards.append((c,frames,dec['motivo']))
                if dec['estado']=='PERTINENTE_PRIVADO':
                    selection=DE.candidato_revisado(pack,m,fato_id=n['fatos'][0])
                    if selection['estado']=='CANDIDATO_PERTINENTE':
                        eligible.append((pack,selection,dec))
            if cache_key:
                previous = AD.consolidar_janelas((cached or {}).get('janelas', []), history['janelas'])
                lib.gravar_analise(meta['sha256'],cache_key,{'publicar':False,'direitos_aprovados':False,'janelas':previous,'exploracao':exploration,'escopo_pesquisa':{**RE.escopo(n),'consultas_en':(n.get('pesquisa') or {}).get('consultas_en') or []}},origem='E258')
            if eligible:
                ranked=DE.selecionar_revisados([{'pacote':p,'midia':m,'decisao':dec} for p,_,dec in eligible],fato_id=n['fatos'][0],preferir_legibilidade=bool(n.get('exigir_legibilidade')))
                if ranked:
                    k=ranked[0]['ordem'];c['selecao_janela']=eligible[k][1]
                    if integral:
                        used_sha.add(meta['sha256'])
                        if c.get('pagina'):used_pages.add(c['pagina'])
                    return eligible[k][2]
            if progressive and any(round(x['inicio_s'],4) not in history['vistos'] for x in exploration['janelas'] if 'diagnostico' in x) and any('revisao' in row for row in batch['janelas']):
                c['revisao_adicional_possivel']=True
            else:c['revisao_adicional_possivel']=False
            if all('falha' in r for r in batch['janelas']):
                return {'estado':'FALHA_VISAO','motivo':'TODAS_RESPOSTAS_INVALIDAS'}
            return {'estado':'INSUFICIENTE','motivo':'SEM_JANELA_PERTINENTE_NAS_AMOSTRAS'}
        span=min(3.8,meta['duration_s']-.15)
        starts=E.windows(m,span,review_technical=True)
        a=starts[0][0] if starts else 0.
        # Short sources are sampled from their actual start, not a fixed 2s offset.
        if meta['duration_s']<9:a=0.
        positions=[a]
        other=max(0.,meta['duration_s']-span-.05)
        if meta['duration_s']<15 and other-a>.5:positions.append(other)
        elif len(starts)>1:positions.append(starts[1][0])
        c['janelas']=[]
        for a in (positions[:1] if adaptive else positions):
            if calls>=budget:break
            frames=[E.frame(p,a+span*f,width=min(960,meta['width'])) for f in (0,.5,.9)]
            pack=DE.pacote_observacao(m,a,span,frames,fato_id=n['fatos'][0],necessidade=n['mostrar'],fracoes=(0,.5,.9))
            pack['diagnostico_tecnico']=DE.diagnosticar_janela(frames)
            try:q=DE.revisar_janela_visao(pack,frames,ask,permitir_chamada=True,evidencia_visual=n['evidencia_visual'],exigir_evidencia_direta=n.get('exigir_evidencia_direta',False))
            except Exception as e:
                boards.append((c,frames,'FALHA_VISAO'));c['janelas'].append({'pacote':pack,'falha':type(e).__name__});continue
            q={**q,'sha256_origem':meta['sha256'],'necessidade_id':n['id']}
            dec=R.decidir(n,c,q,tipo='video')
            pack['revisao_assistida']=q
            c['janelas'].append({'pacote':pack,'decisao':dec})
            boards.append((c,frames,dec['motivo']))
            if dec['estado']=='PERTINENTE_PRIVADO':
                c['selecao_janela']=DE.candidato_revisado(pack,m,fato_id=n['fatos'][0])
                if integral:
                    used_sha.add(meta['sha256'])
                    if c.get('pagina'):used_pages.add(c['pagina'])
                return dec
        return {'estado':'INSUFICIENTE','motivo':'SEM_JANELA_PERTINENTE_NO_ORCAMENTO'}
    try:
        if progressive:
            from src.v4 import acervo_v4 as A
            reports=[];states={};results_by_id={};total_search=0;local_checked=set();pages_checked=set()
            curated=case.get('paginas_oficiais_curadas') or []
            if not isinstance(curated,list) or any(not isinstance(x,dict) or x.get('necessidade_id') not in {n['id'] for n in tri} for x in curated):raise ValueError('E263-CURADORIA')
            search_limit=32 if integral else 16
            def search_progress(n,limit,attempted):
                nonlocal total_search
                if n['id'] not in local_checked:
                    local_checked.add(n['id'])
                    local=RE.candidatos(lib,n)
                    if revisar_acervo:local=[c for c in local if c.get('pista_historica') or c.get('pista_memoria_semantica')]
                    if local:
                        r={'id':n['id'],'buscas':[],'candidatos':local,'biblioteca':[],'publicar':False,'pronto_para_render':False}
                        reports.append(r);return r
                if phase<0:return {'id':n['id'],'buscas':[],'candidatos':[],'biblioteca':[]}
                if not replay and not revisar_acervo and n['id'] not in pages_checked:
                    pages_checked.add(n['id'])
                    pages=[Q.candidato_pagina_usgs(x,n) for x in curated if x['necessidade_id']==n['id']]
                    if pages:
                        rr={'id':n['id'],'buscas':[],'candidatos':pages,'biblioteca':[],'origem':'PAGINAS_CURADAS_PENDENTES','publicar':False,'pronto_para_render':False}
                        reports.append(rr);return rr
                if replay or revisar_acervo or total_search>=phase_limit:return {'id':n['id'],'buscas':[],'candidatos':[],'biblioteca':[]}
                # The no-vision preview run never acquires a master. Keep normal
                # resolution variants for any run that can inspect full media.
                providers=(lambda tipo:A.fontes_documentais(tipo,pretriagem=True)) if preview_pending and (budget==0 or n['id'] in reserved) else None
                r=A.pesquisar_cobertura(n,biblioteca=lib,fontes=providers,max_buscas=min(limit,search_limit-total_search,phase_limit-total_search),max_candidatos=64,progressivo=True,buscas_vistas=attempted)
                total_search+=len(r['buscas']);reports.append(r);return r
            # First pass: one logical review for each obligation if available.
            # Second pass: pool all unused budget across unresolved obligations.
            # Restored cache is inspected across all obligations before fresh vision or remote discovery.
            # The same queue resumes cache misses; they are not semantic negatives.
            for phase in ((-1,0,1) if pack and not replay and not revisar_acervo else (0,1)):
                for index,n in enumerate(tri):
                    nid=n['id'];old=results_by_id.get(nid)
                    if old and old['estado']!='LACUNA_PENDENTE':continue
                    st=states.setdefault(nid,{})
                    start=calls
                    remaining=sum(x['necessidade']!='territorio' for x in tri[index:])
                    phase_limit=total_search if phase<0 else search_limit if phase else total_search+(search_limit-total_search)//max(1,remaining)
                    if phase>=0:
                        R.reabrir_pendentes(st)
                    def inspect_progress(c,n):
                        cache_only=replay or phase<0 or nid in reserved or calls>=budget or (phase==0 and calls!=start)
                        d=inspect(c,n,cache_only=cache_only)
                        if c.get('revisao_adicional_possivel') or (phase<=0 and not replay and calls<budget and d.get('estado')=='ORCAMENTO' and c.get('fonte')=='biblioteca_v3'):
                            if c not in st.setdefault('rever',[]):st['rever'].append(c)
                        return d
                    row=R.cobertura_progressiva(n,search_progress,inspect_progress,
                        pode_buscar=lambda:(nid not in local_checked) or (phase>=0 and not replay and not revisar_acervo and (nid not in pages_checked or total_search<phase_limit)),
                        pode_inspecionar=lambda:replay or (nid not in reserved and phase>=0 and calls<budget and (phase==1 or calls==start)),
                        max_buscas=search_limit,estado=st,
                        pode_reusar=lambda c:c.get('fonte')=='biblioteca_v3',priorizar_novos=phase==1 and n['evidencia_visual']=='movimento')
                    results_by_id[nid]=row
            budget=total_budget
            t.max_http,t.max_bytes=global_http,global_bytes
            results=[{**results_by_id[n['id']],'necessidade_id':n['id'],'fatos':n['fatos']} for n in tri]
            from src.v4.formatos import cobertura_documental as C
            for n,row in zip(tri,results):row['encaminhamento']=C.encaminhar(n,row)
            if preview_pending:
                from src.v4.pretriagem_documental import pendencias_do_fluxo,coletar_fila
                queues=pendencias_do_fluxo(tri,results,states)
                old_http,old_bytes=t.max_http,t.max_bytes
                if chain_previews:
                    queues=[q for q in queues if q[0]['id'] in reserved]
                    # Keep one transfer per reserved need for the selected
                    # final asset. Unused reservation is returned below.
                    final_http=min(len(queues),max(0,old_http-t.http)//2)
                    final_bytes=min(26_000_000*len(queues),max(0,old_bytes-t.bytes)//2)
                else:final_http=final_bytes=0
                t.max_http=min(old_http-final_http,t.http+12)
                t.max_bytes=min(old_bytes-final_bytes,t.bytes+9_000_000)
                def preview_board(n,c,v,im,digest,index):
                    name='pretriagem-'+hashlib.sha256(n['id'].encode()).hexdigest()[:12]+'-'+str(index)+'.jpg'
                    im.thumbnail((960,720));im.save(out/name,quality=90)
                    return {'necessidade_id':n['id'],'mostrar':n['mostrar'],'pagina':c['pagina'],'source_id':c.get('source_id'),'consulta_origem':c.get('consulta_origem'),'preview_url':v['url'],'preview_sha256':digest,'folha':name,'estado':'PRETRIAGEM_PENDENTE','publicar':False}
                try:preview_report=coletar_fila(queues,t,preview_board)
                finally:t.max_http,t.max_bytes=old_http,old_bytes
                if review_previews:
                    from src.v4.pretriagem_documental import revisar_folhas_lote
                    needs_by_id={n['id']:n for n in tri}
                    before_preview_calls=calls
                    for row in sorted(preview_report,key=lambda x:x['id'] not in reserved):
                        n=needs_by_id[row['id']]
                        if chain_previews and n['id'] not in reserved:continue
                        if not row['amostras'] or n['necessidade']!='registro':continue
                        if calls>=budget or (chain_previews and budget-calls<2):
                            preview_review_status.append({'id':n['id'],'estado':'ORCAMENTO_PENDENTE'});continue
                        try:
                            observations=revisar_folhas_lote(n,row['amostras'],out,ask)
                            preview_observations.extend(observations)
                            preview_review_status.append({'id':n['id'],'estado':'PISTAS_OBSERVADAS'})
                        except Exception as e:preview_review_status.append({'id':n['id'],'estado':'REVISAO_PENDENTE','motivo':str(e)[:160]})
                    preview_vision=calls-before_preview_calls
                    if chain_previews:
                        from src.v4.pretriagem_documental import escolhas_observadas,candidato_priorizado,revisar_prioridade
                        observations={'case':caseid,'publicar':False,'direitos_aprovados':False,'observacoes':preview_observations}
                        choices=escolhas_observadas(spec,{'publicar':False,'necessidades':preview_report},observations,out)
                        byid={r['id']:r['amostras'] for r in preview_report}
                        choice_byid={x['id']:x for x in choices['selecao']}
                        for i,n in enumerate(tri):
                            if n['id'] not in reserved or results[i]['estado']!='LACUNA_PENDENTE':continue
                            choice=choice_byid.get(n['id'])
                            if not choice or calls>=budget:
                                chain_status.append({'id':n['id'],'estado':'SEM_PRIORIDADE_OU_SALDO','publicar':False});continue
                            try:
                                c=candidato_priorizado(n,choice,byid[n['id']],states[n['id']]['pendentes'])
                                fresh=A.resolver_foto_commons(c['pagina'],c['source_id'])
                                # The preview is not a final variant. Preserve
                                # provenance and refresh provider-declared sizes.
                                c.update(fresh)
                                # One formal call per chosen asset before any
                                # refinements: protect later obligations.
                                ceiling=budget;budget=min(budget,calls+1)
                                try:results[i]=revisar_prioridade(n,results[i],c,inspect,lambda:calls<budget)
                                finally:budget=ceiling
                                chain_status.append({'id':n['id'],'estado':results[i]['estado'],'publicar':False})
                            except Exception as e:
                                chain_status.append({'id':n['id'],'estado':'REVISAO_PENDENTE','motivo':str(e)[:160],'publicar':False})
                        if auto_chain and calls < budget:
                            # A provider without a thumbnail remains eligible for ordinary review.
                            # Never retry a thumbnail rejected by the observer as a master here.
                            for i, n in enumerate(tri):
                                if n['id'] not in reserved or results[i]['estado'] != 'LACUNA_PENDENTE':
                                    continue
                                state = states[n['id']]
                                observed_pages = {ob['pagina'] for ob in preview_observations if ob['id'] == n['id']}
                                for candidate in R.ordenar_candidatos(n, state['pendentes']):
                                    key = (candidate.get('fonte'), candidate.get('source_id') or candidate.get('url'))
                                    if key in state['vistos'] or candidate.get('pagina') in observed_pages:
                                        continue
                                    if calls >= budget or results[i]['estado'] != 'LACUNA_PENDENTE':
                                        break
                                    state['vistos'].add(key)
                                    results[i] = revisar_prioridade(n, results[i], candidate, inspect, lambda: calls < budget)
                        for n,row in zip(tri,results):row['encaminhamento']=C.encaminhar(n,row)
            aggregate={'cobertura':results,'total':len(results),'resumo':{k:sum(x['estado']==k for x in results) for k in ('CANDIDATO_PRIVADO_REVISADO','LACUNA_PENDENTE','DELEGAR_ATLAS')},'consumo':{'visao':calls,'http':t.http,'bytes':t.bytes,'buscas':total_search},'publicar':False,'pronto_para_render':False}
        elif adaptive:
            reports=[];consulted=set()
            def search(n,limit):
                local=RE.candidatos(lib,n) if pack else []
                if local and n['id'] not in consulted:
                    consulted.add(n['id'])
                    r={'id':n['id'],'estado':'REVISAR_ORIGINAIS_LOCAIS','buscas':[],
                       'candidatos':local,'biblioteca':[],'pronto_para_render':False,'publicar':False}
                else:
                    consulted.add(n['id'])
                    r=D.pesquisar_triagem([n],biblioteca_global=lib,max_buscas=limit)[0]
                    r['candidatos']=local+r['candidatos']
                reports.append(r);return r
            if multi:
                from src.v4.formatos import cobertura_documental as C
                from contextlib import contextmanager
                @contextmanager
                def limitar(http,bytes_):
                    old=(t.max_http,t.max_bytes)
                    t.max_http=min(old[0],http);t.max_bytes=min(old[1],bytes_)
                    try:yield
                    finally:t.max_http,t.max_bytes=old
                aggregate=C.cobrir(tri,search,inspect,lambda:{'visao':calls,'http':t.http,'bytes':t.bytes},
                    max_visao=budget,max_http=t.max_http,max_bytes=t.max_bytes,limitar_aquisicao=limitar)
                results=aggregate['cobertura']
            else:
                for n in tri:
                    results.append(R.cobertura_adaptativa(n,search,inspect,
                        lambda phase:calls<(1 if phase==0 else budget) and t.http<t.max_http and t.bytes<t.max_bytes))
        else:
            reports=D.pesquisar_triagem(tri,biblioteca_global=lib,max_buscas=8)
            for n,r in zip(tri,reports):
                results.append(D.revisar_cobertura_documental(n,r,inspect,max_candidatos=6))
    finally:
        if progressive and not replay:
            lib.exportar_manifesto(out/'manifesto-revisoes.jsonl')
            (out/'ids-adquiridos.json').write_text(json.dumps(sorted(saved_ids)))
            import shutil
            for mid in sorted(saved_ids):
                record=lib.obter(mid)
                if record['tamanho']>PB.MAX_TOTAL:
                    checkpoint_rows.append({'id':mid,'estado':'LIMITE_PACOTE_ORIGINAL'});continue
                dest=out/'checkpoints'/mid
                try:
                    idx=PB.exportar(lib,[mid],dest,incluir_analises_privadas=True)
                    z=shutil.make_archive(str(dest),'zip',root_dir=dest)
                    checkpoint_rows.append({'id':mid,'arquivo':Path(z).name,'sha256':PB.sha(z),'estado':'PRIVADO_LOCAL'})
                except Exception as e:checkpoint_rows.append({'id':mid,'estado':'FALHA_CHECKPOINT','motivo':type(e).__name__+':'+str(e)[:160]})
        lib.fechar()
    if preview_pending:Q.write(out/'pretriagem-pendente.json',{'publicar':False,'direitos_aprovados':False,'visao':0,'cobertura_nova':0,'necessidades':preview_report})
    if review_previews:Q.write(out/'observacoes-previas.json',{'case':caseid,'publicar':False,'direitos_aprovados':False,'observacoes':preview_observations,'visao':preview_vision,'cobertura_nova':0,'status':preview_review_status,'encadeamento':chain_status,'reservadas':sorted(reserved)})
    Q.write(out/'revisao.json',{'case':case,'triagem':tri,'pesquisa':reports,'cobertura':results,
        'restauracao':rest,'rede_aquisicao':t.resumo(),'visao_chamadas_logicas':calls,
        'visao_limite':budget,'telemetria_visao':telemetry,'reusos_analises':cache_hits,'checkpoints':checkpoint_rows,'modo_adaptativo':adaptive,'modo_progressivo':progressive,'modo_replay_privado':replay,'modo_somente_acervo':somente_acervo,'modo_revisar_acervo':revisar_acervo,'modo_multicenas':multi,'modo_qualidade':qualidade,'cobertura_documentario':aggregate,'reuso_bytes_validado':reuses>0,'reusos_bytes':reuses,'publish':False,'pronto_para_render':False})
    for i,(c,ims,verdict) in enumerate(boards):
        board=Image.new('RGB',(1080,380*len(ims)+45),'#101c28');d=ImageDraw.Draw(board)
        d.text((12,10),verdict+' | '+c['aquisicao']['sha256'][:12],fill='white')
        for j,im in enumerate(ims):
            im=im.copy();im.thumbnail((1040,340));y=45+j*380
            board.paste(im,((1080-im.width)//2,y));d.text((12,y+344),f'Amostra {j+1} - {c["tipo"]} - revisao privada',fill='white')
        board.save(out/f'revisao-{i+1}.jpg',quality=94)
    print('E247 COVERAGE',caseid,'vision',calls,'boards',len(boards),'states',[r['estado'] for r in results],flush=True)

if __name__=='__main__':main()
