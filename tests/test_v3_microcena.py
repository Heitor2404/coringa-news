"""Recorte de microcena: um acontecimento do tipo pedido, ~5–8 s, escolhido por regra (sem storyboard manual)."""
import pytest

import tests.v3_material as M
from src.v3 import microcena, pipeline


@pytest.mark.parametrize('perfil,tipos', [('historia', {'impacto', 'evento_historico', 'pessoa', 'lugar', 'documento'}),
                                          ('geografia', {'deslocamento', 'territorio', 'localizacao'}),
                                          ('biologia', {'mecanismo', 'processo', 'transformacao', 'movimento'}),
                                          ('ciencia', {'processo', 'transformacao', 'mecanismo', 'orbita', 'nivel', 'movimento'})])
def test_recorte_escolhe_acontecimento_do_perfil_e_cabe_em_5_8s(perfil, tipos):
    v = M.roteiro()
    r = microcena.recortar(v, perfil)
    mc = r['_microcena']
    assert mc['tipo'] in tipos and 8 <= mc['palavras'] <= microcena.PALAVRAS_MAX
    evs = {e['id']: e for e in pipeline.eventos_de(v)}
    assert set(mc['trechos_originais']) <= set(evs[mc['evento']]['trechos'])        # não mistura outro acontecimento
    assert [c['fala'] for c in r['cenas']] == [v['cenas'][t]['fala'] for t in mc['trechos_originais']]


def test_historia_prefere_a_abertura():
    assert microcena.recortar(M.roteiro(), 'historia')['_microcena']['trechos_originais'][0] == 0


def test_sem_acontecimento_do_tipo_bloqueia_com_motivo():
    v = M.roteiro()
    for c in v['cenas']:
        if (c.get('acontecimento') or {}).get('tipo') in ('deslocamento', 'territorio', 'localizacao'):
            c['acontecimento']['tipo'] = 'impacto'
    with pytest.raises(ValueError, match='não tem acontecimento'):
        microcena.recortar(v, 'geografia')
