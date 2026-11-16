"""V3 — direção audiovisual: contrato, enquadramento vertical, anotação só onde a visão localizou, tempos pela fala."""
from __future__ import annotations

import pytest

from src.v2 import diretor, fiscal_av, regioes

AC = {'a1': {'id': 'a1', 'arq': '/x.jpg', 'wh': [3000, 2000], 'sha': 's1', 'ano': 2007, 'credito': 'Fulano (CC BY 2.0)', 'ia': False},
      'a2': {'id': 'a2', 'arq': '/y.jpg', 'wh': [3000, 2000], 'sha': 's2', 'ano': None, 'credito': '', 'ia': True}}
REG = {'s1': {'foco': {'caixa': [.3, .3, .3, .3]}, 'objetos': {
    'molde': {'caixa': [.4, .3, .1, .4], 'visivel': True, 'ancoravel': True},
    'chao': {'caixa': [0, .75, 1, .25], 'visivel': True, 'ancoravel': True},
    'vulcao': {'caixa': [.4, .1, .2, .1], 'visivel': True, 'ancoravel': True},
    'incerto': {'caixa': [.1, .1, .1, .1], 'visivel': True, 'ancoravel': False}}}}
PAL = [{'w': 'um', 's': 0.1}, {'w': 'morador', 's': 0.4}, {'w': 'protegendo', 's': 1.6}, {'w': 'desce', 's': 2.2}, {'w': 'descer', 's': 3.5}]


def _pl(**kw):
    base = {'evento_id': 'e1', 'fato_id': 'f1', 'funcao_narrativa': 'contexto', 'recurso_visual': {'tipo': 'foto', 'id': 'a1'},
            'funcao_documental': 'CONTEXTO', 'acao_visual': 'aproxima', 'composicao': 'doc.plano', 'objeto_principal': 'molde',
            'movimento_camera': 'aproximar', 'plano_inicial': 'geral', 'plano_final': 'objeto', 'tempo_inicio': 0, 'tempo_fim': 4,
            'fala': 'Um morador protegendo', 'anotacoes': []}
    base.update(kw)
    return base


def test_enquadramento_sempre_vertical_sem_faixa():
    for nome in ('geral', 'contexto', 'objeto', 'detalhe'):
        x, y, w, h = diretor.enquadramento(nome, [.4, .3, .1, .4], None, [3000, 2000])
        assert 0 <= x <= 1 - w + 1e-6 and 0 <= y <= 1 - h + 1e-6
        assert abs((w * 3000) / (h * 2000) - 1080 / 1540) < .02          # proporção da tela acima da legenda


def test_objeto_largo_nao_vira_fatia():
    x, y, w, h = diretor.enquadramento('objeto', [.2, .4, .6, .15], None, [3000, 2000])
    assert w >= .6                                                         # o corpo deitado aparece inteiro


def test_palavra_exata_antes_do_radical():
    assert diretor.tempo_da_palavra(PAL, '', 'descer', 0, 5) == 3.5           # "desce" não é "descer"
    assert diretor.tempo_da_palavra(PAL, '', 'protegendo', 0, 5) == 1.6


def test_anotacao_so_onde_a_visao_localizou_com_confianca():
    sb = {'planos': [_pl(anotacoes=[{'tipo': 'circulo', 'alvo': 'molde', 'texto': 'Vítima', 'na_palavra': 'protegendo'},
                                    {'tipo': 'circulo', 'alvo': 'incerto', 'texto': 'X'}])]}
    cenas, reg = diretor.montar(sb, AC, REG, PAL, {'f1'})
    an = cenas[0]['params']['anot']
    assert len(an) == 1 and an[0]['t0'] == 1.6 and an[0]['caixa'] == [.4, .3, .1, .4]
    assert any('incerto' in l for l in reg[0]['limitacoes'])


def test_regiao_maior_que_o_quadro_vira_marcador():
    sb = {'planos': [_pl(objeto_principal='molde', anotacoes=[{'tipo': 'contorno', 'alvo': 'chao', 'texto': 'Chão'}])]}
    cenas, reg = diretor.montar(sb, AC, REG, PAL, {'f1'})
    assert cenas[0]['params']['anot'][0]['tipo'] == 'ponto'


@pytest.mark.parametrize('mudanca,erro', [({'recurso_visual': {'tipo': 'foto', 'id': 'a2'}}, 'IA'),
                                          ({'fato_id': 'f9'}, 'não está na pesquisa'),
                                          ({'funcao_documental': 'PROVA'}, 'função documental'),
                                          ({'funcao_documental': 'REGISTRO', 'ano_do_fato': 79}, 'não é REGISTRO'),
                                          ({'tempo_fim': .8}, 'curto demais')])
def test_plano_invalido_nao_vira_cena(mudanca, erro):
    cenas, reg = diretor.montar({'planos': [_pl(**mudanca)]}, AC, REG, PAL, {'f1'})
    assert not cenas and any(erro in e for e in reg[0]['erros'])


def test_seta_com_direcao_dada_precisa_dizer_esquema():
    an = {'tipo': 'seta', 'alvo': 'vulcao', 'ate_desvio': [0, -.3], 'texto': '33 km para cima'}
    cenas, reg = diretor.montar({'planos': [_pl(objeto_principal='vulcao', anotacoes=[an])]}, AC, REG, PAL, {'f1'})
    assert not cenas and 'esquema' in reg[0]['erros'][0]
    an['texto'] = '33 km para cima (esquema)'
    cenas, _ = diretor.montar({'planos': [_pl(objeto_principal='vulcao', anotacoes=[an])]}, AC, REG, PAL, {'f1'})
    assert cenas and cenas[0]['params']['anot'][0]['para'][1] < cenas[0]['params']['anot'][0]['de'][1]


def test_movimento_imperceptivel_e_corrigido():
    reg = {'s1': {'foco': {'caixa': [0, 0, 1, 1]}, 'objetos': {'tudo': {'caixa': [0, 0, 1, 1], 'visivel': True, 'ancoravel': True}}}}
    cenas, r = diretor.montar({'planos': [_pl(objeto_principal='tudo')]}, AC, reg, PAL, {'f1'})
    cam = cenas[0]['params']['cam']
    assert cam[0]['caixa'] != cam[-1]['caixa'] and r[0]['limitacoes']


def test_composicao_recebe_tempos_pela_fala():
    pl = _pl(composicao='doc.eclusa', recurso_visual={'tipo': 'composicao', 'id': 'doc.eclusa'}, funcao_documental='ESQUEMA',
             tempos_palavras={'enche': 'desce', 'outro_lado': 'descer'}, params={'degraus': 3})
    cenas, _ = diretor.montar({'planos': [pl]}, AC, REG, PAL, {'f1'})
    assert cenas[0]['params']['tempos'] == {'enche': 2.2, 'outro_lado': 3.5}


def test_regioes_caixa_da_visao_e_cache():
    chamadas = []
    def visao(prompt, imgs):
        chamadas.append(1)
        return {'foco': {'box_2d': [100, 200, 500, 600]}, 'objetos': [{'objeto': 'navio', 'visivel': True, 'box_2d': [300, 400, 400, 600], 'confianca': 'alta'}]}
    cache = {}
    r = regioes.localizar(__file__, ['navio'], cache, visao)
    assert r['objetos']['navio']['caixa'] == [.4, .3, .2, .1] and r['objetos']['navio']['ancoravel']
    regioes.localizar(__file__, ['navio'], cache, visao)
    assert len(chamadas) == 1                                              # segunda vez: cache, sem chamada


def test_fiscal_av_pergunta_central_sem_plano_bloqueia(tmp_path):
    import subprocess
    mp4 = tmp_path / 'v.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=gray:s=108x192:d=4', '-r', '10', str(mp4)], check=True)
    r = fiscal_av.avaliar(mp4, [{'start': 0, 'end': 4, 'comp': 'doc.plano', 'direcao': {'evento_id': 'e1'}}], [], criticos=['e1', 'e5'])
    assert r['bloqueia'] and any(a['codigo'] == 'AV-PARADO' for a in r['achados'])


def test_render_anotacao_acompanha_a_camera(tmp_path):
    from PIL import Image
    from src.v2 import palco
    img = tmp_path / 'f.jpg'
    Image.new('RGB', (3000, 2000), (90, 120, 150)).save(img)
    d = {'duration': 4, 'meta': {'motor': 'v2'}, 'captions': [], 'scenes': [{'comp': 'doc.plano', 'start': 0, 'end': 4, 'params': {
        'img': str(img), 'wh': [3000, 2000], 'cam': [{'t': 0, 'caixa': [0, 0, .5, 1]}, {'t': 3.5, 'caixa': [.35, .25, .2, .4]}],
        'anot': [{'tipo': 'circulo', 'caixa': [.4, .3, .1, .3], 't0': .2, 'texto': 'ALVO'}], 'selo': {'funcao': 'CONTEXTO', 'texto': 'teste'}}}]}
    js = "(()=>{const b=document.querySelector('.an0 .t1').getBBox();const m=document.querySelector('.dp-mundo').style.transform;return [b.x+b.width/2,b.y+b.height/2,m]})()"
    with palco.abrir(palco.preparar(d), tmp_path / 'p') as pg:
        assert not pg.erros
        pos = []
        for t in (1.0, 3.6):
            pg.evaluate(f'seek({t})')
            cx, cy, m = pg.evaluate(js)
            tx, ty, s = [float(v) for v in m.replace('translate(', '').replace('px', '').replace(') scale(', ',').replace(')', '').split(',')]
            pos.append((cx, cy, tx + .45 * 3000 * s, ty + .45 * 2000 * s))
        for cx, cy, ex, ey in pos:                          # o centro do círculo é o centro da região projetada
            assert abs(cx - ex) < 20 and abs(cy - ey) < 20     # traço "à mão" tem ±2% de irregularidade
        assert abs(pos[0][0] - pos[1][0]) > 40               # a câmera se moveu e o círculo foi junto
