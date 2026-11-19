"""Integração SEM rede do adaptador de mídia com FilmeEditorial preexistente.

Não usa fotos históricas, IA, TTS ou publicação. Verifica que o fluxo
positivo gera props reais e que o relatório só diz o que foi autenticado.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.v4.formatos import montagem_privada_real as M


def receita(tema:str):
    assets={}
    cenas=[]
    for i in range(3):
        mid=f"grafico_{i}"
        fonte=("https://www.sec.gov/Archives/edgar/data/1046179/000104617924000036/a20240404.htm"
               if i==0 else
               "https://www.sec.gov/Archives/edgar/data/1046179/000104617924000038/a20240405.htm"
               if i==1 else "https://pr.tsmc.com/english/news/3338")
        assets[mid]={
            "modo":"grafico","pagina":fonte,"licenca":"CC0",
            "credito":f"Infografia original {tema} {i}",
            "dados":{"design":"numero",
                     "etiqueta":f"CONTEXTO {tema} {i}",
                     "valor":f"{i+2}0%",
                     "linha1":"RESULTADO FICTICIO",
                     "linha2":"SOMENTE TESTE",
                     "fracao":(i+2)/10,
                     "rotulo_fonte":"Fonte: fixture de teste"}
        }
        cenas.append({
            "id":f"cena_{i}","asset":mid,"segundos":2.8,
            "lead":f"{i+1} PROVA","headline":f"EVENTO {i} REPRESENTADO",
            "subject":"Gráfico original fictício apenas de teste",
            "cue":"INFORMAÇÃO NOVA",
            "highlight":"EVENTO",
            "intencao":"explicar_contexto",
            "aprendizado":f"Contextualizar o evento visual {i} sem criar filme final",
            "evidence":"representative"
        })
    return {"versao":1,"tipo":"PROVA_VISUAL_PRIVADA",
            "publicar":False,"titulo":tema,"assets":assets,"cenas":cenas}


@pytest.mark.parametrize("tema",["engenharia","historia","economia","biologia"])
def test_montagem_reusa_filme_editorial_gerando_props_reais(tmp_path,monkeypatch,tema):
    monkeypatch.chdir(tmp_path)
    r=M.preparar_receita(receita(tema),Path("saida"),Path("public"))
    assert r["pronto"] and r["shots"]==3
    assert r["fontes_com_direitos_pendentes"]==[]
    p=json.loads(Path("saida/props.json").read_text())
    assert p["preview"] and not p["private_review_only"]
    assert len(p["shots"])==3
    assert all(s["graphic_original"] is True for s in p["shots"])
    assert all(Path("public",s["asset"]).is_file() for s in p["shots"])
    prov=json.loads(Path("saida/proveniencia.json").read_text())
    assert prov["status"]=="PREVIA_PRIVADA_NAO_PUBLICAR"
    assert not prov["sem_aprovacao_visual"] is False
    assert not prov["sem_narracao"] is False
    assert len(prov["fontes"])==3
    assert all(x["sha256"] and len(x["sha256"])==64 for x in prov["fontes"])


def test_nao_permite_trocar_SHA_de_arquivo_ja_autenticado(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("midia").mkdir()
    original=Path("midia/original.mp4")
    original.write_bytes(b"fake bytes are only for hash test")
    fixado=hashlib.sha256(original.read_bytes()).hexdigest()
    item={"modo":"video_institucional",
          "origem":str(original),
          "sha256_esperado":fixado}
    caminho,sha=M._substituir_arquivo("origem",item,Path("stage_documental"))
    assert sha==fixado and caminho.is_file()
    original.write_bytes(b"arquivo modificado")
    with pytest.raises(ValueError,match="SHA"):
        M._substituir_arquivo("origem",item,Path("stage_documental"))


def test_nunca_monta_para_publicar(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    r=receita("ciencia")
    r["publicar"]=True
    with pytest.raises(ValueError,match="NÃO publicada"):
        M.preparar_receita(r,Path("saida"),Path("public"))


def test_nao_aceita_fonte_nao_existente(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    r=receita("engenharia")
    r["cenas"][0]["asset"]="inventado"
    with pytest.raises(ValueError,match="mídia inexistente"):
        M.preparar_receita(r,Path("saida"),Path("public"))


def test_grafico_nao_e_foto_de_acontecimento(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    r=receita("fisica")
    # Prova original do canal é uma explicação. Nunca rotular como
    # registro literal do fenômeno representado.
    r["cenas"][0]["evidence"]="literal"
    r["cenas"][0]["identidade_literal"]="Fenômeno físico filmado em fábrica"
    with pytest.raises(ValueError,match="F-GRAFICO-COMO-REGISTRO"):
        M.preparar_receita(r,Path("saida"),Path("public"))



def test_ponte_mapa_nao_copia_original_para_stage_documental(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    mapa=Path("stage_atlas/taiwan/mapa.mp4")
    mapa.parent.mkdir(parents=True,exist_ok=True)
    mapa.write_bytes(b"MP4_ATLAS_FICTICIO_SOMENTE_TESTE")
    sha=hashlib.sha256(mapa.read_bytes()).hexdigest()
    result,h=M._substituir_arquivo("mapa_de_teste",{
        "modo":"atlas_map","origem":str(mapa),"sha256_esperado":sha
    },Path("stage_documental"))
    assert result==mapa
    assert h==sha
    assert not Path("stage_documental/mapa_de_teste.mp4").exists()



def test_renderizadores_usan_o_diretorio_dos_assets_comprovados():
    root=Path(__file__).resolve().parents[1]
    for name in (
        ".github/workflows/qa-montagem-real-privada.yml",
        ".github/workflows/filme-editorial-prova-visual.yml",
        ".github/workflows/filme-editorial-panama-12s.yml",
        ".github/workflows/filme-editorial-panama-8s-causal.yml",
        ".github/workflows/filme-editorial-panama-ciclo-19s.yml",
    ):
        texto=(root/name).read_text(encoding="utf8")
        assert "--public-dir=remotion/public" in texto, name
