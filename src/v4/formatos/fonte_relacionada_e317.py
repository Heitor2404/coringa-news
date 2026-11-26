"""E317: a related, already downloaded record is a discovery hint only.
The new obligation still requires an independent inspection and non-overlapping
window. Exact factual source page, not merely lexical similarity.
"""
from copy import deepcopy

def pista(n,case,tri,rows,acquired,order):
    if n.get('papel_visual')!='consequencia' or n['id'] not in order:return None
    previous=next((x for x in tri if order.get(x['id'],-2)==order[n['id']]-1),None)
    if not previous or previous.get('papel_visual') not in ('acao','mecanismo') or set(previous['fatos'])&set(n['fatos']):return None
    facts={f['id']:f.get('fonte') for f in case.get('fatos',[])}
    common={facts.get(i) for i in n['fatos'] if isinstance(facts.get(i),str)} & {facts.get(i) for i in previous['fatos'] if isinstance(facts.get(i),str)}
    row=rows.get(previous['id']) or {}
    if row.get('estado')!='CANDIDATO_PRIVADO_REVISADO':return None
    key=tuple(row.get('selecionado') or ())
    if len(key)!=2 or key not in acquired:return None
    for r in reversed(row.get('rodadas',[])):
        for c in r['pesquisa']['candidatos']:
            if (c.get('fonte'),c.get('source_id') or c.get('url'))!=key or c.get('tipo')!='video' or c.get('pagina') not in common:continue
            dec=c.get('decisao') or {};meta=acquired[key][0]
            if (dec.get('estado')!='PERTINENTE_PRIVADO' or dec.get('necessidade_id')!=previous['id'] or not dec.get('revisao_id')
                or dec.get('publicar') is not False or dec.get('direitos_aprovados') is not False
                or (c.get('aquisicao') or {}).get('sha256')!=meta.get('sha256')):continue
            fields=('fonte','source_id','tipo','url','pagina','titulo','descricao','descricao_integral','desc',
                'credito','licenca','direitos','natureza_preliminar','variantes','tamanho_declarado','largura_declarada','altura_declarada')
            return {**{k:deepcopy(c[k]) for k in fields if k in c},'pista_fonte_relacionada':previous['id']}
    return None
