"""VIABILIDADE DO ACERVO antes de fechar o storyboard (decisão do Heitor, 17/11, após o diagnóstico 44049021691: o diretor
escolheu três "vídeos reais" sem saber se existia vídeo comprovado, e as três cenas viraram placas de diagnóstico).

Ordem, sem chamada de IA:
1. Cada cena que pede REGISTRO procura primeiro na biblioteca de mídia COMPROVADA (procedência + licença + evidência de
   correspondência factual, reutilizável entre execuções). Itens reprovados nunca entram.
2. Sem mídia comprovada do tipo pedido → outra forma adequada, por regra: vídeo → foto comprovada do mesmo lugar/objeto
   (se a ação for mostrada noutra cena que a demonstra) → esquema/mapa/tipografia já disponíveis. Nada de registro
   inventado nem imagem de outro lugar.
3. Repetição: o mesmo componente de esquema no máximo 2 vezes; a 3ª ocorrência troca de forma (fluxo no mapa do episódio,
   escala ou tipografia), sem inventar dados.
Busca nova (APIs + visão) só quando o pedido permite (`buscar_novas`) — e mesmo assim falha fechada.
"""
from __future__ import annotations

import copy
import json
import re
import unicodedata
from pathlib import Path

from src.v4.componentes import COMPONENTES, DEMONSTRAM_ACAO

BIB = Path(__file__).with_name('biblioteca_comprovada.json')
MAX_MESMO_ESQUEMA = 2
SCORE_MIN = 2                                  # termos em comum entre o que a cena precisa e o que o item mostra
GEO = re.compile(r'\b(mar|oceano|atl[aâ]ntico|pac[ií]fico|lago|rio|caribe)\b', re.I)
PARADAS = {'de', 'da', 'do', 'das', 'dos', 'a', 'o', 'as', 'os', 'e', 'em', 'no', 'na', 'com', 'um', 'uma', 'the', 'of', 'and', 'in',
           'que', 'para', 'por', 'se', 'ao', 'mais', 'seu', 'sua', 'entre'}


def _norm(t) -> str:
    return ''.join(ch for ch in unicodedata.normalize('NFD', str(t or '').lower()) if unicodedata.category(ch) != 'Mn')


def _tokens(*textos) -> set[str]:
    return {w for t in textos for w in re.findall(r'[a-z0-9]{3,}', _norm(t)) if w not in PARADAS}


def carregar(arq: Path = BIB) -> dict:
    return json.loads(arq.read_text(encoding='utf-8')) if arq.exists() else {'itens': [], 'reprovados': []}


def _lugares(pedido: dict, ep: dict) -> set[str]:
    from src.v4.acervo_v4 import nomes_proprios
    consultas = [q for c in ep['cenas'] for q in ((c.get('busca') or {}).get('consultas_en') or [])]
    return nomes_proprios(consultas) | _tokens(pedido.get('titulo', ''), pedido.get('pergunta', '')) & {'panama', 'gatun', 'miraflores'}


def candidatos(c: dict, bib: dict, lugares: set[str], natureza: str = 'foto') -> list[tuple[int, dict]]:
    """itens comprovados do MESMO lugar que mostram o que a cena precisa (sobreposição de termos, sem IA)"""
    b = c.get('busca') or {}
    alvo = _tokens(b.get('deve_mostrar'), c.get('o_que_precisa_aparecer'), ' '.join(b.get('consultas_en') or []))
    rep = {r['id'] for r in bib.get('reprovados') or []}
    out = []
    for it in bib.get('itens') or []:
        if it['id'] in rep or it.get('natureza') != natureza or not it.get('licenca') or not it.get('credito'):
            continue
        if not (set(it.get('lugar') or []) & lugares):
            continue
        p = it.get('prova') or {}
        if p.get('midia_corresponde') is not True:
            continue
        s = len(alvo & (_tokens(it.get('mostra'), it.get('titulo')) | set(it.get('termos') or [])))
        if s >= SCORE_MIN:
            out.append((s, it))
    return sorted(out, key=lambda x: -x[0])


def _demonstrada_em(c: dict, cenas: list[dict]) -> str | None:
    """outra cena que DEMONSTRA a mesma ação (modalidade capaz + termos da ação em comum)"""
    alvo = _tokens((c.get('prova') or {}).get('acao'), (c.get('prova') or {}).get('resultado'), c.get('fala'))
    melhor = None
    for o in cenas:
        if o is c or o['modalidade'] not in DEMONSTRAM_ACAO or o.get('busca'):
            continue
        p = o.get('params') or {}
        s = len(alvo & _tokens((o.get('prova') or {}).get('acao'), (o.get('prova') or {}).get('resultado'), ' '.join(map(str, p.get('etapas') or [])), o.get('fala')))
        if s >= 2 and (not melhor or s > melhor[0]):
            melhor = (s, o['id'])
    return melhor[1] if melhor else None


def _mapa_do_episodio(cenas: list[dict]) -> dict | None:
    return next((o for o in cenas if o['componente'] == 'mapa.rota' and (o.get('params') or {}).get('rota_osm')), None)


def _reformar_esquema(c: dict, cenas: list[dict], usos: dict) -> tuple[str, dict] | None:
    """3ª ocorrência do mesmo esquema → outra forma que já existe no motor, com parâmetros DERIVADOS do episódio"""
    mapa = _mapa_do_episodio(cenas)
    p = c.get('params') or {}
    if mapa and GEO.search(c.get('fala') or '') and usos.get('mapa.rota', 0) < MAX_MESMO_ESQUEMA:
        q = copy.deepcopy(mapa['params'])
        rot = str((p.get('etapas') or [''])[-1])[:40] or None
        q['rota'] = {'de': .05, 'ate': .9, **({'rotulo_distancia': rot} if rot else {})}
        q['pontos'] = [dict(x, t=round(.15 + .2 * k, 2)) for k, x in enumerate(q.get('pontos') or [])]
        q['areas'] = [dict(x, t=round(.05 + .15 * k, 2)) for k, x in enumerate(q.get('areas') or [])]
        q.pop('localizador', None)
        return 'mapa.rota', q
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*metros', c.get('fala') or '')
    if m and usos.get('dados.escala', 0) < MAX_MESMO_ESQUEMA:
        return 'dados.escala', {'titulo': str(p.get('lago') or '')[:30], 'alvo': float(m.group(1).replace(',', '.')), 'referencias': [], 'passo_m': 5}
    return None


def resolver(ep: dict, pedido: dict, bib: dict | None = None) -> tuple[dict, list[dict]]:
    """devolve (episódio com formas viáveis, relatório por cena). Não chama IA nem rede."""
    bib = bib or carregar()
    ep = copy.deepcopy(ep)
    cenas = ep['cenas']
    lugares = _lugares(pedido, ep)
    usados, rel, usos = set(), [], {}
    for c in cenas:                                       # 1–2: registro
        r = {'cena': c['id'], 'pedido': c['componente']}
        b = c.get('busca')
        if b:
            nat = 'video' if b.get('tipo') == 'video' or c['componente'] == 'registro.video' else 'foto'
            ok = [x for x in candidatos(c, bib, lugares, nat) if x[1]['id'] not in usados]
            if ok:
                it = ok[0][1]
                usados.add(it['id'])
                c['params'] = {**(c.get('params') or {}), 'asset': 'bib:' + it['id']}
                r.update(decisao='biblioteca', asset=it['id'], score=ok[0][0])
            else:
                fotos = [x for x in candidatos(c, bib, lugares, 'foto') if x[1]['id'] not in usados] if nat == 'video' else []
                dem = _demonstrada_em(c, cenas) if c.get('acao_fisica') else None
                if fotos and (not c.get('acao_fisica') or dem):
                    it = fotos[0][1]
                    usados.add(it['id'])
                    c.update(modalidade='registro_foto', componente='registro.foto',
                             params={'asset': 'bib:' + it['id'], **({'enquadramento': 'objeto'} if it.get('roi') else {})})
                    c['busca'] = {**b, 'tipo': 'foto'}
                    if dem:
                        c['demonstrada_em'] = dem
                    r.update(decisao='troca_de_forma', para='registro.foto', asset=it['id'], score=fotos[0][0], demonstrada_em=dem,
                             motivo=f'nenhum {nat} comprovado; foto comprovada do mesmo lugar/objeto' + (f'; a ação é mostrada em {dem}' if dem else ''))
                elif pedido.get('buscar_novas'):
                    r.update(decisao='busca_nova', motivo='sem item comprovado na biblioteca; busca com falha fechada')
                else:
                    r.update(decisao='inviavel', motivo=f'nenhum {nat} nem foto comprovados para {c.get("o_que_precisa_aparecer")!r}')
        rel.append(r)
    for c, r in zip(cenas, rel):                          # 3: repetição de esquema
        comp = c['componente']
        usos[comp] = usos.get(comp, 0) + 1
        if c['modalidade'] == 'esquema_2d' and usos[comp] > MAX_MESMO_ESQUEMA:
            nova = _reformar_esquema(c, cenas, usos)
            if nova:
                usos[comp] -= 1
                comp2, params = nova
                c.update(componente=comp2, modalidade=COMPONENTES[comp2]['modalidades'][0], params=params)
                usos[comp2] = usos.get(comp2, 0) + 1
                r.update(repeticao=f'{comp} já usado {MAX_MESMO_ESQUEMA}×: virou {comp2} (parâmetros do próprio episódio)')
            else:
                r.update(repeticao=f'{comp} usado {usos[comp]}× — sem forma alternativa: revisão humana')
        r['final'] = c['componente']
    return ep, rel


def acervo_da_biblioteca(ep: dict, pasta: Path, bib: dict | None = None, baixar=None) -> dict:
    """baixa (ou usa do cache) os itens 'bib:' do episódio e devolve o acervo no formato do V4"""
    from src.v4 import acervo_v4
    bib = bib or carregar()
    por_id = {it['id']: it for it in bib['itens']}
    baixar = baixar or acervo_v4.baixar
    acv = {}
    for c in ep['cenas']:
        a = (c.get('params') or {}).get('asset')
        if not (isinstance(a, str) and a.startswith('bib:')):
            continue
        it = por_id[a[4:]]
        aid = f"b{len(acv) + 1}"
        x = baixar({'url': it['url'], 'titulo': it['titulo'], 'credito': it['credito']}, pasta, aid)
        acv[aid] = {'id': aid, 'arq': x['arq'], 'wh': [x.get('w'), x.get('h')] if x.get('w') else it['wh'], 'titulo': it['titulo'],
                    'desc': it.get('mostra'), 'ano': it.get('ano'), 'credito': it['credito'], 'licenca': it['licenca'], 'fonte_url': it['url'],
                    'roi': it.get('roi'), 'escolha': {'metodo': 'biblioteca_comprovada', 'prova': 'PROVADO', 'evidencia': it.get('prova'), 'item': it['id']}}
        c['params']['asset'] = aid
    return acv
