"""Regiões de interesse nas fotos do acervo — onde está o objeto que o plano precisa mostrar.

A direção (src/v2/diretor.py) só ancora uma ANOTAÇÃO (círculo, contorno, seta com rótulo) numa região que a visão
localizou com confiança. Sem isso, a região serve só para ENQUADRAR (câmera), nunca para afirmar "isto é X".

Fontes, em ordem:
  1. cache local (regioes.json), chave = sha256 da imagem + objeto pedido — resultado de uma chamada anterior;
  2. visão (Gemini, cota gratuita; `gemini.json_visao`) — devolve caixa 0–1000 e confiança;
  3. saliência local (OpenCV, sem custo) — SÓ para enquadramento: `ancoravel=False`.

Uso offline (sem chave): só cache e saliência. No GitHub: `python -m src.v2.regioes pedir <pedidos.json> <saida.json>`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROMPT = """Você localiza objetos numa FOTOGRAFIA para um editor de documentários. Não invente: se o objeto não aparece
com clareza, diga visivel=false. Para cada objeto pedido devolva a caixa que o contém, em coordenadas 0–1000
[ymin, xmin, ymax, xmax] da imagem inteira. Inclua também "foco", a caixa do assunto principal da foto.

Objetos pedidos: {objetos}

Responda SÓ JSON: {{"foco": {{"box_2d": [..], "descricao": "<curta>"}},
 "objetos": [{{"objeto": "<igual ao pedido>", "visivel": true|false, "box_2d": [..], "confianca": "alta|media|baixa",
               "descricao": "<o que exatamente está na caixa, curto>"}}]}}"""


def sha(arq: Path) -> str:
    return hashlib.sha256(Path(arq).read_bytes()).hexdigest()


def _caixa(b) -> list[float] | None:
    """[ymin,xmin,ymax,xmax] 0–1000 → [x, y, w, h] normalizado 0–1 (validado)."""
    try:
        y0, x0, y1, x1 = [max(0.0, min(1000.0, float(v))) / 1000 for v in b]
    except Exception:
        return None
    if x1 - x0 < .01 or y1 - y0 < .01:
        return None
    return [round(x0, 4), round(y0, 4), round(x1 - x0, 4), round(y1 - y0, 4)]


def ler_cache(arq: Path | None) -> dict:
    try:
        return json.loads(Path(arq).read_text(encoding='utf-8')) if arq and Path(arq).exists() else {}
    except Exception:
        return {}


def saliencia(img: Path) -> dict:
    """Caixa do que mais chama atenção (resíduo espectral + bordas). Só enquadra: nunca rotula."""
    import cv2
    import numpy as np
    im = cv2.imread(str(img))
    if im is None:
        return {}
    h, w = im.shape[:2]
    pq = cv2.resize(im, (256, max(32, int(256 * h / w))))
    ok, m = cv2.saliency.StaticSaliencySpectralResidual_create().computeSaliency(pq)
    if not ok:
        return {}
    m = cv2.GaussianBlur((m * 255).astype('uint8'), (0, 0), 6)
    _, b = cv2.threshold(m, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ys, xs = np.nonzero(b)
    if not len(xs):
        return {}
    ph, pw = m.shape
    x0, x1 = np.percentile(xs, [8, 92]) / pw
    y0, y1 = np.percentile(ys, [8, 92]) / ph
    return {'foco': {'caixa': [round(float(x0), 4), round(float(y0), 4), round(float(x1 - x0), 4), round(float(y1 - y0), 4)], 'origem': 'saliencia', 'ancoravel': False}}


def localizar(img: Path, objetos: list[str], cache: dict, chamar=None) -> dict:
    """{'foco': {caixa, origem, ancoravel}, 'objetos': {nome: {caixa, confianca, descricao, ancoravel}}}"""
    chave = sha(img)
    feito = cache.get(chave) or {}
    faltam = [o for o in objetos if o not in (feito.get('objetos') or {})]
    if (faltam or not feito.get('foco')) and chamar:
        try:
            r = chamar(PROMPT.format(objetos=json.dumps(faltam or objetos, ensure_ascii=False)), [Path(img).read_bytes()])
        except Exception as e:                          # visão fora: registra e segue sem âncora (sem nova tentativa)
            r = {'_erro': str(e)[:200]}
        if isinstance(r, dict) and not r.get('_erro'):
            f = _caixa(((r.get('foco') or {}).get('box_2d')) or [])
            if f:
                feito['foco'] = {'caixa': f, 'origem': 'visao', 'ancoravel': False, 'descricao': (r.get('foco') or {}).get('descricao', '')}
            obs = feito.setdefault('objetos', {})
            for o in r.get('objetos') or []:
                nome = o.get('objeto')
                if nome not in objetos:
                    continue
                cx = _caixa(o.get('box_2d') or []) if o.get('visivel') else None
                obs[nome] = {'caixa': cx, 'visivel': bool(cx), 'confianca': o.get('confianca') or 'baixa',
                             'descricao': str(o.get('descricao') or '')[:120], 'origem': 'visao',
                             'ancoravel': bool(cx) and o.get('confianca') in ('alta', 'media')}
        else:
            feito['erro_visao'] = (r or {}).get('_erro', 'resposta inválida')
        cache[chave] = feito
    if not feito.get('foco'):
        feito.update(saliencia(img))
    return feito


def _cli():
    if len(sys.argv) >= 4 and sys.argv[1] == 'pedir':
        from src import gemini
        pedidos = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
        saida = Path(sys.argv[3])
        cache = ler_cache(saida)
        for p in pedidos:
            img = Path(p['arquivo'])
            r = localizar(img, p['objetos'], cache, chamar=lambda pr, ims: gemini.json_visao(pr, ims, leve=False))
            print(p['id'], json.dumps(r, ensure_ascii=False)[:300])
            saida.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
        return
    print('uso: python -m src.v2.regioes pedir pedidos.json regioes.json')


if __name__ == '__main__':
    _cli()
