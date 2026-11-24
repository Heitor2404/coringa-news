"""E202: diretor visual autônomo — formas, compilador declarativo, verificação e cache (sem IA, sem render)."""
import json
import re
from pathlib import Path

import pytest

from src.v4.formatos import cena_declarativa_e202 as CD
from src.v4.formatos import diretor_visual_e202 as D
from src.v4.formatos import formas_e202 as F

FX = json.loads(Path('tests/dados/e202_cena_sintetica.json').read_text(encoding='utf8'))
DISP = {k: {'disponivel': k == 'cena_declarativa', 'motivo': 'teste'} for k in D.MODALIDADES}


def _copia():
    return json.loads(json.dumps(FX['plano']))


def test_formas_tem_origem_e_licenca():
    r = F.icone(['potted-plant'])
    assert r['origem'] == 'icone:fluent-emoji-flat/potted-plant' and r['licenca'] == 'MIT' and r['credito']
    assert F.icone(['termo-que-nao-existe-xyz']) is None
    g = F.geo('Brazil')
    assert g['natureza'] == 'dado_real' and g['licenca'] == 'domínio público' and g['view'][2] > 0
    assert F.geo('Pais Inventado') is None
    for p in F.PRIMITIVAS:
        assert F.primitiva(p, '#123456')['origem'] == f'primitiva:{p}'
    assert F.svg_ia('M0 0 L500 500 Z') is None          # fora da caixa
    assert F.svg_ia('M10 10 L90 10 L50 90 Z')['natureza'] == 'desenho_gerado_ia'
    r, motivo = F.resolver({'tipo': 'icone', 'termos_en': ['nada-xyz']})
    assert r is None and motivo.startswith('ICONE-NAO-ENCONTRADO')


def test_compila_fixture_sem_problemas_e_contrato_v2():
    probs, comp = D.verificar(FX['plano'], FX['caso'], DISP)
    # fixture lotada (6 atores) no plano geral final: alerta honesto de sujeito pequeno, nada além disso
    assert probs == [] and {g['regra'] for g in comp['c1']['alertas_geometria']} <= {'G-SUJEITO-PEQUENO'}
    sg = comp['c1']['scene_graph']
    assert sg['schema'] == 'coringa.scene_graph.private.v2' and sg['publish'] is False
    dur = comp['c1']['duracao']
    for a in sg['actors']:
        ts = [s['t'] for s in a['states']]
        assert ts[0] == 0 and all(b > x for x, b in zip(ts, ts[1:])) and ts[-1] <= round(dur, 4) + 1e-9
        assert len(a['states']) <= 600 and a['origem']
    assert sg['captions_origin'] == 'ESTIMADA_SEM_AUDIO'     # sem voz: marcado como estimativa
    assert [c['t'] for c in sg['camera']] == sorted({c['t'] for c in sg['camera']})
    prov = comp['c1']['proveniencia']
    assert prov['atores']['planta']['origem'].startswith('icone:')


def test_acoes_mudam_estado_visivel():
    _, comp = D.verificar(FX['plano'], FX['caso'], DISP)
    sg = comp['c1']['scene_graph']
    planta = next(a for a in sg['actors'] if a['id'] == 'planta')
    assert planta['states'][0]['sat'] < .3 and planta['states'][-1]['sat'] == 1          # tingir
    esq = next(a for a in sg['actors'] if a['id'] == 'esq')
    dirr = next(a for a in sg['actors'] if a['id'] == 'dir')
    d0 = dirr['states'][0]['x'] - esq['states'][0]['x']
    d1 = dirr['states'][-1]['x'] - esq['states'][-1]['x']
    assert d1 > d0 + 50                                                                 # afastar
    retidos = [a for a in sg['actors'] if re.fullmatch(r'filtrar\d+r\d+', a['id']) and a['layer'] == 'particula']
    assert retidos and all(a['states'][-1]['opacity'] > .9 for a in retidos)           # retido fica no filtro


@pytest.mark.parametrize('mut,regra', [
    (lambda p: p['cenas'][0]['beats'][0]['acoes'].append({'verbo': 'teleportar'}), 'C-VERBO'),
    (lambda p: p['cenas'][0]['beats'][0].__setitem__('fala', 'A planta bebe 37 litros por dia sem parar nunca.'), 'C-NUMERO'),
    (lambda p: p['cenas'][0]['beats'][1].__setitem__('fatos', ['z9']), 'C-FATO'),
    (lambda p: p['cenas'][0]['beats'][1].__setitem__('acoes', []), 'C-SEM-ACAO'),
    (lambda p: p['cenas'][0]['beats'][1].__setitem__('acoes', [{'verbo': 'destacar', 'alvo': 'filtro'}]), 'C-ACAO-FRACA'),
    (lambda p: p['cenas'][0]['atores'][1].__setitem__('forma', {'tipo': 'icone', 'termos_en': ['nada-xyz']}), 'C-FORMA'),
    (lambda p: p['cenas'][0].__setitem__('modalidade', 'mapa_atlas'), 'P-MODALIDADE-INDISPONIVEL'),
])
def test_verificacao_recusa_plano_ruim(mut, regra):
    p = _copia()
    mut(p)
    probs, _ = D.verificar(p, FX['caso'], DISP)
    assert regra in {x['regra'] for x in probs}


def test_geometria_detecta_sujeito_pequeno():
    _, comp = D.verificar(FX['plano'], FX['caso'], DISP)
    sg = json.loads(json.dumps(comp['c1']['scene_graph']))
    for c in sg['camera']:
        c['zoom'] = .2
    assert 'G-SUJEITO-PEQUENO' in {x['regra'] for x in D.geometria(sg)}


def test_cache_e_bloqueio_sem_chamada(tmp_path):
    reg = []
    (tmp_path / (D._sha('pedido') + '.json')).write_text(json.dumps({'provedor': 'teste', 'json': {'ok': 1}}))
    assert D.pedir_ia('pedido', reg, tmp_path, permitir_chamada=False) == {'ok': 1}
    assert reg[0]['origem'] == 'cache' and reg[0]['chamada_nova'] is False
    with pytest.raises(RuntimeError, match='E202-SEM-CACHE'):
        D.pedir_ia('outro pedido', reg, tmp_path, permitir_chamada=False)


def test_legenda_usa_palavras_medidas():
    pal = [{'w': w, 's': i * .4, 'e': i * .4 + .35} for i, w in enumerate('A planta parece parada.'.split())]
    cena = FX['plano']['cenas'][0]
    r = CD.compilar(cena, D.estimar_duracoes(cena), FX['caso']['fatos'], pal, 'x')
    assert r['scene_graph']['captions_origin'] == 'palavras_medidas_da_narracao'
    assert r['scene_graph']['captions'][0]['words'][0]['w'] == 'A'


def test_prompt_inclui_fatos_limites_e_disponibilidade():
    txt = D.prompt(FX['caso'], DISP)
    assert 't1: Raízes absorvem' in txt and 'Fixture sintética' in txt and 'mapa_atlas: INDISPONÍVEL' in txt
    assert 'potted-plant' in txt                  # catálogo real de ícones, não lista inventada


def test_sem_ramos_por_tema_no_codigo():
    proibidos = re.compile(r'flamingo|isl[aâ]ndia|iceland|caf[eé]|cafe[ií]na|caffeine|plate|placa_|tect', re.I)
    for nome in ('formas_e202.py', 'cena_declarativa_e202.py', 'diretor_visual_e202.py', 'ciclo_e202.py'):
        txt = Path('src/v4/formatos', nome).read_text(encoding='utf8')
        assert not proibidos.search(txt), nome


def test_rubrica_comum_reconhece_cena_declarativa():
    f = D.filme({'plano': FX['plano']}, FX['caso'])
    r = D.auditoria_contrato(f['props'])
    assert r['estrutura_declarada_ok'] and r['provas_resolvidas_no_plano'] == 1
    assert r['prova_visual'] == 'NAO_INSPECIONADA' and r['aprovacao_humana'] == 'PENDENTE'


def test_tingir_para_cor_e_caixa_justa():
    p = _copia()
    p['cenas'][0]['beats'][0]['acoes'].append({'verbo': 'tingir', 'alvo': 'copo', 'para_cor': '#6B3F1D', 'inicio': 0.2, 'fim': 0.9})
    _, comp = D.verificar(p, FX['caso'], DISP)
    copo = next(a for a in comp['c1']['scene_graph']['actors'] if a['id'] == 'copo')
    assert copo['tint_color'] == '#6B3F1D' and copo['states'][0]['tint'] == 0 and copo['states'][-1]['tint'] > .7
    v = F.icone(['potted-plant'])['view']
    assert v[0] > 0 and v[2] < 32                       # moldura do ícone sem o respiro lateral
