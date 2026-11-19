"""Animatic de estilo fiel ao renderer, sem TTS nem áudio fictício."""
import json

from src.v4.formatos.animatic import palavras_provisorias, preparar


def test_marcadores_provisorios_nao_sao_fala_real():
    meta = palavras_provisorias('A fábrica tem muitos circuitos.')
    assert len(meta['palavras']) == 5
    assert meta['origem'] == 'SIMULACAO_VISUAL_SEM_VOZ'
    assert meta['palavras'][0]['s'] == 0
    assert meta['duracao'] >= meta['palavras'][-1]['e']


def test_animatic_bloqueia_antigo_piloto_antes_de_fazer_voz(tmp_path):
    from pathlib import Path
    arq = (Path(__file__).resolve().parents[1] /
           'src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json')
    p = json.loads(arq.read_text())
    res = preparar(p, tmp_path, catalogo={'itens': []}, recolher=False)
    assert not res['pronto']
    assert res['etapa'] == 'triagem'
    assert not (tmp_path / 'narracao.json').exists()


def test_palavras_provisorias_resolvem_ancora_simples():
    from src.v4.formatos import plano as P
    m = palavras_provisorias('A fábrica fica em Taiwan.')
    assert P.ancora('@taiwan', m['palavras']) > 0
