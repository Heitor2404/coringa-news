"""DECISÃO DE COMPOSIÇÃO DO doc.plano (correção estrutural de 16/11) — layout e câmera escolhidos por regra, em qualquer tema.

LAYOUT, nesta ordem (o 'integral' automático — cartão sobre fundo escuro — deixou de existir):
  1. enquadramento VERTICAL que preserva a informação importante ('cobrir'; recorta no objeto principal quando o pedido
     era mais largo que 9:16 — exceto documento/mapa/arte quando o pedido é ver o todo);
  2. outra mídia do acervo (o diretor troca ANTES, ver diretor.montar: 'alternativas');
  3. composição EDITORIAL para documento, mapa, gravura ou pintura (visão geral inteira + detalhe ampliado);
  4. revisão (bloqueio se o plano é crítico) — com o melhor recorte vertical, nunca com fundo vazio.

CÂMERA (só em 'cobrir'; o editorial é fixo):
  * fixa é o padrão; movimento sem objeto principal, sem 'revela' e sem chave de câmera vira fixo;
  * recuo (escala cai > 15%) só se REVELA algo nomeado em 'revela' (fora do quadro antes, dentro depois), mantendo o
    objeto principal no quadro; senão o trecho de recuo é recusado (o quadro anterior fica);
  * em 'cobrir' a ocupação é sempre 1,0: recuo nunca encolhe a imagem.
Toda decisão vira degradação registrada (aceitável quando o motor resolveu; revisão/bloqueio quando não).
"""
from __future__ import annotations

from src.v3 import geometria as G
from src.v3 import linguagem

DOCUMENTAIS = ('documento', 'mapa', 'gravura', 'pintura')
RECUO = 0.85                  # escala final < 85% da anterior = recuo
AMPLO = 0.45                  # pedido que cobre ≥ 45% da área da fonte = "ver o todo"


def _cabe(c, wh) -> bool:
    return G.visivel(c, wh, 'cobrir') >= .9


def decidir(pl: dict, x: dict, wh, cam: list[dict], roi, obs: dict, enq_obj, enq_det, avanco=None, gancho=False) -> dict:
    """→ {layout, cam, visao_geral?, natureza, degradacoes: [(impacto, codigo, texto, essencial)]}"""
    deg = []
    nat = linguagem.natureza(x)
    documental = nat in DOCUMENTAIS
    pedido = pl.get('layout')
    caixas = [k['caixa'] for k in cam]
    res_ok = G.nat(wh) <= G.SMAX * 1.12
    roi_cabe = roi is None or G.visivel(roi, wh, 'cobrir') >= .95
    amplo = any(c[2] * c[3] >= AMPLO for c in caixas) or pedido == 'integral'
    critico = bool(pl.get('critico'))
    out = {'natureza': nat, 'degradacoes': deg}

    def horizontal(c):          # a visão geral só preenche a largura se o trecho for mais largo que W × (VISAO_MAX·H)
        return c[2] * wh[0] >= c[3] * wh[1] * G.W / (G.VISAO_MAX * G.H) * .98

    def contem(c):
        return roi is None or (c[0] <= roi[0] and c[1] <= roi[1] and c[0] + c[2] >= roi[0] + roi[2] and c[1] + c[3] >= roi[1] + roi[3])

    def visao_geral():          # o maior enquadramento amplo pedido que contém o objeto principal; senão a fonte inteira
        return max((c for c in caixas if c[2] * c[3] >= AMPLO and contem(c)), key=lambda c: c[2] * c[3], default=[0, 0, 1, 1])

    amplo_h = horizontal(visao_geral())

    def editorial():
        visao = visao_geral()
        detalhe = enq_obj if roi else (caixas[-1] if caixas[-1][2] * caixas[-1][3] < AMPLO else [.25, .25, .5, .5])
        e = G.editorial(wh, visao, detalhe)
        deg.append(('aceitavel', 'COMPOSICAO-EDITORIAL', f"{nat} horizontal visto inteiro: visão geral + detalhe ampliado (sem fundo vazio)", False))
        if len(set(map(tuple, caixas))) > 1 or pl.get('camera_chaves'):
            deg.append(('aceitavel', 'MOVIMENTO-EDITORIAL-FIXO', 'composição editorial é fixa: o movimento pedido não entra', False))
        if not e['resolucao_ok']:
            deg.append(('revisao', 'RESOLUCAO-BAIXA', f"detalhe ampliado {e['detalhe']['s']:.1f}× sobre a fonte de {wh[0]}×{wh[1]}: troque a mídia se puder", False))
        out.update(layout='editorial', cam=[{'t': 0, 'caixa': detalhe}], visao_geral=[round(v, 4) for v in visao])
        return out

    if pedido in ('editorial', 'integral') and not amplo_h:
        # documento em retrato: o editorial deixaria faixas vazias ao lado da visão geral → recorte vertical (preferência 1)
        deg.append(('aceitavel', 'EDITORIAL-RECUSADO', f'{nat} em retrato ({wh[0]}×{wh[1]}): a visão geral não preencheria a largura; recorte vertical', False))
        cam = [{**k, 'caixa': k['caixa'] if _cabe(k['caixa'], wh) else _recorte_916(k['caixa'], wh, roi)} for k in cam]
        caixas = [k['caixa'] for k in cam]
        pedido = 'cobrir'
    if pedido == 'editorial' or (pedido == 'integral' and documental and not avanco):
        return editorial()
    if pedido == 'cobrir':
        layout = 'cobrir'
        if not all(_cabe(c, wh) for c in caixas):
            deg.append(('revisao', 'ENQUADRAMENTO-CORTADO', 'layout cobrir pedido: parte do enquadramento fica fora do quadro vertical',
                        bool(roi) and not roi_cabe))
    elif all(_cabe(c, wh) for c in caixas) and res_ok and (not documental or roi_cabe) and not (documental and amplo_h and not gancho and not avanco):
        layout = 'cobrir'
    elif roi is not None and roi_cabe and res_ok and (gancho or avanco or not (documental and amplo_h)):
        # 1. recorte vertical no objeto principal (o que importa cabe; o resto do pedido largo sai)
        novo = enq_obj if _cabe(enq_obj, wh) else enq_det
        cam = [{**k, 'caixa': k['caixa'] if _cabe(k['caixa'], wh) else novo} for k in cam]
        deg.append(('aceitavel', 'ENQUADRAMENTO-VERTICAL', 'enquadramento pedido mais largo que 9:16: recortado no objeto principal', False))
        layout = 'cobrir'
    elif documental and not avanco and amplo_h:
        return editorial()                                              # 3. editorial
    else:
        layout = 'cobrir'                                               # 4. sem solução boa: revisão/bloqueio
        if not res_ok:
            deg.append(('bloqueio' if critico else 'revisao', 'RESOLUCAO-BAIXA',
                        f"foto de {wh[0]}×{wh[1]} precisa de {G.nat(wh):.1f}× para cobrir o quadro e não há composição melhor: troque a mídia", critico))
        else:
            deg.append(('bloqueio' if critico else 'revisao', 'SEM-COMPOSICAO-VERTICAL',
                        'o enquadramento pedido não cabe em 9:16 e a mídia não é documento/mapa/arte: troque a mídia ou o recurso', critico))
    out.update(layout=layout, cam=_politica_camera(pl, cam, wh, obs, roi, deg, gancho))
    return out


def _recorte_916(c, wh, roi=None) -> list:
    """maior recorte 9:16 dentro da caixa c (corta as laterais), centrado no objeto principal quando houver"""
    a = (G.W / G.H) * wh[1] / wh[0]                       # largura normalizada que corresponde a 1 de altura em 9:16
    w = min(c[2], c[3] * a)
    h = min(c[3], w / a)
    cx = (roi[0] + roi[2] / 2) if roi else c[0] + c[2] / 2
    x = min(max(cx - w / 2, c[0]), c[0] + c[2] - w)
    return [round(x, 4), round(c[1] + (c[3] - h) / 2, 4), round(w, 4), round(h, 4)]


def _politica_camera(pl, cam, wh, obs, roi, deg, gancho) -> list[dict]:
    if len(cam) < 2:
        return cam
    if pl.get('movimento_camera') not in (None, 'fixo') and not (pl.get('objeto_principal') or pl.get('revela') or pl.get('camera_chaves')):
        deg.append(('aceitavel', 'MOVIMENTO-SEM-MOTIVO', 'movimento sem objeto principal nem revelação: plano fixo', False))
        return [{'t': 0, 'caixa': cam[-1]['caixa']}]
    revela = [obs[n]['caixa'] for n in (pl.get('revela') or []) if (obs.get(n) or {}).get('caixa')]

    def escala(c):
        return G.transform([{'t': 0, 'caixa': c}], 0, wh, 'cobrir')[0]

    def vis(caixa, quadro):
        s, tx, ty = G.transform([{'t': 0, 'caixa': quadro}], 0, wh, 'cobrir')
        return G.visivel_em(caixa, {'s': s, 'tx': tx, 'ty': ty}, wh)
    novo, recusados = [dict(cam[0])], []
    for k in cam[1:]:
        ant = novo[-1]['caixa']
        if escala(k['caixa']) < RECUO * escala(ant):
            ok = bool(revela) and all(vis(r, k['caixa']) >= .8 and vis(r, ant) < .6 for r in revela) \
                and (roi is None or vis(roi, k['caixa']) >= .8)
            if not ok:
                recusados.append(round(k['t'], 2))
                k = {**k, 'caixa': ant}
        novo.append(dict(k))
    if recusados:
        deg.append(('aceitavel', 'RECUO-RECUSADO',
                    ('gancho: ' if gancho else '') + "recuo sem revelação declarada ('revela') recusado: o quadro anterior fica", False))
    if all(k['caixa'] == novo[0]['caixa'] for k in novo):
        return [{'t': 0, 'caixa': novo[0]['caixa']}]
    # imperceptível NA TELA (escala < 8% e centro < 40 px entre todas as chaves): caixas diferentes que, cobrindo o
    # quadro, dão a mesma imagem não são movimento → fixo
    ts = [G.transform([{'t': 0, 'caixa': k['caixa']}], 0, wh, 'cobrir') for k in novo]
    if all(abs(t[0] / ts[0][0] - 1) < .08 and abs(t[1] - ts[0][1]) < 40 and abs(t[2] - ts[0][2]) < 40 for t in ts):
        deg.append(('aceitavel', 'MOVIMENTO-VIRA-FIXO', 'movimento sem diferença visível na tela: plano fixo (nenhum movimento inventado)', False))
        return [{'t': 0, 'caixa': novo[-1]['caixa']}]
    return novo
