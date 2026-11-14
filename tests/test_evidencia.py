"""Modelo de evidência (experimental): regras, independência de sinais, separação representação × fato, flag desligada.
Tudo offline: sem rede, sem IA."""
import datetime as dt
import json
from pathlib import Path

import pytest

from src.v2 import avaliacao_evidencia as A
from src.v2 import evidencia as E

DEV = Path(__file__).parent / 'evidencia' / 'desenvolvimento.json'

REFS = {'evento': {'nomes': ['Grande Evento X'], 'categorias': ['Grande Evento X']},
        'entidades': [{'nome': 'Objeto Y', 'categorias': ['Objeto Y']}]}


def ev(tipo='transformacao', quando='10 de junho de 1990', estado_final='depois', **kw):
    b = {'tipo': tipo, 'sujeito': 'Objeto Y', 'acao': 'muda', 'estado_inicial': 'antes', 'estado_final': estado_final,
         'quando': quando, 'importancia': 'critica', **kw}
    return E.acontecimento(b, kw.pop('falas', ['O Objeto Y mudou.']), REFS, 'e1')


def reg(cats=('Grande Evento X',), datas=None, fonte='Commons', titulo='arquivo', desc=''):
    return E._registro(fonte, titulo, list(cats), {k: E.intervalo(v) for k, v in ({'criacao_declarada': '1990-06-10'} if datas is None else datas).items()},
                       desc, '', '', None)


def vis(confere='acao', natureza='foto', **kw):
    return {'origem': 'cega', 'viu_legenda': False, 'confere_com': confere, 'natureza': natureza, 'classe_confere': True,
            'confianca': 'alta', **kw}


# ── flag ──
def test_flag_desligada_por_padrao(monkeypatch):
    monkeypatch.delenv('EVIDENCIA_V1', raising=False)
    assert not E.ativo()
    monkeypatch.setenv('EVIDENCIA_V1', 'aplicar')
    assert not E.ativo()                      # nesta fase só existe o modo sombra
    monkeypatch.setenv('EVIDENCIA_V1', 'sombra')
    assert E.ativo()


# ── datas ──
@pytest.mark.parametrize('txt,ini,fim,prec', [
    ('18 de maio de 1980', dt.date(1980, 5, 18), dt.date(1980, 5, 18), 'dia'),
    ('23 a 29 de março de 2021', dt.date(2021, 3, 23), dt.date(2021, 3, 29), 'dia'),
    ('Março a maio de 1980', dt.date(1980, 3, 1), dt.date(1980, 5, 31), 'mes'),
    ('<time datetime="1969-07-20">20 July 1969</time>', dt.date(1969, 7, 20), dt.date(1969, 7, 20), 'dia'),
    ('1969-07-21T00:00:00Z', dt.date(1969, 7, 21), dt.date(1969, 7, 21), 'dia'),
    ('1980:05:18 08:32:00', dt.date(1980, 5, 18), dt.date(1980, 5, 18), 'dia'),
    ('1980s', dt.date(1980, 1, 1), dt.date(1989, 12, 31), 'decada'),
])
def test_intervalos(txt, ini, fim, prec):
    i = E.intervalo(txt)
    assert (i['inicio'], i['fim'], i['precisao']) == (ini, fim, prec)


def test_data_desconhecida_e_truncada():
    assert E.intervalo('')['inicio'] is None
    assert E.intervalo('Início de julho de 2')['inicio'] is None      # ano truncado no contrato: não inventa


def test_origem_da_data_commons():
    assert E._classificar_data_commons({'value': '1980-05-18', 'source': 'commons-desc-page'})[0] == 'criacao_declarada'
    assert E._classificar_data_commons({'value': '1980:05:18 08:32:00', 'source': 'mediawiki-metadata'})[0] == 'captura'
    assert E._classificar_data_commons({'value': 'published 1982', 'source': 'commons-desc-page'})[0] == 'publicacao'
    assert E._classificar_data_commons(None)[0] == 'desconhecida'


def test_upload_nunca_situa_a_imagem():
    r = reg(datas={'upload': '1990-06-10'})
    assert E.data_da_imagem(r)[0] == 'desconhecida'


# ── independência dos sinais ──
def test_prova_exige_as_duas_familias():
    a = E.avaliar(ev(), reg(), vis())
    assert a['nivel'] == 'PROVA' and set(a['familias_que_confirmam']) == {'registro', 'visao'}


def test_registro_sozinho_nunca_prova():
    for v in (None, E.visao_legada({'tipo_img': 'foto', 'mostra': 'Objeto Y mudando'}), vis('incerto')):
        assert E.avaliar(ev(), reg(), v)['nivel'] != 'PROVA'


def test_visao_sozinha_nunca_prova():
    a = E.avaliar(ev(), reg(cats=(), datas={}), vis())
    assert a['nivel'] == 'RELACIONADA'


def test_visao_que_viu_a_legenda_nao_e_independente():
    a = E.avaliar(ev(), reg(), {**vis(), 'viu_legenda': True})
    assert a['nivel'] == 'RELACIONADA'
    assert any('não é independente' in d for d in a['dependencias'])


def test_categoria_e_data_do_mesmo_registro_contam_como_uma_familia():
    # categoria do evento + data perfeita, sem visão: continua sem PROVA (mesma família)
    a = E.avaliar(ev(), reg(), None)
    assert a['nivel'] == 'RELACIONADA' and a['familias_que_confirmam'] == ['registro']


def test_metadado_desconhecido_nao_confirma():
    # só a entidade + sem data: a data não pode completar o vínculo
    a = E.avaliar(ev(), reg(cats=('Objeto Y',), datas={}), vis())
    assert a['nivel'] == 'RELACIONADA'
    assert any('desconhecida' in d for d in a['dependencias'])


def test_entidade_mais_data_na_fase_vale_como_vinculo_forte():
    a = E.avaliar(ev(), reg(cats=('Objeto Y',)), vis())
    assert a['nivel'] == 'PROVA'
    a = E.avaliar(ev(), reg(cats=('Objeto Y',), datas={'criacao_declarada': '1990'}), vis())   # só o ano: fraco
    assert a['nivel'] == 'RELACIONADA'


# ── tempo é fase ──
def test_imagem_posterior_para_acao_e_vetada():
    a = E.avaliar(ev(), reg(datas={'criacao_declarada': '2001-01-01'}), vis('acao'))
    assert a['nivel'] == 'CONTEXTO' and a['vetos']


def test_estado_final_aceita_depois_dentro_do_horizonte():
    assert E.avaliar(ev(), reg(datas={'criacao_declarada': '1990-08-01'}), vis('estado_final'))['nivel'] == 'PROVA'
    assert E.avaliar(ev(), reg(datas={'criacao_declarada': '1995-08-01'}), vis('estado_final'))['nivel'] == 'CONTEXTO'


def test_publicada_antes_do_acontecimento_so_mostra_o_antes():
    r = reg(datas={'publicacao': '1985'})
    assert E.avaliar(ev(), r, vis('acao'))['nivel'] == 'CONTEXTO'


# ── natureza ──
@pytest.mark.parametrize('nat', ['pintura', 'gerada_por_ia', 'reconstituicao_3d', 'diagrama', 'mapa', 'objeto_ou_monumento', 'cartaz'])
def test_natureza_que_nao_prova(nat):
    assert E.avaliar(ev(), reg(), vis('acao', nat))['nivel'] == 'CONTEXTO'


def test_genero_pelo_registro_vale_mesmo_se_a_visao_disser_foto():
    r = reg(cats=('Grande Evento X', 'Paintings of Objeto Y'))
    a = E.avaliar(ev(), r, vis('acao', 'foto'))
    assert a['nivel'] == 'CONTEXTO' and any('restritivo' in d for d in a['dependencias'])


def test_texto_em_escrita_que_o_publico_nao_le():
    v = vis('entidade', 'diagrama', texto_visivel={'presente': True, 'escrita': 'cirilica', 'e_o_conteudo': True})
    assert E.avaliar(ev(tipo='lugar'), reg(), v)['nivel'] == 'INCOMPATIVEL'


def test_generica_sem_vinculo_e_incompativel():
    assert E.avaliar(ev(), reg(cats=(), datas={}), vis('nao_mostra', generica=True, classe_confere=False))['nivel'] == 'INCOMPATIVEL'


def test_tipo_quantitativo_nao_se_representa_por_imagem():
    a = E.avaliar(ev(tipo='numero'), reg(), vis('acao'))
    assert a['nivel'] == 'CONTEXTO'


# ── representação × verificação factual ──
def test_imagem_nao_verifica_afirmacao():
    e = E.acontecimento({'tipo': 'evento_historico', 'sujeito': 'terremoto', 'acao': 'desencadeia', 'estado_final': 'encosta em colapso',
                         'quando': '18 de maio de 1980', 'importancia': 'critica'},
                        ['Um terremoto de *magnitude 5,1* sacudiu o vulcão e causou o maior deslizamento.'], REFS, 'e6')
    a = E.avaliar(e, reg(datas={'criacao_declarada': '1980-05-18'}), vis('estado_final'))
    assert a['nivel'] == 'PROVA'
    assert '5.1' in a['nao_comprova']                           # a foto representa o colapso, não comprova a magnitude
    sem = E.verificar_afirmacoes(e, [])
    assert {x['tipo']: x['status'] for x in sem} == {'numero': 'sem_fonte', 'superlativo': 'nao_verificada_automaticamente',
                                                      'causa': 'nao_verificada_automaticamente'}
    com = E.verificar_afirmacoes(e, [{'texto': 'Um terremoto de magnitude 5,1 desencadeou a avalancha.', 'fonte': 'Wikipédia', 'numeros': [5.1]}])
    assert com[0]['status'] == 'sustentada' and com[0]['fonte'] == 'Wikipédia'
    rep = E.decidir(e, [('a1', a)], verificacao=sem)
    assert rep['modo'] == 'foto_prova' and rep['revisao_factual']    # imagem aceita E afirmação sem fonte sinalizada


def test_citacao_so_vira_editorial_com_fonte():
    e = E.acontecimento({'tipo': 'citacao', 'sujeito': 'Fulano'}, ['Pelo rádio, Fulano avisou: *Agora vai!*'], REFS, 'e10')
    assert any(a['tipo'] == 'citacao' for a in e['afirmacoes'])


# ── decisão por acontecimento ──
def test_critico_sem_prova_bloqueia_com_o_que_falta():
    e = ev()
    rep = E.decidir(e, [('a1', E.avaliar(e, reg(), vis('outro_estado')))])
    assert rep['modo'] == 'bloqueio' and 'REGISTRO' in rep['faltam'][0]


def test_critico_relacionado_vai_para_revisao_humana():
    e = ev()
    rep = E.decidir(e, [('a1', E.avaliar(e, reg(cats=(), datas={}), vis()))])
    assert rep['modo'] == 'foto_relacionada' and rep['revisao_humana']


def test_prova_preenche_foto_historica():
    e = ev(tipo='evento_historico')
    rep = E.decidir(e, [('a1', E.avaliar(e, reg(), vis()))])
    assert rep['dados_composicao'] == {'comp': 'foto.historica', 'img': 'a1'}


def test_composicao_com_dados_continua_primeiro():
    e = ev()
    rep = E.decidir(e, [('a1', E.avaliar(e, reg(), vis()))], comp='processo.etapas')
    assert rep['modo'] == 'composicao' and rep['foto_de_apoio'] == 'a1'


# ── avaliação de desenvolvimento e pilotos ──
def test_desenvolvimento_criterios():
    r = A.rodar(DEV)
    m = r['metricas']
    assert m['falsa_prova'] == []
    assert m['invariante_sem_visao_independente'] == []
    assert m['invariante_monotonia'] == []
    assert m['prova_reconhecida'] == m['prova_esperada']
    assert m['eventos_corretos'] == m['eventos']


def test_pilotos_reproduzidos():
    r = A.pilotos()
    sh = {e['id']: e['novo'] for e in r['santa_helena']['rotulado']['eventos']}
    assert sh['e7']['modo'] == 'foto_prova' and sh['e7']['foto'] == 'a25'       # era bloqueio falso
    assert sh['e6']['modo'] == 'foto_prova'
    assert sh['e9']['modo'] != 'foto_prova'                                    # sem imagem da explosão ultrapassando
    eg = {e['id']: e['novo'] for e in r['ever_given']['rotulado']['eventos']}
    assert eg['e9']['modo'] != 'foto_prova'                                    # nenhuma imagem do navio liberado
    for par in r.values():                                                     # legado: nunca PROVA
        assert all(e['novo']['modo'] != 'foto_prova' for e in par['legado']['eventos'])


def test_nao_altera_o_roteiro():
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import _piloto
    v = _piloto.roteiro()
    antes = json.dumps(v, sort_keys=True, default=str)
    E.preparar(v, v['acervo'])
    assert json.dumps(v, sort_keys=True, default=str) == antes
