"""V2.4 — correção ESTRUTURAL dos contratos visuais (piloto da lagartixa), offline, sem IA paga e sem rede:

  1. o prompt V2 leva os dados exigidos por tipo (gerados da tabela TIPOS); o da produção não muda;
  2. pré-validação logo depois do roteiro: correções sem IA + 1 conserto rastreado na pesquisa (nada inventado,
     crítico continua crítico, observável só fica mais restrito);
  3. evidência × ilustração: fenômeno não observável nunca é "foto relacionada/declarada"; a composição que o explica
     é ILUSTRAÇÃO, marcada como não-evidência, com o rastreio dos dados.

Os casos e5/e7 da 2ª execução (43646047814) foram RECONSTRUÍDOS a partir de docs/evidencia/PILOTO_V24_LAGARTIXA.md
(o roteiro real está no pacote cifrado): mesma fala, mesmo tipo, mesmos dados declarados.
"""
import copy
import json
from pathlib import Path

import pytest

from src import gemini, roteiro
from src.v2 import contrato, evidencia, preparo, prevalidacao

F = Path(__file__).parent / 'piloto_lagartixa'

FATOS = """ÉPOCA/LUGAR: Atual (reportagens de 2026), com aplicações tecnológicas desde 2007-2010
- A lagartixa não usa ventosas: o truque são milhões de estruturas microscópicas nas patas. [fato] (Olhar Digital)
- As cerdas das patas da lagartixa criam forças de Van der Waals com a superfície. [fato] (Wikipédia)
- Cada cerda se divide em centenas de espátulas que chegam muito perto da superfície. [fato] (Olhar Digital)
- A força de Van der Waals desaparece rapidamente quando as moléculas ficam mais afastadas. [fato] (Wikipedia (inglês))
- Moléculas próximas se atraem por dipolos instantâneos. [fato] (Wikipédia)
"""


def _cena(fala, ac, tipo='historia'):
    return {'tipo': tipo, 'fala': fala, 'acontecimento': ac, 'evento': ac.get('id')}


def _v2_execucao():
    """e5 e e7 como saíram na retomada 43646047814 (relatório): e5 mecanismo crítico com dados {}; e7 nível com 2 etapas."""
    return {'tipo_conteudo': 'geral', 'fatos': FATOS, 'acervo': [], 'fontes': [], 'cenas': [
        _cena('A lagartixa anda no teto sem *cola*.', {'id': 'e1', 'tipo': 'movimento', 'sujeito': 'lagartixa', 'acao': 'andar no teto',
                                                      'importancia': 'apoio', 'obrigatoria': False, 'dados': {}}, 'gancho'),
        _cena('Nessas patas, as *cerdas* criam forças de Van der Waals.',
              {'id': 'e5', 'tipo': 'mecanismo', 'sujeito': 'cerdas da pata', 'acao': 'criar forças de Van der Waals',
               'mostrar': 'Cerdas encostando na superfície e a atração aparecendo', 'dados': {}, 'importancia': 'critica',
               'fonte': 'Wikipédia'}),
        _cena('E ela *some* rápido quando as moléculas se afastam.',
              {'id': 'e7', 'tipo': 'nivel', 'sujeito': 'força de Van der Waals', 'acao': 'sumir quando as moléculas se afastam',
               'mostrar': 'Moléculas se afastando e a atração sumindo', 'dados': {'etapas': ['perto: atração', 'longe: some']},
               'importancia': 'critica', 'fonte': 'Wikipedia (inglês)'}),
    ]}


ETAPAS_E5 = ['cada cerda se divide em espátulas', 'espátulas chegam muito perto da superfície', 'surgem forças de Van der Waals']


def _ia(contratos, chamadas=None):
    def f(prompt):
        if chamadas is not None:
            chamadas.append(prompt)
        return {'contratos': contratos}
    return f


# ───────────────────────── 1. prompt ─────────────────────────
def test_prompt_v2_declara_os_dados_exigidos_por_tipo_e_o_da_producao_nao_muda():
    b = contrato.bloco_prompt()
    assert 'DADOS EXIGIDOS POR TIPO' in b and '"observavel": false' in b
    assert 'nivel: mecanismo.eclusa → sentido | mecanismo.nivel → de, ate' in b      # o que faltou em e7
    assert 'proporcao: proporcao → pct' in b                                        # o que faltou em e9 (1ª execução)
    assert 'DADOS EXIGIDOS' not in contrato.BLOCO_PROMPT                             # produção: o bloco de sempre
    assert roteiro.CONTRATO_ACONTECIMENTOS == contrato.BLOCO_PROMPT


def test_roteiro_so_usa_o_bloco_novo_e_a_prevalidacao_com_motor_v2():
    import inspect
    src = inspect.getsource(roteiro.escrever_explica)
    # V3.1: o motor v3 usa o mesmo contrato e a mesma pré-validação do v2; a produção (sem MOTOR_VISUAL) continua igual
    assert "_bloco_contrato() if os.getenv('MOTOR_VISUAL') in ('v2', 'v3') else CONTRATO_ACONTECIMENTOS" in src
    assert "if os.getenv('MOTOR_VISUAL') in ('v2', 'v3'):" in src and 'contratos_v2(v, fatos)' in src
    assert "if os.getenv('MOTOR_VISUAL') == 'v2':" in src          # plano vinculante V2.5 só no v2 (no v3 decide o diretor)
    assert "checkpoint.etapa('pesquisa'" in src and "checkpoint.etapa('acervo'" in src


# ───────────────────────── 2. validação e correções sem IA ─────────────────────────
def test_e5_mecanismo_sem_dados_e_invalido_e_pede_conserto():
    ac = contrato.normalizar(_v2_execucao()['cenas'][1]['acontecimento'])
    r = contrato.validar(ac)
    assert r['estado'] == 'invalido' and r['critico'] and r['precisa_reparo']
    assert r['observavel'] == 'parcial'                       # a pata é visível; a força de Van der Waals, não
    assert 'sem dados' in r['problema'] and 'ILUSTRAÇÃO' in r['problema']


def test_e7_nivel_com_duas_etapas_vira_processo_sem_ia():
    ac = contrato.normalizar(_v2_execucao()['cenas'][2]['acontecimento'])
    novo, motivos = contrato.normalizar_dados(ac)
    assert novo['tipo'] == 'processo' and novo['tipo_original'] == 'nivel' and motivos
    assert novo['dados']['etapas'] == ['perto: atração', 'longe: some']        # nada inventado
    assert contrato.validar(novo)['estado'] == 'ok'


@pytest.mark.parametrize('ac', [
    {'tipo': 'nivel', 'dados': {'etapas': ['a1', 'b1'], 'de': 1, 'ate': 2}},           # tem o dado do próprio tipo
    {'tipo': 'nivel', 'dados': {'etapas': ['subindo']}},                               # uma etapa só
    {'tipo': 'comparacao', 'dados': {'etapas': ['Brasil', 'Argentina']}},              # não é tipo dinâmico: A × B
    {'tipo': 'proporcao', 'dados': {'etapas': ['a1', 'b1']}},
    {'tipo': 'movimento', 'dados': {'etapas': ['10%', '20%']}}])                       # "etapas" numéricas
def test_correcao_deterministica_e_conservadora(ac):
    assert contrato.normalizar_dados(ac)[0]['tipo'] == ac['tipo']


def test_campo_sinonimo_vira_o_campo_da_composicao():
    novo, motivos = contrato.normalizar_dados({'tipo': 'processo', 'dados': {'passos': ['a', 'b']}})
    assert novo['dados'] == {'etapas': ['a', 'b']} and contrato.validar(novo)['estado'] == 'ok'


@pytest.mark.parametrize('ac,esperado', [
    ({'tipo': 'mecanismo', 'sujeito': 'força de Van der Waals'}, 'nao'),
    ({'tipo': 'transformacao', 'sujeito': 'nuvem de elétrons', 'acao': 'deslocar-se'}, 'nao'),
    ({'tipo': 'mecanismo', 'sujeito': 'cerdas', 'acao': 'criar forças de Van der Waals'}, 'parcial'),
    ({'tipo': 'mecanismo', 'sujeito': 'patas da lagartixa', 'acao': 'aderir por estruturas microscópicas'}, 'sim'),  # micrografia é registro
    ({'tipo': 'movimento', 'sujeito': 'navio', 'acao': 'ser empurrado pelo vento contra a margem'}, 'sim'),          # Ever Given intacto
    ({'tipo': 'impacto', 'sujeito': 'vulcão', 'acao': 'liberar energia na erupção'}, 'sim'),                         # não é mecanismo
    ({'tipo': 'mecanismo', 'sujeito': 'força de Van der Waals', 'observavel': True}, 'sim'),                         # declarado vale
    ({'tipo': 'mecanismo', 'sujeito': 'engrenagem', 'observavel': False}, 'nao')])
def test_observabilidade_por_escala_fisica_e_nao_por_assunto(ac, esperado):
    assert contrato.observabilidade(ac) == esperado


# ───────────────────────── 2b. conserto (1 chamada, rastreado) ─────────────────────────
def test_conserto_aceito_so_com_dados_rastreados_e_uma_chamada():
    v, chamadas = _v2_execucao(), []
    rel = prevalidacao.reparar(v, chamar=_ia([{'id': 'e5', 'tipo': 'processo', 'dados': {'etapas': ETAPAS_E5}, 'observavel': False,
                                              'base': ['Cada cerda se divide em centenas de espátulas']}], chamadas))
    assert len(chamadas) == 1 and rel['reparo']['pedidos'] == ['e5']          # e7 resolvido sem IA; e1 é apoio
    assert [a['evento'] for a in rel['reparo']['aceitos']] == ['e5'] and rel['pendentes_depois'] == []
    ac = v['cenas'][1]['acontecimento']
    assert ac['tipo'] == 'processo' and ac['dados']['etapas'] == ETAPAS_E5 and ac['observavel'] is False
    assert ac['obrigatoria'] is True                                         # crítico continua crítico
    assert ac['reparo']['antes'] == {'tipo': 'mecanismo', 'dados': {}}
    assert all(i['ok'] for i in ac['reparo']['rastreio'])
    pedidos = chamadas[0].split('ACONTECIMENTOS A CORRIGIR:')[1].split('Regras:')[0]
    assert '"id": "e5"' in pedidos and '"id": "e7"' not in pedidos and '"id": "e1"' not in pedidos


@pytest.mark.parametrize('proposta,motivo', [
    ({'id': 'e5', 'tipo': 'processo', 'dados': {'etapas': ['cerdas liberam cola microscópica', 'cola endurece no teto']}}, 'sem rastreio'),
    ({'id': 'e5', 'tipo': 'pessoa', 'dados': {}}, 'troca o acontecimento por foto'),
    ({'id': 'e5', 'tipo': 'processo', 'dados': {'etapas': ['cerdas']}}, 'não servem'),
    ({'id': 'e5', 'tipo': 'teleporte', 'dados': {}}, 'inválido'),
    ({'id': 'e5', 'impossivel': 'os fatos não descrevem as etapas'}, 'impossível')])
def test_conserto_recusado_mantem_o_contrato_e_o_bloqueio(proposta, motivo):
    v = _v2_execucao()
    antes = copy.deepcopy(v['cenas'][1]['acontecimento'])
    rel = prevalidacao.reparar(v, chamar=_ia([proposta]))
    assert motivo in rel['reparo']['recusados'][0]['motivo'] and rel['pendentes_depois'] == ['e5']
    assert v['cenas'][1]['acontecimento']['dados'] == antes['dados'] and v['cenas'][1]['acontecimento']['tipo'] == 'mecanismo'
    rel_p = preparo.preparar(v, [])
    b = next(b for b in rel_p['bloqueios'] if b['evento'] == 'e5')
    assert any('ILUSTRAÇÃO' in f for f in b['faltam'])                       # falta dita com a palavra certa


def test_conserto_nao_rebaixa_importancia_nem_reabre_a_foto():
    v = _v2_execucao()
    prevalidacao.reparar(v, chamar=_ia([{'id': 'e5', 'tipo': 'processo', 'dados': {'etapas': ETAPAS_E5}, 'observavel': True,
                                        'importancia': 'apoio', 'obrigatoria': False}]))
    ac = v['cenas'][1]['acontecimento']
    assert ac['importancia'] == 'critica' and ac['obrigatoria'] is True
    assert contrato.observabilidade(ac) == 'parcial'                         # "observavel": true da IA não vale


def test_ia_fora_do_ar_nao_piora_nada():
    v = _v2_execucao()
    def falha(_):
        raise RuntimeError('503')
    rel = prevalidacao.reparar(v, chamar=falha)
    assert rel['reparo']['chamadas'] == 0 and '503' in rel['reparo']['erro'] and rel['pendentes_depois'] == ['e5']


def test_sem_pendencia_nenhuma_chamada():
    v, chamadas = _v2_execucao(), []
    v['cenas'][1]['acontecimento']['dados'] = {'etapas': ETAPAS_E5}
    rel = prevalidacao.reparar(v, chamar=_ia([], chamadas))
    assert chamadas == [] and rel['reparo']['chamadas'] == 0


# ───────────────────────── fluxo completo (contratos → preparo) ─────────────────────────
def test_retomada_43646047814_reconstruida_passa_com_ilustracao_e_sem_foto():
    v = _v2_execucao()
    roteiro.contratos_v2(v, chamar=_ia([{'id': 'e5', 'tipo': 'processo', 'dados': {'etapas': ETAPAS_E5}, 'observavel': False}]))
    rel = preparo.preparar(v, [])
    assert rel['bloqueios'] == []
    for eid in ('e5', 'e7'):
        e = next(x for x in rel['eventos'] if x['id'] == eid)
        assert e['representacao'] == {'modo': 'composicao', 'comp': 'processo.etapas'}
        assert e['funcao'] == 'ilustracao' and e['evidencia_visual'] is False and e['ilustracao']['nao_prova'] is True
        assert e['observavel'] in ('nao', 'parcial')
    e5 = next(x for x in rel['eventos'] if x['id'] == 'e5')
    assert set(e5['ilustracao']['base']) == {'Olhar Digital', 'Wikipédia'}
    assert '[ILUSTRAÇÃO, não é evidência]' in preparo.resumo(rel)


def test_primeira_execucao_continua_desbloqueada_e_marca_ilustracoes():
    v = gemini.extrair_json((F / 'roteiro_bruto.txt').read_text(encoding='utf-8'))
    v.update(tipo_conteudo='geral', fatos='ÉPOCA/LUGAR: Atual (reportagens de 2026)\n')
    x = {'id': 'a3', 'arq': 'x', 'mostra': 'Foto em close das cerdas microscópicas na sola da pata de uma lagartixa', 'titulo': 'gecko foot',
         'ano': 2009, 'tipo_img': 'foto'}                                  # a foto real de e4 na execução
    for c in v['cenas']:
        if (c.get('acontecimento') or {}).get('id') == 'e4':
            c['foto'] = 'a3'
    chamadas = []
    rel_c = prevalidacao.reparar(v, chamar=_ia([], chamadas))
    assert chamadas == []           # e9 se resolve sem IA; e4 (observável) fica para o acervo; e10 é a revelação
    rel = preparo.preparar(v, [x])
    # V2.4 (auditoria do MP4 43730252500): e6 é mecanismo crítico com etapas que são frases inteiras ("contato
    # extremamente próximo") — viraria cartão de texto com ícones. Agora o preparo bloqueia e pede o esquema.
    assert [b['evento'] for b in rel['bloqueios']] == ['e6'] and rel_c['pendentes_depois'] == []
    assert any('mecanismo.estados' in f for f in rel['bloqueios'][0]['faltam'])
    funcoes = {e['id']: e['funcao'] for e in rel['eventos']}
    assert {funcoes[k] for k in ('e7', 'e8', 'e9')} == {'ilustracao'}
    assert funcoes['e4'] == 'evidencia'                                      # foto real da estrutura: evidência (revisão)
    e9 = next(e for e in rel['eventos'] if e['id'] == 'e9')
    assert e9['tipo_original'] == 'proporcao' and 'etapas' in e9['reclassificacao']


# ───────────────────────── 3. evidência × ilustração ─────────────────────────
def test_preparo_nao_aceita_foto_declarada_para_fenomeno_nao_observavel():
    v = _v2_execucao()
    v['cenas'] = [v['cenas'][2]]
    v['cenas'][0]['acontecimento'] = {**v['cenas'][0]['acontecimento'], 'tipo': 'mecanismo', 'dados': {}}
    v['cenas'][0]['foto'] = 'a1'
    x = {'id': 'a1', 'arq': 'x.jpg', 'tipo_img': 'foto', 'ano': 2019,
         'mostra': 'Moléculas se afastando e a atração sumindo, força de Van der Waals'}
    rel = preparo.preparar(v, [x])
    e = rel['eventos'][0]
    assert e['representacao']['modo'] == 'bloqueio' and e['funcao'] == 'nenhuma'
    assert any('ILUSTRAÇÃO' in f for f in e['representacao']['faltam'])


def _registro_forte():
    return {'fonte': 'commons', 'titulo': 'Van der Waals forces', 'categorias': ['Van der Waals forces'], 'datas': {}, 'descricao': '',
            'licenca': 'CC0'}


def _visao_cega(confere='acao'):
    return {'origem': 'gemini', 'viu_legenda': False, 'natureza': 'foto', 'confere_com': confere, 'classe_confere': True,
            'confianca': 'alta', 'catalogo': {'natureza': 'foto', 'acao_em_curso': True}}


def test_evidencia_v1_foto_nunca_passa_de_contexto_em_fenomeno_nao_observavel():
    ev = evidencia.acontecimento({'tipo': 'mecanismo', 'sujeito': 'força de Van der Waals', 'acao': 'sumir com a distância',
                                  'importancia': 'critica'}, ['E ela some rápido quando as moléculas se afastam.'],
                                 {'evento': {'categorias': ['Van der Waals forces']}}, 'e7')
    assert ev['observavel'] == 'nao'
    a = evidencia.avaliar(ev, _registro_forte(), _visao_cega())
    assert a['nivel'] == 'CONTEXTO' and a['nivel_sem_veto'] in ('PROVA', 'RELACIONADA')
    assert any('não observável' in m for m in a['vetos'])
    rep = evidencia.decidir(ev, [('a1', a)])
    assert rep['modo'] == 'bloqueio' and 'ILUSTRAÇÃO' in rep['faltam'][0]                # nunca "foto_relacionada"
    rep = evidencia.decidir(ev, [('a1', a)], comp='processo.etapas')
    assert rep['modo'] == 'composicao' and rep['funcao'] == 'ilustracao' and rep['nao_e_evidencia'] is True
    assert 'foto_de_apoio' not in rep                                                      # contexto não vira "apoio de prova"


def test_evidencia_v1_fenomeno_observavel_continua_podendo_ser_prova():
    ev = evidencia.acontecimento({'tipo': 'mecanismo', 'sujeito': 'lagartixa', 'acao': 'andar no teto', 'importancia': 'critica'},
                                 ['A lagartixa anda no teto.'], {'entidades': [{'nome': 'lagartixa', 'categorias': ['Hemidactylus mabouia']}]}, 'e1')
    assert ev['observavel'] == 'sim'
    reg = {'fonte': 'commons', 'titulo': 'gecko', 'categorias': ['Hemidactylus mabouia'], 'datas': {}, 'descricao': '', 'licenca': 'CC0'}
    a = evidencia.avaliar(ev, reg, _visao_cega())
    assert a['nivel'] == 'PROVA'
    assert evidencia.decidir(ev, [('a1', a)])['funcao'] == 'evidencia'
