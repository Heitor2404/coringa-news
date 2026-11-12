"""Medidor geométrico do NTC (tests/ntc_geometria.py): prova que ele ENXERGA erro.

Não exige zero erro no motor (isso esconderia problema real). Planta erros conhecidos numa cena real das baratas e
confere que o medidor acusa como "comprovado"; e planta uma sobreposição normal (barata no pé da Val) e confere que
ela NÃO vira erro comprovado. O relatório de verdade sai de `python -m tests.ntc_geometria`.
"""
import copy, json
import pytest

pytest.importorskip('playwright')
from tests import ntc_geometria as G


def _dados():
    return G.dados_do_roteiro(json.loads(G.BARATAS.read_text(encoding='utf-8')))


def _medir(dados, cenas):
    med = G.medir_dados(dados, passo_mov=0.5, passo_parado=1.0, grade=20, so_cenas=cenas)
    return G.agrupar(G.analisar(med, 'controle'))


def _tem(grupos, cena, tipo, ator_tem, nivel='comprovado'):
    return any(g['cena'] == cena and g['tipo'] == tipo and ator_tem in g['ator'] and g['nivel'] == nivel for g in grupos)


@pytest.fixture(scope='module')
def plantado():
    d = _dados()
    rua = next(i for i, c in enumerate(d['cenas']) if c['cen'] == 'rua' and not c.get('val'))
    com_val = next(i for i, c in enumerate(d['cenas']) if c.get('val') and c['cen'] == 'rua')
    d = copy.deepcopy(d)
    # 1) nuvem em cima das casas (base y=1100 → atravessa as fachadas, que vão de ~860 a 1180)
    d['cenas'][rua]['props'].append({'t': 'nuvem', 'w': 320, 'ar': .5, 'anim': 'aparece', 'ceu': True, 'atras': True, 'x': 330, 'y': 1100, 'de': 0})
    # 2) fogo grande na frente do corpo da Val
    vx = d['cenas'][com_val]['val']['x']
    d['cenas'][com_val]['props'].append({'t': 'fogo', 'w': 320, 'ar': 1.5, 'anim': 'aparece', 'ceu': False, 'atras': False, 'x': vx - 160, 'y': 1650, 'de': 0})
    # 3) barata pequena no pé da Val (profundidade normal: não pode virar erro comprovado)
    d['cenas'][com_val]['props'].append({'t': 'barata', 'w': 120, 'ar': .55, 'anim': 'aparece', 'ceu': False, 'atras': False, 'x': vx + 60, 'y': 1760, 'de': 0})
    # 4) lixo metade para fora da tela, parado no chão
    d['cenas'][rua]['props'].append({'t': 'lixo', 'w': 300, 'ar': .7, 'anim': 'aparece', 'ceu': False, 'atras': False, 'x': 930, 'y': 1800, 'de': 0})
    # 5) chinelo "no chão" flutuando na altura da janela
    d['cenas'][rua]['props'].append({'t': 'chinelo', 'w': 150, 'ar': .35, 'anim': 'aparece', 'ceu': False, 'atras': False, 'x': 450, 'y': 1000, 'de': 0})
    return rua, com_val, _medir(d, {rua, com_val})


def test_acusa_nuvem_atravessando_casa(plantado):
    rua, _, g = plantado
    assert _tem(g, rua, 'ceu_sobre_estrutura', 'nuvem')


def test_acusa_fogo_cobrindo_a_val(plantado):
    _, com_val, g = plantado
    assert _tem(g, com_val, 'cobre_val', 'fogo')


def test_acusa_objeto_fora_da_tela_e_flutuando(plantado):
    rua, _, g = plantado
    assert _tem(g, rua, 'fora_da_tela', 'lixo')
    assert _tem(g, rua, 'flutuando', 'chinelo')


def test_nao_acusa_barata_no_pe_da_val(plantado):
    _, com_val, g = plantado
    assert not any(x['cena'] == com_val and 'barata' in x['ator'] and x['tipo'] in ('cobre_val', 'cobre_rosto') and x['nivel'] == 'comprovado' for x in g)


def test_relatorio_tem_todas_as_colunas(plantado):
    rua, _, g = plantado
    txt = G.relatorio([('controle', {'info': [{}] * 2, 'amostras': [], 'erros_js': []}, g)])
    for col in ('nível', 'cena', 'cenário', 'quando', 'elemento', 'problema', 'região invadida', 'medida'):
        assert col in txt
    assert 'comprovado' in txt


# ───────── Fase 2: as regras de posição que vieram do relatório (12/11/2026) ─────────
from src import fabula as F


def _todas_as_cenas():
    for nome, r in G.casos():
        for k, s in enumerate(G.dados_do_roteiro(r)['cenas']):
            yield nome, k, s


def test_ceu_sempre_inteiro_no_ceu_livre_e_longe_do_texto():
    """Nuvem/sol/lua/bicho 'no céu' ficam inteiros numa região de regioes.json e não encostam na legenda, no painel nem no título."""
    T = F.REGIOES['texto']
    for nome, k, s in _todas_as_cenas():
        regs = F.REGIOES['ceu'][s['cen']]
        for p in s['props']:
            if not p.get('ceu'):
                continue
            cx = F._caixa(p)
            assert any(F._dentro(cx, r) for r in regs), (nome, k, s['cen'], p['t'], cx)
            assert not F._cruza(cx, T['legenda']), (nome, k, p['t'], cx)
            if k == 0:
                assert not F._cruza(cx, T['titulo']), (nome, k, p['t'], cx)


def test_sem_sol_ou_lua_em_dobro():
    for nome, k, s in _todas_as_cenas():
        astro_do_cen = s['cen'] in F.REGIOES['astro']['cenarios']
        igual = [p for p in s['props'] if (p['t'] == 'sol' and not s['noite']) or (p['t'] == 'lua' and s['noite'])]
        if astro_do_cen and igual:
            assert s.get('sem_astro'), (nome, k, s['cen'], 'o cenário desenharia outro astro')
        if s.get('sem_astro'):
            assert igual, (nome, k, 'cenário sem astro mas sem objeto no lugar')
        assert not (s['cen'] == 'espaco' and any(p['t'] in ('terra', 'nuvem') for p in s['props'])), (nome, k)


def test_o_que_cai_termina_no_chao():
    for nome, k, s in _todas_as_cenas():
        for p in s['props']:
            if p['anim'] == 'cai' and p['t'] not in F.ASTROS_E_NUVEM:
                assert not p.get('ceu') and (p['y'] >= 1340 or p.get('atras')), (nome, k, p['t'], p['y'])


def test_objeto_do_chao_inteiro_no_quadro():
    for nome, k, s in _todas_as_cenas():
        for p in s['props']:
            if p.get('ceu') or p['anim'] in ('corre', 'foge') or (s['cen'] == 'rua_destruida' and p['t'] == 'fogo'):
                continue                                       # quem corre entra/sai de propósito; fogo das pontas da rua destruída é cenário
            x0, x1, ymax = F.REGIOES['quadro_seguro']['com_val' if s.get('val') else 'sem_val']
            if p.get('atras') and s['cen'] in F.BANCADA:
                x0, x1 = 0, 1080                                   # bancada tem a faixa dela
            assert p['x'] >= x0 and p['x'] + p['w'] <= x1, (nome, k, p['t'], p['x'], p['w'])
            if not p.get('atras') and p['y'] > 1340:
                assert p['y'] <= ymax, (nome, k, p['t'], p['y'])


def test_regioes_de_ceu_livres_no_chrome():
    """Confere no Chrome, com o cenário DESENHADO, que nenhuma casa/árvore/morro/mar entra nas regiões de céu de regioes.json,
    de dia e de noite. Se um cenário mudar em kit_cenarios.js e invadir o céu declarado, este teste acusa."""
    cens = [c for c in F.CENARIOS if F.REGIOES['ceu'][c] and c != 'rua_destruida']
    base = {'tema': 'teste', 'titulo_tela': 'TESTE', 'cta_placa': 'PARTE 2', 'cta_tela': 'Comenta *X*', 'cta_narracao': 'Comenta x.'}
    cenas = [{'cenario': c, 'cor': 100, 'pose': 'fora', 'balao': '', 'narracao': 'uma duas três quatro cinco seis sete oito nove', 'objetos': [], 'luz': luz}
             for luz in ('dia', 'noite') for c in cens]
    cenas += [{'cenario': 'rua_destruida', 'cor': 30, 'pose': 'fora', 'balao': '', 'narracao': 'um dois três quatro cinco seis sete oito nove', 'objetos': []}]
    dados = G.dados_do_roteiro({**base, 'cenas': cenas})
    med = G.medir_dados(dados, passo_mov=5, passo_parado=5, grade=200)
    ruins = set()
    for a in med['amostras']:
        cen = med['info'][a['i']]['cen']
        for peca in a['cenario']:
            if peca['tipo'] not in ('estrutura', 'fundo'):
                continue
            for r in F.REGIOES['ceu'][cen]:
                if F._cruza(peca['w'], r) > 0:
                    ruins.add((cen, peca['id'], peca['tipo'], tuple(round(v) for v in peca['w']), tuple(r)))
    assert not ruins, sorted(ruins)


def test_amostragem_densa_quando_ha_movimento():
    parada = {'a': 0, 'b': 4, 'anda': False, 'povo': 0, 'planos': [{'t0': 0, 'tipo': 'geral'}], 'props': [{'anim': 'aparece', 'de': 0.3, 'voa': False}]}
    corre = {**parada, 'props': [{'anim': 'corre', 'de': 0.3, 'voa': False}]}
    assert len(G.instantes(corre)) >= 4 * len(G.instantes(parada)) and len(G.instantes(parada)) >= 4
