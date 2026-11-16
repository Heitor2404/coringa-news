"""MICROCENA (validação de generalização, 16/11): recorta de um roteiro pronto UM acontecimento do tipo pedido e só os
trechos de narração que cabem em ~5–8 s. Todo o resto é o fluxo real do V3 (diretor automático, acervo, narração,
render, fiscal). Nenhum storyboard escrito à mão; nenhuma escolha por nome de arquivo ou tema.

MICROCENA=historia|geografia|biologia|ciencia (ou lista de tipos separada por vírgula) no ambiente do main.py.
"""
from __future__ import annotations

import copy
import re

PERFIS = {   # o problema visual que cada microcena precisa provar (tipos de acontecimento do contrato)
    'historia': {'tipos': ['evento_historico', 'impacto', 'pessoa', 'lugar', 'documento'], 'abertura': True,
                 'prova': 'imagem documental com abertura forte e enquadramento adequado'},
    'geografia': {'tipos': ['deslocamento', 'territorio', 'localizacao'], 'abertura': False,
                  'prova': 'mapa revelando uma rota ou propagação'},
    'biologia': {'tipos': ['mecanismo', 'processo', 'transformacao', 'movimento'], 'abertura': False,
                 'prova': 'mecanismo representado por animação 2D/2.5D'},
    'ciencia': {'tipos': ['processo', 'transformacao', 'mecanismo', 'orbita', 'nivel', 'movimento'], 'abertura': False,
                'prova': 'transformação ou processo visualmente demonstrado'},
}
PALAVRAS_MIN, PALAVRAS_MAX = 12, 24          # ~5–8 s na velocidade atual da voz (≈ 3 palavras/s)


def _palavras(t: str) -> int:
    return len(re.findall(r'\w+', str(t or '')))


def recortar(v: dict, perfil: str) -> dict:
    from src.v3 import pipeline
    p = PERFIS.get(perfil) or {'tipos': [t.strip() for t in perfil.split(',') if t.strip()], 'abertura': False, 'prova': perfil}
    evs = pipeline.eventos_de(v)
    cand = [e for e in evs if e.get('tipo') in p['tipos']]
    if not cand:
        raise ValueError(f"microcena {perfil}: o roteiro não tem acontecimento dos tipos {p['tipos']} "
                         f"(tem: {sorted({e.get('tipo') for e in evs if e.get('tipo')})})")
    # ordem: tipo mais específico do perfil primeiro; crítico antes de apoio; para abertura, o que inclui o trecho 0
    cand.sort(key=lambda e: (0 if p['abertura'] and 0 in e['trechos'] else 1, p['tipos'].index(e['tipo']), 0 if e.get('critico') else 1, e['trechos'][0]))
    ev = cand[0]
    trechos, n = [], 0
    for t in sorted(ev['trechos']):
        w = _palavras(v['cenas'][t].get('fala'))
        if trechos and n + w > PALAVRAS_MAX:
            break
        trechos.append(t)
        n += w
        if n >= PALAVRAS_MIN:
            break
    if n < 8:                                  # curto demais sozinho: completa com o trecho seguinte (contexto imediato)
        for t in range(trechos[-1] + 1, len(v['cenas'])):
            w = _palavras(v['cenas'][t].get('fala'))
            if n + w > PALAVRAS_MAX:
                break
            trechos.append(t)
            n += w
            if n >= PALAVRAS_MIN:
                break
    novo = copy.deepcopy(v)
    novo['cenas'] = [novo['cenas'][t] for t in trechos]
    novo['_microcena'] = {'perfil': perfil, 'prova': p['prova'], 'evento': ev['id'], 'tipo': ev['tipo'], 'critico': ev.get('critico'),
                          'trechos_originais': trechos, 'palavras': n, 'candidatos': [(e['id'], e['tipo']) for e in cand[:5]]}
    return novo
