"""Formatos ATLAS/DOSSIÊ: validação determinística, âncoras na fala, tokens por canal, preflight e regressões negativas
históricas (Panamá e anteriores) — tudo sem IA e sem rede."""
import copy
import json
import subprocess
from pathlib import Path

import pytest

from src.v4.formatos import diretor, plano as P, produzir

RAIZ = Path(__file__).resolve().parents[1]
ATLAS_BRUTO = json.loads((RAIZ / 'src/v4/formatos/planos/atlas_panama.json').read_text())
# o ATLAS ancora tudo na fala (narração cifrada): os testes usam o plano RESOLVIDO (só números), mantido em sincronia
ATLAS = json.loads((RAIZ / 'tests/dados/formatos_atlas_resolvido.json').read_text())
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
    """a marcação cai EXATAMENTE no trecho citado da imagem (região em frações da foto, mesma geometria do DocumentCard)"""
    imgs = {a: {'src': 'x', 'w': 1920, 'h': 1429} for a in produzir.assets_do_plano(DOSSIE)}
    pl = P.resolver_tempos(DOSSIE, _pal(DOSSIE['narracao']['texto']))
    pl['duracao'] = 30
    pr = P.props(pl, {}, None, imgs)
    ev = next(L for L in pr['camadas'] if L['id'] == 'acao-1880')
    doc = next(L for L in pr['camadas'] if L['id'] == 'acao')
    f = P.geom_documento(doc, imgs[doc['p']['asset']])['foto']
    x0, y0, x1, y1 = ev['p']['regiao']
    assert abs(ev['caixa']['x'] - (f['x'] + x0 * f['w'])) < 1 and abs(ev['caixa']['y'] - (f['y'] + y0 * f['h'])) < 1
    assert abs(ev['caixa']['w'] - (x1 - x0) * f['w']) < 1


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


def test_workflow_passa_o_segredo_que_decifra_a_narracao():
    """44083616015: CHECKPOINT_KEY não existe no repositório; a chave deriva do COFRE_TOKEN — sem ele, nada decifra"""
    import yaml
    wf = yaml.safe_load((RAIZ / '.github/workflows/formatos-piloto.yml').read_text())
    passo = next(s for s in wf['jobs']['formatos']['steps'] if 'narrar' in str(s.get('run', '')))
    assert 'COFRE_TOKEN' in passo['env'] and 'GEMINI_API_KEY' in passo['env']
    assert set(wf[True if True in wf else 'on'].keys()) <= {'push', 'workflow_dispatch'}


def _bytes_jpg(cor):
    import io

    from PIL import Image
    b = io.BytesIO()
    Image.new('RGB', (1920, 1440), cor).save(b, 'JPEG')
    return b.getvalue()


def test_midia_de_um_episodio_nao_sobrescreve_a_do_outro(tmp_path, monkeypatch):
    """44084129999: ATLAS e DOSSIÊ gravavam f0/f1 na mesma pasta; o DOSSIÊ sobrescreveu e o gancho do ATLAS saiu com a
    foto de 1913 e o crédito da foto de Miraflores. Agora: nome próprio por mídia + impressão digital no preflight."""
    from PIL import Image
    from src.v4 import viabilidade
    pub = tmp_path / 'public' / '_formato'
    monkeypatch.setattr(produzir, 'PUBLICO', pub)
    bib = viabilidade.carregar()
    monkeypatch.setattr(viabilidade, 'carregar', lambda: {**bib, 'itens': [{k: v for k, v in it.items() if k != 'sha256_origem'} for it in bib['itens']]})
    cor = {}
    monkeypatch.setattr(produzir, '_origem', lambda it, cache: (_bytes_jpg(cor.setdefault(it['url'], (len(cor) * 40 % 255, 40, 200))), 'teste'))
    a = produzir.ativos(ATLAS, tmp_path / 'atlas')
    d = produzir.ativos(DOSSIE, tmp_path / 'dossie')
    midia = {k: v for k, v in {**a, **d}.items() if not k.startswith('raster:')}
    assert len({v['src'] for v in midia.values()}) == len(midia)                        # um arquivo por mídia
    for ativo, reg in a.items():
        assert produzir._sha(pub.parent / reg['src']) == reg['sha256']                 # o do ATLAS continua intacto
    # arquivo trocado por baixo → o preflight pega (impressão digital)
    alvo = next(v for k, v in a.items() if not k.startswith('raster:'))
    Image.new('RGB', (1920, 1440), (1, 2, 3)).save(pub.parent / alvo['src'])
    (tmp_path / 'atlas' / 'narracao.json').write_text(json.dumps({'palavras': _pal('x ' * 300), 'duracao': 80.0}))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', '1', str(tmp_path / 'atlas' / 'voz.wav')], check=True)
    r = produzir.preflight(ATLAS, tmp_path / 'atlas', palco_real=False)
    assert not r['pronto'] and any(i['item'].startswith('arquivo é a mídia certa') and not i['ok'] for i in r['itens'])


def test_arquivo_da_origem_diferente_do_registrado_nao_entra(tmp_path, monkeypatch):
    """integridade: a biblioteca guarda o sha256 DA ORIGEM; se a URL passar a servir outro arquivo, a mídia é recusada"""
    monkeypatch.setattr(produzir, 'PUBLICO', tmp_path / 'pub')
    monkeypatch.setattr(produzir, '_origem', lambda it, cache: (_bytes_jpg((9, 9, 9)), 'teste'))
    with pytest.raises(RuntimeError, match='origem mudou'):
        produzir.ativos(DOSSIE, tmp_path / 'd')


def test_raster_do_palco_tem_procedencia_licenca_e_resolucao():
    """mapa rico: só raster com .json (fonte, licença, atribuição, sha256); Sentinel-2 só a edição 2016 (CC BY 4.0)"""
    for r in ATLAS['rasters']:
        m = P.raster_info(r['nome'])
        arq = P.RASTER_DIR / m['arquivo']
        assert arq.exists() and produzir._sha(arq) == m['sha256'] and m['atribuicao']
        lic = json.dumps(m.get('fonte'), ensure_ascii=False)
        assert 'Domínio público' in lic or 'CC BY 4.0' in lic
        if 'Sentinel' in m['atribuicao']:
            assert '2016' in m['atribuicao'] and 'NC' not in lic


def test_mapa_sem_raster_nitido_e_camada_sobre_o_territorio_sao_erro():
    """direção de arte: mapa de baixa qualidade e esquema cobrindo a rota/território são recusados ANTES do render"""
    pl = copy.deepcopy(ATLAS)
    b = next(b for b in pl['beats'] if b['id'] == 'b2-rota')
    b['zoom_max'] = None
    b['roi'] = [-79.62, 8.99, -79.58, 9.02]          # zoom ~13 só com o raster do canal (nítido até 11)
    pl['rasters'] = [r for r in pl['rasters'] if r['nome'] != 's2_miraflores_eclusas']
    assert 'F-MAPA-BAIXA-RESOLUCAO' in _regras(pl)
    pl = copy.deepcopy(ATLAS)
    perfil = next(L for b in pl['beats'] for L in b['camadas'] if L['id'] == 'perfil')
    perfil['caixa'] = [60, 360, 960, 360]             # o perfil em cima do canal (era o erro da 44084129999)
    assert 'F-COBRE-TERRITORIO' in _regras(pl)


def test_reconstrucao_editorial_sempre_rotulada():
    pl = copy.deepcopy(DOSSIE)
    next(L for b in pl['beats'] for L in b['camadas'] if L['id'] == 'cal1913')['p']['reconstrucao'] = ''
    assert 'F-RECONSTRUCAO' in _regras(pl, _pal(pl['narracao']['texto']))


def test_fixture_do_atlas_em_sincronia_com_o_plano():
    ids = lambda pl: [(b['id'], [L['id'] for L in b['camadas']]) for b in pl['beats']]
    assert ids(ATLAS) == ids(ATLAS_BRUTO) and ATLAS['rasters'] == ATLAS_BRUTO['rasters']


def test_mosaico_com_tile_ausente_falha_em_vez_de_virar_satelite_preto(monkeypatch):
    """coleta 44097219552: camada Sentinel-2 com identificador errado → 404 em todos os tiles → mosaico PRETO salvo calado"""
    import sys
    sys.path.insert(0, str(RAIZ / 'scripts'))
    import formatos_raster as R
    monkeypatch.setattr(R, 'baixar', lambda url, tent=4: None)
    with pytest.raises(RuntimeError, match='tiles ausentes'):
        R.mosaico(R.S2, (-79.7, 9.0, -79.6, 9.1), 11, 'RGB')
    assert 's2cloudless_3857' in R.S2          # a edição 2016 (CC BY 4.0), nunca as NC


def test_ritmo_medido_acha_trecho_parado():
    """ERR-067 comprovado no MP4: a métrica das referências (mudança por segundo na zona de conteúdo) acha 4 s parados"""
    from src.v4.formatos import ritmo
    r = ritmo.resumo([3, 2, .1, .2, .1, .3, 4])
    assert r['maior_trecho_parado_s'] == 4 and r['segundos_parados'] == 4


def test_download_de_midia_espera_o_limite_do_commons(monkeypatch):
    """44110855696: 429 do upload.wikimedia.org derrubou o passo de mídia antes do preflight"""
    import requests
    import time
    seq = iter([429, 429, 200])

    class R:
        def __init__(s, c): s.status_code, s.headers, s.content = c, {'Retry-After': '0'}, b'ok'
        def raise_for_status(s):
            if s.status_code >= 400:
                raise requests.HTTPError(str(s.status_code))
    monkeypatch.setattr(requests, 'get', lambda *a, **k: R(next(seq)))
    monkeypatch.setattr(time, 'sleep', lambda s: None)
    assert produzir._origem({'url': 'https://upload.wikimedia.org/x.jpg'}, None) == (b'ok', 'https://upload.wikimedia.org/x.jpg')


def test_mesa_estatica_e_medicao_com_caminho_absoluto():
    """44114805861: QUADROS com caminho relativo (node em outra pasta) e mesa com feTurbulence por quadro (30 min estourados)"""
    palco = (RAIZ / 'motor4/remotion/src/formatos/Palco.tsx').read_text()
    assert 'feTurbulence' not in palco and 'mesa_madeira.jpg' in palco and (RAIZ / 'motor4/remotion/public/formatos/mesa_madeira.jpg').exists()
    assert 'pf.resolve()' in (RAIZ / 'scripts/formatos_validar.py').read_text()
