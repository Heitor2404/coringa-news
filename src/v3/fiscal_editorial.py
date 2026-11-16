"""Fiscal V3.1 — técnico + editorial, por evidência. Três classes de achado:

- bloqueio:  objetivo e verificável (pergunta central sem resposta, número fora da pesquisa, licença não liberada,
             foto de IA, loudness fora da meta, MP4 com duração errada, crítico sem plano);
- revisao:   provável defeito que pede olho humano (objeto principal não localizado, plano sem direção de atenção,
             trecho parado longo, corte inesperado dentro de um plano, área vazia, texto que só repete a fala);
- estetica:  preferência (transições repetidas, ritmo uniforme, planos longos).

Usa as medidas do fiscal audiovisual V3 (src/v2/fiscal_av.py), FFmpeg (loudness) e PySceneDetect (cortes reais × cortes
planejados). A presença do id de um acontecimento no storyboard NÃO comprova cobertura: o plano precisa ter virado cena,
com mídia válida, e o tipo de representação precisa servir ao tipo do acontecimento. Qualidade artística continua humana.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

LUFS_META, LUFS_TOL = -14.0, 1.0
PLANO_LONGO_S = 7.0
DETECTOR_LIMIAR = 27.0        # ContentDetector (padrão 27); calibrado em docs/v3/CALIBRACAO_CENAS.md
TOL_CORTE_S = 0.35


def _lufs(mp4: Path) -> dict:
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(mp4), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', r)
    tp = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
    return {'lufs': float(i[-1]) if i else None, 'pico_dbtp': float(tp[-1]) if tp else None}


def _sonda(mp4: Path) -> dict:
    import json
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height,r_frame_rate',
                        '-of', 'json', str(mp4)], capture_output=True, text=True)
    d = json.loads(r.stdout or '{}')
    v = next((s for s in d.get('streams', []) if s.get('codec_type') == 'video'), {})
    return {'duracao': float((d.get('format') or {}).get('duration') or 0), 'largura': v.get('width'), 'altura': v.get('height'),
            'fps': v.get('r_frame_rate'), 'tem_audio': any(s.get('codec_type') == 'audio' for s in d.get('streams', []))}


def cortes(mp4: Path, limiar: float = DETECTOR_LIMIAR) -> list[float]:
    """Instantes de corte detectados (PySceneDetect, ContentDetector). Dissolve longo pode não aparecer: é esperado."""
    try:
        from scenedetect import ContentDetector, detect
    except Exception:
        return []
    cenas = detect(str(mp4), ContentDetector(threshold=limiar, min_scene_len=6), show_progress=False)
    return [round(float(getattr(a, "seconds", None) if not callable(getattr(a, "seconds", None)) and getattr(a, "seconds", None) is not None else a.get_seconds()), 2) for a, _ in cenas[1:]]


TRANS_D = {'corte': 0, 'mascara': .42, 'deslize': .38, 'zoom': .34, 'flash': .26, 'preto': .5, 'dissolve': .5, 'whip': .55, 'iris': .6}


def comparar_cortes(detectados: list[float], planejados: list, tol: float = TOL_CORTE_S) -> dict:
    """Corte planejado achado no vídeo (acerto) × corte no vídeo sem plano correspondente (inesperado). `planejados`:
    instantes ou (instante, duração da transição) — a mudança pode ser detectada em qualquer ponto da transição."""
    pj = [(p, 0.0) if isinstance(p, (int, float)) else (float(p[0]), float(p[1])) for p in planejados]
    perto = lambda p, d, dt: p - tol <= d <= p + dt + tol      # noqa: E731
    acertos = [p for p, dt in pj if any(perto(p, d, dt) for d in detectados)]
    inesperados = [d for d in detectados if not any(perto(p, d, dt) for p, dt in pj)]
    planejados = [p for p, _ in pj]
    return {'planejados': planejados, 'detectados': detectados, 'acertos': len(acertos),
            'recall': round(len(acertos) / len(planejados), 2) if planejados else None, 'inesperados': inesperados}


def avaliar(mp4: Path, dados: dict, registro: list[dict], ctx: dict, v: dict, sreg: dict | None = None) -> dict:
    from src.v2 import contrato, fiscal_av
    cenas = dados['scenes']
    ach = []

    def a(classe, codigo, problema, inicio=None, fim=None, plano=None, evidencia=''):
        ach.append({'classe': classe, 'codigo': codigo, 'problema': problema, 'inicio': inicio, 'fim': fim, 'plano': plano, 'evidencia': evidencia})

    # ---------------- técnico
    so = _sonda(mp4)
    if (so['largura'], so['altura']) != (1080, 1920):
        a('bloqueio', 'T-RESOLUCAO', f"resolução {so['largura']}×{so['altura']} (esperado 1080×1920)")
    if abs(so['duracao'] - dados['duration']) > 1.0:
        a('bloqueio', 'T-DURACAO', f"MP4 com {so['duracao']:.1f}s para {dados['duration']:.1f}s de narração")
    if not so['tem_audio']:
        a('bloqueio', 'T-AUDIO', 'MP4 sem áudio')
    au = _lufs(mp4)
    if au['lufs'] is None or abs(au['lufs'] - LUFS_META) > LUFS_TOL:
        a('bloqueio', 'T-LOUDNESS', f"loudness {au['lufs']} LUFS (meta {LUFS_META} ± {LUFS_TOL}) (ERR-016)")
    if au['pico_dbtp'] is not None and au['pico_dbtp'] > -1.0:
        a('revisao', 'T-PICO', f"pico {au['pico_dbtp']} dBTP acima de −1")
    av = fiscal_av.avaliar(mp4, cenas, registro, [e['id'] for e in ctx['eventos'] if e['critico']])
    for x in av['achados']:
        if x['codigo'] == 'AV-PERGUNTA':
            a('bloqueio', 'E-PERGUNTA', x['evidencia'])
        elif x['codigo'] == 'AV-PARADO':
            a('revisao', 'E-PARADO', f"imagem parada {x['inicio']}–{x['fim']} s", x['inicio'], x['fim'], evidencia=x['evidencia'])
        elif x['codigo'] == 'AV-VAZIO':
            pass                                          # agregado abaixo (um achado por trecho contínuo)
        elif x['codigo'] == 'AV-REPETE':
            a('revisao', 'E-REPETE', x['evidencia'] + ' (ERR-007)', x['inicio'], x['fim'])
        elif x['codigo'] == 'AV-TRANSICAO':
            a('estetica', 'S-TRANSICAO', x['evidencia'], x['inicio'], x['fim'])
    vaz = [i for i, val in enumerate(av['medidas']['vazio_por_s']) if val > fiscal_av.VAZIO_LIMIAR]
    for ini, fim in _trechos(vaz):
        if fim - ini >= 2:
            a('revisao', 'E-VAZIO', f'área útil sem detalhe {ini}–{fim} s', ini, fim)
    planejados = [(round(c['start'], 2), TRANS_D.get(c.get('transicao') or 'corte', .5)) for c in cenas[1:]]
    det = cortes(mp4)
    cc = comparar_cortes(det, planejados)
    for d in cc['inesperados']:
        k = next((i for i, c in enumerate(cenas) if c['start'] <= d < c['end']), None)
        if k is not None and cenas[k]['comp'] == 'doc.plano':      # dentro de foto dirigida não deveria haver corte seco
            a('revisao', 'T-CORTE-INESPERADO', f'mudança abrupta em {d:.1f}s dentro do plano {k} (foto dirigida)', d, d, k)
    dur_planos = [c['end'] - c['start'] for c in cenas]
    for k, d in enumerate(dur_planos):
        if d > PLANO_LONGO_S:
            a('estetica', 'S-PLANO-LONGO', f'plano {k} com {d:.1f}s', cenas[k]['start'], cenas[k]['end'], k)
    # ---------------- editorial
    fatos_txt = str(v.get('fatos') or '')
    por_evento = {}
    for k, c in enumerate(cenas):
        por_evento.setdefault((c.get('direcao') or {}).get('evento_id'), []).append(k)
    for e in ctx['eventos']:
        ks = por_evento.get(e['id'], [])
        if e['critico'] and ks and e['tipo'] in contrato.EXIGE_DEMONSTRACAO:
            if not any(contrato.demonstra(cenas[k]['comp']) or cenas[k]['comp'] in ('doc.eclusa', 'doc.molde')
                       or (cenas[k].get('direcao') or {}).get('funcao_documental') == 'REGISTRO' for k in ks):
                a('bloqueio', 'E-MECANISMO', f"{e['id']} (mecanismo crítico) só com foto/cartão: não demonstra (ERR-006)", plano=ks[0])
        if e['critico'] and ks:
            falas_ev = set(e['trechos'])
            trechos_planos = {t for k in ks for t in (registro[_idx(registro, cenas[k])] or {}).get('trechos') or []}
            if not falas_ev & trechos_planos:
                a('revisao', 'E-COBERTURA', f"{e['id']} tem plano, mas o plano não cobre a fala do acontecimento (id ≠ cobertura)", plano=ks[0])
    for k, c in enumerate(cenas):
        d = c.get('direcao') or {}
        r = registro[_idx(registro, c)] or {}
        if c['comp'] == 'doc.plano':
            if d.get('objeto_principal') and not (r.get('camera') or {}).get('roi'):
                a('revisao', 'E-OBJETO', f"plano {k}: '{d.get('objeto_principal')}' não localizado na foto (câmera no foco geral)", c['start'], c['end'], k)
            sem_atencao = (d.get('movimento_camera') in (None, 'fixo')) and not (c.get('params') or {}).get('anot')
            if sem_atencao and c['end'] - c['start'] > 3:
                a('revisao', 'E-ATENCAO', f'plano {k}: foto fixa sem anotação por {c["end"] - c["start"]:.1f}s (cara de slide)', c['start'], c['end'], k)
        for an in (c.get('params') or {}).get('anot') or []:
            t = _n(an.get('texto'))
            if t and len(t.split()) >= 4 and t in _n(c.get('fala')):
                a('revisao', 'E-TEXTO-REPETE', f'plano {k}: rótulo só repete a fala ("{an.get("texto")}")', c['start'], c['end'], k)
        for txt in [an.get('texto') or '' for an in (c.get('params') or {}).get('anot') or []] + [((c.get('params') or {}).get('selo') or {}).get('texto') or '']:
            for n in re.findall(r'\d+(?:[.,]\d+)*', txt):
                if not re.match(r'^(1[0-9]{3}|20[0-9]{2})$', n) and n.replace('.', '') not in re.sub(r'[.]', '', fatos_txt + ' ' + ' '.join(str(x.get('fala')) for x in v['cenas'])):
                    a('bloqueio', 'E-NUMERO', f'plano {k}: número {n} na tela fora da pesquisa e da fala (ERR-012)', c['start'], c['end'], k)
    comps = [c['comp'] for c in cenas]
    movs = [(c.get('direcao') or {}).get('movimento_camera') for c in cenas]
    for i in range(len(cenas) - 3):
        if len(set(movs[i:i + 4])) == 1 and comps[i:i + 4] == ['doc.plano'] * 4:
            a('estetica', 'S-MONOTONIA', f'4 planos seguidos com o mesmo movimento ({movs[i]})', cenas[i]['start'], cenas[i + 3]['end'])
            break
    slide = sum(1 for c in cenas if c['comp'] == 'doc.plano' and (c.get('direcao') or {}).get('movimento_camera') in (None, 'fixo')
                and not (c.get('params') or {}).get('anot'))
    if cenas and slide / len(cenas) > .4:
        a('revisao', 'E-SLIDESHOW', f'{slide} de {len(cenas)} planos são foto fixa sem anotação: sequência com cara de apresentação de slides')
    for r in registro:
        for e in r.get('erros') or []:
            a('revisao', 'D-PLANO-RECUSADO', f"plano de {r.get('evento_id')} recusado pelo validador: {e}")
    resumo = {
        'bloqueios': sum(1 for x in ach if x['classe'] == 'bloqueio'), 'revisoes': sum(1 for x in ach if x['classe'] == 'revisao'),
        'esteticas': sum(1 for x in ach if x['classe'] == 'estetica'), 'planos': len(cenas),
        'duracao_media_plano_s': round(sum(dur_planos) / len(dur_planos), 2) if dur_planos else None,
        'parado_pct': av['resumo']['parado_pct'], 'vazio_medio_pct': av['resumo']['vazio_medio_pct'], 'movimento_medio': av['resumo']['movimento_medio'],
        'cortes': {k: cc[k] for k in ('acertos', 'recall')} | {'inesperados': len(cc['inesperados']), 'detectados': len(det)},
        'audio': au, 'video': so, 'composicoes': sorted(set(comps)), 'anotacoes': sum(len((c.get('params') or {}).get('anot') or []) for c in cenas),
        'storyboard_automatico': bool(sreg and sreg.get('resposta_original')), 'correcoes_do_modelo': len((sreg or {}).get('correcoes') or []),
    }
    return {'resumo': resumo, 'achados': ach, 'cortes': cc, 'medidas_av': av['resumo'],
            'nota': 'bloqueio = objetivo; revisão = olho humano; estética = preferência. Aprovação artística é humana.'}


def _n(s) -> str:
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()


def _idx(registro: list[dict], cena: dict) -> int:
    o = (cena.get('origem') or [0])[0]
    return o if 0 <= o < len(registro) else 0


def _trechos(ix: list[int]):
    out = []
    for i in ix:
        if out and i == out[-1][1]:
            out[-1][1] = i + 1
        else:
            out.append([i, i + 1])
    return [tuple(x) for x in out]


def texto(f: dict) -> str:
    r = f['resumo']
    l = [f"# Fiscal V3.1 — {r['bloqueios']} bloqueio(s), {r['revisoes']} revisão(ões), {r['esteticas']} estética(s)", '',
         f"Planos {r['planos']} · média {r['duracao_media_plano_s']} s · parado {r['parado_pct']}% · vazio {r['vazio_medio_pct']}% · "
         f"anotações {r['anotacoes']} · loudness {r['audio']['lufs']} LUFS · cortes planejados achados {r['cortes']['acertos']} (recall {r['cortes']['recall']})", '',
         '| classe | código | quando | problema |', '|---|---|---|---|']
    for a in sorted(f['achados'], key=lambda x: ('bloqueio', 'revisao', 'estetica').index(x['classe'])):
        q = '' if a['inicio'] is None else f"{a['inicio']:.1f}–{(a['fim'] or a['inicio']):.1f}s"
        l.append(f"| {a['classe']} | {a['codigo']} | {q} | {a['problema']} |")
    return '\n'.join(l) + '\n\n' + f['nota'] + '\n'


def folha_contato(mp4: Path, dados: dict, destino: Path, por_cena: int = 2):
    """Galeria de quadros (2 por plano) num JPG, para revisão rápida sem assistir ao vídeo inteiro."""
    ts = []
    for c in dados['scenes']:
        d = c['end'] - c['start']
        ts += [c['start'] + d * f for f in ((.3, .85) if por_cena == 2 else (.5,))]
    sel = '+'.join(f'between(t,{t:.3f},{t + .033:.3f})' for t in ts)
    cols = 8
    linhas = max(1, -(-len(ts) // cols))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-vf', f"select='{sel}',scale=216:384,tile={cols}x{linhas}:padding=4",
                    '-frames:v', '1', '-q:v', '3', str(destino)], check=False)
    return destino
