"""P0 do Plano Mestre: nenhuma saída automática do V3 com '0 bloqueios' e trava financeira efetiva."""
import json
import multiprocessing as mp
import os
import subprocess
import sys
import textwrap
from pathlib import Path

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


# ---------------------------------------------------------------- caixa: regras
RAT = 'humano:heitor:2026-11-16'


@pytest.fixture
def cx(tmp_path, monkeypatch):
    monkeypatch.delenv('CAIXA_RATIFICADO', raising=False)
    monkeypatch.delenv('CAIXA_ARMAZEM', raising=False)
    monkeypatch.setenv('CAIXA_PROVEDORES', json.dumps({'teste_pago': {'faturamento': 'pago'}}))
    caixa.abrir('teste', tmp_path, teto=0.80, alerta=0.60)
    yield tmp_path
    caixa.fechar()


def _reabrir(pasta, monkeypatch, ratificar=True, **kw):
    caixa.fechar()
    if ratificar:
        monkeypatch.setenv('CAIXA_RATIFICADO', RAT)
    return caixa.abrir('teste', pasta, **kw)


def test_sem_caixa_aberto_nao_interfere():
    assert not caixa.aberto()
    assert caixa.antes('cloudflare', 'x', None) is None
    assert caixa.operar('qualquer', 'x', lambda: 7) == 7


def test_pago_sem_ratificacao_negado_antes_de_chamar(cx):
    chamado = []
    with pytest.raises(caixa.OperacaoNegada, match='ratificado'):
        caixa.operar('teste_pago', 'x', lambda: chamado.append(1), pior_usd=.1, medidor=lambda r: .1)
    assert not chamado


def test_provedor_desconhecido_negado(cx):
    with pytest.raises(caixa.OperacaoNegada, match='sem faturamento'):
        caixa.antes('nvidia', 'roteiro', .01)


# ---------------------------------------------------------------- custo pago NÃO pode ser omitido
def test_pago_sem_medidor_e_negado_antes_de_chamar(cx, monkeypatch):
    _reabrir(cx, monkeypatch)
    chamado = []
    with pytest.raises(caixa.OperacaoNegada, match='não verificável'):
        caixa.operar('teste_pago', 'x', lambda: chamado.append(1), pior_usd=.1)
    assert not chamado and caixa.resumo()['cobrado_usd'] == 0


@pytest.mark.parametrize('pior', [None, 0, 0.0, -1])
def test_pior_caso_zero_ou_ausente_negado(cx, monkeypatch, pior):
    _reabrir(cx, monkeypatch)
    with pytest.raises(caixa.OperacaoNegada, match='pior caso positivo'):
        caixa.operar('teste_pago', 'x', lambda: 1, pior_usd=pior, medidor=lambda r: 0.0)


def test_cobranca_real_lida_pelo_medidor(cx, monkeypatch):
    _reabrir(cx, monkeypatch)
    caixa.operar('teste_pago', 'x', lambda: {'custo': .07}, pior_usd=.2, medidor=lambda r: r['custo'])
    r = caixa.resumo()
    assert r['cobrado_usd'] == .07 and r['reservas_abertas'] == 0 and not r['travado']


@pytest.mark.parametrize('medidor', [lambda r: None, lambda r: float('nan'), lambda r: -3, lambda r: 1 / 0, lambda r: True])
def test_medidor_que_nao_le_conta_pior_caso_e_trava(cx, monkeypatch, medidor):
    _reabrir(cx, monkeypatch)
    caixa.operar('teste_pago', 'x', lambda: {}, pior_usd=.25, medidor=medidor)
    r = caixa.resumo()
    assert r['cobrado_usd'] == .25 and r['travado']
    with pytest.raises(caixa.OperacaoNegada, match='travados'):
        caixa.operar('teste_pago', 'y', lambda: {}, pior_usd=.01, medidor=lambda r: 0.0)


def test_falha_da_chamada_paga_conta_pior_caso(cx, monkeypatch):
    _reabrir(cx, monkeypatch)

    def falha():
        raise RuntimeError('500 depois de processar')
    with pytest.raises(RuntimeError):
        caixa.operar('teste_pago', 'x', falha, pior_usd=.3, medidor=lambda r: 0.0)
    assert caixa.resumo()['cobrado_usd'] == .3 and caixa.resumo()['travado']


def test_depois_sem_cobranca_informada_nao_vira_zero(cx, monkeypatch):
    _reabrir(cx, monkeypatch)
    b = caixa.antes('teste_pago', 'x', .15, medidor=True)
    caixa.depois(b)                                           # quem chamou "esqueceu" a cobrança
    assert caixa.resumo()['cobrado_usd'] == .15


def test_gratis_que_cobra_e_bloqueado(cx):
    caixa.operar('gemini', 'tts', lambda: {'custo': .02}, medidor=lambda r: r['custo'])
    r = caixa.resumo()
    assert r['cobrado_usd'] == .02
    with pytest.raises(caixa.OperacaoNegada, match='bloqueado'):
        caixa.operar('gemini', 'tts', lambda: 1)


def test_cota_e_assinatura_sem_cobranca_mas_registradas(cx):
    caixa.operar('gemini', 'tts', lambda: 1)
    caixa.operar('claude_code', 'roteiro', lambda: 1, credito=lambda: 0.12)
    r = caixa.resumo()
    assert r['cobrado_usd'] == 0 and r['credito_usd'] == 0.12 and r['cota'] == {'gemini': 1} and r['chamadas'] == 2
    livro = caixa.fechar()
    assert len(livro['operacoes']) == 2                      # gravadas no fechamento
    caixa.abrir('teste', cx)


def test_teto_conta_reservas_e_futuros(cx, monkeypatch):
    _reabrir(cx, monkeypatch, teto=.80)
    caixa.operar('teste_pago', 'a', lambda: 1, pior_usd=.5, medidor=lambda r: .5)
    with pytest.raises(caixa.OperacaoNegada, match='teto'):
        caixa.operar('teste_pago', 'b', lambda: 1, pior_usd=.2, futuros_usd=.2, medidor=lambda r: .2)
    b = caixa.antes('teste_pago', 'b', .2, medidor=True)    # reserva aberta conta
    with pytest.raises(caixa.OperacaoNegada, match='teto'):
        caixa.antes('teste_pago', 'c', .15, medidor=True)
    caixa.depois(b, cobrado_usd=.1)


def test_tentativas_pagas_limitadas_por_etapa(cx, monkeypatch):
    monkeypatch.setattr(caixa, 'MAX_POR_ETAPA', 2)
    _reabrir(cx, monkeypatch)
    for _ in range(2):
        caixa.operar('teste_pago', 'imagem', lambda: 1, pior_usd=.01, medidor=lambda r: .01)
    with pytest.raises(caixa.OperacaoNegada, match='tentativas'):
        caixa.operar('teste_pago', 'imagem', lambda: 1, pior_usd=.01, medidor=lambda r: .01)


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


def test_corrida_local_duas_execucoes_mesmo_video(cx):
    fila = mp.get_context('fork').Queue()
    p = mp.get_context('fork').Process(target=_segunda, args=(cx, fila))
    p.start()
    p.join(20)
    assert fila.get(timeout=5) == 'ocupado'


# ---------------------------------------------------------------- caminho real das integrações (provedor simulado)
class _Resp:
    status_code, ok, text = 200, True, ''

    def json(self):
        return {'candidates': [{'content': {'parts': [{'inlineData': {'data': ''}}]}}]}


def test_imagem_cloudflare_bloqueada_mesmo_ratificada_sem_medidor(cx, monkeypatch):
    """imagens._uma → _klein → requests.post (Cloudflare simulado). Cobrança não verificável: o servidor nunca é chamado."""
    from src import imagens
    _reabrir(cx, monkeypatch)
    monkeypatch.setenv('CF_ACCOUNT_ID', 'x')
    monkeypatch.setenv('CF_API_TOKEN', 'y')
    servidor = []
    monkeypatch.setattr(imagens.requests, 'post', lambda *a, **k: servidor.append(a) or _Resp())
    monkeypatch.setattr(imagens.requests, 'get', lambda *a, **k: servidor.append(a) or _Resp())
    monkeypatch.setattr(imagens, '_pollinations', lambda *a: None)
    monkeypatch.setattr(imagens.time, 'sleep', lambda s: None)
    assert imagens._uma('p', None, 1, 'r') is None
    assert servidor == []
    neg = json.loads((cx / 'caixa_teste.json').read_text())['negadas']
    assert {n['provedor'] for n in neg} == {'cloudflare', 'gemini_imagem'} and all('não verificável' in n['motivo'] for n in neg)
    assert caixa.resumo()['cobrado_usd'] == 0


def test_gemini_texto_e_tts_param_se_declarados_pagos(cx, monkeypatch):
    """gemini._tentar e voz._rest_tts (HTTP simulado): com o Gemini declarado pago, nada sai — sem medidor de cobrança."""
    from src import gemini, voz
    monkeypatch.setenv('CAIXA_PROVEDORES', json.dumps({'gemini': {'faturamento': 'pago'}}))
    _reabrir(cx, monkeypatch)
    monkeypatch.setattr(gemini, 'CHAVES', ['k'])
    monkeypatch.setattr(gemini, '_esgotado', set())
    chamadas = []
    with pytest.raises(caixa.OperacaoNegada, match='não verificável'):
        gemini._tentar(lambda m: chamadas.append(m) or 'ok')
    import requests
    monkeypatch.setattr(requests, 'post', lambda *a, **k: chamadas.append(a) or _Resp())
    with pytest.raises(caixa.OperacaoNegada):
        voz._rest_tts('m', 'texto', 'Charon', 'novo', 'k')
    assert chamadas == []


def test_gemini_gratis_passa_e_conta_cota(cx, monkeypatch):
    from src import gemini
    monkeypatch.setattr(gemini, 'CHAVES', ['k'])
    monkeypatch.setattr(gemini, '_esgotado', set())
    monkeypatch.setattr(gemini.time, 'sleep', lambda s: None)
    assert gemini._tentar(lambda m: 'ok') == 'ok'
    assert caixa.resumo()['cota'] == {'gemini': 1} and caixa.resumo()['cobrado_usd'] == 0


def test_claude_assinatura_registra_credito_e_nao_cobranca(cx, monkeypatch):
    """claude.pedir com o CLI simulado: o custo equivalente vira CRÉDITO da assinatura, cobrança 0."""
    from src import claude

    class R:
        returncode, stderr = 0, ''
        stdout = json.dumps({'type': 'result', 'result': 'ok', 'total_cost_usd': 0.042, 'usage': {}})
    monkeypatch.setattr(claude.subprocess, 'run', lambda *a, **k: R())
    monkeypatch.setattr(claude, 'guardar_bruta', lambda s: None)
    assert claude.pedir('oi') == 'ok'
    r = caixa.resumo()
    assert r['credito_usd'] == 0.042 and r['cobrado_usd'] == 0


def test_toda_integracao_paga_no_codigo_tem_medidor_ou_e_negada():
    """Varre src/: toda chamada caixa.operar a provedor que cobra sem `medidor=` só pode ser negada (nunca registra 0)."""
    import ast
    achados = []
    for arq in Path('src').rglob('*.py'):
        for no in ast.walk(ast.parse(arq.read_text(encoding='utf-8'))):
            if isinstance(no, ast.Call) and getattr(no.func, 'attr', '') == 'operar' and getattr(no.func, 'value', None) is not None \
                    and getattr(no.func.value, 'id', '') == 'caixa':
                prov = no.args[0].value if no.args and isinstance(no.args[0], ast.Constant) else None
                tem_medidor = any(k.arg == 'medidor' for k in no.keywords)
                achados.append((str(arq), prov, tem_medidor))
    assert achados
    for arq, prov, med in achados:
        if prov is None:                                   # provedor escolhido em tempo de execução (imagens._uma)
            continue
        if caixa.faturamento(prov) in caixa.PAGOS:
            assert not med, f'{arq}: {prov} tem medidor — confira a leitura de cobrança antes de liberar'


# ---------------------------------------------------------------- reexecução independente (runners diferentes)
@pytest.fixture
def remoto(tmp_path):
    """Um repositório 'remoto' (bare) e dois clones independentes, como dois runners do Actions."""
    bare = tmp_path / 'remoto.git'
    subprocess.run(['git', 'init', '-q', '--bare', str(bare)], check=True)
    clones = []
    for nome in ('runner_a', 'runner_b'):
        d = tmp_path / nome
        subprocess.run(['git', 'clone', '-q', str(bare), str(d)], check=True, capture_output=True)
        clones.append(d)
    return bare, clones


_RUNNER = textwrap.dedent("""
    import json, os, sys, time
    sys.path.insert(0, {raiz!r})
    from pathlib import Path
    from src import caixa
    os.environ['CAIXA_RATIFICADO'] = 'humano:heitor:2026-11-16'
    os.environ['CAIXA_PROVEDORES'] = json.dumps({{'teste_pago': {{'faturamento': 'pago'}}}})
    caixa.ARRENDAMENTO_S = float(os.environ.get('ARR', '3600'))
    arm = caixa.ArmazemGit(Path({repo!r}), 'chave-de-teste')
    acao = {acao!r}
    try:
        caixa.abrir('londres', Path({repo!r}) / '_local', armazem=arm, teto=0.80)
    except caixa.CaixaOcupado as e:
        print('OCUPADO', e); sys.exit(0)
    try:
        if acao == 'gasta':
            caixa.operar('teste_pago', 'imagem', lambda: 1, pior_usd=.6, medidor=lambda r: .5)
        elif acao == 'morre':
            caixa.antes('teste_pago', 'imagem', .3, medidor=True)
            os._exit(0)                                     # runner morto no meio da chamada: sem depois(), sem fechar()
        elif acao == 'tenta':
            caixa.operar('teste_pago', 'imagem', lambda: 1, pior_usd=.4, medidor=lambda r: .4)
        elif acao == 'segura':
            time.sleep(float(os.environ.get('SEGURA', '4')))
        print('OK', json.dumps(caixa.resumo()))
    except caixa.OperacaoNegada as e:
        print('NEGADO', e)
    caixa.fechar()
""")


def _runner(repo, acao, **env):
    cod = _RUNNER.format(raiz=str(Path.cwd()), repo=str(repo), acao=acao)
    return subprocess.Popen([sys.executable, '-c', cod], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            env={**os.environ, **env})


def _rodar(repo, acao, **env):
    """Última linha da saída do runner (o alerta do caixa pode vir antes)."""
    return [l for l in _runner(repo, acao, **env).communicate(timeout=60)[0].splitlines() if l.strip()][-1]


def test_reexecucao_independente_ve_o_gasto_do_outro_runner(remoto):
    bare, (a, b) = remoto
    out_a = _rodar(a, 'gasta')
    assert out_a.startswith('OK') and '"cobrado_usd": 0.5' in out_a, out_a
    out_b = _rodar(b, 'tenta')          # outro clone, outro processo, nenhum arquivo em comum
    assert out_b.startswith('NEGADO') and 'teto' in out_b, out_b


def test_runner_morto_reserva_vira_gasto_e_arrendamento_segura(remoto):
    bare, (a, b) = remoto
    _runner(a, 'morre', ARR='3').communicate(timeout=60)              # arrendamento de 3 s, runner morre no meio
    out = _rodar(b, 'tenta')
    assert out.startswith('OCUPADO'), out                             # arrendamento do runner morto ainda vale
    import time
    time.sleep(3.2)
    out = _rodar(b, 'tenta')              # arrendamento vencido: abre
    assert out.startswith('OK') and '"cobrado_usd": 0.7' in out, out  # 0,30 da reserva abandonada (pior caso) + 0,40
    out = _rodar(a, 'tenta')              # 0,70 + 0,40 > 0,80
    assert out.startswith('NEGADO') and 'teto' in out, out


def test_duas_execucoes_simultaneas_em_runners_diferentes_so_uma_abre(remoto):
    bare, (a, b) = remoto
    pa = _runner(a, 'segura', SEGURA='5')
    pb = _runner(b, 'segura', SEGURA='5')
    saidas = sorted([pa.communicate(timeout=90)[0].split()[0], pb.communicate(timeout=90)[0].split()[0]])
    assert saidas == ['OCUPADO', 'OK'], saidas


def test_livro_remoto_e_cifrado(remoto):
    bare, (a, b) = remoto
    _runner(a, 'gasta').communicate(timeout=60)
    txt = subprocess.run(['git', '-C', str(bare), 'show', 'caixa-livro:londres.json.enc'], capture_output=True, text=True).stdout
    assert txt and 'cobrado' not in txt and 'teste_pago' not in txt
