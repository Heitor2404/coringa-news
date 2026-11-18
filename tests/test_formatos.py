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
    foto = _camada(pl, 'pino-mira')
    for k, t in enumerate((24.0, 62.0)):
        pl['beats'][-1]['camadas'].append({**copy.deepcopy(foto), 'id': f'rep{k}', 't0': t, 't1': t + 1})
    assert 'F-MIDIA-REPETIDA' in _regras(pl)


def test_texto_que_nao_cabe_e_componente_fora_do_formato():
    pl = copy.deepcopy(ATLAS)
    _camada(pl, 'payoff')['p']['linhas'][0]['texto'] = 'UM LAGO NO ALTO DA MONTANHA'      # corpo vem do token do slot
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
            meta = ' '.join(m for b in pl['beats'] for L in b['camadas'] if (L.get('p') or {}).get('asset') == a
                            for m in ([L['p']['meta']] if isinstance(L['p'].get('meta'), str) else L['p'].get('meta') or []))
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
    _camada(pl, 'km')['caixa'] = [72, 300, 936, 28]          # zona da marca ATLAS: y 294–338, dentro do feed Reels
    _camada(pl, 'zero')['caixa'] = [72, 1250, 936, 80]
    r = P.validar(P.resolver_tempos(pl, []))
    assert sum(v['regra'] == 'F-ZONA-IDENTIDADE' for v in r) == 1  # ATLAS sem marca sobreposta; legenda continua protegida
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
    pl['rasters'] = []                                 # sem base: antes a checagem era PULADA e saía mapa vetorial chapado
    assert 'F-MAPA-SEM-BASE' in _regras(pl)
    pl = copy.deepcopy(ATLAS)
    b = next(b for b in pl['beats'] if b['id'] == 'b2-rota')
    b['roi'] = [-79.62, 8.99, -79.58, 9.02]          # território minúsculo: a câmera PARA na nitidez da base, não amplia além
    pl['rasters'] = [r for r in pl['rasters'] if r['nome'] != 's2_miraflores_eclusas']
    r = P.resolver_tempos(pl, [])
    k = next(k for k in r['palco'] if k.get('roi') == b['roi'])
    assert k['camera']['zoom'] <= P.teto_zoom(r, b['roi']) + 1e-6
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


# ---------------------------------------------------------------- gramática da referência ATLAS (atlas_parametros.json)
def test_atlas_parametros_validos_e_integrados():
    """o JSON entregue pelo Heitor está no repositório, válido, e o motor usa: porte 512×910 → 1080×1920 e câmera medida"""
    from src.v4.formatos import atlas_ref as A
    assert A.PAR['measured_original']['width_px'] == 512 and A.PAR['reference_filename'].startswith('insta_post_')
    assert A.porta(A.PAR['pixel_regions_512x910_estimates']['hierarchy_25s']) == [57, 268, 987, 274]
    assert A.legenda_centro_ref() == 1496
    # a conferência própria bate com a tabela do relatório (±1,5 % de escala) e os presets saem dela
    for nosso, deles in zip(A.CAM['conferencia_relatorio'], A.PAR['measured_camera_affine_sift']):
        assert abs(nosso['escala'] - deles['scale']) < .015
    assert 0.02 < A.DERIVA['aproxima'] < 0.06 and A.DERIVA['fixo'] == 0 and A.DERIVA['recua'] < -0.03


def test_camera_aproxima_fica_parada_no_dado_e_recua_no_fecho():
    import math
    pl = P.resolver_tempos(ATLAS, [])
    ks = {k['composicao']: k for k in pl['palco']}
    assert ks['atlas.painel']['deriva'] == 0 and ks['atlas.protagonista']['deriva'] > 0
    fecho = pl['palco'][-1]
    assert fecho['movimento'] == 'recua'
    fim = P.camera_em(pl['palco'], pl['duracao'] - .05)
    roi = next(b for b in pl['beats'] if b['id'] == 'b9-payoff')['roi']
    alvo = P.camera_roi(roi, P.COMP['atlas.manchete']['quadro'], P.teto_zoom(pl, roi), .86, P.COMP['atlas.manchete'].get('centro_intencao'))
    assert math.isclose(fim['zoom'], alvo['zoom'], abs_tol=.02)       # termina no enquadramento do território inteiro


def test_pino_segue_o_territorio_e_fora_dele_e_erro():
    pl = P.resolver_tempos(ATLAS, [])
    pino = next(L for L in P.camadas(pl) if L['id'] == 'p-gatun')
    t = pino['t0'] + .5
    cam = P.camera_em(pl['palco'], t)
    ax, ay = P.projetar(cam, *pino['p']['lonlat'])
    qx, qy, qw, qh = P.COMP['atlas.escada']['quadro']
    assert qx <= ax <= qx + qw and qy <= ay <= qy + qh
    ruim = copy.deepcopy(ATLAS)
    _camada(ruim, 'p-gatun')['p']['lonlat'] = [-75.0, 12.0]          # fora do território enquadrado
    assert 'F-PINO-FORA' in _regras(ruim)


def test_camadas_cartograficas_proibidas_e_creditos_corretos():
    from src.v4.formatos import atlas_ref as A
    assert A.proibido('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}')
    assert A.proibido('https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg')
    assert A.proibido('https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg') is None
    cr = P._creditos(ATLAS)
    assert cr['datasets']['s2_2016'].startswith('EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH')
    assert cr['datasets']['osm_rota'] == '© OpenStreetMap contributors' and 'terrain_tiles' not in cr['datasets']
    # fonte factual ≠ atribuição cartográfica
    fatos = {u for f in ATLAS['narracao'].get('fatos', []) for u in f['fontes']}
    assert fatos and not any(u in ' '.join(cr['datasets'].values()) for u in fatos)


def test_planta_tecnica_rebobina_e_medicao_conta_o_desenho_svg():
    """17/11: o país na planta técnica virou retângulo (anel no sentido errado para o d3-geo) e a medição contava a
    tela inteira do <svg> do fio do pino como "camada" (falso transbordo de 10 000 px)"""
    palco = (RAIZ / 'motor4/remotion/src/formatos/Palco.tsx').read_text()
    assert 'turf.rewind' in palco and 'reverse: true' in palco
    fmt = (RAIZ / 'motor4/remotion/src/formatos/Formato.tsx').read_text()
    assert 'ownerSVGElement' in fmt and 'data-ancora-geo' in fmt


def test_partes_do_mostrador_ancoradas_na_fala():
    """44155276352: '@metade' das partes do mostrador não era resolvido → o meio-círculo nunca enchia (5 s parados)"""
    pal = [{'w': w, 's': i * .5, 'e': i * .5 + .4} for i, w in enumerate('metade sobe metade desce'.split())]
    pl = copy.deepcopy(ATLAS)
    _camada(pl, 'litros')['p']['partes'][0]['t'] = '@metade'
    _camada(pl, 'litros')['p']['partes'][1]['t'] = '@2:metade'
    r = P.resolver_tempos(pl, pal)
    partes = next(L for b in r['beats'] for L in b['camadas'] if L['id'] == 'litros')['p']['partes']
    assert [x['t'] for x in partes] == [0.0, 1.0]


# ---------------- consolidação ATLAS (17/11): legenda × áudio, plataformas, cartões, gancho, CTA, amostragem ----------------

def _wav_fala(tmp_path, trechos, dur):
    """voz sintética: tom nos trechos de fala, silêncio digital entre eles (como o TTS)"""
    import wave

    import numpy as np
    sr = 16000
    x = np.zeros(int(dur * sr), dtype=np.float32)
    for a, b in trechos:
        n = np.arange(int(a * sr), int(b * sr))
        x[n] = .4 * np.sin(2 * np.pi * 220 * n / sr)
    arq = tmp_path / 'voz.wav'
    with wave.open(str(arq), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((x * 32767).astype('<i2').tobytes())
    return arq


def test_legenda_realinhada_pelas_pausas_reais_do_audio(tmp_path):
    """44155276352: palavras marcadas no silêncio ('OCEANOS' depois do fim da fala, 'O CANAL' antes de recomeçar)"""
    from src.v4.formatos import legenda_sync as LS
    wav = _wav_fala(tmp_path, [(0.2, 2.0), (2.8, 4.6)], 5.0)
    # marcas do TTS deslocadas: a 2ª frase "começa" dentro da pausa real (2,0–2,8)
    pal = [{'w': w, 's': s, 'e': e} for w, s, e in [('UM', .2, .6), ('NAVIO', .6, 1.2), ('SOBE', 1.2, 2.3),
                                                    ('O', 2.35, 2.5), ('CANAL', 2.5, 3.4), ('CRUZA', 3.4, 4.0), ('O', 4.0, 4.2), ('ISTMO', 4.2, 4.6)]]
    narr = tmp_path / 'n.json'
    narr.write_text(json.dumps({'palavras': pal}))
    assert not LS.conferir(narr, wav)['ok']
    novo = LS.realinhar(pal, wav)
    narr.write_text(json.dumps({'palavras': novo}))
    r = LS.conferir(narr, wav)
    assert r['ok'], r
    assert novo[3]['s'] >= 2.75 and novo[2]['e'] <= 2.05


def test_legenda_sem_troca_brusca():
    from src.v4.formatos import legenda_sync as LS
    pal = [{'w': 'A', 's': 0, 'e': .5}, {'w': 'CERCA', 's': .8, 'e': .95}, {'w': 'DE', 's': 1.4, 'e': 1.6}, {'w': 'OITO', 's': 1.6, 'e': 2.2}]
    gs = LS.grupos(pal)
    assert all(g['fim'] - g['ini'] >= .35 for g in gs) and ' '.join(g['txt'] for g in gs) == 'A CERCA DE OITO'
    tsx = (RAIZ / 'motor4/remotion/src/Camada.tsx').read_text()
    assert '>= .35' in tsx and '.25' in tsx and '1.6' in tsx           # Camada usa a MESMA regra


def test_faixas_proprias_legenda_creditos_conteudo():
    """créditos cartográficos 'praticamente sobre as legendas' (44155276352): faixas separadas dentro da área segura"""
    from src.v4.formatos import layout
    fi = layout.faixa_inferior()
    cx, cy, cw, ch = fi['creditos']
    lx, ly, lw, lh = fi['legenda']
    assert ly + lh <= cy and fi['conteudo_base'] <= ly
    assert cy + ch <= fi['base_visivel'] and cx >= layout.uniao()['esquerda']
    for nome in layout.CFG['ativos']:
        for mk in layout.mascaras(nome):
            if mk.get('aviso'):
                continue
            x, y, w, h = mk['caixa']
            for bx in (fi['creditos'], fi['legenda']):
                assert not (bx[0] < x + w and x < bx[0] + bx[2] and bx[1] < y + h and y < bx[1] + bx[3]), (nome, mk, bx)


def test_pino_protagonista_cabe_na_area_segura_e_encolhe_se_preciso():
    pl = P.resolver_tempos(copy.deepcopy(ATLAS), [])
    pin = next(L for L in P.camadas(pl) if L['id'] == 'pino-mira')
    assert pin['p']['papel'] == 'protagonista' and pin['p']['raio'] >= .75 * P.papel_pino(pin['p'])['raio']
    assert pin['p']['raio'] > next(L for L in P.camadas(pl) if L['id'] == 'pino-mira-2')['p']['raio']
    assert 'F-PINO-FORA' not in {v['regra'] for v in P.validar(pl)}
    pl2 = copy.deepcopy(ATLAS)
    _camada(pl2, 'pino-mira')['p']['desloc'] = [400, 0]                # foto empurrada para a coluna de ícones
    assert 'F-PINO-FORA' in _regras(pl2)


def test_rotulo_de_pino_troca_de_lado_se_sair_da_area_segura():
    pl = P.resolver_tempos(copy.deepcopy(ATLAS), [])
    m = next(L for L in P.camadas(pl) if L['id'] == 'p-mira')
    assert m['p']['lado'] == 'direita' and m['p']['lado_auto'] != 'direita'


def test_pilula_encolhe_ate_30px_e_so_entao_falha():
    L = {'componente': 'editorial.statCard', 'slot': 'nota', 'caixa': {'x': 173, 'y': 1130, 'w': 734, 'h': 88},
         'p': {'estilo': 'pilula', 'valor': 'ATRAVESSA A DIVISA CONTINENTAL'}}
    assert P._cabe(L) == []
    L['p']['valor'] = 'ATRAVESSA A DIVISA CONTINENTAL DAS AMÉRICAS DO SUL'
    assert P._cabe(L)


def test_gancho_exige_prova_visual_forte_no_inicio():
    pl = copy.deepcopy(ATLAS)
    pl['clipes'] = [c for c in pl['clipes'] if c.get('papel') != 'gancho']
    _camada(pl, 'pino-mira')['p']['papel'] = 'secundario'
    _camada(pl, 'pino-mira')['t0'] = 4.0
    perg = _camada(pl, 'pergunta')
    perg['t0'] = 4.0
    for i, linha in enumerate(perg['p']['linhas']):
        linha['t'] = 4.1 + i * .4
    assert 'F-GANCHO' in _regras(pl)


def test_cta_automatico_no_fecho_sem_alongar_video():
    """ATLAS V1: quando a revelação termina tarde, CTA discreto sobrepõe o fecho em slot separado."""
    pl = P.resolver_tempos(copy.deepcopy(ATLAS), [])
    cta = [L for L in P.camadas(pl) if L['componente'] == 'editorial.cta']
    assert len(cta) == 1 and 'sobreposto' in pl['cta_decisao']
    assert cta[0]['t0'] >= pl['duracao'] - 1.3 and cta[0]['t1'] <= pl['duracao']
    assert any(L['componente'] == 'editorial.titleOrPayoff' for L in P.camadas(pl))
    pl2 = copy.deepcopy(ATLAS)
    pl2['duracao'] = ATLAS['duracao'] + 2.5
    r = P.resolver_tempos(pl2, [])
    cta2 = [L for L in P.camadas(r) if L['componente'] == 'editorial.cta']
    assert len(cta2) == 1 and 'sobreposto' not in r['cta_decisao']
    assert cta2[0]['t0'] >= max(x['t'] for x in _camada(r, 'payoff')['p']['linhas']) + .8
    assert cta2[0]['t1'] <= r['duracao']


def _medida(**k):
    return {'camadas': [], 'rotulos': [], 'textos': [], 'cortados': [], 'metas': [], 'pinos': [], 'roi': None, **k}


def test_quadro_cartao_desalinhado_inclinado_e_legenda_fora_da_faixa():
    import scripts.formatos_validar as V
    from src.v4.formatos import layout
    pl = {'formato': 'atlas', 'beats': [], 'duracao': 10}
    lx, ly, lw, lh = layout.faixa_inferior()['legenda']
    m = _medida(cartoes=[{'camada': 'c1', 'alvo': [540, 900], 'centro': [548, 900], 'caixa': {}, 'rot': -2.0}],
                camada={'legenda': {'x': lx, 'y': ly - 40, 'w': lw, 'h': lh}})
    regras = {p['regra'] for p in V.checar(m, pl, 1.0)}
    assert {'R-CARTAO-DESALINHADO', 'R-CARTAO-INCLINADO', 'R-LEGENDA-FORA'} <= regras


def test_quadro_contra_interface_simulada_das_plataformas():
    import scripts.formatos_validar as V
    pl = {'formato': 'atlas', 'beats': [], 'duracao': 10}
    m = _medida(camadas=[{'id': 'x', 'componente': 'editorial.statCard', 'caixa': {'x': 900, 'y': 1300, 'w': 160, 'h': 80}}])
    assert any(p['regra'] == 'R-PLATAFORMA' for p in V.checar_plataformas(m, pl, 1.0))
    m = _medida(camadas=[{'id': 'x', 'componente': 'editorial.statCard', 'caixa': {'x': 200, 'y': 700, 'w': 600, 'h': 200}}])
    assert not V.checar_plataformas(m, pl, 1.0)


def test_atribuicao_obrigatoria_visivel_com_o_mapa():
    import scripts.formatos_validar as V
    pl = copy.deepcopy(ATLAS)
    roi = {'x': 100, 'y': 500, 'w': 800, 'h': 600}
    m = _medida(roi=roi, metas=[{'tipo': 'atribuicao', 'caixa': {'x': 72, 'y': 1394, 'w': 835, 'h': 22}, 'txt': 'Natural Earth', 'datasets': ['ne_vetor', 's2_2016']}])
    assert 'R-ATRIBUICAO-AUSENTE' in {p['regra'] for p in V.checar(m, pl, 1.0)}
    m['metas'] = []
    assert 'R-ATRIBUICAO-AUSENTE' in {p['regra'] for p in V.checar(m, pl, 1.0)}


def test_amostragem_ampliada_cobre_gancho_transicoes_e_o_meio_dos_beats():
    import scripts.formatos_validar as V
    pl = P.resolver_tempos(copy.deepcopy(ATLAS), [])
    a = V.amostrar(pl)
    ts = [x['t'] for x in a]
    assert len(a) > 3 * len(pl['beats'])
    assert all(not (c['t0'] - .05 <= t <= c['t1'] + .05) for c in pl['clipes'] for t in ts)
    furos = sorted((c['t0'], c['t1']) for c in pl['clipes'])
    livres = [(a_, b_) for a_, b_ in zip([0] + [z for _, z in furos], [x for x, _ in furos] + [pl['duracao']])]
    for t0, t1 in zip(ts, ts[1:]):
        if not any(a_ - .05 <= t0 and t1 <= b_ + .05 for a_, b_ in livres):
            continue
        assert t1 - t0 <= 3.0, (t0, t1)


def test_medicao_da_legenda_pede_medir_na_selecao_da_composicao():
    """a caixa real da legenda NUNCA foi medida: renderStill usa as props resolvidas na seleção (sem medir)"""
    js = (RAIZ / 'motor4/remotion/medir.mjs').read_text()
    assert "fs.readFileSync(pc, 'utf8')), medir: true }" in js


def test_ritmo_do_portao_desconta_a_camera():
    src = (RAIZ / 'src/v4/formatos/produzir.py').read_text()
    assert "rit['sem_camera']['maior_trecho_parado_s'] <= 3" in src and "'legenda_ok'" in src


def test_mascara_de_fala_com_narracao_densa(tmp_path):
    """narração quase sem pausa: o percentil 15 é FALA — o limiar não pode subir acima dela (tudo virava silêncio)"""
    from src.v4.formatos import legenda_sync as LS
    wav = _wav_fala(tmp_path, [(0.05, 3.0), (3.15, 6.0)], 6.1)
    pal = [{'w': f'P{i}', 's': round(.05 + i * .49, 3), 'e': round(.05 + (i + 1) * .49, 3)} for i in range(6)]
    pal += [{'w': f'Q{i}', 's': round(3.15 + i * .47, 3), 'e': round(3.15 + (i + 1) * .47, 3)} for i in range(6)]
    narr = tmp_path / 'n.json'
    narr.write_text(json.dumps({'palavras': pal}))
    assert LS.conferir(narr, wav)['ok']


def test_conexao_entre_paises_sem_trajeto_osm():
    """rota 'arco' (dois pontos): desenhada pelo canal, não exige trajeto OSM nem ODbL; Palco usa círculo máximo"""
    pl = json.loads((RAIZ / 'src/v4/formatos/planos/reuso/atlas_chips.json').read_text())
    assert all(r.get('arco') for r in pl['rotas'])
    tsx = (RAIZ / 'motor4/remotion/src/formatos/Palco.tsx').read_text()
    assert 'turf.greatCircle' in tsx and '!r.arco' in tsx


def test_reuso_em_outras_historias_sem_codigo_novo():
    """§6: chips (mapa-múndi, conexões, empresas) e história (fotos, datas, régua) passam nas MESMAS regras do motor"""
    import scripts.formatos_reuso as R
    for nome in ('atlas_chips', 'atlas_historia_panama'):
        pl = json.loads((RAIZ / f'src/v4/formatos/planos/reuso/{nome}.json').read_text())
        pal, falas, dur = R.tempos_sinteticos(pl['narracao']['texto'])
        r = P.resolver_tempos(pl, pal)
        r['duracao'] = dur
        erros = [v for v in P.validar(r) if v['gravidade'] == 'erro']
        assert not erros, (nome, erros)


def test_camera_respeita_o_limite_do_maplibre_e_a_copia_do_mundo():
    """reuso China × EUA: no mapa-múndi os pinos descolavam 37–340 px (MapLibre trava zoom/centro; Pacífico cruza a data)"""
    cam = P.camera_roi([100, 8, 250, 58], [100, 470, 807, 650])
    assert cam['zoom'] >= P.Z_MIN - 1e-9
    palco = [{'t': 0, 'camera': cam}]
    c = P.camera_em(palco, 1.0)
    ws = 512 * 2 ** c['zoom']
    cy = c['fy'] - (c['ancora'][1] - 960) / ws
    assert 960 / ws - 1e-9 <= cy <= 1 - 960 / ws + 1e-9
    x_eua, _ = P.projetar(c, -121.96, 37.35)            # Califórnia na vista centrada no Pacífico: à DIREITA de Taiwan
    x_tw, _ = P.projetar(c, 120.97, 24.78)
    assert 0 < x_tw < x_eua < 1080
    tsx = (RAIZ / 'motor4/remotion/src/formatos/Palco.tsx').read_text()
    assert 'Math.log2(H / 512)' in tsx and 'arcoContinuo' in tsx
    assert '% 1 + 1) % 1 - .5' in (RAIZ / 'motor4/remotion/src/formatos/Primitivas.tsx').read_text()


def test_camada_que_entra_com_a_camera_em_voo_nao_cobre_o_territorio():
    r = copy.deepcopy(ATLAS)
    _camada(r, 'perfil')['t0'] = next(b['t'] for b in r['beats'] if b['id'] == 'b4-degraus') + .15
    assert 'F-COBRE-TERRITORIO' in _regras(r)


def test_legenda_mede_o_corpo_com_a_fonte_real_e_rotulos_do_mapa_na_area_segura():
    cam = (RAIZ / 'motor4/remotion/src/Camada.tsx').read_text()
    assert 'measureText' in cam and 'linhas <= (L.linhas_max' in cam and '[frame, fontes]' in cam
    assert "'seguro'" in (RAIZ / 'src/v4/formatos/plano.py').read_text() and 'S.dir_max' in (RAIZ / 'motor4/remotion/src/formatos/Palco.tsx').read_text()


def test_storyboard_nao_escolhe_estetica_nem_diagrama_no_lugar_do_mapa():
    """auditoria 17/11: o plano podia trocar mapa por diagrama, dispensar a base cartográfica e reescrever a identidade"""
    pl = copy.deepcopy(ATLAS_BRUTO)
    b = next(b for b in pl['beats'] if b.get('composicao') == 'atlas.tecnica')
    b.pop('funcao')
    _camada(pl, 'payoff')['p']['linhas'][0]['tamanho'] = 140
    pl['rotas'][0]['largura'] = 20
    pl['beats'][0]['transicao'] = 3.0
    viol = P.estilo_no_episodio(pl)
    assert any('tamanho' in x for x in viol) and any('largura' in x for x in viol) and any('transicao' in x for x in viol)
    regras = _regras({**copy.deepcopy(ATLAS), '_estilo_no_episodio': viol, 'beats': [dict(x, funcao=None) if x.get('composicao') == 'atlas.tecnica' else x for x in copy.deepcopy(ATLAS)['beats']]})
    assert {'F-ESTILO-NO-EPISODIO', 'F-TECNICO-SEM-MECANISMO'} <= regras
    assert 'atlas.tecnica' in P.COMP and P.COMP['atlas.tecnica'].get('exige_funcao')


def test_legenda_do_atlas_segue_a_referencia_e_vem_do_canal():
    """referência A medida: frase em caixa normal, 1–3 palavras, ~56 px, sem karaokê — estilo do CANAL, não do episódio"""
    from src.v4.formatos import legenda_sync as LS
    pl = P.resolver_tempos(copy.deepcopy(ATLAS), [])
    pal = [{'w': w, 's': i * .4, 'e': i * .4 + .35} for i, w in enumerate(['O', 'CANAL', 'DO', 'PANAMÁ', 'LIGA', 'O', 'ATLÂNTICO'])]
    c = P.props_camada(pl, {'palavras': pal})
    assert c['estilo']['caixa'] == 'frase' and c['estilo']['max_palavras'] == 3 and c['estilo']['destaque_palavra'] is False
    txt = ' '.join(w['w'] for w in c['palavras'])
    assert 'Panamá' in txt and 'Atlântico' in txt and 'liga' in txt and txt.startswith('O ')
    assert all(len(g['txt'].split()) <= 4 for g in LS.grupos(c['palavras'], 3))


def test_base_cobre_a_tela_inteira_e_recuo_suavizado():
    """trecho do mapa-múndi (17/11): a borda do recorte NE2 aparecia; recuo da referência acelera e assenta"""
    import scripts.formatos_reuso as R
    pl = json.loads((RAIZ / 'src/v4/formatos/planos/reuso/atlas_chips.json').read_text())
    pl['rasters'] = [{'nome': 'ne2_asia_leste'}, {'nome': 'ne2_pacifico'}]
    pal, _, dur = R.tempos_sinteticos(pl['narracao']['texto'])
    r = P.resolver_tempos(pl, pal); r['duracao'] = dur
    assert 'F-MAPA-BORDA-DA-BASE' in {v['regra'] for v in P.validar(r)} or 'F-MAPA-SEM-BASE' in {v['regra'] for v in P.validar(r)}
    a = P.resolver_tempos(copy.deepcopy(ATLAS), [])
    k = a['palco'][-1]
    assert k['movimento'] == 'recua' and k.get('dur_deriva')
    t0 = k['t'] + k['dur_camera']
    z = [P.camera_em(a['palco'], t0 + f * k['dur_deriva'])['zoom'] for f in (0, .1, .5, .9, 1)]
    assert abs(z[1] - z[0]) < abs(z[2] - z[1]) / 2          # começa devagar


def test_diretor_atlas_descreve_contrato_real_e_nao_proibe_pessoas():
    """O storyboard de episódios novos não pode receber o contrato antigo que pedia palco manual e omitia rasters."""
    pr = diretor.prompt([{'id': 'f1', 'texto': 'pessoa e lugar'}], 'atlas', None, '- asset licenciado')
    assert '"camera":"roi"' in pr and 'NÃO escreva "palco"' in pr
    assert '"rasters"' in pr and '"roi"' in pr and '"composicao"' in pr
    assert "'cedula'" in pr and "'selo'" in pr
    assert 'fotos licenciadas de pessoas reais' in pr
    assert 'não a substitua por um prédio' in pr


def test_pino_referencia_tem_ancora_mensuravel_apos_pulso():
    """Após 0,7 s o pulso acaba, mas a âncora tem que continuar no DOM para medir pan/zoom."""
    src = (RAIZ / 'motor4/remotion/src/formatos/Primitivas.tsx').read_text()
    trecho = src.split('const PinoReferencia:')[1].split("// statCard estilo 'cedula'")[0]
    assert 'data-ancora-geo={JSON.stringify(p.lonlat)}' in trecho
    assert "width: 2, height: 2, pointerEvents: 'none'" in trecho
    assert 'kp >= 1 && <div data-ancora-geo' not in trecho


def test_raster_fora_do_zoom_nao_conta_como_base_visivel():
    """Um arquivo raster existente pode estar 100% transparente por de/ate: impedir mapa chapado."""
    assert P.opacidade_raster(3.5, de=9.0) == 0
    assert P.opacidade_raster(3.5, ate=1.0) == 0
    assert P.opacidade_raster(3.5) == 1
    pl = copy.deepcopy(ATLAS)
    for r in pl['rasters']:
        r['de'] = 20.0
    assert 'F-MAPA-BASE-INVISIVEL' in _regras(pl)


def test_marca_atlas_dentro_do_feed_e_recorte_e_bloqueador():
    """Regressao 44221167260: 40/40 quadros com marca fora do feed nao podem passar no fiscal."""
    import scripts.formatos_validar as V
    from src.v4.formatos import layout
    marco = layout.CFG['faixa_inferior']['marca_y']
    assert layout.CFG['faixa_inferior']['marca_atlas'] is False
    assert P.zonas('atlas').get('marca') is None
    assert P.props_camada({'formato': 'atlas', 'duracao': 2, 'canal': 'coringa', 'clipes': []}, {'palavras': []})['marca_visivel'] is False
    assert marco >= layout.CFG['perfis']['instagram_reels']['recorte_feed']['topo'] + 6
    pl = {'formato': 'atlas', 'beats': [], 'duracao': 10}
    m = _medida(camada={'marca': {'x': 72, 'y': 232, 'w': 350, 'h': 35}})
    erros = V.checar_plataformas(m, pl, 1.0)
    assert any(e['regra'] == 'R-MARCA-RECORTE-FEED' and not e.get('aviso') for e in erros)
    m['camada']['marca']['y'] = marco
    assert not any(e['regra'] == 'R-MARCA-RECORTE-FEED' for e in V.checar_plataformas(m, pl, 1.0))


def test_preflight_bloqueia_marca_cortada_sem_render(monkeypatch):
    """Recorte do feed deve falhar em P.validar ANTES da fase cara de quadros/render."""
    from src.v4.formatos import layout
    pl = copy.deepcopy(ATLAS)
    assert 'F-MARCA-RECORTE-FEED' not in _regras(pl)
    monkeypatch.setitem(layout.CFG['faixa_inferior'], 'marca_atlas', True)
    monkeypatch.setitem(layout.CFG['faixa_inferior'], 'marca_y', 232)
    assert 'F-MARCA-RECORTE-FEED' in _regras(pl)


def test_atlas_v1_tokens_exclusivos_e_template_documentado():
    """Tokens de design ATLAS não podem estilizar o DOSSIÊ acidentalmente."""
    can = P.canal('coringa')
    assert can['cartao_atlas']['raio_px'] == 5
    assert can['cartao_atlas']['borda_px'] > 0
    assert can['pino']['protagonista']['raio'] > can['pino']['secundario']['raio']
    assert can['palco']['tecnico_atlas']['fundo'] == '#070B14'
    ts = (RAIZ / 'motor4/remotion/src/formatos/Primitivas.tsx').read_text()
    assert "c.P.formato === 'atlas'" in ts and 'cartao_atlas' in ts
    palco = (RAIZ / 'motor4/remotion/src/formatos/Palco.tsx').read_text()
    assert "P.formato === 'atlas'" in palco and 'tecnico_atlas' in palco
    guia = (RAIZ / 'docs/v4/formatos/GUIA_VISUAL_ATLAS_V1.md').read_text()
    assert 'MAPA HERO' in guia and 'CTA final' in guia


def test_faixas_atlas_creditos_abaixo_de_legenda_e_dentro_da_area_segura():
    from src.v4.formatos import layout
    fi = layout.faixa_inferior()
    leg, cred = fi['legenda'], fi['creditos']
    assert leg[1] + leg[3] < cred[1]
    assert cred[1] + cred[3] <= fi['base_visivel']
    assert leg[0] >= 60 and cred[0] >= 60


def test_atlas_v1_primeiro_quadro_deve_ser_mapa_e_cta_nao_some(monkeypatch):
    """Regressão: clipe técnico inicial e CTA pedido mas omitido bloqueiam antes do render."""
    pl = copy.deepcopy(ATLAS)
    assert 'F-GANCHO-MAPA-PRIMEIRO' not in _regras(pl)
    pl['beats'][0]['t'] = 2.4
    assert 'F-GANCHO-MAPA-PRIMEIRO' in _regras(pl)
    pl = copy.deepcopy(ATLAS)
    pl['clipes'].append({'t0': 0, 't1': 2.1, 'componente': 'mecanismo.eclusa',
                         'params': {'tempos': []}})
    assert 'F-GANCHO-MAPA-PRIMEIRO' in _regras(pl)
    # Mantém a composição e remove APENAS seu slot opcional de CTA: não pode sumir silenciosamente.
    slots = P.COMP['atlas.manchete']['slots']
    monkeypatch.setitem(P.COMP['atlas.manchete'], 'slots', {k: v for k, v in slots.items() if k != 'cta'})
    pl = copy.deepcopy(ATLAS)
    assert 'F-CTA-FINAL-AUSENTE' in _regras(pl)


def test_creditos_da_foto_e_mapa_medidos_pelo_texto_real():
    """Regressão: caixa de créditos cabia, porém texto multi-linha invadia a legenda."""
    import scripts.formatos_validar as V
    pl = {'formato': 'atlas', 'beats': [], 'duracao': 10}
    x, y, w, h = P.zonas('atlas')['creditos']
    atrib = {'tipo': 'atribuicao', 'caixa': {'x': x, 'y': y, 'w': w, 'h': h},
              'texto_caixa': {'x': x, 'y': y - 25, 'w': w, 'h': h + 25},
              'txt': 'Natural Earth · foto licenciada', 'datasets': []}
    m = _medida(metas=[atrib])
    assert 'R-CREDITOS-TEXTO-TRANSBORDA' in {p['regra'] for p in V.checar(m, pl, 1.0)}
    atrib['texto_caixa'] = {'x': x, 'y': y, 'w': w, 'h': h}
    assert 'R-CREDITOS-TEXTO-TRANSBORDA' not in {p['regra'] for p in V.checar(m, pl, 1.0)}
