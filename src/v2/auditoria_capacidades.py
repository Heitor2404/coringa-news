"""V2.5 — Auditoria RENDERIZADA das capacidades (não basta o teste unitário passar).

Para cada composição do catálogo e cada (tipo de acontecimento × composição capaz) de contrato.TIPOS:
  1. o EXEMPLO da galeria é renderizado no palco (o que a composição sabe fazer no melhor caso);
  2. um contrato BEM FORMADO passa pelo caminho real (contrato → capacidades → montagem → palco);
  3. o MESMO contrato como o roteirista costuma escrever (frases soltas, campos faltando) passa pelo mesmo caminho.
Mede: erros do renderizador, texto fora/sobreposto persistente, área vazia, mudança entre início e fim, se a
composição mostra um acontecimento (DEMONSTRATIVA) ou só escreve (TEXTUAL), se usa imagem/vídeo real.

Classificação (por composição):
  FUNCIONAL     exemplo e contrato bem formado renderizam sem defeito; dado ruim é recusado (limitação explícita) ou
                renderiza sem defeito; se é demonstrativa, há mudança visível.
  LIMITADA      funciona, mas só escreve (cartão/etapas), ou dado ruim vira tela degradada sem bloqueio, ou depende de
                insumo que o fluxo raramente tem (vídeo, par antes/depois, quadros pré-renderizados).
  NÃO FUNCIONAL o exemplo ou o contrato bem formado falha no render.
Uso: python -m src.v2.auditoria_capacidades <pasta_saida>
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from src.v2 import contrato, fiscal_v2, galeria, montagem, previa

RAIZ = Path(__file__).resolve().parents[2]
IMG = [str(RAIZ / 'tests' / 'img' / f) for f in ('fundo_b.jpg', 'fundo_c.jpg', 'fundo_d.jpg')]
VIDEO = str(RAIZ / 'tests' / 'midia' / 'video_horizontal_navio.mp4')
P = lambda *a: [{'nome': n, 'lon': lo, 'lat': la} for n, lo, la in a]
ESQ = {'objetos': [{'id': 'r', 'forma': 'superficie', 'rotulo': 'ROCHA', 'y': .85, 'w': 1},
                   {'id': 'm', 'forma': 'corpo', 'rotulo': 'MAGMA', 'x': .5, 'y': .6, 'w': .3, 'h': .2}],
       'estados': [{'rotulo': 'PRESSÃO CRESCE'}, {'rotulo': 'MAGMA SOBE', 'objetos': {'m': {'dy': -.35, 'escala': 1.3}},
                                                 'relacoes': [{'de': 'm', 'para': 'r', 'tipo': 'empurra', 'forca': 1, 'rotulo': 'PRESSÃO'}]}]}

# tipo → comp → (fala, dados bem formados, dados como o roteirista escreve). Assuntos variados, nenhum da lagartixa.
AMOSTRAS = {
    'mecanismo': {
        'mecanismo.estados': ('A pressão do magma empurra a rocha até romper.', {'esquema': ESQ}, {'esquema': 'magma empurrando a rocha'}),
        'diagrama.explicativo': ('O pedal gira a coroa, que puxa a corrente e gira a roda.', {'nos': [{'id': 'a', 'rotulo': 'Pedal'}, {'id': 'b', 'rotulo': 'Coroa'}, {'id': 'c', 'rotulo': 'Corrente'}, {'id': 'd', 'rotulo': 'Roda'}]},
                                 {'nos': ['o ciclista empurra o pedal para baixo com força', 'a corrente transmite o giro até a roda traseira']}),
        'processo.etapas': ('O vapor empurra o pistão, que gira a roda.', {'etapas': [{'titulo': 'Vapor', 'texto': 'A caldeira ferve a água'}, {'titulo': 'Pistão', 'texto': 'O vapor empurra o pistão'}, {'titulo': 'Roda', 'texto': 'A biela gira a roda'}]},
                            {'etapas': ['a água da caldeira ferve e vira vapor sob pressão', 'o vapor empurra o pistão dentro do cilindro']}),
        'forcas.vetores': ('O empuxo da água segura o navio contra o peso.', {'forcas': [{'nome': 'Peso', 'angulo': -90, 'intensidade': .8}, {'nome': 'Empuxo', 'angulo': 90, 'intensidade': .8}], 'objeto': 'navio', 'meio': 'agua'},
                           {'forcas': ['forças eletromagnéticas entre as partículas']}),
        'mecanismo.eclusa': ('A câmara enche e o navio sobe até o lago.', {'sentido': 'subir', 'desnivel_m': 26}, {'sentido': 'para cima'}),
    },
    'transformacao': {
        'mecanismo.estados': ('A pressão do magma empurra a rocha até romper.', {'esquema': ESQ}, {}),
        'comparacao.antes_depois': ('A geleira recuou em cem anos.', {'img_antes': IMG[0], 'img_depois': IMG[1], 'rotulo_antes': '1920', 'rotulo_depois': 'HOJE'}, {'img_antes': IMG[0]}),
        'processo.etapas': ('O ferro oxida e vira ferrugem.', {'etapas': ['Ferro', 'Água e oxigênio', 'Ferrugem']}, {'etapas': ['o ferro exposto à chuva por muito tempo']}),
    },
    'movimento': {
        'forcas.vetores': ('A maçã cai porque o peso a puxa.', {'forcas': [{'nome': 'Peso', 'angulo': -90, 'intensidade': .8}], 'objeto': 'bola', 'meio': 'ar'}, {'forcas': ['gravidade terrestre puxando o objeto']}),
        'mecanismo.nivel': ('O rio subiu de 2 para 9 metros.', {'de': 2, 'ate': 9, 'max': 10, 'unidade': 'm', 'objeto': 'casa'}, {'de': 'baixo', 'ate': 'alto'}),
        'animacao.quadros': ('O foguete sobe em arco.', {'cena': 'lancamento', 'quadros': {'manim': 'lancamento', 'angulo': 60}}, {'cena': 'foguete subindo'}),
    },
    'nivel': {'mecanismo.nivel': ('A represa encheu de 10 para 40 metros.', {'de': 10, 'ate': 40, 'max': 50, 'unidade': 'm', 'objeto': 'nenhum'}, {'de': 'vazia'})},
    'deslocamento': {'mapa.rota': ('O navio saiu de Xangai e chegou a Roterdã.', {'pontos': P(('Xangai', 121.5, 31.2), ('Roterdã', 4.5, 51.9)), 'tipo': 'maritima'},
                                   {'pontos': [{'nome': 'Xangai'}, {'nome': 'Roterdã'}]})},
    'processo': {'mecanismo.estados': ('A pressão do magma empurra a rocha até romper.', {'esquema': ESQ}, {}),
                 'processo.etapas': ('A lagarta vira pupa e depois borboleta.', {'etapas': ['Lagarta', 'Pupa', 'Borboleta']}, {'etapas': ['a lagarta se fecha num casulo por semanas']}),
                 'diagrama.explicativo': ('A água evapora, condensa e chove.', {'nos': [{'id': 'e', 'rotulo': 'Evaporação'}, {'id': 'c', 'rotulo': 'Condensação'}, {'id': 'p', 'rotulo': 'Chuva'}]}, {'nos': 'ciclo da água'})},
    'evolucao_temporal': {'grafico.temporal': ('A população cresceu de 1950 a 2020.', {'serie': [[1950, 2.5], [1970, 3.7], [1990, 5.3], [2020, 7.8]], 'unidade': 'bi', 'titulo': 'População mundial (bilhões)', 'fonte': 'ONU'},
                                               {'serie': [[1950, 2.5], [2020, 7.8]]})},
    'impacto': {'evento.impacto': ('A explosão destruiu tudo num raio de 2 km.', {'aneis': [{'raio_km': 2, 'rotulo': 'Destruição total'}, {'raio_km': 10, 'rotulo': 'Vidros quebrados'}], 'centro': 'Porto'},
                                   {'aneis': ['muito destruído perto do porto']})},
    'orbita': {'astronomia.orbita': ('A Terra leva um ano para dar uma volta no Sol.', {'central': {'nome': 'Sol'}, 'orbitante': {'nome': 'Terra'}, 'periodo': '365 dias'}, {})},
    'escala': {'comparacao.grandezas': ('O navio tem 400 metros, mais que a Torre Eiffel.', {'itens': [{'rotulo': 'Navio', 'valor': 400, 'forma': 'navio'}, {'rotulo': 'Torre Eiffel', 'valor': 330, 'forma': 'torre'}], 'unidade': 'm', 'fonte': 'Wikipédia'},
                                          {'itens': ['navio enorme', 'torre alta']})},
    'comparacao': {'grafico.barras': ('O Brasil produz mais café que a Colômbia.', {'itens': [{'rotulo': 'Brasil', 'valor': 3.7}, {'rotulo': 'Vietnã', 'valor': 1.8}, {'rotulo': 'Colômbia', 'valor': .8}], 'unidade': 'Mt', 'fonte': 'FAO', 'titulo': 'Café (milhões de t)'},
                                      {'itens': [{'rotulo': 'Brasil'}, {'rotulo': 'Colômbia'}]})},
    'proporcao': {'proporcao': ('71% da Terra é coberta por água.', {'pct': 71, 'rotulo': 'Superfície coberta por água', 'fonte': 'NASA'}, {'pct': 'a maior parte'})},
    'numero': {'numero.animado': ('A ponte tem 1.280 metros.', {'valor': 1280, 'unidade': 'm', 'rotulo': 'Vão da ponte', 'fonte': 'Wikipédia'}, {'valor': 'mais de mil'})},
    'sequencia_historica': {'linha_tempo.historica': ('Construído em 1904, aberto em 1914.', {'eventos': [{'ano': 1904, 'texto': 'Obras começam'}, {'ano': 1914, 'texto': 'Canal aberto'}]}, {'eventos': ['começo das obras']})},
    'evento_historico': {'foto.historica': ('Em 1912, o navio deixou o porto.', {'img': IMG[2], 'ano': 1912, 'descricao': 'Navio no porto'}, {}),
                         'video.documental': ('O navio passa pelo canal.', {'video': VIDEO}, {}),
                         'linha_tempo.historica': ('Construído em 1904, aberto em 1914.', {'eventos': [{'ano': 1904, 'texto': 'Obras começam'}, {'ano': 1914, 'texto': 'Canal aberto'}]}, {})},
    'localizacao': {'mapa.localizacao': ('Fica no Panamá, entre dois oceanos.', {'pontos': P(('Cidade do Panamá', -79.5, 9.0))}, {'pontos': [{'nome': 'Panamá'}]})},
    'territorio': {'mapa.territorio': ('O Chile é longo e estreito.', {'pais': 'Chile'}, {'pais': 'um país sul-americano'})},
    'citacao': {'citacao': ('"Um pequeno passo", disse Armstrong.', {'texto': 'Um pequeno passo para o homem.', 'autor': 'Neil Armstrong'}, {'texto': 'frase famosa'})},
    'documento': {'fonte.evidencia': ('O jornal noticiou o naufrágio.', {'veiculo': 'Wikipédia', 'trecho': 'O navio afundou em 1912.', 'titulo': 'Naufrágio'}, {'veiculo': 'um jornal'}),
                  'foto.historica': ('A carta foi assinada em 1888.', {'img': IMG[2], 'ano': 1888}, {})},
    'pessoa': {'lower_third': ('Marie Curie ganhou dois Nobel.', {'nome': 'Marie Curie', 'descricao': 'física e química'}, {}), 'foto.documental': ('Marie Curie em seu laboratório.', {}, {})},
    'lugar': {'video.documental': ('O porto à noite.', {'video': VIDEO}, {}), 'foto.documental': ('A cidade vista do alto.', {}, {})},
    'ambiente': {'video.documental': ('A floresta úmida.', {'video': VIDEO}, {}), 'foto.documental': ('A floresta úmida.', {}, {})},
}
INSUMO_RARO = {'video.documental': 'vídeo real licenciado', 'comparacao.antes_depois': 'par de fotos do mesmo lugar em épocas diferentes',
               'animacao.quadros': 'quadros pré-renderizados (Manim)', 'foto.historica': 'foto de arquivo com resolução',
               'mecanismo.eclusa': 'específica de eclusa (canal)'}


def _pelo_caminho_real(tipo: str, comp: str, fala: str, dados: dict, critico: bool = True) -> tuple[dict, dict]:
    ac = {'id': 'e1', 'tipo': tipo, 'sujeito': 'x', 'mostrar': fala, 'capacidade': comp, 'dados': copy.deepcopy(dados),
          'importancia': 'critica' if critico else 'apoio', 'fonte': 'Wikipédia'}
    s = {'tipo': 'historia', 'fala': fala, 'start': 0.0, 'end': previa.DUR, 'img': IMG[1], 'grupo': 'g0', 'acontecimento': ac}
    d1 = {'duration': previa.DUR, 'meta': {'titulo': 't', 'fontes': ['Wikipédia', 'ONU', 'FAO', 'NASA']}, 'scenes': [s], 'captions': []}
    v2, direcao = montagem.converter(d1)
    r = fiscal_v2.avaliar(v2, direcao, [], d1)
    direcao[0]['_fiscal'] = sorted({a['codigo'] for a in r['achados'] if a['gravidade'] == 'bloqueio'})
    return v2['scenes'][0], direcao[0]


def _render(sc: dict, pasta: Path, nome: str) -> dict:
    try:
        r = previa.renderizar(sc['comp'], sc.get('params') or {}, pasta, nome, fundo=sc.get('fundo'))
    except Exception as e:
        return {'erros': [f'render falhou: {str(e)[:140]}'], 'graves': [], 'medidas': {'std': [0], 'dif_ini_fim': 0, 'dif_ini_meio': 0, 'frac_mudou': 0}, 'quadros': []}
    return r


def _defeitos(comp: str, r: dict) -> list[str]:
    return previa.problemas(comp, {**r, 'params': {}}) if comp != 'mecanismo.estados' else \
        [p for p in previa.problemas(comp, {**r, 'params': {'esquema': ESQ}})]


def auditar(pasta: Path) -> dict:
    pasta = Path(pasta)
    cat = {m['id']: m for m in galeria.catalogo(pasta / '_cat')}
    linhas, por_comp = [], {}
    for cid, m in cat.items():                                         # 1. exemplo
        ex = m.get('exemplo') or {}
        sc = {'comp': cid, 'params': galeria.dados_exemplo(m)['scenes'][0].get('params'), 'fundo': galeria.dados_exemplo(m)['scenes'][0].get('fundo')}
        r = _render(sc, pasta / 'exemplo', cid)
        por_comp[cid] = {'exemplo': {'defeitos': _defeitos(cid, r), 'medidas': r['medidas'], 'quadros': [Path(q).name for q in r['quadros']]},
                         'contratos': [], 'tem_exemplo': bool(ex)}
    for tipo, comps in AMOSTRAS.items():                               # 2/3. caminho real
        for comp, (fala, bom, cru) in comps.items():
            for rotulo, dados in (('bem_formado', bom), ('roteirista', cru)):
                sc, d = _pelo_caminho_real(tipo, comp, fala, dados)
                l = {'tipo': tipo, 'pedida': comp, 'dados': rotulo, 'escolhida': sc['comp'], 'params_recebidos': sorted((sc.get('params') or {}).keys()),
                     'limitacao': d.get('limitacao'), 'faltam': d.get('faltam'), 'fiscal_bloqueia': d.get('_fiscal')}
                # crítico que não ganhou a composição pedida: precisa de outra capaz OU limitação + bloqueio (nada silencioso)
                capazes = set(contrato.capazes(tipo)) - contrato.GENERICAS
                l['fallback_silencioso'] = bool(sc['comp'] != comp and sc['comp'] not in capazes and not d.get('_fiscal')
                                                and contrato.TIPOS[tipo]['critico'])
                if sc['comp'] == comp:
                    r = _render(sc, pasta / 'contrato', f'{tipo}__{comp}__{rotulo}')
                    l.update(defeitos=_defeitos(comp, r), medidas=r['medidas'], quadros=[Path(q).name for q in r['quadros']])
                else:
                    l.update(defeitos=[], medidas=None, quadros=[])
                linhas.append(l)
                por_comp.setdefault(comp, {'exemplo': None, 'contratos': []})['contratos'].append(l)
    matriz = {}
    for cid, x in por_comp.items():
        ex = x.get('exemplo') or {'defeitos': ['sem exemplo']}
        bons = [l for l in x['contratos'] if l['dados'] == 'bem_formado']
        crus = [l for l in x['contratos'] if l['dados'] == 'roteirista']
        bom_ok = all(l['escolhida'] == l['pedida'] and not l['defeitos'] for l in bons) if bons else None
        cru_degrada = [l for l in crus if l['escolhida'] == l['pedida'] and l['defeitos']]
        cru_seguro = all(l['escolhida'] != l['pedida'] or not l['defeitos'] for l in crus)
        motivos = []
        if ex['defeitos']:
            estado = 'NÃO FUNCIONAL'; motivos.append('exemplo: ' + '; '.join(ex['defeitos']))
        elif bom_ok is False:
            estado = 'NÃO FUNCIONAL'; motivos += [f"contrato bem formado ({l['tipo']}): " + ('; '.join(l['defeitos']) or f"virou {l['escolhida']}") for l in bons if l['escolhida'] != l['pedida'] or l['defeitos']]
        else:
            estado = 'FUNCIONAL'
            if cid in contrato.TEXTUAIS:
                estado = 'LIMITADA'; motivos.append('só escreve etapas/nós: aceito para mecanismo crítico apenas com rótulos curtos')
            if cru_degrada:
                estado = 'LIMITADA'; motivos += [f"dado do roteirista ({l['tipo']}) renderiza degradado: {'; '.join(l['defeitos'])}" for l in cru_degrada]
            if cid in INSUMO_RARO:
                estado = 'LIMITADA' if estado == 'FUNCIONAL' and cid not in ('foto.historica',) else estado
                motivos.append('depende de ' + INSUMO_RARO[cid])
            if bom_ok is None:
                motivos.append('sem tipo de acontecimento que a escolha (uso editorial/apoio)')
        matriz[cid] = {'estado': estado, 'demonstra': contrato.demonstra(cid), 'textual': cid in contrato.TEXTUAIS,
                       'usa_midia_real': cid in ('foto.documental', 'foto.historica', 'foto.sequencia', 'comparacao.antes_depois', 'video.documental', 'abertura.pergunta', 'abertura.revelacao'),
                       'tipos': sorted({l['tipo'] for l in x['contratos']}), 'motivos': motivos,
                       'dado_ruim_recusado': cru_seguro, 'exemplo': ex.get('medidas')}
    rel = {'matriz': matriz, 'linhas': linhas, 'fallbacks_silenciosos': [l for l in linhas if l.get('fallback_silencioso')]}
    (pasta / 'auditoria_capacidades.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return rel


if __name__ == '__main__':
    r = auditar(Path(sys.argv[1] if len(sys.argv) > 1 else 'saida/_auditoria'))
    print('fallbacks silenciosos:', [(l['tipo'], l['pedida'], l['dados'], l['escolhida']) for l in r['fallbacks_silenciosos']])
    for cid, x in sorted(r['matriz'].items(), key=lambda kv: (kv[1]['estado'], kv[0])):
        print(f"{x['estado']:14} {cid:24} {'DEMONSTRA' if x['demonstra'] else ('TEXTO' if x['textual'] else ''):10} {' | '.join(x['motivos'])[:200]}")
