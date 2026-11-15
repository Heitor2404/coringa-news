"""V2.5 — matriz multinicho (src/v2/matriz.py), fluxo real offline com renderização da prévia.
DEV: assuntos usados na correção → precisam passar todos. VAL: assuntos inéditos, expectativa escrita antes de rodar;
a 1ª rodada deu 29/33 (as 4 diferenças são revisões humanas conservadoras, documentadas em CORRECAO_V25_GERAL.md).
O teste impede REGRESSÃO de VAL, mas não força VAL a 100% (não se ajusta o código a um assunto reservado)."""
import pytest

from src.v2 import matriz

pytest.importorskip('playwright')


@pytest.fixture(scope='module')
def resultado(tmp_path_factory):
    return matriz.rodar(tmp_path_factory.mktemp('matriz'))


def test_matriz_tem_8_grupos_e_40_cenarios(resultado):
    grupos = {c['grupo'] for c in resultado['cenarios']}
    assert resultado['total'] >= 40 and {'ciencia', 'natureza', 'historia', 'geografia', 'espaco', 'engenharia', 'numeros', 'pessoas', 'misto'} <= grupos
    assert sum(1 for c in resultado['cenarios'] if 'bloqueia' in c['esperado']) >= 15          # casos negativos


def test_dev_todos_passam(resultado):
    falhas = [(c['id'], c['resultado'], c['bloqueios'][:1] + c['revisoes'][:1]) for c in resultado['cenarios'] if c['conjunto'] == 'dev' and not c['passou']]
    assert not falhas, falhas


def test_val_sem_regressao(resultado):
    val = [c for c in resultado['cenarios'] if c['conjunto'] == 'val']
    assert sum(c['passou'] for c in val) >= 29, [(c['id'], c['resultado']) for c in val if not c['passou']]


def test_nenhum_negativo_aprovado(resultado):
    # o critério que importa para publicação: nenhum cenário que deveria bloquear terminou aprovado
    assert not [c['id'] for c in resultado['cenarios'] if c['esperado'] == ['bloqueia'] and c['resultado'] == 'aprova']
