"""Avaliação OFFLINE do modelo de evidência (src/v2/evidencia.py) — sem rede, sem IA.

Cada caso: um acontecimento, uma imagem (registro da fonte), a leitura visual CORRETA (rotulada) e o nível esperado
(gabarito, definido antes da avaliação, com o fundamento verificável). O mesmo caso roda em vários cenários:

  visão:    correta (rotulada, cega) | adversaria (a IA diz "mostra a ação", com confiança alta) | legado (viu a legenda) | ausente
  registro: completo | sem_categoria | sem_data

Métricas:
  falsa_prova           PROVA quando o gabarito não é PROVA (visão correta, registro completo) — critério: 0
  recall_prova          PROVA reconhecida quando o gabarito é PROVA (visão correta, registro completo)
  acerto                nível igual ao gabarito
  invariantes           sem visão independente (legado/ausente) nunca há PROVA; tirar dado do registro nunca CRIA PROVA
                        (sem a data, um veto temporal some e o nível pode subir até RELACIONADA = revisão humana)
  falsa_prova_adversaria  quanto o modelo depende da visão: PROVA errada quando a IA mente (medida, não critério)
  eventos               decisão por acontecimento (bloqueio/revisão/prova) com o acervo do caso
"""
from __future__ import annotations

import json
from pathlib import Path

from src.v2 import evidencia as E

CENARIOS_VISAO = ('correta', 'adversaria', 'adversaria_casamento', 'legado', 'ausente')
CENARIOS_REGISTRO = ('completo', 'sem_categoria', 'sem_data')


def registro(r: dict, cenario: str = 'completo') -> dict:
    cats = [] if cenario == 'sem_categoria' else list(r.get('categorias') or [])
    datas = {} if cenario == 'sem_data' else {k: E.intervalo(v) for k, v in (r.get('datas') or {}).items()}
    if r.get('datetimeoriginal_bruto') and cenario != 'sem_data':      # valor cru do extmetadata: classificado pelo código
        origem, iv = E._classificar_data_commons(r['datetimeoriginal_bruto'])
        if origem != 'desconhecida':
            datas[origem] = iv
    return E._registro(r.get('fonte'), r.get('titulo'), cats, datas, r.get('descricao'), r.get('autor'), r.get('licenca'),
                       r.get('ancestrais'), pagina=r.get('pagina'), etiquetas_livres=bool(r.get('etiquetas_livres')))


def visao(caso: dict, ev: dict, cenario: str) -> dict | None:
    vc = caso.get('visao_correta') or {}
    # catálogo (outra chamada, por imagem): rotulado com a verdade nos cenários correta e adversaria_casamento
    cat = {'natureza': vc.get('natureza', 'foto'), 'generica': bool(vc.get('generica')), 'acao_em_curso': vc.get('confere_com') == 'acao'}
    if cenario == 'correta':
        return {'origem': 'rotulada_cega', 'viu_legenda': False, 'confianca': 'alta', 'generica': False, **vc, 'catalogo': cat}
    if cenario == 'adversaria_casamento':     # só o casamento erra (uma alucinação), com confiança alta
        return {'origem': 'adversaria', 'viu_legenda': False, 'confere_com': (ev['exige'] or ['acao'])[0], 'natureza': 'foto',
                'classe_confere': True, 'confianca': 'alta', 'generica': False, 'catalogo': cat}
    if cenario == 'adversaria':
        return {'origem': 'adversaria', 'viu_legenda': False, 'confere_com': (ev['exige'] or ['acao'])[0], 'natureza': 'foto',
                'classe_confere': True, 'confianca': 'alta', 'generica': False}
    if cenario == 'legado':
        return {'origem': 'legado', 'viu_legenda': True, 'confere_com': 'incerto', 'natureza': vc.get('natureza', 'foto'),
                'classe_confere': None, 'confianca': 'baixa', 'generica': vc.get('generica', False),
                'texto_visivel': vc.get('texto_visivel')}
    return None


def _ev(dom: dict, chave: str) -> dict:
    a = dom['acontecimentos'][chave]
    return E.acontecimento(a['bruto'], a.get('falas'), dom.get('referencias'), chave)


def avaliar_conjunto(fix: dict) -> dict:
    res = {'grupo': fix.get('grupo'), 'casos': [], 'eventos': [], 'por_dominio': {}}
    for nome, dom in fix['dominios'].items():
        for c in dom['casos']:
            ev = _ev(dom, c['acontecimento'])
            img = dom['imagens'][c['imagem']]
            linha = {'dominio': nome, 'id': c['id'], 'tipo_caso': c.get('tipo_caso'), 'acontecimento': c['acontecimento'],
                     'imagem': c['imagem'], 'esperado': c['esperado'], 'fundamento': c.get('fundamento'), 'cenarios': {}}
            for rc in CENARIOS_REGISTRO:
                reg = registro(img['registro'], rc)
                for vc in CENARIOS_VISAO:
                    a = E.avaliar(ev, reg, visao(c, ev, vc))
                    linha['cenarios'][f'{vc}/{rc}'] = a['nivel']
                    if vc == 'correta' and rc == 'completo':
                        linha['obtido'] = a['nivel']
                        linha['motivos'] = a['motivos']
                        linha['dependencias'] = a['dependencias']
                        linha['familias'] = a['familias_que_confirmam']
            res['casos'].append(linha)
        for rotulo, esp in (dom.get('eventos_esperados') or {}).items():
            chave = esp.get('acontecimento') or rotulo
            ev = _ev(dom, chave)
            casos_ev = {c['imagem']: c for c in dom['casos'] if c['acontecimento'] == chave}
            cands = []
            for i in esp['acervo']:
                c = casos_ev.get(i) or {'visao_correta': {'confere_com': 'nao_mostra', 'natureza': 'foto', 'classe_confere': None}}
                cands.append((i, E.avaliar(ev, registro(dom['imagens'][i]['registro']), visao(c, ev, 'correta'))))
            rep = E.decidir(ev, cands)
            modo = 'revisao' if rep['modo'] == 'foto_relacionada' and rep.get('revisao_humana') else rep['modo']
            res['eventos'].append({'dominio': nome, 'acontecimento': rotulo, 'esperado': esp['esperado'], 'obtido': modo,
                                   'foto': rep.get('foto'), 'fundamento': esp.get('fundamento'), 'faltam': rep.get('faltam')})
    res['metricas'] = metricas(res)
    return res


def metricas(res: dict) -> dict:
    cs = res['casos']
    m = {'casos': len(cs),
         'acerto': sum(c['obtido'] == c['esperado'] for c in cs),
         'falsa_prova': [c['id'] for c in cs if c['obtido'] == 'PROVA' and c['esperado'] != 'PROVA'],
         'prova_esperada': sum(c['esperado'] == 'PROVA' for c in cs),
         'prova_reconhecida': sum(c['esperado'] == 'PROVA' and c['obtido'] == 'PROVA' for c in cs),
         'falsa_prova_adversaria': [c['id'] for c in cs if c['cenarios']['adversaria/completo'] == 'PROVA' and c['esperado'] != 'PROVA'],
         'falsa_prova_adversaria_casamento': [c['id'] for c in cs if c['cenarios']['adversaria_casamento/completo'] == 'PROVA' and c['esperado'] != 'PROVA'],
         'invariante_sem_visao_independente': [c['id'] for c in cs for k, n in c['cenarios'].items()
                                               if k.split('/')[0] in ('legado', 'ausente') and n == 'PROVA'],
         # tirar categoria/data (visão correta) nunca CRIA uma prova que o registro completo não dá
         'invariante_monotonia': [f"{c['id']}:{k}" for c in cs for k, n in c['cenarios'].items()
                                  if k.startswith('correta/') and k != 'correta/completo' and n == 'PROVA' and c['obtido'] != 'PROVA'],
         'eventos': len(res['eventos']), 'eventos_corretos': sum(e['obtido'] == e['esperado'] for e in res['eventos']),
         'negativos': [e for e in res['eventos'] if e['esperado'] in ('bloqueio', 'revisao')]}
    m['negativos_corretos'] = sum(e['obtido'] == e['esperado'] or (e['esperado'] == 'bloqueio' and e['obtido'] == 'bloqueio') for e in m['negativos'])
    m['recall_prova'] = round(m['prova_reconhecida'] / m['prova_esperada'], 3) if m['prova_esperada'] else None
    por = {}
    for c in cs:
        d = por.setdefault(c['dominio'], {'casos': 0, 'acerto': 0, 'falsa_prova': 0, 'prova_esperada': 0, 'prova_reconhecida': 0})
        d['casos'] += 1
        d['acerto'] += c['obtido'] == c['esperado']
        d['falsa_prova'] += c['obtido'] == 'PROVA' and c['esperado'] != 'PROVA'
        d['prova_esperada'] += c['esperado'] == 'PROVA'
        d['prova_reconhecida'] += c['esperado'] == 'PROVA' and c['obtido'] == 'PROVA'
    m['por_dominio'] = por
    m['negativos'] = len(m['negativos'])
    return m


def relatorio_md(res: dict, titulo: str) -> str:
    m = res['metricas']
    l = [f'# {titulo}', '', f"Grupo: **{res['grupo']}** · {m['casos']} casos · acerto {m['acerto']}/{m['casos']} · "
         f"falsa prova **{len(m['falsa_prova'])}** · recall de prova {m['prova_reconhecida']}/{m['prova_esperada']} · "
         f"eventos {m['eventos_corretos']}/{m['eventos']}", '',
         '| Domínio | Casos | Acerto | Falsa prova | Prova reconhecida |', '|---|---|---|---|---|']
    for d, x in m['por_dominio'].items():
        l.append(f"| {d} | {x['casos']} | {x['acerto']} | {x['falsa_prova']} | {x['prova_reconhecida']}/{x['prova_esperada']} |")
    l += ['', f"- Invariante — sem visão independente nunca há PROVA: {'ok' if not m['invariante_sem_visao_independente'] else m['invariante_sem_visao_independente']}",
          f"- Invariante — tirar categoria ou data nunca cria PROVA: {'ok' if not m['invariante_monotonia'] else m['invariante_monotonia']}",
          f"- Dependência da visão (catálogo E casamento mentindo com confiança alta): {len(m['falsa_prova_adversaria'])} falsa(s) prova(s): "
          f"{', '.join(m['falsa_prova_adversaria']) or 'nenhuma'}",
          f"- Só o casamento erra (catálogo correto): {len(m['falsa_prova_adversaria_casamento'])} falsa(s) prova(s): "
          f"{', '.join(m['falsa_prova_adversaria_casamento']) or 'nenhuma'}", '',
          '## Casos', '', '| Caso | Tipo | Acontecimento | Imagem | Esperado | Obtido | Adversária | Legado | Sem categoria | Motivo |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for c in res['casos']:
        ok = '' if c['obtido'] == c['esperado'] else ' ✘'
        l.append(f"| {c['id']} | {c['tipo_caso']} | {c['acontecimento']} | {c['imagem']} | {c['esperado']} | **{c['obtido']}**{ok} | "
                 f"{c['cenarios']['adversaria/completo']} | {c['cenarios']['legado/completo']} | {c['cenarios']['correta/sem_categoria']} | "
                 f"{'; '.join(c['motivos'][:2])[:160]} |")
    l += ['', '## Decisão por acontecimento', '', '| Domínio | Acontecimento | Esperado | Obtido | Imagem | Fundamento |', '|---|---|---|---|---|---|']
    for e in res['eventos']:
        ok = '' if e['obtido'] == e['esperado'] else ' ✘'
        l.append(f"| {e['dominio']} | {e['acontecimento']} | {e['esperado']} | **{e['obtido']}**{ok} | {e['foto'] or '—'} | {e['fundamento']} |")
    return '\n'.join(l) + '\n'


def rodar(arq: str | Path) -> dict:
    return avaliar_conjunto(json.loads(Path(arq).read_text(encoding='utf-8')))


if __name__ == '__main__':
    import sys
    r = rodar(sys.argv[1])
    print(relatorio_md(r, sys.argv[2] if len(sys.argv) > 2 else 'Avaliação do modelo de evidência'))


# ───────────────────────── reprodução dos dois pilotos (antigo × novo) ─────────────────────────
RAIZ_TESTES = Path(__file__).resolve().parents[2] / 'tests'


def _rotulos_do_piloto(dev: dict, dominio: str, ids: dict | None = None) -> tuple[dict, dict, dict]:
    """Registros e leituras visuais ROTULADAS (casos de desenvolvimento) mapeados para os ids do acervo do piloto."""
    dom = dev['dominios'][dominio]
    regs, vis = {}, {}
    for chave, img in dom['imagens'].items():
        if img.get('pilot_id'):
            regs[img['pilot_id']] = registro(img['registro'])
    for c in dom['casos']:
        pid = dom['imagens'][c['imagem']].get('pilot_id')
        if pid:
            vis[((ids or {}).get(c['acontecimento'], c['acontecimento']), pid)] = visao(c, {'exige': []}, 'correta')
    return regs, vis, dom['referencias']


def _linhas_fatos(fp: dict) -> str:
    return '\n'.join(f"- {f['fato']} ({f.get('fonte') or 'sem fonte'})" for f in fp.get('fatos') or [])


def pilotos() -> dict:
    """Ever Given: roteiro e acervo reais, preparo antigo recalculado. Santa Helena: decisão antiga GRAVADA no piloto."""
    import sys
    sys.path.insert(0, str(RAIZ_TESTES))
    import _piloto
    dev = json.loads((RAIZ_TESTES / 'evidencia' / 'desenvolvimento.json').read_text(encoding='utf-8'))
    out = {}
    v = _piloto.roteiro()
    # o contrato do piloto usa ids i0, i2...; os casos de desenvolvimento também (mesmo roteiro)
    ids = {c.get('evento'): (c.get('acontecimento') or {}).get('id') for c in v['cenas'] if c.get('evento')}
    regs, vis, refs = _rotulos_do_piloto(dev, 'naval', ids)
    out['ever_given'] = {'legado': E.preparar(v, v['acervo']),
                         'rotulado': E.preparar(v, v['acervo'], regs, vis, refs)}
    sh = RAIZ_TESTES / 'piloto_santa_helena'
    v2 = json.loads((sh / 'roteiro.json').read_text(encoding='utf-8'))
    v2['fatos'] = _linhas_fatos(json.loads((sh / 'fatos_pesquisados.json').read_text(encoding='utf-8')))
    ac = json.loads((sh / 'acervo_do_registro.json').read_text(encoding='utf-8'))
    antigo = json.loads((sh / 'preparo_original.json').read_text(encoding='utf-8'))
    regs, vis, refs = _rotulos_do_piloto(dev, 'geologia')
    out['santa_helena'] = {'legado': E.preparar(v2, ac, rel_antigo=antigo),
                           'rotulado': E.preparar(v2, ac, regs, vis, refs, rel_antigo=antigo)}
    return out


def pilotos_md(r: dict) -> str:
    l = ['# Os dois pilotos: preparo atual × modelo de evidência', '',
         '- **legado**: só o que o sistema guarda hoje (ano, 220 caracteres, catálogo que viu a legenda). Sem categorias e sem '
         'visão independente, o modelo novo nunca dá PROVA: o máximo é RELACIONADA (revisão humana).',
         '- **rotulado**: registros completos e leitura visual cega dos casos de desenvolvimento (o que a coleta e os prompts '
         'novos devolveriam), só para os pares rotulados; o resto continua legado.', '']
    for nome, par in r.items():
        l += [f'## {nome}', '', '| Acontecimento | Antigo | Novo (legado) | Novo (rotulado) |', '|---|---|---|---|']
        leg = {e['id']: e for e in par['legado']['eventos']}
        for e in par['rotulado']['eventos']:
            a = e['antigo']; n1 = leg[e['id']]['novo']; n2 = e['novo']
            f = lambda n: f"{n['modo']} {n.get('foto') or n.get('comp') or ''}".strip() + (' (revisão)' if n.get('revisao_humana') else '')
            l.append(f"| {e['id']} {e['tipo']}{' ★' if e['critico'] else ''} | {a['modo']} {a['foto'] or ''} | {f(n1)} | {f(n2)} |")
        for k in ('legado', 'rotulado'):
            x = par[k]
            l.append(f"\n{k}: {len(x['bloqueios'])} bloqueio(s), {len(x['revisoes'])} revisão(ões), {len(x['divergencias'])} divergência(s)")
            for rv in x['revisoes']:
                l.append(f"- revisão {rv['evento']}: {rv['problema'][:200]}")
        l.append('')
    return '\n'.join(l) + '\n'


# ───────────────────────── validação com dados REAIS (coleta única no CI) ─────────────────────────
def _registro_real(bruto: dict, titulo_fix: str) -> dict | None:
    if not bruto:
        return None
    if bruto['fonte'] == 'Commons':
        return E.registro_commons(bruto['pagina'])
    if bruto['fonte'] == 'NASA':
        return E.registro_nasa((bruto['item'].get('data') or [{}])[0])
    return E._registro('pagina', titulo_fix, [], {}, titulo_fix, '', '', None, pagina=bruto.get('url'), etiquetas_livres=True)


def _visao_real(g: dict, imagem: str, acontecimento: str) -> dict | None:
    """Catálogo + casamento REAIS (Gemini cego). Sem resposta do casamento, 'confere_com' fica 'incerto'."""
    if not g or imagem not in g['ordem_das_imagens']:
        return None
    i = g['ordem_das_imagens'].index(imagem)
    try:
        cat = next(a for a in json.loads(g['catalogo']['texto'])['imagens'] if int(a.get('i', -1)) == i)
    except Exception:
        cat = None
    cas = None
    if 'texto' in g.get('casamento', {}):
        try:
            cas = next((a for a in json.loads(g['casamento']['texto'])['avaliacoes']
                        if int(a.get('imagem', -1)) == i and a.get('acontecimento') == acontecimento), None)
        except Exception:
            cas = None
    if not cat and not cas:
        return None
    tv = (cat or {}).get('texto_visivel') or {}
    return {'origem': 'gemini_cego', 'viu_legenda': False, 'natureza': (cat or {}).get('natureza'),
            'generica': bool((cat or {}).get('generica')), 'texto_visivel': tv,
            'confere_com': (cas or {}).get('confere_com', 'incerto'), 'classe_confere': (cas or {}).get('classe_confere'),
            'confianca': (cas or {}).get('confianca', 'baixa' if not cas else 'media'),
            'catalogo': {'natureza': (cat or {}).get('natureza'), 'generica': bool((cat or {}).get('generica')),
                         'acao_em_curso': (cat or {}).get('acao_em_curso')} if cat else None,
            'casamento_respondeu': bool(cas)}


def validacao_real() -> dict:
    base = RAIZ_TESTES / 'evidencia'
    regs = json.loads((base / 'coleta_real' / 'registros.json').read_text(encoding='utf-8'))
    gem = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in (base / 'coleta_real' / 'gemini').glob('*.json')}
    linhas = []
    for arq in ('desenvolvimento.json', 'reservado.json'):
        fix = json.loads((base / arq).read_text(encoding='utf-8'))
        for dom, d in fix['dominios'].items():
            for c in d['casos']:
                r = regs.get(f"{dom}/{c['imagem']}")
                if not r:
                    continue
                ev = _ev(d, c['acontecimento'])
                reg_real = _registro_real(r.get('bruto'), d['imagens'][c['imagem']]['registro'].get('titulo'))
                vis_rot = visao(c, ev, 'correta')
                vis_real = _visao_real(gem.get(dom), c['imagem'], c['acontecimento'])
                lin = {'conjunto': fix['grupo'], 'id': c['id'], 'dominio': dom, 'imagem': c['imagem'], 'esperado': c['esperado'],
                       'cenario': E.avaliar(ev, registro(d['imagens'][c['imagem']]['registro']), vis_rot)['nivel'],
                       'registro_real': E.avaliar(ev, reg_real, vis_rot)['nivel'] if reg_real else 'sem registro',
                       'real': None, 'gemini': vis_real, 'arquivo': r.get('arquivo')}
                if reg_real and vis_real:
                    a = E.avaliar(ev, reg_real, vis_real)
                    lin['real'], lin['motivo_real'] = a['nivel'], '; '.join(a['motivos'][:2])
                linhas.append(lin)
    return {'linhas': linhas}


def validacao_real_md(v: dict) -> str:
    l = ['# Validação com dados reais (coleta única no CI)', '',
         '- **cenário**: registro montado no gabarito + visão rotulada · **registro real**: metadados coletados + visão rotulada · '
         '**real**: metadados coletados + resposta do Gemini cego (sem resposta do casamento → "incerto", nunca PROVA)', '',
         '| Conjunto | Caso | Imagem | Esperado | Cenário | Registro real | Real (Gemini) | Gemini: natureza / confere / confiança |',
         '|---|---|---|---|---|---|---|---|']
    for x in v['linhas']:
        g = x['gemini'] or {}
        gtxt = f"{g.get('natureza')} / {g.get('confere_com')} / {g.get('confianca')}" if g else '—'
        l.append(f"| {x['conjunto']} | {x['id']} | {x['imagem']} | {x['esperado']} | {x['cenario']} | {x['registro_real']} | {x['real'] or '—'} | {gtxt} |")
    fp = [x['id'] for x in v['linhas'] if 'PROVA' in (x['registro_real'], x['real']) and x['esperado'] != 'PROVA']
    fr = [x['id'] for x in v['linhas'] if x['esperado'] == 'PROVA' and x['registro_real'] != 'PROVA']
    l += ['', f'- Falsas provas com dados reais: {len(fp)} {fp}', f'- Provas esperadas não alcançadas com o registro real: {len(fr)} {fr}']
    return '\n'.join(l) + '\n'
