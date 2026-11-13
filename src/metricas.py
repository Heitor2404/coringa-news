"""MÉTRICAS DA RODADA (plano-mestre, etapa I — 12/11/2026). Só leitura do que o pipeline já registrou; nenhuma chamada.

Junta num lugar: chamadas e tokens por fase (Claude e Gemini, com falhas e repetições), tempo das etapas, acerto do
acervo (casamento × reserva × sem foto), motivos de recusa de imagem, representação adequada por cena (storyboard) e
problemas editoriais. Vai para `-metricas.json` e uma linha 📈 no diagnóstico. Custos são ESTIMADOS (crédito do Claude
Code); o teto de US$ 0,30 não é garantido: o orçamento continua em modo monitorar.
"""
from collections import Counter


def coletar(v: dict, cenas: list[dict]) -> dict:
    from . import custo, orcamento, storyboard
    livro = list(custo.LIVRO)
    fases = {}
    for x in livro:
        f = fases.setdefault(f"{x['ia']}:{x['etapa']}", {'chamadas': 0, 'falhas': 0, 'tokens_saida': 0, 'tokens': 0,
                                                         'usd': 0.0, 'segundos': 0.0})
        f['chamadas'] += 1
        f['falhas'] += 0 if x['ok'] else 1
        f['tokens_saida'] += x['saida']
        f['tokens'] += x['entrada'] + x['cache_escrita'] + x['cache_lida'] + x['saida']
        f['usd'] = round(f['usd'] + x['usd'], 4)
        f['segundos'] = round(f['segundos'] + x['segundos'], 1)
    claude = [x for x in livro if x['ia'] == 'claude']
    ideias = [c for c in v.get('cenas', []) if c.get('tipo') not in ('fechamento', 'mapa') and not c.get('sub')]
    escolha = [c.get('_escolha') or {} for c in ideias]
    recusas = Counter(r['motivo'] for e in escolha for r in e.get('rejeitadas') or [])
    rebaixadas = sum(1 for e in escolha for m in e.get('motivos') or [] if 'o Gemini disse' in m)
    reservas = sum(1 for e in escolha for m in e.get('motivos') or [] if m.startswith('reserva com'))
    sb = storyboard.resumo(cenas) if any(c.get('sb') for c in cenas) else {}
    por = [s for s in {id(c['sb']): c['sb'] for c in cenas if c.get('sb')}.values()]
    return {
        'claude': {'chamadas': len(claude), 'falhas': sum(1 for x in claude if not x['ok']),
                   'repetidas': sum(max(0, f['chamadas'] - 1) for k, f in fases.items() if k.startswith('claude:')),
                   'usd_estimado': custo.claude_usd(), 'teto_garantido': False},
        'gemini': {'chamadas': sum(1 for x in livro if x['ia'] == 'gemini'),
                   'falhas': sum(1 for x in livro if x['ia'] == 'gemini' and not x['ok'])},
        'fases': fases,
        'tempo_min': dict(orcamento.MARCAS),
        'acervo': {'ideias': len(ideias), 'com_foto': sum(1 for c in ideias if c.get('foto')),
                   'do_casamento': sum(1 for c in ideias if c.get('foto')) - reservas, 'reservas': reservas,
                   'sem_foto': sum(1 for c in ideias if not c.get('foto')),
                   'relacao_rebaixada': rebaixadas, 'recusas': dict(recusas)},
        'representacao': {'cenas': len(por), 'explica': sum(1 for s in por if s['explica']),
                          'evidencia': sb.get('evidencia', {}), 'centrais_sem_explicacao': sb.get('centrais_sem_explicacao', [])},
    }


def linha_telegram(m: dict) -> str:
    cl, ac, rp = m['claude'], m['acervo'], m['representacao']
    partes = [f"📈 Métricas: Claude {cl['chamadas']} chamada(s)"
              + (f" ({cl['falhas']} falha(s))" if cl['falhas'] else '') + (f" · {cl['repetidas']} repetida(s)" if cl['repetidas'] else '')]
    if m['gemini']['falhas']:
        partes.append(f"Gemini {m['gemini']['falhas']} falha(s)")
    if ac['ideias']:
        partes.append(f"acervo {ac['com_foto']}/{ac['ideias']} ideias com foto ({ac['reservas']} de reserva)"
                      + (f", {ac['relacao_rebaixada']} relação rebaixada" if ac['relacao_rebaixada'] else ''))
    if ac['recusas']:
        partes.append('recusas: ' + ', '.join(f'{k} {n}' for k, n in sorted(ac['recusas'].items(), key=lambda t: -t[1])[:3]))
    if rp['cenas']:
        partes.append(f"representação {rp['explica']}/{rp['cenas']}")
    return ' · '.join(partes)
