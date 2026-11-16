"""Material local para os testes V3.1: roteiro e acervo reais do piloto Ever Given (tests/piloto_ever_given), sem IA.
Os storyboards destes testes são STUBS escritos para exercitar o código — não são saídas de modelo."""
from __future__ import annotations

import copy
import json
from pathlib import Path

BASE = Path(__file__).parent / 'piloto_ever_given'


def roteiro() -> dict:
    v = json.loads((BASE / 'roteiro.json').read_text(encoding='utf-8'))
    ac = json.loads((BASE / 'acervo.json').read_text(encoding='utf-8'))
    ac = ac.get('acervo', ac) if isinstance(ac, dict) else ac
    v['acervo'] = []
    for x in ac:
        if x.get('arquivo') and (BASE / 'img' / x['arquivo']).exists():
            v['acervo'].append({**x, 'arq': str(BASE / 'img' / x['arquivo'])})
    v['pergunta'] = 'Como um navio parou o Canal de Suez por seis dias?'
    return v


def plano(trechos, foto='a3', evento='e1', **kw):
    p = {'trechos': trechos, 'evento_id': evento, 'fato_id': 'f1', 'receita': 'R-APROXIMA-OBJETO', 'funcao_narrativa': 'contexto',
         'recurso_visual': {'tipo': 'foto', 'id': foto}, 'composicao': 'doc.plano', 'funcao_documental': 'REGISTRO',
         'objeto_principal': 'navio', 'plano_inicial': 'geral', 'plano_final': 'objeto', 'acao_visual': 'aproxima do navio',
         'movimento_camera': 'aproximar', 'anotacoes': [], 'transicao': 'dissolve', 'selo_texto': 'CANAL DE SUEZ, 2021'}
    p.update(kw)
    return p


def storyboard_valido(v: dict) -> dict:
    """Um plano por trecho, alternando fotos para não repetir em seguida (stub)."""
    fotos = [x['id'] for x in v['acervo']]
    evs = {}
    for i, c in enumerate(v['cenas']):
        ac = c.get('acontecimento') or {}
        evs[i] = ac.get('id') or 'e1'
    return {'planos': [plano([i], foto=fotos[i % len(fotos)], evento=evs[i], funcao_documental='CONTEXTO',
                             funcao_narrativa='gancho' if i == 0 else 'fechamento' if i == len(v['cenas']) - 1 else 'contexto')
                       for i in range(len(v['cenas']))]}


def copia(x):
    return copy.deepcopy(x)
