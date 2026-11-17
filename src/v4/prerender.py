"""PRÉ-RENDER: o que pode ser detectado ANTES da execução cara não pode virar descoberta no Actions (Heitor, 17/11).
Sem chamada de IA e sem rede. Para cada cena: componente conhecido, parâmetros obrigatórios e válidos, recurso disponível
(mídia comprovada da biblioteca, com licença e crédito), contrato sem erro, backend com alternativa se falhou no CI,
narração reutilizável que bate com as falas e — para as composições do palco V2 — geometria real medida no Chromium
contra as zonas da identidade V4 (marca, selo, crédito, legenda). Resultado: todas 'pronta', ou a execução não começa.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from src.v4 import contrato, viabilidade
from src.v4.componentes import COMPONENTES
from src.v4.util import IDENT

OBRIGATORIOS = {
    'registro.foto': ['asset'], 'registro.video': ['asset'], 'camadas.recorte': ['asset'],
    'mapa.rota': ['regiao', 'rota_osm'], 'mecanismo.eclusa': ['sentido', 'desnivel_m', 'etapas', 'tempos'],
    'mecanismo.nivel_vasos': ['desnivel_m', 'nomes', 'passos'], 'tresd.camara': ['nivel_baixo_m', 'nivel_alto_m', 'encher', 'rotulos'],
    'dados.escala': ['alvo'], 'tipo.lottie': ['linhas'], 'hf.registro': ['item'],
}
HOSTS_MIDIA = ('upload.wikimedia.org', 'thumb.wikimedia.org', 'commons.wikimedia.org')


def zonas_v4(tem_credito: bool) -> dict:
    a, m, s, c = IDENT['areas_seguras'], IDENT['marca'], IDENT['selo'], IDENT['credito']
    z = {'marca': [m['x'], m['y'] - 6, m['x'] + 420, m['y'] + 40], 'selo': [72, s['y'] - 4, 560, s['y'] + 44],
         'legenda': [150, a['legenda_topo'], 930, a['legenda_base']]}
    if tem_credito:
        z['credito'] = [160, c['y'] - 4, 920, c['y'] + 48]
    return z


def hash_falas(cenas: list[dict]) -> str:
    return hashlib.sha256(json.dumps([c['fala'] for c in cenas], ensure_ascii=False).encode()).hexdigest()[:16]


_JS = """() => { const at = [...document.querySelectorAll('.cena')].find(e => e.style.visibility !== 'hidden') || document;
  const glob = ['marca', 'legenda', 'aviso-ia'].map(id => document.getElementById(id)).filter(Boolean).map(e => (e.dataset.g = e.dataset.g || 'v2-' + e.id, e));
  return [...at.querySelectorAll('[data-g]'), ...glob].filter(e => e.checkVisibility({opacityProperty: true, visibilityProperty: true}))
    .map(e => { const r = e.getBoundingClientRect(); return { g: e.dataset.g, tx: (e.textContent || '').trim().slice(0, 40), b: [r.left, r.top, r.right, r.bottom] }; })
    .filter(x => x.b[2] - x.b[0] > 2 && x.b[3] - x.b[1] > 2); }"""


def geometria_palco(comp: str, params: dict, dur: float, tem_credito: bool, trab: Path, passo: float = .5) -> list[str]:
    """renderiza a composição V2 no palco (local) e mede cada elemento visível contra as zonas da identidade V4"""
    from src.v2 import palco
    dados = {'meta': {'motor': 'v2', 'marca': False}, 'duration': dur, 'captions': [], 'creditos': [],
             'scenes': [{'comp': comp, 'start': 0, 'end': dur, 'transicao': 'corte', 'origem': [0], 'fala': '', 'params': params}]}
    zonas = zonas_v4(tem_credito)
    achados = set()
    with palco.abrir(palco.preparar(copy.deepcopy(dados)), trab) as pg:
        t = .3
        while t < dur:
            pg.evaluate(f'seek({t:.3f})')
            for el in pg.evaluate(_JS):
                x0, y0, x1, y1 = el['b']
                if x0 < -1 or x1 > 1081 or y1 > 1921:
                    achados.add(f"{el['g']} '{el['tx']}' sai do quadro")
                for nome, (a0, b0, a1, b1) in zonas.items():
                    if x0 < a1 and a0 < x1 and y0 < b1 and b0 < y1:
                        achados.add(f"{el['g']} '{el['tx']}' cruza a zona V4 '{nome}' (t={t:.1f}s)")
            t += passo
    return sorted(achados)


def verificar(ep: dict, pedido: dict, narracao: dict | None, trab: Path, palco_real: bool = True) -> dict:
    """ep JÁ resolvido pela viabilidade. Devolve {'pronto': bool, 'cenas': [...], 'gerais': [...]}"""
    from src.v4.componentes import ALTERNATIVAS
    bib = viabilidade.carregar()
    por_id = {it['id']: it for it in bib['itens']}
    reprov = {r['id'] for r in bib.get('reprovados') or []}
    caps = {c['ferramenta']: c for c in json.loads((Path(__file__).resolve().parents[2] / 'motor4' / 'capacidades.json').read_text())}
    gerais = []
    if not narracao:
        gerais.append('narração: nenhuma narração reutilizável (a execução chamaria o TTS)')
    elif narracao.get('falas_hash') != hash_falas(ep['cenas']):
        gerais.append('narração: o pacote reutilizável não corresponde às falas do roteiro')
    # acervo simulado só com os itens da biblioteca (sem rede) para o contrato
    acv = {}
    for c in ep['cenas']:
        a = (c.get('params') or {}).get('asset')
        if isinstance(a, str) and a.startswith('bib:') and a[4:] in por_id:
            it = por_id[a[4:]]
            acv[a] = {'id': a, 'arq': '(biblioteca)', 'wh': it['wh'], 'credito': it['credito'], 'licenca': it['licenca'], 'ano': it.get('ano'),
                      'titulo': it['titulo'], 'roi': it.get('roi'), 'escolha': {'prova': 'PROVADO'}}
    viol = contrato.validar(ep, acv)
    gerais += [f"contrato: {v['regra']} — {v['texto']}" for v in viol if v['gravidade'] == 'erro' and not v.get('cena')]
    cenas = []
    for c in ep['cenas']:
        comp, p = c['componente'], c.get('params') or {}
        prob = []
        if comp not in COMPONENTES:
            prob.append(f'componente desconhecido {comp!r}')
        falta = [k for k in OBRIGATORIOS.get(comp, []) if p.get(k) in (None, '', [], {})]
        if falta:
            prob.append('parâmetros obrigatórios ausentes: ' + ', '.join(falta))
        a = p.get('asset')
        if comp in ('registro.foto', 'registro.video', 'camadas.recorte'):
            if not (isinstance(a, str) and a.startswith('bib:')):
                prob.append(f'mídia não resolvida antes do render ({a!r}): viraria placa de diagnóstico')
            else:
                it = por_id.get(a[4:])
                if not it or it['id'] in reprov:
                    prob.append(f'item {a} fora da biblioteca comprovada ou reprovado')
                else:
                    if not it.get('licenca') or not it.get('credito'):
                        prob.append(f'item {a} sem licença/crédito')
                    if (it.get('prova') or {}).get('midia_corresponde') is not True:
                        prob.append(f'item {a} sem evidência de correspondência factual')
                    if not any(h in it['url'] for h in HOSTS_MIDIA):
                        prob.append(f'item {a} de origem fora das fontes verificadas')
        prob += [f"contrato: {v['regra']} — {v['texto']}" for v in viol if v.get('cena') == c['id'] and v['gravidade'] == 'erro']
        backend = COMPONENTES.get(comp, {}).get('backend', '')
        cap = next((x for k, x in caps.items() if k.lower().startswith(backend.split(':')[0].split('-')[0].lower())), None)
        if cap and str(cap.get('estado')) == 'falhou_ci' and not ALTERNATIVAS.get(comp):
            prob.append(f'backend {backend} falhou no CI e não tem alternativa')
        geo = []
        if comp == 'mecanismo.eclusa' and palco_real and not prob:
            q = {**p, 'v4': True}
            dur = round(c['fim'] - c['ini'], 2) if c.get('fim') else 8.0
            if q.get('tempos') and all(isinstance(x, (int, float)) and x <= 1.0001 for x in q['tempos']):
                q['tempos'] = [round(x * dur, 2) for x in q['tempos']]
            geo = geometria_palco('mecanismo.eclusa', q, dur, False, trab / c['id'])
            prob += [f'geometria: {g}' for g in geo]
        cenas.append({'cena': c['id'], 'componente': comp, 'modalidade': c['modalidade'], 'estado': 'pronta' if not prob else 'NAO_PRONTA',
                      'problemas': prob, 'asset': a, 'demonstrada_em': c.get('demonstrada_em')})
    return {'pronto': not gerais and all(x['estado'] == 'pronta' for x in cenas), 'gerais': gerais, 'cenas': cenas,
            'avisos': [f"{v['cena']}: {v['regra']}" for v in viol if v['gravidade'] == 'aviso']}
