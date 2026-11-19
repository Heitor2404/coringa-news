"""ATLAS P1 — testes sem rede/IA para imagem protagonista e clipe real do V4.

Teste unitário cobre: contrato de mídia, falha fechada, proveniência, crédito e
reuso do backend FFmpeg existente. Não depende de vídeos externos.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from src.v4.formatos import plano as P, produzir
from src.v4 import viabilidade


ROOT = Path(__file__).resolve().parents[1]
ATLAS = json.loads((ROOT / 'tests/dados/formatos_atlas_resolvido.json').read_text())


def _video(t0=10.0, t1=12.0, inicio=0.0):
    return {'componente': 'registro.video', 't0': t0, 't1': t1,
            'params': {'asset': 'video:licenciado', 'inicio': inicio}}


def _imgs(tipo='video', duracao=9.0):
    return {'video:licenciado': {'src': '_formato/m_video.mp4', 'w': 1920, 'h': 1080,
                                  'tipo': tipo, 'duracao': duracao, 'credito': 'Autoria · CC BY 4.0'}}


def _codigos(pl, imgs=None):
    # Mesmo caminho do motor: a câmera/slots são reconstruídos dos beats.
    resolvido = P.resolver_tempos(copy.deepcopy(pl), [])
    return {v['regra'] for v in P.validar(resolvido, imgs) if v['gravidade'] == 'erro'}


def test_catalogo_tem_prova_documental_sem_mudar_dossie():
    assert 'atlas.provaVisual' in P.CFG['formatos']['atlas']['componentes']
    assert 'registro.video' in P.CFG['formatos']['atlas']['clipes']
    assert 'atlas.prova' in P.COMP and P.COMP['atlas.prova']['formato'] == 'atlas'
    assert 'atlas.provaVisual' not in P.CFG['formatos']['dossie']['componentes']
    assert 'registro.video' not in P.CFG['formatos']['dossie']['clipes']


def test_video_real_falha_fechado_se_ausente_ou_com_tipo_errado():
    pl = copy.deepcopy(ATLAS)
    pl['clipes'].append(_video())
    assert 'F-ASSET' in _codigos(pl, {})
    assert 'F-VIDEO-TIPO' in _codigos(pl, _imgs(tipo='foto'))
    pl['clipes'][-1]['params']['inicio'] = 9
    assert 'F-VIDEO-DURACAO' in _codigos(pl, _imgs())


def test_clipe_nao_pode_ocultar_camadas_do_storyboard():
    pl = copy.deepcopy(ATLAS)
    pl['clipes'].append(_video())
    # Adiciona propositalmente camada sob um clipe que irá substituir o palco.
    pl['beats'][0]['camadas'].append({
        'id': 'invisivel', 'componente': 'editorial.titleOrPayoff', 'slot': 'pergunta',
        't0': 10.3, 't1': 11.5, 'p': {'linhas': [{'texto': 'PARE'}]},
    })
    assert 'F-VIDEO-SOBREPOE-CAMADA' in _codigos(pl, _imgs())


def test_video_rejeita_configuracao_invalida():
    for ini in (-1, 'zero', True):
        pl = copy.deepcopy(ATLAS)
        pl['clipes'].append(_video(inicio=ini))
        assert 'F-VIDEO-PARAMS' in _codigos(pl)
    pl = copy.deepcopy(ATLAS)
    pl['clipes'].append({**_video(), 'fonte': {'ini': 2, 'dur': 5}})
    assert 'F-VIDEO-PARAMS' in _codigos(pl)


def test_video_recebe_selo_registro_e_credito_na_faixa_inferior():
    pl = copy.deepcopy(ATLAS)
    pl['clipes'].append(_video(t0=10, t1=12))
    meta = {'palavras': []}
    props = P.props_camada(pl, meta, _imgs())
    ativo = next(c for c in props['cenas'] if c['ini'] == 10 and c['fim'] == 12)
    assert ativo['selo'] == 'REGISTRO'
    assert ativo['credito'] == 'Autoria · CC BY 4.0'
    assert props['credito_caixa'] == P.zonas('atlas')['creditos']


def test_imagem_principal_exige_credito_e_tipo_correto():
    pl = copy.deepcopy(ATLAS)
    pl['beats'][0]['camadas'].append({
        'id': 'prova-sem-credito', 'componente': 'atlas.provaVisual', 'slot': 'pergunta',
        't0': 5, 't1': 6, 'p': {'asset': 'video:licenciado'},
    })
    assert 'F-PROVA-CREDITO' in _codigos(pl, _imgs(tipo='foto'))
    pl['beats'][0]['camadas'][-1]['p']['meta'] = 'Autor · CC BY 4.0'
    assert 'F-PROVA-TIPO' in _codigos(pl, _imgs(tipo='video'))


def test_ativos_reutiliza_hash_origem_e_probe_v4(monkeypatch, tmp_path):
    import src.v4.formatos.produzir as prod

    original = tmp_path / 'original.mp4'
    # Video sintético produzido no teste; nenhum conteúdo de terceiros.
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi',
                    '-i', 'testsrc2=size=640x1136:rate=12', '-t', '0.8', '-an',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', str(original)], check=True)
    bruto = original.read_bytes()
    sha = hashlib.sha256(bruto).hexdigest()
    item = {'id': 'video:licenciado', 'natureza': 'video', 'uso_comercial': 'sim',
            'sha256_origem': sha, 'url': 'https://arquivo.exemplo/video.mp4',
            'credito': 'Autor de teste · CC BY 4.0', 'licenca': 'CC BY 4.0',
            'prova': {'midia_corresponde': True}}
    monkeypatch.setattr(viabilidade, 'carregar', lambda: {'itens': [item]})
    monkeypatch.setattr(prod, '_origem', lambda it, cache: (bruto, 'cache:teste.mp4'))
    monkeypatch.setattr(prod, 'PUBLICO', tmp_path / 'public' / '_formato')
    pl = {'beats': [], 'clipes': [_video(t0=3, t1=3.7)], 'rasters': []}
    data = prod.ativos(pl, tmp_path / 'saida')
    reg = data['video:licenciado']
    assert reg['tipo'] == 'video' and reg['duracao'] > .75
    assert reg['origem_conferida'] is True
    assert reg['sha256_origem'] == sha
    assert (tmp_path / 'public' / reg['src']).is_file()
    assert (tmp_path / 'saida' / 'ativos' / Path(reg['src']).name).is_file()
    # Prova o render de um clipe REAL pelo backend FFmpeg existente, sem mock e sem rede.
    from src.v4.util import sondar
    trecho = _video(t0=3, t1=3.45, inicio=.1)
    renderizado = tmp_path / 'corte_real.mp4'
    prod._clipe(trecho, {'canal': 'coringa'}, tmp_path / 'render_ffmpeg', renderizado, data)
    info = sondar(renderizado)
    assert info['w'] == 1080 and info['h'] == 1920
    assert 0.40 <= info['duracao'] <= 0.55
    assert info['audio'] is False


def test_sem_sha_ou_licenca_nao_importa_video(monkeypatch, tmp_path):
    import src.v4.formatos.produzir as prod
    for campo in ('sha256_origem', 'uso_comercial'):
        item = {'id': 'video:licenciado', 'natureza': 'video', 'uso_comercial': 'sim',
                'sha256_origem': 'a' * 64, 'url': 'https://arquivo.exemplo/video.mp4',
                'credito': 'Autor · CC BY 4.0', 'licenca': 'CC BY 4.0'}
        item.pop(campo)
        monkeypatch.setattr(viabilidade, 'carregar', lambda: {'itens': [item]})
        monkeypatch.setattr(prod, '_origem', lambda it, cache: (b'arquivo-sintetico', 'cache'))
        monkeypatch.setattr(prod, 'PUBLICO', tmp_path / 'public' / '_formato')
        pl = {'beats': [], 'clipes': [_video(t0=3, t1=4)], 'rasters': []}
        with pytest.raises(RuntimeError):
            prod.ativos(pl, tmp_path / 'saida')


def test_render_de_video_usa_backend_existente_sem_efeito(monkeypatch, tmp_path):
    import src.v4.formatos.produzir as prod
    from src.v4.backends import legado

    public = tmp_path / 'public'
    public.mkdir()
    (public / 'video.mp4').write_bytes(b'video-teste')
    monkeypatch.setattr(prod, 'PUBLICO', public / '_formato')
    chamadas = []

    def render_video(arq, wh, roi, ini, dur, saida, trab):
        chamadas.append((str(arq), wh, roi, ini, dur))
        saida.write_bytes(b'video-normalizado')
        return {'backend': 'ffmpeg'}

    monkeypatch.setattr(legado, 'render_video', render_video)
    asset = {'video:licenciado': {'src': 'video.mp4', 'w': 640, 'h': 1136, 'tipo': 'video'}}
    prod._clipe(_video(t0=4, t1=6.5, inicio=.2), {'canal': 'coringa'},
                tmp_path / 'render', tmp_path / 'output.mp4', asset)
    assert chamadas == [(str(public / 'video.mp4'), [640, 1136], None, .2, 2.5)]


def test_codigo_renderer_conta_com_componente_grande_e_credito_seguro():
    tsx = (ROOT / 'motor4/remotion/src/formatos/Primitivas.tsx').read_text()
    camada = (ROOT / 'motor4/remotion/src/Camada.tsx').read_text()
    assert "'atlas.provaVisual': ProvaVisual" in tsx
    assert 'objectFit: p.enquadramento' in tsx
    assert 'credito_caixa' in camada
