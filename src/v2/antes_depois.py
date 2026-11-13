"""ANTES × DEPOIS com o vídeo do Panamá (execução 43435732255): as MESMAS falas, nos mesmos segundos, renderizadas
pelo motor atual (template.html, main) e pela V2 (montagem.converter + palco). Sem IA, sem TTS, sem geração paga:
usa o dados.json e as imagens recuperadas pela auditoria (workflow extrair-auditoria).

Uso: CORINGA_AUDITORIA=/caminho/do/diagnostico python -m src.v2.antes_depois --saida saida/galeria_v2
Grava quadros em <saida>/antes_depois/ e a lista em <saida>/comparacoes.json (a galeria lê esse arquivo).
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

from src.v2 import fatos, fiscal_v2, montagem, palco

AUD = Path(os.environ.get('CORINGA_AUDITORIA', str(palco.RAIZ / 'saida' / 'auditoria')))
# (id, título, segundo, nota)
PARES = [
    ('abertura', 'Abertura', 1.6, 'Antes: título, selo e mascote empilhados sobre a foto. Depois: abertura com a pergunta como texto principal no terço de baixo, kicker e linha de contexto; o 1º quadro já é capa.'),
    ('mapa', 'Mapa', 6.6, 'Antes: mapa d3 estático com dois pinos. Depois: MapLibre + Natural Earth (lago Gatún, rios, fronteiras), câmera que aproxima, rota desenhada no ritmo da fala e distância (80 km).'),
    ('escala', 'Número de escala (26 m)', 10.2, 'Antes: foto de satélite com "26 metros" na legenda. Depois: comparação de escala com referências conhecidas (prédios, Cristo Redentor), mesma escala.'),
    ('mecanismo1', 'Mecanismo da eclusa — entra e fecha', 16.5, 'Antes: foto do SS Ancon (1914) com etiqueta. Depois: corte esquemático; o navio entra e a comporta de trás fecha.'),
    ('mecanismo2', 'Mecanismo da eclusa — a câmara enche', 21.0, 'Antes: tela roxa com palavras (nenhum recurso mostrava a câmara enchendo). Depois: a água do lago desce pelo túnel por gravidade, a câmara enche e o navio sobe com a régua em metros.'),
    ('mecanismo3', 'Mecanismo da eclusa — gravidade', 23.5, 'Antes: cartão "GRAVIDADE, sem bombas" sobre fundo roxo. Depois: a mesma informação dentro do mecanismo (seta e rótulo GRAVIDADE no túnel).'),
    ('mecanismo4', 'Mecanismo da eclusa — comporta da frente abre', 27.0, 'Antes: foto das comportas. Depois: nível igual, comporta da frente abre e o navio segue para o lago.'),
    ('descer', 'Descida (o inverso)', 30.5, 'Antes: tela roxa. Depois: a mesma eclusa no sentido inverso: a câmara esvazia para o mar.'),
    ('historica', 'Fotografia histórica (1913)', 34.0, 'Antes: a foto de 1913 aparecia como faixa fina com retângulo branco (era o cartão do scanner). Depois: recorte automático do conteúdo, visão geral + varredura ampliada (máx. 2×), carimbo de procedência.'),
    ('numero', 'Número (200 milhões de litros)', 39.0, 'Antes: número grande sobre foto, texto triplicado. Depois: infográfico em papel com natureza do valor, equivalência e fonte. (Fonte "Wikipédia" assumida para a demonstração: o roteiro não registrou a fonte; sem ela a V2 BLOQUEIA a cena.)'),
    ('identificacao', 'Banner / identificação de lugar', 41.2, 'Antes: etiqueta "AGUA CLARA · 2016" solta na foto. Depois: lower third de identificação (barra, nome, descrição).'),
    ('legenda', 'Legenda sobre foto', 47.0, 'Antes: legenda 76 px com contorno grosso. Depois: legenda 66 px em faixa fixa, palavra atual em amarelo, futuras translúcidas.'),
    ('dinheiro', 'Valor financeiro (era "R$ 27 milhões")', 51.5, 'Antes: "R$ 27 milhões pagos por um navio para atravessar", fonte fora da lista. Depois: moeda original (US$ 5,3 mi), natureza "LANCE RECORDE EM LEILÃO", contexto (vaga; pedágio à parte) e fonte listada — validado por src/v2/fatos.py. A narração antiga ainda diz "R$ 27 milhões": a correção precisa voltar ao roteiro e à voz.'),
    ('revelacao', 'Revelação', 55.2, 'Antes: resposta sobre a foto. Depois: revelação no instante em que é dita, com clarão e barra.'),
    ('encerramento', 'Encerramento', 58.6, 'Antes: mascote pequeno sobre árvores, @ duplicado, fontes ilegíveis. Depois: fundo limpo, Coringa grande, marca e @ uma vez, fontes ≥ 26 px.'),
]
PREVIAS = [('mecanismo', 14.8, 28.5), ('mapa', 2.9, 7.7), ('abertura', 0.0, 2.9)]


def _v1_absoluto(dados: dict) -> dict:
    d = copy.deepcopy(dados)
    for sc in d['scenes']:
        for k in ('img', 'rec', 'img_fundo'):
            if sc.get(k) and not str(sc[k]).startswith('file:'):
                sc[k] = str((AUD / sc[k]).resolve())
    return d


def antes(dados: dict, tempos: list[float], pasta: Path) -> dict:
    from playwright.sync_api import sync_playwright
    from src.render import render
    d = render.preparar(_v1_absoluto(dados))
    d['cap_baixo'] = dados.get('cap_baixo', [])
    (pasta / '_v1').mkdir(parents=True, exist_ok=True)
    pg_arq = render._escrever_pagina(d, pasta / '_v1')
    out = {}
    with sync_playwright() as p:
        nav = p.chromium.launch(args=render.NAVEGADOR)
        pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(pg_arq.as_uri())
        pg.wait_for_function('window.READY===true', timeout=120000)
        for t in tempos:
            pg.evaluate(f'seek({t})')
            a = pasta / f'antes_{t:05.2f}.jpg'
            pg.screenshot(path=str(a), type='jpeg', quality=88)
            out[t] = a
        nav.close()
    return out


def depois_dados(dados: dict) -> tuple[dict, list[dict]]:
    corr = {13: {'valor': 200, 'unidade': 'milhões de litros', 'rotulo': 'Água doce por travessia', 'natureza': 'tipico', 'natureza_txt': 'MÉDIA POR TRAVESSIA',
                 'contexto': 'Sai do lago Gatún e vai para o mar.', 'fonte': 'Wikipédia', 'equivalencia': {'icone': 'piscina', 'n': 80, 'texto': '≈ 80 piscinas olímpicas (2,5 milhões de L cada)'}},
            18: fatos.PANAMA_LEILAO}
    return montagem.converter(dados, AUD, fatos_corrigidos=corr)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--saida', default=str(palco.RAIZ / 'saida' / 'galeria_v2'))
    ap.add_argument('--sem-previa', action='store_true')
    a = ap.parse_args(argv)
    saida = Path(a.saida).resolve()
    pasta = saida / 'antes_depois'
    pasta.mkdir(parents=True, exist_ok=True)
    dados = json.loads((AUD / 'dados.json').read_text(encoding='utf-8'))
    tempos = [t for _, _, t, _ in PARES]
    A = antes(dados, tempos, pasta)
    v2, direcao = depois_dados(dados)
    (pasta / 'panama_v2.json').write_text(json.dumps({'dados': v2, 'direcao': direcao}, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    comps, previas = [], {}
    with palco.abrir(palco.preparar(v2), pasta / '_v2') as pg:
        geo = palco.medir(pg, v2['duration'], .25)
        for t in tempos:
            palco.capturar(pg, t, pasta / f'depois_{t:05.2f}.jpg', 88)
        if not a.sem_previa:
            for nome, i0, i1 in PREVIAS:
                previas[nome] = palco.previa(pg, i0, i1, pasta / f'previa_{nome}.mp4', fps=24)
        erros = pg.erros + pg.evaluate('V2.avisos')
    rel = fiscal_v2.avaliar(v2, direcao, geo, dados)
    (pasta / 'fiscal_v2_panama.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding='utf-8')
    print(fiscal_v2.texto(rel))
    if erros:
        print('ERROS DA PÁGINA:', erros)
    for pid, tit, t, nota in PARES:
        sc = next((s for s in v2['scenes'] if s['start'] <= t < s['end']), {})
        pv = 'mecanismo' if pid.startswith('mecanismo') else pid if pid in previas else None
        comps.append({'id': pid, 'titulo': tit, 't': t, 'nota': nota, 'comp': sc.get('comp', ''),
                      'antes': A[t].relative_to(saida).as_posix(), 'depois': (pasta / f'depois_{t:05.2f}.jpg').relative_to(saida).as_posix(),
                      'previa': previas[pv].relative_to(saida).as_posix() if pv in previas else None})
    (saida / 'comparacoes.json').write_text(json.dumps(comps, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(comps)} comparações em {pasta}')


if __name__ == '__main__':
    main()
