"""Canal Ninguém Te Contou: roteiro → dados da animação → quadros (sem IA, sem voz)."""
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _roteiro():
    from src import fabula
    return fabula.validar(json.loads((RAIZ / 'tests' / 'ntc_roteiro_baratas.json').read_text(encoding='utf-8')))


def test_validar_corrige_valores_fora_da_lista():
    from src import fabula
    r = json.loads((RAIZ / 'tests' / 'ntc_roteiro_baratas.json').read_text(encoding='utf-8'))
    r['cenas'][0].update(cenario='marte', pose='voando', sfx='trovão', cor='abc', objetos=[{'tipo': 'dragão'}, {'tipo': 'rato'}])
    v = fabula.validar(r)
    c = v['cenas'][0]
    assert c['cenario'] == 'cozinha' and c['pose'] == 'neutra' and c['sfx'] is None and c['cor'] == 100
    assert [o['tipo'] for o in c['objetos']] == ['rato']


def test_roteiro_curto_e_recusado():
    from src import fabula
    with pytest.raises(ValueError):
        fabula.validar({'cenas': [{'narracao': 'oi'}] * 3})


def test_dados_do_template():
    from src import fabula
    r = _roteiro()
    tempos = [(k * 5.0, k * 5.0 + 5.0) for k in range(len(r['cenas']))]
    d = fabula.dados_template(r, tempos, [], tempos[-1][1] + 2.5)
    assert len(d['cenas']) == len(r['cenas'])
    assert d['cenas'][0]['titulo'].count('<i>') == 1                       # *BARATAS* colorida no título
    assert d['cenas'][-1]['fim']['p'] and d['cenas'][-1]['b'] == d['duration']
    p = [c['painel'] for c in d['cenas'] if c.get('painel') and c['painel']['rot'] == 'DIAS SEM BARATAS']
    assert [x['para'] for x in p] == [0, 1, 30, 90, 365] and p[2]['de'] == 1   # o contador continua de onde parou
    for c in d['cenas']:                                                    # Valdirene com os pés no chão do cenário
        assert c['chao'] == fabula.CHAO[c['cen']] and c['cen'] in fabula.CENARIOS
        for p in c['props']:
            assert p['ar'] > 0 and p['w'] > 0
    c0 = d['cenas'][0]                                                      # baratas na bancada: Val sai do meio e elas ficam atrás dela
    assert c0['val']['x'] != fabula.VAL_X['centro'] and all(p['atras'] for p in c0['props'] if p['t'] == 'barata')


def test_kit_vetorial_tem_tudo_que_o_roteiro_pode_pedir():
    import re
    from src import fabula
    cen = (fabula.VETOR / 'kit_cenarios.js').read_text(encoding='utf-8')
    obj = (fabula.VETOR / 'kit_objetos.js').read_text(encoding='utf-8')
    val = (fabula.VETOR / 'kit_val.js').read_text(encoding='utf-8')
    for n in fabula.CENARIOS:
        assert re.search(rf'\b{n}: o =>', cen), n
    for n, ar in fabula.PROPORCAO.items():                                  # mesma proporção no Python e no desenho
        assert re.search(rf'\b{n}: {{ ar: {str(ar).lstrip("0") if ar < 1 else ar},', obj), n
    for n in fabula.POSES:
        assert re.search(rf'\b{n}:\s+{{ D:', val), n
    for n, (y, x0, x1) in fabula.BANCADA.items():
        assert f'{n}: [{y}, {x0}, {x1}]' in cen
    assert len(fabula.SFX) >= 10


def test_previa_desenha_um_quadro_por_cena(tmp_path):
    pytest.importorskip('playwright')
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
    except Exception:
        pytest.skip('sem Chromium')
    from PIL import Image
    import io
    from src import fabula
    r = _roteiro()
    img = Image.open(io.BytesIO(fabula.quadros_previa(r, tmp_path)))
    assert img.size == (5 * 216, -(-len(r['cenas']) // 5) * 384)
