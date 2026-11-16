"""Render de referência no Actions: material cifrado para o workflow, prévia PRIVADA ao Telegram (não é publicação)."""
import importlib.util
import json
from pathlib import Path

import pytest

from src.v3 import estado_final as EF
from src.v3 import material, previa_telegram as PT


def test_material_so_quem_tem_o_segredo_decifra():
    pub = material.publica('segredo-do-workflow')
    blob = material.cifrar(pub, b'narracao' * 1000)
    assert material.decifrar('segredo-do-workflow', blob) == b'narracao' * 1000
    assert b'narracao' not in blob
    with pytest.raises(Exception):
        material.decifrar('outro-segredo', blob)
    assert material.publica('segredo-do-workflow') == pub          # derivação determinística


def test_previa_separada_de_publicacao():
    for st in EF.ESTADOS:
        assert EF.pode_enviar_previa({'estado': st})
    assert not EF.pode_enviar_previa({'estado': 'APROVADO_FISCAL'}) and not EF.pode_enviar_previa({})
    assert not EF.pode_publicar({'estado': EF.AGUARDANDO}) and not EF.pode_publicar({'estado': EF.BLOQUEADO})
    assert EF.pode_enviar is EF.pode_publicar


class _R:
    def __init__(self, result, ok=True):
        self.ok, self.status_code, self.text, self._r = ok, 200 if ok else 400, '', result

    def json(self):
        return {'result': self._r}


@pytest.fixture
def tg(monkeypatch, tmp_path):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'tok')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '12345')
    chamadas = []
    tipo = {'v': 'private'}

    def post(url, data=None, files=None, timeout=None):
        metodo = url.rsplit('/', 1)[1]
        chamadas.append((metodo, dict(data or {})))
        return _R({'type': tipo['v']} if metodo == 'getChat' else {})
    monkeypatch.setattr(PT.requests, 'post', post)
    mp4 = tmp_path / 'v.mp4'
    mp4.write_bytes(b'0' * 1000)
    return chamadas, tipo, mp4


def test_previa_vai_so_ao_chat_privado_autorizado_com_status(tg):
    chamadas, tipo, mp4 = tg
    r = PT.enviar(mp4, {'estado': EF.AGUARDANDO, 'pendencias': ['x']}, 'Londres', 'relatório')
    assert [m for m, _ in chamadas] == ['getChat', 'sendVideo', 'sendMessage']
    assert {d['chat_id'] for _, d in chamadas} == {'12345'}
    leg = chamadas[1][1]['caption']
    assert 'PRÉVIA PRIVADA — NÃO PUBLICADO' in leg and 'AGUARDANDO_APROVACAO_HUMANA' in leg and r['mensagens'] == 1


def test_previa_de_video_bloqueado_tambem_vai_com_status(tg):
    chamadas, tipo, mp4 = tg
    PT.enviar(mp4, {'estado': EF.BLOQUEADO, 'motivos': ['G-BORDA']}, 'Londres', 'r')
    assert 'STATUS: BLOQUEADO' in chamadas[1][1]['caption'] and 'G-BORDA' in chamadas[1][1]['caption']


@pytest.mark.parametrize('chat', ['-100123', '-55', 'meu_canal', ''])
def test_recusa_grupo_canal_ou_sem_chat(tg, monkeypatch, chat):
    chamadas, tipo, mp4 = tg
    monkeypatch.setenv('TELEGRAM_CHAT_ID', chat)
    with pytest.raises(PT.EnvioRecusado):
        PT.enviar(mp4, {'estado': EF.AGUARDANDO}, 'x', 'r')
    assert not [m for m, _ in chamadas if m.startswith('send')]


def test_recusa_se_o_telegram_disser_que_nao_e_privado(tg):
    chamadas, tipo, mp4 = tg
    tipo['v'] = 'group'
    with pytest.raises(PT.EnvioRecusado, match='não é privado'):
        PT.enviar(mp4, {'estado': EF.AGUARDANDO}, 'x', 'r')
    assert [m for m, _ in chamadas] == ['getChat']


def test_recusa_estado_desconhecido(tg):
    chamadas, tipo, mp4 = tg
    with pytest.raises(PT.EnvioRecusado):
        PT.enviar(mp4, {'estado': 'APROVADO_FISCAL'}, 'x', 'r')
    assert chamadas == []


def test_render_bloqueia_qualquer_ia_e_relatorio_traz_status_fiscal_e_custos(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('render_londres', Path('scripts/render_londres.py'))
    rl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rl)
    from src import caixa
    with caixa.video('teste-render', tmp_path):
        for prov in ('claude_code', 'gemini', 'groq', 'pollinations'):
            with pytest.raises(caixa.OperacaoNegada):
                caixa.operar(prov, 'x', lambda: 1)
        cx = caixa.resumo()
    assert cx['chamadas'] == 0 and cx['cobrado_usd'] == 0 and cx['negadas'] == 4
    mp4 = tmp_path / 'l.mp4'
    mp4.write_bytes(b'0' * 2048)
    est = {'estado': EF.AGUARDANDO, 'pendencias': ['revisão multimodal sem visão disponível (pendente)']}
    fis = {'bloqueios': 0, 'revisoes': 1, 'esteticas': 3, 'audio': {'lufs': -14.4, 'pico_dbtp': -1.6}, 'video': {'duracao': 64.6}}
    txt = rl.relatorio(est, fis, cx, 180, mp4, [{'classe': 'revisao', 'inicio': 38.1, 'codigo': 'G-ZOOM-RAPIDO', 'problema': 'zoom'}])
    for trecho in ('STATUS: AGUARDANDO_APROVACAO_HUMANA', 'não publicado', 'G-ZOOM-RAPIDO', 'cobrança efetiva: US$ 0.00',
                   'chamadas de IA: 0', '-14.4 LUFS', 'PENDÊNCIAS'):
        assert trecho in txt, trecho
