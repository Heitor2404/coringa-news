"""Engenharia reversa AUTOMÁTICA de uma execução V4 (só leitura de artefatos; sem IA): por cena e por recurso —
backend/versão, render ok/falhou (log), medidas do MP4 (vazio, movimento, cortes, repetição), contrato (violações),
revisão multimodal (ou PENDENTE), áudio, custo. Julgamento estético: sempre PENDENTE HUMANO."""
from __future__ import annotations

import json
from pathlib import Path


def _l(p: Path, d=None):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return d


def escrever(saida: Path) -> Path:
    res, lt, m = _l(saida / 'resultado.json', {}), _l(saida / 'linha_do_tempo.json', []), _l(saida / 'metricas.json', {})
    ep = _l(saida / 'episodio.json', {})
    porc = {c['cena']: c for c in m.get('por_cena', [])}
    rev = {p.get('evento_id'): p for p in (res.get('revisao_multimodal') or {}).get('planos', [])}
    viol = (res.get('contrato') or {}).get('violacoes', [])
    L = [f"# Engenharia reversa automática — {res.get('video_id')}", '',
         f"Estado: **{res.get('estado')}** (NÃO PUBLICADO). Duração {m.get('resumo', {}).get('duracao')} s, {len(lt)} cenas. "
         'Julgamento estético: PENDENTE HUMANO.', '', '## Plano a plano', '',
         '| Cena | Tempo | Modalidade → componente | Backend | Render | Vazio méd/máx | Movimento | Estático c/ movimento prometido | Revisão multimodal | Violações |',
         '|' + '---|' * 10]
    for c in lt:
        x, r = porc.get(c['cena'], {}), rev.get(c['cena'], {})
        v = r.get('veredito') or {}
        rv = 'PENDENTE' if not r or '_nao_revisado' in v else f"demonstra={v.get('demonstra')} corresponde={v.get('midia_corresponde')}"
        vv = '; '.join(f"{y['regra']}" for y in viol if y['cena'] == c['cena']) or '—'
        st = c.get('estado') or ('falhou' if (c.get('detalhes') or {}).get('erro') else '?')
        L.append(f"| {c['cena']} | {c['ini']:.1f}–{c['fim']:.1f} | {c['modalidade']} → {c['componente']} | {c.get('backend')} {c.get('versao') or ''} | {st} "
                 f"({c.get('segundos_render') or '—'} s) | {x.get('vazio_medio')}/{x.get('vazio_max')} | {x.get('movimento_medio')} | "
                 f"{'SIM' if x.get('estatico_com_movimento_prometido') else 'não'} | {rv} | {vv} |")
    L += ['', '## Falas e o que precisava aparecer', '']
    for c in lt:
        L.append(f"- **{c['cena']}** ({c['ini']:.1f}s) “{c.get('fala')}” → precisa: {c.get('o_que_precisa_aparecer')}; câmera {c.get('camera')}; transição {c.get('transicao')}")
    cort = m.get('cortes') or {}
    L += ['', '## Cortes, repetição, continuidade', '',
          f"- cortes planejados {len(cort.get('planejados', []))} ({cort.get('por_minuto_planejados')}/min); detectados {len(cort.get('reais', []))}; "
          f"não planejados {cort.get('nao_planejados')}; planejados não detectados {cort.get('planejados_nao_detectados')}",
          f"- repetição perceptual (dHash ≤ 10): {m.get('repeticao_perceptual')}",
          f"- maiores saltos de brilho nos cortes: {sorted(m.get('continuidade', []), key=lambda z: -abs(z['salto_brilho']))[:4]}",
          '', '## Áudio e custo', '', f"- {res.get('audio')}", f"- som: {((res.get('etapas') or {}).get('composicao') or {}).get('som', {}).get('efeitos')}",
          f"- caixa: {json.dumps(res.get('caixa'), ensure_ascii=False, default=str)[:600]}",
          '', '## Contrato e direção', '', f"- famílias: {(res.get('contrato') or {}).get('familias')}",
          f"- correções impostas em código: {((res.get('etapas') or {}).get('direcao') or {}).get('correcoes_impostas')}",
          f"- violações: {viol}", f"- acervo: {(res.get('etapas') or {}).get('acervo')}", '', '## Bloqueios', ''] + [f'- {b}' for b in res.get('bloqueios', [])]
    arq = saida / 'ENGENHARIA_REVERSA_AUTOMATICA.md'
    arq.write_text('\n'.join(L) + '\n', encoding='utf-8')
    return arq
