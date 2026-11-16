"""Forma visual decidida pelo acontecimento ANTES da câmera (16/11)."""
import pytest

from src.v3 import linguagem as L


@pytest.mark.parametrize('titulo,nat', [
    ('Map of London showing the extent of the Great Fire', 'mapa'), ('Plano de la ciudad', 'mapa'),
    ('Thomas Faryner shop plaque', 'documento'), ('Letter from Samuel Pepys', 'documento'),
    ('Woodcut, 1612', 'gravura'), ('Victorian engraving after Visscher', 'gravura'),
    ('Oil painting of the Great Fire', 'pintura'), ('Golden Boy of Pye Corner', 'foto')])
def test_natureza_da_midia_pelo_titulo(titulo, nat):
    assert L.natureza({'titulo': titulo}) == nat


@pytest.mark.parametrize('tipo,viaveis,nats,forma', [
    ('mecanismo', ['mecanismo.estados'], set(), 'esquema'),
    ('processo', [], set(), 'esquema'),
    ('transformacao', ['comparacao.antes_depois'], set(), 'comparacao'),
    ('deslocamento', ['mapa.rota'], set(), 'mapa'),
    ('territorio', [], {'mapa'}, 'mapa'),
    ('localizacao', [], {'foto'}, 'registro'),          # sem mapa viável nem mapa no acervo: registro do lugar (justificado)
    ('documento', [], {'documento'}, 'documento'),
    ('numero', ['numero.animado'], set(), 'tipografia'),
    ('numero', [], set(), 'registro'),
    ('pessoa', [], {'foto'}, 'registro'),
    ('escala', ['comparacao.grandezas'], set(), 'comparacao')])
def test_forma_pelo_acontecimento(tipo, viaveis, nats, forma):
    f = L.forma_do_evento({'tipo': tipo, 'viaveis': viaveis, 'critico': True}, nats)
    assert f['forma'] == forma and f['justificativa']


def test_acao_essencial_nao_aceita_foto_com_zoom():
    ev = {'id': 'e1', 'tipo': 'mecanismo', 'critico': True, 'viaveis': ['mecanismo.estados']}
    assert 'foto com zoom' in L.validar_plano({'composicao': 'doc.plano'}, ev, {'titulo': 'gecko foot'})
    assert L.validar_plano({'composicao': 'mecanismo.estados', 'forma_visual': 'esquema'}, ev, None) is None


def test_mapa_com_foto_que_nao_e_mapa_pede_justificativa():
    ev = {'id': 'e2', 'tipo': 'deslocamento', 'critico': True, 'viaveis': ['mapa.rota']}
    assert 'pede mapa' in L.validar_plano({'composicao': 'doc.plano'}, ev, {'titulo': 'ship at sea'})
    assert L.validar_plano({'composicao': 'doc.plano', 'justificativa_forma': 'a rota está na foto aérea'}, ev, {'titulo': 'ship at sea'}) is None
    assert L.validar_plano({'composicao': 'doc.plano'}, ev, {'titulo': 'Map of the canal route'}) is None


def test_forma_diferente_da_ficha_exige_justificativa():
    ev = {'id': 'e3', 'tipo': 'pessoa', 'critico': False, 'viaveis': []}
    assert 'sem' in L.validar_plano({'composicao': 'doc.plano', 'forma_visual': 'documento'}, ev, {'titulo': 'portrait'})
    assert L.validar_plano({'composicao': 'doc.plano', 'forma_visual': 'documento', 'justificativa_forma': 'carta assinada'}, ev, {'titulo': 'portrait'}) is None


def test_regras_unificadas_no_prompt():
    from src.v3 import pipeline as P
    t = L.texto_prompt()
    for chave in ('GANCHO', 'PROGRESSÃO', 'FORMA ANTES DA CÂMERA', 'CÂMERA', 'MAPA', 'MECANISMO', 'DOCUMENTO', 'RETENÇÃO'):
        assert chave in t
    assert '{linguagem}' in P.PROMPT and '"revela"' in P.PROMPT and '"forma_visual"' in P.PROMPT
    assert 'integral' not in P.PROMPT.split('Regras de direção')[1].split('\n')[4]


def test_ficha_traz_forma_antes_da_camera():
    from src.v3 import plano_av
    v = {'cenas': [{'fala': 'a lagartixa gruda na parede', 'acontecimento': {'id': 'e1'}}]}
    acervo = {'m1': {'mostra': 'lagartixa gruda parede vidro', 'uso_comercial': 'sim', 'titulo': 'Gecko on glass'}}
    f = plano_av.fichas(v, acervo, [], [{'id': 'e1', 'tipo': 'mecanismo', 'critico': True, 'trechos': [0], 'viaveis': ['mecanismo.estados'],
                                         'ac': {'sujeito': 'lagartixa', 'acao': 'gruda na parede'}}])[0]
    assert f['forma_visual'] == 'esquema' and 'mecanismo.estados' in f['composicoes_forma']
    assert 'FORMA: esquema' in plano_av.texto_prompt([f])
