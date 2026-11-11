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
        if c.get('val'):
            v = c['val']
            pes = v['y'] + 1032 * v['s'] * 815 / 860
            assert abs(pes - fabula.CHAO[c['cen']]) < 3


def test_todos_os_arquivos_existem():
    from src import fabula
    for n in fabula.CENARIOS:
        assert (fabula.CANAL / 'cen' / f'{n}.svg').exists(), n
    for n in fabula.OBJETOS:
        assert (fabula.CANAL / 'prop' / f'{n}.svg').exists(), n
    for n in ('neutra', 'comemora', 'explica', 'susto', 'brava', 'desesperada'):
        assert (fabula.CANAL / 'val' / f'{n}.svg').exists(), n
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
