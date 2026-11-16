"""V2.5 estrutural — plano visual vinculante, documentário histórico, cobertura estruturada, rastreio por fonte.
Cada teste corresponde a um defeito encontrado nos pilotos reais (céu azul, Titanic, Pisa) ou na auditoria da matriz."""
from __future__ import annotations

import pytest

from src.v2 import cobertura, contrato, fiscal_v2, montagem, plano_exec, preparo, prevalidacao

FATOS = ('FATOS:\n- O primeiro oficial William Murdoch ordenou virar o leme para estibordo. (Wikipédia)\n'
         '- O RMS Titanic partiu de Southampton em 10 de abril de 1912. (Wikipédia)\n'
         '- O vão da Golden Gate tem 1.280 metros. (Wikipédia)\n- Hoje, mais de 5 milhões de turistas visitam a praça. (Wikipedia (inglês))\n')
LINHAS = preparo.pesquisa({'fatos': FATOS})


def _v(cenas, acervo=()):
    return {'titulo': 'Como o Titanic afundou?', 'fatos': FATOS, 'fontes': ['Wikipédia'], 'acervo': list(acervo),
            'cenas': [dict(c, grupo=k, evento=f'i{k}') for k, c in enumerate(cenas)]}


def _ac(eid, tipo, sujeito, dados=None, crit=True, **kw):
    return {'id': eid, 'tipo': tipo, 'sujeito': sujeito, 'mostrar': kw.pop('mostrar', sujeito), 'dados': dados or {},
            'importancia': 'critica' if crit else 'apoio', 'obrigatoria': crit, 'fonte': 'Wikipédia', **kw}


# ── rastreio: a fonte precisa sustentar o fato ESPECÍFICO ──
def test_rastreio_exige_numeros_e_nomes_proprios_na_mesma_linha():
    assert prevalidacao.rastrear_texto('O primeiro oficial William Murdoch ordenou desvio para estibordo.', LINHAS)
    assert prevalidacao.rastrear_texto('O primeiro oficial Charles Lightoller ordenou desvio para estibordo.', LINHAS) is None
    assert prevalidacao.rastrear_texto('O vão da Golden Gate tem 1.300 metros.', LINHAS) is None


def test_leitor_de_numeros_por_extenso_e_aproximacao():
    assert cobertura.valores('Mais de mil e quinhentas pessoas') == [(1500.0, True)]
    assert cobertura.valores('às vinte e três e quarenta') == [(23.0, False), (40.0, False)]
    assert cobertura.valores('cerca de 3,7 milhões') == [(3700000.0, True)]
    assert preparo.rastrear(5000000, None, LINHAS)                       # "5 milhões" na pesquisa


# ── dado declarado inválido não é escondido por foto/cartão (g3/g4) ──
@pytest.mark.parametrize('ac', [_ac('e1', 'territorio', 'país', {'pais': 'Terra Média'}, crit=False),
                                _ac('e1', 'localizacao', 'Saara', {'pontos': [{'nome': 'Saara', 'lon': 300, 'lat': 23}]}, crit=False)])
def test_dado_declarado_invalido_bloqueia_mesmo_em_apoio(ac):
    rel = preparo.preparar(_v([{'tipo': 'historia', 'fala': 'Fala.', 'acontecimento': ac}]))
    assert rel['bloqueios'] and 'dado declarado inválido' in ' '.join(rel['bloqueios'][0]['faltam'])


# ── cobertura estruturada: m6 e números de tela sem apoio ──
def test_numero_na_tela_sem_apoio_na_fala_nem_na_pesquisa_bloqueia():
    ac = _ac('e1', 'escala', 'Golden Gate', representacao={'modo': 'composicao', 'comp': 'comparacao.grandezas'})
    tela = {'itens': [{'rotulo': 'Golden Gate', 'valor': 1280}, {'rotulo': 'Torre Eiffel', 'valor': 330}], 'unidade': 'm'}
    r = cobertura.avaliar_evento(ac, 'O vão da Golden Gate tem 1.280 metros, mais que o Everest.', 'comparacao.grandezas', tela, None, None, '', LINHAS)
    assert r['resultado'] == 'bloqueio' and r['verificacoes']['dados'] == 'falha' and '330' in r['motivo']


def test_esquema_de_outro_assunto_nao_passa_pelo_titulo():
    ac = _ac('e1', 'mecanismo', 'DNA', estado_inicial='hélice fechada', estado_final='duas fitas', representacao={'modo': 'composicao', 'comp': 'mecanismo.estados'})
    tela = {'titulo': 'A fita de DNA se abre', 'esquema': {'objetos': [{'id': 'a', 'forma': 'corpo', 'rotulo': 'BLOCO'}, {'id': 'b', 'forma': 'superficie', 'rotulo': 'BASE'}],
                                                         'estados': [{'rotulo': 'INÍCIO'}, {'rotulo': 'FIM', 'objetos': {'a': {'dy': .3}}}]}}
    r = cobertura.avaliar_evento(ac, 'O DNA se duplica.', 'mecanismo.estados', tela, None, {'medidas': {'dif_ini_fim': 9}}, '', LINHAS)
    assert r['resultado'] == 'bloqueio' and r['verificacoes']['sujeito'] == 'falha'


def test_foto_de_outra_pessoa_bloqueia_e_contexto_nunca_e_prova():
    foto = {'id': 'a1', 'mostra': 'Retrato de Albert Einstein', 'ano': 1950}
    ac = _ac('e1', 'pessoa', 'Alan Turing', representacao={'modo': 'foto_direta', 'foto': 'a1'})
    assert cobertura.avaliar_evento(ac, 'Turing criou a máquina.', 'foto', {}, foto, None)['resultado'] == 'bloqueio'
    ac2 = _ac('e2', 'evento_historico', 'William Murdoch', representacao={'modo': 'contexto', 'foto': 'a2'})
    foto2 = {'id': 'a2', 'mostra': 'O RMS Titanic no porto de Southampton', 'ano': 1912}
    r = cobertura.avaliar_evento(ac2, 'Murdoch ordenou o desvio.', 'foto', {}, foto2, None, 'Como o Titanic afundou?')
    assert r['resultado'] == 'revisao' and r['verificacoes']['funcao'] == 'contexto'


# ── documentário: fato comprovado + foto de contexto identificada (não bloqueia; não vira prova) ──
def test_fato_documentado_sem_foto_do_instante_vira_contexto_identificado():
    x = {'id': 'a0', 'arq': __file__, 'mostra': 'O RMS Titanic deixando Southampton', 'titulo': 'Titanic 1912', 'ano': 1912, 'tipo_img': 'foto'}
    ac = _ac('e1', 'pessoa', 'William Murdoch', {'nome': 'William Murdoch'}, estado_final='desvio para estibordo')
    v = _v([{'tipo': 'historia', 'fala': 'O primeiro oficial William Murdoch ordenou desvio para estibordo.', 'acontecimento': ac}], [x])
    rel = preparo.preparar(v)
    rep = v['cenas'][0]['acontecimento']['representacao']
    assert not rel['bloqueios'] and rep['modo'] == 'contexto' and rep['nao_prova'] and 'não é o instante' in v['cenas'][0]['rotulo_contexto']


def test_fato_sem_fonte_nao_vira_contexto_nem_ilustracao():
    x = {'id': 'a0', 'arq': __file__, 'mostra': 'O RMS Titanic deixando Southampton', 'ano': 1912, 'tipo_img': 'foto'}
    ac = _ac('e1', 'pessoa', 'Charles Lightoller', {'nome': 'Charles Lightoller'})
    v = _v([{'tipo': 'historia', 'fala': 'Charles Lightoller salvou dezenas de botes.', 'acontecimento': ac}], [x])
    rel = preparo.preparar(v)
    assert rel['bloqueios'] and any('retirar ou qualificar' in f for f in rel['bloqueios'][0]['faltam'])


def test_renderizacao_do_catalogo_nao_vale_como_registro():
    x = {'id': 'a1', 'arq': __file__, 'mostra': 'Renderização digital do Titanic navegando à noite', 'titulo': 'Titanic', 'tipo_img': 'foto'}
    a = preparo.avaliar_imagem(x, _ac('e1', 'evento_historico', 'Titanic'), {'mostrar': 'Titanic navegando', '_falas': ['O Titanic navegava.']}, 1912)
    assert a['forca'] <= .5


def test_fiscal_exige_o_selo_de_contexto_na_tela():
    ac = {'id': 'e1', 'tipo': 'evento_historico', 'importancia': 'critica', 'representacao': {'modo': 'contexto', 'foto': 'a1'}}
    sc_sem = {'comp': 'foto.documental', 'start': 0, 'end': 3, 'params': {'lugar': ''}, 'fundo': {'img': __file__}, 'origem': [0]}
    sc_com = {**sc_sem, 'comp': 'banner.discreto', 'params': {'rotulo': 'CONTEXTO', 'texto': 'x · não é o instante'}}
    v1 = {'scenes': [{'tipo': 'historia', 'fala': 'x', 'start': 0, 'end': 3, 'acontecimento': ac}]}
    cod = lambda sc: [a['codigo'] for a in fiscal_v2.avaliar({'scenes': [sc], 'captions': []}, [{}], dados_v1=v1)['achados'] if a['gravidade'] == 'bloqueio']
    assert 'S5' in cod(sc_sem) and 'S5' not in cod(sc_com)


# ── contratos: mesmas definições, formatos do roteirista corrigidos sem inventar ──
def test_normalizacao_sem_inventar():
    ac, m = contrato.normalizar_dados({'tipo': 'numero', 'dados': {'numero': {'animado': {'valor': '170000', 'fonte': 'Wikipédia'}}}})
    assert ac['dados'] == {'valor': '170000', 'fonte': 'Wikipédia'} and m
    ac, m = contrato.normalizar_dados({'tipo': 'escala', 'fonte': 'Wikipédia', 'dados': {'itens': [{'rotulo': 'Peso', 'valor': 14500}]}})
    assert ac['tipo'] == 'numero' and ac['dados']['valor'] == 14500
    assert 'mecanismo.nivel' not in contrato.capazes('movimento')          # velocidade não é nível de líquido


def test_tela_tem_titulo_sem_conectivo_e_numero_diz_o_que_mede():
    p = contrato.params_tela({'mostrar': 'Deformação das chapas de aço e rebites do casco'}, 'mecanismo.estados', {})
    assert not p['titulo'].lower().endswith((' e', ' de', ' das'))
    n = contrato.params_tela({'mostrar': 'mortos no naufrágio'}, 'numero.animado', {'valor': 1517, 'unidade': 'valor'})
    assert n['unidade'] == '' and n['rotulo'] == 'MORTOS NO NAUFRÁGIO'


def test_planos_seguidos_com_a_mesma_foto_viram_um():
    out = [{'comp': 'banner.discreto', 'start': 0, 'end': 2, 'params': {'rotulo': 'CONTEXTO'}, 'fundo': {'img': 'a.jpg'}, 'origem': [0], 'fala': 'a'},
           {'comp': 'foto.documental', 'start': 2, 'end': 4, 'params': {}, 'fundo': {'img': 'a.jpg'}, 'origem': [1], 'fala': 'b'}]
    o, d = montagem._juntar_planos_iguais(out, [{}, {}])
    assert len(o) == 1 and o[0]['comp'] == 'banner.discreto' and o[0]['end'] == 4 and o[0]['origem'] == [0, 1]


# ── plano vinculante ──
def _roteiro_com_inviavel():
    cenas = [{'tipo': 'gancho', 'fala': 'Como o Titanic afundou?', 'acontecimento': _ac('e0', 'ambiente', 'Titanic', crit=False)}]
    cenas += [{'tipo': 'historia', 'fala': f'O RMS Titanic partiu de Southampton em 1912, fato {i}.', 'acontecimento': _ac(f'e{i}', 'numero', 'Titanic', {'valor': 1912, 'fonte': 'Wikipédia'}, crit=False)} for i in range(1, 6)]
    cenas.insert(3, {'tipo': 'historia', 'fala': 'A enzima corta a proteína.', 'acontecimento': _ac('e9', 'mecanismo', 'enzima')})
    return _v(cenas)


def test_plano_registra_status_e_faz_um_ajuste_depois_retira_com_seguranca():
    v = _roteiro_com_inviavel()
    chamadas = []
    pl = plano_exec.vincular(v, '', chamar=lambda p: chamadas.append(p) or {'ajustes': []})
    assert len(chamadas) == 1                                            # um só ajuste
    assert pl['historico']['retirados'] == ['e9'] and not pl['inviaveis']
    assert all(c['acontecimento']['id'] != 'e9' for c in v['cenas']) and v['_plano_visual_exec'] is pl
    assert {a['status'] for a in pl['acontecimentos']} <= {plano_exec.STATUS_OK, plano_exec.STATUS_REV}


def test_plano_recusa_quando_retirar_descaracterizaria_o_roteiro():
    v = _roteiro_com_inviavel()
    for k, eid in ((2, 'e7'), (4, 'e8')):                                    # 3 inviáveis > MAX_RETIRADAS (2)
        v['cenas'][k]['acontecimento'] = _ac(eid, 'mecanismo', 'enzima')
    with pytest.raises(ValueError, match='antes da narração'):
        plano_exec.vincular(v, '', chamar=lambda p: (_ for _ in ()).throw(RuntimeError('IA fora')))
    assert len(v['_plano_visual_exec']['inviaveis']) == 1 and v['_estados'][-1]['ok'] is False


def test_numero_estruturado_nao_e_lido_como_texto_e_respeita_a_escala():
    L = preparo.pesquisa({'fatos': 'FATOS:\n- A população passou de 2,5 bilhões em 1950 para 7,8 bilhões em 2020. (ONU)\n'})
    ac = _ac('e1', 'evolucao_temporal', 'população', crit=False, representacao={'modo': 'composicao', 'comp': 'grafico.linha'})
    ok = cobertura.avaliar_evento(ac, 'A população cresceu de 1950 a 2020.', 'grafico.barras', {'itens': [{'rotulo': 'População', 'valor': 2.5}], 'unidade': 'bi'}, None, None, '', L)
    sem_unidade = cobertura.avaliar_evento(ac, 'A população cresceu de 1950 a 2020.', 'grafico.barras', {'itens': [{'rotulo': 'População', 'valor': 2.5}]}, None, None, '', L)
    assert '25' not in ok['motivo'] and ok['verificacoes']['dados'] != 'falha'
    assert sem_unidade['verificacoes']['dados'] == 'falha'                 # "2.5" sem unidade não é "2,5 bilhões"


def test_nota_de_destaque_nao_vira_selo_de_contexto_e_une_com_a_mesma_foto():
    out = [{'comp': 'banner.discreto', 'start': 0, 'end': 2, 'params': {'rotulo': 'NOTA', 'texto': '2 degraus a menos'}, 'fundo': {'img': 'a.jpg'}, 'origem': [0], 'fala': 'a'},
           {'comp': 'foto.documental', 'start': 2, 'end': 4, 'params': {}, 'fundo': {'img': 'a.jpg'}, 'origem': [1], 'fala': 'b'}]
    o, _ = montagem._juntar_planos_iguais(out, [{}, {}])
    assert len(o) == 1 and o[0]['params']['rotulo'] == 'NOTA' and o[0]['end'] == 4


# ── render: a linha do tempo não pode vazar para as outras cenas (Pompeia, piloto real: "1748" em quase todo o vídeo) ──
def test_cena_oculta_esconde_inclusive_filhos_que_reverteram_visibility(tmp_path):
    from src.v2 import palco
    d = {'duration': 12, 'meta': {'motor': 'v2'}, 'captions': [], 'scenes': [
        {'comp': 'numero.animado', 'start': 0, 'end': 6, 'params': {'valor': 33, 'unidade': 'km', 'rotulo': 'ALTURA DA COLUNA'}},
        {'comp': 'linha_tempo.historica', 'start': 6, 'end': 12, 'params': {'eventos': [{'ano': 79, 'texto': 'Soterramento'}, {'ano': 1748, 'texto': 'Redescoberta'}]}}]}
    js = """[...document.querySelectorAll('.ano')].filter(e=>getComputedStyle(e).visibility!=='hidden'&&e.getBoundingClientRect().width>0).map(e=>e.textContent)"""
    with palco.abrir(palco.preparar(d), tmp_path) as pg:
        for t in (.5, 3, 5.5):
            pg.evaluate(f'seek({t})')
            assert pg.evaluate(js) == [], t                  # nenhum ano da linha do tempo visível na cena do número
        pg.evaluate('seek(11)')
        assert '1748' in pg.evaluate(js)


def test_objeto_avulso_nao_e_contexto_de_outro_fato():
    linhas = preparo.pesquisa({'fatos': 'FATOS:\n- Arqueólogos encontraram em Pompeia um morador protegendo a cabeça. (Wikipédia)\n'})
    gato = {'id': 'a0', 'arq': __file__, 'mostra': 'Foto de uma estatueta de bronze representando Bastet como gato, de Pompeia', 'ano': 79, 'tipo_img': 'foto'}
    ac = _ac('e1', 'evento_historico', 'morador de Pompeia', estado_final='protegendo a cabeça')
    v = {'titulo': 'Como Pompeia foi soterrada?', 'fatos': 'FATOS:\n- Arqueólogos encontraram em Pompeia um morador protegendo a cabeça. (Wikipédia)\n',
         'fontes': ['Wikipédia'], 'acervo': [gato],
         'cenas': [{'tipo': 'historia', 'fala': 'Arqueólogos encontraram em Pompeia um morador protegendo a cabeça.', 'acontecimento': ac, 'grupo': 0, 'evento': 'i0'}]}
    preparo.preparar(v)
    assert (v['cenas'][0]['acontecimento'].get('representacao') or {}).get('foto') != 'a0'
    assert preparo._objeto_alheio({'mostra': 'Moeda romana'}, {'sujeito': 'moeda'}, 'a moeda foi achada') is False


def test_numero_sem_unidade_recebe_a_unidade_do_texto_que_o_sustenta():
    p = contrato.params_tela({'mostrar': 'coluna de cinzas'}, 'numero.animado', {'valor': 33}, ['A coluna subiu 33 km.'])
    assert p['unidade'] == 'km'
    assert contrato.unidade_no_texto(3000000, ['3 milhões de pessoas']) == 'pessoas'
    assert contrato.unidade_no_texto(33, ['trinta e três quilômetros']) == 'quilômetros'
    assert contrato.unidade_no_texto(6, ['muitos andares']) == ''         # não inventa: o número não está escrito


def test_legenda_de_lugar_e_a_mesma_foto_viram_um_plano():
    out = [{'comp': 'lower_third', 'start': 0, 'end': 2, 'params': {'texto': 'Fórum de Pompeia'}, 'fundo': {'img': 'a.jpg'}, 'origem': [0], 'fala': 'a'},
           {'comp': 'foto.documental', 'start': 2, 'end': 4, 'params': {}, 'fundo': {'img': 'a.jpg'}, 'origem': [1], 'fala': 'b'}]
    o, _ = montagem._juntar_planos_iguais(out, [{}, {}])
    assert len(o) == 1 and o[0]['comp'] == 'lower_third' and o[0]['end'] == 4
