"""V2.2 — foto histórica: enquadramento decidido pela resolução e pela proporção reais (fixtures reais, licenciadas)."""
from pathlib import Path

import pytest
from PIL import Image

from src.v2 import acervo_v2, fiscal_v2, palco

M = Path(__file__).parent / 'midia'
CASOS = [  # (arquivo, modo esperado)
    ('foto_panoramica_1913.jpg', 'varredura'), ('foto_panoramica_caracas.jpg', 'varredura'), ('foto_horizontal_roraima.jpg', 'inteira'),
    ('foto_vertical_salto_angel.jpg', 'inteira'), ('foto_quadrada_salto_angel.jpg', 'inteira'),
]
JS = """(()=>{const c=V2.cenas[0].el,j=c.querySelector('.jn'),r=j.getBoundingClientRect(),bs=j.style.backgroundSize.split(' ').map(parseFloat);
  return {w:r.width,h:r.height,left:r.left,right:r.right,bs}})()"""


def _baixa(tmp, nome, altura):
    im = Image.open(M / nome); r = altura / im.size[1]
    arq = tmp / ('baixa_' + nome); im.resize((round(im.size[0] * r), altura)).save(arq); return arq


@pytest.mark.parametrize('nome,modo', CASOS)
def test_foto_historica_real_por_formato(tmp_path, nome, modo):
    arq = M / nome
    with Image.open(arq) as im:
        wh = im.size
    rc = acervo_v2.recorte_conteudo(arq)
    assert acervo_v2.adequacao_historica(wh, rc)['modo'] == modo
    d = {'duration': 6, 'meta': {'motor': 'v2'}, 'captions': [], 'scenes': [{'comp': 'foto.historica', 'start': 0, 'end': 6,
         'params': {'img': str(arq), 'recorte': 'auto', 'ano': 1913, 'credito': 'teste', 'foco': [.5, .5]}}]}
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        for t in (1.0, 5.5):                          # momento 1 (inteira) e momento 2 (aproximação/varredura)
            pg.evaluate(f'seek({t})')
            j = pg.evaluate(JS)
            esc = j['bs'][0] / wh[0]                  # px de tela por px real
            assert esc <= acervo_v2.ESC_MAX + .02, (nome, t, esc)        # nunca amplia além de 1,5×
            assert abs((j['left'] + j['right']) / 2 - 540) <= 2, (nome, j)  # moldura centrada
        assert j['h'] >= acervo_v2.PROTAGONISTA_MIN, (nome, j)              # não é faixa fina
    assert not [a for a in fiscal_v2.avaliar(d, [{}], [])['achados'] if a['codigo'] == 'D12']


@pytest.mark.parametrize('nome', ['foto_panoramica_1913.jpg', 'foto_horizontal_roraima.jpg'])
def test_baixa_resolucao_bloqueia_como_protagonista(tmp_path, nome):
    arq = _baixa(tmp_path, nome, 91 if 'panoramica' in nome else 160)
    d = {'duration': 6, 'meta': {}, 'captions': [], 'scenes': [{'comp': 'foto.historica', 'start': 0, 'end': 6, 'params': {'img': str(arq), 'recorte': [0, 0, 1, 1]}}]}
    r = fiscal_v2.avaliar(d, [{}], [])
    assert any(a['codigo'] == 'D12' and a['gravidade'] == 'bloqueio' for a in r['achados']), r['achados']
