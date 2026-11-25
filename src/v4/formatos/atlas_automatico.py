"""Entrega ATLAS automática para necessidades `territorio` (E284).

Antes, o fluxo integral só aceitava mapas com `CURADORIA_GEOGRAFICA_VERIFICADA` preparados à mão
(`entregas_verificadas.json`). Aqui o mesmo caminho existente é encadeado: verificação geográfica por duas fontes
(`geografia_verificada`) → aquisição/reuso dos mosaicos (`qa_atlas_multiscale.adquirir_bases`) → plano e render
nativo (`qa_documentario_geografia_e219.mapclip`) → comprovante. Sem verificação concordante, nada é entregue e a
necessidade fica pendente com o motivo — nunca coordenadas de modelo.
"""
from __future__ import annotations

from pathlib import Path


def entregar(necessidade, saida, *, verificar=None, adquirir=None, resolver=None, mapclip=None, sha=None, span=5.5):
    from src.v4.formatos import geografia_verificada as GV
    verificar = verificar or GV.verificar
    if necessidade.get('necessidade') != 'territorio':
        raise ValueError('ATLAS-AUTO-NECESSIDADE')
    ctx = ' '.join((necessidade.get('pesquisa') or {}).get('contexto_busca') or necessidade.get('contexto_busca') or [])
    v = verificar(necessidade['sujeito'], ctx, rotulo=necessidade['sujeito'], caso_id='geo_' + necessidade['id'].lower())
    if v.get('estado') != 'VERIFICADA':
        return None, {'necessidade_id': necessidade['id'], 'estado': 'PENDENTE', 'motivo': v.get('motivo')}
    if adquirir is None or resolver is None or mapclip is None or sha is None:
        from scripts import qa_atlas_multiscale as G, qa_documentario_geografia_e219 as E
        adquirir, resolver, sha = adquirir or G.adquirir_bases, resolver or G.resolver, sha or E.sha
        if mapclip is None:
            E.MAP = Path(saida) / necessidade['id']
            E.MAP.mkdir(parents=True, exist_ok=True)
            mapclip = lambda ch, s, p: E.mapclip(ch, s, plano_resolvido=p, documentary_layout=True)
    caso = v['caso_atlas']
    adquirido = adquirir(caso)
    ch, plano, camera = resolver(caso, adquirido, span)
    clip, prova = mapclip(ch, span, plano)
    entrega = {'necessidade_id': necessidade['id'], 'fatos': necessidade['fatos'], 'mostrar': necessidade['mostrar'],
               'origem': GV.ORIGEM, 'verificacao': v, 'local_source': str(clip), 'atlas_proof': str(prova),
               'expected_sha256': sha(clip), 'camera': camera}
    return entrega, {'necessidade_id': necessidade['id'], 'estado': 'ENTREGUE', 'fontes': caso['fontes']}


def completar_entregas(report, entregas, saida, **kw):
    """Acrescenta mapas automáticos às entregas existentes, sem substituir curadoria já presente."""
    atlas = dict((entregas or {}).get('atlas') or {})
    estados = {r['necessidade_id']: r.get('estado') for r in report.get('cobertura', [])}
    log = []
    for n in report.get('triagem', []):
        if n.get('necessidade') == 'territorio' and estados.get(n['id']) == 'DELEGAR_ATLAS' and n['id'] not in atlas:
            try:
                e, info = entregar(n, saida, **kw)
            except Exception as exc:          # render/aquisição falhou: pendente, nunca mapa sem comprovante
                e, info = None, {'necessidade_id': n['id'], 'estado': 'PENDENTE', 'motivo': 'FALHA:' + type(exc).__name__}
            if e:
                atlas[n['id']] = e
            log.append(info)
    return {**(entregas or {}), 'atlas': atlas}, log
