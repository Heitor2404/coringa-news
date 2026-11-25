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
