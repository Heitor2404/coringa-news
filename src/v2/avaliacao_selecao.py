"""Avaliação da seleção visual (V2.1) com conteúdo que NÃO foi usado no desenvolvimento.

Cada caso traz a fala, os dados disponíveis (params) e o que é ACEITÁVEL — decidido pelo que a cena precisa mostrar,
antes de rodar o seletor. Os casos negativos verificam que o sistema RECUSA (limitação/aviso) em vez de inventar.
Os resultados (inclusive as falhas) vão para o relatório; os casos não são ajustados para passar.

Uso: python -m src.v2.avaliacao_selecao [saida.json]
"""
from __future__ import annotations

import json
import sys

from src.v2 import capacidades

LIM = 'LIMITACAO'   # o aceitável é a recusa explícita (comp None + limitação)

# (id, domínio, fala, params disponíveis, contexto, aceitáveis)
CASOS = [
    # história
    ('h1', 'historia', 'Em 1453 Constantinopla caiu; em 1492 Colombo chegou à América.', {'eventos': [{'ano': 1453}, {'ano': 1492}]}, '', {'linha_tempo.historica'}),
    ('h2', 'historia', 'A muralha foi erguida como defesa e hoje virou atração turística.', {}, '', {LIM}),
    ('h3', 'historia', 'Napoleão nasceu na Córsega.', {}, '', {'foto.documental', 'mapa.localizacao', 'lower_third'}),
    # geografia
    ('g1', 'geografia', 'O Amazonas atravessa o continente do Peru até o Atlântico.', {'pontos': [{'lon': -73, 'lat': -4}, {'lon': -50, 'lat': 0}]}, '', {'mapa.rota'}),
    ('g2', 'geografia', 'O Chile é um país estreito e comprido.', {'pais': 'Chile'}, '', {'mapa.territorio'}),
    ('g3', 'geografia', 'O Everest fica no Nepal, na fronteira com a China.', {'pontos': [{'lon': 86.9, 'lat': 27.99}]}, '', {'mapa.localizacao'}),
    # biologia
    ('b1', 'biologia', 'Primeiro a lagarta forma o casulo, depois vira borboleta.', {'etapas': ['lagarta', 'casulo', 'borboleta']}, '', {'processo.etapas', 'comparacao.antes_depois'}),
    ('b2', 'biologia', 'Cerca de 60% do corpo humano é água.', {'pct': 60}, '', {'proporcao'}),
    ('b3', 'biologia', 'O coração bombeia cerca de 7 mil litros de sangue por dia.', {'valor': 7000, 'fonte': 'Wikipédia'}, '', {'numero.animado'}),
    # química
    ('q1', 'quimica', 'Quando o sódio encosta na água, ele explode.', {}, '', {LIM}),
    ('q2', 'quimica', 'O gelo derrete e vira água líquida.', {'etapas': ['gelo', 'água']}, '', {'processo.etapas', 'comparacao.antes_depois'}),
    ('q3', 'quimica', 'A água ferve a 100 graus ao nível do mar.', {}, '', {'foto.documental', 'numero.animado', 'destaque.palavras'}),
    # física
    ('f1', 'fisica', 'O elevador sobe porque o motor puxa o cabo.', {'forcas': [{'nome': 'Tração'}, {'nome': 'Peso'}]}, '', {'forcas.vetores'}),
    ('f2', 'fisica', 'Um navio de aço flutua porque o empuxo equilibra o peso.', {'forcas': [{'nome': 'Empuxo'}, {'nome': 'Peso'}]}, '', {'forcas.vetores'}),
    ('f3', 'fisica', 'A luz percorre 300 mil quilômetros por segundo.', {'valor': 300000, 'fonte': 'Wikipédia'}, '', {'numero.animado'}),
    # astronomia
    ('a1', 'astronomia', 'A Lua gira em torno da Terra a cada 27 dias.', {}, '', {'astronomia.orbita'}),
    ('a2', 'astronomia', 'A estrela mais próxima do Sol está a 4,2 anos-luz.', {'valor': 4.2, 'fonte': 'Wikipédia'}, '', {'numero.animado'}),
    ('a3', 'astronomia', 'Em 1908, uma explosão no ar derrubou árvores na Sibéria.', {'aneis': [{'raio_km': 26}]}, '', {'evento.impacto'}),
    # tecnologia
    ('t1', 'tecnologia', 'O chip tem 50 bilhões de transistores.', {'valor': 5e10, 'fonte': 'fabricante'}, '', {'numero.animado'}),
    ('t2', 'tecnologia', 'Primeiro o sinal sai da antena, depois chega ao satélite e então volta à Terra.', {'etapas': ['antena', 'satélite', 'Terra']}, '', {'processo.etapas', 'diagrama.explicativo'}),
    ('t3', 'tecnologia', 'Em 2007 veio o primeiro smartphone da marca; em 2010, o tablet.', {'eventos': [{'ano': 2007}, {'ano': 2010}]}, '', {'linha_tempo.historica'}),
    # fenômenos naturais
    ('n1', 'fenomenos', 'A maré sobe duas vezes por dia.', {}, '', {'mecanismo.nivel'}),
    ('n2', 'fenomenos', 'O vulcão entrou em erupção e cobriu a cidade de cinzas.', {'aneis': [{'raio_km': 10}]}, '', {'evento.impacto'}),
    ('n3', 'fenomenos', 'O rio transbordou e inundou a cidade.', {}, '', {'mecanismo.nivel'}),
]

# negativos: (id, o que testa, fala, params, contexto, aceitáveis, proibidos)
NEGATIVOS = [
    ('x1', 'mecanismo sem representação', 'A turbina gira e o gerador transforma o movimento em eletricidade.', {}, '', {LIM}, {'foto.documental'}),
    ('x2', 'comparação sem valores', 'O Brasil tem quatro vezes mais área que a Argentina.', {}, '', {'foto.documental'}, {'grafico.barras', 'comparacao.grandezas'}),
    ('x3', 'mapa sem coordenadas', 'O navio vai de Santos até Roterdã.', {}, '', {LIM}, {'mapa.rota'}),
    ('x4', 'mapa com coordenadas inválidas', 'O navio vai de Santos até Roterdã.', {'pontos': [{'lon': -46.3, 'lat': -23.9}, {'lon': 4.4, 'lat': 251.9}]}, '', {LIM}, {'mapa.rota'}),
    ('x5', 'número sem fonte', 'O lago tem 425 quilômetros quadrados e 20 milhões de litros.', {'valor': 425}, '', {'foto.documental'}, {'numero.animado'}),
    ('x6', 'série temporal com dados insuficientes', 'O preço cresceu desde 1990.', {'serie': [1, 2]}, '', {'foto.documental'}, {'grafico.temporal'}),
    ('x7', 'barras com valores não numéricos', 'O porto A movimenta mais do que o porto B, 3 vezes mais.', {'itens': [{'rotulo': 'A', 'valor': 'muito'}, {'rotulo': 'B', 'valor': 'pouco'}]}, '', {'foto.documental'}, {'grafico.barras'}),
    ('x8', 'eclusa fora de contexto de eclusa', 'O elevador sobe e leva as pessoas ao topo.', {}, '', {'forcas.vetores', LIM}, {'mecanismo.eclusa'}),
]

# RESERVA: escrito depois das correções do seletor e rodado UMA vez; o resultado é relatado como saiu (não se ajusta
# o seletor a estes casos — se mudar o seletor depois, este conjunto deixa de ser reserva e isso deve ser dito).
RESERVA = [
    ('r1', 'historia', 'Roma foi fundada em 753 a.C. e caiu em 476.', {'eventos': [{'ano': -753}, {'ano': 476}]}, '', {'linha_tempo.historica'}),
    ('r2', 'historia', 'Os vikings navegaram da Noruega até a Groenlândia.', {'pontos': [{'lon': 10.7, 'lat': 59.9}, {'lon': -45, 'lat': 61}]}, '', {'mapa.rota'}),
    ('r3', 'geografia', 'O deserto do Saara avança alguns quilômetros por ano.', {}, '', {LIM, 'grafico.temporal', 'foto.documental'}),
    ('r4', 'geografia', 'A Rússia faz fronteira com 14 países.', {'pais': 'Russia'}, '', {'mapa.territorio'}),
    ('r5', 'biologia', 'O sangue leva oxigênio dos pulmões até as células.', {}, '', {LIM, 'processo.etapas', 'diagrama.explicativo'}),
    ('r6', 'biologia', 'Uma baleia-azul pode ter 30 metros, o tamanho de três ônibus.', {'itens': [{'rotulo': 'Baleia', 'valor': 30}, {'rotulo': 'Ônibus', 'valor': 12}]}, '', {'comparacao.grandezas'}),
    ('r7', 'quimica', 'O ferro enferruja quando reage com o oxigênio e a água.', {'etapas': ['ferro', 'ferrugem']}, '', {'processo.etapas', 'comparacao.antes_depois', LIM}),
    ('r8', 'quimica', 'Cerca de 78% do ar é nitrogênio.', {'pct': 78}, '', {'proporcao'}),
    ('r9', 'fisica', 'Ao frear, o atrito transforma movimento em calor.', {'forcas': [{'nome': 'Atrito'}]}, '', {'forcas.vetores'}),
    ('r10', 'fisica', 'O pistão comprime o ar e o motor gira.', {'etapas': ['admissão', 'compressão', 'explosão', 'escape']}, '', {'processo.etapas', 'diagrama.explicativo'}),
    ('r11', 'astronomia', 'Júpiter leva 12 anos para dar uma volta ao redor do Sol.', {}, '', {'astronomia.orbita'}),
    ('r12', 'astronomia', 'A cratera de Chicxulub tem 180 quilômetros de diâmetro.', {'aneis': [{'raio_km': 90}]}, '', {'evento.impacto', 'numero.animado'}),
    ('r13', 'tecnologia', 'A fibra óptica leva a luz de um continente a outro pelo fundo do mar.', {}, '', {LIM, 'mapa.rota', 'diagrama.explicativo'}),
    ('r14', 'tecnologia', 'Hoje 5 bilhões de pessoas usam a internet.', {'valor': 5e9, 'fonte': 'UIT'}, '', {'numero.animado'}),
    ('r15', 'fenomenos', 'Na seca, o nível do reservatório baixou 12 metros.', {}, '', {'mecanismo.nivel'}),
    ('r16', 'fenomenos', 'O furacão se formou no Atlântico e seguiu até a Flórida.', {'pontos': [{'lon': -40, 'lat': 15}, {'lon': -81, 'lat': 27}]}, '', {'mapa.rota'}),
]


def _resultado(r: dict) -> str:
    return r['comp'] if r.get('comp') else LIM


def rodar() -> dict:
    out = {'positivos': [], 'negativos': []}
    for cid, dom, fala, params, ctx, ok in CASOS:
        r = capacidades.escolher({'fala': fala}, params, ctx)
        res = _resultado(r)
        out['positivos'].append({'id': cid, 'dominio': dom, 'fala': fala, 'escolha': res, 'aceitaveis': sorted(ok), 'passou': res in ok,
                                 'motivo': r.get('motivo') or r.get('limitacao'), 'aviso': r.get('aviso')})
    for cid, oque, fala, params, ctx, ok, proib in NEGATIVOS:
        r = capacidades.escolher({'fala': fala}, params, ctx)
        res = _resultado(r)
        out['negativos'].append({'id': cid, 'testa': oque, 'fala': fala, 'escolha': res, 'aceitaveis': sorted(ok), 'proibidos': sorted(proib),
                                 'passou': res in ok and res not in proib, 'motivo': r.get('motivo') or r.get('limitacao'), 'aviso': r.get('aviso')})
    out['reserva'] = []
    for cid, dom, fala, params, ctx, ok in RESERVA:
        r = capacidades.escolher({'fala': fala}, params, ctx)
        res = _resultado(r)
        out['reserva'].append({'id': cid, 'dominio': dom, 'fala': fala, 'escolha': res, 'aceitaveis': sorted(ok), 'passou': res in ok,
                               'motivo': r.get('motivo') or r.get('limitacao'), 'aviso': r.get('aviso')})
    for k in ('positivos', 'negativos', 'reserva'):
        out[f'{k}_passaram'] = sum(x['passou'] for x in out[k])
        out[f'{k}_total'] = len(out[k])
    por = {}
    for x in out['positivos']:
        d = por.setdefault(x['dominio'], [0, 0]); d[0] += x['passou']; d[1] += 1
    out['por_dominio'] = {k: f'{a}/{b}' for k, (a, b) in por.items()}
    return out


if __name__ == '__main__':
    r = rodar()
    for k in ('positivos', 'negativos', 'reserva'):
        for x in r[k]:
            print(('ok ' if x['passou'] else 'XX '), x['id'], x['escolha'].ljust(24), '|', x['fala'][:60], '|', (x['motivo'] or '')[:80])
    print('positivos', r['positivos_passaram'], '/', r['positivos_total'], ' negativos', r['negativos_passaram'], '/', r['negativos_total'],
          ' reserva', r['reserva_passaram'], '/', r['reserva_total'], r['por_dominio'])
    if len(sys.argv) > 1:
        json.dump(r, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
