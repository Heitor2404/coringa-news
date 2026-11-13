"""PONTA A PONTA COM ASSUNTO INÉDITO E NARRAÇÃO HUMANA REAL (V2.2) — Venezuela.

Diferente de experimental.py (composições, coordenadas e tempos preparados à mão para o Panamá), aqui o motor recebe
só o que o roteirista entregaria e decide o resto. Cada etapa diz se rodou o código real ou uma fixture:

  1 roteirista ............ FIXTURE (tests/midia/roteiro_venezuela.json): a etapa real chama um modelo pago; a fixture
                            reproduz o contrato de saída (falas + acontecimento declarado + fatos com fonte)
  2 normalização .......... real (acontecimentos.normalizar → contrato.normalizar)
  3 alinhamento ........... real: texto do roteiro × instantes da fala HUMANA (faster-whisper rodado no Actions;
                            o reconhecimento erra palavras — o alinhamento por sequência absorve)
  4 edição da narração .... real: trechos do áudio original recortados nas fronteiras de palavra (pausas naturais
                            mantidas dentro dos trechos); o que o roteiro não usa (ranking garbled) fica fora
  5 acervo ................ real (acervo_v2.escolher) sobre um acervo LOCAL de fotos reais licenciadas (tests/midia);
                            a busca no Commons do acervo de produção não roda aqui (sem internet nesta máquina)
  6 seleção + montagem .... real (montagem.converter → capacidades.escolher pelo contrato)
  7 sincronia ............. real: legenda pelos instantes alinhados; cortes de cena nas fronteiras de fala
  8 render ................ real, 1080×1920, com música de teste SINTETIZADA aqui (sem licença a verificar) abaixando
                            sob a voz, masterização −14 LUFS do motor de produção
  9 fiscal ................ real (fiscal_v2 + geometria do palco + loudness medido no arquivo final)
 10 exportação ............ mp4 + relatório

Uso: python -m src.v2.inedito [--sem-render] [--saida saida/v22/inedito]
"""
from __future__ import annotations

import argparse
import copy
import difflib
import json
import re
import subprocess
import time
import unicodedata
import wave
from pathlib import Path

import numpy as np

from src import acontecimentos
from src.v2 import acervo_v2, fiscal_v2, galeria, montagem, palco

RAIZ = palco.RAIZ
M = RAIZ / 'tests' / 'midia'
ETAPAS = [('roteirista', 'fixture'), ('normalização', 'real'), ('alinhamento', 'real'), ('edição da narração', 'real'), ('acervo', 'real (acervo local)'),
          ('seleção + montagem', 'real'), ('sincronia', 'real'), ('render 1080×1920', 'real'), ('fiscal', 'real'), ('exportação', 'real')]


def _tok(s: str) -> str:
    s = unicodedata.normalize('NFKD', s.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in s if not unicodedata.combining(c)))


def alinhar(palavras_roteiro: list[str], asr: list[dict]) -> list[dict]:
    """Cada palavra do roteiro recebe o instante da palavra reconhecida correspondente (SequenceMatcher sobre os tokens
    normalizados). Palavras não reconhecidas (erro do ASR) são interpoladas entre as vizinhas casadas."""
    a = [_tok(w) for w in palavras_roteiro]
    b = [_tok(w['w']) for w in asr]
    t = [None] * len(a)
    for bl in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(bl.size):
            t[bl.a + k] = (asr[bl.b + k]['s'], asr[bl.b + k]['e'])
    casadas = [i for i, x in enumerate(t) if x]
    for i in range(len(t)):
        if t[i]:
            continue
        ant = max((j for j in casadas if j < i), default=None); pos = min((j for j in casadas if j > i), default=None)
        if ant is not None and pos is not None:
            s0, s1 = t[ant][1], t[pos][0]; n = pos - ant
            f = (i - ant) / n
            t[i] = (s0 + (s1 - s0) * (f - 1 / n / 2), s0 + (s1 - s0) * f)
        elif ant is not None:
            t[i] = (t[ant][1] + .05, t[ant][1] + .3)
        else:
            t[i] = (max(0, t[pos][0] - .3), t[pos][0] - .05)
    return [{'w': w, 's': round(x[0], 3), 'e': round(x[1], 3), 'casada': i in casadas} for i, (w, x) in enumerate(zip(palavras_roteiro, t))]


def _musica(arq: Path, dur: float):
    """Fundo musical de teste SINTETIZADO (acordes lentos, sem licença a verificar)."""
    sr = 48000; t = np.arange(int(sr * dur)) / sr; y = np.zeros_like(t)
    acordes = [(220, 261.6, 329.6), (196, 246.9, 293.7), (174.6, 220, 261.6), (196, 246.9, 329.6)]
    for k, ac in enumerate(acordes * int(dur // 16 + 1)):
        t0 = k * 4.0
        if t0 >= dur:
            break
        m = (t >= t0) & (t < t0 + 4.4)
        env = np.clip(np.minimum((t[m] - t0) / .8, (t0 + 4.4 - t[m]) / .8), 0, 1)
        for f in ac:
            y[m] += np.sin(2 * np.pi * f * t[m]) * env * .08
    y = (y / max(1e-9, np.abs(y).max()) * .35 * 32767).astype(np.int16)
    with wave.open(str(arq), 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


def _acervo_local() -> list[dict]:
    """Fotos reais do diretório de fixtures, com título/descrição/licença da API do Commons gravados no download."""
    out = []
    for js in sorted(M.glob('foto_*.json')) + sorted(M.glob('documento_*.json')):
        j = json.loads(js.read_text(encoding='utf-8'))
        arq = M / (j.get('fixture') or {}).get('arquivo', js.stem + '.jpg')
        if not arq.exists():
            continue
        titulo = re.sub(r'^File:|\.\w+$', '', j.get('titulo') or '')
        out.append({'id': str(arq), 'titulo': titulo, 'descricao': j.get('descricao') or '', 'licenca': j.get('licenca'),
                    'credito': ((j.get('autor') or '').split('\n')[0][:40] + ' · ' + (j.get('licenca') or '')).strip(' ·'),
                    'busca': titulo, 'ano': (re.search(r'(1[5-9]\d\d|20\d\d)', j.get('data') or '') or [None])[0]})
    return out


def montar(saida: Path) -> dict:
    rot = json.loads((M / 'roteiro_venezuela.json').read_text(encoding='utf-8'))
    asr = json.loads((M / 'voz_venezuela.palavras.json').read_text(encoding='utf-8'))['palavras']
    # 2 normalização (real)
    v = acontecimentos.normalizar({'cenas': [{'tipo': 'historia', 'fala': c['fala'], 'acontecimento': c['acontecimento']} for c in rot['cenas']]})
    # 3 alinhamento (real) — roteiro inteiro × reconhecimento
    pal = [w for c in rot['cenas'] for w in c['fala'].split()]
    ali = alinhar(pal, asr)
    k, trechos = 0, []
    for c in rot['cenas']:
        n = len(c['fala'].split()); ws = ali[k:k + n]; k += n
        trechos.append(ws)
    # 4 edição da narração (real): trechos CONTÍGUOS na leitura original viram uma peça só (pausa natural mantida);
    #   só há corte onde o roteiro pula parte da leitura — aí entra uma pausa de 0,35 s. Nunca repete áudio.
    saida.mkdir(parents=True, exist_ok=True)
    pecas, atual = [], None
    for i, ws in enumerate(trechos):
        if atual and ws[0]['s'] - atual['fim_bruto'] < 1.0:
            atual['segs'].append(i); atual['fim_bruto'] = ws[-1]['e']
        else:
            atual = {'segs': [i], 'ini_bruto': ws[0]['s'], 'fim_bruto': ws[-1]['e']}; pecas.append(atual)
    voz = saida / 'narracao.wav'; ent, fil, novo, t = [], [], [None] * len(trechos), 0.0
    for k, pc in enumerate(pecas):
        a0 = max(0.0, pc['ini_bruto'] - .12)
        a1 = pc['fim_bruto'] + .25
        if k + 1 < len(pecas):
            a1 = min(a1, pecas[k + 1]['ini_bruto'] - .12)
        ent += ['-ss', f'{a0:.3f}', '-t', f'{a1 - a0:.3f}', '-i', str(M / 'voz_venezuela.ogg')]
        fil.append(f'[{k}:a]aresample=48000,afade=t=in:d=0.03,afade=t=out:st={max(0, a1 - a0 - .06):.3f}:d=0.06,apad=pad_dur={.35 if k + 1 < len(pecas) else 0}[t{k}]')
        for i in pc['segs']:
            novo[i] = [{**w, 's': round(w['s'] - a0 + t, 3), 'e': round(w['e'] - a0 + t, 3)} for w in trechos[i]]
        t += (a1 - a0) + (.35 if k + 1 < len(pecas) else 0)
    fil.append(''.join(f'[t{k}]' for k in range(len(pecas))) + f'concat=n={len(pecas)}:v=0:a=1[voz]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ent, '-filter_complex', ';'.join(fil), '-map', '[voz]', '-ac', '1', str(voz)], check=True)
    cortes = [{'peca': k, 'original_s': [round(max(0.0, pc['ini_bruto'] - .12), 2), round(pc['fim_bruto'] + .25, 2)], 'cenas': pc['segs']} for k, pc in enumerate(pecas)]
    fim_fala = t
    # 5 acervo (real, acervo local): só cenas cujo contrato pede foto/lugar
    acervo = _acervo_local()
    precisam = [i for i, c in enumerate(v['cenas']) if c['acontecimento'].get('tipo') in ('lugar', 'pessoa', 'ambiente', 'evento_historico')]
    esc = acervo_v2.escolher([{**v['cenas'][i], 'mostrar': v['cenas'][i]['acontecimento'].get('mostrar', '')} for i in precisam], acervo)
    img = {precisam[e['cena']]: e for e in esc}
    # 6 dados V1 → montagem real
    cenas, caps = [], []
    for i, (c, ws) in enumerate(zip(v['cenas'], novo)):
        ini = 0.0 if i == 0 else round(ws[0]['s'] - .12, 3)
        fim = round(novo[i + 1][0]['s'] - .12, 3) if i + 1 < len(novo) else round(fim_fala, 3)
        from src.v2 import contrato
        acont = contrato.resolver_sincronia(c['acontecimento'], ws, ini) if c['acontecimento'].get('sincronia') else c['acontecimento']
        sc = {'tipo': 'historia', 'fala': c['fala'], 'start': ini, 'end': fim, 'acontecimento': acont, 'grupo': f'g{i}',
              'mostrar': c['acontecimento'].get('mostrar', ''), 'lugar': c['acontecimento'].get('onde', '')}
        e = img.get(i)
        if e and e.get('img'):
            sc['img'] = e['img']; it = next(x for x in acervo if x['id'] == e['img']); sc['credito'] = it['credito']
        cenas.append(sc)
        bloco = []
        for j, w in enumerate(ws):            # legenda: ≤ 4 palavras, fecha em pontuação; instantes da voz humana
            bloco.append(w)
            if len(bloco) == 4 or w['w'][-1:] in ',.;:?!' or j == len(ws) - 1:
                prox = ws[j + 1]['s'] if j + 1 < len(ws) else bloco[-1]['e'] + .3
                caps.append({'start': bloco[0]['s'], 'end': round(min(bloco[-1]['e'] + .12, prox - .01), 3),
                             'words': [{'w': x['w'].upper(), 's': x['s']} for x in bloco]}); bloco = []
    for a, b in zip(caps, caps[1:]):          # bloco final de uma cena não pode invadir o primeiro da seguinte
        a['end'] = round(min(a['end'], b['start'] - .01), 3)
    dur = round(fim_fala + 3.0, 3)
    cenas.append({'tipo': 'fechamento', 'fala': '', 'start': round(fim_fala, 3), 'end': dur, 'resumo': rot['fechamento']['resumo']})
    meta = {'titulo': rot['titulo'], 'fontes': rot['fontes'] + [rot['creditos_audio']], 'marca': '@coringa.explica'}
    d1 = {'duration': dur, 'meta': meta, 'scenes': cenas, 'captions': caps}
    v2, direcao = montagem.converter(d1)
    v2['meta'].update(motor='v2', plataforma='todas')
    return {'d1': d1, 'v2': v2, 'direcao': direcao, 'voz': voz, 'alinhamento': ali, 'acervo': esc, 'acervo_local': acervo, 'trechos': novo, 'fim_fala': fim_fala, 'cortes': cortes}


def _lufs(arq: Path) -> dict:
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(arq), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); tp = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
    return {'lufs': float(i[-1]) if i else None, 'pico_dbtp': float(tp[-1]) if tp else None}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--saida', default=str(RAIZ / 'saida' / 'v22' / 'inedito')); ap.add_argument('--sem-render', action='store_true')
    a = ap.parse_args(argv); saida = Path(a.saida).resolve(); saida.mkdir(parents=True, exist_ok=True)
    T = {}; t0 = time.time()
    r = montar(saida); T['montagem_s'] = round(time.time() - t0, 2)
    v2, direcao, d1 = r['v2'], r['direcao'], r['d1']
    from src.v2 import experimental
    t0 = time.time()
    with palco.abrir(palco.preparar(copy.deepcopy(v2)), saida / '_palco') as pg:
        geo = palco.medir(pg, v2['duration'], .25)
        verif = experimental.verificar_sincronia(pg, v2, [], [[{'txt': w['w'], 's': w['s']} for w in ws] for ws in r['trechos']])
        conflitos = pg.evaluate('V2.conflitosLegenda || []'); erros = pg.erros + pg.evaluate('V2.avisos')
        vis = [k for k, sc in enumerate(v2['scenes']) if (pg.evaluate(f"seek({(sc['start'] + sc['end']) / 2:.3f})") or True)
               and pg.evaluate(f"(()=>{{const e=V2.cenas[{k}].el;return e && getComputedStyle(e).visibility!=='hidden' && e.querySelectorAll('*').length>0}})()")]
        for k, sc in enumerate(v2['scenes']):
            palco.capturar(pg, round(sc['start'] + (sc['end'] - sc['start']) * .7, 2), saida / f'quadro_{k}.jpg', 88)
    T['medicao_s'] = round(time.time() - t0, 2)
    cat = {m['id']: m for m in galeria.catalogo(saida / '_cat')}
    rel = fiscal_v2.avaliar(v2, direcao, geo, d1, catalogo=cat, conflitos_legenda=conflitos, renderizadas=vis)
    video, perf, audio = None, {}, {}
    if not a.sem_render:
        from src.render import render
        musica = saida / 'musica_sintetizada.wav'; _musica(musica, v2['duration'] + 2)
        import resource
        t0 = time.time()
        video = saida / 'venezuela_1080x1920.mp4'
        render.renderizar(copy.deepcopy(v2), r['voz'], video, saida / '_render', musica=musica)
        perf = {'render_s': round(time.time() - t0, 1), 'pico_memoria_mb_filhos': round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024),
                'tamanho_mb': round(video.stat().st_size / 1e6, 2)}
        audio = _lufs(video)
        rel = fiscal_v2.avaliar(v2, direcao, geo, d1, audio=audio, catalogo=cat, conflitos_legenda=conflitos, renderizadas=vis)
    casadas = sum(1 for w in r['alinhamento'] if w['casada'])
    relatorio = {
        'etapas': [{'etapa': e, 'execucao': x} for e, x in ETAPAS],
        'alinhamento': {'palavras_roteiro': len(r['alinhamento']), 'casadas_com_o_reconhecimento': casadas,
                        'interpoladas': len(r['alinhamento']) - casadas, 'reconhecimento': 'faster-whisper small (int8), português'},
        'edicao_narracao': r['cortes'], 'acervo': r['acervo'], 'cenas': [{'k': k, 'comp': sc['comp'], 'inicio': sc['start'], 'fim': sc['end'], 'fala': sc.get('fala', '')[:90],
                                         'decisao': (d.get('motivo') or d.get('limitacao') or '')[:140], 'origem': d.get('origem')}
                                        for k, (sc, d) in enumerate(zip(v2['scenes'], direcao))],
        'sincronia': verif, 'fiscal': {'aprovado_tecnicamente': rel['aprovado_tecnicamente'], 'aprovacao_automatica': rel['aprovacao_automatica'],
                                       'por_categoria': rel['por_categoria'], 'achados': [x for x in rel['achados'] if x['codigo'] != 'E-pergunta']},
        'audio': {**audio, 'narracao': 'voz humana real (Wilfredor, CC0), recortada em 5 trechos', 'musica': 'sintetizada localmente',
                  'registro': v2.get('registro_audio')},
        'erros_pagina': erros, 'tempos': T, 'desempenho_render': perf, 'video': video.name if video else None,
        'nao_testado': ['etapa do roteirista com modelo de linguagem (fixture no lugar)', 'busca de acervo no Commons em produção (acervo local no lugar)',
                        'voz de produção do canal (a voz é humana real, mas de outro locutor)'],
    }
    (saida / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    (saida / 'fiscal.md').write_text(fiscal_v2.tabela_md(rel), encoding='utf-8')
    print(json.dumps({'cenas': [(c['comp'], c['origem']) for c in relatorio['cenas']], 'alinhamento': relatorio['alinhamento'], 'sincronia_ok': [x.get('ok') for x in verif],
                      'audio': audio, 'perf': perf, 'tempos': T, 'erros': erros}, ensure_ascii=False))
    print(fiscal_v2.texto(rel))
    return relatorio


if __name__ == '__main__':
    main()
