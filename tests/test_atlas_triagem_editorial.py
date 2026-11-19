"""Contrato de evidência audiovisual ATLAS antes de pagar TTS/render."""
import json
from pathlib import Path

from src.v4.formatos.triagem_editorial import avaliar

RAIZ = Path(__file__).resolve().parents[1]


def _plano(*beats):
    return {'formato': 'atlas',
            'narracao': {'fatos': [{'id': 'f1', 'fontes': ['https://example.org/fato']}]},
            'beats': list(beats)}


def _dir(verbo, provas):
    return {'verbo': verbo,
            'pergunta': 'O que a cena precisa tornar compreensível?',
            'referente': 'O objeto concreto que deve aparecer ao público',
            'aprendizado': 'Ao final se entende o papel causal desse objeto',
            'provas': provas}


def test_reprova_piloto_chips_que_passou_no_fiscal_tecnico():
    pl = json.loads((RAIZ / 'src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json')
                    .read_text(encoding='utf-8'))
    res = avaliar(pl)
    assert res['pronto'] is False
    assert res['beats'] == 6
    assert sum(e['codigo'] == 'E-SEM-CONTRATO-VISUAL' for e in res['bloqueios']) == 6


def test_triagem_grava_artefato_de_diagnostico_antes_de_tts(tmp_path):
    from src.v4.formatos.triagem_editorial import main
    plano = json.loads((RAIZ / 'src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json')
                       .read_text(encoding='utf-8'))
    arq = tmp_path / 'plano.json'
    arq.write_text(json.dumps(plano), encoding='utf-8')
    destino = tmp_path / 'reprovado'
    assert main([str(arq), str(destino)]) == 1
    resultado = json.loads((destino / 'triagem_editorial.json').read_text())
    assert not resultado['pronto']
    assert resultado['bloqueios'][0]['codigo'] == 'E-SEM-CONTRATO-VISUAL'


def test_prova_fisica_com_asset_comprovado_passa():
    beat = {'id': 'b1', 'fatos': ['f1'], 'direcao_visual': _dir('MOSTRAR', ['foto-real']),
            'camadas': [{'id': 'foto-real', 'componente': 'atlas.provaVisual',
                         'p': {'asset': 'foto-licenciada'}}]}
    catalogo = {'itens': [{'id': 'foto-licenciada', 'sha256_origem': 'a' * 64,
                          'licenca': 'CC BY 4.0', 'prova': {'midia_corresponde': True}}]}
    assert avaliar(_plano(beat), catalogo)['pronto'] is True


def test_reprova_foto_generica_ou_nao_comprovada():
    beat = {'id': 'b1', 'fatos': ['f1'], 'direcao_visual': _dir('MOSTRAR', ['foto-real']),
            'camadas': [{'id': 'foto-real', 'componente': 'atlas.provaVisual',
                         'p': {'asset': 'foto-sem-comprovacao'}}]}
    assert 'E-MIDIA-NAO-COMPROVADA' in [e['codigo'] for e in
            avaliar(_plano(beat), {'itens': []})['bloqueios']]


def test_proibe_pais_com_etiqueta_como_dependencia_fisica():
    beat = {'id': 'b1', 'fatos': ['f1'], 'direcao_visual': _dir('CONECTAR', ['etiqueta']),
            'camadas': [{'id': 'etiqueta', 'componente': 'editorial.statCard',
                         'p': {'valor': 'MÁQUINAS NA HOLANDA'}}]}
    erros = [e['codigo'] for e in avaliar(_plano(beat))['bloqueios']]
    assert 'E-TEXTO-NAO-E-PROVA' in erros


def test_fluxo_visual_real_pode_demonstrar_dependencia():
    beat = {'id': 'b1', 'fatos': ['f1'], 'direcao_visual': _dir('CONECTAR', ['cadeia']),
            'camadas': [{'id': 'cadeia', 'componente': 'editorial.flowConnections',
                         'p': {'nos': [{'rotulo': 'Projeto'}, {'rotulo': 'Fábrica'}]}}]}
    assert avaliar(_plano(beat))['pronto'] is True


def test_nao_afeta_outros_motores_e_modelos():
    assert avaliar({'formato': 'dossie'})['pronto'] is True
    assert avaliar({'formato': 'ntc'})['pronto'] is True


def test_diretor_atlas_reusa_reprovacao_humana_sem_promover_regra():
    from src.v4.formatos import diretor
    prompt = diretor.prompt(
        [{'id': 'f1', 'texto': 'Fato verificado de uma fábrica'}],
        'atlas', palavras=[], inventario='biblioteca curada')
    assert 'REPROVAÇÕES HUMANAS DOCUMENTADAS' in prompt
    assert 'FB-0009' in prompt
    # A memoria editorial ainda nao tem regras aprovadas. Nao criar aprovacao falsa.
    assert 'REGRAS EDITORIAIS TESTADAS E APROVADAS' not in prompt


def test_telegram_mostra_triagem_sem_preflight_fake(monkeypatch, tmp_path):
    from src.v4.formatos import produzir
    from src.v3 import previa_telegram

    (tmp_path / 'triagem_editorial.json').write_text(json.dumps({
        'pronto': False,
        'bloqueios': [{'codigo': 'E-SEM-CONTRATO-VISUAL',
                       'beat': 'g-01', 'motivo': 'sem objeto e prova'}]
    }), encoding='utf-8')
    enviados = []
    monkeypatch.setattr(previa_telegram, 'chat_autorizado',
                        lambda: ('123', {'tipo': 'private', 'membros': 2}))
    monkeypatch.setattr(previa_telegram, '_api',
                        lambda nome, data: enviados.append((nome, data)))
    resposta = produzir.telegram(tmp_path, 'Chips')
    assert resposta == {'enviado': True, 'sem_mp4': True}
    msg = enviados[0][1]['text']
    assert 'etapa: triagem editorial ANTES DA VOZ' in msg
    assert 'E-SEM-CONTRATO-VISUAL' in msg
    assert 'preflight: 0/0' not in msg


def test_territorio_global_nao_serve_de_pano_de_fundo_ao_wafer():
    beat = {'id': 'b1', 'composicao': 'atlas.protagonista', 'roi': [0, 16, 126, 56],
            'fatos': ['f1'], 'direcao_visual': _dir('CONECTAR', ['cadeia']),
            'camadas': [{'id': 'cadeia', 'componente': 'editorial.flowConnections',
                         'p': {'nos': [{'rotulo': 'Holanda'}, {'rotulo': 'Taiwan'}]}}]}
    erros = [e['codigo'] for e in avaliar(_plano(beat))['bloqueios']]
    assert 'E-MAPA-GLOBAL-DECORATIVO' in erros


def test_mapa_regional_com_prova_nao_e_bloqueado_por_distancia():
    beat = {'id': 'b1', 'composicao': 'atlas.abertura', 'roi': [118, 21, 124, 26],
            'fatos': ['f1'], 'direcao_visual': _dir('LOCALIZAR', ['mapa']),
            'camadas': [{'id': 'pino', 'componente': 'atlas.geoPin',
                         'p': {'tipo': 'local', 'lonlat': [121, 23]}}]}
    assert avaliar(_plano(beat))['pronto'] is True


def test_palco_de_foto_protagonista_e_independente_do_mapa():
    import json
    cfg = json.loads((RAIZ / 'src/v4/formatos/formatos.json').read_text())
    prova = cfg['composicoes']['atlas.prova']
    assert prova['palco'] == 'prova'
    assert prova['slots']['prova']['h'] >= 900
    assert 'prova' in cfg['formatos']['atlas']['palcos']
