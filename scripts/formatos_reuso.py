"""PROVA DE REUSO do motor ATLAS sem render completo, sem TTS e sem IA.

Para um plano novo (outra história): narração com tempos SINTÉTICOS (duração por sílaba aproximada, pausas na pontuação)
e voz sintética só para os portões de legenda (tom durante a fala, silêncio nas pausas) → ativos (acervo comprovado, sem
pesquisa nova) → preflight COMPLETO → quadros renderizados com TODAS as regras (plataformas, colisões, cartões,
legenda, atribuição, amostragem ampliada). Nada aqui é específico do episódio: se uma história precisar de código novo,
a prova falha. uso: python scripts/formatos_reuso.py <plano.json> <saida> [--sem-quadros]
"""
from __future__ import annotations

import json
import re
import sys
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.v4.formatos import produzir  # noqa: E402


def tempos_sinteticos(texto: str, ritmo: float = 1.0) -> tuple[list[dict], list[tuple[float, float]], float]:
    pal, falas, t, ini = [], [], .25, .25
    for m in re.finditer(r"([\wÀ-ÿº%]+)([^\wÀ-ÿº%]*)", texto):
        w, sep = m.group(1), m.group(2)
        d = (.12 + .055 * len(w)) / ritmo
        pal.append({'w': w.upper(), 's': round(t, 3), 'e': round(t + d, 3), 'hl': False})
        t += d
        pausa = .42 if re.search(r'[.!?]', sep) else .26 if re.search(r'[,:;]', sep) else 0
        if pausa:
            falas.append((ini, t)); t += pausa; ini = t
    if t > ini:
        falas.append((ini, t))
    return pal, falas, round(t + .5, 3)


def voz_sintetica(arq: Path, falas, dur: float, sr: int = 48000):
    x = np.zeros(int(dur * sr), dtype=np.float32)
    for a, b in falas:
        n = np.arange(int(a * sr), min(len(x), int(b * sr)))
        x[n] = .3 * np.sin(2 * np.pi * 180 * n / sr) * (1 + .3 * np.sin(2 * np.pi * 4 * n / sr))
    with wave.open(str(arq), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def main(plano: Path, saida: Path, quadros: bool = True) -> dict:
    pl = json.loads(plano.read_text(encoding='utf-8'))
    saida.mkdir(parents=True, exist_ok=True)
    pal, falas, dur = tempos_sinteticos(pl['narracao']['texto'])
    voz_sintetica(saida / 'voz.wav', falas, dur)
    (saida / 'narracao.json').write_text(json.dumps({'palavras': pal, 'duracao': dur, 'origem': 'SINTÉTICA (teste de reuso, sem TTS)'}, ensure_ascii=False))
    produzir.ativos(pl, saida)
    pf = produzir.preflight(pl, saida)
    falhas = [i for i in pf['itens'] if not i['ok']]
    res = {'plano': pl['video_id'], 'duracao_sintetica': dur, 'preflight': {'pronto': pf['pronto'], 'itens': len(pf['itens']), 'falhas': falhas}}
    if quadros and pf['pronto']:
        import importlib.util
        spec = importlib.util.spec_from_file_location('fv', RAIZ / 'scripts' / 'formatos_validar.py')
        fv = importlib.util.module_from_spec(spec); spec.loader.exec_module(fv)
        r = fv.main(saida, saida / 'quadros', 'auto', int(pl.get('styleframes', 6)))
        res['quadros'] = {'n': len(r['quadros']), 'problemas': [p for p in r['problemas'] if not p.get('aviso')], 'amostragem': r.get('amostragem')}
    (saida / 'reuso.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({'plano': res['plano'], 'preflight': res['preflight']['pronto'], 'falhas': [f['item'] + ' — ' + f['detalhe'] for f in falhas],
                      'quadros': (res.get('quadros') or {}).get('n'), 'problemas': [(p['t'], p['regra'], p['texto']) for p in (res.get('quadros') or {}).get('problemas', [])]},
                     ensure_ascii=False, indent=1))
    return res


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]), '--sem-quadros' not in sys.argv)
