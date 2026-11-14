"""PILOTO DE PRODUÇÃO V2.2 (experimental, isolado e reversível).

Liga o motor visual V2.2 ao fluxo REAL do Coringa (main.py: pesquisa → roteirista → acervo → voz → cenas) só quando
MOTOR_VISUAL=v2. Sem a variável, nada muda: main.py chama o render atual. Este módulo NÃO escolhe composições nem
mexe em cenas: entrega as cenas do fluxo real a montagem.converter (seletor + contrato), mede no palco, renderiza
1080×1920 e roda o fiscal V2.2. O resultado do fiscal é registrado; bloqueio não é escondido nem corrigido.

Saídas (em <pasta>/<nome>-piloto/): v1_cenas.json (o que o fluxo real entregou), v2_dados.json, direcao.json (decisão do
seletor por cena), fiscal.json / fiscal.md, quadros por cena, relatorio.json (tempos, memória, áudio, erros da página).
"""
from __future__ import annotations

import copy
import json
import re
import resource
import subprocess
import time
from pathlib import Path


def _lufs(arq: Path) -> dict:
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(arq), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); tp = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
    return {'lufs': float(i[-1]) if i else None, 'pico_dbtp': float(tp[-1]) if tp else None}


def _sincronia(dados: dict) -> list[dict]:
    """Contrato 'sincronia' → instantes das palavras ditas (legendas da voz de produção). Mesmo passo do inedito.py."""
    from src.v2 import contrato
    ws = [w for c in dados.get('captions', []) for w in c.get('words', [])]
    out = []
    for k, sc in enumerate(dados['scenes']):
        ac = sc.get('acontecimento')
        if isinstance(ac, dict) and ac.get('sincronia'):
            pal = [{'w': w['w'], 's': w['s']} for w in ws if sc['start'] - .05 <= w['s'] < sc['end']]
            sc['acontecimento'] = contrato.resolver_sincronia(ac, pal, sc['start'])
            out.append({'cena': k, 'sincronia': ac.get('sincronia'), 'faltou': sc['acontecimento'].get('sincronia_faltou')})
    return out


def renderizar(dados: dict, audio: Path, saida: Path, trab: Path, musica: Path | None, pasta: Path, nome: str) -> dict:
    from src.render import render
    from src.v2 import fiscal_v2, galeria, montagem, palco
    dest = pasta / f'{nome}-piloto'
    dest.mkdir(parents=True, exist_ok=True)
    T, erros = {}, []
    d1 = copy.deepcopy(dados)
    (dest / 'v1_cenas.json').write_text(json.dumps(d1, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    sinc = _sincronia(d1)
    t0 = time.time()
    v2, direcao = montagem.converter(d1)
    v2['meta'].update(motor='v2', plataforma='todas')
    T['selecao_montagem_s'] = round(time.time() - t0, 2)
    (dest / 'v2_dados.json').write_text(json.dumps(v2, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    (dest / 'direcao.json').write_text(json.dumps(direcao, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print('  [piloto V2.2] composições: ' + ' · '.join(f"{sc['comp']}({d.get('origem') or '-'})" for sc, d in zip(v2['scenes'], direcao)))
    t0 = time.time()
    geo, conflitos, vis = [], [], []
    try:
        with palco.abrir(palco.preparar(copy.deepcopy(v2)), trab / '_palco_v2') as pg:
            geo = palco.medir(pg, v2['duration'], .25)
            conflitos = pg.evaluate('V2.conflitosLegenda || []')
            erros = list(pg.erros) + list(pg.evaluate('V2.avisos') or [])
            tempos_pg = pg.evaluate('V2.TEMPOS || null')
            for k, sc in enumerate(v2['scenes']):
                pg.evaluate(f"seek({(sc['start'] + sc['end']) / 2:.3f})")
                if pg.evaluate(f"(()=>{{const e=V2.cenas[{k}] && V2.cenas[{k}].el;return !!e && getComputedStyle(e).visibility!=='hidden' && e.querySelectorAll('*').length>0}})()"):
                    vis.append(k)
                palco.capturar(pg, round(sc['start'] + (sc['end'] - sc['start']) * .7, 2), dest / f'quadro_{k:02d}.jpg', 88)
    except Exception as e:                       # medição falhou: registra e segue para o render (não esconde)
        erros.append(f'medição no palco falhou: {str(e)[:300]}'); tempos_pg = None
    T['medicao_s'] = round(time.time() - t0, 2)
    cat = {m['id']: m for m in galeria.catalogo(trab / '_cat_v2')}
    t0 = time.time()
    perf, audio_med, erro_render = {}, {}, None
    try:
        render.renderizar(copy.deepcopy(v2), audio, saida, trab / '_render_v2', musica=musica)
        perf = {'render_s': round(time.time() - t0, 1),
                'pico_memoria_mb_filhos': round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024),
                'tamanho_mb': round(saida.stat().st_size / 1e6, 2)}
        audio_med = _lufs(saida)
    except Exception as e:
        erro_render = f'{type(e).__name__}: {str(e)[:500]}'
        perf = {'render_s': round(time.time() - t0, 1), 'erro': erro_render}
    rel = fiscal_v2.avaliar(v2, direcao, geo, d1, audio=audio_med or None, catalogo=cat, conflitos_legenda=conflitos, renderizadas=vis)
    (dest / 'fiscal.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    (dest / 'fiscal.md').write_text(fiscal_v2.tabela_md(rel), encoding='utf-8')
    relatorio = {'tempos': T, 'desempenho_render': perf, 'audio': audio_med, 'sincronia_contrato': sinc, 'erros_pagina': erros,
                 'preparacao_pagina_ms': tempos_pg, 'resolucao': '1080x1920',
                 'cenas': [{'k': k, 'comp': sc['comp'], 'inicio': sc['start'], 'fim': sc['end'], 'fala': (sc.get('fala') or '')[:120],
                            'origem': d.get('origem'), 'decisao': d.get('motivo') or d.get('limitacao'), 'sem_contrato': d.get('sem_contrato'),
                            'faltam': d.get('faltam'), 'substituicao': d.get('substituicao')} for k, (sc, d) in enumerate(zip(v2['scenes'], direcao))],
                 'fiscal': {'aprovado_tecnicamente': rel.get('aprovado_tecnicamente'), 'aprovacao_automatica': rel.get('aprovacao_automatica'),
                            'por_categoria': rel.get('por_categoria')}}
    (dest / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(fiscal_v2.texto(rel))
    if erro_render:
        raise RuntimeError(f'piloto V2.2: render falhou ({erro_render})')
    bloq = [a for a in rel.get('achados', []) if a.get('gravidade') == 'bloqueio']
    return {'relatorio': relatorio, 'bloqueios': [f"{a['codigo']} cena {a.get('cena')}: {a.get('problema')}" for a in bloq],
            'aprovacao_automatica': rel.get('aprovacao_automatica')}
