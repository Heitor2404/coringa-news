"""E284 (run 45667613774): voz medida 72,8 s > capacidade verificada 68,4 s → E254-TEMPO-CAPITULO. A correção ajusta o
ritmo da fala uniformemente (até 8%) em vez de esticar ou repetir imagens; acima disso exige replanejar a fala."""
from scripts import qa_documentario_integral_e254 as I


def _case(n):
    return {'chapters': [{'needs': [f'n{i}' for i in range(k * 3, k * 3 + 3)]} for k in range(n)]}


def test_fator_cobre_o_capitulo_mais_apertado():
    case = _case(2); chosen = {f'n{i}': {'cap': 3.8} for i in range(6)}
    tempos = [(0, 12.1), (12.1, 23.0)]
    f = I.ritmo_necessario(case, chosen, tempos, 23.0)
    assert abs(f - 12.1 / 11.4) < 1e-3 and f <= I.FATOR_MAX


def test_sem_excesso_fator_um_e_excesso_grande_exige_replanejamento():
    case = _case(1); chosen = {f'n{i}': {'cap': 3.8} for i in range(3)}
    assert I.ritmo_necessario(case, chosen, [(0, 10.0)], 10.0) == 1.0
    assert I.ritmo_necessario(case, chosen, [(0, 13.5)], 13.5) > I.FATOR_MAX
