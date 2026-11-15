"""V2.4 — checkpoint e retomada por etapa, offline: nada de pesquisa, acervo nem roteiro é refeito na retomada; o
checkpoint de origem nunca muda; edição à mão (contrato ou imagem) é detectada e listada para auditoria."""
import json
from pathlib import Path

import pytest

from src.v2 import checkpoint as ck


@pytest.fixture(autouse=True)
def _limpo():
    ck.desativar()
    yield
    ck.desativar()


def _acervo(tmp: Path):
    tmp.mkdir(parents=True, exist_ok=True)
    out = []
    for k in range(2):
        arq = tmp / f'a{k}.jpg'
        arq.write_bytes(f'imagem {k}'.encode())
        out.append({'id': f'a{k}', 'arq': arq, 'mostra': f'foto {k}', 'mini': b'\x00\x01bytes'})
    return out


def _v(acervo):
    return {'titulo': 'POR QUE LAGARTIXAS NÃO CAEM', 'acervo': acervo, 'fatos': '- fato. (Fonte)',
            'cenas': [{'fala': 'E ela some rápido.', 'acontecimento': {'id': 'e7', 'tipo': 'nivel', 'dados': {'etapas': ['perto', 'longe']}}}]}


def _primeira(tmp):
    c = ck.ativar(tmp / 'exec1' / 'checkpoint', pedido='lagartixa no teto', parte=1)
    ck.etapa('tema', lambda: {'pergunta': 'Por que a lagartixa não cai?', 'pedido': 'lagartixa no teto'})
    pesq = ck.etapa('pesquisa', lambda: ('- fato. (Fonte)', ['Fonte'], 'http://x', {'epoca': 'atual'}))
    acervo = ck.etapa('acervo', lambda: _acervo(tmp / 'tmp_acervo'))
    v = _v(acervo)
    ck.etapa('roteiro', lambda: {'tema': {'pergunta': 'Por que a lagartixa não cai?'}, 'v': v})
    ck.desativar()
    return c.pasta, pesq


def test_sem_checkpoint_ativo_so_executa():
    assert ck.etapa('pesquisa', lambda: 42) == 42 and ck.registro() is None


def test_grava_etapas_com_hash_arquivos_e_bytes(tmp_path):
    pasta, _ = _primeira(tmp_path)
    man = ck.manifesto_de(pasta)
    assert man['pedido'] == 'lagartixa no teto' and list(man['etapas']) == ['tema', 'pesquisa', 'acervo', 'roteiro']
    assert all(len(e['sha256']) == 64 for e in man['etapas'].values())
    assert set(man['etapas']['acervo']['arquivos']) == {'arquivos/a0_a0.jpg', 'arquivos/a1_a1.jpg'}
    rot = json.loads((pasta / 'roteiro.json').read_text())
    assert rot['v']['acervo'][0]['arq'] == 'arquivos/a0_a0.jpg'               # caminho relativo: retomável em outra máquina
    assert (pasta / '.original' / 'roteiro.json').exists()


def test_retomada_nao_refaz_nada_e_restaura_imagens(tmp_path):
    origem, pesq = _primeira(tmp_path)
    nunca = lambda: pytest.fail('etapa refeita na retomada')
    c = ck.ativar(tmp_path / 'exec2' / 'checkpoint', origem, 'roteiro')
    assert ck.etapa('tema', nunca)['pergunta'] == 'Por que a lagartixa não cai?'
    assert list(ck.etapa('pesquisa', nunca)) == list(pesq[:3]) + [pesq[3]]
    acervo = ck.etapa('acervo', nunca)
    pronto = ck.etapa('roteiro', nunca)
    assert Path(acervo[0]['arq']).read_bytes() == b'imagem 0' and acervo[0]['mini'] == b'\x00\x01bytes'
    assert Path(pronto['v']['acervo'][1]['arq']).is_file() and str(c.pasta.resolve()) in str(pronto['v']['acervo'][1]['arq'])
    reg = ck.registro()
    assert reg['carregadas'] == ['tema', 'pesquisa', 'acervo', 'roteiro'] and reg['executadas'] == [] and reg['editado'] == {}
    man2 = ck.manifesto_de(c.pasta)
    assert man2['origem']['pasta'] == str(origem) and man2['pedido'] == 'lagartixa no teto'
    assert all('carregada de' in e['procedencia'] for e in man2['etapas'].values())


def test_retomar_ate_acervo_refaz_so_o_roteiro(tmp_path):
    origem, _ = _primeira(tmp_path)
    ck.ativar(tmp_path / 'exec2' / 'checkpoint', origem, 'acervo')
    ck.etapa('tema', lambda: pytest.fail('tema refeito'))
    ck.etapa('pesquisa', lambda: pytest.fail('pesquisa refeita'))
    ck.etapa('acervo', lambda: pytest.fail('acervo refeito'))
    feito = []
    ck.etapa('roteiro', lambda: feito.append(1) or {'tema': {}, 'v': {'cenas': []}})
    assert feito == [1] and ck.registro()['executadas'] == ['roteiro']


def test_edicao_a_mao_do_contrato_e_detectada_com_o_que_mudou(tmp_path):
    origem, _ = _primeira(tmp_path)
    arq = origem / 'roteiro.json'
    d = json.loads(arq.read_text())
    d['v']['cenas'][0]['fala'] = 'E ela enfraquece rapidamente.'
    d['v']['cenas'][0]['acontecimento']['tipo'] = 'processo'
    arq.write_text(json.dumps(d, ensure_ascii=False))
    ck.ativar(tmp_path / 'exec2' / 'checkpoint', origem, 'roteiro')
    pronto = ck.etapa('roteiro', lambda: pytest.fail('refeito'))
    assert pronto['v']['cenas'][0]['acontecimento']['tipo'] == 'processo'
    mud = ck.registro()['editado']['roteiro']
    assert any('cenas[0].fala' in m and 'enfraquece' in m for m in mud)
    assert any('acontecimento.tipo' in m and '"nivel" → "processo"' in m for m in mud)
    assert 'EDITADA À MÃO' in ck.manifesto_de(tmp_path / 'exec2' / 'checkpoint')['etapas']['roteiro']['procedencia']
    assert json.loads((origem / '.original' / 'roteiro.json').read_text())['v']['cenas'][0]['fala'] == 'E ela some rápido.'


def test_imagem_trocada_e_detectada(tmp_path):
    origem, _ = _primeira(tmp_path)
    (origem / 'arquivos' / 'a1_a1.jpg').write_bytes(b'outra imagem')
    ck.ativar(tmp_path / 'exec2' / 'checkpoint', origem, 'acervo')
    ck.etapa('acervo', lambda: pytest.fail('refeito'))
    assert ck.registro()['editado']['acervo'] == ['imagem trocada: arquivos/a1_a1.jpg']


def test_retomar_de_novo_a_partir_da_retomada(tmp_path):
    origem, _ = _primeira(tmp_path)
    ck.ativar(tmp_path / 'exec2' / 'checkpoint', origem, 'roteiro')
    for nome in ck.ETAPAS:
        ck.etapa(nome, lambda: pytest.fail('refeito'))
    ck.desativar()
    ck.ativar(tmp_path / 'exec3' / 'checkpoint', tmp_path / 'exec2' / 'checkpoint', 'roteiro')
    pronto = ck.etapa('roteiro', lambda: pytest.fail('refeito'))
    assert Path(pronto['v']['acervo'][0]['arq']).read_bytes() == b'imagem 0'
    assert not any('a0_a0_a0' in str(p) for p in (tmp_path / 'exec3' / 'checkpoint' / 'arquivos').iterdir())


def test_etapa_desconhecida_e_manifesto_ausente(tmp_path):
    origem, _ = _primeira(tmp_path)
    with pytest.raises(ValueError):
        ck.ativar(tmp_path / 'x', origem, 'narracao')
    with pytest.raises(FileNotFoundError):
        ck.ativar(tmp_path / 'y', tmp_path / 'nada', 'roteiro')


def test_main_retomada_do_roteiro_pula_pesquisa_acervo_e_roteiro(tmp_path, monkeypatch):
    """O caminho do main.py: com checkpoint de roteiro, nem tema_livre nem escrever_explica rodam; os contratos são
    conferidos de novo (pega a edição à mão) e o montar_video recebe o roteiro com o registro do checkpoint."""
    import main
    from src import roteiro
    origem, _ = _primeira(tmp_path)
    monkeypatch.setattr(roteiro, 'tema_livre', lambda *a, **k: pytest.fail('tema refeito'))
    monkeypatch.setattr(roteiro, 'escrever_explica', lambda *a, **k: pytest.fail('roteiro refeito'))
    conferidos, montados = [], []
    monkeypatch.setattr(roteiro, 'contratos_v2', lambda v, *a, **k: conferidos.append(v['titulo']))

    def montar(v, pasta, nome, teste=False):
        montados.append(v)
        raise ValueError('material ruim: parada aqui (teste)')
    monkeypatch.setattr(main, 'montar_video', montar)
    monkeypatch.setattr(main, '_arquivo_serie', lambda pedido, parte: tmp_path / 'serie.json')
    monkeypatch.setattr(main, '_tg', lambda *a, **k: True)
    ck.ativar(tmp_path / 'exec2' / 'checkpoint', origem, 'roteiro')
    r = main._fazer_curiosidade('lagartixa no teto', 1, tmp_path, unico=True)
    assert r == 'pular' and conferidos == ['POR QUE LAGARTIXAS NÃO CAEM']
    assert montados[0]['_checkpoint']['carregadas'] == ['roteiro']


def test_ids_repetidos_com_imagens_diferentes_nao_se_sobrescrevem(tmp_path):
    c = ck.ativar(tmp_path / 'ck')
    (tmp_path / 'p1').mkdir(); (tmp_path / 'p2').mkdir()
    (tmp_path / 'p1' / 'a0.jpg').write_bytes(b'um'); (tmp_path / 'p2' / 'a0.jpg').write_bytes(b'dois')
    ck.etapa('acervo', lambda: [{'id': 'a0', 'arq': tmp_path / 'p1' / 'a0.jpg'}, {'id': 'a0', 'arq': tmp_path / 'p2' / 'a0.jpg'}])
    arqs = json.loads((c.pasta / 'acervo.json').read_text())
    assert len({x['arq'] for x in arqs}) == 2
    assert {(c.pasta / x['arq']).read_bytes() for x in arqs} == {b'um', b'dois'}


def test_edicao_editorial_com_trava_de_texto_e_registro(tmp_path):
    import hashlib
    origem, _ = _primeira(tmp_path)
    sha = hashlib.sha256('E ela some rápido.'.encode()).hexdigest()
    ed = {'motivo': 'precisão', 'autor': 'editor', 'operacoes': [
        {'evento': 'e7', 'esperado_sha256': {'fala': sha}, 'set': {'fala': 'E ela enfraquece rapidamente.', 'acontecimento.tipo': 'processo'}}]}
    with pytest.raises(ValueError, match='não é o texto esperado'):
        ck.editar(origem, {**ed, 'operacoes': [{**ed['operacoes'][0], 'esperado_sha256': {'fala': '0' * 64}}]})
    reg = ck.editar(origem, ed)
    assert reg['aplicadas'] and (origem / 'edicao_aplicada.json').exists()
    assert json.loads((origem / '.original' / 'roteiro.json').read_text())['v']['cenas'][0]['fala'] == 'E ela some rápido.'
    ck.ativar(tmp_path / 'exec2' / 'checkpoint', origem, 'roteiro')
    pronto = ck.etapa('roteiro', lambda: pytest.fail('refeito'))
    r = ck.registro()
    assert pronto['v']['cenas'][0]['fala'] == 'E ela enfraquece rapidamente.'
    assert r['edicao']['motivo'] == 'precisão' and any('cenas[0].fala' in m for m in r['editado']['roteiro'])
