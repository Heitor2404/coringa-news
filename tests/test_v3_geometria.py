"""P1 do Plano Mestre (§4): câmera, layout, transições e prova quadro a quadro (espelho Python × palco real)."""
import copy
import math
import random

import pytest

from src.v2 import diretor
from src.v3 import geometria as G
from src.v3 import pipeline as P


# ---------------------------------------------------------------- 'fixo' é fixo
def test_fixo_nao_tem_transformacao_no_tempo():
    cam = diretor.camera('fixo', [.1, .1, .5, .5], [.2, .2, .4, .4], 5.0)
    assert cam == [{'t': 0, 'caixa': [.2, .2, .4, .4]}]
    wh = (2000, 3000)
    assert len({tuple(round(x, 6) for x in G.transform(cam, t / 10, wh)) for t in range(51)}) == 1


# ---------------------------------------------------------------- trajetória contínua sem borda nem encolhimento
def _caminho(rnd, n):
    out = []
    for i in range(n):
        w = rnd.uniform(.12, 1.0)
        h = rnd.uniform(.12, 1.0)
        out.append({'t': i * rnd.uniform(.4, 3.0) if i else 0, 'caixa': [rnd.uniform(0, 1 - w), rnd.uniform(0, 1 - h), w, h]})
    for i in range(1, n):
        out[i]['t'] = out[i - 1]['t'] + max(.3, out[i]['t'] - out[i - 1]['t'] if out[i]['t'] > out[i - 1]['t'] else 1.0)
    return out


@pytest.mark.parametrize('semente', range(40))
def test_cobrir_nunca_mostra_borda_nem_encolhe_no_meio_do_caminho(semente):
    rnd = random.Random(semente)
    wh = (rnd.choice([800, 1600, 2400, 4000]), rnd.choice([600, 1000, 2000, 3800]))
    cam = _caminho(rnd, rnd.randint(2, 5))
    ach = G.auditar(cam, cam[-1]['t'] + .5, wh, 'cobrir')
    assert not [a for a in ach if a['codigo'] in ('G-BORDA', 'G-ENCOLHE')], ach


@pytest.mark.parametrize('semente', range(40))
def test_integral_sobra_so_na_barra_da_legenda(semente):
    rnd = random.Random(1000 + semente)
    wh = (rnd.choice([800, 1600, 2400, 4000]), rnd.choice([600, 1000, 2000, 3800]))
    cam = _caminho(rnd, rnd.randint(2, 5))
    assert not [a for a in G.auditar(cam, cam[-1]['t'] + .5, wh, 'integral') if a['codigo'] == 'G-BORDA']


def test_caixa_larga_nao_encolhe_a_foto_e_layout_nao_e_silencioso():
    """Antes: caixa mais larga que 9:16 reduzia a escala abaixo da cobertura e deixava a cópia desfocada aparecer."""
    wh = (1920, 1118)
    larga = [.05, .05, .9, .9]
    s, tx, ty = G.transform([{'t': 0, 'caixa': larga}], 0, wh, 'cobrir')
    assert s >= G.nat(wh) - 1e-9 and tx <= 0 and ty <= 0
    assert G.escolher_layout([larga], wh)[0] == 'integral'
    assert G.escolher_layout([larga], wh, 'cobrir')[0] == 'cobrir'          # pedido explícito é respeitado


def test_detalhe_de_documento_fica_acima_da_legenda():
    """Londres 12–15 s: o detalhe na base da placa (1274×960) caía embaixo da legenda nas duas versões anteriores."""
    wh, caixa = (1274, 960), [.39, .62, .34, .32]
    s, tx, ty = G.transform([{'t': 0, 'caixa': caixa}], 0, wh, 'integral')
    centro_y = ty + (caixa[1] + caixa[3] / 2) * wh[1] * s
    assert centro_y < G.BARRA - 200
    assert ty + wh[1] * s >= G.BARRA - 1                                     # sobra só abaixo da linha da legenda


def test_foto_pequena_nao_vira_cartao_deslizando():
    wh = (480, 640)
    cam = [{'t': 0, 'caixa': [.27, .61, .36, .39]}, {'t': 2.1, 'caixa': [.14, .11, .57, .61]}]
    assert G.escolher_layout([k['caixa'] for k in cam], wh)[0] == 'integral'
    a, b = G.transform(cam, 0, wh, 'integral'), G.transform(cam, 2.1, wh, 'integral')
    assert max(abs(x - y) for x, y in zip(a, b)) < 1e-6


def test_aceleracao_suave_pico_de_velocidade():
    """Seno in-out: pico ≈ 1,57× a velocidade média (o cúbico dava 3×: arranque e freada bruscos)."""
    wh = (4000, 3000)
    cam = [{'t': 0, 'caixa': [0, .2, .3, .5]}, {'t': 4, 'caixa': [.6, .2, .3, .5]}]
    xs = [G.transform(cam, i / 30, wh)[1] for i in range(121)]
    v = [abs(xs[i + 1] - xs[i]) for i in range(120)]
    assert max(v) / (sum(v) / len(v)) < 1.65


def test_auditoria_acusa_salto_e_zoom_rapido():
    wh = (4000, 3000)
    pan = [{'t': 0, 'caixa': [0, .3, .2, .3]}, {'t': .3, 'caixa': [.8, .3, .2, .3]}]
    assert {'G-SALTO', 'G-PAN-RAPIDO'} <= {a['codigo'] for a in G.auditar(pan, 1.0, wh)}
    zoom = [{'t': 0, 'caixa': [0, 0, 1, 1]}, {'t': .3, 'caixa': [.45, .45, .08, .1]}]
    assert 'G-ZOOM-RAPIDO' in {a['codigo'] for a in G.auditar(zoom, 1.0, wh)}
    calmo = [{'t': 0, 'caixa': [0, .3, .2, .3]}, {'t': 6, 'caixa': [.2, .3, .2, .3]}]
    assert not G.auditar(calmo, 6.5, wh)


def test_resolucao_baixa_aparece():
    cod = {a['codigo'] for a in G.auditar([{'t': 0, 'caixa': [0, 0, 1, 1]}], 1.0, (480, 640), 'cobrir')}
    assert 'G-RESOLUCAO' in cod


# ---------------------------------------------------------------- diretor: layout e transição
AC = {'f': {'id': 'f', 'arq': '/x.jpg', 'wh': [1920, 1118], 'sha': 's1', 'credito': 'c', 'ano': 1675}}
PAL = [{'w': w, 's': i * .4, 'e': i * .4 + .35} for i, w in enumerate('o fogo começou na padaria do rei e se espalhou'.split())]


def _pl(**kw):
    base = {'evento_id': 'e1', 'fato_id': 'f1', 'funcao_narrativa': 'contexto', 'recurso_visual': {'tipo': 'foto', 'id': 'f'},
            'funcao_documental': 'CONTEXTO', 'acao_visual': 'x', 'composicao': 'doc.plano', 'movimento_camera': 'revelar',
            'plano_inicial': [.3, .3, .2, .3], 'plano_final': [.05, .05, .9, .9], 'tempo_inicio': 0, 'tempo_fim': 4,
            'fala': 'o fogo começou na padaria'}
    base.update(kw)
    return base


def test_enquadramento_largo_em_foto_sem_solucao_fica_registrado_sem_cartao():
    # 16/11: o 'integral' automático (cartão sobre fundo escuro) deixou de existir. Foto (não documento/mapa/arte) com
    # pedido mais largo que 9:16 e sem objeto principal localizado: cobre o quadro e pede revisão — nunca em silêncio.
    cenas, reg = diretor.montar({'planos': [_pl()]}, AC, {}, PAL, {'f1'})
    assert cenas[0]['params']['layout'] == 'cobrir'
    assert any(d['codigo'] == 'SEM-COMPOSICAO-VERTICAL' and d['impacto'] == 'revisao' for d in reg[0]['degradacoes'])


def test_cobrir_pedido_com_corte_do_enquadramento_pede_revisao():
    cenas, reg = diretor.montar({'planos': [_pl(layout='cobrir')]}, AC, {}, PAL, {'f1'})
    assert cenas[0]['params']['layout'] == 'cobrir'
    assert any(d['codigo'] == 'ENQUADRAMENTO-CORTADO' and d['impacto'] == 'revisao' for d in reg[0]['degradacoes'])


def test_transicao_zoom_nao_empilha_com_zoom_de_camera():
    # aproximação com motivo (objeto principal localizado), para a câmera de fato se mover
    reg_ = {'s1': {'objetos': {'casa': {'caixa': [.4, .4, .12, .15], 'visivel': True, 'ancoravel': True}}}}
    pl = _pl(transicao='zoom', movimento_camera='aproximar', objeto_principal='casa', plano_inicial='geral', plano_final='objeto')
    cenas, reg = diretor.montar({'planos': [pl]}, AC, reg_, PAL, {'f1'})
    assert cenas[0]['transicao'] == 'corte'
    assert any(d['codigo'] == 'TRANSICAO-ZOOM-EMPILHADA' for d in reg[0]['degradacoes'])
    cenas, _ = diretor.montar({'planos': [_pl(transicao='zoom', movimento_camera='fixo')]}, AC, {}, PAL, {'f1'})
    assert cenas[0]['transicao'] == 'zoom'


def test_prompt_multitematico_sem_variedade_gratuita_de_transicao():
    assert 'Varie transições' not in P.PROMPT and 'documentário' not in P.PROMPT.split('\n')[0]
    assert 'multitemático' in P.PROMPT and '"layout"' in P.PROMPT and '"corte" por padrão' in P.PROMPT
    assert 'Varie transições' not in diretor.PROMPT_DIRETOR and 'varie enquadramento e transição' not in diretor.PROMPT_DIRETOR


def test_validador_recusa_layout_inexistente():
    v = {'cenas': [{'fala': 'o fogo começou na padaria'}], 'fatos': ''}
    ctx = {'eventos': [], 'plano_av': []}
    pl = {**_pl(layout='tela-cheia'), 'trechos': [0]}
    erros = P.validar_storyboard({'planos': [pl]}, v, AC, ctx)
    assert any('layout inexistente' in e for _, e in erros)


def test_receitas_sem_transicao_decorativa_por_padrao():
    from src.v3 import receitas
    for r in receitas.todas() if hasattr(receitas, 'todas') else receitas.carregar():
        assert r['transicao'] == 'corte' or r['transicao'] == 'preto', r['id']


# ---------------------------------------------------------------- palco real (Chromium) × espelho
@pytest.fixture(scope='module')
def img(tmp_path_factory):
    from PIL import Image, ImageDraw
    d = tmp_path_factory.mktemp('geo')
    out = {}
    for nome, wh in (('larga', (2400, 1400)), ('alta', (1500, 3200)), ('pequena', (500, 650))):
        im = Image.new('RGB', wh, (90, 110, 130))
        dr = ImageDraw.Draw(im)
        for x in range(0, wh[0], 100):
            dr.line([(x, 0), (x, wh[1])], fill=(200, 200, 60), width=6)
        im.save(d / f'{nome}.jpg', quality=85)
        out[nome] = (str(d / f'{nome}.jpg'), list(wh))
    return out


def test_palco_real_igual_ao_espelho_e_sem_borda(img, tmp_path):
    from src.v2 import palco
    cenas = []
    planos = [('larga', 'cobrir', [{'t': 0, 'caixa': [.1, .1, .3, .7]}, {'t': 3, 'caixa': [.55, .2, .25, .5]}]),
              ('larga', 'integral', [{'t': 0, 'caixa': [0, 0, 1, 1]}, {'t': 3, 'caixa': [.4, .5, .2, .3]}]),
              ('alta', 'cobrir', [{'t': 0, 'caixa': [0, .2, 1, .7]}, {'t': 1, 'caixa': [0, .2, 1, .7]}, {'t': 3, 'caixa': [.3, 0, .3, .2]}]),
              ('pequena', 'integral', [{'t': 0, 'caixa': [.2, .2, .4, .4]}]),
              ('larga', 'editorial', [{'t': 0, 'caixa': [.55, .4, .2, .3]}])]
    for k, (nome, lay, cam) in enumerate(planos):
        arq, wh = img[nome]
        cenas.append({'comp': 'doc.plano', 'start': 3.5 * k, 'end': 3.5 * (k + 1), 'transicao': 'corte' if k != 2 else 'dissolve',
                      'origem': [k], 'fala': '', 'params': {'img': arq, 'wh': wh, 'cam': cam, 'layout': lay, 'anot': [],
                                                             'selo': {'funcao': 'CONTEXTO', 'texto': ''}, 'credito': 'teste'}})
    dados = {'duration': 17.5, 'scenes': cenas, 'captions': [], 'creditos': []}
    with palco.abrir(palco.preparar(copy.deepcopy(dados)), tmp_path / 'p') as pg:
        amostras = sum(len(pg.evaluate(f'geometria({t / 4:.3f})')) for t in range(70))
        ed = pg.evaluate('geometria(16.0)')[0]
        ach = G.auditar_palco(pg, dados, fps=8)
    assert amostras >= 60
    assert ed['layout'] == 'editorial' and len(ed['paineis']) == 2              # visão geral + detalhe, medidos no palco
    oc = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in ed['paineis']) / (1080 * 1920)
    assert oc > .97
    assert not ach, ach


def test_editorial_sem_choque_entre_selo_credito_e_marca(img, tmp_path):
    """ERR-041 (microcena Panamá, 16/11): no editorial o selo desce para o painel de detalhe e o crédito ficava fixo em
    1132 px (posição do layout cobrir) — selo × crédito sobrepostos bloquearam o vídeo (ERR-008)."""
    from src.v2 import palco
    arq, wh = img['larga']
    # visão geral alta (≈ painel de 55%): o detalhe começa em y ≈ 1072, onde o cobrir punha o crédito; ponto no topo do detalhe
    dados = {'duration': 4, 'captions': [], 'creditos': [], 'scenes': [
        {'comp': 'doc.plano', 'start': 0, 'end': 4, 'transicao': 'corte', 'origem': [0], 'fala': '',
         'params': {'img': arq, 'wh': wh, 'cam': [{'t': 0, 'caixa': [.5, .3, .3, .6]}], 'layout': 'editorial',
                    'anot': [{'tipo': 'ponto', 'caixa': [.6, .31, .02, .02], 't0': .3, 'texto': '80 km de rota'}],
                    'visao_geral': [.3, 0, .6, 1], 'selo': {'funcao': 'DOCUMENTO', 'texto': 'carta náutica, 1914'},
                    'credito': '"Admiralty Chart No 657 Panama Canal and Approaches" — United Kingdom Hydrographic Office'}}]}
    with palco.abrir(palco.preparar(copy.deepcopy(dados)), tmp_path / 'p') as pg:
        geo = palco.medir(pg, 4, .5)
    assert not [g for g in geo if g.get('tipo') == 'choque' and g.get('grave') and not g.get('cap')], geo
