"""P0 do Plano Mestre: nenhuma saída automática do V3 com '0 bloqueios' e trava financeira efetiva."""
import json
import multiprocessing as mp

import pytest

from src import caixa
from src.v3 import estado_final as EF


# ---------------------------------------------------------------- estado final / publicação
def _mp4(tmp_path):
    f = tmp_path / 'v.mp4'
    f.write_bytes(b'x' * 10)
    return str(f)


def test_zero_bloqueios_aguarda_humano_nunca_publicavel(tmp_path):
    e = EF.decidir({'mp4': _mp4(tmp_path), 'bloqueios': [], 'revisoes': [], 'revisao_multimodal': {'chamadas': 12}})
    assert e['estado'] == EF.AGUARDANDO
    assert not EF.pode_enviar(e)


def test_bloqueio_e_mp4_ausente_bloqueiam(tmp_path):
    assert EF.decidir({'mp4': _mp4(tmp_path), 'bloqueios': ['x']})['estado'] == EF.BLOQUEADO
    assert EF.decidir({'mp4': str(tmp_path / 'nao.mp4'), 'bloqueios': []})['estado'] == EF.BLOQUEADO
    assert EF.decidir({'mp4': None, 'bloqueios': []})['estado'] == EF.BLOQUEADO


def test_multimodal_ausente_ou_sem_visao_fica_pendente(tmp_path):
    e = EF.decidir({'mp4': _mp4(tmp_path), 'bloqueios': []})
    assert e['estado'] == EF.AGUARDANDO and any('multimodal' in p for p in e['pendencias'])
    e = EF.decidir({'mp4': _mp4(tmp_path), 'bloqueios': [], 'revisao_multimodal': {'chamadas': 0}})
    assert any('sem visão' in p for p in e['pendencias'])


def test_revisoes_obrigatorias_aparecem_como_pendencia(tmp_path):
    e = EF.decidir({'mp4': _mp4(tmp_path), 'bloqueios': [], 'revisoes_obrigatorias': ['plano 3 (X): y'],
                    'revisao_multimodal': {'chamadas': 3}})
    assert e['pendencias'] == ['plano 3 (X): y']


def test_publicavel_so_com_aprovacao_humana_e_autorizacao(tmp_path):
    e = EF.decidir({'mp4': _mp4(tmp_path), 'bloqueios': [], 'revisao_multimodal': {'chamadas': 1}})
    with pytest.raises(ValueError):
        EF.liberar_publicacao(e, 'humano:heitor:2026-11-16')          # pular a aprovação
    with pytest.raises(ValueError):
        EF.aprovar_humano(e, 'fiscal-automatico', 'v.mp4')            # aprovação não humana
    a = EF.aprovar_humano(e, 'humano:heitor:2026-11-16', 'v.mp4')
    assert a['estado'] == EF.APROVADO and not EF.pode_enviar(a)
    with pytest.raises(ValueError):
        EF.liberar_publicacao(a, '')
    assert EF.pode_enviar(EF.liberar_publicacao(a, 'humano:heitor:2026-11-16'))


def test_main_v3_nao_envia_telegram_sem_publicavel(monkeypatch, tmp_path):
    import main
    enviados = []
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 't')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'c')
    monkeypatch.setattr(main, '_tg', lambda *a, **k: enviados.append(a) or True)
    arq = tmp_path / 'v.mp4'
    arq.write_bytes(b'x')
    main.telegram(arq, 'legenda', {'_estado_final': {'estado': EF.AGUARDANDO}})
    assert enviados == []


def test_main_v3_estado_no_status(monkeypatch, tmp_path):
    import main
    monkeypatch.setenv('MOTOR_VISUAL', 'v3')
    arq = tmp_path / 'v.mp4'
    arq.write_bytes(b'x')
    main._status_v2(tmp_path, EF.AGUARDANDO, {}, mp4=arq, motivo='pendente')
    assert json.loads((tmp_path / 'status_execucao.json').read_text())['status'] == EF.AGUARDANDO
    main._status_v2(tmp_path, EF.AGUARDANDO, {}, mp4=tmp_path / 'nao.mp4')
    assert json.loads((tmp_path / 'status_execucao.json').read_text())['status'] == 'FALHA_OPERACIONAL'


# ---------------------------------------------------------------- caixa
@pytest.fixture
def cx(tmp_path, monkeypatch):
    monkeypatch.delenv('CAIXA_RATIFICADO', raising=False)
    monkeypatch.delenv('CAIXA_PROVEDORES', raising=False)
    caixa.abrir('teste', tmp_path, teto=0.80, alerta=0.60)
    yield tmp_path
    caixa.fechar()


def test_sem_caixa_aberto_nao_interfere():
    assert not caixa.aberto()
    assert caixa.antes('cloudflare', 'x', None) is None
    assert caixa.operar('qualquer', 'x', lambda: 7) == 7


def test_pago_sem_ratificacao_negado(cx):
    with pytest.raises(caixa.OperacaoNegada, match='ratificado'):
        caixa.antes('cloudflare', 'imagem', 0.01)


def test_provedor_desconhecido_negado(cx):
    with pytest.raises(caixa.OperacaoNegada, match='sem faturamento'):
        caixa.antes('nvidia', 'roteiro', 0.0)


def test_cota_e_assinatura_registram_sem_cobranca(cx):
    caixa.operar('gemini', 'tts', lambda: 1)
    caixa.operar('claude_code', 'roteiro', lambda: 1, credito=lambda: 0.12)
    r = caixa.resumo()
    assert r['cobrado_usd'] == 0 and r['credito_usd'] == 0.12 and r['cota'] == {'gemini': 1}


def test_custo_desconhecido_negado(cx, monkeypatch):
    monkeypatch.setenv('CAIXA_RATIFICADO', 'humano:heitor:2026-11-16')
    caixa.fechar()
    caixa.abrir('teste', cx)
    with pytest.raises(caixa.OperacaoNegada, match='desconhecido'):
        caixa.antes('cloudflare', 'imagem', None)


def test_orcamento_esgotado_e_futuros_reservados(cx, monkeypatch):
    monkeypatch.setenv('CAIXA_RATIFICADO', 'humano:heitor:2026-11-16')
    caixa.fechar()
    caixa.abrir('teste', cx, teto=0.80)
    b = caixa.antes('cloudflare', 'a', 0.50)
    caixa.depois(b, cobrado_usd=0.50)
    with pytest.raises(caixa.OperacaoNegada, match='teto'):
        caixa.antes('cloudflare', 'b', 0.20, futuros_usd=0.20)     # 0,50 + 0,20 + 0,20 > 0,80
    caixa.antes('cloudflare', 'b', 0.20)                            # 0,70 cabe


def test_api_falha_tambem_conta_e_persiste_entre_execucoes(cx, monkeypatch):
    monkeypatch.setenv('CAIXA_RATIFICADO', 'humano:heitor:2026-11-16')
    caixa.fechar()
    caixa.abrir('teste', cx)

    def falha():
        raise RuntimeError('500')
    with pytest.raises(RuntimeError):
        caixa.operar('cloudflare', 'imagem', falha, pior_usd=0.10)
    b = caixa.antes('cloudflare', 'imagem', 0.10)
    caixa.depois(b, ok=True, cobrado_usd=0.30)
    n = caixa.fechar()['execucoes']
    c = caixa.abrir('teste', cx)                                     # retry/job novo: retoma o total gasto
    assert c['cobrado_usd'] == 0.30 and c['execucoes'] == n + 1
    assert [o['ok'] for o in c['operacoes']] == [False, True]


def test_tentativas_pagas_limitadas_por_etapa(cx, monkeypatch):
    monkeypatch.setenv('CAIXA_RATIFICADO', 'humano:heitor:2026-11-16')
    monkeypatch.setattr(caixa, 'MAX_POR_ETAPA', 2)
    caixa.fechar()
    caixa.abrir('teste', cx)
    for _ in range(2):
        caixa.depois(caixa.antes('cloudflare', 'imagem', 0.01))
    with pytest.raises(caixa.OperacaoNegada, match='tentativas'):
        caixa.antes('cloudflare', 'imagem', 0.01)


def test_limite_de_chamadas_e_tempo(cx, monkeypatch):
    monkeypatch.setattr(caixa, 'MAX_CHAMADAS', 1)
    caixa.operar('gemini', 'x', lambda: 1)
    with pytest.raises(caixa.OperacaoNegada, match='chamadas'):
        caixa.antes('gemini', 'x')
    monkeypatch.setattr(caixa, 'MAX_CHAMADAS', 99)
    monkeypatch.setattr(caixa, 'MAX_SEGUNDOS', -1)
    with pytest.raises(caixa.OperacaoNegada, match='tempo'):
        caixa.antes('gemini', 'x')


def _segunda(pasta, fila):
    try:
        caixa.abrir('teste', pasta)
        fila.put('abriu')
    except caixa.CaixaOcupado:
        fila.put('ocupado')


def test_corrida_duas_execucoes_mesmo_video(cx):
    fila = mp.get_context('fork').Queue()
    p = mp.get_context('fork').Process(target=_segunda, args=(cx, fila))
    p.start()
    p.join(20)
    assert fila.get(timeout=5) == 'ocupado'


def test_gemini_nao_insiste_quando_caixa_nega(cx, monkeypatch):
    from src import gemini
    monkeypatch.setenv('CAIXA_PROVEDORES', json.dumps({'gemini': {'faturamento': 'desconhecido'}}))
    monkeypatch.setattr(gemini, 'CHAVES', ['k'])
    monkeypatch.setattr(gemini, '_esgotado', set())
    chamadas = []
    with pytest.raises(caixa.OperacaoNegada):
        gemini._tentar(lambda m: chamadas.append(m) or 'ok')
    assert chamadas == []


def test_imagem_paga_pulada_sem_ratificacao(cx, monkeypatch):
    from src import imagens
    usados = []
    monkeypatch.setattr(imagens, '_klein', lambda *a: usados.append('flux2') or b'x')
    monkeypatch.setattr(imagens, '_schnell', lambda *a: usados.append('schnell') or b'x')
    monkeypatch.setattr(imagens, '_pollinations', lambda *a: usados.append('poll') or b'img')
    assert imagens._uma('p', None, 1, 'r') == b'img'
    assert usados == ['poll']
