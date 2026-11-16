"""Plano audiovisual por acontecimento — a etapa que decide O QUE DEMONSTRAR antes do storyboard e antes da narração
definitiva (V3.1-resgate). Reaproveita o contrato do roteiro (src/v2/contrato.py: sujeito, ação, estados) e o plano V2
por cena (`sb`: requisitos, mídia preferida) — não cria outro planejamento; junta os dois com o acervo disponível e os
fatos, e diz para cada acontecimento se ele é demonstrável, com o quê, e como verificar no vídeo.

Sem IA. A ficha vai ao prompt do diretor (decidir demonstrações e ajustar a narração) e ao fiscal semântico (critério).
"""
from __future__ import annotations

import re

from src.v2 import contrato

# o que cada tipo de acontecimento precisa MOSTRAR (representação necessária) e como verificar no vídeo
REPRESENTACAO = {
    'localizacao': ('o lugar identificado: mapa com o ponto ou foto do próprio lugar', 'o ponto/lugar está na tela, legível, quando a fala o nomeia'),
    'lugar': ('o lugar identificado: mapa com o ponto ou foto do próprio lugar', 'o lugar está na tela quando a fala o nomeia'),
    'deslocamento': ('mapa com origem, destino e o sentido do avanço', 'o avanço aparece em etapas, na ordem da fala, sobre geografia correta'),
    'territorio': ('mapa com a área atingida destacada', 'a área destacada corresponde à área dita, sobre geografia correta'),
    'processo': ('as etapas em sequência, com o sujeito que age', 'cada etapa aparece quando é dita; o sujeito é reconhecível'),
    'mecanismo': ('sujeito, estado inicial, ação e resultado animados', 'há mudança visível entre estados; não é cartão de texto'),
    'transformacao': ('antes e depois do mesmo sujeito', 'a mesma coisa em dois estados'),
    'pessoa': ('retrato ou registro da própria pessoa', 'a pessoa mostrada é a pessoa citada (nome/época conferem)'),
    'evento_historico': ('registro ou representação de época do próprio acontecimento', 'a imagem é do acontecimento (ou rotulada como representação/contexto)'),
    'sequencia_historica': ('datas em ordem com o que muda em cada uma', 'cada data aparece com o seu acontecimento'),
    'numero': ('o número com unidade e uma referência que dê escala', 'número com unidade e contexto; nunca sozinho'),
}
PADRAO = ('registro ou representação do acontecimento', 'a imagem corresponde ao que a fala diz')


def _tok(s) -> set[str]:
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z0-9]{4,}', s)}


def fichas(v: dict, acervo: dict, fatos: list[tuple[str, str]], eventos: list[dict]) -> list[dict]:
    """Uma ficha por acontecimento: sujeito, estado inicial, ação, transformação, consequência, representação
    necessária, mídia/composição disponível, evidência factual, critério de verificação e status."""
    out = []
    for e in eventos:
        ac = e.get('ac') or {}
        sb = next((c.get('sb') or {} for c in v['cenas'] if (c.get('acontecimento') or {}).get('id') == e['id']), {})
        rep, crit = REPRESENTACAO.get(e.get('tipo'), PADRAO)
        chave = _tok(' '.join(str(ac.get(k) or '') for k in ('sujeito', 'quem', 'onde', 'mostrar', 'acao', 'estado_final'))
                     + ' ' + ' '.join(str(v['cenas'][t].get('fala') or '') for t in e['trechos']))
        midias = []
        for k, x in acervo.items():
            if x.get('ia') or x.get('uso_comercial') != 'sim':
                continue
            hit = chave & _tok(x.get('mostra'))
            if len(hit) >= 2 or (hit and e.get('tipo') in ('pessoa', 'localizacao')):
                midias.append((len(hit), k))
        midias = [k for _, k in sorted(midias, reverse=True)[:4]]
        evid = [i for i, t in fatos if len(chave & _tok(t)) >= 2][:3]
        comps = e.get('viaveis') or []
        if e.get('tipo') in contrato.EXIGE_DEMONSTRACAO:
            status = 'demonstravel' if comps else ('esquema_a_escrever' if e.get('tipo') in ('mecanismo', 'processo') else 'parcial')
        else:
            status = 'demonstravel' if (midias or comps) else 'indisponivel'
        from src.v3 import linguagem                   # 16/11: a FORMA visual sai antes da câmera
        forma = linguagem.forma_do_evento(e, {linguagem.natureza(acervo[k]) for k in midias if k in acervo})
        out.append({'evento_id': e['id'], 'tipo': e.get('tipo'), 'critico': e.get('critico'), 'trechos': e['trechos'],
                    'forma_visual': forma['forma'], 'justificativa_forma': forma['justificativa'], 'composicoes_forma': forma['comps'],
                    'naturezas_midia': {k: linguagem.natureza(acervo[k]) for k in midias if k in acervo},
                    'sujeito': ac.get('sujeito') or ac.get('quem'), 'estado_inicial': ac.get('estado_inicial'), 'acao': ac.get('acao'),
                    'transformacao': ac.get('estado_final'), 'consequencia': sb.get('avanca'),
                    'representacao_necessaria': rep, 'midia_disponivel': midias, 'composicoes_viaveis': comps,
                    'evidencia': evid, 'criterio_visual': crit, 'status': status})
    return out


def texto_prompt(fs: list[dict]) -> str:
    return '\n'.join(
        f"{f['evento_id']} [{f['tipo']}{' · CRÍTICO' if f['critico'] else ''} · {f['status']}] FORMA: {f.get('forma_visual')} "
        f"({f.get('justificativa_forma')}; composições: {', '.join(f.get('composicoes_forma') or []) or 'nenhuma'}) · sujeito: {f['sujeito']} · "
        f"{f['estado_inicial'] or '?'} → {f['acao'] or '?'} → {f['transformacao'] or '?'} · precisa mostrar: {f['representacao_necessaria']} · "
        f"mídia: {', '.join(f'{k} ({n})' for k, n in (f.get('naturezas_midia') or {}).items()) or ', '.join(f['midia_disponivel']) or 'nenhuma'} · composições: {', '.join(f['composicoes_viaveis']) or 'nenhuma'} · "
        f"fatos: {', '.join(f['evidencia']) or '—'} · verificar: {f['criterio_visual']}" for f in fs)


def validar_ajustes(ajustes: list, v: dict, base_fatos: str) -> tuple[list[dict], list[str]]:
    """Ajustes de narração pedidos pelo diretor depois de decidir as demonstrações. Aceita só: trecho existente, texto
    com tamanho parecido (60–140%), nenhum número fora da pesquisa. → (aceitos, recusados com motivo)."""
    from src.v3.pipeline import _numeros, _texto_tem_numero
    ok, nao = [], []
    falas = [str(c.get('fala') or '') for c in v['cenas']]
    for a in ajustes or []:
        t, novo = a.get('trecho'), str(a.get('texto') or '').strip()
        if not isinstance(t, int) or not 0 <= t < len(falas) or not novo:
            nao.append(f'ajuste inválido: {a}')
            continue
        r = len(novo) / max(1, len(falas[t]))
        if not .6 <= r <= 1.4:
            nao.append(f'trecho {t}: tamanho {r:.0%} do original (aceito 60–140%)')
            continue
        fora = [n for n in _numeros(novo) if not _texto_tem_numero(n, base_fatos + ' ' + falas[t])]
        if fora:
            nao.append(f'trecho {t}: números fora da pesquisa {fora}')
            continue
        ok.append({'trecho': t, 'antes': falas[t], 'texto': novo, 'motivo': a.get('motivo', '')})
    return ok, nao
