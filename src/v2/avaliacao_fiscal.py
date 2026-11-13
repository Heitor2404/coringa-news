"""Mede o fiscal_v2 com defeitos INJETADOS (deve acusar) e as versões corretas dos mesmos casos (deve calar).

Cada caso = uma cena V2 mínima. Reporta verdadeiros positivos, falsos negativos (defeito não acusado) e falsos
positivos (acusou o caso correto). Não depende de render: as checagens geométricas (D1–D3) são medidas no render
das 33 composições, à parte.

Uso: python -m src.v2.avaliacao_fiscal [saida.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.v2 import fiscal_v2

RAIZ = Path(__file__).resolve().parents[2]
IMG_OK = str(RAIZ / 'tests' / 'img' / 'video_teste.mp4')
CANAL = [[-79.92, 9.4], [-79.55, 8.85]]
HORN_OK = [[-73.8, 40.3], [-65, 33], [-50, 15], [-33.5, -5], [-37, -20], [-47, -30], [-56, -40], [-63, -50], [-66, -57.2], [-70, -57.2], [-76.5, -52], [-76.5, -40], [-74, -25]]
RETA_NY_SF = [[-74.0, 40.7], [-122.4, 37.8]]
CAT = {'mapa.rota': {'limites': {'titulo': 36}}, 'abertura.pergunta': {'limites': {'pergunta': 60}}}


def _cena(comp, params, fala='', dur=4.0, **extra):
    return {'comp': comp, 'start': 0.0, 'end': dur, 'params': params, 'fala': fala, **extra}


def _dados(sc, caps=None):
    return {'duration': sc['end'], 'scenes': [sc], 'captions': caps or [], 'meta': {}}


# (id, código esperado, cena com defeito, cena correta, direcao defeito, direcao correta, legendas)
CASOS = [
    ('coord_fora', 'D7', _cena('mapa.localizacao', {'pontos': [{'nome': 'X', 'lon': -79.6, 'lat': 191.0}]}),
     _cena('mapa.localizacao', {'pontos': [{'nome': 'X', 'lon': -79.6, 'lat': 9.1}]}), {}, {}, None),
    ('coord_pais', 'D7', _cena('mapa.localizacao', {'pontos': [{'nome': 'Colón', 'lon': -3.7, 'lat': 40.4, 'pais': 'Panama'}]}),
     _cena('mapa.localizacao', {'pontos': [{'nome': 'Colón', 'lon': -79.9, 'lat': 9.36, 'pais': 'Panama'}]}), {}, {}, None),
    ('rota_terra', 'D8', _cena('mapa.rota', {'tipo': 'maritima', 'rota': RETA_NY_SF, 'pontos': []}),
     _cena('mapa.rota', {'tipo': 'maritima', 'rota': HORN_OK, 'pontos': []}), {}, {}, None),
    ('arquivo', 'D5', _cena('foto.documental', {'img': '/nao/existe/foto.jpg'}), _cena('foto.documental', {'img': IMG_OK}), {}, {}, None),
    ('limite', 'D6', _cena('mapa.rota', {'titulo': 'Um título que passa bem do limite de trinta e seis', 'tipo': 'canal', 'rota': CANAL}),
     _cena('mapa.rota', {'titulo': 'Do Caribe ao Pacífico', 'tipo': 'canal', 'rota': CANAL}), {}, {}, None),
    ('eclusa_sentido', 'S3', _cena('mecanismo.eclusa', {'sentido': 'subir'}, 'A câmara esvazia e o navio desce até o mar.'),
     _cena('mecanismo.eclusa', {'sentido': 'descer'}, 'A câmara esvazia e o navio desce até o mar.'), {}, {}, None),
    ('eclusa_sentido2', 'S3', _cena('mecanismo.eclusa', {'sentido': 'descer'}, 'A água enche a câmara e ergue o navio.'),
     _cena('mecanismo.eclusa', {'sentido': 'subir'}, 'A água enche a câmara e ergue o navio.'), {}, {}, None),
    ('critico', 'S1', _cena('foto.documental', {}, 'A turbina gira e o gerador produz energia.'),
     _cena('diagrama.explicativo', {'nos': [1, 2]}, 'A turbina gira e o gerador produz energia.'),
     {'comp': None, 'critica': True, 'limitacao': 'máquina sem composição viável'}, {'comp': 'diagrama.explicativo', 'critica': True}, None),
    ('numero', 'D9', _cena('numero.animado', {'valor': 5.3}), _cena('numero.animado', {'valor': 5.3}),
     {'bloqueio': ['US$ 5,3 mi sem contexto de leilão']}, {}, None),
    ('revelacao', 'D10', _cena('revelacao.surpresa', {'resposta': 'GRAVIDADE', 'virada': .3}), _cena('revelacao.surpresa', {'resposta': 'GRAVIDADE', 'virada': 2.0}),
     {}, {}, [{'start': 1.5, 'end': 2.5, 'words': [{'w': 'GRAVIDADE', 's': 2.0}]}]),
    ('plano', 'D11', _cena('foto.documental', {'img': IMG_OK}, dur=11), _cena('foto.documental', {'img': IMG_OK}, dur=5), {}, {}, None),
    ('dados', 'S4', _cena('foto.documental', {'img': IMG_OK}, 'O porto A movimenta 3 vezes mais.'), _cena('foto.documental', {'img': IMG_OK}),
     {'comp': 'foto.documental', 'aviso': 'dados insuficientes para grafico.barras'}, {'comp': 'foto.documental'}, None),
]


def rodar() -> dict:
    out = []
    for cid, cod, ruim, bom, d_ruim, d_bom, caps in CASOS:
        r1 = fiscal_v2.avaliar(_dados(ruim, caps), [d_ruim], [], catalogo=CAT)
        r2 = fiscal_v2.avaliar(_dados(bom, caps), [d_bom], [], catalogo=CAT)
        c1 = sorted({a['codigo'] for a in r1['achados'] if a['categoria'] != 'estetico'})
        c2 = sorted({a['codigo'] for a in r2['achados'] if a['categoria'] != 'estetico'})
        out.append({'id': cid, 'esperado': cod, 'acusou_no_defeito': c1, 'acusou_no_correto': c2,
                    'detectou': cod in c1, 'falso_positivo': bool(c2), 'evidencia': next((a['evidencia'] for a in r1['achados'] if a['codigo'] == cod), None)})
    return {'casos': out, 'detectados': sum(x['detectou'] for x in out), 'total': len(out),
            'falsos_positivos': sum(x['falso_positivo'] for x in out)}


if __name__ == '__main__':
    r = rodar()
    for x in r['casos']:
        print(('ok ' if x['detectou'] and not x['falso_positivo'] else 'XX '), x['id'].ljust(16), x['esperado'], 'defeito→', x['acusou_no_defeito'], 'correto→', x['acusou_no_correto'], '|', str(x['evidencia'])[:70])
    print('detectados', r['detectados'], '/', r['total'], ' falsos positivos', r['falsos_positivos'])
    if len(sys.argv) > 1:
        json.dump(r, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
