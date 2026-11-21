"""Regressão de fonte recuperável na biblioteca V3, sem usar licença como atalho."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.v4.formatos import rehidratar_fontes as R
from src.v3.biblioteca import Biblioteca

RAIZ=Path(__file__).resolve().parents[1]
MANIFESTO=RAIZ/"docs/v4/formatos/FONTES_RECUPERAVEIS_NIST_20261119.json"


def item():
    return json.loads(MANIFESTO.read_text(encoding="utf8"))["itens"][0]


def test_receita_e_kaltura_original_com_sha_e_nao_publicacao():
    m=json.loads(MANIFESTO.read_text(encoding="utf8"))
    assert len(m["itens"])==2
    assert all(x["aprovado_publicacao"] is False for x in m["itens"])
    for x in m["itens"]:
        R.validar_item(x)
        assert len(x["sha256"])==64


@pytest.mark.parametrize("chave,valor",[
    ("provider","qualquer_http"),
    ("partner_id","000000"),
    ("entry_id","outro_site/../script"),
    ("pagina","https://exemplo.com/roubo"),
    ("sha256","hash-falso"),
    ("aprovado_publicacao",True),
    ("formato","worst; rm -rf /"),
])
def test_rejeita_receita_nao_auditada(chave,valor):
    it=item()
    it[chave]=valor
    with pytest.raises(ValueError):
        R.validar_item(it)


def test_rehidrata_reusa_v3_existente_e_nunca_aprova(tmp_path,monkeypatch):
    it=item()
    dados=b"video_falso_so_para_teste_unitario"*3000
    it["sha256"]=hashlib.sha256(dados).hexdigest()
    cache=tmp_path/"cache"
    cache.mkdir()
    video=cache/(it["id"]+".mp4")
    video.write_bytes(dados)
    monkeypatch.setattr(R,"provar_video",lambda p:{"dimensoes":[720,1280],"duracao_s":11.833})
    bib=Biblioteca(db=tmp_path/"bib.sqlite3",armazem=tmp_path/"armazem")
    try:
        primeira=R.reidratar(it,cache,bib)
        segunda=R.reidratar(it,cache,bib)
        assert primeira["status"]=="INGESTAO_V3_CANDIDATA_SEM_APROVACAO"
        assert primeira["id_v3"]==segunda["id_v3"]
        assert segunda["reuso"]=="sha"
        assert primeira["uso_comercial"]!="sim"
        assert bib.verificar()["ok"]==1
    finally:
        bib.fechar()


def test_reidratar_rejeita_bytes_alterados_sem_ingestao(tmp_path,monkeypatch):
    it=item()
    cache=tmp_path/"cache"
    cache.mkdir()
    (cache/(it["id"]+".mp4")).write_bytes(b"falso"*30000)
    def nunca(*args):
        raise AssertionError("não deve chegar a prover o vídeo")
    monkeypatch.setattr(R,"provar_video",nunca)
    bib=Biblioteca(db=tmp_path/"bib.sqlite3",armazem=tmp_path/"armazem")
    try:
        with pytest.raises(ValueError,match="SHA divergente"):
            R.reidratar(it,cache,bib)
        assert bib.verificar()["ok"]==0
    finally:
        bib.fechar()


def test_reidratar_rejeita_link_fora_do_workspace(tmp_path):
    it=item()
    pasta=tmp_path/"cache"
    pasta.mkdir()
    externo=tmp_path/"fora.mp4"
    externo.write_bytes(b"video"*20000)
    (pasta/(it["id"]+".mp4")).symlink_to(externo)
    bib=Biblioteca(db=tmp_path/"bib.sqlite3",armazem=tmp_path/"armazem")
    try:
        with pytest.raises(ValueError,match="fora do workspace"):
            R.reidratar(it,pasta,bib)
    finally:
        bib.fechar()
