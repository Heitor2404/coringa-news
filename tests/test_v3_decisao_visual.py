"""Regressões da DECISÃO visual (correção estrutural de 16/11). Escritas ANTES da correção: falham no motor de 4b2aa20.

Os casos vêm de problemas reais de Londres (dimensões, regiões e intenção de enquadramento dos planos), mas nada aqui
é exceção para Londres: o motor recebe só mídia, regiões e a intenção do plano, como em qualquer tema.
A medida principal é a OCUPAÇÃO: fração do quadro 1080×1920 coberta pela(s) imagem(ns) do plano. Calibração
(tests/dados/londres_decisoes_humanas.json, vereditos do Heitor): aprovados mantêm 1,00; reprovados ficam entre 0,31 e 0,65.
"""
import json
from pathlib import Path

import pytest

from src.v2 import diretor
from src.v3 import geometria as G

W, H = 1080, 1920
OCUP_MIN = 0.80          # calibrado nos 13 vereditos (todos os reprovados < 0,66; todos os aprovados = 1,00)


def amostras(sc, passo=0.1):
    """Ocupação e escala útil ao longo do plano. Usa geometria.ocupacao quando existe (motor novo); no motor antigo,
    a conta equivalente com a transformação única do doc.plano (o que o palco desenha)."""
    p = sc['params']
    dur = sc['end'] - sc['start']
    out = []
    for i in range(int(dur / passo) + 1):
        t = i * passo
        if hasattr(G, 'ocupacao'):
            o = G.ocupacao(p, t)
            out.append((o['ocupacao'], o['escala_util']))
        else:
            s, tx, ty = G.transform(p['cam'], t, p['wh'], p.get('layout') or 'cobrir')
            iw, ih = p['wh']
            area = max(0, min(W, tx + iw * s) - max(0, tx)) * max(0, min(H, ty + ih * s) - max(0, ty))
            out.append((area / (W * H), s))
    return out


def _cena(titulo, wh, regioes, **plano):
    sha = 'sha-' + titulo
    acervo = {'m': {'id': 'm', 'arq': '/x.jpg', 'wh': list(wh), 'sha': sha, 'credito': 'c', 'titulo': titulo, 'desc': titulo}}
    reg = {sha: {'objetos': {k: {'caixa': v, 'visivel': True, 'ancoravel': True} for k, v in regioes.items()}}}
    pal = [{'w': w, 's': i * .4, 'e': i * .4 + .35} for i, w in enumerate(('o fogo começou na padaria do rei e tomou a cidade inteira ' * 3).split())]
    pl = {'evento_id': 'e1', 'fato_id': 'f1', 'funcao_narrativa': 'contexto', 'recurso_visual': {'tipo': 'foto', 'id': 'm'},
          'funcao_documental': 'CONTEXTO', 'acao_visual': 'x', 'composicao': 'doc.plano', 'tempo_inicio': 0, 'tempo_fim': 6,
          'fala': 'o fogo começou na padaria do rei'}
    pl.update(plano)
    cenas, reg_ = diretor.montar({'planos': [pl]}, acervo, reg, pal, {'f1'})
    return cenas[0], reg_[0]


# ---------------------------------------------------------------- 1. abertura
def test_abertura_nao_recua_reduzindo_a_presenca_da_imagem():
    """Londres 0–7 s: a pintura começa cobrindo o quadro e recua até uma faixa (ocupação 1,00 → 0,46)."""
    sc, _ = _cena('Pintura do Grande Incêndio, c. 1675', (1920, 1118),
                  {'cidade_em_chamas': [0.18, 0.33, 0.6, 0.32], 'chamas_centro': [0.36, 0.38, 0.2, 0.2]},
                  funcao_narrativa='gancho', movimento_camera='revelar', objeto_principal='chamas_centro',
                  plano_inicial='detalhe', plano_final={'objeto': 'cidade_em_chamas', 'enquadramento': 'objeto'})
    oc = [o for o, _ in amostras(sc)]
    assert oc[0] >= 0.95, 'gancho deve começar com o assunto ocupando o quadro'
    assert min(oc) >= OCUP_MIN, f'abertura perdeu presença: ocupação mínima {min(oc):.2f}'
    assert oc[-1] >= oc[0] - 0.05, f'abertura encolheu: {oc[0]:.2f} → {oc[-1]:.2f}'


def test_receita_de_gancho_nao_produz_recuo_automatico():
    from src.v3 import receitas
    r = next(x for x in receitas.todas() if x['id'] == 'R-GANCHO-IMPACTO')
    enq = r.get('enquadramento') or {}
    # a receita do gancho não pode MANDAR afastar: começo no detalhe e fim no contexto/geral é recuo automático
    ordem = ['detalhe', 'objeto', 'contexto', 'geral']
    if enq.get('inicial') in ordem and enq.get('final') in ordem:
        assert ordem.index(enq['final']) <= ordem.index(enq['inicial']), f"receita do gancho manda recuar: {enq}" 
    sc, _ = _cena('Foto de impacto', (1920, 1280), {'assunto': [0.4, 0.35, 0.2, 0.3]}, funcao_narrativa='gancho',
                  movimento_camera=r['movimento'], objeto_principal='assunto',
                  plano_inicial=enq.get('inicial') or 'objeto', plano_final=enq.get('final') or 'objeto')
    oc = [o for o, _ in amostras(sc)]
    assert min(oc) >= OCUP_MIN and oc[-1] >= oc[0] - 0.05


# ---------------------------------------------------------------- 2. gravuras horizontais
def test_gravura_horizontal_nao_vira_cartao_de_slideshow():
    """Londres 21–25 s: gravura de 1560×873 encolhe para um cartão sobre fundo escuro (ocupação 0,82 → 0,31)."""
    sc, reg = _cena('Victorian engraving after Visscher', (1560, 873),
                    {'fumaca': [0.22, 0.17, 0.5, 0.25], 'cidade': [0.0, 0.38, 1.0, 0.14]},
                    funcao_narrativa='consequencia', movimento_camera='revelar', objeto_principal='fumaca',
                    plano_inicial={'objeto': 'fumaca', 'enquadramento': 'detalhe'}, plano_final={'objeto': 'cidade', 'enquadramento': 'objeto'})
    oc = [o for o, _ in amostras(sc)]
    assert min(oc) >= OCUP_MIN, f'gravura virou cartão: ocupação mínima {min(oc):.2f} (layout {sc["params"].get("layout")})'
    assert sc['params'].get('layout') != 'integral'


def test_gravura_pequena_recua_so_com_revelacao_e_sem_perder_ocupacao():
    sc, _ = _cena('Woodcut, 1612', (1920, 1515), {'homens': [0.12, 0.1, 0.35, 0.6], 'casa': [0.5, 0.05, 0.4, 0.8]},
                  movimento_camera='revelar', objeto_principal='homens',
                  plano_inicial={'objeto': 'homens', 'enquadramento': 'objeto'}, plano_final='geral')
    oc = [o for o, _ in amostras(sc)]
    assert min(oc) >= OCUP_MIN and oc[-1] >= oc[0] - 0.15


# ---------------------------------------------------------------- 3. mapa
def test_mapa_amplo_continua_legivel_e_ocupando_o_quadro():
    """Londres 7–12 s e 38–44 s: o mapa inteiro em faixa (escala 0,54–0,61, ocupação 0,40)."""
    sc, _ = _cena('Map of London showing the extent of the Great Fire, 1666', (2000, 1265),
                  {'cidade': [0.12, 0.12, 0.75, 0.5], 'pudding_lane': [0.66, 0.57, 0.04, 0.05]},
                  funcao_narrativa='contexto', movimento_camera='fixo', objeto_principal='cidade',
                  plano_final=[0.05, 0.0, 0.9, 1.0])                    # a direção pediu a extensão inteira (como em Londres)
    am = amostras(sc)
    assert min(o for o, _ in am) >= OCUP_MIN, f'mapa pequeno: ocupação {min(o for o, _ in am):.2f}'
    assert min(e for _, e in am) >= 0.8, f'mapa ilegível: escala útil {min(e for _, e in am):.2f} (< 0,8 px por px do mapa)'


# ---------------------------------------------------------------- 4. documento horizontal
def test_documento_horizontal_tem_composicao_editorial():
    """Londres 12–15 s: placa 3840×2400 vira faixa sobre fundo preto; precisa ser mostrada inteira E legível."""
    sc, _ = _cena('Thomas Faryner shop plaque, Pudding Lane', (3840, 2400),
                  {'placa': [0.04, 0.12, 0.92, 0.72], 'paragrafo': [0.37, 0.22, 0.56, 0.23]},
                  funcao_documental='DOCUMENTO', movimento_camera='fixo', objeto_principal='paragrafo', plano_final='geral')
    am = amostras(sc)
    assert min(o for o, _ in am) >= OCUP_MIN, f'documento sobre fundo vazio: ocupação {min(o for o, _ in am):.2f}'
    assert min(e for _, e in am) >= 0.45, 'o trecho principal do documento precisa de escala legível'
    p = sc['params']
    assert p.get('layout') == 'editorial' and p.get('visao_geral') == [0, 0, 1, 1], 'documento inteiro visível na composição'


# ---------------------------------------------------------------- recuo e câmera
def test_localizar_sem_revelacao_nao_recua():
    sc, reg = _cena('Foto de rua', (3000, 2000), {'placa': [0.45, 0.4, 0.08, 0.08]}, movimento_camera='localizar',
                    objeto_principal='placa')
    ss = [e for _, e in amostras(sc)]
    assert ss[-1] >= ss[0] * 0.95, f'recuo automático: escala {ss[0]:.2f} → {ss[-1]:.2f}'


def test_recuo_que_revela_e_mantem_quadro_cheio_e_permitido():
    """P1b aprovada: Golden Boy (menino → nicho e inscrição) e Monumento (base → inteiro) recuam cobrindo o quadro."""
    sc, reg = _cena('Golden Boy of Pye Corner', (3672, 4041),
                    {'menino': [0.41, 0.24, 0.15, 0.40], 'inscricao': [0.29, 0.76, 0.33, 0.19]},
                    movimento_camera='revelar', objeto_principal='menino', revela=['inscricao'],
                    plano_inicial={'objeto': 'menino', 'enquadramento': [0.33, 0.2, 0.32, 0.5]},
                    plano_final={'objeto': 'menino', 'enquadramento': [0.25, 0.20, 0.48, 0.76]})
    am = amostras(sc)
    assert am[-1][1] < am[0][1] * 0.85 and min(o for o, _ in am) >= 0.95


# ---------------------------------------------------------------- fiscal: decisões ruins nos exemplos reais
CALIBRADOS = {'F-IMAGEM-PEQUENA', 'F-OCUPACAO-QUEDA', 'F-GANCHO-PERDE-IMPACTO', 'F-MAPA-ILEGIVEL'}
CASOS = json.loads(Path('tests/dados/londres_decisoes_humanas.json').read_text(encoding='utf-8'))['cenas']


@pytest.mark.parametrize('c', CASOS, ids=[f"{c['versao']}-p{c['plano']}-{c['veredito']}" for c in CASOS])
def test_fiscal_de_decisao_concorda_com_o_veredito_humano(c):
    from src.v3 import fiscal_editorial as F
    sc = {'comp': 'doc.plano', 'start': 0.0, 'end': c['dur'], 'params': {**c['params'], 'natureza': c['natureza']},
          'direcao': {'funcao_narrativa': c['funcao_narrativa']}}
    ach = F.decisoes({'scenes': [sc]}, [{}], indice_gancho=0 if c['plano'] == 0 else None)
    # os vereditos julgaram ocupação, encolhimento, legibilidade e abertura; anotação é outra categoria (teste abaixo)
    graves = [a for a in ach if a['classe'] in ('revisao', 'bloqueio') and a['codigo'] in CALIBRADOS]
    if c['veredito'] == 'reprovado':
        assert graves, f"{c['motivo']}: o fiscal deixou passar"
    else:
        assert not graves, f"aprovado pelo Heitor, mas o fiscal acusou: {[a['codigo'] for a in graves]}"


def test_fiscal_acha_seta_desenhada_para_fora_do_quadro_no_mapa_aprovado():
    """Achado novo (não julgado nos vereditos): no mapa da P1b, a seta 'TERÇA: PARA O OESTE' começa a ser desenhada
    rumo a um ponto ainda fora do quadro (x −393 → 11 px em 1 s) enquanto a câmera vai para o oeste. É revisão, não bloqueio."""
    from src.v3 import fiscal_editorial as F
    c = next(c for c in CASOS if c['versao'] == 'p1b' and c['plano'] == 7)
    sc = {'comp': 'doc.plano', 'start': 0.0, 'end': c['dur'], 'params': {**c['params'], 'natureza': 'mapa'}}
    ach = [a for a in F.decisoes({'scenes': [sc]}, [{}], indice_gancho=None) if a['codigo'] == 'F-ANOTACAO-PREJUDICADA']
    assert len(ach) == 1 and ach[0]['classe'] == 'revisao' and 'PARA O OESTE' in ach[0]['problema']


def test_critico_de_acao_essencial_so_com_foto_e_bloqueado():
    from src.v3 import fiscal_editorial as F
    sc = {'comp': 'doc.plano', 'start': 0, 'end': 4, 'params': {'wh': [2000, 2000], 'cam': [{'t': 0, 'caixa': [.2, .2, .5, .5]}], 'layout': 'cobrir', 'natureza': 'foto'}}
    ev = [{'id': 'e1', 'tipo': 'mecanismo', 'critico': True, 'viaveis': ['mecanismo.estados']}]
    cods = {a['codigo'] for a in F.decisoes({'scenes': [sc]}, [{'evento_id': 'e1'}], eventos=ev)}
    assert 'F-ACAO-SEM-ESQUEMA' in cods
    cods = {a['codigo'] for a in F.decisoes({'scenes': [sc]}, [{'evento_id': 'outro'}], eventos=ev)}
    assert 'F-CRITICO-SEM-REPRESENTACAO' in cods


def test_foto_sem_resolucao_troca_pela_alternativa_do_acervo():
    acervo = {'baixa': {'id': 'baixa', 'arq': '/a.jpg', 'wh': [480, 640], 'sha': 'a', 'credito': 'c', 'titulo': 'statue'},
              'boa': {'id': 'boa', 'arq': '/b.jpg', 'wh': [3600, 4000], 'sha': 'b', 'credito': 'c', 'titulo': 'statue'}}
    pl = {'evento_id': 'e1', 'fato_id': 'f1', 'funcao_narrativa': 'contexto', 'recurso_visual': {'tipo': 'foto', 'id': 'baixa'},
          'funcao_documental': 'CONTEXTO', 'acao_visual': 'x', 'composicao': 'doc.plano', 'tempo_inicio': 0, 'tempo_fim': 4,
          'fala': 'x', 'alternativas': ['boa']}
    cenas, reg = diretor.montar({'planos': [pl]}, acervo, {}, [{'w': 'x', 's': 0, 'e': .3}], {'f1'})
    assert cenas[0]['params']['img'] == '/b.jpg' and cenas[0]['params']['layout'] == 'cobrir'
    assert any(d['codigo'] == 'MIDIA-ALTERNATIVA' for d in reg[0]['degradacoes'])


def test_documento_em_retrato_nao_vira_editorial_com_faixas_pretas():
    """ERR-041 (microcena Panamá, 16/11): carta náutica 11330×18230 (retrato) virou editorial; a visão geral não
    preenchia a largura e ficou com faixas pretas laterais. Editorial só serve para documento mais largo que o painel."""
    sc, reg = _cena('Carta náutica do Canal do Panamá, 1914 (mapa)', (11330, 18230),
                    {'canal': [0.4, 0.3, 0.3, 0.5]}, objeto_principal='canal', layout='editorial',
                    plano_inicial='contexto', plano_final='contexto')
    p = sc['params']
    assert p.get('layout') != 'editorial', 'documento em retrato não preenche a largura na visão geral'
    assert min(o for o, _ in amostras(sc)) >= 0.99, 'sem fundo vazio'
