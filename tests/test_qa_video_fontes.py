"""Fallback honesto + 3 fontes reais; não simular prova histórica pela etiqueta."""
import json
from pathlib import Path
import pytest
from src.v4.formatos import qa_video_fontes as Q

ROOT=Path(__file__).resolve().parents[1]


def _uso(evento='Guerra do Iraque',origem='Guerra do Iraque',uso='registro',
         especifica=True,rotulo='',licenca=True,proveniencia=True):
    return Q.decidir_uso(acontecimento=evento,evento_da_midia=origem,
                        uso=uso,cena_especifica=especifica,rotulo=rotulo,
                        origem_verificada=proveniencia,licenca_verificada=licenca)


def test_outro_conflito_nunca_e_registro_do_iraque():
    d=_uso(origem='Guerra da Síria')
    assert not d['permitido'] and d['codigo']=='M-OUTRO-EVENTO-NAO-E-PROVA'


def test_outro_conflito_na_cena_especifica_nao_pode_entrar_com_legenda():
    d=_uso(origem='Guerra da Síria',uso='ilustracao',
           rotulo='IMAGENS ILUSTRATIVAS · Guerra da Síria')
    assert not d['permitido'] and d['codigo']=='M-SUBSTITUICAO-ENGANOSA'


def test_outro_conflito_so_entra_em_explicacao_generica_com_identidade_revelada():
    r=_uso(origem='Guerra da Síria',uso='contexto',especifica=False,
           rotulo='CENAS DA GUERRA DA SÍRIA · CONTEXTO ILUSTRATIVO')
    assert r['permitido'] and r['prova_do_fato'] is False
    assert r['categoria']=='CONTEXTO_OU_ILUSTRACAO'


def test_nao_basta_uma_legenda_generica_para_esconder_outro_evento():
    r=_uso(origem='Guerra da Síria',uso='contexto',especifica=False,
           rotulo='IMAGENS DE ARQUIVO')
    assert not r['permitido'] and r['codigo']=='M-ORIGEM-NAO-IDENTIFICADA'


@pytest.mark.parametrize('licenca,proveniencia',[(False,True),(True,False)])
def test_sem_licenca_ou_fonte_nao_entra(licenca,proveniencia):
    assert _uso(licenca=licenca,proveniencia=proveniencia)['codigo']=='M-SEM-PROVENIENCIA'


def test_registro_real_e_candidato_nao_prova_automaticamente():
    r=_uso()
    assert r['permitido'] and r['categoria']=='REGISTRO_CANDIDATO'
    assert r['prova_do_fato'] is False


def test_3_dominios_manifestados_nao_sao_clipes_de_um_so_tema():
    p=json.loads((ROOT/'docs/v4/formatos/qa_fontes_tres_videos.json').read_text())
    assert {x['dominio'] for x in p['itens']}==set(Q.DOMINIOS)
    assert all(x['pagina'].startswith('https://commons.wikimedia.org/wiki/File:')
               and x['licenca'] and x['autor'] for x in p['itens'])
    assert p['itens'][0]['arquivo']!=p['itens'][1]['arquivo']
    assert p['itens'][-1]['sha1_esperado']


def test_nao_confunde_pixels_com_informacao_real():
    from src.v4.formatos import contrato_visual_comum as C
    assert C.julgar_inspecao(
        'DEMONSTRAR', False, {'referente_visivel': True,
                             'enquadramento_adequado':True,
                             'imagem_celular_legivel':True,
                             'aprendizado_demonstrado':False,
                             'acao_ou_relacao_visivel':False})
