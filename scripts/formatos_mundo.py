"""Geometria do MUNDO para o ATLAS (histórias globais: cadeias de fornecimento, rotas, conexões entre países).

Fonte: world-atlas 2.0.2 (já instalado em motor4/node_modules; ISC) = Natural Earth 1:50m admin-0, domínio público.
Sem rede e sem instalação nova: só renomeia o objeto para o contrato do Palco ({topo: {objects: {paises}}, meta}).
uso: python scripts/formatos_mundo.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIG = RAIZ / 'motor4' / 'node_modules' / 'world-atlas' / 'countries-50m.json'
DEST = RAIZ / 'motor4' / 'formatos' / 'dados' / 'mundo.topo.json'


def main():
    bruto = ORIG.read_bytes()
    t = json.loads(bruto)
    t['objects'] = {'paises': t['objects']['countries']}
    meta = {'regiao': [-180, -58, 180, 78], 'atribuicao': ['Natural Earth (domínio público)'],
            'fonte': 'world-atlas 2.0.2 · Natural Earth 1:50m admin-0', 'sha256_origem': hashlib.sha256(bruto).hexdigest(),
            'contagem': {'paises': len(t['objects']['paises']['geometries'])}}
    DEST.write_text(json.dumps({'topo': t, 'meta': meta}, ensure_ascii=False, separators=(',', ':')))
    print(DEST, DEST.stat().st_size, meta['contagem'])


if __name__ == '__main__':
    main()
