"""E314: bind a registered E213 candidate to a specific reviewed gap.
Private only. Preserve the exact clip duration and never turn a failed search,
a missing file, or a model proposal into permission to animate.
"""
import math
from pathlib import Path
from . import ponte_animacao_editorial as B,politica_animacao as PA,cobertura_documental as C

def source_path(source):
    p=Path(source)
    if p.is_absolute() or p.parts[:1]!=('stage_documental',) or '..' in p.parts or p.is_symlink() or not p.resolve().is_relative_to(Path('stage_documental').resolve()):
        raise ValueError('E314-CAMINHO')
    return p

def entrega(n,row,packet):
    if (n.get('necessidade')!='lacuna_explicativa' or not n.get('lacuna') or
        row.get('estado')!='LACUNA_PENDENTE' or not isinstance(packet,dict) or
        packet.get('publicar') is not False or packet.get('direitos_aprovados') is not False or
        packet.get('origem') not in ('CURADORIA_HUMANA','INSPECAO_ASSISTIDA_PRIVADA') or
        packet.get('necessidade_id')!=n['id'] or packet.get('fatos')!=n['fatos'] or
        packet.get('acao')!=n['mostrar'] or packet.get('lacuna')!=n['lacuna'] or
        packet.get('midia_adequada') is not False or
        not isinstance(packet.get('revisao_id'),str) or not packet['revisao_id'].strip() or
        not isinstance(packet.get('justificativa'),str) or len(packet['justificativa'].strip())<20):
        raise ValueError('E314-ESCOPO')
    motive=packet.get('motivo_lacuna')
    if motive=='BUSCA_SEM_REGISTRO_ADEQUADO':
        evidence=C.evidencia_lacuna(n,row)
        if not evidence['revisoes_negativas'] or not evidence['consultas_executadas']:
            raise ValueError('E314-SEM-BUSCA-REVISADA')
    if PA.decidir_complemento(midia_adequada=False,acao=n['mostrar'],lacuna=n['lacuna'],
             motivo_lacuna=motive,renderer='animation_clip:'+B.SCHEMA)!='ANIMACAO_COMPLEMENTAR_EM_QA_PRIVADA':
        raise ValueError('E314-POLITICA')
    src=source_path(packet['local_source'])
    proof=B.verificar(packet['renderer'],src)
    if packet.get('sha256')!=proof['sha256'] or packet.get('referencia')!=proof['source']:
        raise ValueError('E314-REFERENCIA')
    proof.update(acao=n['mostrar'],lacuna=n['lacuna'],motivo_lacuna=motive,midia_adequada=False)
    span=math.ceil(proof['duration_s']*30-1e-8)/30
    entry=PA.POLICY['external_candidates'][packet['renderer']]
    shot={'id':n['id'],'type':'animation_clip','start':0.,'end':span,
          'asset':'animation_e213/'+proof['sha256']+'.mp4','animation_proof':proof,
          'animation_local_source':str(src),'animation_review':packet,
          'evidence':'explainer','source':entry['source'],'source_display':entry['credit'],
          'subject':n['sujeito'],'headline':n['mostrar'],'lead':'Ilustração explicativa','cues':[]}
    validar(shot)
    return shot

def validar(shot):
    PA.exigir([shot],privado=True)
    p=shot['animation_proof'];r=shot['animation_review']
    if (r.get('necessidade_id')!=shot['id'] or r.get('acao')!=p['acao'] or r.get('lacuna')!=p['lacuna'] or
        r.get('sha256')!=p['sha256'] or r.get('renderer')!=p['renderer'] or r.get('referencia')!=p['source'] or
        r.get('local_source')!=shot.get('animation_local_source') or r.get('publicar') is not False or
        r.get('direitos_aprovados') is not False or r.get('midia_adequada') is not False or
        r.get('origem') not in ('CURADORIA_HUMANA','INSPECAO_ASSISTIDA_PRIVADA') or
        not r.get('fatos') or not r.get('revisao_id') or shot.get('literal_identity') or
        shot.get('assetB') or shot.get('source_in_seconds') is not None):
        raise ValueError('E314-VINCULO')
    actual=B.verificar(p['renderer'],source_path(shot['animation_local_source']))
    if any(p.get(k)!=v for k,v in actual.items()):raise ValueError('E314-PROVA')
    return actual

def preparar(shot,public_root):
    validar(shot)
    p=shot['animation_proof']
    out=B.preparar(p['renderer'],source_path(shot['animation_local_source']),public_root,
        cid=shot['id'],acao=p['acao'],lacuna=p['lacuna'],motivo_lacuna=p['motivo_lacuna'],
        midia_adequada=False,start=shot['start'])
    if out['end']!=shot['end'] or out['animation_proof']!=p:raise ValueError('E314-TEMPO-OU-PROVA')
    return out
