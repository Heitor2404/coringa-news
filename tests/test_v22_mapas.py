"""V2.2 — rótulos de mar/golfo sobre ÁGUA, em várias regiões, com a câmera andando e no quadro final.

A verificação de terra é feita em Python (geo.em_terra, Natural Earth), independente do código do palco que escolheu
a posição. Sem ajuste por nome: as regiões testadas incluem golfos dentro de países côncavos e mares fechados."""
import pytest

from src.v2 import geo, palco

TEM_NE = (palco.PASTA / 'dados' / 'ne').exists()
REGIOES = [   # (nome, composição, params, precisa de algum rótulo de mar visível no final?)
    ('Panamá (golfo côncavo)', 'mapa.territorio', {'pais': 'Panama', 'titulo': 'Panamá', 'folga': .25, 'max_paises': 2}, True),
    ('Itália (Mediterrâneo)', 'mapa.territorio', {'pais': 'Italy', 'titulo': 'Itália', 'folga': .2}, True),
    ('Catar (Golfo Pérsico)', 'mapa.territorio', {'pais': 'Qatar', 'titulo': 'Catar', 'folga': 1.5}, False),
    ('Veracruz (Golfo do México)', 'mapa.localizacao', {'titulo': 'Veracruz', 'pontos': [{'nome': 'Veracruz', 'lon': -96.13, 'lat': 19.17}], 'folga': 6}, True),
    ('Bangladesh (Baía de Bengala)', 'mapa.territorio', {'pais': 'Bangladesh', 'titulo': 'Bangladesh', 'folga': .4}, False),
    ('Venezuela (Caribe; Canal do Iucatão com anel invertido nos dados)', 'mapa.territorio', {'pais': 'Venezuela', 'titulo': 'Venezuela', 'folga': .35, 'max_mares': 2}, True),
    ('Lisboa (Atlântico)', 'mapa.localizacao', {'titulo': 'Lisboa', 'pontos': [{'nome': 'Lisboa', 'lon': -9.14, 'lat': 38.72}], 'folga': 6}, True),
]
JS = """(()=>{const c=V2.cenas[0],h=c.el.querySelector('.mapa-host'),m=h._map,dy=m._dy||0,out=[];
 c.el.querySelectorAll('.rot-mapa.mar').forEach(e=>{ if(+getComputedStyle(e).opacity<.05) return; const r=e.getBoundingClientRect(); const pts=[];
  for(const fx of [0,.25,.5,.75,1]) for(const fy of [0,.5,1]){ const u=m.unproject([r.left+fx*r.width, r.top+fy*r.height-dy]); pts.push([u.lng,u.lat]); }
  const u=m.unproject([(r.left+r.right)/2,(r.top+r.bottom)/2-dy]); out.push({nome:e.textContent, ne:e.dataset.ne, centro:[u.lng,u.lat], pts, caixa:[r.left,r.top,r.right,r.bottom]}); }); return out;})()"""


@pytest.mark.skipif(not TEM_NE, reason='Natural Earth não baixado')
@pytest.mark.parametrize('nome,comp,params,precisa', REGIOES, ids=[r[0] for r in REGIOES])
def test_rotulo_de_mar_sobre_agua(tmp_path, nome, comp, params, precisa):
    d = {'duration': 5, 'meta': {'motor': 'v2'}, 'captions': [], 'scenes': [{'comp': comp, 'start': 0, 'end': 5, 'params': dict(params)}]}
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        visto_final = []
        for t in (1.0, 2.0, 3.0, 4.6):          # câmera andando e enquadramento final
            pg.evaluate(f'seek({t})')
            for r in pg.evaluate(JS):
                terra = [p for p in r['pts'] if geo.em_terra(*p)]
                assert not terra, (nome, t, r['nome'], terra[:3])
                # o rótulo está no mar que ele NOMEIA (verificação plana independente do d3)
                assert r['ne'] in geo.mares_em(*r['centro']), (nome, t, r['nome'], r['ne'], geo.mares_em(*r['centro']))
                assert 60 <= r['caixa'][0] and r['caixa'][2] <= 1020, (nome, t, r['nome'], r['caixa'])
                if t == 4.6:
                    visto_final.append(r['nome'])
        if precisa:
            assert visto_final, f'{nome}: nenhum rótulo de mar no quadro final'
        assert 'Mar das Caraíbas' not in visto_final      # nomes em português do Brasil
