"""E283 — legenda medida não cobre a filmagem integral (defeito observado em quadro renderizado).

Antes, o vídeo horizontal integral do caminho media-first usava a caixa DOC_MEDIA.integral (y 395–1150), enquanto a
faixa de legenda documental fica em y 1040–1150: a legenda caía sobre a parte inferior da evidência. Com legendas, o
vídeo integral passa a usar a mesma caixa das fotos integrais, que termina acima da faixa de legenda.
"""
import re
from pathlib import Path

TSX = Path(__file__).resolve().parents[1] / 'motor4/remotion/src/formatos/FilmeEditorial.tsx'


def _doc_media():
    code = TSX.read_text(encoding='utf8')
    m = re.search(r'const DOC_MEDIA=\{(.*?)\} as const;', code)
    boxes = dict((k, [int(v) for v in vals.split(',')]) for k, vals in re.findall(r'(\w+):\[([\d,]+)\]', m.group(1)))
    return code, boxes


def test_caixa_integral_legendada_termina_acima_da_legenda():
    code, b = _doc_media()
    assert b['photoIntegral'][3] <= b['subtitle'][1]
    assert b['subtitle'][3] <= b['source'][1] + 1
    # 16:9 ocupa a largura total dentro da caixa legendada (não encolhe a evidência horizontal).
    w, h = b['photoIntegral'][2] - b['photoIntegral'][0], b['photoIntegral'][3] - b['photoIntegral'][1]
    assert w == 1080 and h >= 1080 * 9 / 16
    assert "rectStyle(captioned?DOC_MEDIA.photoIntegral:DOC_MEDIA.integral)" in code
    assert 'captioned={subtitleMode}' in code
