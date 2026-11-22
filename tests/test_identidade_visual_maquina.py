"""Nova trava: identidade visual do equipamento != animar um pistão.

São testes de manifesto/estrutura, não pixels. A CI não concede aprovação
estética a um vídeo por passar num esquema desenhado manualmente.
"""
import copy
import json
from pathlib import Path
from src.v4.formatos import identidade_visual_maquina as I

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"docs/v4/formatos/reference_first/identidade_compressor_oficina_tanque_horizontal.json"


def manifest():
    return json.loads(PATH.read_text("utf8"))


def test_compressor_tanque_horizontal_tem_identidade_estrutural_pretendida():
    m=manifest()
    result=I.verificar(m)
    assert result["gate"]=="ESTRUTURA_DECLARADA_OK_VISUAL_NAO_CERTIFICADO"
    assert result["erros"]==[]
    assert result["validacao_por_pixels"]=="NAO_REALIZADA"
    assert result["revisao_humana"]=="PENDENTE"
    assert result["publicar"] is False


def test_pistao_com_tanque_fake_nao_serve_como_compressor_de_oficina():
    old={
        "configuracao":"compressor_ar_eletrico_tanque_horizontal_correia",
        "processo":"compressor_alternativo",
        "publicar":False,
        "pecas":[
            {"id":"cilindro","papel":"piston_cutaway","bbox":[.34,.38,.28,.36]},
            {"id":"tanque_pequeno","papel":"receiver_horizontal","bbox":[.8,.72,.16,.23]},
        ],
        "ligacoes":[],
    }
    result=I.verificar(old)
    assert result["gate"]=="BLOQUEADO"
    assert "F-IDENTIDADE-SEM-COMPONENTES-OBRIGATORIOS" in result["erros"]
    assert "electric_motor" in result["pecas_faltantes"]
    assert "intake_filter" in result["pecas_faltantes"]
    assert "drive_belt" in result["pecas_faltantes"]


def test_pecas_presentes_mas_tubo_desconectado_bloqueiam():
    m=manifest()
    m["ligacoes"]=[x for x in m["ligacoes"] if not (
        x["a"]=="discharge_pipe" and x["b"]=="receiver_horizontal")]
    result=I.verificar(m)
    assert result["gate"]=="BLOQUEADO"
    assert "F-CAMINHO-MECANICO-INCOMPLETO" in result["erros"]
    assert ["discharge_pipe","receiver_horizontal","feeds"] in result["ligacoes_faltantes"]


def test_falso_reservatorio_menor_que_bomba_rejeitado():
    m=manifest()
    for part in m["pecas"]:
        if part["papel"]=="receiver_horizontal":
            part["bbox"]=[.82,.70,.13,.19]
    result=I.verificar(m)
    assert result["gate"]=="BLOQUEADO"
    assert "F-RESERVATORIO-SEM-PROPORCAO-OUPOSICAO" in result["erros"]


def test_nao_fingir_otto_4_tempos_com_mesma_maquina():
    m=manifest()
    m["processo"]="motor_otto_4t"
    result=I.verificar(m)
    assert result["gate"]=="BLOQUEADO"
    assert "F-PROCESSO-VISUAL-DIFERENTE" in result["erros"]


def test_confusao_de_subtipo_tambem_bloqueia():
    m=manifest()
    m["configuracao"]="compressor_parafuso_sem_tanque"
    result=I.verificar(m)
    assert result["gate"]=="BLOQUEADO"
    assert "F-CONFIGURACAO-NAO-CADASTRADA" in result["erros"]


def test_nenhuma_posicao_invalida_ou_rotulo_inventado_passa():
    m=manifest()
    m["pecas"][0]["bbox"]=[.8,.90,.9,.8]
    result=I.verificar(m)
    assert result["gate"]=="BLOQUEADO"
    assert "F-PECA-INVALIDA-OU-DUPLICADA" in result["erros"]
    m=manifest()
    m["pecas"][0]["bbox"]=[True,.8,.1,.1]
    result=I.verificar(m)
    assert result["gate"]=="BLOQUEADO"


def test_mesmo_sucesso_estrutural_nao_autoriza_publicacao_ou_qa_visual():
    m=manifest()
    result=I.verificar(m)
    assert not result["publicar"]
    assert result["validacao_por_pixels"]=="NAO_REALIZADA"
    m["publicar"]=True
    result=I.verificar(m)
    assert result["gate"]=="BLOQUEADO"
    assert "F-PUBLICACAO-BLOQUEADA" in result["erros"]
