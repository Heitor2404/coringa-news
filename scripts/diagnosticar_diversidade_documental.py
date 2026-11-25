"""Editorial modality inventory, not an arbitrary approval gate."""
from collections import Counter

def diagnosticar(report):
    rows=[]
    for n in report.get('cobertura') or []:
        nid=n.get('necessidade_id')
        if n.get('estado')!='CANDIDATO_PRIVADO_REVISADO':
            rows.append({'id':nid,'estado':n.get('estado'),'modalidade':None})
            continue
        selected=[c for rd in n.get('rodadas') or [] for c in (rd.get('pesquisa') or {}).get('candidatos') or [] if (c.get('decisao') or {}).get('estado')=='PERTINENTE_PRIVADO']
        c=selected[-1] if selected else {}
        rows.append({'id':nid,'estado':n['estado'],'modalidade':c.get('tipo'),'sha256':(c.get('aquisicao') or {}).get('sha256')})
    counts=Counter(x['modalidade'] for x in rows if x['modalidade'])
    return {'modalidades_candidatos':dict(counts),'total_cobertos':sum(x['estado']=='CANDIDATO_PRIVADO_REVISADO' for x in rows),'linhas':rows,'somente_fotos':bool(counts) and set(counts)=={'foto'},'qualidade_editorial':'PENDENTE_INSPECAO_MONTAGEM','publicar':False}

def fila_editorial(report,audit):
    """Scoped observations supplement technical coverage, never promote or erase it."""
    if report.get('publish') is not False or audit.get('publicar') is not False:raise ValueError('E268-PRIVADO')
    from src.v4.formatos import revisao_documental as R
    needs={n['id']:n for n in report['triagem']}
    rows=[];matched=set()
    for row in report['cobertura']:
        nid=row['necessidade_id'];n=needs[nid]
        candidates=[c for rd in row.get('rodadas',[]) for c in (rd.get('pesquisa') or {}).get('candidatos',[])]
        chosen=[c for c in candidates if (c.get('decisao') or {}).get('estado')=='PERTINENTE_PRIVADO' and [c.get('fonte'),c.get('source_id') or c.get('url')]==list(row.get('selecionado') or [])]
        c=chosen[-1] if chosen else {}
        digest=(c.get('aquisicao') or {}).get('sha256') or ''
        observations=[o for o in audit.get('observacoes',[]) if o.get('id')==nid and o.get('mostrar')==n.get('mostrar') and o.get('sha256')==digest]
        if observations:matched.update((o['id'],o['sha256']) for o in observations)
        if row['estado']=='CANDIDATO_PRIVADO_REVISADO' and not observations:continue
        options=[];seen=set()
        for c in R.ordenar_candidatos(n,candidates):
            key=(c.get('fonte'),c.get('source_id') or c.get('url'))
            if not key[1] or key in seen:continue
            seen.add(key)
            d=c.get('decisao') or {}
            if d.get('estado')=='PERTINENTE_PRIVADO' or c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA' or c.get('observacao_negativa_reutilizada'):continue
            if d.get('estado')=='INSUFICIENTE' and d.get('motivo') in ('SEM_PERTINENCIA','NATUREZA_INCOMPATIVEL_OU_INCERTA','INCOMPATIBILIDADE_NA_AMOSTRA_REVISADA'):continue
            if n.get('evidencia_visual')=='movimento' and c.get('tipo')!='video':continue
            options.append({k:c.get(k) for k in ('tipo','titulo','pagina','fonte','source_id')}|{'estado':'PISTA_PENDENTE','publicar':False})
        rows.append({'id':nid,'mostrar':n['mostrar'],'estado_tecnico':row['estado'],'observacoes':observations,'pistas_foto':[x for x in options if x['tipo']=='foto'][:4],'pistas_video':[x for x in options if x['tipo']=='video'][:4],'publicar':False})
    return {'fila':rows,'observacoes_nao_aplicadas':[o for o in audit.get('observacoes',[]) if (o.get('id'),o.get('sha256')) not in matched],'publicar':False,'aprovacao_editorial':False}
