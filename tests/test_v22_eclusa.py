"""V2.2 P1-12 — a eclusa com 'degraus' identifica o esquema (1 câmara = desnível total; no canal, N câmaras) sem cobrir
o próprio mecanismo nem a legenda, em toda a viagem da câmera."""
from src.v2 import palco

P = {'sentido': 'subir', 'desnivel_m': 26, 'lago': 'LAGO GATÚN', 'mar': 'MAR DO CARIBE', 'kicker': 'MECANISMO · ECLUSA', 'degraus': 3}
JS = """(()=>{const e=V2.cenas[0].el,c=e.querySelector('.esc-deg').getBoundingClientRect(),l=document.getElementById('legenda').getBoundingClientRect();
  const sob=[...e.querySelectorAll('svg *, .navio, [data-g]')].filter(x=>!x.closest('.esc-deg')&&+getComputedStyle(x).opacity>.05)
    .map(x=>{const r=x.getBoundingClientRect(),v=x.closest('svg')?x.closest('svg').getBoundingClientRect():null;   // recorta pela janela visível do SVG
      return v?{left:Math.max(r.left,v.left),top:Math.max(r.top,v.top),right:Math.min(r.right,v.right),bottom:Math.min(r.bottom,v.bottom),width:r.width,height:r.height}:r;})
    .filter(r=>r.right>r.left&&r.bottom>r.top).filter(r=>r.width>2&&r.height>2&&r.width<1000&&r.height<1500&&r.right>c.left+2&&r.left<c.right-2&&r.bottom>c.top+2&&r.top<c.bottom-2);
  return {txt:e.querySelector('.esc-deg').textContent, chip:[c.left,c.top,c.right,c.bottom], leg:[l.top,l.bottom], sob:sob.length}})()"""


def test_eclusa_degraus_identifica_esquema_sem_cobrir_mecanismo(tmp_path):
    caps = [{'start': .2, 'end': 9.8, 'words': [{'w': w, 's': .2 + i * .4} for i, w in enumerate('A ÁGUA DO LAGO DESCE E ENCHE A CÂMARA'.split())]}]
    d = {'duration': 10, 'meta': {'motor': 'v2'}, 'captions': caps, 'scenes': [{'comp': 'mecanismo.eclusa', 'start': 0, 'end': 10, 'params': dict(P)}]}
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        for t in (.8, 2, 3, 4, 5, 6, 7, 8, 8.5, 9.8):      # câmera aberta, seguindo o navio, e aberta de novo
            pg.evaluate(f'seek({t})')
            g = pg.evaluate(JS)
            assert '1 CÂMARA PARA OS 26 m' in g['txt'] and '3 CÂMARAS EM SEQUÊNCIA' in g['txt'], g
            assert g['sob'] == 0, (t, g)                     # nada do mecanismo sob o aviso
            assert g['chip'][3] <= g['leg'][0] + 2, (t, g)   # aviso acima da legenda
