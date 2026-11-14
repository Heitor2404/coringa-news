"""Adaptador de provedores de visão (Gemini → NVIDIA), dupla leitura e ação × estado resultante — OFFLINE, com as
respostas REAIS já armazenadas (Gemini 3.5-flash-lite, NVIDIA Nemotron VL, Gemini 3.8 no Katrina). Nenhuma chamada."""
import json
from pathlib import Path

import pytest

from src.v2 import avaliacao_evidencia as A
from src.v2 import evidencia as E
from src.v2 import visao_provedores as P

R = Path(__file__).parent / 'evidencia' / 'coleta_real'
DEV = json.loads((Path(__file__).parent / 'evidencia' / 'desenvolvimento.json').read_text(encoding='utf-8'))['dominios']['naval']
REG = json.loads((R / 'registros.json').read_text(encoding='utf-8'))
CAT_NAVAL, _ = A._catalogos({'naval': json.loads((R / 'gemini' / 'naval.json').read_text(encoding='utf-8'))}, None)
GEM = json.loads((R / 'teste_modelo_43635338190' / 'casamento.json').read_text(encoding='utf-8'))
NV = json.loads((R / 'teste_openrouter_43637054557' / 'casamento.json').read_text(encoding='utf-8'))


def _leitura(prov, texto, ordem):
    return P.avaliacoes({'provedor': prov, 'modelo': prov, 'json': P.extrair(texto)}, ordem)


L_GEM = _leitura('gemini', GEM['texto'], GEM['ordem_das_imagens'])
L_NV = _leitura('nvidia', NV['chamadas'][0]['resposta']['choices'][0]['message']['content'], NV['ordem_das_imagens'])


def _nivel(ev_id, img, par, bruto_extra=None):
    d = DEV['acontecimentos'][ev_id]
    ev = E.acontecimento({**d['bruto'], **(bruto_extra or {})}, d.get('falas'), DEV['referencias'], ev_id)
    reg = A._registro_real(REG[f'naval/{img}']['bruto'], DEV['imagens'][img]['registro']['titulo'])
    return E.avaliar(ev, reg, P.para_visao(par, CAT_NAVAL.get(f'naval/{img}')))


# ── as duas respostas reais cabem no mesmo contrato ──
def test_respostas_reais_no_mesmo_contrato():
    for L in (L_GEM, L_NV):
        assert len(L) == 8
        for a in L.values():
            assert a['confere_com'] in E.CONFERE and isinstance(a.get('classe_confere'), bool)


# ── ação × estado resultante (falha comum aos dois modelos) ──
def test_navio_preso_parado_com_duas_leituras_concordantes_e_prova_do_encalhe():
    par = P.combinar(L_GEM[('i6', 'a6_commons')], L_NV[('i6', 'a6_commons')])
    assert par['provedor'] == 'dupla_concordante'
    a = _nivel('i6', 'a6_commons', par)
    assert a['nivel'] == 'PROVA'                                   # nav-01 (gabarito PROVA)
    assert a['familias_que_confirmam'].count('visao') == 1          # duas leituras = UMA família
    assert any('estado resultante' in d for d in a['dependencias'])


def test_navio_preso_parado_com_uma_leitura_so_vai_para_revisao():
    for L in (L_GEM, L_NV):
        a = _nivel('i6', 'a6_commons', L[('i6', 'a6_commons')])
        assert a['nivel'] == 'RELACIONADA'


def test_foto_do_navio_preso_nao_representa_a_liberacao():
    par = P.combinar(L_GEM[('i6', 'a6_commons')], L_NV[('i6', 'a6_commons')])
    d = DEV['acontecimentos']['i14']
    ev = E.acontecimento(d['bruto'], d['falas'], DEV['referencias'], 'i14')
    reg = A._registro_real(REG['naval/a6_commons']['bruto'], '')
    assert E.avaliar(ev, reg, P.para_visao(par, CAT_NAVAL['naval/a6_commons']))['nivel'] in ('CONTEXTO', 'INCOMPATIVEL')


def test_acao_com_movimento_continua_acao():
    v = P.para_visao({'confere_com': 'acao', 'classe_confere': True, 'confianca': 'alta', 'movimento_visivel': True},
                     {'natureza': 'foto', 'acao_em_curso': True})
    assert E._semantica(v)['confere_com'] == 'acao'


# ── imagem enganosa: homônimo de 2011 navegando ──
def test_homonimo_navegando_nunca_prova():
    par = P.combinar(L_GEM[('i2', 'a10_outro_navio')], L_NV[('i2', 'a10_outro_navio')])
    assert par.get('discordancia')                                 # Gemini "entidade" × NVIDIA "ação"
    assert _nivel('i2', 'a10_outro_navio', par)['nivel'] == 'CONTEXTO'    # nav-07
    assert _nivel('i2', 'a10_outro_navio', L_NV[('i2', 'a10_outro_navio')])['nivel'] == 'CONTEXTO'
    assert _nivel('i2', 'a12_2020', L_NV[('i2', 'a12_2020')])['nivel'] == 'CONTEXTO'  # nav-08


def test_discordancia_nunca_aprova():
    a = {'confere_com': 'acao', 'classe_confere': True, 'confianca': 'alta', 'provedor': 'gemini'}
    b = {'confere_com': 'outro_estado', 'classe_confere': True, 'confianca': 'alta', 'provedor': 'nvidia'}
    c = P.combinar(a, b)
    v = P.para_visao(c, {'natureza': 'foto', 'acao_em_curso': True})
    ev = E.acontecimento({'tipo': 'evento_historico', 'acao': 'x', 'estado_final': 'y', 'quando': '1 de maio de 2000',
                          'importancia': 'critica'}, ['x'], {'evento': {'categorias': ['Evento K']}}, 'e1')
    r = E._registro('Commons', 't', ['Evento K'], {'criacao_declarada': E.intervalo('2000-05-01')}, '', '', '', None)
    a1 = E.avaliar(ev, r, v)
    assert a1['nivel'] == 'RELACIONADA' and any('discordância' in d for d in a1['dependencias'])
    assert E.decidir(ev, [('i', a1)])['revisao_humana']


# ── vários domínios: ação em curso e estado final com respostas reais do catálogo ──
def test_katrina_resposta_real_estado_final_prova():
    lin = {x['id']: x for x in A.validacao_real()['linhas']}
    assert lin['kt-01']['real'] == 'PROVA'


def test_tacoma_colapso_em_curso_nao_e_reinterpretado():
    cat = A._catalogos({'engenharia_tacoma': json.loads((R / 'gemini' / 'engenharia_tacoma.json').read_text(encoding='utf-8'))}, None)[0]
    v = P.para_visao({'confere_com': 'acao', 'classe_confere': True, 'confianca': 'alta'}, cat['engenharia_tacoma/commons_upload'])
    assert E._semantica(v)['confere_com'] == 'acao'                # catálogo real: "ponte desabando" (acao_em_curso)


# ── adaptador: fallback, teto, privacidade, sem nova tentativa ──
def _falha(msg):
    def f(*_):
        raise RuntimeError(msg)
    return f


def test_fallback_gemini_para_nvidia_por_indisponibilidade():
    orc = P.Orcamento(4)
    r = P.ler('p', [b'x'], orc, chamadores={'gemini': _falha('503 UNAVAILABLE'), 'nvidia': lambda *_: '{"avaliacoes": []}'})
    assert r['provedor'] == 'nvidia' and r['tentativas'][-1]['fallback_de']['provedor'] == 'gemini' and orc.usadas == 2


def test_os_dois_falham_leitura_incerta_sem_repetir():
    orc = P.Orcamento(4)
    r = P.ler('p', [b'x'], orc, chamadores={'gemini': _falha('503'), 'nvidia': _falha('429 rate limit')})
    assert r.get('incerta') and orc.usadas == 2


def test_erro_que_nao_e_disponibilidade_nao_troca_de_provedor():
    orc = P.Orcamento(4)
    r = P.ler('p', [b'x'], orc, chamadores={'gemini': _falha('400 invalid argument'), 'nvidia': lambda *_: '{}'})
    assert r.get('incerta') and orc.usadas == 1


def test_teto_de_chamadas():
    orc = P.Orcamento(1)
    r = P.ler('p', [b'x'], orc, chamadores={'gemini': _falha('503'), 'nvidia': lambda *_: '{}'})
    assert r.get('incerta') and orc.usadas == 1 and 'teto' in r['tentativas'][-1]['pulado']


@pytest.mark.parametrize('cat,pode', [
    ({'elemento_principal': 'navio', 'conteudo': 'navio atravessado', 'natureza': 'satelite_ou_aerea'}, True),
    ({'elemento_principal': 'pessoa', 'conteudo': 'astronauta na superfície'}, False),
    ({'elemento_principal': 'multidão', 'conteudo': 'repórteres numa coletiva'}, False),
    ({'elemento_principal': 'placa', 'conteudo': 'aviso', 'texto_visivel': {'presente': True, 'e_o_conteudo': True}}, False),
    (None, False)])
def test_privacidade_endpoint_gratis(cat, pode):
    assert P.permitido_nvidia(cat)[0] is pode


def test_ler_roteiro_fallback_respeita_privacidade_e_registra():
    enviados = {}

    def gem(prompt, imgs):
        if 'Você vai descrever' in prompt:
            return json.dumps({'imagens': [{'i': 0, 'elemento_principal': 'navio', 'conteudo': 'navio parado', 'natureza': 'foto',
                                            'acao_em_curso': False}, {'i': 1, 'elemento_principal': 'pessoa', 'conteudo': 'retrato'}]})
        raise RuntimeError('503 UNAVAILABLE')

    def nv(prompt, imgs):
        enviados['n'] = len(imgs)
        return json.dumps({'avaliacoes': [{'acontecimento': 'e1', 'imagem': 0, 'confere_com': 'estado_final', 'classe_confere': True,
                                           'confianca': 'alta'}]})
    ev = E.acontecimento({'tipo': 'impacto', 'acao': 'bloqueia', 'estado_final': 'preso', 'quando': '2021', 'importancia': 'critica'}, ['x'], None, 'e1')
    r = P.ler_roteiro([ev], {'a': b'1', 'b': b'2'}, 'Você vai descrever {n}', 'casar {n} {primeiro} {acontecimentos}',
                      P.Orcamento(4), chamadores={'gemini': gem, 'nvidia': nv})
    assert enviados['n'] == 1                                     # o retrato não saiu para o endpoint grátis
    assert 'b' in r['registro']['retidas_nvidia']
    assert any(c.get('provedor') == 'nvidia' for c in r['registro']['chamadas'])
    assert r['visoes'][('e1', 'a')]['provedor'] == 'nvidia'
