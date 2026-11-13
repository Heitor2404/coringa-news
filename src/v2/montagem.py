"""MONTAGEM V2: do roteiro/dados do motor atual para cenas V2 (direção visual por acontecimento, ritmo e continuidade).

Entrada: o `dados` que o motor atual entrega ao template (scenes com tipo/fala/img/…, captions, meta).
Saída: (dados_v2, direcao) — dados_v2 com meta.motor = 'v2' para o palco V2; `direcao` explica a decisão de cada
cena (composição, acontecimento, motivo, limitação), e alimenta o fiscal_v2.

Regras de montagem:
  M1 estrutura: gancho → abertura.pergunta; revelação → revelacao.surpresa (virada no instante em que a resposta é
     dita); fechamento → encerramento.editorial; tipos gráficos do roteiro → composição equivalente;
  M2 cenas de foto passam por capacidades.escolher(): acontecimento crítico ganha a composição que o mostra;
  M3 CONTINUIDADE: cenas seguidas que narram o MESMO mecanismo viram UMA composição (as etapas acompanham a fala),
     em vez de cortar entre telas soltas;
  M4 pedaços da mesma ideia (sub) com a mesma foto viram um plano só se couberem em 5 s; senão, enquadramentos
     diferentes (sem repetir a mesma imagem igual);
  M5 foto antiga/de arquivo (etiqueta com ano < 1960 ou recorte de scanner) vai para foto.historica;
  M6 número só entra se passar em fatos.validar(); se não passar, a cena fica BLOQUEADA (registrada), nunca "chamativa";
  M7 ritmo: foto parada > 5 s ganha segundo foco; nenhuma imagem repete fora da mesma ideia.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

from src.v2 import acervo_v2, capacidades, contrato, fatos

ESTATICO_MAX = 5.0


def _limpo(s) -> str:
    return re.sub(r'\*', '', str(s or '')).strip()


def _num_m(txt: str) -> float | None:
    m = re.search(r'(\d+[.,]?\d*)\s*metros', _limpo(txt))
    return float(m.group(1).replace(',', '.')) if m else None


def _virada(sc: dict, captions: list[dict]) -> float:
    alvo = {w.lower() for w in re.findall(r'\w{3,}', _limpo(sc.get('resposta', '')))}
    for c in captions:
        for w in c['words']:
            t = w.get('s', c['start'])
            if sc['start'] <= t <= sc['end'] and re.sub(r'\W', '', w['w'].lower()) in alvo:
                return round(max(.5, t - sc['start'] - .1), 2)
    return 1.0


def _img(sc: dict, base: Path | None) -> str | None:
    i = sc.get('img')
    if not i:
        return None
    p = Path(i)
    if not p.is_absolute() and base:
        p = base / p
    return str(p) if p.exists() else None


def _fase_eclusa(sc: dict) -> int:
    t = capacidades._n(sc.get('fala', ''))
    if re.search(r'iguala|se abre|abre', t):
        return 2
    if re.search(r'ench|sob|desc|esvazi|gravidade|agua vem', t):
        return 1
    return 0


def converter(dados: dict, base: Path | None = None, fatos_corrigidos: dict | None = None) -> tuple[dict, list[dict]]:
    """`base`: pasta onde estão as imagens (img/...). `fatos_corrigidos`: {índice da cena: valor (src/v2/fatos.py)} —
    a correção editorial de um número, que ainda assim passa pela validação."""
    meta = copy.deepcopy(dados.get('meta', {}))
    fontes = meta.get('fontes') or []
    caps = dados.get('captions', [])
    v1 = dados['scenes']
    ctx_tema = ' '.join(_limpo(x) for x in [meta.get('titulo'), meta.get('pergunta')] + [s.get('fala') for s in v1])
    desnivel = next((_num_m(s.get('fala', '')) for s in v1 if _num_m(s.get('fala', ''))), None)
    out, direcao, usadas = [], [], {}
    i = 0
    while i < len(v1):
        sc = v1[i]
        tipo = sc.get('tipo')
        img = _img(sc, base)
        nova = {'start': sc['start'], 'end': sc['end'], 'fala': sc.get('fala', ''), 'origem': [i]}
        d = {'cenas_v1': [i], 'inicio': sc['start'], 'fala': _limpo(sc.get('fala'))}
        if tipo == 'gancho':
            nova.update(comp='abertura.pergunta', params={'kicker': ' · '.join(x for x in [meta.get('categoria') or 'CURIOSIDADE', _limpo(sc.get('subtitulo')).split(',')[0]] if x).upper()[:32],
                        'pergunta': sc.get('titulo') or meta.get('titulo'), 'contexto': ', '.join(_limpo(sc.get('subtitulo')).split(',')[1:]).strip().capitalize()})
            if img:
                nova['fundo'] = {'img': img, 'de': 'auto', 'para': 'auto'}
            d.update(comp='abertura.pergunta', motivo='M1: gancho')
        elif tipo == 'mapa':
            pts = [{'nome': p['nome'], 'lon': p['lon'], 'lat': p['lat']} for p in sc.get('pontos') or []]
            km = re.search(r'(\d+)\s*km', _limpo(sc.get('fala', '')))
            if len(pts) >= 2:
                nova.update(comp='mapa.rota', params={'pontos': pts, 'titulo': sc.get('rotulo') or '', 'distancia_km': int(km.group(1)) if km else None, 'folga': .5})
            else:
                nova.update(comp='mapa.localizacao', params={'pontos': pts, 'pais': sc.get('pais')})
            d.update(comp=nova['comp'], motivo='M1: mapa do roteiro')
        elif tipo == 'numero':
            valor = (fatos_corrigidos or {}).get(i) or {'valor': sc.get('valor'), 'prefixo': sc.get('prefixo'), 'unidade': _limpo(sc.get('sufixo')),
                                                        'rotulo': sc.get('rotulo'), 'nota': sc.get('nota'), 'contexto': sc.get('nota') or '', 'fonte': sc.get('fonte')}
            erros = fatos.validar(valor, fontes)
            if erros:
                nova.update(comp='banner.importante', params={'rotulo': 'NÚMERO BLOQUEADO', 'titulo': 'Dado sem verificação', 'texto': '; '.join(e.split(':')[0] for e in erros), 'cor': 'vermelho'}, bloqueada=True)
                if img:
                    nova['fundo'] = {'img': img, 'de': 'auto', 'para': 'auto'}
                d.update(comp=None, bloqueio=erros, motivo='M6: número não passou na validação factual')
            else:
                p = fatos.para_tela(valor)
                nova.update(comp='numero.animado', params=p)
                d.update(comp='numero.animado', motivo='M6: número validado' + (' (correção editorial)' if (fatos_corrigidos or {}).get(i) else ''))
        elif tipo == 'revelacao':
            nova.update(comp='revelacao.surpresa', params={'pergunta': sc.get('pergunta'), 'resposta': sc.get('resposta'), 'detalhe': sc.get('detalhe'),
                                                          'virada': _virada(sc, caps), 'cor': 'amarelo'})
            mec = next((x for x in reversed(out) if x['comp'] in ('mecanismo.eclusa', 'mecanismo.nivel') and x['params'].get('sentido', 'subir') == 'subir'), None)
            if mec:
                # M8 (V2.1): a resposta aparece SOBRE o mecanismo que ela explica (congelado nos níveis iguais), não sobre foto escura
                bp = {**mec['params'], 'planos': False}
                tf = (bp.get('tempos') or [0, 0, (mec['end'] - mec['start']) * .76])[2] + .9
                nova['base'] = {'comp': mec['comp'], 'params': bp, 't': round(tf, 2), 'dur': round(mec['end'] - mec['start'], 2), 'escurece': .15}
                d.update(comp='revelacao.surpresa', motivo='M1: payoff · M8: sobre o mecanismo congelado')
            else:
                if img:
                    nova['fundo'] = {'img': img, 'de': 'auto', 'para': 'auto', 'escurece': 1}
                d.update(comp='revelacao.surpresa', motivo='M1: payoff')
        elif tipo in ('lista', 'cards'):
            it = sc.get('itens') or []
            etapas = [{'titulo': _limpo(x.get('rotulo'))[:22], 'texto': _limpo(x.get('valor'))[:60], 'icone': 'documento'} if isinstance(x, dict) else
                      {'titulo': _limpo(x)[:22], 'texto': '', 'icone': 'documento'} for x in it][:5]
            nova.update(comp='processo.etapas', params={'kicker': _limpo(sc.get('titulo'))[:22] or 'EM RESUMO', 'titulo': '', 'etapas': etapas})
            d.update(comp='processo.etapas', motivo=f'M1: {tipo} → etapas')
        elif tipo == 'linha_tempo':
            nova.update(comp='linha_tempo.historica', params={'titulo': sc.get('titulo', ''), 'eventos': [{'ano': x.get('ano'), 'texto': x.get('texto')} for x in sc.get('itens') or []]})
            d.update(comp='linha_tempo.historica', motivo='M1: linha do tempo')
        elif tipo in ('comparacao', 'escala'):
            it = sc.get('itens') or [{'rotulo': m.get('rotulo'), 'valor': m.get('valor')} for m in (sc.get('marcas') or [])] + ([sc['destaque']] if isinstance(sc.get('destaque'), dict) else [])
            nova.update(comp='grafico.barras', params={'titulo': sc.get('titulo', ''), 'itens': [{'rotulo': _limpo(x.get('rotulo')), 'valor': x.get('valor')} for x in it],
                                                       'unidade': sc.get('unidade', ''), 'fonte': sc.get('fonte') or ''})
            if not sc.get('fonte'):
                nova['bloqueada'] = True
                d.update(comp=None, bloqueio=['F3: gráfico sem fonte'], motivo='M6')
            else:
                d.update(comp='grafico.barras', motivo='M1: comparação')
        elif tipo == 'citacao':
            nova.update(comp='citacao', params={'texto': sc.get('texto'), 'autor': sc.get('autor'), 'papel': sc.get('nota', '')})
            d.update(comp='citacao', motivo='M1: citação')
        elif tipo == 'fechamento':
            rev = next((x for x in reversed(out) if x['comp'] == 'revelacao.surpresa'), None)
            conclusao = ''
            if rev:     # a conclusão vem da resposta que o vídeo deu (sem texto novo inventado)
                r = rev['params']
                conclusao = f"{_limpo(r.get('pergunta')).rstrip('?')}? *{_limpo(r.get('resposta')).capitalize()}*." if r.get('pergunta') else _limpo(r.get('detalhe'))
            nova.update(comp='encerramento.editorial', params={'variante': 'cta' if sc.get('proxima') else 'conclusao', 'resumo': conclusao, 'fontes': fontes,
                                                               'marca': meta.get('marca', '@coringa.explica'), 'proxima': sc.get('proxima'), 'mascote': 'apontando'})
            if rev and rev.get('base'):
                nova['base'] = {**rev['base'], 'escurece': .6}
            d.update(comp='encerramento.editorial', motivo='M1: fechamento')
        else:
            dec = capacidades.escolher(sc, {}, ctx_tema)
            d.update(capacidade=dec.get('capacidade'), critica=dec.get('critica'), trecho=dec.get('trecho'), origem=dec.get('origem'),
                     acontecimento=dec.get('acontecimento'), aviso=dec.get('aviso'))
            if dec.get('comp') in ('mecanismo.eclusa', 'mecanismo.nivel'):
                # M3: junta as cenas seguidas que narram o mesmo mecanismo
                j, grupo = i, []
                while j < len(v1) and v1[j].get('tipo') in ('historia', 'imagem') and capacidades.escolher(v1[j], {}, ctx_tema).get('comp') == dec['comp']:
                    grupo.append(j); j += 1
                descer = any(re.search(r'esvazi|para descer', capacidades._n(v1[k].get('fala', ''))) for k in grupo)
                subir = [k for k in grupo if not re.search(r'esvazi|para descer|inverso', capacidades._n(v1[k].get('fala', '')))]
                if descer and subir and len(subir) < len(grupo):
                    grupo = subir                             # o "inverso" vira a cena seguinte, com sentido próprio
                    j = grupo[-1] + 1
                fim = v1[grupo[-1]]['end']
                tempos, fases_vistas = [0.0, None, None], set()
                for k in grupo:
                    f = _fase_eclusa(v1[k])
                    if f not in fases_vistas and f > 0:
                        tempos[f] = round(v1[k]['start'] - sc['start'], 2)
                    fases_vistas.add(f)
                dur = fim - sc['start']
                tempos[1] = tempos[1] if tempos[1] else round(min(.8, dur * .2) if len(grupo) == 1 else dur * .3, 2)
                tempos[2] = tempos[2] if tempos[2] is not None else round(max(tempos[1] + 1.5, dur * .78), 2)
                sentido = 'descer' if descer and not subir else 'subir'
                nova.update(end=fim, comp=dec['comp'], origem=grupo, fala=' '.join(_limpo(v1[k].get('fala')) for k in grupo),
                            params={'sentido': sentido, 'desnivel_m': desnivel or 26, 'lago': 'LAGO GATÚN' if 'gatun' in capacidades._n(ctx_tema) else 'NÍVEL ALTO',
                                    'mar': 'MAR', 'tempos': tempos, 'kicker': 'MECANISMO · ECLUSA'} if dec['comp'] == 'mecanismo.eclusa' else
                            {'de': 0, 'ate': desnivel or 10, 'max': (desnivel or 10) * 1.2, 'unidade': 'm', 'objeto': 'navio', 'flutua': True})
                if dec['comp'] == 'mecanismo.eclusa' and sentido == 'subir' and tempos[2] < dur - .8:
                    pass
                if dec.get('origem') == 'contrato':
                    nova['params'].update({k: v for k, v in (dec.get('params') or {}).items() if v not in (None, '')})
                d.update(cenas_v1=grupo, comp=dec['comp'], motivo=f"M3: {len(grupo)} cena(s) do mesmo mecanismo numa composição; {dec.get('motivo', '')}",
                         origem=dec.get('origem'), acontecimento=dec.get('acontecimento'))
                out.append(nova); direcao.append(d)
                i = j
                continue
            if dec.get('comp') and dec['comp'] not in contrato.GENERICAS:
                if dec.get('origem') == 'contrato':
                    # V2.2: composição desenhada pelo acontecimento DECLARADO, com os dados declarados (antes, toda composição
                    # que não fosse eclusa/nível/escala caía no ramo de foto, mesmo com o seletor certo)
                    p = dict(dec.get('params') or {})
                    if dec['comp'] in ('foto.historica',) and not p.get('img') and img:
                        p['img'] = img
                    nova.update(comp=dec['comp'], params=p)
                    if img and dec['comp'] in ('revelacao.surpresa', 'destaque.palavras'):
                        nova['fundo'] = {'img': img, 'de': 'auto', 'para': 'auto'}
                    d.update(comp=dec['comp'], motivo=dec.get('motivo', ''), origem='contrato', acontecimento=dec.get('acontecimento'))
                    out.append(nova); direcao.append(d)
                    if img:
                        usadas.setdefault(img, []).append(len(out) - 1)
                    i += 1
                    continue
                # padrão textual achou uma composição desenhada, mas sem dados declarados: a cena fica com foto e a troca
                # é REGISTRADA (o fiscal bloqueia se o acontecimento for crítico — S5), nunca silenciosa
                d['substituicao'] = f"{dec['comp']} reconhecida por padrão textual (\"{dec.get('trecho', '')}\"), sem dados declarados → foto"
            if dec.get('sem_contrato'):
                d['sem_contrato'] = True
            if dec.get('comp') is None:
                d['faltam'] = dec.get('faltam', [])
                # acontecimento crítico sem composição: registra e mantém a imagem (a cena será REPROVADA pelo fiscal)
                nova.update(comp='foto.documental', params={'lugar': _limpo(sc.get('lugar'))[:28]}, limitacao=dec['limitacao'])
                if img:
                    nova['fundo'] = {'img': img, 'de': 'auto', 'para': 'auto'}
                d.update(comp=None, limitacao=dec['limitacao'])
            else:
                # M4: pedaços da mesma ideia com a mesma imagem
                j = i + 1
                while j < len(v1) and v1[j].get('grupo') == sc.get('grupo') and v1[j].get('sub') and v1[j].get('img') == sc.get('img') and v1[j]['end'] - sc['start'] <= ESTATICO_MAX:
                    j += 1
                fim = v1[j - 1]['end']
                lims = [capacidades.escolher(v1[k], {}, ctx_tema) for k in range(i, j)]
                esc = next((x for x in lims if x.get('capacidade') == 'escala' and x.get('comp') is None), None)
                if esc and _num_m(' '.join(v1[k].get('fala', '') for k in range(i, j))):
                    # escala com referências conhecidas (tabela curada, fonte Wikipédia) em vez de foto parada
                    v = _num_m(' '.join(v1[k].get('fala', '') for k in range(i, j)))
                    nova.update(end=fim, origem=list(range(i, j)), fala=' '.join(_limpo(v1[k].get('fala')) for k in range(i, j)), comp='comparacao.grandezas',
                                params=capacidades.escala_com_referencias(v, 'Desnível'))
                    d.update(cenas_v1=list(range(i, j)), comp='comparacao.grandezas', motivo=f'escala: "{esc["trecho"]}" → referências conhecidas')
                    i = j
                    out.append(nova); direcao.append(d)
                    continue
                nova.update(end=fim, origem=list(range(i, j)), fala=' '.join(_limpo(v1[k].get('fala')) for k in range(i, j)))
                etq = str(sc.get('etiqueta') or '')
                ano = re.search(r'(1[5-9]\d\d|20\d\d)', etq + ' ' + str(sc.get('lugar') or ''))
                historica = bool(ano and int(ano.group(1)) < 1960 and etq.startswith('FOTO'))
                rc = acervo_v2.recorte_conteudo(img) if img else [0, 0, 1, 1]
                if img and (historica or rc != [0.0, 0.0, 1.0, 1.0]):
                    nova.update(comp='foto.historica', params={'img': img, 'recorte': rc, 'ano': ano.group(1) if ano else '', 'credito': 'Wikimedia Commons',
                                                               'descricao': _limpo(sc.get('mostrar'))[:60].capitalize()})
                    d.update(comp='foto.historica', motivo='M5: foto de arquivo' + (' com recorte de scanner' if rc != [0.0, 0.0, 1.0, 1.0] else ''))
                elif img:
                    if sc.get('destaque'):
                        nova.update(comp='banner.discreto', params={'rotulo': 'CONTEXTO', 'texto': sc['destaque']})
                    elif sc.get('lugar') and '·' in str(sc.get('lugar')):
                        # lugar com data ("AGUA CLARA · 2016"): identificação no padrão lower third, não etiqueta solta
                        nome, quando = [x.strip() for x in str(sc['lugar']).split('·', 1)]
                        nova.update(comp='lower_third', params={'nome': nome.title()[:28], 'descricao': f"{_limpo(sc.get('mostrar'))[:30]} · {quando}"[:40], 'tipo': 'lugar'})
                    else:
                        nova.update(comp='foto.documental', params={'lugar': _limpo(sc.get('lugar'))[:28]})
                    nova['fundo'] = {'img': img, 'de': 'auto', 'para': 'auto', 'variante': len(usadas.get(img, []))}
                    d.update(comp=nova['comp'], motivo=dec.get('motivo', ''))
                else:
                    nova.update(comp='destaque.palavras', params={'frase': sc.get('destaque') or sc.get('fala')}, limitacao='cena sem imagem e sem acontecimento específico')
                    d.update(comp='destaque.palavras', limitacao='sem imagem')
                if img:
                    usadas.setdefault(img, []).append(len(out))
                i = j
                out.append(nova); direcao.append(d)
                continue
        if img and tipo not in ('fechamento',):
            usadas.setdefault(img, []).append(len(out))
        out.append(nova); direcao.append(d)
        i += 1
    # M7: repetição de imagem fora da mesma ideia
    for img_, idx in usadas.items():
        for k in idx[1:]:
            if set(out[k]['origem']) and v1[out[k]['origem'][0]].get('grupo') == v1[out[idx[0]]['origem'][0]].get('grupo'):
                direcao[k].setdefault('notas', []).append('mesma ideia: mesma foto com outro enquadramento')
                continue
            direcao[k].setdefault('avisos', []).append(f'imagem repetida ({Path(img_).name}) — já usada na cena v2 {idx[0]}')
    for k, sc in enumerate(out):
        if sc['comp'] == 'foto.documental' and sc['end'] - sc['start'] > ESTATICO_MAX:
            direcao[k].setdefault('avisos', []).append(f"foto parada por {sc['end'] - sc['start']:.1f} s (> {ESTATICO_MAX} s)")
    meta['motor'] = 'v2'
    return {'duration': dados['duration'], 'meta': meta, 'scenes': out, 'captions': caps}, direcao
