"""V2.4 — seleção de imagens por IDENTIDADE DOCUMENTAL (preparo V2.3) e vínculos POR ACONTECIMENTO (Evidência V1),
com os dados reais da execução 43654018515 (tests/piloto_lagartixa/v24_selecao_43654018515.json: os acontecimentos
e2, e3, e11, e12 e o catálogo do acervo, imagens corretas e enganosas). Sem IA, sem rede.

Gabarito (auditoria independente):
  e2  desenho anatômico de OUTRA espécie (a0, Tarentola) não representa Hemidactylus mabouia; sem representação
      legítima, o bloqueio continua
  e3  a3 (sola da pata no vidro) representa a anatomia visível, nunca prova a escala microscópica
  e11 a13/a15/a18 (Astrobee, NASA, 2025): "NASA" é quem assina, não o objeto visual; a10 (lagartixa) nunca serve
  e12 a9/a11 (Suni Williams + Astrobee) servem; fotos de lagartixa (a12) nunca
"""
import copy
import json
from pathlib import Path

import pytest

from src.v2 import evidencia as E
from src.v2 import identidade, preparo

D = json.loads((Path(__file__).parent / 'piloto_lagartixa' / 'v24_selecao_43654018515.json').read_text(encoding='utf-8'))
ACV = {x['id']: x for x in D['acervo']}


def _ev(eid):
    cenas = [c for c in D['cenas'] if c['acontecimento']['id'] == eid]
    ac = cenas[0]['acontecimento']
    return ac, {'mostrar': cenas[0].get('mostrar'), 'tipo': cenas[0]['tipo'], '_falas': [c['fala'] for c in cenas]}


def _forca(eid, img, ano=None):
    ac, ctx = _ev(eid)
    ano = ano if ano is not None else (2025 if eid == 'e11' else None)       # e11 declara dados.ano = 2025
    return preparo.avaliar_imagem(ACV[img], ac, ctx, ano)


def _v():
    return {'tipo_conteudo': 'geral', 'fatos': D['fatos'], 'cenas': copy.deepcopy(D['cenas']), 'acervo': copy.deepcopy(D['acervo'])}


# ───────────────────────── preparo V2.3: imagem por imagem ─────────────────────────
def test_e2_desenho_de_outra_especie_e_incompativel():
    a = _forca('e2', 'a0')
    assert not a['compativel'] and 'identidade diferente' in a['motivos'][0] and 'tarentola mauretanica' in a['motivos'][0]


@pytest.mark.parametrize('img', ['a2', 'a8', 'a10', 'a12', 'a16'])
def test_e2_foto_da_especie_e_so_contexto(img):
    assert _forca('e2', img)['forca'] <= 1                  # mostra a espécie, não as lamelas narradas


def test_e3_sola_no_vidro_representa_a_anatomia_visivel_e_nunca_a_escala_microscopica():
    a = _forca('e3', 'a3')
    assert a['forca'] == 2 and any('escala microscópica' in m for m in a['motivos'])
    datado = _forca('e3', 'a3', ano=2009)                         # mesmo com época, a escala impede "mostra o fato"
    assert datado['forca'] < 3
    for img in ('a2', 'a10', 'a12', 'a19', 'a20'):               # outras lagartixas/lagartos: contexto, no máximo
        assert _forca('e3', img)['forca'] <= 1, img


@pytest.mark.parametrize('img', ['a13', 'a15'])
def test_e11_astrobee_e_registro_documental_mesmo_com_sujeito_nasa(img):
    a = _forca('e11', img)
    assert a['forca'] == 3 and 'registro documental' in a['motivos'][0]
    assert 'Astrobee' in a['motivos'][0] and 'NASA' in a['motivos'][0] and '2025' in a['motivos'][0]


@pytest.mark.parametrize('img,teto', [('a10', .5), ('a12', .5), ('a2', .5), ('a1', 1), ('a5', 2), ('a7', 2)])
def test_e11_enganosas_nao_mostram_o_fato(img, teto):
    """lagartixas (sem o assunto) · dispositivo do JPL de 2014 (só contexto) · Victor Glover com o Astrobee em 2021
    (outra época: no máximo o que o roteiro pediu)."""
    a = _forca('e11', img)
    assert a['forca'] <= teto, (img, a)


def test_e12_suni_williams_serve_e_lagartixa_nunca():
    assert _forca('e12', 'a9')['forca'] >= 2 and _forca('e12', 'a11')['forca'] >= 2
    for img in ('a12', 'a10', 'a2', 'a5'):                      # a5 é Victor Glover: outra pessoa
        assert _forca('e12', img)['forca'] <= .5, img


# ───────────────────────── preparo V2.3: decisão ─────────────────────────
def test_preparo_decide_e11_foto_direta_e3_e12_declaradas_e_mantem_e2_bloqueado():
    v = _v()
    rel = preparo.preparar(v, v['acervo'])
    ev = {e['id']: e for e in rel['eventos']}
    assert ev['e11']['representacao']['modo'] == 'foto_direta' and ev['e11']['foto'] in ('a13', 'a15')
    assert ev['e11']['funcao'] == 'evidencia'
    assert ev['e3']['representacao']['modo'] == 'foto_declarada' and ev['e3']['foto'] == 'a3'   # nunca "direta"
    assert ev['e12']['representacao']['modo'] == 'foto_declarada' and ev['e12']['foto'] in ('a9', 'a11')
    assert [b['evento'] for b in rel['bloqueios']] == ['e2']                                    # bloqueio legítimo
    assert {r['evento'] for r in rel['revisoes']} >= {'e3', 'e12'}                              # crítico declarado: revisão


# ───────────────────────── identidade ─────────────────────────
def test_instituicao_que_assina_nao_e_objeto_visual():
    ac, ctx = _ev('e11')
    c = identidade.confrontar(identidade.do_acontecimento(ac, ctx['_falas']), ACV['a13'])
    assert 'NASA' in c['assinantes'] and 'Astrobee' in c['visiveis']


def test_binomio_so_com_marca_de_nome_cientifico():
    assert identidade.binomios('O Ever Given levava') == set()
    assert identidade.binomios('', ['Flickr images', 'Extracted images']) == set()
    assert identidade.binomios('lagartixa da espécie Tarentola mauretanica') == {'tarentola mauretanica'}
    assert identidade.binomios('', ['Hemidactylus mabouia (Dominica)']) == {'hemidactylus mabouia'}


# ───────────────────────── Evidência V1: vínculos por acontecimento ─────────────────────────
REFS_VIDEO = {'evento': {'nomes': ['Gekkota', 'lagartixa'], 'categorias': ['Gekkota']},
              'entidades': [{'nome': 'Hemidactylus mabouia', 'categorias': ['Hemidactylus mabouia']},
                            {'nome': 'NASA', 'categorias': ['NASA']}]}
REG_GECKO = {'fonte': 'commons', 'titulo': 'Day 30 Tropical House Gecko (Hemidactylus mabouia)', 'categorias': ['Hemidactylus mabouia', 'Gekkota'],
             'datas': {}, 'descricao': 'Lower Sabie Camp, Kruger NP', 'licenca': 'CC BY-SA 2.0'}
REG_SUNI = {'fonte': 'nasa', 'titulo': 'Astronaut Suni Williams monitors an Astrobee robotic free-flyer', 'categorias': [],
            'datas': {}, 'descricao': 'NASA astronaut Suni Williams monitors an Astrobee outfitted with gecko-like adhesive pads', 'licenca': 'PD-NASA'}
INCERTO = {'origem': 'gemini', 'viu_legenda': False, 'natureza': 'foto', 'confere_com': 'incerto', 'classe_confere': True, 'confianca': 'media'}


def _ev1(eid):
    cenas = [c for c in D['cenas'] if c['acontecimento']['id'] == eid]
    bruto, falas = cenas[0]['acontecimento'], [c['fala'] for c in cenas]
    return E.acontecimento(bruto, falas, E.referencias_do_evento(REFS_VIDEO, bruto, falas), eid)


@pytest.mark.parametrize('eid', ['e11', 'e12'])
def test_v1_foto_de_lagartixa_nao_se_liga_ao_astrobee(eid):
    ev = _ev1(eid)
    assert not any(e['nome'] == 'Hemidactylus mabouia' for e in ev['referencias']['entidades'])
    assert ev['referencias']['evento'] == {}
    assert E.avaliar(ev, REG_GECKO, INCERTO)['nivel'] == 'INCOMPATIVEL'


def test_v1_e12_suni_williams_tem_vinculo_proprio_e_nao_vira_prova_sem_categoria():
    a = E.avaliar(_ev1('e12'), REG_SUNI, {**INCERTO, 'confere_com': 'acao', 'confianca': 'alta'})
    assert a['nivel'] == 'RELACIONADA' and a['sinais']['registro']['vinculo_entidade'] == 'descricao'


def test_v1_e2_desenho_de_outra_especie_incompativel_e_foto_da_especie_nunca_prova():
    ev = _ev1('e2')
    assert ev['taxons'] == ['hemidactylus mabouia']
    reg_tar = {'fonte': 'commons', 'titulo': "Gecko's secret power", 'categorias': [], 'datas': {}, 'licenca': 'CC BY-SA 3.0',
               'descricao': 'The drawing represent a Gecko (Tarentola mauretanica Linnaeus, 1758).'}
    assert E.avaliar(ev, reg_tar, INCERTO)['nivel'] == 'INCOMPATIVEL'
    assert E.avaliar(ev, REG_GECKO, INCERTO)['nivel'] != 'PROVA'          # a espécie certa, sem as lamelas confirmadas


def test_v1_fase_anonima_do_acontecimento_central_continua_herdando():
    """Santa Helena/Ever Given: fala sem nome próprio herda o acontecimento central (como antes)."""
    bruto = {'tipo': 'movimento', 'sujeito': 'face norte', 'acao': 'desliza de uma só vez', 'importancia': 'critica'}
    refs = E.referencias_do_evento({'evento': {'nomes': ['1980 eruption of Mount St. Helens']}, 'entidades': [{'nome': 'Mount St. Helens'}]},
                                   bruto, ['Toda a face norte deslizou.'])
    assert refs['evento'] and refs['entidades']


# ───────────────────────── dados reais completos (checkpoint decifrado, se existir) ─────────────────────────
CK = Path('/home/claude/pacote/saida/2026-11-14/checkpoint')


@pytest.mark.skipif(not (CK / 'roteiro.json').exists(), reason='checkpoint real da 43654018515 não está nesta máquina (é privado)')
def test_checkpoint_real_completo(tmp_path):
    from src.v2 import checkpoint as ck, prevalidacao
    c = ck.Checkpoint(tmp_path, CK, 'roteiro')
    v = c.carregar('roteiro')['v']
    chamadas = []
    prevalidacao.reparar(v, chamar=lambda p: chamadas.append(p) or {'contratos': []})
    assert chamadas == []                                            # nada pendente: retomada sem IA de contrato
    rel = preparo.preparar(copy.deepcopy(v), copy.deepcopy(v['acervo']))
    ev = {e['id']: e for e in rel['eventos']}
    assert [b['evento'] for b in rel['bloqueios']] == ['e2']
    assert ev['e11']['representacao']['modo'] == 'foto_direta'
    for eid in ('e4', 'e5', 'e6', 'e7', 'e8', 'e9', 'e10'):          # mecanismos invisíveis: ilustração
        assert ev[eid]['funcao'] == 'ilustracao', eid
