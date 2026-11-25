"""E284 — riscos 3.3 (contrato exato do reuso) e 3.4 (estados inequívocos das provas)."""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from scripts import contrato_reuso_replay as C
from scripts import resumo_provas as RP
from src.v4.formatos import amostragem_documental as A

RAIZ = Path(__file__).resolve().parents[1]


def _saida(tmp_path, ids, estados=('CANDIDATO_PRIVADO_REVISADO', 'LACUNA_PENDENTE'), visao=0, http=0):
    r = {'reusos_analises': len(ids), 'reusos_ids': ids, 'visao_chamadas_logicas': visao, 'telemetria_visao': [],
         'cobertura': [{'estado': e, 'selecionado': ['b', 'x'] if i == 0 else None} for i, e in enumerate(estados)],
         'cobertura_documentario': {'consumo': {'http': http, 'buscas': 0}}, 'rede_aquisicao': {'http': 0}, 'publish': False,
         'x': [{'provedor': 'reuso_privado', 'revisao_id': i} for i in ids]}
    p = tmp_path / 'r.json'
    p.write_text(json.dumps(r))
    return p


def test_contrato_detecta_perda_troca_de_identidade_visao_e_download(tmp_path):
    base = [f'id{i}' for i in range(9)]
    contrato = C.extrair(_saida(tmp_path, base))
    assert C.conferir(C.extrair(_saida(tmp_path, base)), contrato) == []
    assert C.conferir(C.extrair(_saida(tmp_path, base[:6])), contrato)          # 6 >= 6 passava no workflow antigo
    assert C.conferir(C.extrair(_saida(tmp_path, base[:8] + ['outro'])), contrato)  # mesma quantidade, outra revisão
    assert C.conferir(C.extrair(_saida(tmp_path, base, visao=1)), contrato)
    assert C.conferir(C.extrair(_saida(tmp_path, base, http=3)), contrato)
    assert C.conferir(C.extrair(_saida(tmp_path, base, estados=('LACUNA_PENDENTE', 'LACUNA_PENDENTE'))), contrato)


def test_contrato_congelado_existe_com_nove_reusos():
    c = json.loads((RAIZ / 'benchmarks/e284/contrato_replay_e260.json').read_text())
    assert c['reusos_analises'] == 9 and sum(n for _, n in c['reusos_ids']) == 9
    assert c['estados'] == ['CANDIDATO_PRIVADO_REVISADO', 'LACUNA_PENDENTE']


def test_estados_das_provas_nao_aprovam_prova_ausente_ou_bloqueada(tmp_path):
    sh = RAIZ / 'scripts/estado_prova.sh'
    env = {'PROVAS_DIR': str(tmp_path), 'PATH': '/usr/bin:/bin'}
    subprocess.run(['bash', str(sh), 'ok', 'true'], env=env, check=True)
    subprocess.run(['bash', str(sh), 'falha', 'false'], env=env, check=True)
    subprocess.run(['bash', str(sh), 'acesso', 'bash', '-c', 'exit 77'], env=env, check=True)
    est = RP.resumir(tmp_path, ['ok', 'falha', 'acesso', 'ausente'])
    assert est == {'ok': 'APROVADA', 'falha': 'REPROVADA', 'acesso': 'BLOQUEADA', 'ausente': 'NAO_EXECUTADA'}
    assert RP.main([str(tmp_path), 'ok']) == 0
    for outra in ('falha', 'acesso', 'ausente'):
        assert RP.main([str(tmp_path), 'ok', outra]) == 1


def test_workflow_isolado_sem_continue_on_error_nem_limiar_frouxo():
    wf = (RAIZ / '.github/workflows/qa-consolidacao-claude-20261125.yml').read_text()
    assert 'continue-on-error' not in wf and ">=6" not in wf and '|| true' not in wf
    assert 'resumo_provas.py' in wf and 'contrato_reuso_replay' in wf


def test_chaves_arredondadas_em_colisao_restauram_cada_inicio_exato():
    frame = lambda path, t, width: Image.new('RGB', (width, 120), (int(t * 1000) % 255, 40, 40))
    m = {'expected_sha256': 'f' * 64, 'duration_s': 60.0, 'local_source': 'fixture', 'width': 320, 'height': 180,
         'varredura_local': False}
    n = {'id': 'n', 'fatos': ['f'], 'mostrar': 'x', 'evidencia_visual': 'movimento'}
    a1, a2 = 17.12340, 17.12344          # mesma chave round(.,4)
    assert round(a1, 4) == round(a2, 4)
    e, w = A.preparar_lote(m, n, frame, priorizar_cache={round(a1, 4)}, inicios_exatos={round(a1, 4): [a1, a2]})
    starts = {x['inicio_s'] for x in e['janelas']}
    assert a1 in starts and a2 in starts
