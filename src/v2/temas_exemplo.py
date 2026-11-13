"""Sequências curtas em 5 temas para testar REUTILIZAÇÃO da biblioteca fora do Panamá.

Dados SINTÉTICOS ou aproximados, marcados como tal (não vão ao ar; servem para ver a composição com outro conteúdo).
Cada sequência = cenas V2 encadeadas + legenda sintética, renderizada pela galeria e pelos testes de regressão.
"""
from src.v2.galeria import legendas_sinteticas

AVISO = 'EXEMPLO DE GALERIA · dados aproximados/sintéticos'


def _seq(cenas, falas):
    t, out, caps = 0.0, [], []
    for (comp, dur, params, extra), fala in zip(cenas, falas):
        sc = {'comp': comp, 'start': round(t, 2), 'end': round(t + dur, 2), 'params': params, 'fala': fala, **extra}
        out.append(sc)
        caps += legendas_sinteticas(fala, t, t + dur)
        t += dur
    return {'duration': round(t, 2), 'meta': {'titulo': AVISO, 'fontes': ['Wikipédia']}, 'scenes': out, 'captions': caps}


TEMAS = {
    'historia': ('História — a construção da Torre Eiffel', _seq([
        ('titulo.capitulo', 2.0, {'numero': '01', 'titulo': 'Paris, *1887*', 'subtitulo': 'uma torre para a Exposição Universal'}, {}),
        ('linha_tempo.historica', 5.5, {'titulo': 'Da obra ao *recorde*', 'eventos': [{'ano': 1887, 'texto': 'Começa a montagem'}, {'ano': 1889, 'texto': 'Inaugurada na Exposição'}, {'ano': 1930, 'texto': 'Perde o posto de mais alta'}]}, {}),
        ('comparacao.grandezas', 4.5, {'titulo': 'Quanto são *330 metros*?', 'unidade': 'm', 'destaque': 2, 'itens': [{'rotulo': 'Est. Liberdade', 'valor': 93, 'forma': 'torre'}, {'rotulo': 'Prédio 30 and.', 'valor': 90, 'forma': 'predio'}, {'rotulo': 'Torre Eiffel', 'valor': 330, 'forma': 'torre'}], 'fonte': 'Wikipédia'}, {'transicao': 'mascara'}),
    ], ['Paris, 1887.', 'A montagem começou em 1887 e a torre abriu em 1889.', 'Com 330 metros, ela foi a estrutura mais alta do mundo.'])),
    'biologia': ('Biologia — fotossíntese e cromatóforos', _seq([
        ('processo.etapas', 6.0, {'kicker': 'BIOLOGIA', 'titulo': 'Como a planta faz *açúcar*', 'etapas': [{'titulo': 'Luz', 'texto': 'A clorofila capta a luz', 'icone': 'sol'}, {'titulo': 'Água', 'texto': 'A água é quebrada', 'icone': 'agua'}, {'titulo': 'Glicose', 'texto': 'Vira açúcar e sobra oxigênio', 'icone': 'folha'}]}, {}),
        ('proporcao', 4.0, {'rotulo': 'Oxigênio do planeta (≈)', 'pct': 50, 'texto': 'vem do fitoplâncton nos oceanos', 'resto': 'plantas em terra', 'fonte': 'Wikipédia (estimativa)'}, {'transicao': 'mascara'}),
        ('destaque.palavras', 3.0, {'frase': 'A pele do polvo tem *células de cor*.'}, {'fundo': {'img': '@pele', 'de': [.5, .5, 1], 'para': [.45, .45, 1.1]}}),
    ], ['A planta capta luz, quebra a água e produz açúcar.', 'Cerca de metade do oxigênio vem do fitoplâncton.', 'A pele do polvo tem células de cor.'])),
    'fisica': ('Física — por que o navio flutua', _seq([
        ('forcas.vetores', 5.0, {'titulo': 'Por que o aço *flutua*?', 'objeto': 'navio', 'meio': 'agua', 'forcas': [{'nome': 'Peso', 'angulo': -90, 'intensidade': .8, 'cor': '#FF4D3D'}, {'nome': 'Empuxo', 'angulo': 90, 'intensidade': .8, 'cor': '#3FD0E0'}], 'resultado': 'Empuxo = Peso → flutua'}, {}),
        ('mecanismo.nivel', 4.5, {'titulo': 'A água sobe *quando o navio entra*', 'de': 3, 'ate': 4.2, 'max': 6, 'unidade': 'm', 'objeto': 'navio', 'flutua': True, 'entrada': 'cima', 'rotulo': 'DESLOCAMENTO'}, {'transicao': 'mascara'}),
        ('revelacao.surpresa', 3.5, {'pergunta': 'Quem segura o navio?', 'resposta': 'A ÁGUA', 'detalhe': 'Ele desloca o próprio peso em água.', 'virada': 1.2, 'cor': 'verde'}, {}),
    ], ['O peso puxa o navio para baixo e o empuxo empurra para cima.', 'O navio empurra a água e o nível sobe.', 'Quem segura o navio é a água.'])),
    'astronomia': ('Astronomia — o ano e o impacto', _seq([
        ('astronomia.orbita', 5.0, {'titulo': 'Um ano é *uma volta*', 'central': {'nome': 'Sol', 'cor': '#FFD21F', 'raio': 64}, 'orbitante': {'nome': 'Terra', 'cor': '#5B9BFF', 'raio': 22}, 'excentricidade': .25, 'periodo': '365,25 dias', 'distancia': '150 milhões de km', 'fora_de_escala': True}, {}),
        ('evento.impacto', 4.5, {'titulo': 'Tunguska, *1908*', 'centro': 'EXPLOSÃO', 'escala_km': 40, 'aneis': [{'raio_km': 26, 'rotulo': 'árvores derrubadas (≈)'}]}, {'transicao': 'flash'}),
    ], ['A Terra leva um ano para dar uma volta no Sol.', 'Em 1908, uma explosão no ar derrubou árvores num raio de dezenas de quilômetros.'])),
    'geografia': ('Geografia — o Nilo', _seq([
        ('mapa.territorio', 4.5, {'pais': 'Egypt', 'kicker': 'TERRITÓRIO', 'titulo': 'Um país *ao longo de um rio*', 'dado': '95% da população perto do Nilo (≈)', 'folga': .2, 'max_paises': 2}, {}),
        ('mapa.rota', 5.0, {'kicker': 'TRAJETO', 'titulo': 'O Nilo até o *Mediterrâneo*', 'pontos': [{'nome': 'Cartum', 'lon': 32.53, 'lat': 15.6}, {'nome': 'Cairo', 'lon': 31.24, 'lat': 30.04}], 'rota': [[32.53, 15.6], [33.0, 17.5], [33.9, 18.5], [32.3, 19.6], [31.5, 21.5], [32.9, 24.1], [32.6, 25.7], [31.2, 27.2], [31.24, 30.04]], 'folga': .25}, {'transicao': 'zoom'}),
    ], ['No Egito, quase todo mundo vive perto do Nilo.', 'O rio corre de Cartum até o Cairo.'])),
    'mapas': ('Mapas — rotas, deslocamento histórico e comparação de distâncias', _seq([
        ('mapa.rota', 5.0, {'kicker': 'VOO DIRETO', 'titulo': 'De *Lisboa* ao *Rio*', 'tipo': 'aerea', 'pontos': [{'nome': 'Lisboa', 'lon': -9.14, 'lat': 38.72}, {'nome': 'Rio de Janeiro', 'lon': -43.2, 'lat': -22.9}], 'folga': .12}, {}),
        ('mapa.rota', 5.5, {'kicker': 'HISTÓRIA · 1500', 'titulo': 'A rota de *Cabral* (aproximada)', 'tipo': 'maritima', 'pontos': [{'nome': 'Lisboa', 'lon': -9.14, 'lat': 38.72}, {'nome': 'Porto Seguro', 'lon': -39.06, 'lat': -16.45}],
                             'rota': [[-9.25, 38.6], [-13, 33], [-16, 28], [-22.5, 16.5], [-26, 6], [-30, -4], [-35, -12], [-39.0, -16.4]], 'folga': .12, 'nota': 'traçado aproximado · ilustrativo'}, {'transicao': 'zoom'}),
        ('mapa.rota', 7.0, {'kicker': 'NOVA YORK → SÃO FRANCISCO', 'titulo': 'O canal *corta* a viagem', 'tipo': 'maritima', 'pontos': [{'nome': 'Nova York', 'lon': -74.0, 'lat': 40.7}, {'nome': 'São Francisco', 'lon': -122.42, 'lat': 37.77}],
                             'rotas': [{'nome': 'Pelo canal', 'rota': [[-73.8, 40.3], [-72.5, 37], [-75.5, 30], [-78.0, 27.3], [-79.5, 26.0], [-79.9, 24.6], [-82, 23.9], [-84.8, 22.6], [-86.0, 21.0], [-84.0, 16.5], [-80.5, 11.5], [-79.92, 9.4], [-79.55, 8.85], [-79.4, 8.0], [-80.0, 6.2], [-84.5, 6.5], [-88.5, 10.5], [-96, 13.8], [-103, 17], [-106.5, 20], [-110.3, 21.8], [-113.5, 24.5], [-116.5, 28.5], [-119, 32], [-121, 34.3], [-122.6, 37.7]], 'distancia_km': 9500},
                                       {'nome': 'Cabo Horn', 'rota': [[-73.8, 40.3], [-65, 33], [-50, 15], [-33.5, -5], [-37, -20], [-47, -30], [-56, -40], [-63, -50], [-66, -57.2], [-70, -57.2], [-76.5, -52], [-76.5, -40], [-74, -25], [-78, -15], [-84, -5], [-84, 3], [-88.5, 10.5], [-96, 13.8], [-103, 17], [-106.5, 20], [-110.3, 21.8], [-113.5, 24.5], [-116.5, 28.5], [-119, 32], [-121, 34.3], [-122.6, 37.7]], 'distancia_km': 22500}],
                             'folga': .06, 'nota': 'distâncias: Wikipédia (Panama Canal); traçado ilustrativo'}, {'transicao': 'zoom'}),
    ], ['Um voo direto liga Lisboa ao Rio.', 'Em 1500, a frota de Cabral desceu o Atlântico até a Bahia.', 'Pelo canal são nove mil e quinhentos quilômetros; pelo Cabo Horn, vinte e dois mil e quinhentos.'])),
}
