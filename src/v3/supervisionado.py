"""Produção SUPERVISIONADA de referência (V3.1-resgate): executa um storyboard escrito pelo diretor humano/Claude Code
com o MESMO caminho do diretor automático (src/v3/pipeline.aplicar_tempos → src/v2/diretor.montar → palco → render →
fiscal). O storyboard tem o mesmo formato que o modelo produz; as regiões vêm marcadas à mão (`regioes_manuais`) no
lugar da visão. Assim, o que for aprovado aqui vira exemplo direto para o diretor automático.

  python -m src.v3.supervisionado STORYBOARD.json MATERIAL/ SAIDA/ previa|trecho INI FIM|completo
MATERIAL/ contém o que o storyboard cita (checkpoint/arquivos, extra/) e narracao.json + narracao.wav (tempos por palavra).
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from src.v2 import diretor
from src.v3 import pipeline


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def preparar(sb_arq: Path, mat: Path, saida: Path) -> dict:
    from PIL import Image
    from src.v3 import derivados
    sbd = json.loads(Path(sb_arq).read_text(encoding='utf-8'))
    saida.mkdir(parents=True, exist_ok=True)
    acervo, regioes = {}, {}
    for k, x in sbd['acervo'].items():
        arq = mat / x['arq']
        with Image.open(arq) as im:
            wh = list(im.size)
        sha = _sha(arq)
        acervo[k] = {'id': k, 'arq': str(arq), 'wh': wh, 'sha': sha, 'ano': x.get('ano'), 'credito': x['credito'], 'credito_curto': x['credito'][:78],
                     'ia': False, 'uso_comercial': 'sim'}
        regioes[sha] = {'objetos': {n: {'caixa': c, 'visivel': True, 'ancoravel': True, 'confianca': 'alta', 'origem': 'manual-diretor'}
                                    for n, c in (sbd['regioes_manuais'].get(k) or {}).items()}}
    deriv = {}
    for k, d in (sbd.get('derivados') or {}).items():
        dst = saida / f'{k}.jpg'
        if d['funcao'] == 'apagar_cor':
            derivados.apagar_cor(Path(acervo[d['de']]['arq']), tuple(d['rgb']), dst, d.get('tol', 60), preservar=d.get('preservar'))
        deriv[k] = str(dst)
    nar = json.loads((mat / 'narracao.json').read_text(encoding='utf-8'))
    planos = copy.deepcopy(sbd['planos'])
    for pl in planos:
        pl['_falas'] = [nar['falas'][t] for t in pl['trechos']]
        if pl.get('avanco', {}).get('base') in deriv:
            pl['avanco']['base'] = deriv[pl['avanco']['base']]
    sb = {'planos': planos}
    palavras = diretor.palavras_da_narracao(nar['caps'])
    tempos = [tuple(t) for t in nar['tempos']]
    avisos = pipeline.aplicar_tempos(sb, tempos, palavras, nar['dur'])
    cenas, reg = diretor.montar(sb, acervo, regioes, palavras, set())
    criticos = set(sbd.get('criticos') or [])
    for r, pl in zip(reg, sb['planos']):
        r['critico'] = r.get('evento_id') in criticos
        r['trechos'] = pl.get('trechos')
    dados = {'duration': nar['dur'], 'meta': {'motor': 'v2', 'plataforma': 'todas', 'titulo': sbd['episodio'], 'categoria': 'historia',
                                              'serie': 'coringa', 'parte': 0, 'marca': '@coringa.explica', 'pergunta': sbd.get('pergunta', ''), 'fontes': []},
             'scenes': cenas, 'captions': nar['caps']}
    out = {'sb': sb, 'reg': reg, 'dados': dados, 'avisos': avisos, 'acervo': acervo, 'nar': nar, 'audio': mat / nar['audio'],
           'musica': Path(sbd['musica']) if sbd.get('musica') else None, 'storyboard': sbd}
    (saida / 'direcao.json').write_text(json.dumps({'storyboard_usado': sb, 'registro': reg, 'avisos': avisos}, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    (saida / 'v2_dados.json').write_text(json.dumps(dados, ensure_ascii=False, default=str), encoding='utf-8')
    return out


def previa(p: dict, saida: Path, por_plano: int = 4) -> dict:
    """Quadros por plano (início → fim) no palco, sem MP4 — enquadramento, anotação, avanço, legibilidade."""
    from src.v2 import palco
    from PIL import Image
    dados, erros, geo = p['dados'], [], []
    with palco.abrir(palco.preparar(copy.deepcopy(dados)), saida / '_palco') as pg:
        geo = palco.medir(pg, dados['duration'], .5)
        for k, sc in enumerate(dados['scenes']):
            ims = []
            for f in [.06 + .88 * j / (por_plano - 1) for j in range(por_plano)]:
                q = saida / f'_q{k:02d}_{int(f * 100)}.jpg'
                palco.capturar(pg, round(sc['start'] + (sc['end'] - sc['start']) * f, 2), q, 80)
                ims.append(Image.open(q).resize((270, 480)))
                q.unlink()
            tira = Image.new('RGB', (270 * por_plano + 6 * (por_plano - 1), 480), 'black')
            for j, im in enumerate(ims):
                tira.paste(im, (j * 276, 0))
            tira.save(saida / f'previa_{k:02d}.jpg', quality=82)
        erros = list(pg.erros) + list(pg.evaluate('V2.avisos') or [])
        cam = pipeline._camera(pg, dados)
    graves = pipeline._choques({'problemas_geometria': geo}, dados)
    res = {'erros_pagina': erros, 'choques_graves': graves, 'geometria': len(geo), 'camera': cam,
           'degradacoes': [{'plano': i, **d} for i, r in enumerate(p['reg']) for d in r.get('degradacoes') or []]}
    (saida / 'previa.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return res


def trecho(p: dict, ini: float, fim: float, saida: Path) -> Path:
    """Trecho curto ANIMADO (vídeo + narração) para conferir movimento, avanço, sincronia — sem o vídeo inteiro."""
    from src.render import render
    d = copy.deepcopy(p['dados'])
    cen = []
    for sc in d['scenes']:
        if sc['end'] <= ini or sc['start'] >= fim:
            continue
        sc = dict(sc)
        corte = max(0.0, ini - sc['start'])
        if corte:                                   # o plano começa antes do trecho: desloca a timeline interna
            sc['_t_off'] = corte
        sc['start'], sc['end'] = max(0.0, sc['start'] - ini), min(fim, sc['end']) - ini
        cen.append(sc)
    d['scenes'] = cen
    d['duration'] = fim - ini
    d['captions'] = [{**c, 'start': c['start'] - ini, 'end': c['end'] - ini,
                      'words': [{**w, 's': w['s'] - ini} for w in c.get('words') or []]} for c in d['captions'] if c['end'] > ini and c['start'] < fim]
    aud = saida / f'_aud_{ini:.0f}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ini), '-t', str(fim - ini), '-i', str(p['audio']), str(aud)], check=True)
    out = saida / f'trecho_{ini:05.1f}-{fim:05.1f}.mp4'
    render.renderizar(d, aud, out, saida / '_render_trecho', musica=None)
    return out


def completo(p: dict, saida: Path, nome: str) -> dict:
    from src.render import render
    from src.v3 import fiscal_editorial, revisao_multimodal, plano_av
    t0 = time.time()
    mp4 = saida / f'{nome}.mp4'
    render.renderizar(copy.deepcopy(p['dados']), p['audio'], mp4, saida / '_render', musica=p['musica'])
    t_render = time.time() - t0
    sbd = p['storyboard']
    evs = [{'id': e, 'tipo': t, 'critico': e in set(sbd.get('criticos') or []), 'trechos': tr, 'viaveis': []}
           for e, t, tr in sbd.get('eventos') or []]
    v = {'fatos': sbd.get('fatos_texto', ''), 'cenas': [{'fala': f} for f in p['nar']['falas']]}
    fis = fiscal_editorial.avaliar(mp4, p['dados'], p['reg'], {'eventos': evs}, v, None)
    for i, r in enumerate(p['reg']):
        for d in r.get('degradacoes') or []:
            if d['impacto'] != 'aceitavel':
                fis['achados'].append({'classe': d['impacto'], 'dimensao': 'semantica' if d['essencial'] else 'tecnica', 'codigo': 'D-' + d['codigo'],
                                       'problema': f"plano {i}: {d['texto']}", 'inicio': r['tempo'][0], 'fim': r['tempo'][1], 'plano': i, 'evidencia': ''})
    fichas = [{'evento_id': e['id'], 'tipo': e['tipo'], 'critico': e['critico'],
               'representacao_necessaria': plano_av.REPRESENTACAO.get(e['tipo'], plano_av.PADRAO)[0],
               'criterio_visual': plano_av.REPRESENTACAO.get(e['tipo'], plano_av.PADRAO)[1]} for e in evs]
    rv = revisao_multimodal.revisar(mp4, p['dados'], fichas, None, saida / 'tiras')
    revisao_multimodal.gravar(rv, saida / 'revisao_multimodal.json')
    (saida / 'fiscal.json').write_text(json.dumps(fis, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    (saida / 'fiscal.md').write_text(fiscal_editorial.texto(fis), encoding='utf-8')
    fiscal_editorial.folha_contato(mp4, p['dados'], saida / 'folha_contato.jpg')
    return {'mp4': str(mp4), 'render_s': round(t_render, 1), 'fiscal': fis['resumo']}


if __name__ == '__main__':
    sb_arq, mat, out, modo = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    p = preparar(sb_arq, mat, out)
    if modo == 'previa':
        print(json.dumps(previa(p, out), ensure_ascii=False, indent=1, default=str)[:4000])
    elif modo == 'trecho':
        print(trecho(p, float(sys.argv[5]), float(sys.argv[6]), out))
    else:
        print(json.dumps(completo(p, out, sys.argv[5] if len(sys.argv) > 5 else 'londres_1666_referencia'), ensure_ascii=False, indent=1, default=str))
