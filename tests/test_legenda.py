"""Legenda: número nunca se parte ('CERCA DE 3' + '000 HABITANTES' no vídeo Coober Pedy de 10/11)."""
import pytest

from src import voz


@pytest.mark.parametrize('texto,esperado', [
    ('cerca de 3 000 habitantes', 'cerca de 3.000 habitantes'),
    ('há 3 000 anos', 'há 3.000 anos'),
    ('1 000 000 de dólares', '1.000.000 de dólares'),
    ('20 % da cidade', '20% da cidade'),
    ('50 °C no verão', '50°C no verão'),
    ('em 1915 300 garimpeiros', 'em 1915 300 garimpeiros'),      # ano seguido de número: não junta
    ('entre 2 e 3 pessoas', 'entre 2 e 3 pessoas'),
])
def test_numeros_juntos(texto, esperado):
    assert voz.numeros_juntos(texto) == esperado


def test_legenda_mostra_o_numero_inteiro():
    fala = 'A cidade abriga cerca de 3 000 habitantes'
    pal = voz.alinhar(voz._estimar(fala, 3.0), fala)
    palavras = [w['w'] for c in voz.legendas(pal, set()) for w in c['words']]
    assert '3.000' in palavras and '000' not in palavras


def test_fiscal_final_usa_a_fala_da_propria_cena():
    """Com uma ideia dividida em 2 planos há mais cenas que frases; o fiscal não pode procurar a fala por posição."""
    import inspect
    import main
    fonte = inspect.getsource(main.fiscal_final)
    assert "v['cenas'][k]" not in fonte and "cenas[k].get('fala')" in fonte


def test_blocos_de_2_a_4_palavras_sem_terminar_em_palavra_fraca():
    """11/11: legenda saía com "ATÉ", "OS", "DO WADI EL" soltos."""
    from src.voz import legendas, _fraca
    txt = ('Os egípcios extraíam natrão do Wadi el Natrun para mumificar. Raso, com menos de três metros, '
           'mas tem 57 quilômetros. E pode superar 12, como o alvejante.')
    ws, t = [], 0.0
    for w in txt.split():
        ws.append({'w': w.strip('.,'), 'raw': w, 'start': t, 'end': t + 0.3}); t += 0.33
    bl = legendas(ws, set())
    assert sum(len(b['words']) for b in bl) == len(ws)              # nenhuma palavra some
    for b in bl:
        assert 1 <= len(b['words']) <= 4
        assert len(b['words']) == 1 or not _fraca({'w': b['words'][-1]['w']}), b
    assert sum(1 for b in bl if len(b['words']) == 1) <= 1
