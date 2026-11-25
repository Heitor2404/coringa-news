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


def test_cortes_de_imagem_podem_adiantar_ou_atrasar_ate_1_2s_sem_exceder_capacidade():
    """Run 45671032979: voz 63,8 s < capacidade 68,4 s, mas um capítulo pedia fator 1,15."""
    case = {'chapters': [{'needs': ['a', 'b', 'c']}, {'needs': ['d', 'e', 'f']}]}
    chosen = {k: {'cap': 3.8, 'min': 1.4} for k in 'abcdef'}
    ends = [round(12.2 * 30), round(21.0 * 30)]          # capítulo 1 com 12,2 s > 11,4 s de evidência
    out = I.ajustar_cortes(case, chosen, ends, ends[-1])
    assert out and out[-1] == ends[-1] and abs(out[0] - ends[0]) <= 36 and out[0] <= 342
    assert out[1] - out[0] <= 342
    assert I.ajustar_cortes(case, chosen, [round(14 * 30), round(22 * 30)], round(22 * 30)) is None   # excede 1,2 s


def test_compactar_pausas_preserva_fala_e_mapeia_tempos(tmp_path):
    import numpy as np, wave
    sr = 16000
    tom = lambda s: (np.sin(np.arange(int(s * sr)) * 2 * np.pi * 220 / sr) * 8000).astype(np.int16)
    sil = lambda s: np.zeros(int(s * sr), np.int16)
    a = np.concatenate([tom(1.0), sil(1.4), tom(1.0), sil(.2), tom(.5)])
    src = tmp_path / 'v.wav'
    with wave.open(str(src), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(a.tobytes())
    dur, mapa = I.compactar_pausas(src, tmp_path / 'c.wav')
    assert abs(dur - (4.1 - (1.4 - I.PAUSA_MAX_S))) < .08          # só a pausa longa foi encurtada
    assert abs(mapa(2.5) - (2.5 - (1.4 - I.PAUSA_MAX_S))) < .08 and abs(mapa(.5) - .5) < 1e-6


def test_plano_com_foto_na_capacidade_exata_em_quadros_inteiros_nao_e_reprovado():
    """Run 45674218044: n16 com 114 quadros reprovado como F-PLANO-SEM-DIRECAO porque fim-início em segundos
    (quadros/30) deu 3.8000000000000043 > 3.8."""
    from src.v4.formatos import filme_editorial as F
    import inspect
    a, b = 1404 / 30, 1518 / 30
    assert b - a > 3.8 and b - a <= 3.8 + 1e-6
    assert 'span > max_span + 1e-6' in inspect.getsource(F.avaliar)
