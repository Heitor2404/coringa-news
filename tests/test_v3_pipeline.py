"""V3.1 — diretor automático no fluxo: contexto recuperado (não a biblioteca inteira), 1 chamada + no máximo 1 correção,
storyboard do modelo usado na montagem, tempos da fala alinhada, crítico sem plano bloqueia sem render."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import v3_material as M  # noqa: E402

from src.v3 import biblioteca as B, pipeline as P  # noqa: E402


def _ac(tmp_path, v):
    bib = B.Biblioteca(tmp_path / 'b.sqlite3', tmp_path / 'arm')
    ac, reuso = P.acervo_diretor(v, bib, 'video-teste', 'Ever Given Canal de Suez')
    return bib, ac, reuso


def test_prompt_traz_so_o_contexto_recuperado(tmp_path):
    v = M.roteiro()
    bib, ac, _ = _ac(tmp_path, v)
    p, ctx = P.montar_prompt(v, ac, bib)
    assert 'R-APROXIMA-OBJETO · BOA PRÁTICA APROVADA' in p and 'R-EXPERIMENTO' not in p        # proposta não entra
    assert 'ERR-006' in p and 'ERR-016' not in p                                                # só erros pertinentes, com regra
    assert all(f'{i}: ' in p for i in range(len(v['cenas'])))                                     # todos os trechos indexados
    assert ctx['fatos_ids'][0] == 'f1' and len(p) < 30000


def test_midia_de_outro_video_e_recuperada_da_biblioteca(tmp_path):
    v = M.roteiro()
    bib, ac, _ = _ac(tmp_path, v)                                    # 1º vídeo cataloga o acervo
    v2 = M.roteiro()
    v2['acervo'] = v2['acervo'][:2]                                  # 2º vídeo do mesmo assunto, acervo pequeno
    ac2, reuso = P.acervo_diretor(v2, bib, 'video-2', 'Ever Given Canal de Suez navio')
    globais = [k for k in ac2 if k.startswith('cm-')]
    assert globais and reuso['recuperadas_de_outros_videos'][0]['de_videos'] == ['video-teste']
    assert all(Path(ac2[k]['arq']).exists() for k in globais)


def test_uma_chamada_e_no_maximo_uma_correcao(tmp_path):
    v = M.roteiro()
    bib, ac, _ = _ac(tmp_path, v)
    bom = M.storyboard_valido(v)
    ruim = M.copia(bom)
    ruim['planos'][3]['transicao'] = 'explosao'
    ruim['planos'][4]['anotacoes'] = [{'tipo': 'circulo', 'alvo': 'navio', 'texto': '777 m de comprimento', 'na_palavra': 'navio'}]
    chamadas = []

    def chamar(prompt):
        chamadas.append(prompt)
        return (ruim if len(chamadas) == 1 else ruim), {'usd': .01, 'segundos': 1, 'tamanho_prompt': len(prompt)}
    sb, reg = P.storyboard_automatico(v, ac, bib, chamar)
    assert len(chamadas) == 2                                         # nunca mais que 2, mesmo com erro remanescente
    assert 'transição inexistente: explosao' in chamadas[1] and 'número 777' in chamadas[1]
    assert reg['resposta_original'] == ruim and reg['erros_finais'] and reg['consumo']['chamadas'] == 2


def test_tempos_vem_da_fala_alinhada_e_divisao_na_palavra():
    sb = {'planos': [{'trechos': [0]}, {'trechos': [1]}, {'trechos': [1], 'comeca_na_palavra': 'canal'}]}
    tempos = [(0.0, 2.0), (2.0, 6.0)]
    pal = [{'w': 'e', 's': 2.1}, {'w': 'bloqueou', 's': 2.4}, {'w': 'canal', 's': 4.2}]
    av = P.aplicar_tempos(sb, tempos, pal, 6.5)
    t = [(p['tempo_inicio'], p['tempo_fim']) for p in sb['planos']]
    assert t == [(0.0, 2.0), (2.0, 4.2), (4.2, 6.5)] and not av


def test_critico_sem_plano_bloqueia(tmp_path):
    v = M.roteiro()
    sb = M.storyboard_valido(v)
    sb['planos'] = [p for p in sb['planos'] if p['evento_id'] != 'e3']        # tira o acontecimento crítico e3
    renders = []

    def narrar(cenas, trab):
        tempos = [(i * 2.5, i * 2.5 + 2.5) for i in range(len(cenas))]
        return tmp_path / 'a.wav', tempos, [], len(cenas) * 2.5
    import os
    os.environ['BIBLIOTECA_DB'] = str(tmp_path / 'b.sqlite3'); os.environ['BIBLIOTECA_ARMAZEM'] = str(tmp_path / 'arm')
    try:
        res = P.montar_video(v, tmp_path, 'ever', tmp_path / 'trab', chamar=lambda p: (M.copia(sb), {'usd': 0, 'tamanho_prompt': len(p)}),
                             chamar_visao=None, narrar=narrar, renderizar=lambda *a: renders.append(a))
    finally:
        os.environ.pop('BIBLIOTECA_DB'); os.environ.pop('BIBLIOTECA_ARMAZEM')
    assert any('e3' in b for b in res['bloqueios']) and not renders and res['mp4'] is None
    assert (tmp_path / 'ever-v3' / 'storyboard_ia.json').exists() and (tmp_path / 'ever-v3' / 'direcao.json').exists()


def test_err_017_datas_horas_e_nos_nao_sao_falso_positivo(tmp_path):
    v = M.roteiro()
    v['fatos'] += '\n- O navio partiu em 10/04/1912 a 22 nós e o vigia avistou o gelo às 23h40.'
    bib, ac, _ = _ac(tmp_path, v)
    _, ctx = P.montar_prompt(v, ac, bib)
    sb = M.storyboard_valido(v)
    for t in ('Velocidade: 22 nós', 'Partida: 10/04/1912', 'Avistado às 23h40'):
        sb['planos'][1]['anotacoes'] = [{'tipo': 'circulo', 'alvo': 'navio', 'texto': t, 'na_palavra': 'canal'}]
        assert not [e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == 1 and 'número' in e], t
    sb['planos'][1]['anotacoes'][0]['texto'] = 'Partida: 10/04/1913'          # ano fora da pesquisa continua sendo pego
    assert [e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == 1 and ('1913' in e or '41' in e)]
    sb['planos'][1]['anotacoes'][0]['texto'] = '22 nós (41 km/h)'               # conversão feita pelo modelo, fora da pesquisa: pego
    assert [e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == 1 and ('1913' in e or '41' in e)]


def test_err_018_ate_desvio_invalido_nao_derruba(tmp_path):
    from src.v2 import diretor
    v = M.roteiro()
    bib, ac, _ = _ac(tmp_path, v)
    _, ctx = P.montar_prompt(v, ac, bib)
    sb = M.storyboard_valido(v)
    sb['planos'][0]['anotacoes'] = [{'tipo': 'seta', 'alvo': 'navio', 'ate_desvio': True, 'texto': 'esquema'}]
    assert any('ERR-018' in e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == 0)
    pl = {**sb['planos'][0], 'tempo_inicio': 0, 'tempo_fim': 3}
    x = ac[pl['recurso_visual']['id']]
    reg = {x['sha']: {'objetos': {'navio': {'caixa': [.3, .3, .2, .2], 'visivel': True, 'ancoravel': True}}}}
    cenas, r = diretor.montar({'planos': [pl]}, ac, reg, [], {'f1'})
    assert cenas and not cenas[0]['params']['anot'] and any('ERR-018' in l for l in r[0]['limitacoes'])


def test_err_019_sem_saliencia_nao_derruba(monkeypatch):
    import cv2
    from src.v2 import regioes
    if hasattr(cv2, 'saliency'):
        monkeypatch.delattr(cv2, 'saliency')
    assert regioes.saliencia(M.BASE / 'img' / 'a23-g.jpg') == {}


def test_err_020_tempos_em_lista_e_casas_decimais():
    from src.v2 import contrato, diretor
    pl = {'evento_id': 'e1', 'fato_id': 'f1', 'funcao_narrativa': 'mecanismo', 'recurso_visual': {'tipo': 'composicao', 'id': 'processo.etapas'},
          'funcao_documental': 'ESQUEMA', 'acao_visual': 'etapas', 'composicao': 'processo.etapas', 'tempo_inicio': 0, 'tempo_fim': 6,
          'params': {'etapas': ['a', 'b']}, 'tempos_palavras': {'inicio': 'um', 'cede': 'dois'}, 'fala': 'um dois'}
    cenas, _ = diretor.montar({'planos': [pl]}, {}, {}, [{'w': 'um', 's': .4}, {'w': 'dois', 's': 2.5}], {'f1'})
    assert cenas[0]['params']['tempos'] == [.4, 2.5]                        # lista em ordem, não {passo: segundo}
    assert contrato.params_tela({'dados': {'valor': 5.5, 'unidade': 'graus'}}, 'numero.animado')['casas'] == 1
