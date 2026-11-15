"""V2.4 — planejamento visual direcionado (1 tentativa) para crítico OBSERVÁVEL sem imagem específica nem composição,
e as correções finais da Evidência V1 (cronologia por dados.ano; visão incompleta; mecanismo × entidade).
Dados reais da execução 43654018515/43700052750 (fixture v24_selecao_43654018515.json). Sem IA, sem rede."""
import copy
import json
from pathlib import Path

import pytest

from src.v2 import evidencia as E
from src.v2 import planejamento, preparo
from src.v2 import visao_provedores as P

D = json.loads((Path(__file__).parent / 'piloto_lagartixa' / 'v24_selecao_43654018515.json').read_text(encoding='utf-8'))

A3_OK = {'id': 'e2', 'saida': 'foto_ilustrativa', 'foto': 'a3', 'parte': 'lamelas na parte de baixo dos dedos',
         'trecho_imagem': "Close-up of the underside of a gecko's foot", 'trecho_fato': 'referente às lamelas dos dedos'}


def _v():
    return {'tipo_conteudo': 'geral', 'fatos': D['fatos'], 'cenas': copy.deepcopy(D['cenas']), 'acervo': copy.deepcopy(D['acervo'])}


def _ia(planos, chamadas=None):
    return lambda p: (chamadas.append(p) if chamadas is not None else None) or {'planos': planos}


def test_so_e2_e_pendente_e3_e11_e12_ja_tem_representacao():
    assert [p['id'] for p in planejamento.pendentes(_v())] == ['e2']


def test_foto_generica_vira_ilustracao_identificada_nunca_prova():
    v, chamadas = _v(), []
    rel = planejamento.planejar(v, chamar=_ia([A3_OK], chamadas))
    assert len(chamadas) == 1 and [a['evento'] for a in rel['aceitos']] == ['e2']
    assert 'e3' not in chamadas[0].split('ACONTECIMENTOS:')[1] and '"id": "e2"' in chamadas[0]
    prep = preparo.preparar(v, v['acervo'])
    assert prep['bloqueios'] == []
    e2 = next(e for e in prep['eventos'] if e['id'] == 'e2')
    assert e2['representacao']['modo'] == 'foto_ilustrativa' and e2['representacao']['foto'] == 'a3' and e2['representacao']['nao_prova']
    assert e2['funcao'] == 'ilustracao' and e2['evidencia_visual'] is False and e2['critico']
    assert e2['ilustracao']['rotulo'] == 'imagem ilustrativa · não identifica a espécie'
    assert any(r['evento'] == 'e2' and 'ILUSTRATIVA' in r['problema'] for r in prep['revisoes'])     # revisão humana
    cena = next(c for c in v['cenas'] if c['acontecimento']['id'] == 'e2')
    assert cena['foto'] == 'a3' and cena['rotulo_ilustracao'] and 'CC BY-SA' in cena['credito']
    assert cena['acontecimento']['importancia'] in ('critica', None) and cena['acontecimento'].get('obrigatoria', True) is not False


@pytest.mark.parametrize('prop,motivo', [
    ({**A3_OK, 'foto': 'a0', 'trecho_imagem': "structure of the gecko's toe pads"}, 'outra identidade'),            # outra espécie
    ({**A3_OK, 'foto': 'a2', 'trecho_imagem': 'lagartixa tropical Hemidactylus mabouia'}, 'espécie identificada'),   # só a espécie
    ({**A3_OK, 'foto': 'a10', 'trecho_imagem': 'Tropical House Gecko'}, 'espécie identificada'),
    ({**A3_OK, 'foto': 'a4', 'trecho_imagem': 'Geco Tarentola mauritanica'}, 'outra identidade'),                    # outra espécie, só no título
    ({**A3_OK, 'foto': 'a13', 'trecho_imagem': 'Astrobee robotic free-flyer with blue tentacle-like arms'}, 'não catalogada como genérica'),
    ({**A3_OK, 'trecho_imagem': 'lamelas microscópicas visíveis em detalhe'}, 'não está literalmente'),            # inventado
    ({**A3_OK, 'trecho_fato': 'lamelas com 400 mil cerdas cada'}, 'não está literalmente nos FATOS'),
    ({**A3_OK, 'foto': 'a99'}, 'não está no acervo'),
    ({'id': 'e2', 'saida': 'composicao', 'tipo': 'processo', 'dados': {'etapas': ['lamelas liberam cola', 'cola seca']}}, 'sem rastreio'),
    ({'id': 'e2', 'saida': 'impossivel', 'motivo': 'sem imagem fiel'}, 'impossível')])
def test_planos_infieis_sao_recusados_e_o_bloqueio_continua(prop, motivo):
    v = _v()
    rel = planejamento.planejar(v, chamar=_ia([prop]))
    assert rel['aceitos'] == [] and motivo in rel['recusados'][0]['motivo'], rel
    prep = preparo.preparar(v, v['acervo'])
    assert [b['evento'] for b in prep['bloqueios']] == ['e2']


def test_composicao_didatica_rastreada_tambem_resolve():
    v = _v()
    prop = {'id': 'e2', 'saida': 'composicao', 'tipo': 'mecanismo',
            'dados': {'nos': [{'nome': 'lamelas dos dedos'}, {'nome': 'almofadas adesivas'}]}}
    rel = planejamento.planejar(v, chamar=_ia([prop]))
    assert [a['evento'] for a in rel['aceitos']] == ['e2']
    e2 = next(e for e in preparo.preparar(v, v['acervo'])['eventos'] if e['id'] == 'e2')
    assert e2['representacao'] == {'modo': 'composicao', 'comp': 'diagrama.explicativo'} and e2['funcao'] == 'ilustracao'


def test_ia_fora_do_ar_mantem_o_bloqueio():
    v = _v()
    rel = planejamento.planejar(v, chamar=lambda p: (_ for _ in ()).throw(RuntimeError('503')))
    assert rel['chamadas'] == 0 and '503' in rel['erro']
    assert [b['evento'] for b in preparo.preparar(v, v['acervo'])['bloqueios']] == ['e2']


def test_sem_pendente_nenhuma_chamada():
    v = _v()
    for c in v['cenas']:
        if c['acontecimento']['id'] == 'e2':
            c['acontecimento']['plano_visual'] = {'modo': 'foto_ilustrativa', 'foto': 'a3', 'rotulo': 'x', 'nao_prova': True}
    chamadas = []
    assert planejamento.planejar(v, chamar=_ia([], chamadas))['pendentes'] == [] and chamadas == []


def test_plano_ilustrativo_nao_vale_para_imagem_incompativel():
    """O preparo reconfere o plano contra o acervo: imagem de outra espécie nunca entra, mesmo se gravada no contrato."""
    v = _v()
    for c in v['cenas']:
        if c['acontecimento']['id'] == 'e2':
            c['acontecimento']['plano_visual'] = {'modo': 'foto_ilustrativa', 'foto': 'a0', 'rotulo': 'x', 'nao_prova': True}
    assert [b['evento'] for b in preparo.preparar(v, v['acervo'])['bloqueios']] == ['e2']


def test_montagem_identifica_a_ilustracao_na_tela():
    import inspect
    from src.v2 import montagem
    src = inspect.getsource(montagem.converter)
    assert "sc.get('rotulo_ilustracao')" in src and "'rotulo': 'ILUSTRAÇÃO'" in src


# ───────────────────────── Evidência V1 ─────────────────────────
INCERTO = {'origem': 'gemini', 'viu_legenda': False, 'natureza': 'foto', 'confere_com': 'incerto', 'classe_confere': True, 'confianca': 'media'}


def _ev1(eid, refs):
    cenas = [c for c in D['cenas'] if c['acontecimento']['id'] == eid]
    bruto, falas = cenas[0]['acontecimento'], [c['fala'] for c in cenas]
    return E.acontecimento(bruto, falas, E.referencias_do_evento(refs, bruto, falas), eid)


def test_v1_cronologia_por_dados_ano():
    ev = _ev1('e11', {'entidades': [{'nome': 'NASA', 'categorias': ['NASA']}]})
    assert ev['intervalo'].get('inicio') and ev['intervalo']['inicio'].year == 2025
    jpl = {'fonte': 'commons', 'titulo': 'Gecko Adhesives', 'categorias': ['NASA'], 'licenca': 'PD-NASA',
           'descricao': 'Gecko-inspired adhesives developed at NASA Jet Propulsion Laboratory', 'datas': {'criacao_declarada': E.intervalo('2014-09-30')}}
    a = E.avaliar(ev, jpl, {**INCERTO, 'confere_com': 'acao', 'confianca': 'alta'})
    assert a['nivel'] not in ('PROVA', 'RELACIONADA'), a          # 2014 antes de 2025: não representa o teste de 2025
    astro = {'fonte': 'nasa', 'titulo': 'An Astrobee robotic free-flyer with blue tentacle-like arms', 'categorias': [], 'licenca': 'PD-NASA',
             'descricao': 'Astrobee with gecko-like adhesive pads aboard the International Space Station', 'datas': {'criacao_declarada': E.intervalo('2025-02-04')}}
    b = E.avaliar(ev, astro, {**INCERTO, 'confere_com': 'acao', 'confianca': 'alta'})
    assert b['nivel'] == 'RELACIONADA'                            # sem fonte independente de categoria: nunca PROVA


def test_v1_foto_da_especie_em_mecanismo_e_so_contexto():
    refs = {'entidades': [{'nome': 'Hemidactylus mabouia', 'categorias': ['Hemidactylus mabouia']}]}
    ev = _ev1('e2', refs)
    reg = {'fonte': 'commons', 'titulo': 'Day 30 Tropical House Gecko (Hemidactylus mabouia)', 'categorias': ['Hemidactylus mabouia'],
           'datas': {}, 'descricao': 'Lower Sabie Camp', 'licenca': 'CC BY-SA 2.0'}
    a = E.avaliar(ev, reg, INCERTO)
    assert a['nivel'] == 'CONTEXTO' and any('não o mecanismo' in m for m in a['motivos'])


def test_v1_visao_incompleta_quando_o_catalogo_falha():
    def chamar(provedor, prompt, imgs, modelo):
        if 'CATALOGO' in prompt:
            raise RuntimeError('503 UNAVAILABLE')
        return json.dumps({'avaliacoes': [{'i': 0, 'acontecimento': 'e11', 'confere_com': 'acao', 'classe_confere': True,
                                           'natureza': 'foto', 'confianca': 'alta'}]})
    evs = [{'id': 'e11', 'tipo': 'mecanismo', 'critico': True, 'exige': ['acao'], 'sujeito': 'Astrobee', 'acao': 'agarrar'}]
    r = P.ler_roteiro(evs, {'a13': b'x'}, 'CATALOGO {n}', 'CASAR {n} {primeiro} {acontecimentos}',
                      chamadores={'gemini': lambda *a, **k: chamar('gemini', *a, **k), 'nvidia': lambda *a, **k: chamar('nvidia', *a, **k)})
    reg = r['registro']
    assert reg['estado'] == 'incompleta' and reg['concordancia'] is None and reg['dupla'] == []
    assert any('catálogo' in f for f in reg['falhas']) and any('NVIDIA não consultada' in f for f in reg['falhas'])
    assert reg['retidas_nvidia'] == {'a13': 'sem catálogo cego da imagem: não envio ao endpoint grátis'}   # privacidade intacta
    txt = E.resumo({'versao': 'x', 'eventos': [], 'bloqueios': [], 'revisoes': [], 'divergencias': [], 'visao': reg})
    assert 'visão INCOMPLETA' in txt and 'NÃO é concordância' in txt
