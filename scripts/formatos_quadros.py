"""Quadros parados (Remotion still) de um plano de formato JÁ preflightado — inspeção local de layout, sem MP4.
uso: python scripts/formatos_quadros.py <saida_preflight> <t1,t2,...> <folha.jpg>"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.v4.backends.js import CHROME  # noqa: E402
from src.v4.formatos import plano as P  # noqa: E402

S, ts, folha = Path(sys.argv[1]), [float(x) for x in sys.argv[2].split(',')], Path(sys.argv[3])
pl = json.loads((S / 'plano_resolvido.json').read_text())
can = P.canal(pl.get('canal', 'coringa'))
geo = json.loads((RAIZ / pl['geo']).read_text()) if pl.get('geo') else None
pj = S / 'props_quadros.json'
pj.write_text(json.dumps(P.props(pl, {k: can[k] for k in ('cores', 'fontes', 'tempo', 'palco')}, geo, json.loads((S / 'ativos.json').read_text()))))
rem = RAIZ / 'motor4' / 'remotion'
ims = []
for t in ts:
    out = S / f'q_{t:.1f}.png'
    subprocess.run(['npx', 'remotion', 'still', 'src/index.ts', 'Formato', str(out), f'--props={pj}', f'--frame={int(t * 30)}', '--gl=swangle',
                    f'--browser-executable={CHROME}', f'--public-dir={rem / "public"}'], cwd=rem, capture_output=True, timeout=300)
    ims.append(Image.open(out).convert('RGB').resize((270, 480)))
o = Image.new('RGB', (270 * min(5, len(ims)), 480 * ((len(ims) + 4) // 5)))
for i, im in enumerate(ims):
    o.paste(im, ((i % 5) * 270, (i // 5) * 480))
o.save(folha, quality=82)
