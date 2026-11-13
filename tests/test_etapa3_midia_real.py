"""Etapa 3 (13/11/2026), item 1: mídia real não é recusada só por ser "genérica". O critério é se ela MOSTRA o
acontecimento narrado. Sem IA: catálogo e casamento simulados com os campos que o pipeline real produz."""
import copy

from src import acervo, gemini, resolucao, selecao, storyboard as sbm

AC = lambda recurso='': {'quem': '', 'onde': '', 'quando': '', 'recurso': recurso}

ACV = [
    {'id': 'cam', 'tipo_img': 'foto', 'mostra': 'polvo camuflado entre corais, quase invisível', 'generica': True,
     'mini': b'', 'nota': 8, 'fonte': 'commons'},
    {'id': 'vid', 'tipo_img': 'foto', 'mostra': 'polvo mudando de cor rapidamente', 'generica': True,
     'video': {'url': 'u'}, 'mini': b'', 'nota': 7, 'fonte': 'commons'},
    {'id': 'est', 'tipo_img': 'foto', 'mostra': 'polvo parado sobre rocha', 'generica': True, 'mini': b'', 'nota': 9,
     'fonte': 'commons'},
    {'id': 'mud', 'tipo_img': 'foto', 'mostra': 'polvo mudando de cor', 'generica': True, 'mini': b'', 'nota': 8,
     'fonte': 'commons'},
]


def _cena(k, fala, funcao, mostrar, recurso='foto', **kw):
    return {'tipo': 'gancho' if k == 0 else 'historia', 'fala': fala, 'grupo': k, 'evento': f'e{k}',
            'bloco': {'funcao': funcao}, 'acontecimento': AC(recurso), 'mostrar': mostrar, 'imagem': f'c{k}', **kw}


def _video(cenas, modo='mecanismo'):
    return {'plano': {'modos': [modo], 'assunto': 'polvo'}, 'acervo': copy.deepcopy(ACV),
            'cenas': cenas + [{'tipo': 'fechamento', 'fala': 'Segue.'}]}


def _r(v, k):
    return v['cenas'][k]['sb']['resolucao']


def test_criterio_e_conteudo_e_desconta_o_assunto():
    c = {'sb': {'intencao_visual': 'polvo se camuflando nas rochas'}}
    assert selecao.mostra_o_fato(ACV[0], c, frozenset({'polvo'}))[0]           # "camuf" em comum
    ok, comum = selecao.mostra_o_fato(ACV[2], {'sb': {'intencao_visual': 'polvo muda de cor'}}, frozenset({'polvo'}))
    assert not ok and comum == []                                              # "polvo" sozinho não prova nada
    assert not selecao.mostra_o_fato(ACV[0], {'sb': {}, 'fala': 'O polvo se camufla'})[0]   # sem intenção visual: nada muda


def test_polvo_camuflado_representa_a_camuflagem_mesmo_generico():
    v = sbm.construir(_video([_cena(0, 'Ele se camufla em segundos.', 'payoff', 'polvo camuflado no fundo',
                                    foto='cam', relacao='tema')], modo='curiosidade'))
    resolucao.resolver(v)
    r = _r(v, 0)
    assert r['tipo'] == 'evidencia_real' and r['nivel'] == 'direto' and r['midia'] == 'cam'
    assert 'mostra o próprio acontecimento' in r['justificativa'] and 'camuf' in r['mostra']


def test_video_real_de_mudanca_de_cor_representa_o_fenomeno():
    v = sbm.construir(_video([_cena(0, 'O polvo muda de cor.', 'abertura', 'x'),
                              _cena(1, 'E a cor muda em frações de segundo.', 'mecanismo', 'polvo mudando de cor',
                                    foto='vid', relacao='tema')]))
    resolucao.resolver(v)
    r = _r(v, 1)
    assert v['cenas'][1]['sb']['necessidade'] == 'processo'
    assert r['tipo'] == 'evidencia_real' and r['midia'] == 'vid' and 'fenômeno acontecendo' in r['justificativa']


def test_foto_estatica_nao_demonstra_o_funcionamento_dos_cromatoforos():
    v = sbm.construir(_video([_cena(0, 'O polvo muda de cor.', 'abertura', 'x'),
                              _cena(1, 'Músculos esticam o saco de pigmento.', 'mecanismo',
                                    'músculos radiais esticando o saco de pigmento', foto='est', relacao='tema'),
                              _cena(2, 'A cor muda.', 'mecanismo', 'polvo mudando de cor', foto='mud', relacao='tema')]))
    resolucao.resolver(v)
    assert _r(v, 1)['tipo'] == 'esquema_pendente'                               # foto do polvo ≠ mecanismo interno
    r2 = _r(v, 2)
    assert r2['tipo'] == 'esquema_pendente'                                     # mostra o resultado, não o funcionamento
    assert 'foto estática mostra o resultado' in r2['rejeitadas'][0]['motivo']


def test_tres_categorias_continuam_distintas():
    v = sbm.construir(_video([
        _cena(0, 'Ele se camufla.', 'payoff', 'polvo camuflado', foto='cam', relacao='tema'),
        _cena(1, 'Por dentro, um saco de pigmento.', 'mecanismo', 'saco de pigmento', recurso='esquema',
              foto='dg', relacao='diagrama'),
        _cena(2, 'Imagine o polvo no escuro.', 'contexto', 'polvo no escuro', recurso='ia', midia='ia', prompt_imagem='p')],
        modo='curiosidade'))
    v['acervo'].append({'id': 'dg', 'tipo_img': 'diagrama', 'mostra': 'diagrama do cromatóforo', 'mini': b''})
    resolucao.resolver(v)
    assert [_r(v, k)['tipo'] for k in range(3)] == ['evidencia_real', 'reconstrucao_explicativa', 'ilustracao_conceitual']


def test_casar_nao_recusa_generica_que_mostra_o_fato(monkeypatch):
    v = sbm.construir(_video([_cena(0, 'O polvo muda de cor.', 'abertura', 'x'),
                              _cena(1, 'Ele se camufla.', 'payoff', 'polvo camuflado no fundo'),
                              _cena(2, 'Ele muda de cor.', 'payoff', 'polvo mudando de cor')], modo='curiosidade'))
    esc = [{'ideia': 1, 'foto': 'cam', 'exata': False, 'relacao': 'tema'},
           {'ideia': 2, 'foto': 'est', 'exata': False, 'relacao': 'tema'}]       # genérica que NÃO mostra: sai como antes
    monkeypatch.setattr(gemini, 'json_visao', lambda prompt, minis, leve=False: {'escolhas': esc})
    acervo.casar(v, v['acervo'])
    assert v['cenas'][1]['foto'] == 'cam'
    assert v['cenas'][2].get('foto') is None
    assert v['cenas'][2]['_escolha']['rejeitadas'][0]['motivo'] == 'genérica e não mostra o que a frase diz'


def test_preencher_usa_reserva_que_mostra_em_cena_estrita_e_so_video_em_processo():
    v = sbm.construir(_video([_cena(0, 'O polvo muda de cor.', 'abertura', 'x', foto='est'),
                              _cena(1, 'Ele se camufla.', 'payoff', 'polvo camuflado no fundo'),
                              _cena(2, 'A cor muda rápido.', 'mecanismo', 'polvo mudando de cor'),
                              _cena(3, 'Músculos puxam o pigmento.', 'mecanismo', 'músculos puxando pigmento')]))
    acervo.preencher(v, v['acervo'])
    c = v['cenas']
    assert c[1]['sb']['necessidade'] == 'acontecimento' and c[1]['foto'] == 'cam'   # fato central: o polvo camuflado
    assert c[2]['foto'] == 'vid'                                                # vídeo do fenômeno, não a foto 'mud'
    assert c[3].get('foto') is None                                             # nada mostra os músculos: resolvedor
