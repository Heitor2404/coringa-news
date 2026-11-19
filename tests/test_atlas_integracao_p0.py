"""Regressoes ATLAS P0: voz sem troca silenciosa e portao editorial V3.

Tudo offline: nao gera voz, nao renderiza MP4, nao chama Claude/Gemini/Telegram.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import voz
from src.v3 import estado_final
from src.v4.formatos import estado, plano as P, produzir


def _resultado(mp4: Path) -> dict:
    return {
        'estado': 'AGUARDANDO_APROVACAO_HUMANA',
        'mp4': str(mp4),
        'nao_publicado': True,
        'motivos_bloqueio': [],
        'portoes': {
            'preto_ou_congelado': [],
            'audio_ok': True,
            'ritmo_ok': True,
            'legenda_ok': True,
        },
    }


def test_atlas_tem_narrador_pinado_sem_fallback():
    p = P.canal('coringa')['narrador']
    assert p['motor'] == 'gemini'
    assert p['voz'] == 'Charon'
    assert p['fallback'] == 'bloquear'


def test_sem_chave_gemini_nao_cai_para_edge(monkeypatch, tmp_path):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)

    def edge_proibido(*args, **kwargs):
        pytest.fail('Edge NAO pode ser chamado em ATLAS')

    monkeypatch.setattr(voz, '_narrar_edge', edge_proibido)
    with pytest.raises(RuntimeError, match='Edge não autorizada'):
        voz.narrar([{'fala': 'Teste.'}], tmp_path, cfg={'voz_motor': 'gemini', 'voz_gemini': 'Charon'},
                   exigir_gemini=True)


def test_falha_gemini_nao_cai_para_edge(monkeypatch, tmp_path):
    monkeypatch.setenv('GEMINI_API_KEY', 'teste-offline-nao-real')

    def gemini_indisponivel(*args, **kwargs):
        raise RuntimeError('serviço indisponível')

    monkeypatch.setattr(voz, '_narrar_gemini', gemini_indisponivel)
    monkeypatch.setattr(voz, '_narrar_edge', lambda *args, **kwargs: pytest.fail('fallback nao autorizado'))
    with pytest.raises(RuntimeError, match='não substituo a voz'):
        voz.narrar([{'fala': 'Teste.'}], tmp_path, cfg={'voz_motor': 'gemini', 'voz_gemini': 'Charon'},
                   exigir_gemini=True)


def test_motores_antigos_continuam_com_fallback_sem_flag(monkeypatch, tmp_path):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    esperado = ('edge-teste', [], [], 1.0)
    monkeypatch.setattr(voz, '_narrar_edge', lambda *args: esperado)
    assert voz.narrar([{'fala': 'Teste.'}], tmp_path) == esperado


def test_atlas_narrar_registra_provedor_e_hash_sem_gerar_voz(monkeypatch, tmp_path):
    from src.v4.formatos import legenda_sync

    chamadas = []

    def narrar_falso(cenas, pasta, *, cfg, exigir_gemini):
        chamadas.append((cenas, cfg, exigir_gemini))
        pasta.mkdir(parents=True, exist_ok=True)
        p = pasta / 'voz.wav'
        p.write_bytes(b'voz-falsa-para-teste-sem-audio')
        caps = [{'words': [{'w': 'TESTE', 's': 0.05}], 'end': 1.0}]
        return p, [], caps, 1.0

    monkeypatch.setattr(voz, 'narrar', narrar_falso)
    monkeypatch.setattr(legenda_sync, 'realinhar', lambda palavras, wav: palavras)
    r = produzir.narrar({'formato': 'atlas', 'canal': 'coringa',
                         'narracao': {'texto': 'Teste.'}}, tmp_path / 'out')
    assert chamadas and chamadas[0][2] is True
    assert chamadas[0][1]['voz_motor'] == 'gemini'
    assert chamadas[0][1]['voz_gemini'] == 'Charon'
    assert chamadas[0][1]['_estilo_separado'] is True
    assert r['narrador']['motor'] == 'gemini'
    assert r['narrador']['fallback'] == 'proibido'
    assert len(r['sha256_voz']) == 64


def test_gate_bloqueia_mesmo_com_job_render_verde(tmp_path):
    mp4 = tmp_path / 'existe.mp4'
    mp4.write_bytes(b'mp4-apenas-sentinela')
    r = _resultado(mp4)
    r['motivos_bloqueio'] = ['G-MP4-JANELA 36.0-40.0s congelada']
    r['estado'] = 'BLOQUEADO'
    assert estado.avaliar(r)['estado'] == estado_final.BLOQUEADO


def test_gate_nao_confia_no_status_declarado(tmp_path):
    mp4 = tmp_path / 'existe.mp4'
    mp4.write_bytes(b'mp4-apenas-sentinela')
    r = _resultado(mp4)
    r['portoes']['ritmo_ok'] = False
    e = estado.avaliar(r)
    assert e['estado'] == estado_final.BLOQUEADO
    assert any('RITMO_OK' in m for m in e['motivos'])
    r['estado'] = 'APROVADO_HUMANO'
    assert estado.avaliar(r)['estado'] == estado_final.BLOQUEADO


def test_sem_mp4_ou_resultado_falha_fechado(tmp_path):
    e = estado.conferir(tmp_path / 'sem-resultado')
    assert e['estado'] == estado_final.BLOQUEADO
    reg = json.loads((tmp_path / 'sem-resultado' / 'estado_editorial.json').read_text())
    assert reg['estado'] == estado_final.BLOQUEADO


def test_gate_somente_deixa_aguardando_humano(tmp_path):
    mp4 = tmp_path / 'existe.mp4'
    mp4.write_bytes(b'mp4-apenas-sentinela')
    r = _resultado(mp4)
    e = estado.avaliar(r)
    assert e['estado'] == estado_final.AGUARDANDO
    assert not estado_final.pode_publicar(e)
    assert any('multimodal' in x for x in e['pendencias'])


def test_workflow_tem_gate_depois_da_previa_privada():
    src = (Path(__file__).resolve().parents[1] / '.github/workflows/formatos-piloto.yml').read_text()
    assert src.index('Prévias PRIVADAS ao Telegram') < src.index('Portao editorial final')
    assert src.index('Portao editorial final') < src.index('Cifrar e publicar no ramo de resultado')
    assert 'python -m src.v4.formatos gate "$PLANO_ATLAS"' in src
    assert 'if: always()' in src
