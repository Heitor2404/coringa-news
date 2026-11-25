"""E253: shared budgets and coverage reporting for a complete set of obligations.
No rendering or automatic approval. Geographic obligations remain with ATLAS.
"""
from .revisao_documental import cobertura_adaptativa

def cobrir(necessidades,pesquisar,inspecionar,medir,*,max_visao,max_http,max_bytes):
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
            result=cobertura_adaptativa(n,pesquisar,inspecionar,allowed)
        else:
            result={'estado':'LACUNA_PENDENTE','rodadas':[],'tentativas':0,'pronto_para_render':False,'publicar':False}
        after=medir()
        rows.append({**result,'necessidade_id':n['id'],'fatos':n['fatos'],'limites_locais':cap,
                     'consumo':{k:after[k]-before[k] for k in limits}})
    end=medir()
    counts={state:sum(r['estado']==state for r in rows) for state in
            ('CANDIDATO_PRIVADO_REVISADO','LACUNA_PENDENTE','DELEGAR_ATLAS')}
    return {'cobertura':rows,'resumo':counts,'total':len(rows),'limites':limits,
            'consumo':{k:end[k]-start[k] for k in limits},'pronto_para_render':False,'publicar':False,
            'estado':'COBERTURA_PRIVADA_PARCIAL' if counts['LACUNA_PENDENTE'] or counts['DELEGAR_ATLAS'] else 'CANDIDATOS_PRIVADOS_PENDENTES_DIREITOS'}
