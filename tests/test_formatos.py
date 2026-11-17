"""Formatos ATLAS/DOSSIÊ: validação determinística, âncoras na fala, tokens por canal, preflight e regressões negativas
históricas (Panamá e anteriores) — tudo sem IA e sem rede."""
import copy
import json
import subprocess
from pathlib import Path

import pytest

from src.v4.formatos import diretor, plano as P, produzir

RAIZ = Path(__file__).resolve().parents[1]
ATLAS = json.loads((RAIZ / 'src/v4/formatos/planos/atlas_panama.json').read_text())
DOSSIE = json.loads((RAIZ / 'src/v4/formatos/planos/dossie_panama_demo.json').read_text())


def _pal(texto, ritmo=2.4):
    import re
    ws = re.findall(r'[\wÀ-ÿº]+', texto)
    return [{'w': w.upper(), 's': round(.1 + i / ritmo, 3), 'e': round(.1 + (i + 1) / ritmo, 3), 'hl': False} for i, w in enumerate(ws)]


def _regras(pl, palavras=()):
    r = P.resolver_tempos(pl, list(palavras))
    if isinstance(r.get('duracao'), str):
        r['duracao'] = palavras[-1]['e'] + .6
    return {v['regra'] for v in P.validar(r) if v['gravidade'] == 'erro'}


def test_planos_aprovados_passam_na_validacao():
    assert _regras(ATLAS) == set()
    assert _regras(DOSSIE, _pal(DOSSIE['narracao']['texto'])) == set()


def test_ancoras_seguem_a_palavra_da_fala():
    pal = _pal('o navio entra e depois o navio sai')
    assert P.ancora('@navio', pal) == pal[1]['s'] and P.ancora('@2:navio+0.5', pal) == round(pal[6]['s'] + .5, 3)
    assert P.ancora('@fim', pal) == round(pal[-1]['e'] + .6, 3)
    with pytest.raises(ValueError):
        P.ancora('@inexistente', pal)


# ---------------- regressões NEGATIVAS (falhas que já aconteceram) ----------------

def _camada(pl, cid):
    return next(L for b in pl['beats'] for L in b['camadas'] if L['id'] == cid)


def test_legenda_titulo_e_cartao_no_mesmo_lugar_e_colisao():
    """"títulos e legendas colididos" (44049021691 e anteriores): duas camadas no mesmo slot ao mesmo tempo"""
    pl = copy.deepcopy(ATLAS)
    _camada(pl, 'mar')['t0'] = 62.0                    # sobrepõe a pílula 'doce' na base
    assert 'F-COLISAO' in _regras(pl)


def test_mesma_midia_duas_vezes_no_mesmo_plano():
    """c4 (43972774128): a mesma foto em cima e embaixo"""
    pl = copy.deepcopy(ATLAS)
    b = pl['beats'][0]
    b['camadas'].append({**copy.deepcopy(b['camadas'][0]), 'id': 'dup', 'slot': 'base'})
    assert 'F-MIDIA-DUPLICADA' in _regras(pl)


def test_foto_ou_texto_parado_sem_informacao_nova():
    """foto longa sem informação nova (c4/c9 de 43972774128); cena estática mascarada pela legenda"""
    pl = copy.deepcopy(ATLAS)
    pl['beats'] = [b for b in pl['beats'] if b['id'] != 'b6-gravidade']   # 41–50 s só com o palco técnico
    assert 'F-SEM-PROGRESSAO' in _regras(pl)


def test_mapa_que_promete_rota_sem_geometria():
    pl = copy.deepcopy(ATLAS)
    pl.pop('geo')
    assert 'F-ROTA-SEM-GEOMETRIA' in _regras(pl)


def test_excesso_de_modalidades_vira_erro():
    """vitrine de ferramentas (43972774128: nove famílias por cota)"""
    pl = copy.deepcopy(ATLAS)
    extra = ['editorial.timeline', 'editorial.peopleCard', 'editorial.comparison', 'dossie.evidenceHighlight']
    for k, c in enumerate(extra):
        pl['beats'][-1]['camadas'].append({'id': f'x{k}', 'componente': c, 'slot': 'direita', 't0': 1 + k * 0.01, 't1': 1.5 + k * 0.01, 'p': {}})
    assert 'F-EXCESSO-MODALIDADES' in _regras(pl)


def test_mesma_midia_tres_vezes_no_episodio():
    """a mesma eclusa/mídia repetida três vezes (44049021691)"""
    pl = copy.deepcopy(ATLAS)
    foto = _camada(pl, 'foto-gancho')
    for k, t in enumerate((24.0, 60.0)):
        pl['beats'][-1]['camadas'].append({**copy.deepcopy(foto), 'id': f'rep{k}', 't0': t, 't1': t + 1, 'slot': 'direita'})
    assert 'F-MIDIA-REPETIDA' in _regras(pl)


def test_texto_que_nao_cabe_e_componente_fora_do_formato():
    pl = copy.deepcopy(ATLAS)
    _camada(pl, 'payoff')['p']['linhas'][0]['tamanho'] = 120
    _camada(pl, 'km')['componente'] = 'tresd.camara'
    r = _regras(pl)
    assert 'F-TEXTO-NAO-CABE' in r and 'F-COMPONENTE' in r


def test_preflight_sem_narracao_ou_sem_midia_nao_deixa_renderizar(tmp_path):
    """3 vídeos exigidos sem prova de existência / placas de diagnóstico (44049021691): nada é renderizado sem 100%"""
    r = produzir.preflight(ATLAS, tmp_path, palco_real=False)
    assert not r['pronto'] and r['itens'][0]['item'] == 'narração'
    (tmp_path / 'narracao.json').write_text(json.dumps({'palavras': _pal('x ' * 200), 'duracao': 80.0}))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', '1', str(tmp_path / 'voz.wav')], check=True)
    r = produzir.preflight(ATLAS, tmp_path, palco_real=False)
    falhas = [i['item'] for i in r['itens'] if not i['ok']]
    assert not r['pronto'] and any(f.startswith('arquivo de mídia') for f in falhas)          # mídia não baixada = não renderiza
    with pytest.raises(SystemExit):
        produzir.render(tmp_path)


def test_toda_midia_dos_planos_e_comprovada_e_creditada():
    from src.v4 import viabilidade
    bib = {it['id']: it for it in viabilidade.carregar()['itens']}
    for pl in (ATLAS, DOSSIE):
        for a in produzir.assets_do_plano(pl):
            assert a in bib and bib[a]['prova']['midia_corresponde'] is True
            meta = ' '.join(m for b in pl['beats'] for L in b['camadas'] if (L.get('p') or {}).get('asset') == a for m in L['p'].get('meta') or [])
            assert any(x in meta.upper() for x in ('CC BY', 'DOMÍNIO PÚBLICO')), a


def test_geometria_versionada_tem_rota_medida_e_atribuicao():
    g = json.loads((RAIZ / 'motor4/formatos/dados/panama.topo.json').read_text())
    assert 'rota' in g['topo']['objects'] and 80 < g['meta']['rota_km'] < 90
    assert any('OpenStreetMap' in a for a in g['meta']['atribuicao']) and any('Natural Earth' in a for a in g['meta']['atribuicao'])


def test_evidencia_mira_a_parte_certa_do_documento():
    imgs = {a: {'src': 'x', 'w': 1920, 'h': 1519} for a in produzir.assets_do_plano(DOSSIE)}
    pl = P.resolver_tempos(DOSSIE, _pal(DOSSIE['narracao']['texto']))
    pl['duracao'] = 30
    pr = P.props(pl, {}, None, imgs)
    ev = next(L for L in pr['camadas'] if L['id'] == 'data1913')
    doc = next(L for L in pr['camadas'] if L['id'] == 'doc1913')
    g = P.geom_documento(doc, imgs[doc['p']['asset']])
    assert ev['caixa']['x'] > g['foto']['x'] + g['foto']['w'] / 2 and ev['caixa']['y'] < g['foto']['y']   # canto do cabeçalho (data)


def test_tokens_por_canal_sem_fork(tmp_path, monkeypatch):
    """outro canal = outro arquivo de configuração; mesma engine"""
    can = P.canal('coringa')
    assert can['cores']['destaque'] == '#FFD21F' and can['cores']['fundo'] == '#05080F'
    outro = dict(can, canal='teste', cores=dict(can['cores'], destaque='#00FF88'))
    pasta = Path(P.__file__).parent / 'canais'
    arq = pasta / 'teste_tmp.json'
    arq.write_text(json.dumps(outro))
    try:
        assert P.canal('teste_tmp')['cores']['destaque'] == '#00FF88'
    finally:
        arq.unlink()


def test_diretor_de_formato_preenche_e_corrige_uma_vez_sem_cota():
    """o diretor só preenche primitivas aprovadas; erro volta como correção dirigida UMA vez (modelo falso)"""
    ruim = copy.deepcopy(ATLAS)
    _camada(ruim, 'mar')['t0'] = 62.0
    respostas = iter([json.dumps(ruim), json.dumps(ATLAS)])
    prompts = []
    pl, viol = diretor.pedir([{'id': 'f1', 'texto': 'x'}], 'atlas', None, '- foto: x', lambda p: prompts.append(p) or next(respostas))
    assert viol == [] and len(prompts) == 2 and 'F-COLISAO' in prompts[1]
    assert 'NÃO invente estilo' in prompts[0] and 'editorial.statCard' in prompts[0] and 'tresd.camara' not in prompts[0]


def test_componentes_registrados_no_remotion():
    src = (RAIZ / 'motor4/remotion/src/formatos/Primitivas.tsx').read_text()
    usados = {c for f in P.CFG['formatos'].values() for c in f['componentes']}
    assert all(f"'{c}'" in src for c in usados)


def test_camada_na_zona_da_marca_ou_da_legenda_e_erro():
    """17/11 (ensaio DOSSIÊ): datas da linha do tempo encostavam na marca 'CORINGA EXPLICA' (y 292)"""
    pl = copy.deepcopy(ATLAS)
    _camada(pl, 'km')['caixa'] = [72, 300, 936, 80]
    _camada(pl, 'zero')['caixa'] = [72, 1250, 936, 80]
    r = P.validar(P.resolver_tempos(pl, []))
    assert sum(v['regra'] == 'F-ZONA-IDENTIDADE' for v in r) == 2
    for x, y, w, h in P.SLOTS.values():
        for zx, zy, zw, zh in P.CFG['zonas_identidade'].values():
            assert not (x < zx + zw and zx < x + w and y < zy + zh and zy < y + h), 'slot padrão dentro de zona da identidade'
