"""V2.5 — MATRIZ MULTINICHO offline: o fluxo real, sem IA paga, sem rede, com acervo local.

Cada cenário é um mini-roteiro (1–3 acontecimentos) + acervo (imagens locais com o catálogo `mostra`, corretas ou
ENGANOSAS) + fatos. Passa por: pré-validação (IA indisponível) → plano visual (IA indisponível) → preparo → prévia
renderizada → cobertura → montagem → fiscal. Resultado: 'aprova' | 'revisao' | 'bloqueia' (+ etapa e motivo).

Dois conjuntos SEPARADOS:
  DEV  — assuntos usados durante a correção (lagartixa, magma, Ever Given, Panamá, café, Marie Curie…);
  VAL  — assuntos que NÃO foram usados no desenvolvimento, escritos com a expectativa ANTES de rodar. Falha em VAL é
         reportada como está (não se ajusta código para um assunto de VAL).
Uso: python -m src.v2.matriz <pasta> [dev|val|todos]
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

from src.v2 import cobertura, fiscal_v2, montagem, planejamento, preparo, prevalidacao, previa

RAIZ = Path(__file__).resolve().parents[2]
IM = {'b': str(RAIZ / 'tests/img/fundo_b.jpg'), 'c': str(RAIZ / 'tests/img/fundo_c.jpg'), 'd': str(RAIZ / 'tests/img/fundo_d.jpg'),
      'eg5': str(RAIZ / 'tests/piloto_ever_given/img/a5-g.jpg'), 'eg1': str(RAIZ / 'tests/piloto_ever_given/img/a1-g.jpg'),
      'faltando': str(RAIZ / 'tests/img/nao_existe.jpg')}
VID = str(RAIZ / 'tests/midia/video_horizontal_navio.mp4')
P = lambda *a: [{'nome': n, 'lon': lo, 'lat': la} for n, lo, la in a]


def esq(objetos, estados):
    return {'objetos': objetos, 'estados': estados}


def _ac(eid, tipo, sujeito, mostrar, dados=None, ini='', fim='', crit=True, **kw):
    return {'id': eid, 'tipo': tipo, 'sujeito': sujeito, 'mostrar': mostrar, 'dados': dados or {}, 'estado_inicial': ini, 'estado_final': fim,
            'importancia': 'critica' if crit else 'apoio', 'obrigatoria': crit, 'fonte': 'Wikipédia', **kw}


def C(fala, ac, foto=None, tipo='historia', **kw):
    return {'tipo': tipo, 'fala': fala, 'acontecimento': ac, 'foto': foto, **kw}


def A(i, img, mostra, ano=None, titulo=''):
    return {'id': i, 'arq': IM.get(img, img), 'mostra': mostra, 'titulo': titulo or mostra[:40], 'ano': ano, 'tipo_img': 'foto', 'credito': f'Teste {i} (CC BY 4.0)'}


# esquemas genéricos
ESQ_VULCAO = esq([{'id': 'c', 'forma': 'superficie', 'rotulo': 'CROSTA', 'y': .3, 'w': 1}, {'id': 'm', 'forma': 'corpo', 'rotulo': 'MAGMA', 'y': .8, 'w': .4, 'h': .2}],
                 [{'rotulo': 'MAGMA ACUMULA'}, {'rotulo': 'PRESSÃO EMPURRA A CROSTA', 'objetos': {'m': {'dy': -.3, 'escala': 1.2}},
                                                'relacoes': [{'de': 'm', 'para': 'c', 'tipo': 'empurra', 'forca': 1, 'rotulo': 'PRESSÃO'}]}])
ESQ_OSMOSE = esq([{'id': 'mb', 'forma': 'superficie', 'rotulo': 'MEMBRANA', 'x': .5, 'y': .5, 'w': .06, 'h': .9},
                  {'id': 'ag', 'forma': 'particulas', 'rotulo': 'ÁGUA', 'x': .25, 'y': .5, 'w': .3, 'n': 6}],
                 [{'rotulo': 'MAIS ÁGUA À ESQUERDA'}, {'rotulo': 'A ÁGUA ATRAVESSA A MEMBRANA', 'objetos': {'ag': {'dx': .45}}}])
ESQ_ESTRAGADO = esq([{'id': 'a', 'forma': 'corpo', 'rotulo': 'CÉLULA'}, {'id': 'b', 'forma': 'superficie', 'rotulo': 'MEMBRANA'}],
                    [{'rotulo': 'ANTES'}, {'rotulo': 'DEPOIS'}])                       # dois estados iguais: nada muda
ESQ_SEM_ROTULO_DO_ASSUNTO = esq([{'id': 'a', 'forma': 'corpo', 'rotulo': 'BLOCO'}, {'id': 'b', 'forma': 'superficie', 'rotulo': 'BASE'}],
                                [{'rotulo': 'INÍCIO'}, {'rotulo': 'FIM', 'objetos': {'a': {'dy': -.3}}}])

FATOS = ('FATOS:\n- O magma acumulado aumenta a pressão sob a crosta. (Wikipédia)\n- A osmose leva a água através da membrana. (Wikipédia)\n'
         '- O Ever Given encalhou no Canal de Suez em 2021. (Wikipédia)\n- A população mundial passou de 2,5 bilhões em 1950 para 7,8 bilhões em 2020. (ONU)\n'
         '- O Brasil produz 3,7 milhões de toneladas de café. (FAO)\n- Marie Curie ganhou o Nobel de Física em 1903 e o de Química em 1911. (Wikipédia)\n'
         '- A Terra leva 365 dias para orbitar o Sol. (NASA)\n- O pedal gira a coroa, a corrente gira a roda. (Wikipédia)\n'
         '- A Muralha da China tem mais de 21 mil km. (Wikipédia)\n- As baleias-jubarte migram até 8 mil km por ano. (Wikipédia)\n'
         '- O Concorde voava a 2.180 km/h. (Wikipédia)\n- Em 1986 o reator 4 de Chernobyl explodiu. (Wikipédia)\n'
         '- A ponte Golden Gate tem vão de 1.280 m. (Wikipédia)\n- Alan Turing propôs a máquina de Turing em 1936. (Wikipédia)\n'
         '- O Monte Everest tem 8.849 m. (Wikipédia)\n- 71% da superfície da Terra é coberta por água. (NASA)\n'
         '- O Saara ocupa cerca de 9 milhões de km². (Wikipédia)\n- Júpiter leva 12 anos para orbitar o Sol. (NASA)\n'
         '- Em 1969 a Apollo 11 pousou na Lua. (NASA)\n- O cometa Halley passa a cada 76 anos. (NASA)\n')

# (id, grupo, conjunto, descrição, cenas, acervo, esperado ∈ {'aprova','revisao','bloqueia'} ou conjunto)
CENARIOS = [
    # ── 1. ciência microscópica / mecanismos invisíveis ──
    ('c1', 'ciencia', 'dev', 'mecanismo com esquema válido', [C('A pressão do magma empurra a crosta.', _ac('e1', 'mecanismo', 'magma', 'magma empurrando a crosta', {'esquema': ESQ_VULCAO}, 'magma acumula', 'crosta empurrada pela pressão'))], [], {'aprova'}),
    ('c2', 'ciencia', 'dev', 'mecanismo crítico só com frases (cartão)', [C('O magma sobe.', _ac('e1', 'mecanismo', 'magma', 'magma subindo', {'etapas': ['o magma acumula embaixo da crosta por anos', 'a pressão aumenta até romper a rocha']}, 'magma', 'rocha rompida'))], [], {'bloqueia'}),
    ('c3', 'ciencia', 'dev', 'mecanismo com seta sem sentido físico', [C('Forças moleculares seguram tudo.', _ac('e1', 'mecanismo', 'moléculas', 'forças', {'forcas': ['forças eletromagnéticas entre partículas']}))], [], {'bloqueia'}),
    ('c4', 'ciencia', 'dev', 'esquema estragado (estados iguais)', [C('A célula muda.', _ac('e1', 'mecanismo', 'célula', 'célula', {'esquema': ESQ_ESTRAGADO}, 'antes', 'depois'))], [], {'bloqueia'}),
    ('c5', 'ciencia', 'dev', 'mecanismo sem dados e sem foto', [C('A enzima corta a proteína.', _ac('e1', 'mecanismo', 'enzima', 'enzima cortando proteína'))], [], {'bloqueia'}),
    ('c6', 'ciencia', 'val', 'osmose com esquema', [C('Pela osmose, a água atravessa a membrana.', _ac('e1', 'processo', 'água', 'água atravessando a membrana', {'esquema': ESQ_OSMOSE}, 'mais água de um lado', 'água atravessou a membrana'))], [], {'aprova'}),
    ('c7', 'ciencia', 'val', 'esquema que desenha outra coisa (cobertura zero)', [C('O DNA se duplica.', _ac('e1', 'mecanismo', 'DNA', 'fita de DNA se abrindo', {'esquema': ESQ_SEM_ROTULO_DO_ASSUNTO}, 'dupla hélice fechada', 'duas fitas novas'))], [], {'bloqueia'}),
    ('c8', 'ciencia', 'val', 'foto microscópica enganosa como prova de mecanismo', [C('O vírus entra na célula.', _ac('e1', 'mecanismo', 'vírus', 'vírus entrando na célula', ini='vírus fora', fim='vírus dentro da célula'), foto='a1')],
     [A('a1', 'b', 'Paisagem de montanha com neve ao entardecer')], {'bloqueia'}),
    # ── 2. natureza e comportamento animal ──
    ('n1', 'natureza', 'dev', 'animal: foto real que mostra o comportamento', [C('A lagartixa caça no teto.', _ac('e1', 'ambiente', 'lagartixa', 'lagartixa no teto caçando', crit=False), foto='a1')],
     [A('a1', 'c', 'Lagartixa no teto caçando um inseto à noite')], {'aprova'}),
    ('n2', 'natureza', 'val', 'migração: rota marítima válida', [C('As jubartes migram da Antártida ao Brasil.', _ac('e1', 'deslocamento', 'baleias-jubarte', 'rota de migração', {'pontos': P(('Península Antártica', -60, -64), ('Abrolhos', -38.7, -17.9)), 'tipo': 'maritima'}))], [], {'aprova'}),
    ('n3', 'natureza', 'val', 'migração com rota sem coordenadas', [C('As jubartes migram da Antártida ao Brasil.', _ac('e1', 'deslocamento', 'baleias-jubarte', 'rota de migração', {'pontos': [{'nome': 'Antártida'}, {'nome': 'Brasil'}]}))], [], {'bloqueia'}),
    ('n4', 'natureza', 'val', 'animal com foto de OUTRO animal', [C('O polvo muda de cor.', _ac('e1', 'transformacao', 'polvo', 'polvo mudando de cor', ini='polvo marrom', fim='polvo branco'), foto='a1')],
     [A('a1', 'c', 'Cachorro dormindo em um sofá')], {'bloqueia'}),
    ('n5', 'natureza', 'val', 'animal de apoio, sem foto', [C('As abelhas vivem em colmeias.', _ac('e1', 'ambiente', 'abelhas', 'colmeia', crit=False))], [], {'aprova', 'revisao'}),
    # ── 3. história e acontecimentos reais ──
    ('h1', 'historia', 'dev', 'evento histórico com linha do tempo', [C('Começou em 1904 e abriu em 1914.', _ac('e1', 'sequencia_historica', 'canal', 'obras do canal', {'eventos': [{'ano': 1904, 'texto': 'Obras começam'}, {'ano': 1914, 'texto': 'Canal aberto'}]}, crit=False))], [], {'aprova'}),
    ('h2', 'historia', 'val', 'acidente histórico com foto de arquivo correta', [C('Em 1986, o reator de Chernobyl explodiu.', _ac('e1', 'evento_historico', 'reator 4 de Chernobyl', 'reator destruído', {'ano': 1986}, 'reator funcionando', 'reator destruído', quando='1986'), foto='a1')],
     [A('a1', 'eg1', 'Reator 4 de Chernobyl destruído após a explosão de 1986', 1986)], {'aprova', 'revisao'}),
    ('h3', 'historia', 'val', 'acidente histórico com foto anacrônica', [C('Em 1986, o reator de Chernobyl explodiu.', _ac('e1', 'evento_historico', 'reator 4 de Chernobyl', 'reator destruído', {'ano': 1986}, 'reator funcionando', 'reator destruído', quando='1986'), foto='a1')],
     [A('a1', 'eg1', 'Usina nuclear moderna em funcionamento, 2019', 2019)], {'bloqueia', 'revisao'}),
    ('h4', 'historia', 'val', 'evento histórico sem nenhuma mídia', [C('Em 1666, Londres pegou fogo.', _ac('e1', 'evento_historico', 'Grande Incêndio de Londres', 'cidade em chamas', quando='1666'))], [], {'bloqueia'}),
    ('h5', 'historia', 'val', 'citação literal com autor', [C('"Eu vim, vi e venci", escreveu César.', _ac('e1', 'citacao', 'Júlio César', 'frase', {'texto': 'Vim, vi e venci.', 'autor': 'Júlio César'}, crit=False))], [], {'aprova'}),
    # ── 4. geografia, territórios e deslocamentos ──
    ('g1', 'geografia', 'dev', 'rota marítima válida', [C('O navio saiu de Xangai para Roterdã.', _ac('e1', 'deslocamento', 'navio', 'rota', {'pontos': P(('Xangai', 121.5, 31.2), ('Roterdã', 4.5, 51.9)), 'tipo': 'maritima'}))], [], {'aprova'}),
    ('g2', 'geografia', 'dev', 'território válido', [C('O Chile é longo e estreito.', _ac('e1', 'territorio', 'Chile', 'Chile', {'pais': 'Chile'}, crit=False))], [], {'aprova'}),
    ('g3', 'geografia', 'val', 'território inexistente', [C('Esse país é enorme.', _ac('e1', 'territorio', 'país', 'país', {'pais': 'Terra Média'}, crit=False))], [], {'aprova', 'revisao'}),
    ('g4', 'geografia', 'val', 'localização com coordenada inválida', [C('O Saara fica no norte da África.', _ac('e1', 'localizacao', 'Saara', 'Saara', {'pontos': [{'nome': 'Saara', 'lon': 300, 'lat': 23}]}, crit=False))], [], {'aprova', 'revisao'}),
    ('g5', 'geografia', 'val', 'localização válida', [C('O Saara fica no norte da África.', _ac('e1', 'localizacao', 'Saara', 'Saara', {'pontos': P(('Saara', 13, 23))}, crit=False))], [], {'aprova'}),
    # ── 5. espaço e astronomia ──
    ('e1', 'espaco', 'dev', 'órbita com dado parcial', [C('A Terra leva um ano para dar a volta no Sol.', _ac('e1', 'orbita', 'Terra', 'Terra orbitando o Sol', {'central': {'nome': 'Sol'}, 'orbitante': {'nome': 'Terra'}, 'periodo': '365 dias'}, 'Terra num ponto da órbita', 'volta completa'))], [], {'aprova'}),
    ('e2', 'espaco', 'val', 'órbita de Júpiter (só nomes em texto)', [C('Júpiter leva 12 anos para dar a volta no Sol.', _ac('e1', 'orbita', 'Júpiter', 'Júpiter orbitando', {'central': 'Sol', 'orbitante': 'Júpiter', 'periodo': '12 anos'}, 'Júpiter num ponto', 'volta completa'))], [], {'aprova'}),
    ('e3', 'espaco', 'val', 'pouso na Lua com foto correta', [C('Em 1969, a Apollo 11 pousou na Lua.', _ac('e1', 'evento_historico', 'Apollo 11', 'módulo lunar na Lua', {'ano': 1969}, 'nave em órbita', 'módulo pousado na Lua', quando='1969'), foto='a1')],
     [A('a1', 'd', 'Módulo lunar da Apollo 11 pousado na superfície da Lua, 1969', 1969)], {'aprova', 'revisao'}),
    ('e4', 'espaco', 'val', 'impacto sem raio', [C('O asteroide abriu uma cratera enorme.', _ac('e1', 'impacto', 'asteroide', 'cratera', {'aneis': ['uma cratera muito grande']}))], [], {'bloqueia'}),
    ('e5', 'espaco', 'val', 'impacto com raios', [C('A explosão derrubou árvores num raio de 30 km.', _ac('e1', 'impacto', 'explosão de Tunguska', 'árvores derrubadas', {'aneis': [{'raio_km': 30, 'rotulo': 'árvores derrubadas'}], 'centro': 'Tunguska'}, 'floresta de pé', 'árvores derrubadas'))], [], {'aprova'}),
    # ── 6. engenharia e máquinas ──
    ('m1', 'engenharia', 'dev', 'máquina com diagrama de rótulos curtos', [C('O pedal gira a coroa e a corrente gira a roda.', _ac('e1', 'mecanismo', 'bicicleta', 'transmissão', {'nos': [{'id': 'p', 'rotulo': 'Pedal'}, {'id': 'c', 'rotulo': 'Coroa'}, {'id': 'r', 'rotulo': 'Roda'}]}, 'pedal parado', 'roda girando'))], [], {'aprova', 'revisao'}),
    ('m2', 'engenharia', 'dev', 'nível de água com números', [C('O rio subiu de 2 para 9 metros.', _ac('e1', 'nivel', 'rio', 'rio subindo', {'de': 2, 'ate': 9, 'unidade': 'm'}, 'rio a 2 metros', 'rio a 9 metros'))], [], {'aprova'}),
    ('m3', 'engenharia', 'val', 'nível com palavras no lugar de números', [C('A represa encheu.', _ac('e1', 'nivel', 'represa', 'represa enchendo', {'de': 'vazia', 'ate': 'cheia'}, 'represa vazia', 'represa cheia'))], [], {'bloqueia'}),
    ('m4', 'engenharia', 'val', 'avião: forças com sentido', [C('A sustentação vence o peso e o avião sobe.', _ac('e1', 'movimento', 'avião', 'avião subindo', {'forcas': [{'nome': 'Sustentação', 'intensidade': 1}, {'nome': 'Peso', 'intensidade': .6}]}, 'avião na pista', 'avião subindo'))], [], {'aprova'}),
    ('m5', 'engenharia', 'val', 'ponte: escala com itens sem valor', [C('A ponte é maior que o prédio.', _ac('e1', 'escala', 'ponte', 'comparação', {'itens': ['ponte comprida', 'prédio alto']}))], [], {'bloqueia'}),
    ('m6', 'engenharia', 'val', 'ponte: escala válida', [C('O vão da Golden Gate tem 1.280 metros, mais que o Everest de altura relativa.', _ac('e1', 'escala', 'Golden Gate', 'comparação', {'itens': [{'rotulo': 'Golden Gate', 'valor': 1280, 'forma': 'barra'}, {'rotulo': 'Torre Eiffel', 'valor': 330, 'forma': 'torre'}], 'unidade': 'm', 'fonte': 'Wikipédia'}))], [], {'aprova'}),
    # ── 7. estatísticas, números e comparações ──
    ('s1', 'numeros', 'dev', 'série temporal válida', [C('A população cresceu de 1950 a 2020.', _ac('e1', 'evolucao_temporal', 'população', 'crescimento', {'serie': [[1950, 2.5], [1970, 3.7], [1990, 5.3], [2020, 7.8]], 'unidade': 'bi', 'fonte': 'ONU'}, crit=False))], [], {'aprova'}),
    ('s2', 'numeros', 'dev', 'barras sem valores', [C('O Brasil produz mais café.', _ac('e1', 'comparacao', 'café', 'produção', {'itens': [{'rotulo': 'Brasil'}, {'rotulo': 'Colômbia'}]}, crit=True))], [], {'bloqueia'}),
    ('s3', 'numeros', 'val', 'proporção válida', [C('71% da Terra é coberta por água.', _ac('e1', 'proporcao', 'água', 'proporção', {'pct': 71, 'rotulo': 'Superfície com água', 'fonte': 'NASA'}, crit=False))], [], {'aprova'}),
    ('s4', 'numeros', 'val', 'proporção com texto no lugar do número (crítica)', [C('Quase toda a Terra é água.', _ac('e1', 'proporcao', 'água', 'proporção', {'pct': 'a maior parte'}, crit=True))], [], {'bloqueia'}),
    ('s5', 'numeros', 'val', 'série com só 2 pontos (crítica)', [C('O Concorde ficou mais rápido.', _ac('e1', 'evolucao_temporal', 'Concorde', 'velocidade', {'serie': [[1969, 1000], [1976, 2180]]}, crit=True))], [], {'bloqueia'}),
    ('s6', 'numeros', 'val', 'número validado com fonte', [C('O Everest tem 8.849 metros.', _ac('e1', 'numero', 'Everest', 'altura', {'valor': 8849, 'unidade': 'm', 'fonte': 'Wikipédia'}, crit=False))], [], {'aprova'}),
    # ── 8. biografias e pessoas ──
    ('p1', 'pessoas', 'dev', 'pessoa com foto correta e nome', [C('Marie Curie ganhou dois Nobel.', _ac('e1', 'pessoa', 'Marie Curie', 'retrato de Marie Curie', {'nome': 'Marie Curie', 'descricao': 'física e química'}, crit=False), foto='a1')],
     [A('a1', 'd', 'Retrato de Marie Curie em seu laboratório', 1911)], {'aprova'}),
    ('p2', 'pessoas', 'val', 'pessoa com foto de outra pessoa', [C('Alan Turing criou a máquina de Turing.', _ac('e1', 'pessoa', 'Alan Turing', 'retrato de Alan Turing', {'nome': 'Alan Turing'}, crit=True), foto='a1')],
     [A('a1', 'd', 'Retrato de Albert Einstein sorrindo', 1950)], {'bloqueia', 'revisao'}),
    ('p3', 'pessoas', 'val', 'pessoa com foto correta, mídia ausente no disco', [C('Alan Turing criou a máquina de Turing.', _ac('e1', 'pessoa', 'Alan Turing', 'retrato de Alan Turing', {'nome': 'Alan Turing'}, crit=True), foto='a1')],
     [A('a1', 'faltando', 'Retrato de Alan Turing', 1936)], {'bloqueia'}),
    ('p4', 'pessoas', 'val', 'biografia: linha do tempo + pessoa', [C('Turing nasceu em 1912 e propôs sua máquina em 1936.', _ac('e1', 'sequencia_historica', 'Alan Turing', 'vida', {'eventos': [{'ano': 1912, 'texto': 'Nasce em Londres'}, {'ano': 1936, 'texto': 'Máquina de Turing'}]}, crit=False))], [], {'aprova'}),
    # ── mistos (vários acontecimentos no mesmo vídeo) ──
    ('x1', 'misto', 'dev', 'vulcão: esquema + número + localização', [
        C('A pressão do magma empurra a crosta.', _ac('e1', 'mecanismo', 'magma', 'magma empurrando', {'esquema': ESQ_VULCAO}, 'magma acumula', 'crosta empurrada pela pressão')),
        C('O Everest tem 8.849 metros.', _ac('e2', 'numero', 'Everest', 'altura', {'valor': 8849, 'unidade': 'm', 'fonte': 'Wikipédia'}, crit=False)),
        C('O Saara fica no norte da África.', _ac('e3', 'localizacao', 'Saara', 'Saara', {'pontos': P(('Saara', 13, 23))}, crit=False))], [], {'aprova'}),
    ('x2', 'misto', 'val', 'história + mecanismo inválido no meio', [
        C('Em 1969, a Apollo 11 pousou na Lua.', _ac('e1', 'evento_historico', 'Apollo 11', 'módulo lunar na Lua', {'ano': 1969}, 'nave em órbita', 'módulo pousado na Lua', quando='1969'), foto='a1'),
        C('O foguete funciona por reação.', _ac('e2', 'mecanismo', 'foguete', 'foguete', {'etapas': ['os gases quentes saem com muita força pela tubeira', 'o foguete é empurrado para o lado oposto']}, 'foguete parado', 'foguete subindo'))],
     [A('a1', 'd', 'Módulo lunar da Apollo 11 pousado na superfície da Lua, 1969', 1969)], {'bloqueia'}),
    ('x3', 'misto', 'val', 'biografia + série + rota', [
        C('Turing nasceu em 1912 e propôs sua máquina em 1936.', _ac('e1', 'sequencia_historica', 'Alan Turing', 'vida', {'eventos': [{'ano': 1912, 'texto': 'Nasce'}, {'ano': 1936, 'texto': 'Máquina'}]}, crit=False)),
        C('A população cresceu de 1950 a 2020.', _ac('e2', 'evolucao_temporal', 'população', 'crescimento', {'serie': [[1950, 2.5], [1970, 3.7], [1990, 5.3], [2020, 7.8]], 'fonte': 'ONU'}, crit=False)),
        C('As jubartes migram da Antártida ao Brasil.', _ac('e3', 'deslocamento', 'baleias-jubarte', 'rota', {'pontos': P(('Península Antártica', -60, -64), ('Abrolhos', -38.7, -17.9)), 'tipo': 'maritima'}))], [], {'aprova'}),
    ('x4', 'misto', 'val', 'tipo desconhecido declarado', [C('O som viaja pelo ar.', _ac('e1', 'propagacao_sonora', 'som', 'ondas', {}))], [], {'bloqueia'}),
    ('x5', 'misto', 'val', 'vídeo real do lugar (apoio)', [C('O porto de Santos à noite.', _ac('e1', 'lugar', 'porto', 'porto à noite', {'video': VID}, crit=False))], [], {'aprova'}),
]


def _sem_ia(prompt):                               # provedor de IA indisponível: nenhum conserto, nenhum plano
    raise RuntimeError('provedor de IA indisponível (simulado)')


def rodar_um(cen, pasta: Path) -> dict:
    cid, grupo, conj, desc, cenas, acervo, esperado = cen
    v = {'titulo': desc, 'fatos': FATOS, 'fontes': ['Wikipédia', 'ONU', 'FAO', 'NASA'], 'acervo': copy.deepcopy(acervo),
         'cenas': [dict(copy.deepcopy(c), grupo=k, evento=f'i{k}') for k, c in enumerate(cenas)]}
    etapa, bloq, rev = 'preparo', [], []
    try:
        prevalidacao.reparar(v, chamar=_sem_ia)
    except Exception as e:                         # falha do provedor não pode derrubar: vira pendência registrada
        rev.append(f'pré-validação: {str(e)[:80]}')
    try:
        planejamento.planejar(v, chamar=_sem_ia)
    except Exception:
        pass
    rel = preparo.preparar(v)
    bloq += [f"preparo {b['evento']}: {' | '.join(map(str, b['faltam']))[:160]}" for b in rel['bloqueios']]
    rev += [f"preparo {r['evento']}: {r['problema'][:120]}" for r in rel['revisoes']]
    if not bloq:
        etapa = 'previa'
        pv = previa.validar(v, pasta / cid)
        bloq += [f"prévia {b['evento']}: {' | '.join(b['faltam'])[:160]}" for b in pv['bloqueios']]
        if not bloq:
            etapa = 'cobertura'
            cb = cobertura.avaliar(v, pv)
            bloq += [f"cobertura {b['evento']}: {' | '.join(b['faltam'])[:160]}" for b in cb['bloqueios']]
            rev += [f"cobertura {r['evento']}: {r['problema'][:120]}" for r in cb['revisoes']]
    if not bloq:
        etapa = 'fiscal'
        por = {x['id']: x for x in v['acervo']}
        t, s1 = 0.0, []
        for c in v['cenas']:
            d = max(2.0, min(4.0, len(c['fala']) / 14.6))
            x = por.get(c.get('foto'))
            s1.append({**c, 'start': t, 'end': t + d, 'img': x['arq'] if x and Path(x['arq']).exists() else None, 'credito': (x or {}).get('credito')})
            t += d
        d1 = {'duration': t, 'meta': {'titulo': desc, 'fontes': v['fontes'], 'preparo': rel}, 'scenes': s1, 'captions': []}
        v2, dire = montagem.converter(d1)
        r = fiscal_v2.avaliar(v2, dire, None, d1)
        bloq += [f"fiscal {a['codigo']}: {a['problema']}" for a in r['achados'] if a['gravidade'] == 'bloqueio']
        rev += [f"fiscal {a['codigo']}: {a['problema']}" for a in r['achados'] if a['gravidade'] == 'revisao']
        comps = [sc['comp'] for sc in v2['scenes']]
    else:
        comps = []
    res = 'bloqueia' if bloq else 'revisao' if rev else 'aprova'
    return {'id': cid, 'grupo': grupo, 'conjunto': conj, 'descricao': desc, 'esperado': sorted(esperado), 'resultado': res, 'passou': res in esperado,
            'etapa': etapa, 'composicoes': comps, 'bloqueios': bloq, 'revisoes': rev}


def rodar(pasta: Path, conjunto: str = 'todos') -> dict:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    out = [rodar_um(c, pasta) for c in CENARIOS if conjunto in ('todos', c[2])]
    por = {}
    for r in out:
        g = por.setdefault((r['conjunto'], r['grupo']), {'total': 0, 'passou': 0})
        g['total'] += 1; g['passou'] += r['passou']
    rel = {'cenarios': out, 'por_grupo': {f'{k[0]}/{k[1]}': v for k, v in sorted(por.items())},
           'total': len(out), 'passaram': sum(r['passou'] for r in out)}
    (pasta / 'matriz.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding='utf-8')
    return rel


if __name__ == '__main__':
    r = rodar(Path(sys.argv[1] if len(sys.argv) > 1 else 'saida/_matriz'), sys.argv[2] if len(sys.argv) > 2 else 'todos')
    for c in r['cenarios']:
        print(f"{'OK ' if c['passou'] else 'XX '} {c['conjunto']} {c['id']:3} {c['grupo']:10} esperado={'/'.join(c['esperado']):16} obtido={c['resultado']:8} "
              f"[{c['etapa']}] {c['descricao'][:40]} {'; '.join(c['bloqueios'] + c['revisoes'])[:150] if not c['passou'] else ''}")
    print(f"{r['passaram']}/{r['total']}", r['por_grupo'])
