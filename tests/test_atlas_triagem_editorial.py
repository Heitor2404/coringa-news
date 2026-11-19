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
