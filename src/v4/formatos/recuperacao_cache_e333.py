"""E333: re-use alternative historical windows of the exact same obligation.
The caller authenticates pixels; no lexical guessing or extra vision.
"""
from copy import deepcopy
from . import direcao_eventos as DE,revisao_documental as R,especificidade_movimento_e331 as M

def alternativa(need,candidate,validate):
    if need.get('evidencia_visual')!='movimento' or candidate.get('tipo')!='video':return None
    a=candidate['aquisicao'];h=a['sha256'];old=candidate['decisao']['revisao_id']
    media={'id':candidate.get('source_id'),'expected_sha256':h,'duration_s':a['duration_s'],'width':a['width'],'height':a['height']}
    eligible=[]
    for row in candidate.get('janelas',[]):
        p=row.get('pacote') or {};q=p.get('revisao_assistida') or {}
        if (p.get('revisao_id')==old or p.get('publicar') is not False or p.get('sha256_origem')!=h
            or p.get('fato_id')!=need['fatos'][0] or p.get('necessidade')!=need['mostrar']
            or q.get('revisao_id')!=p.get('revisao_id') or not p.get('amostras')):continue
        try:
            d=R.decidir(need,candidate,q,tipo='video')
            if d['estado']!='PERTINENTE_PRIVADO':continue
            s=DE.candidato_revisado(p,media,fato_id=need['fatos'][0])
            if s['estado']!='CANDIDATO_PERTINENTE':continue
            eligible.append({'pacote':p,'midia':media,'decisao':d,'selection':s})
        except (ValueError,KeyError,TypeError,AttributeError):continue
    for ranked in DE.selecionar_revisados(eligible,fato_id=need['fatos'][0],preferir_legibilidade=bool(need.get('exigir_legibilidade'))):
        x=eligible[ranked['ordem']]
        c={**deepcopy(candidate),'decisao':x['decisao'],'selecao_janela':x['selection']}
        if not validate(need,c):continue
        return {'estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':[c.get('fonte'),c.get('source_id') or c.get('url')],
            'rodadas':[{'pesquisa':{'candidatos':[c]}}],'publicar':False,'origem':'JANELA_HISTORICA_REVALIDADA'}
    return None
