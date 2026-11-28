"""E284: autorização de visão persistente entre execuções, sem reinício e contando tentativas externas."""
import pytest

from src.v4 import orcamento_visao as OV


def test_saldo_persiste_e_nao_reinicia(tmp_path):
    arm = OV.ArmazemLocal(tmp_path / 'aut.json')
    r = OV.abrir('aut', limite_logico=8, limite_operacoes=12, armazem=arm)
    assert r['saldo_logico'] == 8
    t = OV.reservar('aut', 'filmagem', armazem=arm)
    OV.liquidar('aut', t['id'], operacoes=2, tokens=100, armazem=arm)
    # "Nova execução": reabrir não zera
    r = OV.abrir('aut', limite_logico=8, limite_operacoes=12, armazem=OV.ArmazemLocal(tmp_path / 'aut.json'))
    assert r['logicas_consumidas'] == 1 and r['operacoes_consumidas'] == 2 and r['saldo_logico'] == 7
    with pytest.raises(RuntimeError, match='DIVERGENTES'):
        OV.abrir('aut', limite_logico=16, limite_operacoes=12, armazem=arm)


def test_reserva_orfa_conta_no_pior_caso_e_operacoes_limitam(tmp_path):
    arm = OV.ArmazemLocal(tmp_path / 'a.json')
    OV.abrir('a', limite_logico=8, limite_operacoes=5, max_operacoes_por_chamada=2, armazem=arm)
    OV.reservar('a', 'x', armazem=arm)                      # execução morreu sem liquidar
    t = OV.reservar('a', 'x', armazem=arm)
    OV.liquidar('a', t['id'], operacoes=2, ok=False, motivo='JSON_INVALIDO', armazem=arm)
    r = OV.saldo('a', armazem=arm)
    assert r['logicas_consumidas'] == 2 and r['operacoes_consumidas'] == 4 and r['reservas_nao_liquidadas'] == 1
    with pytest.raises(OV.SaldoEsgotado):                    # 1 operação restante < pior caso 2
        OV.reservar('a', 'x', armazem=arm)


def test_limite_por_finalidade(tmp_path):
    arm = OV.ArmazemLocal(tmp_path / 'f.json')
    OV.abrir('f', limite_logico=8, limite_operacoes=16, armazem=arm)
    for _ in range(2):
        t = OV.reservar('f', 'filmagem_acao', limite_finalidade=2, armazem=arm)
        OV.liquidar('f', t['id'], operacoes=1, armazem=arm)
    with pytest.raises(OV.SaldoEsgotado, match='FINALIDADE'):
        OV.reservar('f', 'filmagem_acao', limite_finalidade=2, armazem=arm)
    assert OV.reservar('f', 'geleiras', limite_finalidade=6, armazem=arm)


def test_teto_de_tentativas_do_provedor(monkeypatch):
    from src import gemini
    monkeypatch.setenv('CORINGA_VISAO_MAX_TENTATIVAS', '2')
    monkeypatch.setattr(gemini, 'CHAVES', ['k1', 'k2'])
    monkeypatch.setattr(gemini.time, 'sleep', lambda *_: None)
    n = []

    def falha(modelo):
        n.append(modelo)
        raise RuntimeError('503 UNAVAILABLE')
    with pytest.raises(RuntimeError):
        gemini._tentar(falha, ['m1', 'm2', 'm3'])
    assert len(n) == 2
