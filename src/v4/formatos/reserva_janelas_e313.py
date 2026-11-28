"""E313: reserve actual admissible source windows before closing coverage.
No new search budget, no semantic inference, no forced same-source reuse.
Use the SAME E254 bridge to determine effective capacity, including progression.
"""
from . import ponte_cobertura_filme as P

def propor(need,candidate,selection,decision):
    c={**candidate,'selecao_janela':selection,'decisao':decision}
    row={'necessidade_id':need['id'],'estado':'CANDIDATO_PRIVADO_REVISADO',
         'selecionado':[c.get('fonte'),c.get('source_id') or c.get('url')],
         'rodadas':[{'pesquisa':{'candidatos':[c]}}]}
    case={'chapters':[{'needs':[need['id']]}]}
    chosen,gate=P.preparar_cobertura({'publish':False,'triagem':[need],'cobertura':[row]},case,minimo_s=1.4)
    if not gate['pronto_para_tts'] or need['id'] not in chosen:return None
    x=chosen[need['id']]
    if x['kind']!='video':return None
    a=c['aquisicao'];start=x['window']['source_in_seconds']
    return {'id':need['id'],'fatos':tuple(need['fatos']),'sha256':a['sha256'],'pagina':c['pagina'],
            'inicio':start,'fim':start+x['cap'],'revisao_id':decision['revisao_id']}

def compativel(reserva,existentes,*,pages=(),hashes=()):
    if reserva is None:return False
    previous=[x for x in existentes.values() if x['id']!=reserva['id']]
    same=[x for x in previous if x['sha256']==reserva['sha256'] or x['pagina']==reserva['pagina']]
    if not same and (reserva['pagina'] in pages or reserva['sha256'] in hashes):
        return False # occupied by a static original, or an untracked legacy selection
    for x in same:
        if x['sha256']!=reserva['sha256'] or x['pagina']!=reserva['pagina']:return False
        if set(x['fatos'])&set(reserva['fatos']):return False
        if max(x['inicio'],reserva['inicio'])<min(x['fim'],reserva['fim'])-.001:return False
    return True

def escolher(need,candidate,eligible,ranked,reservas,ordem,*,pages=(),hashes=()):
    """Rank existing pertinent candidates only. Prefer forward chronology when
    the previous story obligation used the same source; not a hard quota."""
    options=[]
    preceding=[x for x in reservas.values() if ordem.get(x['id'],-2)==ordem.get(need['id'],-1)-1]
    for rank,entry in enumerate(ranked):
        k=entry['ordem'];_,selection,decision=eligible[k]
        reservation=propor(need,candidate,selection,decision)
        if not compativel(reservation,reservas,pages=pages,hashes=hashes):continue
        reverse=any(x['sha256']==reservation['sha256'] and reservation['inicio']<x['fim']-.001 for x in preceding)
        options.append((reverse,rank,k,reservation))
    if not options:return None
    _,_,k,reservation=min(options,key=lambda x:x[:2])
    return k,reservation


def janela_elegivel(need,sha,pagina,window,reservas):
    """Cheap structural prefilter before paid review, matching E254 reserved capacity.
    No inferred visual relation; never mark an excluded window semantically negative."""
    import math
    start=window.get('inicio_s');duration=window.get('duracao_s')
    if not all(type(v) in (int,float) and math.isfinite(v) for v in (start,duration)) or start<0 or duration<1.4:return False
    end=start+math.floor(min(3.8,duration)*30+1e-6)/30
    for x in reservas.values():
        if x['id']==need['id'] or (x['sha256']!=sha and x['pagina']!=pagina):continue
        if x['sha256']!=sha or x['pagina']!=pagina or set(x['fatos'])&set(need['fatos']):return False
        if max(start,x['inicio'])<min(end,x['fim'])-.001:return False
    return True

def liberar_reserva_individual(nid,reservas,pages,hashes):
    """Release only the rejected obligation's reservation. A shared source
    stays reserved for other facts. Caller owns the rollback snapshot."""
    old=reservas.pop(nid,None)
    if old is None:return
    if not any(x['pagina']==old['pagina'] for x in reservas.values()):pages.discard(old['pagina'])
    if not any(x['sha256']==old['sha256'] for x in reservas.values()):hashes.discard(old['sha256'])
