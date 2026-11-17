"""Regressões da execução real 43956541084 (Canal do Panamá): causas gerais, não casos do vídeo."""
from pathlib import Path

from src.v4.acervo_v4 import _licenca
from src.v4.backends import js, rembg_camadas


def test_backends_recebem_caminhos_absolutos(monkeypatch, tmp_path):
    vistos = []
    monkeypatch.setattr(js, 'rodar', lambda cmd, **k: vistos.append([str(c) for c in cmd]) or {'rc': 0})
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'rel').mkdir()
    (tmp_path / 'rel' / 'x.mp4').write_bytes(b'0')
    js.remotion('Camada', {}, Path('rel/x.mp4'), Path('rel'))
    js.revideo({}, Path('rel/x.mp4'), Path('rel'))
    for cmd in vistos:
        caminhos = [a.split('=', 1)[-1] for a in cmd if 'rel' in a]
        assert caminhos and all(Path(c).is_absolute() for c in caminhos), cmd


def test_rembg_le_o_json_mesmo_com_aviso_do_onnxruntime_depois():
    log = '$ cmd\n\n{"cobertura": 0.07, "fragmentos": 2}\n[W:onnxruntime:Default] Skipping pci_bus_id …\n'
    assert rembg_camadas.medidas_do_log(log)['cobertura'] == .07


def test_licenca_vem_do_ultimo_parentese_do_credito():
    assert _licenca('Ship (1913) — Fulano (CC BY-SA 3.0), Wikimedia Commons') == 'CC BY-SA 3.0'
    assert _licenca('"x" — y (GFDL), via Wikimedia Commons') == 'GFDL'
    assert _licenca('sem licença') is None
    assert _licenca('Navio na eclusa (1913) — autor desconhecido') is None, 'ano não é licença'
    assert _licenca('Gatun (1912) — X (Public domain), via Wikimedia Commons') == 'Public domain'


def test_telegram_tenta_de_novo_em_falha_passageira_do_servidor(monkeypatch):
    """execução 43956541084: getChat 502 Bad Gateway e a prévia não foi entregue. 5xx tenta de novo; 4xx não."""
    from src.v3 import previa_telegram as PT
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'x')
    monkeypatch.setattr(PT.time, 'sleep', lambda s: None)
    respostas = iter([(502, {}), (200, {'ok': True, 'result': {'id': 1}})])

    class R:
        def __init__(self, c, j): self.status_code, self._j, self.ok, self.text = c, j, c == 200, str(j)
        def json(self): return self._j
    monkeypatch.setattr(PT.requests, 'post', lambda *a, **k: R(*next(respostas)))
    assert PT._api('getChat', {'chat_id': 1}) == {'id': 1}
    monkeypatch.setattr(PT.requests, 'post', lambda *a, **k: R(403, {'ok': False}))
    import pytest
    with pytest.raises(PT.EnvioRecusado):
        PT._api('getChat', {'chat_id': 1})


def test_video_de_banco_de_outro_lugar_e_descartado_antes_da_visao():
    """execução 43972774128: vídeo do Pixabay 'sunset, canal, city' (outro país) foi aceito pela visão como eclusa do
    Panamá. Vídeo de banco só se identifica pelas tags: sem nome próprio do pedido, é outro lugar."""
    from src.v4 import acervo_v4 as A
    nomes = A.nomes_proprios(['Panama Canal locks video', 'Miraflores Locks ship', 'Gatun Locks ship transit'])
    assert nomes == {'panama', 'miraflores', 'gatun'}
    errado = {'url': 'https://cdn.pixabay.com/video/x.mp4', 'titulo': 'pixabay #230248: sunset, canal, city, light', 'video': {'url': 'x'}}
    certo = {'url': 'https://cdn.pixabay.com/video/y.mp4', 'titulo': 'pixabay #1: panama, canal, ship, lock', 'video': {'url': 'y'}}
    assert not A.mesmo_lugar(errado, nomes) and A.mesmo_lugar(certo, nomes)
    esc, info = A.escolher([errado], 'navio na eclusa', set(), ['Panama Canal locks video'])
    assert esc is None and 'outro lugar' in info['motivo']


def test_roi_em_pixels_e_descartada():
    from src.v4.acervo_v4 import _roi_valida
    assert _roi_valida([428, 523, 132, 30]) is None
    assert _roi_valida([.1, .2, .5, .6]) == [.1, .2, .5, .6]
    assert _roi_valida(None) is None


def test_pico_do_aac_e_corrigido_sem_baixar_a_loudness(monkeypatch, tmp_path):
    """execução 43972774128: master −1,4 dBTP, MP4 −0,1 dBTP (o AAC sobe o pico). O MP4 é medido e o limitador age só
    nos picos, com teto que desconta o excesso do AAC."""
    from src.v4 import compositor as C
    cmds = []
    monkeypatch.setattr(C, 'rodar', lambda cmd, **k: cmds.append([str(x) for x in cmd]) or (tmp_path / 'final_pico.mp4').write_bytes(b'x'))
    mp4, wav = tmp_path / 'v.mp4', tmp_path / 'm.wav'
    mp4.write_bytes(b'x')
    medidas = {str(mp4): [{'pico': -0.1, 'lufs': -14.6}, {'pico': -2.4, 'lufs': -14.6}], str(wav): [{'pico': -1.4}]}
    r = C.corrigir_pico_aac(mp4, wav, tmp_path, medir=lambda p: medidas[str(p)].pop(0))
    assert r['corrigido'] and r['teto_limitador_db'] == -2.6 and r['pico_depois'] <= -1 and r['lufs_depois'] == -14.6
    assert 'volume=' not in ' '.join(cmds[0]) and 'alimiter' in ' '.join(cmds[0]) and '-c:v' in cmds[0] and 'copy' in cmds[0]
    assert C.corrigir_pico_aac(mp4, wav, tmp_path, medir=lambda p: {'pico': -1.5})['corrigido'] is False


def test_revideo_registra_o_chrome_e_tenta_flags_minimas():
    """execução 43972774128: 'Target closed' na partida, sem o motivo no log. NÃO VERIFICADO NO RUNNER: este teste só
    garante que o motivo passa a aparecer (dumpio) e que há segunda tentativa; o render real depende da próxima execução."""
    import subprocess
    src = (Path(__file__).resolve().parents[1] / 'motor4' / 'revideo' / 'render.mjs')
    t = src.read_text()
    assert 'dumpio: true' in t and t.count('executablePath') >= 3 and "'--disable-dev-shm-usage'" in t
    assert subprocess.run(['node', '--check', str(src)]).returncode == 0


def test_demonstracao_exige_render_e_revisao_semantica():
    """execução 43972774128: c6 (backend falhou, quadro preto) e c5 (vídeo de outro lugar) contavam como 'demonstra'
    só pela modalidade declarada."""
    from src.v4 import metricas as M
    m = {'por_cena': [{'cena': 'c5', 'demonstra_acao': True}, {'cena': 'c6', 'demonstra_acao': False},
                      {'cena': 'c8', 'demonstra_acao': True}, {'cena': 'c9', 'demonstra_acao': True}], 'resumo': {}}
    rev = {'planos': [{'evento_id': 'c5', 'veredito': {'demonstra': 'nao'}}, {'evento_id': 'c6', 'veredito': {'demonstra': 'nao'}},
                      {'evento_id': 'c8', 'veredito': {'demonstra': 'sim'}}, {'evento_id': 'c9', 'veredito': {'_nao_revisado': 'erro'}}]}
    r = M.combinar_revisao(m, rev)
    assert [c['demonstra_acao'] for c in r['por_cena']] == [False, False, True, False]
    assert r['resumo']['pct_cenas_que_demonstram'] == 25.0 and r['resumo']['cenas_demonstracao_pendente'] == ['c9']


def test_acervo_falha_fechado_sem_prova_de_lugar_e_objeto(monkeypatch):
    """auditoria 16/11 (3.3): sem visão, com erro da visão ou sem confirmação de lugar+objeto, a 1ª opção NÃO vira prova."""
    from src.v4 import acervo_v4 as A
    import src.gemini as gem
    cands = [{'url': 'http://x/a.jpg', 'w': 1600, 'h': 1200, 'credito': 'a — b (CC BY 4.0), via Wikimedia Commons'}]
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    esc, info = A.escolher(cands, 'navio na eclusa', set(), ['Gatun Locks'])
    assert esc is None and info['prova'] == 'INCERTO'
    monkeypatch.setenv('GEMINI_API_KEY', 'x')
    monkeypatch.setattr(A, '_miniatura', lambda url: b'jpg')
    monkeypatch.setattr(gem, 'json_visao', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('cota')))
    assert A.escolher(cands, 'x', set(), ['Gatun Locks'])[1]['prova'] == 'INCERTO'
    monkeypatch.setattr(gem, 'json_visao', lambda *a, **k: {'escolha': 0, 'local_confere': False, 'objeto_confere': True})
    assert A.escolher(cands, 'x', set(), ['Gatun Locks'])[0] is None
    monkeypatch.setattr(gem, 'json_visao', lambda *a, **k: {'escolha': 0, 'local_confere': True, 'objeto_confere': True, 'roi': [3, 4, 5, 6]})
    esc, info = A.escolher(cands, 'x', set(), ['Gatun Locks'])
    assert esc is cands[0] and info['prova'] == 'PROVADO' and info['roi'] is None


def test_detalhe_que_repete_a_visao_geral_vira_foto_unica():
    """auditoria 16/11 (c4): visão geral [0,0,1,1] + 'detalhe' 1,23× maior = a mesma foto duas vezes na cena."""
    from src.v3 import decisao
    wh = [1920, 1519]
    dec = decisao.decidir({'layout': 'editorial'}, {'titulo': 'foto de arquivo 1913', 'desc': 'documento'}, wh,
                          [{'t': 0, 'caixa': [0.2226, 0.0, 0.5548, 1.0]}], [0.03, 0.02, 0.94, 0.96], {},
                          [0.2226, 0.0, 0.5548, 1.0], [0.2226, 0.0, 0.5548, 1.0])
    assert dec['layout'] == 'cobrir' and 'DETALHE-REPETE-GERAL' in [d[1] for d in dec['degradacoes']]


def _fx():
    import json
    return json.loads((Path(__file__).parent / 'dados' / 'v4_panama_43972774128.json').read_text())


def test_episodio_reprovado_aciona_os_portoes():
    """regressão NEGATIVA (auditoria 16/11): a execução 43972774128 tinha estado BLOQUEADO só por licença/backend; os
    portões precisam derrubá-la também pelo que a revisão viu, e nunca deixá-la como episódio pronto."""
    from src.v4 import portoes
    fx = _fx()
    regs = [{'estado': fx['estados'][c['id']]} for c in fx['cenas']]
    g = portoes.decidir(fx['cenas'], regs, {'planos': fx['revisao']}, [])
    assert g['estado'] == portoes.DIAGNOSTICO and 'c6' in g['cenas_nao_prontas']      # tela preta = diagnóstico
    assert any(b.startswith('G-MIDIA-ERRADA c5') for b in g['bloqueios'])               # canal de outro país
    assert any('G-DEMONSTRA-PARCIAL c2' in x for x in g['revisoes']) and any('G-DEMONSTRA-PARCIAL c7' in x for x in g['revisoes'])
    # mesmo se c6 tivesse renderizado, a mídia errada em c5 bloqueia
    regs[[c['id'] for c in fx['cenas']].index('c6')] = {'estado': 'renderizado'}
    assert portoes.decidir(fx['cenas'], regs, {'planos': fx['revisao']}, [])['estado'] == portoes.BLOQUEADO


def test_revisao_ausente_e_info_parada_nunca_viram_aprovacao():
    from src.v4 import portoes
    cenas = [{'id': 'c1', 'modalidade': 'registro_foto', 'componente': 'registro.foto'}]
    g = portoes.decidir(cenas, [{'estado': 'renderizado'}], None, [{'cena': 'c1', 'informacao_parada_s': 9.5}])
    assert g['estado'] == portoes.PENDENTE and any('G-SEM-REVISAO' in x for x in g['revisoes']) and any('G-INFO-PARADA' in x for x in g['revisoes'])
    ess = [{'id': 'c6', 'modalidade': 'esquema_2d', 'componente': 'mecanismo.eclusa', 'acao_fisica': True}]
    g = portoes.decidir(ess, [{'estado': 'renderizado'}], {'planos': [{'evento_id': 'c6', 'veredito': {'demonstra': 'nao'}}]}, [])
    assert g['estado'] == portoes.BLOQUEADO and 'essencial' in g['bloqueios'][0]


def test_clipe_preto_ou_congelado_reprova_no_portao(tmp_path):
    """c6: 98,5% de pixels pretos por 7 s entrou no episódio. Agora o clipe não passa e a cena vai para a alternativa."""
    import subprocess
    from src.v4 import portoes
    preto = tmp_path / 'preto.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=1080x1920:r=30:d=3', '-pix_fmt', 'yuv420p', str(preto)], check=True)
    v = portoes.validar_clipe(preto, 3.0, exige_movimento=True)
    assert not v['ok'] and any(m.startswith('PRETO') for m in v['motivos'])
    parado = tmp_path / 'parado.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=s=1080x1920:r=30:d=3', '-vf', 'trim=end_frame=1,tpad=stop_mode=clone:stop_duration=3',
                    '-t', '3', '-pix_fmt', 'yuv420p', str(parado)], check=True)
    v = portoes.validar_clipe(parado, 3.0, exige_movimento=True)
    assert any(m.startswith('CONGELADO') for m in v['motivos']) and portoes.validar_clipe(parado, 3.0, exige_movimento=False)['ok']
    vivo = tmp_path / 'vivo.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=s=1080x1920:r=30:d=3', '-pix_fmt', 'yuv420p', str(vivo)], check=True)
    assert portoes.validar_clipe(vivo, 3.0, exige_movimento=True)['ok']


def test_backend_que_falha_cai_na_alternativa_pre_validada(monkeypatch, tmp_path):
    """c6: Revideo falhou e o orquestrador pôs tela preta. Agora: mecanismo.eclusa (palco V2) com os mesmos parâmetros."""
    from src.v4 import episodio as E, portoes
    usados = []

    def render(c, acv, trab, primeira=False):
        usados.append(c['componente'])
        if c['componente'] == 'mecanismo.nivel_vasos':
            raise RuntimeError('TargetCloseError')
        assert c['params']['sentido'] == 'subir' and c['params']['desnivel_m'] == 9 and len(c['params']['etapas']) == 3
        return tmp_path / 'ok.mp4', {'backend': 'legacy-v2'}
    monkeypatch.setattr(E, 'render_cena', render)
    monkeypatch.setattr(portoes, 'validar_clipe', lambda clipe, dur, exige: {'ok': True, 'motivos': []})
    c = {'id': 'c6', 'ini': 0, 'fim': 7, 'modalidade': 'esquema_2d', 'componente': 'mecanismo.nivel_vasos', 'acao_fisica': True,
         'params': {'desnivel_m': 9, 'nomes': {'alto': 'Lago', 'baixo': 'Mar'}, 'passos': ['a', 'b', 'c', 'd', 'e']}}
    clipe, r = E.render_validado(c, {}, tmp_path)
    assert usados == ['mecanismo.nivel_vasos', 'mecanismo.eclusa'] and r['alternativa'] and c['componente_usado'] == 'mecanismo.eclusa'
    monkeypatch.setattr(E, 'render_cena', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('x')))
    clipe, r = E.render_validado(dict(c, componente='mecanismo.nivel_vasos'), {}, tmp_path)
    assert clipe is None and r['estado'] == 'nao_pronta' and len(r['tentativas']) == 2


def test_mapa_que_promete_rota_sem_geometria_nao_fica_pronto(monkeypatch, tmp_path):
    """auditoria 16/11 (c2): o OSM não voltou, a rota não foi desenhada e o mapa entrou mesmo assim (decorativo)."""
    from src.v4 import episodio as E, geo
    from src.v4.util import FalhaBackend
    import pytest
    monkeypatch.setattr(geo, 'preparar', lambda p, trab: {'meta': {'rota_km': None, 'rota_motivo_ausente': 'sem geometria'}})
    c = {'id': 'c2', 'ini': 0, 'fim': 7, 'modalidade': 'mapa', 'componente': 'mapa.rota', 'params': {'regiao': [0, 0, 1, 1], 'rota': {'de': 1, 'ate': 5}}}
    with pytest.raises(FalhaBackend, match='rota pedida sem geometria'):
        E.render_cena(c, {}, tmp_path)


def test_osm_tenta_espelhos_e_consulta_sem_nome_e_registra(monkeypatch, tmp_path):
    from src.v4 import geo
    chamadas = []

    class R:
        def __init__(self, els): self.els = els
        def raise_for_status(self): pass
        def json(self): return {'elements': self.els}

    def post(url, data=None, **k):
        chamadas.append((url, '"name"' in data['data']))
        if url == geo.ESPELHOS[0]:
            raise RuntimeError('504')
        if '"name"' in data['data']:
            return R([])                                   # com filtro de nome: vazio
        return R([{'type': 'way', 'id': 1, 'geometry': [{'lon': 0, 'lat': 0}, {'lon': 1, 'lat': 1}]}])
    monkeypatch.setattr(geo.requests, 'post', post)
    monkeypatch.setattr('time.sleep', lambda s: None)
    monkeypatch.delenv('CORINGA_OSM_CACHE', raising=False)
    arq = geo.osm_rota([0, 0, 1, 1], {'tags': {'waterway': 'canal'}, 'nome': 'Panam'}, tmp_path / 'c', tmp_path / 'tent.json')
    assert arq and arq.exists() and (tmp_path / 'tent.json').exists()
    assert chamadas[0] == (geo.ESPELHOS[0], True) and chamadas[-1][1] is False


def test_legenda_some_so_quando_o_componente_escreve_a_fala():
    """c9: '98,5 MIL M³ DE ÁGUA DOCE' na tela e a mesma frase na legenda."""
    from src.v4.episodio import texto_repete_fala
    fala = 'O preço dessa subida: cerca de 98,5 mil metros cúbicos de água doce do lago.'
    assert texto_repete_fala({'fala': fala, 'params': {'linhas': [{'texto': '98,5 mil m³'}, {'texto': 'de água doce'}]}})
    assert not texto_repete_fala({'fala': fala, 'params': {'linhas': [{'texto': 'Sem bombas.'}]}})
    assert not texto_repete_fala({'fala': fala, 'params': {}})


def test_acao_fisica_exige_cadeia_visivel_no_contrato():
    from src.v4 import contrato
    ep = {'versao_contrato': contrato.VERSAO, 'cenas': [{'id': 'c1', 'ini': 0, 'fim': 5, 'fala': 'a água sobe', 'objetivo': 'x', 'o_que_precisa_aparecer': 'água subindo',
          'modalidade': 'esquema_2d', 'componente': 'mecanismo.eclusa', 'params': {}, 'camera': {'tipo': 'fixa'}, 'transicao': {'tipo': 'corte'}, 'acao_fisica': True}]}
    assert 'R-ACAO-SEM-PROVA' in [v['regra'] for v in contrato.validar(ep)]
    ep['cenas'][0]['prova'] = {'sujeito': 'navio', 'estado_inicial': 'nível baixo', 'acao': 'água entra', 'resultado': 'navio sobe 9 m'}
    assert 'R-ACAO-SEM-PROVA' not in [v['regra'] for v in contrato.validar(ep)]


def test_informacao_parada_e_vazio_geometrico():
    """c4/c9: ~10 s sem mudança; c1: casco escuro medido como 50% 'vazio' por pixels, mas a foto cobre o quadro."""
    from src.v4 import metricas as M
    assert M.parada_max([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0], .5) == 5.0
    assert M.parada_max([2, 2, 0, 2], .5) == .5
    det = {'params': {'wh': [1920, 1440], 'layout': 'cobrir', 'cam': [{'t': 0, 'caixa': [0.2, 0.0, 0.42, 1.0]}]}}
    assert M.vazio_geometrico(det, 0, 6) <= .01
