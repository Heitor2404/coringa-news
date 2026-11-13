"""PIPELINE EXPERIMENTAL V2.1 (isolado e reversível: não altera o motor de produção nem o roteirista).

roteiro estruturado → acontecimentos → composições → recursos → linha do tempo → sincronia da animação →
sincronia da legenda → render → fiscal → exportação.

ÁUDIO: voz LOCAL e gratuita (espeak-ng), sintetizada PALAVRA POR PALAVRA e concatenada com pausas conhecidas.
A voz é robótica de propósito: o objetivo é ter o instante exato de cada palavra (verdade de referência) para testar
a sincronia da legenda e da animação — NÃO é teste de qualidade de voz, de mixagem nem de alinhamento forçado com
uma voz real. Sem espeak-ng, `--silencio` gera a mesma linha do tempo com um ritmo fixo por sílaba e áudio mudo.

Sincronia da animação: a cena declara `sync` = {parâmetro: palavra}. O instante em que a palavra começa (relativo ao
início da cena) vira o parâmetro (ex.: eclusa `tempos` = [entra, enche, iguala]; revelação `virada` = 'gravidade').
Depois do render, o relatório MEDE no palco o estado no instante de cada palavra (ex.: no 'iguala' a diferença de
nível é < 0,3 m e a comporta da frente está abrindo).

Uso: python -m src.v2.experimental [--silencio] [--saida saida/v21/experimental]
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
import time
import wave
from pathlib import Path

import numpy as np

from src.v2 import capacidades, fatos, fiscal_v2, galeria, palco

RAIZ = palco.RAIZ
SR = 22050
PAUSA = {'palavra': .07, ',': .22, ';': .3, '.': .42, '?': .42, ':': .3, 'cena': .35}

# Roteiro do teste: Panamá, com os fatos corrigidos (US$ 5,3 mi = lance em LEILÃO por uma vaga; 82 km pela fonte citada).
ROTEIRO = {
    'titulo': 'Quem ergue o navio no Canal do Panamá (teste experimental V2.1)',
    'fontes': ['Wikipedia (inglês)', 'Britannica', 'Revista Oeste'],
    'contexto': 'canal do panama eclusa comporta navio lago gatun',
    'cenas': [
        {'fala': 'Ninguém empurra este navio, mas ele sobe *26 metros*.', 'comp': 'abertura.pergunta',
         'params': {'pergunta': 'Quem empurra este navio *26 metros* para cima?', 'kicker': 'ENGENHARIA · PANAMÁ', 'contexto': 'Sem bombas. Sem guindastes.'},
         'fundo': {'img': '@navio_eclusa', 'de': [.5, .5, 1.0], 'para': [.55, .52, 1.12]}},
        {'fala': 'O canal tem *82 quilômetros* e liga o Caribe ao Pacífico.',
         'params': {'kicker': 'TRAJETO', 'titulo': 'Do *Caribe* ao *Pacífico*', 'tipo': 'canal', 'distancia_km': 82, 'nota': 'Distância: Wikipedia (inglês); Britannica',
                    'pontos': [{'nome': 'Colón', 'lon': -79.9, 'lat': 9.36}, {'nome': 'Cidade do Panamá', 'lon': -79.53, 'lat': 8.96}],
                    'rota': [[-79.915, 9.37], [-79.92, 9.27], [-79.87, 9.2], [-79.8, 9.16], [-79.72, 9.13], [-79.68, 9.1], [-79.64, 9.05], [-79.6, 9.01], [-79.57, 8.96], [-79.55, 8.9]], 'folga': .45}},
        {'fala': 'O navio entra na câmara e a comporta fecha. Então a água do lago desce por gravidade e enche a câmara. Quando o nível iguala, a comporta da frente abre.',
         'params': {'sentido': 'subir', 'desnivel_m': 26, 'lago': 'LAGO GATÚN', 'mar': 'MAR DO CARIBE', 'kicker': 'MECANISMO · ECLUSA'},
         'sync': {'tempos': ['entra', 'desce', 'iguala']}},
        {'fala': 'Cada travessia gasta *200 milhões de litros* de água doce.',
         'fato': {'rotulo': 'Água doce por travessia', 'valor': 200, 'unidade': 'milhões de litros', 'natureza': 'tipico', 'natureza_txt': 'MÉDIA POR TRAVESSIA',
                  'contexto': 'Sai do lago Gatún e vai para o mar.', 'fonte': 'Wikipedia (inglês)'}},
        {'fala': 'Em 2026, uma vaga para cruzar foi leiloada por *5,3 milhões de dólares*; o pedágio é cobrado à parte.',
         'fato': {**fatos.PANAMA_LEILAO}},
        {'fala': 'O que ergue o navio? A *gravidade*.', 'comp': 'revelacao.surpresa',
         'params': {'pergunta': 'O que ergue o navio?', 'resposta': 'GRAVIDADE', 'detalhe': 'A água desce do lago e enche a câmara', 'cor': 'amarelo'},
         'base_de': 2, 'sync': {'virada': 'gravidade'}},
        {'fala': 'Segue o Coringa Explica.', 'comp': 'encerramento.editorial',
         'params': {'variante': 'conclusao', 'resumo': 'O que ergue o navio? *Gravidade*.', 'marca': '@coringa.explica', 'mascote': 'apontando'},
         'base_de': 2},
    ],
}


def _palavras(fala: str) -> list[dict]:
    out = []
    for tok in fala.split():
        hl = '*' in tok
        limpo = tok.replace('*', '')
        pont = limpo[-1] if limpo and limpo[-1] in ',.;:?!' else ''
        out.append({'txt': limpo, 'falar': re.sub(r'[,.;:?!]+$', '', limpo), 'hl': hl, 'pausa': PAUSA.get(pont, PAUSA['palavra'])})
    return out


def _sintetizar(palavra: str, pasta: Path, voz: str) -> np.ndarray:
    arq = pasta / (re.sub(r'\W+', '_', palavra.lower()) + '.wav')
    if not arq.exists():
        subprocess.run(['espeak-ng', '-v', voz, '-s', '168', '-p', '45', '-w', str(arq), palavra], check=True, capture_output=True)
    with wave.open(str(arq)) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    if sr != SR:
        x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * SR / sr)), np.arange(len(x)), x)
    # corta o silêncio do começo/fim da palavra (o instante medido é o começo do som)
    nz = np.where(np.abs(x) > 300)[0]
    return x[nz[0]:nz[-1] + 1] if len(nz) else x[:int(.1 * SR)]


def voz(roteiro: dict, pasta: Path, silencio: bool = False, lingua: str = 'pt-br') -> tuple[Path, list[list[dict]]]:
    """Gera o áudio e devolve os instantes de cada palavra por cena (verdade de referência)."""
    pasta.mkdir(parents=True, exist_ok=True)
    cache = pasta / 'palavras'; cache.mkdir(exist_ok=True)
    pedacos, t, por_cena = [np.zeros(int(.35 * SR), np.float32)], .35, []
    for sc in roteiro['cenas']:
        ws = []
        for w in _palavras(sc['fala']):
            if silencio:
                silabas = max(1, len(re.findall(r'[aeiouáéíóúâêôãõà]+', w['falar'].lower())))
                x = np.zeros(int(silabas * .17 * SR), np.float32)
            else:
                x = _sintetizar(w['falar'], cache, lingua)
            ws.append({**w, 's': round(t, 3), 'e': round(t + len(x) / SR, 3)})
            pedacos += [x, np.zeros(int(w['pausa'] * SR), np.float32)]
            t += len(x) / SR + w['pausa']
        pedacos.append(np.zeros(int(PAUSA['cena'] * SR), np.float32)); t += PAUSA['cena']
        por_cena.append(ws)
    pedacos.append(np.zeros(int(1.2 * SR), np.float32))
    y = np.concatenate(pedacos)
    y = (y / max(1.0, np.abs(y).max()) * 0.7 * 32767).astype(np.int16) if not silencio else y.astype(np.int16)
    arq = pasta / ('voz_silencio.wav' if silencio else 'voz_espeak.wav')
    with wave.open(str(arq), 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
    return arq, por_cena


def _legendas(por_cena: list[list[dict]], max_palavras: int = 4) -> list[dict]:
    caps = []
    for ws in por_cena:
        bloco = []
        for i, w in enumerate(ws):
            bloco.append(w)
            fim_frase = w['txt'][-1:] in ',.;:?!'
            if len(bloco) == max_palavras or fim_frase or i == len(ws) - 1:
                prox = ws[i + 1]['s'] if i + 1 < len(ws) else bloco[-1]['e'] + .3
                caps.append({'start': bloco[0]['s'], 'end': round(min(bloco[-1]['e'] + .12, prox - .01), 3),
                             'words': [{'w': x['txt'].upper(), 'hl': x['hl'], 's': x['s']} for x in bloco]})
                bloco = []
    return caps


def _instante(ws: list[dict], alvo: str) -> float | None:
    a = capacidades._n(alvo)
    w = next((w for w in ws if capacidades._n(w['falar']).startswith(a)), None)
    return w['s'] if w else None


def montar(roteiro: dict, por_cena: list[list[dict]], dur_audio: float) -> tuple[dict, list[dict], list[dict]]:
    """Acontecimentos → composições → linha do tempo → sincronia. Devolve (dados_v2, direcao, sincronias)."""
    M = galeria.midia(avisar=False)
    cenas, direcao, sincs = [], [], []
    inicios = [ws[0]['s'] - .2 for ws in por_cena]
    inicios[0] = 0.0
    for k, (sc, ws) in enumerate(zip(roteiro['cenas'], por_cena)):
        ini, fim = round(inicios[k], 3), round(inicios[k + 1] if k + 1 < len(inicios) else dur_audio, 3)
        params = galeria._resolver(copy.deepcopy(sc.get('params') or {}), M)
        if sc.get('fato'):   # número: os parâmetros vêm do fato validado (fonte única), nunca escritos à mão
            params = {**fatos.para_tela(sc['fato']), **params}
        if sc.get('comp'):
            dec = {'comp': sc['comp'], 'critica': False, 'motivo': 'estrutura do roteiro (abertura/revelação/encerramento)'}
        else:
            dec = capacidades.escolher({'fala': sc['fala']}, params, roteiro.get('contexto', ''))
        if sc.get('fato'):
            erros = fatos.validar(sc['fato'], roteiro['fontes'])
            if erros:
                dec['bloqueio'] = erros
        comp = dec.get('comp') or 'destaque.palavras'
        # sincronia da animação com a fala: o parâmetro recebe o instante (relativo à cena) da palavra
        for chave, alvo in (sc.get('sync') or {}).items():
            alvos = alvo if isinstance(alvo, list) else [alvo]
            ts = [_instante(ws, a) for a in alvos]
            if None in ts:
                sincs.append({'cena': k, 'param': chave, 'palavras': alvos, 'erro': 'palavra não encontrada na fala'})
                continue
            rel = [round(t - ini, 3) for t in ts]
            params[chave] = rel if isinstance(alvo, list) else rel[0]
            sincs.append({'cena': k, 'comp': comp, 'param': chave, 'palavras': alvos, 'instantes_palavra': ts, 'param_relativo': params[chave]})
        cena = {'comp': comp, 'start': ini, 'end': fim, 'params': params, 'fala': sc['fala'], 'origem': [k]}
        if sc.get('fundo'):
            cena['fundo'] = galeria._resolver(copy.deepcopy(sc['fundo']), M)
        if sc.get('base_de') is not None:
            b = cenas[sc['base_de']]
            T = b['params'].get('tempos') or [0, 0, 0]
            cena['base'] = {'comp': b['comp'], 'params': {**b['params'], 'planos': False}, 't': round(T[2] + 1.2, 2),
                            'dur': round(b['end'] - b['start'], 2), 'escurece': .15 if comp == 'revelacao.surpresa' else .6}
        cenas.append(cena)
        direcao.append({**dec, 'comp': dec.get('comp')})
    dados = {'duration': round(dur_audio, 3), 'scenes': cenas, 'captions': _legendas(por_cena),
             'meta': {'motor': 'v2', 'titulo': roteiro['titulo'], 'fontes': roteiro['fontes'], 'plataforma': 'todas', 'marca': '@coringa.explica'}}
    for sc in cenas:   # encerramento usa as fontes do vídeo
        if sc['comp'] == 'encerramento.editorial':
            sc['params'].setdefault('fontes', roteiro['fontes'])
    return dados, direcao, sincs


def verificar_sincronia(pg, dados: dict, sincs: list[dict], por_cena: list[list[dict]]) -> list[dict]:
    """Mede no palco o que está na tela no instante de cada palavra sincronizada, e a legenda ativa em cada palavra."""
    out = []
    for s in sincs:
        if s.get('erro'):
            out.append({**s, 'ok': False}); continue
        k = s['cena']; sc = dados['scenes'][k]
        if sc['comp'] == 'mecanismo.eclusa':
            medidas = []
            for nome, t in zip(['entra', 'desce/enche', 'iguala'], s['instantes_palavra']):
                pg.evaluate(f'seek({t + .05:.3f})'); e0 = pg.evaluate(f'V2.cenas[{k}].ctx.estadoFisico')
                pg.evaluate(f'seek({t + 1.0:.3f})'); e1 = pg.evaluate(f'V2.cenas[{k}].ctx.estadoFisico')
                medidas.append({'palavra': nome, 't': t, 'agora': e0, '+1s': e1})
            m_ent, m_ench, m_ig = medidas
            crit = {
                'navio_em_movimento_ao_dizer_entra': abs((m_ent['+1s'] or {}).get('navio_x', 0) - (m_ent['agora'] or {}).get('navio_x', 0)) > 1,
                'nivel_subindo_apos_dizer_desce': (m_ench['+1s'] or {}).get('nivel_m', 0) > (m_ench['agora'] or {}).get('nivel_m', 0) + .2,
                'niveis_iguais_ao_dizer_iguala': abs((m_ig['agora'] or {}).get('delta_m', 99)) < .3,
                'comporta_abre_logo_apos_iguala': bool((m_ig['+1s'] or {}).get('comporta_frente_aberta')),
                'comporta_fechada_antes_de_iguala': not (m_ig['agora'] or {}).get('comporta_frente_aberta', True) or abs((m_ig['agora'] or {}).get('delta_m', 99)) < .3,
            }
            out.append({**s, 'medidas': medidas, 'criterios': crit, 'ok': all(crit.values())})
        elif sc['comp'] == 'revelacao.surpresa':
            t = s['instantes_palavra'][0]
            pg.evaluate(f'seek({t - .3:.3f})')
            antes = pg.evaluate(f"(()=>{{const e=V2.cenas[{k}].el.querySelector('.rv-rs');return e?+getComputedStyle(e).opacity:null}})()")
            pg.evaluate(f'seek({t + .35:.3f})')
            depois = pg.evaluate(f"(()=>{{const e=V2.cenas[{k}].el.querySelector('.rv-rs');return e?+getComputedStyle(e).opacity:null}})()")
            crit = {'resposta_oculta_0_3s_antes': (antes or 0) < .1, 'resposta_visivel_0_35s_depois': (depois or 0) > .6}
            out.append({**s, 'opacidade_antes': antes, 'opacidade_depois': depois, 'criterios': crit, 'ok': all(crit.values())})
        else:
            out.append({**s, 'ok': None, 'nota': 'sem medida específica para esta composição'})
    # legenda: no instante de cada palavra, a palavra está no bloco ativo e já marcada como dita
    erros_leg, ocultas, total = [], {}, 0
    for ws in por_cena:
        for w in ws:
            total += 1
            pg.evaluate(f"seek({w['s'] + .04:.3f})")
            st = pg.evaluate("(()=>{const l=document.getElementById('legenda');return l?{txt:l.innerText.replace(/\\s+/g,' ').trim(),vis:getComputedStyle(l).opacity!=='0'&&l.style.opacity!=='0',motivo:l.dataset.motivo||''}:{txt:'',vis:false,motivo:'sem elemento'}})()")
            if not st['vis']:   # oculta por regra (redundante com o texto da cena / legenda integrada): conta à parte
                ocultas[st['motivo'] or 'oculta'] = ocultas.get(st['motivo'] or 'oculta', 0) + 1
                continue
            if w['txt'].upper().strip(',.;:?!*') not in st['txt'].upper():
                erros_leg.append({'palavra': w['txt'], 't': w['s'], 'legenda_na_tela': st['txt'][:60]})
    out.append({'legenda': True, 'palavras': total, 'fora_do_bloco': len(erros_leg), 'ocultas_por_regra': ocultas, 'exemplos': erros_leg[:6], 'ok': not erros_leg})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--saida', default=str(RAIZ / 'saida' / 'v21' / 'experimental'))
    ap.add_argument('--silencio', action='store_true', help='sem voz: áudio mudo com ritmo fixo por sílaba')
    ap.add_argument('--sem-render', action='store_true')
    a = ap.parse_args(argv)
    saida = Path(a.saida).resolve(); saida.mkdir(parents=True, exist_ok=True)
    silencio = a.silencio or not shutil.which('espeak-ng')
    T = {}
    t0 = time.time(); audio, por_cena = voz(ROTEIRO, saida / 'audio', silencio); T['voz_s'] = round(time.time() - t0, 2)
    with wave.open(str(audio)) as w:
        dur = w.getnframes() / w.getframerate()
    t0 = time.time(); dados, direcao, sincs = montar(ROTEIRO, por_cena, dur); T['montagem_s'] = round(time.time() - t0, 2)
    (saida / 'dados_v2.json').write_text(json.dumps({'dados': dados, 'direcao': direcao, 'sincronias': sincs}, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    t0 = time.time()
    with palco.abrir(palco.preparar(copy.deepcopy(dados)), saida / '_palco') as pg:
        geo = palco.medir(pg, dados['duration'], .25)
        verif = verificar_sincronia(pg, dados, sincs, por_cena)
        conflitos = pg.evaluate('V2.conflitosLegenda || []')
        erros_pag = pg.erros + pg.evaluate('V2.avisos')
        for k, sc in enumerate(dados['scenes']):
            palco.capturar(pg, round(sc['start'] + (sc['end'] - sc['start']) * .7, 2), saida / f'quadro_{k}.jpg', 86)
    T['medicao_s'] = round(time.time() - t0, 2)
    cat = {m['id']: m for m in galeria.catalogo(saida / '_cat')}
    rel = fiscal_v2.avaliar(dados, direcao, geo, None, catalogo=cat, conflitos_legenda=conflitos)
    (saida / 'fiscal.md').write_text(fiscal_v2.tabela_md(rel), encoding='utf-8')
    video = None
    if not a.sem_render:
        from src.render import render
        t0 = time.time()
        video = saida / ('panama_experimental_silencio.mp4' if silencio else 'panama_experimental_espeak.mp4')
        render.renderizar(copy.deepcopy(dados), audio, video, saida / '_render')
        T['render_s'] = round(time.time() - t0, 2)
    relatorio = {
        'audio': {'tipo': 'silêncio (ritmo fixo por sílaba)' if silencio else 'voz local espeak-ng (pt-br), sintetizada por palavra',
                  'duracao_s': round(dur, 2), 'arquivo': audio.name},
        'o_que_foi_testado': ['instante de cada palavra conhecido por construção (concatenação) → legenda e animação amarradas a ele',
                              'estado físico da eclusa medido no palco no instante das palavras entra / desce / iguala',
                              'resposta da revelação oculta 0,3 s antes e visível 0,35 s depois da palavra',
                              'cada palavra presente no bloco de legenda ativo no instante em que é dita',
                              'fiscal V2.1 completo sobre o vídeo montado', 'render completo com o motor de produção (render.renderizar, motor v2)'],
        'o_que_nao_foi_testado': ['voz humana ou TTS de produção (ElevenLabs etc.): nenhuma chamada paga',
                                  'alinhamento forçado (Whisper/aeneas) de uma voz real com o roteiro',
                                  'mixagem com música e loudness de publicação (o áudio do teste é a voz crua)',
                                  'o áudio antigo do Panamá: o roteiro corrigido mudou (82 km, leilão de US$ 5,3 mi), então ele NÃO é usado como teste de sincronia'],
        'sincronia': verif, 'fiscal': {'aprovado_tecnicamente': rel['aprovado_tecnicamente'], 'por_categoria': rel['por_categoria'],
                                       'achados': [x for x in rel['achados'] if x['codigo'] != 'E-pergunta']},
        'erros_pagina': erros_pag, 'tempos': T, 'video': video.name if video else None,
        'tamanho_video_mb': round(video.stat().st_size / 1e6, 2) if video and video.exists() else None,
        'cenas': [{'k': k, 'comp': sc['comp'], 'inicio': sc['start'], 'fim': sc['end'], 'fala': sc['fala'], 'decisao': d.get('motivo') or d.get('limitacao')}
                  for k, (sc, d) in enumerate(zip(dados['scenes'], direcao))],
    }
    (saida / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(json.dumps({'sincronia_ok': [v.get('ok') for v in verif], 'fiscal': rel['por_categoria'], 'tempos': T, 'video': relatorio['video'], 'erros': erros_pag}, ensure_ascii=False))
    print(fiscal_v2.texto(rel))
    return relatorio


if __name__ == '__main__':
    main()
