"""V2.5 — COBERTURA SEMÂNTICA: o que a fala manda mostrar × o que o plano visual efetivamente representa.

Geometria certa e estados diferentes não bastam (uma seta sem objeto, um mapa sem o lugar, cartões em sequência
"renderizam"). Para cada acontecimento CRÍTICO, antes da narração, registra:
  afirmação narrada · elementos necessários (sujeito, estado inicial/final, o que mostrar) · elementos representados
  (o que a composição escreve/desenha, ou o que a foto do acervo mostra pelo catálogo) · mudança exigida × produzida
  (medida na prévia renderizada) · fonte/justificativa · resultado (aprovado | revisao | bloqueio) e o motivo.

Se a composição escolhida não cobre o acontecimento, tenta UMA alternativa entre as composições capazes do tipo cujos
dados o contrato já tem (sem IA, sem inventar dado). Se nenhuma serve, BLOQUEIO com a limitação — nunca imagem,
relação ou fato inventado. Sem rede, sem custo.
"""
from __future__ import annotations

import re
import unicodedata

from src.v2 import contrato

PARE = set('para pelo pela pelos pelas como quando onde entre sobre depois antes mais menos muito muita muitos muitas '
           'esse essa isso este esta isto aquele aquela seus suas dele dela eles elas fica ficam está estão sendo foram '
           'cena mostrar mostra esquema imagem foto vídeo video'.split())
COBERTURA_MIN = .5


def _raizes(t) -> set[str]:
    t = unicodedata.normalize('NFKD', str(t or '').lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return {w[:5] for w in re.findall(r'[a-z]{4,}', t) if w not in PARE}


def _textos(x) -> list[str]:
    if isinstance(x, dict):
        return [s for k, v in x.items() if k not in ('id', 'forma', 'cor', 'tipo', 'lado', 'preso_a', 'img', 'video', 'arq') for s in _textos(v)]
    if isinstance(x, list):
        return [s for v in x for s in _textos(v)]
    return [x] if isinstance(x, str) else []


def necessarios(ac: dict) -> set[str]:
    return _raizes(' '.join(str(ac.get(k) or '') for k in ('sujeito', 'estado_inicial', 'estado_final')))


def representados(ac: dict, comp: str | None, params: dict, foto: dict | None) -> set[str]:
    r = _raizes(' '.join(_textos(params or {})))
    if foto:                                     # foto: o que o catálogo do acervo diz que ela mostra
        r |= _raizes(' '.join(str(foto.get(k) or '') for k in ('mostra', 'titulo', 'legenda')))
    return r


def avaliar_evento(ac: dict, fala: str, comp: str | None, params: dict, foto: dict | None, previa_ev: dict | None) -> dict:
    nec, rep = necessarios(ac), representados(ac, comp, params, foto)
    cob = round(len(nec & rep) / len(nec), 2) if nec else 1.0
    muda = bool(ac.get('estado_inicial')) and _raizes(ac.get('estado_inicial')) != _raizes(ac.get('estado_final'))
    produziu = None
    if previa_ev and previa_ev.get('medidas'):
        m = previa_ev['medidas']
        produziu = max(m.get('dif_ini_fim', 0), m.get('dif_ini_meio', 0)) >= 2 or m.get('frac_mudou', 0) >= .004
    modo = (ac.get('representacao') or {}).get('modo')
    if modo == 'editorial':
        res, motivo = 'aprovado', 'cena editorial (gancho/revelação/fechamento) resume o que já foi mostrado'
    elif comp in contrato.TEXTUAIS and contrato.critico(ac) and ac.get('tipo') in contrato.EXIGE_DEMONSTRACAO:
        res, motivo = 'bloqueio', 'mecanismo crítico só escrito na tela'
    elif muda and comp and contrato.demonstra(comp) and produziu is False:
        res, motivo = 'bloqueio', 'a fala exige mudança de estado e a composição renderizada não muda'
    elif cob >= COBERTURA_MIN:
        res, motivo = 'aprovado', f'{len(nec & rep)}/{len(nec)} elementos necessários na tela'
    elif cob > 0:
        res, motivo = 'revisao', f'só {len(nec & rep)}/{len(nec)} elementos necessários na tela: um humano confere'
    else:
        res, motivo = 'bloqueio', 'nenhum elemento do acontecimento aparece na tela (rótulos/catálogo)'
    if modo in ('foto_ilustrativa', 'foto_declarada') and res == 'aprovado':
        res, motivo = 'revisao', motivo + '; imagem é ilustração/declarada, não prova'
    return {'evento': ac.get('id'), 'tipo': ac.get('tipo'), 'afirmacao': re.sub(r'\*', '', fala or '')[:160], 'comp': comp, 'modo': modo,
            'necessarios': sorted(nec), 'representados': sorted(nec & rep), 'faltando': sorted(nec - rep), 'cobertura': cob,
            'mudanca_exigida': muda, 'mudanca_produzida': produziu, 'fonte': ac.get('fonte'), 'resultado': res, 'motivo': motivo}


def _alternativa(ac: dict, atual: str | None) -> str | None:
    """UMA alternativa entre as composições capazes do tipo cujos dados o contrato JÁ tem (ordem do contrato)."""
    from src.v2 import capacidades
    p = dict(ac.get('dados') or {})
    for comp, reqs in contrato.TIPOS.get(ac.get('tipo'), {}).get('comps', {}).items():
        if comp == atual or comp in contrato.GENERICAS or not contrato.comp_aceita(ac, comp, p):
            continue
        if all(capacidades._tem(r, p, '') for r in reqs):
            return comp
    return None


def avaliar(v: dict, previa_rel: dict | None = None) -> dict:
    """Cobertura de todos os acontecimentos críticos do roteiro já preparado. Muda `representacao` só quando troca para
    UMA alternativa que cobre melhor; devolve {eventos, bloqueios, revisoes} no formato do preparo."""
    por_id = {x['id']: x for x in v.get('acervo') or []}
    pv = {e['evento']: e for e in (previa_rel or {}).get('eventos') or []}
    rel, vistos = {'eventos': [], 'bloqueios': [], 'revisoes': [], 'alternativas': []}, set()
    for i, c in enumerate(v.get('cenas') or []):
        ac = c.get('acontecimento') if isinstance(c.get('acontecimento'), dict) else None
        if not ac or not ac.get('id') or ac['id'] in vistos or not contrato.critico(ac):
            continue
        vistos.add(ac['id'])
        idx = [k for k, x in enumerate(v['cenas']) if (x.get('acontecimento') or {}).get('id') == ac['id']]
        fala = ' '.join(v['cenas'][k].get('fala') or '' for k in idx)
        rep = ac.get('representacao') or {}
        comp = rep.get('comp') if rep.get('modo') == 'composicao' else ('foto' if rep.get('foto') else None)
        foto = por_id.get(rep.get('foto') or c.get('foto'))
        r = avaliar_evento(ac, fala, comp, ac.get('dados') or {}, foto if comp == 'foto' or rep.get('modo', '').startswith('foto') else None, pv.get(ac['id']))
        if r['resultado'] == 'bloqueio' and rep.get('modo') == 'composicao':
            alt = _alternativa(ac, comp)
            if alt:
                r2 = avaliar_evento(ac, fala, alt, ac.get('dados') or {}, None, None)
                rel['alternativas'].append({'evento': ac['id'], 'de': comp, 'para': alt, 'resultado': r2['resultado']})
                if r2['resultado'] != 'bloqueio':
                    for k in idx:
                        v['cenas'][k]['acontecimento']['representacao'] = {'modo': 'composicao', 'comp': alt}
                    r = {**r2, 'motivo': f"alternativa: {comp} → {alt} ({r2['motivo']})"}
        rel['eventos'].append(r)
        if r['resultado'] == 'bloqueio':
            rel['bloqueios'].append({'evento': ac['id'], 'cenas': idx, 'tipo': ac['tipo'], 'mostrar': ac.get('mostrar'),
                                     'faltam': [f"cobertura: {r['motivo']}", f"faltam na tela: {', '.join(r['faltando']) or '-'}"]})
        elif r['resultado'] == 'revisao':
            rel['revisoes'].append({'evento': ac['id'], 'cenas': idx, 'problema': f"cobertura parcial: {r['motivo']}", 'evidencia': ', '.join(r['faltando'])})
    return rel


def resumo(rel: dict) -> str:
    return f"cobertura: {len(rel['eventos'])} crítico(s) · {len(rel['bloqueios'])} bloqueio(s) · {len(rel['revisoes'])} revisão(ões)" + ''.join(
        f"\n  {e['evento']} {e['comp'] or '-'}: {e['resultado']} ({e['cobertura']:.0%}) — {e['motivo']}" for e in rel['eventos'])
