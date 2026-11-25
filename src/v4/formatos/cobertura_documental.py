"""E253: shared budgets and coverage reporting for a complete set of obligations.
No rendering or automatic approval. Geographic obligations remain with ATLAS.
"""
from contextlib import nullcontext
from .revisao_documental import cobertura_adaptativa


def encaminhar(necessidade,row):
    """Plan the next evidence route, never create or approve an asset."""
    base={'id':necessidade['id'],'fatos':necessidade['fatos'],'mostrar':necessidade.get('mostrar'),
          'pronto_para_render':False,'publicar':False,'animacao_autorizada':False}
    if row['estado']=='DELEGAR_ATLAS':
        return {**base,'rota':'ATLAS','proximo':'VALIDAR_GEOGRAFIA_E_RENDERIZAR_MAPA_COM_COMPROVANTE'}
    if row['estado']=='CANDIDATO_PRIVADO_REVISADO':
        return {**base,'rota':'REGISTRO_REAL','proximo':'AUDITAR_DIREITOS_ENQUADRAMENTO_E_TEMPO'}
    evidence=evidencia_lacuna(necessidade,row)
    if necessidade.get('necessidade')=='lacuna_explicativa' and necessidade.get('lacuna') and evidence['revisoes_negativas']:
        return {**base,'rota':'REAVALIAR_COMPLEMENTO','proximo':'VALIDAR_LACUNA_E_REFERENCIAS_PELO_CONTRATO_E217',
                'evidencia_lacuna':evidence,'animacao_autorizada':False}
    return {**base,'rota':'REPLANEJAR_REGISTRO','proximo':'PESQUISAR_OU_REORGANIZAR_NARRATIVA_SEM_INVENTAR_EVIDENCIA'}

def evidencia_lacuna(necessidade,row):
    """Scope the actual reviewed negatives, not missing bytes or exhausted
    budgets. This packet only supports reconsideration, never proves absence.
    """
    import re
    negatives={};queries=[]
    for r in row.get('rodadas',[]):
        report=r.get('pesquisa') or {}
        for q in report.get('buscas',[]):
            if q.get('estado') in ('OK','SEM_NOVOS_CANDIDATOS') and isinstance(q.get('consulta'),str) and q['consulta'] not in queries:
                queries.append(q['consulta'])
        for c in report.get('candidatos',[]):
            sha=(c.get('aquisicao') or {}).get('sha256')
            if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):continue
            # Stills may be relevant to static explanatory obligations. Do not
            # count a photo as a reviewed negative for a motion requirement.
            if c.get('tipo')=='foto' and necessidade.get('evidencia_visual')!='movimento':
                q=c.get('revisao') or {}
                from . import revisao_documental as R
                d=R.decidir(necessidade,c,q,tipo='foto')
                if (q.get('mostrar')==necessidade['mostrar'] and q.get('publicar') is False and
                    isinstance(q.get('pixels_sha256'),str) and re.fullmatch('[0-9a-f]{64}',q['pixels_sha256']) and
                    d.get('motivo') in ('SEM_PERTINENCIA','EVIDENCIA_DIRETA_NAO_LOCALIZADA') and
                    d.get('necessidade_id')==necessidade['id'] and q.get('revisao_id')):
                    rid=q['revisao_id']
                    negatives[rid]={'sha256':sha,'revisao_id':rid,'tipo':'foto','motivo':d['motivo']}
            for win in c.get('janelas',[]):
                pk=win.get('pacote') or {};d=win.get('decisao') or {}
                obs=pk.get('revisao_assistida') or {}
                if (pk.get('sha256_origem')!=sha or obs.get('sha256_origem')!=sha or
                    obs.get('necessidade_id')!=necessidade['id'] or pk.get('fato_id') not in necessidade['fatos'] or
                    pk.get('necessidade')!=necessidade['mostrar'] or d.get('necessidade_id')!=necessidade['id'] or
                    d.get('motivo') not in ('SEM_PERTINENCIA','MUDANCA_NAO_OBSERVADA','EVIDENCIA_DIRETA_NAO_LOCALIZADA') or
                    d.get('publicar') is not False or d.get('direitos_aprovados') is not False):continue
                from . import direcao_eventos as DE
                try:
                    q=DE.aceitar_observacao(pk,obs['resposta_observada'])
                    rid=q['revisao_id']
                    if obs.get('revisao_id')!=rid:continue
                except (ValueError,TypeError,KeyError,AttributeError):continue
                negatives[rid]={'sha256':sha,'revisao_id':rid,'inicio_s':pk['inicio_s'],
                    'duracao_s':pk['duracao_s'],'motivo':d['motivo']}
    return {'necessidade_id':necessidade['id'],'fatos':necessidade['fatos'],
        'consultas_executadas':queries,'revisoes_negativas':list(negatives.values()),
        'escopo':'APENAS_AMOSTRAS_INSPECIONADAS','inclui_fotos_inspecionadas':any(x.get('tipo')=='foto' for x in negatives.values()),'inexistencia_de_midia_comprovada':False,
        'publicar':False,'animacao_autorizada':False}


def reavaliar_complemento(necessidade,row,revisao,referencias,**kwargs):
    """Explicit curator handoff into E217; never auto-create a negative review."""
    from . import diretor_visual_e202 as D
    route=encaminhar(necessidade,row)
    if route['rota']=='REGISTRO_REAL':
        return {**route,'decisao':'USAR_MIDIA_REAL','animacao_autorizada':False}
    if row.get('estado')!='LACUNA_PENDENTE' or necessidade.get('necessidade')!='lacuna_explicativa':
        raise ValueError('E261-COMPLEMENTO-ESCOPO')
    if revisao.get('origem')!='CURADORIA_HUMANA':
        raise ValueError('E261-COMPLEMENTO-REVISAO-INDEPENDENTE')
    if revisao.get('motivo')=='BUSCA_SEM_REGISTRO_ADEQUADO':
        packet=route.get('evidencia_lacuna') or {}
        if not packet.get('revisoes_negativas') or not packet.get('consultas_executadas'):
            raise ValueError('E261-COMPLEMENTO-SEM-REVISAO-DE-MIDIA')
        # Preserve actual executed queries; do not accept claimed searches.
        revisao={**revisao,'consultas_executadas':packet['consultas_executadas']}
    return D.selecionar_complemento(necessidade,revisao,referencias,**kwargs)


def cobrir(necessidades,pesquisar,inspecionar,medir,*,max_visao,max_http,max_bytes,limitar_aquisicao=None):
    if not necessidades or len({n['id'] for n in necessidades})!=len(necessidades):raise ValueError('E253-IDS')
    for x in (max_visao,max_http,max_bytes):
        if type(x) is not int or x<=0:raise ValueError('E253-ORCAMENTO')
    limits={'visao':max_visao,'http':max_http,'bytes':max_bytes}
    start=medir()
    rows=[]
    for i,n in enumerate(necessidades):
        before=medir()
        if n['necessidade']=='territorio':
            rows.append({'necessidade_id':n['id'],'fatos':n['fatos'],'estado':'DELEGAR_ATLAS',
                'solicitacao_atlas':n.get('solicitacao_atlas'),'rodadas':[],'tentativas':0,
                'pronto_para_render':False,'publicar':False,'consumo':{k:0 for k in limits}})
            continue
        later=sum(x['necessidade']!='territorio' for x in necessidades[i+1:])
        remaining={k:max(0,limits[k]-before[k]+start[k]) for k in limits}
        # Reserve one logical vision call and a share of acquisition for later obligations.
        # Do not allocate a second vision call while another obligation would starve.
        cap={'visao':min(2,max(0,remaining['visao']-later)),
             'http':remaining['http']//(later+1),
             'bytes':remaining['bytes']//(later+1)}
        def allowed(phase):
            now=medir()
            local={k:now[k]-before[k] for k in limits}
            return local['visao']<min(cap['visao'],phase+1) and local['http']<cap['http'] and local['bytes']<cap['bytes']
        if all(cap.values()):
            scope=limitar_aquisicao(before['http']+cap['http'],before['bytes']+cap['bytes']) if limitar_aquisicao else nullcontext()
            with scope:
                result=cobertura_adaptativa(n,pesquisar,inspecionar,allowed)
        else:
            result={'estado':'LACUNA_PENDENTE','rodadas':[],'tentativas':0,'pronto_para_render':False,'publicar':False}
        after=medir()
        rows.append({**result,'necessidade_id':n['id'],'fatos':n['fatos'],'limites_locais':cap,
                     'consumo':{k:after[k]-before[k] for k in limits}})
    for n,row in zip(necessidades,rows):row['encaminhamento']=encaminhar(n,row)
    end=medir()
    counts={state:sum(r['estado']==state for r in rows) for state in
            ('CANDIDATO_PRIVADO_REVISADO','LACUNA_PENDENTE','DELEGAR_ATLAS')}
    return {'cobertura':rows,'resumo':counts,'total':len(rows),'limites':limits,
            'consumo':{k:end[k]-start[k] for k in limits},'pronto_para_render':False,'publicar':False,
            'estado':'COBERTURA_PRIVADA_PARCIAL' if counts['LACUNA_PENDENTE'] or counts['DELEGAR_ATLAS'] else 'CANDIDATOS_PRIVADOS_PENDENTES_DIREITOS'}
