"""Captura cada composição do catálogo em 4 instantes (início, meio, máximo de informação, final) a partir de QUALQUER
checkout do motor (ex.: worktree da V2 original), para a galeria comparativa V2 × V2.1.

Uso: (cd <raiz do checkout> && python /caminho/scripts/v2_capturar.py <saida> [--so ids])
Grava <saida>/<id>_<k>.jpg e <saida>/catalogo.json. Só usa o código do checkout atual (cwd).
"""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, os.getcwd())
from src.v2 import galeria, palco  # noqa: E402

FRACOES = (0.08, 0.45, 0.75, 0.97)


def main():
    saida = Path(sys.argv[1]).resolve(); saida.mkdir(parents=True, exist_ok=True)
    so = sys.argv[sys.argv.index('--so') + 1].split(',') if '--so' in sys.argv else []
    cat = galeria.catalogo(saida / '_cat')
    out = {}
    for m in cat:
        if so and m['id'] not in so:
            continue
        d = galeria.dados_exemplo(m)
        t0 = time.time()
        try:
            with palco.abrir(palco.preparar(d), saida / '_tr' / m['id']) as pg:
                ts = []
                for k, f in enumerate(FRACOES):
                    t = round(d['duration'] * f, 2)
                    palco.capturar(pg, t, saida / f"{m['id']}_{k}.jpg", 86)
                    ts.append(t)
                geo = palco.medir(pg, d['duration'], .25)
            out[m['id']] = {'meta': m, 'tempos': ts, 'segundos': round(time.time() - t0, 1), 'problemas': geo}
        except Exception as e:
            out[m['id']] = {'meta': m, 'erro': str(e)}
        print(m['id'], out[m['id']].get('segundos'), len(out[m['id']].get('problemas', [])), flush=True)
    (saida / 'catalogo.json').write_text(json.dumps(out, ensure_ascii=False, default=str), encoding='utf-8')


if __name__ == '__main__':
    main()
