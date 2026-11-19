"""Portão positivo multitema com BYTES REAIS de imagens geradas no teste.

NÃO são fotos de acontecimentos históricos: são fixtures CC0 criadas pelo
próprio teste. O teste demonstra que o código sabe autorizar TTS TECNICAMENTE
sem vídeo obrigatório, não que algum filme recebeu aprovação editorial.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from PIL import Image
from src.v4.formatos import gate_filme_completo as G


def _documentario(tmp_path:Path, tema:str, *, rubrica:dict|None=None):
    itens=[]
    cenas=[]
    etapas=[
        ("contexto","MOSTRAR","Mostrar um registro contextual rastreável"),
        ("elo","CONECTAR","Relacionar dois acontecimentos com fonte documental"),
        ("consequencia","REVELAR","Apresentar o resultado concreto desta relação"),
    ]
    t=0.0
    for i,(nome,acao,promessa) in enumerate(etapas):
        arquivo=tmp_path/(nome+".png")
        Image.new("RGB",(720,720),(20+i*70,50+i*55,80+i*30)).save(arquivo)
        bruto=arquivo.read_bytes()
        asset=f"fixture:{tema}:{nome}"
        itens.append({
            "id":asset,"natureza":"foto",
            "arquivo_local":arquivo.name,
            "sha256_origem":hashlib.sha256(bruto).hexdigest(),
            "licenca":"CC0 — imagem sintética produzida pelo teste",
            "credito":"Fixture de CI; não é registro histórico",
            "prova":{"midia_corresponde":True},
        })
        midia={"tipo":"foto","asset_id":asset,"identidade":"explicativa"}
        if acao=="CONECTAR":
            midia.update({
                "fonte_factual":"https://example.org/fonte-primaria-fixture",
                "relacao_visualmente_verificada":True,
            })
        if acao=="REVELAR":
            midia.update({
                "resultado_verificavel":"Resultado fictício e documentado só no fixture",
                "fonte_factual":"https://example.org/resultado-fixture",
            })
        fim=t+(3.3 if i==2 else 2.8)
        cenas.append({"id":nome,"inicio":t,"fim":fim,
                      "acao":acao,"promessa":promessa,"midia":midia})
        t=fim
    manifesto={
        "versao":1,"id":tema,"formato":"filme_editorial",
        "tipo":"PRE_PRODUCAO_PRIVADA",
        "politica":{"publicar":False},
        "duracao_planejada_s":t,
        "base_narracao":{"motor":"gemini","voz":"Charon",
                         "fallback":"bloquear","arquivo_wav":None},
        "rubrica_editorial":rubrica if rubrica is not None else {
            "min_videos_reais_independentes":2,
            "max_fracao_fotos_estaticas":.4,
            "max_foto_individual_s":3.0
        },
        "cenas":cenas,
    }
    return manifesto,{"itens":itens}


@pytest.mark.parametrize("tema",["economia","geografia","historia","ciencia"])
def test_documentario_com_prova_documental_nao_exige_dois_videos(
        tmp_path,monkeypatch,tema):
    monkeypatch.chdir(tmp_path)
    m,cat=_documentario(tmp_path,tema)
    r=G.avaliar(m,cat)  # conferir_bytes=True, verificação de SHA REAL
    assert r["status"]=="PRONTO_PARA_TTS",r["bloqueios"]
    assert r["pronto_para_tts"] is True
    assert r["pronto_para_render"] is False  # WAV real não existe
    assert r["videos_independentes_conferidos"]==0
    assert r["mapas_atlas_comprovados"]==0
    assert r["inspecao_humana"]=="PENDENTE"
    assert r["publicado"] is False
    assert not r["bloqueios"]
    avisos={x["codigo"] for x in r["avisos_editoriais"]}
    assert {"W-DIVERSIDADE-VIDEO","W-SLIDESHOW","W-FOTO-PARADA"}<=avisos


def test_novo_episodio_nao_precisa_de_rubrica_numerica(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    m,cat=_documentario(tmp_path,"episodio_novo",rubrica={})
    r=G.avaliar(m,cat)
    assert r["pronto_para_tts"] is True
    assert "E-RUBRICA" not in {x["codigo"] for x in r["bloqueios"]}


def test_conexao_com_um_documento_precisa_de_fonte_e_relacao(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    m,cat=_documentario(tmp_path,"conexao")
    m["cenas"][1]["midia"].pop("fonte_factual")
    r=G.avaliar(m,cat)
    assert "E-RELACAO-NAO-DEMONSTRADA" in {
        x["codigo"] for x in r["bloqueios"] if x["cena"]=="elo"
    }
    assert not r["pronto_para_tts"]


def test_conclusao_com_foto_necessita_resultado_concreto(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    m,cat=_documentario(tmp_path,"desfecho")
    m["cenas"][2]["midia"].pop("resultado_verificavel")
    r=G.avaliar(m,cat)
    assert "E-PAYOFF-SEM-CONSEQUENCIA" in {
        x["codigo"] for x in r["bloqueios"] if x["cena"]=="consequencia"
    }
    assert not r["pronto_para_tts"]


def test_arquivo_real_adulterado_continua_bloqueado(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    m,cat=_documentario(tmp_path,"hash")
    (tmp_path/"elo.png").write_bytes(b"alterado")
    r=G.avaliar(m,cat)
    assert "E-BYTES-NAO-COMPROVADOS" in {
        x["codigo"] for x in r["bloqueios"] if x["cena"]=="elo"
    }
    assert not r["pronto_para_tts"]


def test_comparacao_visual_ainda_precisa_de_segundo_asset_para_render(
        tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    m,cat=_documentario(tmp_path,"comparacao")
    m["cenas"][1]["midia"].update({"tipo":"comparison","asset_ids":[
        m["cenas"][1]["midia"]["asset_id"]]})
    r=G.avaliar(m,cat)
    assert "E-COMPARACAO-INCOMPLETA" in {
        x["codigo"] for x in r["bloqueios"] if x["cena"]=="elo"
    }
    assert not r["pronto_para_tts"]


def test_somente_metadados_sem_bytes_nao_aprovam_filme(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    m,cat=_documentario(tmp_path,"faltou_imagem")
    (tmp_path/"contexto.png").unlink()
    r=G.avaliar(m,cat)
    assert "E-BYTES-NAO-COMPROVADOS" in {x["codigo"] for x in r["bloqueios"]}
    assert not r["pronto_para_tts"]


def test_foto_nao_e_acompanhamento_de_maquina_real(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    m,cat=_documentario(tmp_path,"acao")
    m["cenas"][1]["acao"]="DEMONSTRAR"
    r=G.avaliar(m,cat)
    assert "E-ACAO-SEM-VIDEO" in {x["codigo"] for x in r["bloqueios"]}
    assert not r["pronto_para_tts"]
