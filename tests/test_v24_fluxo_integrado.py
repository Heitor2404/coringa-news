"""V2.4 — fluxo REAL do main.py, offline: `main.main()` com MOTOR_VISUAL=v2 → escrever_explica (checkpoint de tema,
pesquisa e acervo; prompt V2; pré-validação + conserto) → montar_video (preparo V2.3) → status da execução.
Só as folhas de rede/IA são substituídas (pesquisa, coleta do acervo, chamadas de texto); o resto é o código real.

Cenário: e5 crítico não observável sem dados e sem conserto possível → BLOQUEADO_PREPARO com diagnóstico e checkpoint.
Depois: o contrato é corrigido à mão no checkpoint, `--retomar` não refaz pesquisa/acervo/roteiro, a edição aparece
no relatório e o preparo passa com ILUSTRAÇÃO (a execução para de propósito antes da mídia)."""
import json
import sys
from pathlib import Path

import pytest

from src import gemini

F = Path(__file__).parent / 'piloto_lagartixa'
FATOS = """ÉPOCA/LUGAR: Atual
- As cerdas das patas da lagartixa criam forças de Van der Waals com a superfície. [fato] (Wikipédia)
- Cada cerda se divide em centenas de espátulas que chegam muito perto da superfície. [fato] (Olhar Digital)
- A força de Van der Waals enfraquece rapidamente quando as moléculas ficam mais afastadas. [fato] (Wikipedia (inglês))
"""


class Parada(Exception):
    pass


def _roteiro():
    v = gemini.extrair_json((F / 'roteiro_bruto.txt').read_text(encoding='utf-8'))
    for c in v['cenas']:
        ac = c.get('acontecimento') or {}
        if ac.get('id') == 'e5':          # como na retomada 43646047814: mecanismo crítico SEM dados
            ac.update(tipo='mecanismo', sujeito='cerdas da pata', acao='criar forças de Van der Waals', dados={},
                      importancia='critica', obrigatoria=True)
            c['fala'] = 'Nessas patas, as *cerdas* criam forças de Van der Waals.'
    return v


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    import main
    from src import acervo, fontes, roteiro, viabilidade
    from src.v2 import checkpoint, prevalidacao
    monkeypatch.setenv('MOTOR_VISUAL', 'v2')
    monkeypatch.delenv('EVIDENCIA_V1', raising=False)
    monkeypatch.setenv('APROVACAO', '0')
    monkeypatch.setattr(main, 'RAIZ', tmp_path)
    chamadas = {'tema': 0, 'pesquisa': 0, 'acervo': 0, 'roteiro': 0, 'prompts': [], 'reparo': []}

    def tema(p):
        chamadas['tema'] += 1
        return {'pergunta': 'Por que as lagartixas conseguem andar no teto sem cair?', 'pedido': p, 'termos': ['lagartixa']}

    def pesquisa(*a, **k):
        chamadas['pesquisa'] += 1
        return FATOS, ['Wikipédia'], 'https://pt.wikipedia.org', {'epoca': 'atual'}

    def coleta(tema_, dossie, pasta):
        chamadas['acervo'] += 1
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / 'a0.jpg').write_bytes(b'foto da lagartixa')
        (pasta / 'a3.jpg').write_bytes(b'foto da sola')
        return [{'id': 'a0', 'arq': pasta / 'a0.jpg', 'mostra': 'Lagartixa no teto', 'titulo': 'gecko', 'tipo_img': 'foto', 'mini': b'm'},
                {'id': 'a3', 'arq': pasta / 'a3.jpg', 'mostra': 'Foto em close das cerdas microscópicas na sola da pata de uma lagartixa',
                 'titulo': 'gecko foot', 'ano': 2009, 'tipo_img': 'foto'}]

    def melhor(prompt, serie=False):
        chamadas['roteiro'] += 1
        chamadas['prompts'].append(prompt)
        return _roteiro()

    ident = lambda v, *a, **k: v
    monkeypatch.setattr(roteiro, 'tema_livre', tema)
    monkeypatch.setattr(fontes, 'coletar', pesquisa)
    monkeypatch.setattr(acervo, 'coletar', coleta)
    monkeypatch.setattr(acervo, 'complementar', lambda v, ac, pasta: ac)
    monkeypatch.setattr(acervo, 'casar', ident)
    monkeypatch.setattr(acervo, 'preencher', ident)
    monkeypatch.setattr(roteiro, 'decidir_partes', lambda *a: 1)
    monkeypatch.setattr(viabilidade, 'classificar', lambda *a: 'geral')
    monkeypatch.setattr(viabilidade, 'avaliar', lambda *a: {'ok': True, 'especificas': 1, 'uteis': 1, 'videos': 0})
    monkeypatch.setattr(roteiro, '_melhor_de_dois', melhor)
    for nome in ('revisar', 'escolher_gancho', 'geocodificar', '_planos_sem_foto'):
        monkeypatch.setattr(roteiro, nome, ident)
    monkeypatch.setattr(prevalidacao, '_chamar_padrao',
                        lambda p: chamadas['reparo'].append(p) or {'contratos': [{'id': 'e5', 'impossivel': 'fatos sem as etapas'}]})
    monkeypatch.setattr(main, '_tg', lambda *a, **k: False)
    monkeypatch.setattr(main, 'telegram', lambda *a, **k: pytest.fail('nada vai ao Telegram'))
    monkeypatch.setattr(main, '_midia_do_acervo', lambda v, trab: (_ for _ in ()).throw(Parada('parada do teste: preparo passou')))
    yield main, chamadas, tmp_path
    checkpoint.desativar()


def _rodar(main, monkeypatch, *args):
    monkeypatch.setattr(sys, 'argv', ['main.py', *args])
    main.main()
    dia = next((main.RAIZ / 'saida').iterdir())
    return dia


def test_fluxo_real_bloqueia_no_preparo_e_retoma_do_checkpoint_editado(ambiente, monkeypatch):
    main, chamadas, raiz = ambiente
    dia = _rodar(main, monkeypatch, '--curiosidade', 'lagartixa no teto')

    # 1ª execução: bloqueio legítimo, diagnóstico e checkpoint preservados
    st = json.loads((dia / 'status_execucao.json').read_text())
    assert st['status'] == 'BLOQUEADO_PREPARO' and st['mp4'] is None
    # V2.4: e6 (mecanismo crítico com etapas em frases inteiras) também bloqueia — viraria cartão de texto
    assert [b['evento'] for b in st['bloqueios_preparo']] == ['e5', 'e6'] and st['contratos_pendentes'] == ['e5']
    assert any('ILUSTRAÇÃO' in f for f in st['bloqueios_preparo'][0]['faltam'])
    assert any('mecanismo.estados' in f for f in st['bloqueios_preparo'][1]['faltam'])
    prep = json.loads(next(dia.glob('*-preparo.json')).read_text())
    assert prep['contratos']['reparo']['recusados'][0]['evento'] == 'e5'
    assert chamadas == {**chamadas, 'tema': 1, 'pesquisa': 1, 'acervo': 1, 'roteiro': 1} and len(chamadas['reparo']) == 1
    assert 'DADOS EXIGIDOS POR TIPO' in chamadas['prompts'][0] and 'enfraquece rapidamente' in chamadas['prompts'][0]
    ck = dia / 'checkpoint'
    assert set(json.loads((ck / 'manifesto.json').read_text())['etapas']) == {'tema', 'pesquisa', 'acervo', 'roteiro'}

    # correção à mão do contrato no checkpoint (registrada), e retomada
    rot = json.loads((ck / 'roteiro.json').read_text())
    esquema = {'objetos': [{'id': 'par', 'forma': 'superficie', 'rotulo': 'PAREDE', 'y': .08, 'w': 1},
                           {'id': 'esp', 'forma': 'ramos', 'rotulo': 'CERDAS DA PATA', 'y': .8, 'w': .8, 'lado': 'cima'}],
               'estados': [{'rotulo': 'LONGE', 'objetos': {'esp': {'dy': .08}}},
                           {'rotulo': 'ENCOSTA: AS MOLÉCULAS SE ATRAEM', 'objetos': {'esp': {'dy': -.3}},
                            'relacoes': [{'de': 'esp', 'para': 'par', 'tipo': 'atracao', 'forca': 1, 'rotulo': 'ATRAÇÃO'}]}]}
    for c in rot['v']['cenas']:
        if (c.get('acontecimento') or {}).get('id') in ('e5', 'e6'):    # V2.4: o conserto agora é o ESQUEMA demonstrativo
            c['acontecimento']['dados'] = {'esquema': esquema}
    origem = raiz / 'checkpoint_origem'
    import shutil
    shutil.copytree(ck, origem)
    (origem / 'roteiro.json').write_text(json.dumps(rot, ensure_ascii=False))
    shutil.rmtree(dia)
    from src.v2 import checkpoint
    checkpoint.desativar()
    dia = _rodar(main, monkeypatch, '--retomar', str(origem))

    assert chamadas['tema'] == 1 and chamadas['pesquisa'] == 1 and chamadas['acervo'] == 1 and chamadas['roteiro'] == 1
    assert len(chamadas['reparo']) == 1                         # nada pendente: o conserto não chama a IA de novo
    prep = json.loads(next(dia.glob('*-preparo.json')).read_text())
    assert prep['bloqueios'] == []
    e5 = next(e for e in prep['eventos'] if e['id'] == 'e5')
    assert e5['representacao'] == {'modo': 'composicao', 'comp': 'mecanismo.estados'}
    pv = {e['evento']: e for e in prep['previa']['eventos']}                # V2.4: prévia renderizada antes da narração
    assert pv['e5']['ok'] and pv['e5']['comp'] == 'mecanismo.estados' and len(pv['e5']['quadros']) == 3
    assert (next(dia.glob('*-previa')) / 'folha.jpg').exists()
    assert e5['funcao'] == 'ilustracao' and e5['ilustracao']['nao_prova'] and e5['evidencia_visual'] is False
    assert prep['checkpoint']['carregadas'] == ['roteiro']
    assert any('acontecimento.dados' in m for m in prep['checkpoint']['editado']['roteiro'])
    st = json.loads((dia / 'status_execucao.json').read_text())
    assert st['status'] == 'FALHA_OPERACIONAL' and 'parada do teste' in st['motivo']     # parou antes da mídia, sem MP4


def test_status_nunca_declara_mp4_sem_arquivo(tmp_path, monkeypatch):
    import main
    monkeypatch.setenv('MOTOR_VISUAL', 'v2')
    main._status_v2(tmp_path, 'APROVADO_FISCAL', {}, mp4=tmp_path / 'nao_existe.mp4')
    assert json.loads((tmp_path / 'status_execucao.json').read_text())['status'] == 'FALHA_OPERACIONAL'
    (tmp_path / 'v.mp4').write_bytes(b'x')
    main._status_v2(tmp_path, 'MP4_GERADO', {'_bloqueado': 'fiscal'}, mp4=tmp_path / 'v.mp4', motivo='fiscal')
    assert json.loads((tmp_path / 'status_execucao.json').read_text())['status'] == 'MP4_GERADO'


def test_producao_nao_grava_status(tmp_path, monkeypatch):
    import main
    monkeypatch.delenv('MOTOR_VISUAL', raising=False)
    main._status_v2(tmp_path, 'BLOQUEADO_PREPARO', {})
    assert not (tmp_path / 'status_execucao.json').exists()
