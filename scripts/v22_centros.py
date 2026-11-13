"""Auditoria horizontal (V2.2): mede centro da caixa e dos glifos de todo texto visível das composições.

Uso: python scripts/v22_centros.py <saida.json> [--so ids] [--passo 0.25]
Para cada composição (exemplo do catálogo) amostra a cena inteira (padrão a cada 0,25 s) e grava, por elemento,
o pior desvio da caixa e dos glifos em relação a x = 540, o alinhamento efetivo e se é declarado (data-centro).
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, os.getcwd())
from src.v2 import galeria, palco  # noqa: E402
from src.v2.centros import medir  # noqa: E402


def main():
    saida = Path(sys.argv[1]); passo = float(sys.argv[sys.argv.index('--passo') + 1]) if '--passo' in sys.argv else .25
    so = sys.argv[sys.argv.index('--so') + 1].split(',') if '--so' in sys.argv else []
    tr = saida.parent / '_centros'
    out = {}
    for m in galeria.catalogo(tr / '_cat'):
        if so and m['id'] not in so:
            continue
        d = galeria.dados_exemplo(m)
        with palco.abrir(palco.preparar(d), tr / m['id']) as pg:
            out[m['id']] = medir(pg, d['duration'], passo)
        n = [x for x in out[m['id']] if x['alinhamento'] == 'centro' or x['declarado']]
        pior = max((x['_d'] for x in n), default=0)
        print(f"{m['id']:26s} textos={len(out[m['id']]):3d} centralizados={len(n):2d} pior_desvio={pior:6.1f}", flush=True)
    saida.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
