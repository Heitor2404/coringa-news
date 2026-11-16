"""V3.1 — memória de engenharia (erros com teste que existe), receitas consultáveis, feedback por timestamp e regras
editoriais com estado (só aprovada influencia a produção). Inclui os testes de regressão ERR-004 e ERR-006 no V3.1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import v3_material as M  # noqa: E402

from src.v3 import biblioteca as B, memoria, pipeline as P, receitas  # noqa: E402


def test_registro_de_erros_integro_e_cada_teste_existe():
    assert memoria.problemas_registro() == []
    ids = [e['id'] for e in memoria.erros()]
    for esperado in ('ERR-001', 'ERR-002', 'ERR-003', 'ERR-004', 'ERR-005', 'ERR-006', 'ERR-007', 'ERR-008', 'ERR-009', 'ERR-010',
                     'ERR-011', 'ERR-012', 'ERR-013'):
        assert esperado in ids


def test_erros_pertinentes_por_tipo_de_acontecimento():
    mec = {e['id'] for e in memoria.erros_pertinentes({'mecanismo'})}
    assert 'ERR-006' in mec and 'ERR-003' in mec                    # '*' vale para todos
    assert 'ERR-006' not in {e['id'] for e in memoria.erros_pertinentes({'pessoa'})}


def test_receitas_integras_e_recuperacao_aprovadas_primeiro():
    assert receitas.problemas() == []
    rs = receitas.recuperar({'mecanismo'}, {'mecanismo'})
    assert rs[0]['id'] == 'R-MECANISMO-ANIMADO' and rs[0]['estado'] == 'aprovado'
    assert all(r['estado'] in ('aprovado', 'testado') for r in rs)
    assert not receitas.recuperar({'mecanismo'}, {'mecanismo'}, composicoes={'citacao'})   # composição indisponível tira a receita


def test_feedback_por_timestamp_liga_ao_plano(tmp_path):
    direcao = tmp_path / 'direcao.json'
    direcao.write_text(json.dumps({'registro': [{'evento_id': 'e1', 'composicao': 'doc.plano', 'tempo': [0, 4.2], 'receita': 'R-GANCHO-IMPACTO'},
                                                {'evento_id': 'e2', 'composicao': 'mapa.rota', 'tempo': [4.2, 9], 'receita': 'R-DESLOCAMENTO'}]}))
    f = memoria.registrar_feedback('ever', '0:05,5', 'movimento', 'rota rápida demais', direcao=direcao, caminho=tmp_path / 'fb.jsonl')
    assert f['t'] == 5.5 and f['plano']['evento_id'] == 'e2' and f['plano']['receita'] == 'R-DESLOCAMENTO' and f['estado'] == 'aberto'
    with pytest.raises(ValueError):
        memoria.registrar_feedback('ever', 3, 'gosto', 'x', caminho=tmp_path / 'fb.jsonl')


def test_so_regra_aprovada_vai_para_a_producao(tmp_path):
    c = tmp_path / 'regras.json'
    r = memoria.nova_regra('Mapa de rota dura pelo menos 3 s', ['deslocamento'], 'FB-0001', caminho=c)
    assert memoria.regras_para_producao({'deslocamento'}, c) == []
    with pytest.raises(ValueError):
        memoria.mudar_estado(r['id'], 'aprovado', 'pulei o teste', caminho=c)                   # aprovar exige testar antes
    with pytest.raises(ValueError):
        memoria.mudar_estado(r['id'], 'testado', '', caminho=c)                                 # sem evidência não muda
    memoria.mudar_estado(r['id'], 'testado', 'vídeo X: rota 3,4 s legível', caminho=c)
    assert memoria.regras_para_producao({'deslocamento'}, c) == []
    memoria.mudar_estado(r['id'], 'aprovado', 'Heitor aprovou o vídeo X', caminho=c)
    assert [x['id'] for x in memoria.regras_para_producao({'deslocamento'}, c)] == [r['id']]
    memoria.mudar_estado(r['id'], 'obsoleto', 'substituída', caminho=c)
    assert memoria.regras_para_producao({'deslocamento'}, c) == []


def _ctx(tmp_path):
    v = M.roteiro()
    bib = B.Biblioteca(tmp_path / 'b.sqlite3', tmp_path / 'arm')
    ac, _ = P.acervo_diretor(v, bib, 'ever', 'Ever Given')
    _, ctx = P.montar_prompt(v, ac, bib)
    return v, ac, ctx


def test_err_004_numero_sem_unidade(tmp_path):
    v, ac, ctx = _ctx(tmp_path)
    sb = M.storyboard_valido(v)
    sb['planos'][1]['anotacoes'] = [{'tipo': 'circulo', 'alvo': 'navio', 'texto': 'SEIS: 6', 'na_palavra': 'canal'}]
    erros = [e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == 1]
    assert any('sem unidade' in e for e in erros)
    sb['planos'][1]['anotacoes'][0]['texto'] = '6 dias bloqueado'
    assert not [e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == 1]


def test_err_006_mecanismo_nao_vira_cartao(tmp_path):
    v, ac, ctx = _ctx(tmp_path)
    mec = next(e for e in ctx['eventos'] if e['tipo'] == 'mecanismo' and e['critico'])
    sb = M.storyboard_valido(v)
    k = mec['trechos'][0]
    erros = [e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == k]
    assert any('mecanismo crítico' in e for e in erros)                      # foto CONTEXTO não demonstra o mecanismo
    sb['planos'][k]['composicao'] = 'processo.etapas'                        # cartão de frases também não
    assert any('não é viável' in e or 'mecanismo crítico' in e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == k)
    sb['planos'][k].update(composicao='doc.plano', funcao_documental='REGISTRO')   # registro real do próprio mecanismo: aceito
    assert not any('mecanismo crítico' in e for i, e in P.validar_storyboard(sb, v, ac, ctx) if i == k)
