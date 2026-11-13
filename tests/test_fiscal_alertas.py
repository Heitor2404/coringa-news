"""Plano-mestre, etapa H (12/11/2026): fiscal sombra observacional. Alertas graves FORA da nota (P0/P1 com evidência),
evidência por cena, "não medido" nunca vira nota boa, e nada muda na publicação. Sem IA (respostas simuladas)."""
import copy
import json
from pathlib import Path

from src import editorial as ed, fiscal, storyboard as sbm

RAIZ = Path(__file__).resolve().parent.parent
CASOS = json.loads((RAIZ / 'tests/editorial_casos.json').read_text(encoding='utf-8'))
BASE = 'FATOS:{fatos}|FRASES:{frases}|TITULO:{titulo}'


def _resp(n):
    return {'fatos': {'frases': [{'frase': k + 1, 'status': 'confere'} for k in range(n)]},
            'narrativa': {'nota': 13}, 'recursos': {'faltou': []}}


def _video(nome, explica=True):
    caso = copy.deepcopy(CASOS[nome])
    v = caso['roteiro']
    v.update(categoria=caso['categoria'], fatos=caso['fatos'])
    ed.preparar(v)
    t = 0.0
    for k, c in enumerate(v['cenas']):
        c.update(grupo=k, evento=f'e{k}', start=t, end=t + 3.0, img=f'{k}.jpg' if c['tipo'] != 'fechamento' else None)
        if explica and c['tipo'] != 'fechamento':
            c.update(foto=f'a{k}', relacao='fato')
        t += 3.0
    sbm.atualizar_midia(sbm.construir(v))
    return v


def _sombra(v, tela=None, pedir=None, monkeypatch=None):
    if monkeypatch:
        from src import orcamento
        monkeypatch.setattr(orcamento, 'sobra', lambda: 999)
    n = len([c for c in v['cenas'] if c['tipo'] != 'fechamento'])
    return fiscal.sombra(v, v['cenas'], None, 7, tela or [], pedir=pedir or (lambda p: _resp(n)), prompt_base=BASE)


def test_video_bom_sem_alertas_e_com_evidencia_por_cena(monkeypatch):
    for nome in CASOS:
        r = _sombra(_video(nome), monkeypatch=monkeypatch)
        assert r['alertas'] == [], (nome, r['alertas'])
        assert r['por_cena'] and all(c['explica'] for c in r['por_cena'])
        assert '🖼 representação' in '\n'.join(fiscal.linhas_telegram(r))


def test_falhas_graves_viram_alertas_separados_sem_mexer_na_nota(monkeypatch):
    bom = _sombra(_video('historia'), monkeypatch=monkeypatch)
    v = _video('historia', explica=False)                                      # nenhuma mídia que explique
    v['plano']['promessa'] = 'você não vai acreditar no que aconteceu'
    v['cenas'].insert(3, {'tipo': 'numero', 'valor': 512, 'fala': 'tinha 512 degraus', 'bloco': {'funcao': 'evidencia'},
                          'start': 9, 'end': 9})
    r = _sombra(v, tela=['3,0s (historia): "FOTO" em cima de "FERRO"'], monkeypatch=monkeypatch)
    niveis = {(a['nivel'], a['motivo']) for a in r['alertas']}
    assert ('P0', 'texto em cima de texto') in niveis and ('P0', 'gráfico com dado fora dos fatos') in niveis
    assert ('P1', 'cena central sem mídia que explique') in niveis
    assert any(a['nivel'] == 'P1' and 'clickbait' in a['evidencia'] for a in r['alertas'])
    assert all(a['evidencia'] for a in r['alertas'])                            # cada alerta com a evidência
    assert bom['partes']['fatos'] == r['partes']['fatos']                      # alerta não entra na conta da nota
    txt = '\n'.join(fiscal.linhas_telegram(r))
    assert '🚩 alertas (fora da nota, não decidem)' in txt and 'P0' in txt


def test_nao_medido_fica_desconhecido_e_nao_vira_nota_boa(monkeypatch):
    def falha(p):
        raise TimeoutError('sem resposta')
    r = _sombra(_video('biologia'), pedir=falha, monkeypatch=monkeypatch)
    assert {'fatos', 'narrativa', 'recursos'} <= set(r['nao_medido'])
    assert all(r['partes'][k] is None for k in ('fatos', 'narrativa', 'recursos'))
    assert 'não respondeu' in '\n'.join(fiscal.linhas_telegram(r))


def test_roteiro_antigo_sem_storyboard_nao_inventa_alerta(monkeypatch):
    v = {'titulo': 'x', 'fatos': 'F', 'cenas': [{'tipo': 'gancho', 'fala': 'a', 'start': 0, 'end': 3, 'img': 'a.jpg'},
                                                {'tipo': 'fechamento', 'fala': 'b', 'start': 3, 'end': 5}]}
    r = _sombra(v, monkeypatch=monkeypatch)
    assert r['alertas'] == [] and r['por_cena'] == []
