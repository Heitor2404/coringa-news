"""Fiscal sombra (12/11/2026, depois da Torre Eiffel 4): só o fiscal sombra muda; nenhuma chamada real de IA.
1 fatos/narrativa/recursos: o motivo de "não medido" aparece; principais → lite; resposta vazia não passa por medida.
2 ritmo: imagem imóvel × movimento de câmera que muda a vista, sem premiar movimento à toa."""
import re
from pathlib import Path

import pytest

from src import custo, estaticos as E, fiscal

BASE = 'FATOS:{fatos}|FRASES:{frases}|TITULO:{titulo}'
RAIZ = Path(__file__).resolve().parent.parent
V = {'titulo': 'Torre', 'fatos': '- A torre tem 330 m (Wikipédia)',
     'cenas': [{'tipo': 'gancho', 'fala': 'A torre tem 330 m.'}, {'tipo': 'historia', 'fala': 'Ela foi erguida em 1889.'}]}
CENAS = [{'tipo': 'historia', 'img': 'a.jpg', 'start': 0, 'end': 3.0}, {'tipo': 'historia', 'img': 'b.jpg', 'start': 3.0, 'end': 6.0}]
RESP = {'fatos': {'frases': [{'frase': 1, 'status': 'confere'}, {'frase': 2, 'status': 'confere'}]},
        'narrativa': {'nota': 12, 'comentario': 'ok'}, 'recursos': {'faltou': []}}


@pytest.fixture(autouse=True)
def limpo(monkeypatch):
    from src import orcamento
    monkeypatch.setattr(orcamento, 'sobra', lambda: 999)
    custo.zerar()
    yield
    custo.zerar()


# ───────── 1. texto ─────────
def test_gemini_falhando_mostra_o_motivo_no_telegram_e_no_registro(capsys):
    def falha(p):
        raise RuntimeError('Gemini indisponível: 429 RESOURCE_EXHAUSTED')
    r = fiscal.sombra(V, CENAS, None, 7, pedir=falha, prompt_base=BASE)
    assert {'fatos', 'narrativa', 'recursos'} <= set(r['nao_medido'])
    txt = '\n'.join(fiscal.linhas_telegram(r))
    assert 'não medido' in txt and 'Gemini não respondeu' in txt and '429' in txt
    assert '[fiscal sombra] fatos/narrativa/recursos não medidos' in capsys.readouterr().out


def test_resposta_sem_as_partes_nao_vira_medida():
    r = fiscal.sombra(V, CENAS, None, 7, pedir=lambda p: {'outra': 1}, prompt_base=BASE)
    assert r['partes']['fatos'] is None and r['partes']['narrativa'] is None
    assert 'sem fatos/narrativa/recursos' in '\n'.join(fiscal.linhas_telegram(r))


def test_resposta_boa_mede_as_tres_partes():
    r = fiscal.sombra(V, CENAS, None, 7, pedir=lambda p: dict(RESP), prompt_base=BASE)
    assert r['partes']['fatos'] == 25 and r['partes']['narrativa'] == 12 and r['partes']['recursos'] == 5
    assert 'não medido: fatos' not in '\n'.join(fiscal.linhas_telegram(r))


def test_gemini_direto_tenta_principais_e_depois_lite_e_marca_o_lite(monkeypatch, capsys):
    from src import gemini
    usados = []

    def tentar(fn, modelos=None):
        usados.append(list(modelos))
        return dict(RESP, _modelo=modelos[-1])         # simula: principais sem cota, o último (lite) respondeu
    monkeypatch.setattr(gemini, '_tentar', tentar)
    monkeypatch.setattr(gemini, 'PRINCIPAIS', ['gemini-x-flash'])
    monkeypatch.setattr(gemini, 'LITES', ['gemini-x-flash-lite'])
    r = fiscal.sombra(V, CENAS, None, 7, pedir=fiscal._gemini_direto, prompt_base=BASE)
    assert usados == [['gemini-x-flash', 'gemini-x-flash-lite']]
    assert r['partes']['fatos'] == 25
    assert 'modelo lite gemini-x-flash-lite' in '\n'.join(fiscal.linhas_telegram(r))
    assert 'avaliado pelo modelo lite' in capsys.readouterr().out


def test_limite_de_tempo_cabe_principal_e_lite():
    assert fiscal.LIMITE_TEXTO_S >= 120


# ───────── 2. ritmo ─────────
def _cenas(*spec, img='x.jpg'):
    out, t = [], 0.0
    for d, kw in spec:
        c = {'tipo': 'historia', 'img': img, 'start': t, 'end': t + d}
        c.update(kw)
        out.append(c)
        t += d
    return out


def test_template_e_detector_usam_os_mesmos_numeros_de_camera():
    js = (RAIZ / 'src/render/template.html').read_text(encoding='utf-8')

    def arr(nome):
        m = re.search(r'const ' + nome + r'=(\[.*?\]);', js, re.S)
        return eval(m.group(1).replace("'", '"'))
    assert arr('CAMS') == E.CAMS and arr('SUB') == E.SUB and arr('FOCOS') == E.FOCOS
    cam = re.search(r'const CAM=\{(.*?)\};', js, re.S).group(1)
    no_template = {n: [float(x) for x in v.split(',')] for n, v in re.findall(r'(\w+):\[([^\]]*)\]', cam)}
    assert no_template == {n: [float(x) for x in v] for n, v in E.CAM.items()}


def test_foto_imovel_e_camera_lenta_continuam_paradas():
    imovel = E.medir_movimento(_cenas((5.4, {})))                                 # sem câmera escolhida
    lenta = E.medir_movimento(_cenas((5.4, {'camera': 'aproxima'})))              # zoom de 8%: não muda a vista
    pan = E.medir_movimento(_cenas((3.0, {'camera': 'esquerda'}), (2.4, {'camera': 'direita'})))
    for m in (imovel, lenta, pan):
        assert m['movimento'] == 0 and m['frac_estatica'] == 1.0


def test_reenquadramento_que_muda_a_vista_conta_so_no_mesmo_acontecimento():
    com = E.medir_movimento(_cenas((3.0, {'camera': 'aproxima', 'moldura': True, 'evento': 'e1'}),
                                   (2.5, {'sub': 1, 'moldura': True, 'evento': 'e1'})))
    sem = E.medir_movimento(_cenas((3.0, {'camera': 'aproxima', 'moldura': True}), (2.5, {'sub': 1, 'moldura': True})))
    assert com['movimento'] == 1 and com['frac_estatica'] == 0.0
    assert sem['movimento'] == 0 and sem['frac_estatica'] == 1.0
    assert com['mesma_imagem']['frac_estatica'] == 1.0                            # a régua antiga fica ao lado


def test_tremor_e_cortes_nervosos_nao_ganham_nada():
    tremor = E.medir_movimento(_cenas((5.0, {'camera': 'tremor', 'moldura': True, 'evento': 'e'})))
    assert tremor['movimento'] == 0
    nervoso = E.medir_movimento(_cenas((1.0, {'camera': 'aproxima', 'moldura': True, 'evento': 'e'}),
                                       *[(0.8, {'sub': j, 'moldura': True, 'evento': 'e'}) for j in (1, 2, 3, 4, 5)]))
    assert nervoso['movimento'] <= 2                                              # no máximo 1 a cada 2 s


def test_mesma_foto_por_muito_tempo_fica_parada_mesmo_com_camera():
    m = E.medir_movimento(_cenas((3.0, {'camera': 'aproxima', 'moldura': True, 'evento': 'e'}),
                                 *[(2.5, {'sub': j, 'moldura': True, 'evento': 'e'}) for j in (1, 2, 3, 4)]))
    assert m['estaticos'] and m['estaticos'][-1][1] == 13.0                       # depois de 8 s: parado
    assert m['estaticos'][-1][0] <= E.MOV_MAX_MESMA


def test_clipe_de_video_e_movimento_real():
    m = E.medir_movimento(_cenas((5.4, {'video': True})))
    assert m['movimento'] >= 1 and m['frac_estatica'] == 0.0


def test_troca_de_imagem_continua_contando_como_antes():
    cenas = _cenas((3.0, {})) + [dict(c, img='y.jpg', start=c['start'] + 3, end=c['end'] + 3) for c in _cenas((3.0, {}))]
    novo, antigo = E.medir_movimento(cenas), E.medir_cenas(cenas)
    assert novo['estaticos'] == antigo['estaticos'] == [] and novo['mudancas'] == antigo['mudancas'] == 1


def test_nota_de_ritmo_usa_a_regua_nova_e_o_telegram_mostra_as_duas():
    parado = _cenas((3.0, {'camera': 'aproxima', 'moldura': True}), (2.5, {'sub': 1, 'moldura': True}))
    movido = _cenas((3.0, {'camera': 'aproxima', 'moldura': True, 'evento': 'e'}), (2.5, {'sub': 1, 'moldura': True, 'evento': 'e'}))
    assert fiscal.nota_ritmo(movido)[0] > fiscal.nota_ritmo(parado)[0]
    r = fiscal.sombra(V, movido, None, 7, pedir=lambda p: dict(RESP), prompt_base=BASE)
    txt = '\n'.join(fiscal.linhas_telegram(r))
    assert 'câmera com propósito conta' in txt and 'sem contar a câmera' in txt and '1 mudança(s) vieram da câmera' in txt
