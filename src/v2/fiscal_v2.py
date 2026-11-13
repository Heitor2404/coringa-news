"""FISCAL V2: bloqueios determinísticos separados da avaliação subjetiva.

O fiscal anterior dava nota alta a vídeos que não cumpriam a promessa (a eclusa "explicada" com telas roxas e texto).
Aqui:
  - BLOQUEIO (reprova a cena e o vídeo, sem nota que compense):
      B1 acontecimento crítico sem representação (capacidades → limitação);
      B2 fala promete mecanismo/processo e a cena mostra foto ou texto;
      B3 número que não passou em fatos.validar();
      B4 texto sobre texto ou fora do quadro persistente (≥ 0,75 s);
      B5 revelação mostrada antes de ser dita (spoiler) ou > 0,4 s depois.
  - AVISO (vai para o relatório, não bloqueia): imagem repetida, foto parada > 5 s, plano > 8 s, texto na zona da
    interface, letra < 24 px, loudness fora de −14 ± 1 LUFS, composições iguais em sequência.
  - SUBJETIVO: lista de perguntas para o Heitor (composição, beleza, ritmo percebido). NÃO vira nota automática.
"""
from __future__ import annotations

import re

from src.v2 import capacidades

MECANISMOS = {'mecanismo.eclusa', 'mecanismo.nivel', 'processo.etapas', 'diagrama.explicativo', 'forcas.vetores', 'astronomia.orbita', 'evento.impacto'}
PERGUNTAS = ['A abertura faz querer ver o resto (sem depender da legenda)?', 'O mecanismo ficou claro só olhando a tela, sem som?',
             'Algum gráfico/mapa ficou bonito mas não explicou nada?', 'Alguma foto parece de banco de imagens, sem relação com a fala?',
             'O ritmo cansa em algum trecho (anotar o segundo)?', 'O encerramento tem cara de marca (mascote, marca, fontes legíveis)?']


def _persistentes(geo: list[dict], passo: float = .25, minimo: float = .75) -> list[dict]:
    grupos = {}
    for p in sorted(geo, key=lambda x: x['t']):
        k = (p['tipo'], p['txt'])
        g = grupos.setdefault(k, [])
        if g and p['t'] - g[-1]['fim'] <= passo * 1.5:
            g[-1]['fim'] = p['t']
        else:
            g.append({**p, 'ini': p['t'], 'fim': p['t']})
    return [x for g in grupos.values() for x in g if x['fim'] - x['ini'] + passo >= minimo]


def avaliar(dados_v2: dict, direcao: list[dict], geometria: list[dict] | None = None, dados_v1: dict | None = None, audio: dict | None = None) -> dict:
    bloq, avis = [], []
    cenas = dados_v2['scenes']
    for k, (sc, d) in enumerate(zip(cenas, direcao)):
        ini = round(sc['start'], 1)
        if d.get('limitacao') and (d.get('critica') or sc.get('limitacao')) and d.get('comp') is None:
            bloq.append({'codigo': 'B1', 'cena': k, 'inicio': ini, 'texto': d['limitacao']})
        if d.get('bloqueio'):
            bloq.append({'codigo': 'B3', 'cena': k, 'inicio': ini, 'texto': '; '.join(d['bloqueio'])})
        for a in d.get('avisos', []):
            avis.append({'codigo': 'A-rep' if 'repetida' in a else 'A-ritmo', 'cena': k, 'inicio': ini, 'texto': a})
        dur = sc['end'] - sc['start']
        if dur > 8 and sc['comp'] not in MECANISMOS | {'linha_tempo.historica'}:
            avis.append({'codigo': 'A-plano', 'cena': k, 'inicio': ini, 'texto': f'plano de {dur:.1f} s ({sc["comp"]})'})
        if k and sc['comp'] == cenas[k - 1]['comp'] and sc.get('params') == cenas[k - 1].get('params') and (sc.get('fundo') or {}).get('img') == (cenas[k - 1].get('fundo') or {}).get('img'):
            avis.append({'codigo': 'A-cont', 'cena': k, 'inicio': ini, 'texto': 'mesma composição e mesmos dados da cena anterior'})
    # B2: a fala promete mecanismo e a tela não mostra
    if dados_v1:
        for i, s in enumerate(dados_v1['scenes']):
            if s.get('tipo') not in ('historia', 'imagem'):
                continue
            achados = [a for a in capacidades.detectar(s) if a['critica'] and a['por_texto']]
            mec = (s.get('bloco') or {}).get('funcao') == 'mecanismo' or any(a['capacidade'] in ('agua_subindo', 'agua_descendo', 'elevacao_vertical', 'manobra_eclusa', 'processo', 'forca', 'explosao') for a in achados)
            if not mec:
                continue
            k = next((k for k, sc in enumerate(cenas) if i in sc.get('origem', [])), None)
            if k is None:
                continue
            if cenas[k]['comp'] not in MECANISMOS:
                bloq.append({'codigo': 'B2', 'cena': k, 'inicio': round(s['start'], 1),
                             'texto': f'fala descreve mecanismo ("{re.sub(r"[*]", "", s.get("fala", ""))[:60]}") e a tela mostra {cenas[k]["comp"]}'})
    # B4 e avisos de geometria
    for p in _persistentes(geometria or []):
        if p.get('grave'):
            bloq.append({'codigo': 'B4', 'cena': None, 'inicio': p['ini'], 'texto': f"{p['tipo']}: {p['txt']} ({p['ini']:.1f}–{p['fim']:.1f}s, {p['cena']})"})
        else:
            avis.append({'codigo': 'A-geo', 'cena': None, 'inicio': p['ini'], 'texto': f"{p['tipo']}: {p['txt']} ({p['cena']})"})
    # B5 sincronização da revelação
    for k, sc in enumerate(cenas):
        if sc['comp'] != 'revelacao.surpresa':
            continue
        alvo = {w.lower() for w in re.findall(r'\w{3,}', str(sc['params'].get('resposta', '')))}
        dito = next((w.get('s', c['start']) for c in dados_v2.get('captions', []) for w in c['words']
                     if sc['start'] <= w.get('s', c['start']) <= sc['end'] and re.sub(r'\W', '', w['w'].lower()) in alvo), None)
        if dito is not None:
            mostra = sc['start'] + float(sc['params'].get('virada', 1.0))
            if mostra < dito - .4 or mostra > dito + .4:
                bloq.append({'codigo': 'B5', 'cena': k, 'inicio': round(sc['start'], 1), 'texto': f'resposta aparece em {mostra:.2f}s e é dita em {dito:.2f}s'})
    if audio and audio.get('lufs') is not None and abs(audio['lufs'] + 14) > 1:
        avis.append({'codigo': 'A-audio', 'cena': None, 'inicio': 0, 'texto': f"loudness {audio['lufs']:.1f} LUFS (meta −14)"})
    criticas = [d for d in direcao if d.get('critica')]
    det = {
        'cenas': len(cenas),
        'acontecimentos_criticos': len(criticas),
        'criticos_representados': sum(1 for d in criticas if d.get('comp')),
        'mecanismos_na_tela': sum(1 for sc in cenas if sc['comp'] in MECANISMOS),
        'numeros_bloqueados': sum(1 for d in direcao if d.get('bloqueio')),
        'problemas_geometricos_graves': sum(1 for b in bloq if b['codigo'] == 'B4'),
        'imagens_repetidas': sum(1 for a in avis if a['codigo'] == 'A-rep'),
        'maior_plano_s': round(max((sc['end'] - sc['start'] for sc in cenas), default=0), 1),
        'composicoes_distintas': len({sc['comp'] for sc in cenas}),
    }
    return {'aprovado_tecnicamente': not bloq, 'bloqueios': bloq, 'avisos': avis, 'deterministico': det,
            'subjetivo': {'estado': 'pendente de avaliação humana (sem nota automática)', 'perguntas': PERGUNTAS}}


def texto(r: dict) -> str:
    linhas = [f"FISCAL V2 — {'sem bloqueio' if r['aprovado_tecnicamente'] else str(len(r['bloqueios'])) + ' bloqueio(s)'}"]
    for b in r['bloqueios']:
        linhas.append(f"  ✘ {b['codigo']} {b['inicio']}s: {b['texto']}")
    for a in r['avisos']:
        linhas.append(f"  ! {a['codigo']} {a['inicio']}s: {a['texto']}")
    linhas.append('  medidas: ' + ', '.join(f'{k}={v}' for k, v in r['deterministico'].items()))
    linhas.append('  estética: ' + r['subjetivo']['estado'])
    return '\n'.join(linhas)
