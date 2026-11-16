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
