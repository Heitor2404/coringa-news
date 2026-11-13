"""V2.2 — contrato de acontecimentos (roteirista → motor visual) e fiscal semântico que não depende de padrões."""
import inspect

from src import acontecimentos, roteiro
from src.v2 import avaliacao_contrato, capacidades, contrato, fiscal_v2, montagem


def test_criterios_de_aceitacao_c1_a_c5():
    r = avaliacao_contrato.rodar()
    for k in ('C1', 'C2', 'C3', 'C4'):
        falhas = [x for x in r[k] if not x['passou']]
        assert not falhas, (k, falhas)
    assert r['C5']['passou'], r['C5']


def test_acontecimento_critico_nao_reconhecido_impede_aprovacao_automatica():
    """A frase da reserva que os padrões não reconhecem (paráfrase) não pode virar foto aprovada."""
    v2, direcao, r = avaliacao_contrato._uma('O sangue leva oxigênio dos pulmões até as células.', None)
    assert v2['scenes'][0]['comp'] == 'foto.documental'
    assert not r['aprovacao_automatica'] and any(a['codigo'] == 'S6' for a in r['achados'])
    # o mesmo acontecimento DECLARADO sem dados: bloqueio (não só revisão), com o que falta
    v2, direcao, r = avaliacao_contrato._uma('O sangue leva oxigênio dos pulmões até as células.', {'tipo': 'processo', 'importancia': 'critica'})
    assert not r['aprovado_tecnicamente'] and direcao[0]['faltam']


def test_contrato_tem_precedencia_sobre_padroes():
    # a fala tem "percorre" (padrão de rota), mas o roteiro declarou um número
    r = capacidades.escolher({'fala': 'A luz percorre 300 mil km por segundo.', 'acontecimento': {'tipo': 'numero', 'dados': {'valor': 300000, 'fonte': 'Wikipédia'}}})
    assert r['comp'] == 'numero.animado' and r['origem'] == 'contrato'


def test_integracao_no_fluxo_real_do_roteirista():
    # o pedido do roteiro leva o contrato e a normalização o preserva (sem chamada paga: só o texto e a função)
    assert 'CONTRATO_ACONTECIMENTOS' in inspect.getsource(roteiro.escrever_explica)
    assert 'CONTRATO DE ACONTECIMENTOS' in roteiro.CONTRATO_ACONTECIMENTOS
    v = {'cenas': [{'tipo': 'historia', 'fala': 'x', 'acontecimento': {'tipo': 'Reação química', 'dados': {'etapas': ['a', 'b']}, 'importancia': 'alta'}}]}
    ac = acontecimentos.normalizar(v)['cenas'][0]['acontecimento']
    assert ac['tipo'] == 'transformacao' and ac['importancia'] == 'critica' and ac['dados']['etapas'] == ['a', 'b']
    assert set(ac) >= {'quem', 'onde', 'quando', 'recurso'}       # formato anterior continua


def test_formato_antigo_continua_funcionando():
    r = capacidades.escolher({'fala': 'A maré sobe duas vezes por dia.'})
    assert r['comp'] == 'mecanismo.nivel' and r['origem'] == 'padroes'


def test_montagem_desenha_a_composicao_declarada_em_vez_de_foto():
    v2, direcao, r = avaliacao_contrato._uma('O vapor empurra o êmbolo.', {'tipo': 'mecanismo', 'dados': {'nos': [{'id': 'a', 'rotulo': 'Vapor'}, {'id': 'b', 'rotulo': 'Êmbolo'}]}})
    assert v2['scenes'][0]['comp'] == 'diagrama.explicativo' and v2['scenes'][0]['params']['nos'][0]['rotulo'] == 'Vapor'
    assert r['aprovacao_automatica']


def test_todo_tipo_do_contrato_aponta_para_composicao_registrada(tmp_path):
    from src.v2 import galeria
    ids = {m['id'] for m in galeria.catalogo(tmp_path)}
    for t, d in contrato.TIPOS.items():
        assert set(d['comps']) <= ids, (t, set(d['comps']) - ids)
