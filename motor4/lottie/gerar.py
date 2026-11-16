"""Gera animações Lottie ORIGINAIS do Coringa (sem asset de terceiros; licença: do próprio canal).
gota.json: gota de água cai e abre ondas — ícone de "gravidade move a água". 60 quadros a 30 fps, 512×512."""
import json, sys
from pathlib import Path

AZ = [0.247, 0.561, 0.847, 1]; AM = [1, 0.824, 0.122, 1]

def kf(t, v, ease=True):
    k = {'t': t, 's': v if isinstance(v, list) else [v]}
    if ease:
        k.update(i={'x': [0.4], 'y': [1]}, o={'x': [0.6], 'y': [0]})
    return k

def gota():
    # caminho de gota (bezier) centrado em (0,0), ~70 px de altura
    c = {'i': [[0, 0], [-19, 0], [0, 0]], 'o': [[0, 0], [19, 0], [0, 0]], 'v': [[0, -46], [0, 26], [0, -46]], 'c': True}
    c = {'i': [[0, 0], [16, -9], [0, 0], [-16, -9]], 'o': [[-16, -9], [0, 0], [16, -9], [0, 0]], 'v': [[0, -48], [26, 6], [0, 30], [-26, 6]], 'c': True}
    camada_gota = {'ty': 4, 'nm': 'gota', 'ip': 0, 'op': 60, 'st': 0, 'ks': {
        'o': {'a': 1, 'k': [kf(0, 0), kf(4, 100), kf(30, 100), kf(33, 0, False)]},
        'p': {'a': 1, 'k': [kf(0, [256, 60, 0]), kf(30, [256, 330, 0])]}, 'a': {'a': 0, 'k': [0, 0, 0]},
        's': {'a': 1, 'k': [kf(0, [80, 120, 100]), kf(30, [100, 100, 100])]}, 'r': {'a': 0, 'k': 0}},
        'shapes': [{'ty': 'sh', 'ks': {'a': 0, 'k': c}}, {'ty': 'fl', 'c': {'a': 0, 'k': AZ}, 'o': {'a': 0, 'k': 100}}]}
    def onda(atraso, cor):
        return {'ty': 4, 'nm': f'onda{atraso}', 'ip': 0, 'op': 60, 'st': 0, 'ks': {
            'o': {'a': 1, 'k': [kf(0, 0), kf(30 + atraso, 0), kf(32 + atraso, 100), kf(58, 0)]},
            'p': {'a': 0, 'k': [256, 360, 0]}, 'a': {'a': 0, 'k': [0, 0, 0]},
            's': {'a': 1, 'k': [kf(30 + atraso, [10, 4, 100]), kf(58, [100, 40, 100])]}, 'r': {'a': 0, 'k': 0}},
            'shapes': [{'ty': 'el', 'p': {'a': 0, 'k': [0, 0]}, 's': {'a': 0, 'k': [300, 300]}},
                       {'ty': 'st', 'c': {'a': 0, 'k': cor}, 'o': {'a': 0, 'k': 100}, 'w': {'a': 0, 'k': 10}}]}
    return {'v': '5.7.0', 'fr': 30, 'ip': 0, 'op': 60, 'w': 512, 'h': 512, 'nm': 'coringa-gota', 'ddd': 0, 'assets': [],
            'layers': [camada_gota, onda(0, AZ), onda(8, AM)], 'meta': {'g': 'Coringa Explica (original)', 'licenca': 'propria'}}

out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / 'gota.json')
out.write_text(json.dumps(gota()))
print(out)
