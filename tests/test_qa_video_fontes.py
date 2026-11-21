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


def test_gates_compartilhados_reprovam_outro_conflito_como_iraque():
    import copy
    from src.v4.formatos import contrato_visual_comum as C
    from src.v4.formatos import filme_editorial, triagem_editorial
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    filme=json.loads((root/'docs/v4/formatos/filme_taiwan_prova.json').read_text())
    filme['shots'][0]['substituicao']={
        'acontecimento':'Guerra do Iraque','evento_da_midia':'Guerra da Síria',
        'uso':'registro','cena_especifica':True,
        'rotulo':'GUERRA NO IRAQUE', 'origem_verificada':True,
        'licenca_verificada':True,
    }
    common=C.auditar(filme)
    assert not common['estrutura_declarada_ok']
    assert 'M-OUTRO-EVENTO-NAO-E-PROVA' in {x['codigo'] for x in common['falhas']}
    assert not filme_editorial.avaliar(filme)['pronto']

    atlas={
        'formato':'atlas','narracao':{'fatos':[{'id':'f1','fontes':['fonte verificada']}]},
        'beats':[{'id':'b1','composicao':'atlas.prova','fatos':['f1'],
          'direcao_visual':{'verbo':'MOSTRAR','pergunta':'Qual guerra?',
            'referente':'Filmagem documental do combate',
            'aprendizado':'Onde o acontecimento ocorreu e o que aconteceu',
            'provas':['foto'],
            'substituicao':filme['shots'][0]['substituicao']},
          'camadas':[{'id':'foto','componente':'atlas.provaVisual',
                      'p':{'asset':'foto-contexto'}}]}]
    }
    cat={'itens':[{'id':'foto-contexto','sha256_origem':'a'*64,
                   'licenca':'CC BY 4.0','prova':{'midia_corresponde':True}}]}
    r=triagem_editorial.avaliar(atlas,cat)
    assert not r['pronto']
    assert 'M-OUTRO-EVENTO-NAO-E-PROVA' in {x['codigo'] for x in r['bloqueios']}


def test_contexto_de_outro_evento_aceito_somente_com_rotulo_nunca_prova():
    from src.v4.formatos import contrato_visual_comum as C
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    filme=json.loads((root/'docs/v4/formatos/filme_taiwan_prova.json').read_text())
    filme['shots'][0]['substituicao']={
        'acontecimento':'Guerra do Iraque','evento_da_midia':'Guerra da Síria',
        'uso':'contexto','cena_especifica':False,
        'rotulo':'IMAGENS DA GUERRA DA SÍRIA · CONTEXTO',
        'origem_verificada':True,'licenca_verificada':True,
    }
    r=C.auditar(filme)
    assert r['estrutura_declarada_ok']
    assert r['prova_visual']=='NAO_INSPECIONADA'
    assert r['aprovacao_humana']=='PENDENTE'


def _processo(*, narrado="deposicao_metalica_em_wafer",
             filmado="deposicao_metalica_em_wafer", atribuicao=False,
             compatibilidade=True, origem="Laboratorio NIST"):
    return Q.decidir_uso(
        acontecimento="Fabricacao industrial em Taiwan",
        evento_da_midia="Laboratorio NIST", uso="demonstracao",
        cena_especifica=True, rotulo="",
        origem_verificada=True, licenca_verificada=True,
        representacao={
            "tipo":"processo_equivalente",
            "processo_narrado":narrado,
            "processo_midia":filmado,
            "compatibilidade_tecnica_verificada":compatibilidade,
            "evidencia_inspecao":"frames verificam deposicao no wafer",
            "fala_atribui_registro":atribuicao,
            "origem_no_credito":origem,
        })


def test_demonstracao_equivalente_de_laboratorio_fora_do_pais_pode_ilustrar():
    d=_processo()
    assert d["permitido"] and d["categoria"]=="ILUSTRACAO_TECNICA"
    assert d["prova_do_fato"] is False
    assert d["aprovacao_humana"]=="PENDENTE"


def test_demonstracao_nao_converte_e_beam_em_euv():
    d=_processo(narrado="litografia_euv",filmado="litografia_e_beam")
    assert not d["permitido"] and d["codigo"]=="M-PROCESSO-NAO-EQUIVALENTE"


def test_demonstracao_nao_pode_ser_narrada_como_filmagem_da_entidade():
    d=_processo(atribuicao=True)
    assert not d["permitido"] and d["codigo"]=="M-REGISTRO-NAO-REPRESENTAVEL"


def test_demonstracao_sem_inspecao_tecnica_ou_credito_real_nao_e_aprovada():
    assert not _processo(compatibilidade=False)["permitido"]
    assert _processo(origem="Banco de imagens")["codigo"]=="M-ORIGEM-NAO-IDENTIFICADA"


def test_contrato_compartilhado_permite_equivalente_sem_confundir_registro():
    from src.v4.formatos import contrato_visual_comum as C
    filme=json.loads((ROOT/'docs/v4/formatos/filme_taiwan_prova.json').read_text())
    rep = {
        "tipo":"processo_equivalente",
        "processo_narrado":"deposicao_metalica_em_wafer",
        "processo_midia":"deposicao_metalica_em_wafer",
        "compatibilidade_tecnica_verificada":True,
        "evidencia_inspecao":"quadros inspecionados mostram processo de deposicao",
        "fala_atribui_registro":False,
        "origem_no_credito":"Laboratorio NIST · tecnica de deposicao",
    }
    filme['shots'][0]['substituicao']={
        'acontecimento':'Processo industrial em Taiwan',
        'evento_da_midia':'Laboratorio NIST',
        'uso':'demonstracao','cena_especifica':True,
        'origem_verificada':True,'licenca_verificada':True,
        'representacao':rep,
    }
    r=C.auditar(filme)
    assert r['estrutura_declarada_ok']
    assert r['aprovacao_humana']=='PENDENTE'
    filme['shots'][0]['substituicao']['representacao']['processo_midia']='litografia_euv'
    r=C.auditar(filme)
    assert 'M-PROCESSO-NAO-EQUIVALENTE' in {x['codigo'] for x in r['falhas']}
