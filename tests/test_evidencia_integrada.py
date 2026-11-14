"""Caminho INTEGRADO do modo sombra, offline: acervo → metadados reais → referências → catálogo → casamento → dupla
leitura → Evidência V1 → relatório. Respostas REAIS armazenadas (Commons, Gemini 3.5-flash-lite, NVIDIA Nemotron VL);
a Wikidata é o único dublê (rótulos e P373 conhecidos), porque a coleta não guardou essa consulta."""
import copy
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import _piloto  # noqa: E402

from src.v2 import evidencia_registros as ER  # noqa: E402
from src.v2 import visao_provedores as P  # noqa: E402

R = Path(__file__).parent / 'evidencia' / 'coleta_real'
DEV = json.loads((Path(__file__).parent / 'evidencia' / 'desenvolvimento.json').read_text(encoding='utf-8'))['dominios']['naval']
REGS = json.loads((R / 'registros.json').read_text(encoding='utf-8'))
PAGINAS = {r['bruto']['pagina']['title']: r['bruto']['pagina'] for r in REGS.values() if (r.get('bruto') or {}).get('fonte') == 'Commons'}
CAT_ANT = json.loads((R / 'gemini' / 'naval.json').read_text(encoding='utf-8'))
GEM = json.loads((R / 'teste_modelo_43635338190' / 'casamento.json').read_text(encoding='utf-8'))
NV = json.loads((R / 'teste_openrouter_43637054557' / 'casamento.json').read_text(encoding='utf-8'))
NV_TXT = NV['chamadas'][0]['resposta']['choices'][0]['message']['content']
DEV_PARA_PILOTO = {'i6': 'e4', 'i2': 'e2'}                       # mesmos acontecimentos, ids do contrato do piloto
FIX_POR_PILOTO = {img['pilot_id']: k for k, img in DEV['imagens'].items() if img.get('pilot_id')}
WIKIDATA = {'2021 Suez Canal obstruction': ('Q1', ['2021 Suez Canal obstruction', 'Obstrução do Canal de Suez em 2021'], ['2021 Suez Canal obstruction']),
            'Ever Given': ('Q2', ['Ever Given'], ['Ever Given (ship, 2018)'])}


def get_falso(url, params):
    if 'wikipedia' in url and params.get('list') == 'search':        # dublê: a busca da Wikipédia pelo título acha o artigo
        return {'query': {'search': [{'title': 'Obstrução do Canal de Suez em 2021'}] if 'Suez' in params['srsearch'] else []}}
    if 'wikipedia' in url:
        return {'query': {'pages': [{'pageprops': {'wikibase_item': 'Q1'}}]}}
    if 'commons' in url:
        return {'query': {'pages': [PAGINAS[t] for t in params['titles'].split('|') if t in PAGINAS]}}
    if 'wikidata' in url and params['action'] == 'wbsearchentities':
        h = next(((q, a, c) for k, (q, a, c) in WIKIDATA.items() if k.lower() in params['search'].lower()), None)
        return {'search': [{'id': h[0]}] if h else []}
    if 'wikidata' in url:
        q, a, c = next(x for x in WIKIDATA.values() if x[0] == params['ids'])
        return {'entities': {q: {'labels': {'en': {'value': a[0]}}, 'aliases': {'pt': [{'value': x} for x in a[1:]]},
                                 'claims': {'P373': [{'mainsnak': {'datavalue': {'value': x}}} for x in c]}}}}
    return {}


def _ids_por_bytes(v):
    return {Path(x['arq']).read_bytes(): x['id'] for x in v['acervo'] if x.get('arq')}


def chamadores(v, registro):
    por_bytes = _ids_por_bytes(v)
    cat_ant = {CAT_ANT['ordem_das_imagens'][int(a['i'])]: a for a in json.loads(CAT_ANT['catalogo']['texto'])['imagens']}

    def resp_casar(texto, ordem_ant, imgs):
        ids = [por_bytes[b] for b in imgs]
        out = []
        for a in json.loads(texto)['avaliacoes']:
            pid = next(p for p, k in FIX_POR_PILOTO.items() if k == ordem_ant[int(a['imagem'])])
            if pid in ids and DEV_PARA_PILOTO.get(a['acontecimento']):
                out.append({**a, 'acontecimento': DEV_PARA_PILOTO[a['acontecimento']], 'imagem': ids.index(pid)})
        return json.dumps({'avaliacoes': out})

    def gemini(prompt, imgs):
        registro.append(('gemini', len(imgs)))
        if prompt.startswith('CAT'):
            ids = [por_bytes[b] for b in imgs]
            return json.dumps({'imagens': [{**cat_ant[FIX_POR_PILOTO[i]], 'i': k} for k, i in enumerate(ids) if FIX_POR_PILOTO.get(i) in cat_ant]})
        return resp_casar(GEM['texto'], GEM['ordem_das_imagens'], imgs)

    def nvidia(prompt, imgs):
        registro.append(('nvidia', len(imgs)))
        return resp_casar(NV_TXT, NV['ordem_das_imagens'], imgs)
    return {'gemini': gemini, 'nvidia': nvidia}


PROMPTS = ('CAT {n}', 'CAS {n} {primeiro} {acontecimentos}')


@pytest.fixture(scope='module')
def rodada():
    v = _piloto.roteiro()
    antes = json.dumps(v, sort_keys=True, default=str)
    chamadas = []
    rel = P.executar_sombra(v, v['acervo'], chamadores=chamadores(v, chamadas), get=get_falso, prompts=PROMPTS)
    return v, antes, rel, chamadas


def _ev(rel, eid):
    return next(e for e in rel['eventos'] if e['id'] == eid)


def test_metadados_reais_e_referencias_ligados(rodada):
    _, _, rel, _ = rodada
    assert rel['registros']['real_commons'] >= 5 and rel['referencias']['resumo']['wikidata'] >= 1


def test_imagem_autentica_vira_prova_com_dupla_leitura(rodada):
    _, _, rel, chamadas = rodada
    e4 = _ev(rel, 'e4')['novo']                                   # "ficou de través": a6 (navio preso, 24–25/03/2021)
    assert e4['modo'] == 'foto_prova' and e4['foto'] == 'a6'
    assert e4['evidencia']['fonte'] == 'Commons' and e4['evidencia']['familias'] == ['registro', 'visao']
    assert any(p == 'nvidia' for p, _ in chamadas)                # a dupla leitura aconteceu
    assert rel['visao']['dupla']


def test_contexto_e_outro_navio_nao_viram_prova(rodada):
    _, _, rel, _ = rodada
    e2 = _ev(rel, 'e2')['novo']                                   # navegar: a10 é o homônimo de 2011
    assert e2['modo'] != 'foto_prova'
    assert all(c['nivel'] != 'PROVA' for c in e2['candidatos'] if c['imagem'] in ('a10', 'a12', 'a1'))


def test_estado_resultante_nao_representa_a_liberacao(rodada):
    _, _, rel, _ = rodada
    assert _ev(rel, 'e9')['novo']['modo'] != 'foto_prova'          # "voltou a flutuar": nenhuma imagem do navio solto


def test_discordancia_registrada_e_sem_aprovacao(rodada):
    _, _, rel, _ = rodada
    for d in rel['visao']['discordancias']:
        e, img = d['par']
        cand = next((c for c in _ev(rel, e)['novo']['candidatos'] if c['imagem'] == img), None)
        assert cand is None or cand['nivel'] != 'PROVA'


def test_privacidade_imagem_sem_catalogo_nunca_vai_para_nvidia(rodada):
    _, _, rel, _ = rodada
    retidas = rel['visao']['retidas_nvidia']
    assert retidas and all('catálogo' in m or 'pessoa' in m or 'texto' in m for m in retidas.values())


def test_sombra_nao_altera_roteiro_nem_decisoes_v23(rodada):
    v, antes, rel, _ = rodada
    assert json.dumps(v, sort_keys=True, default=str) == antes
    from src.v2 import preparo
    vv = _piloto.roteiro()
    r1 = preparo.preparar(copy.deepcopy(vv))
    assert [(e['id'], e['representacao']['modo']) for e in r1['eventos']] == [(e['id'], e['antigo']['modo']) for e in rel['eventos']]


def test_catalogo_falhou_nada_vai_para_nvidia():
    v = _piloto.roteiro()
    enviados = []

    def gem(prompt, imgs):
        raise RuntimeError('503 UNAVAILABLE')

    def nv(prompt, imgs):
        enviados.append(len(imgs)); return '{"avaliacoes": []}'
    rel = P.executar_sombra(v, v['acervo'], chamadores={'gemini': gem, 'nvidia': nv}, get=get_falso, prompts=PROMPTS)
    assert enviados == [] and 'catálogo indisponível' in rel['visao']['catalogo']
    assert all(e['novo']['modo'] != 'foto_prova' for e in rel['eventos'])


def test_json_invalido_nao_troca_de_provedor():
    orc = P.Orcamento(4)
    r = P.ler('p', [b'x'], orc, chamadores={'gemini': lambda *_: 'isto não é json', 'nvidia': lambda *_: '{}'})
    assert r.get('incerta') and orc.usadas == 1
