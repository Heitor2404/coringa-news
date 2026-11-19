"""Recuperação COMPROVADA de fotos já existentes, independente do tema."""
import hashlib
import io
import json

import pytest
from PIL import Image
from src.v4.formatos import estagiar_fotos as E


def origem():
    im=Image.effect_noise((640,720),40)
    b=io.BytesIO()
    im.convert("RGB").save(b,"JPEG",quality=92)
    return b.getvalue()


def catalogo(ident="foto_comprovada",dados=None):
    dados=dados if dados is not None else origem()
    return {"itens":[{
        "id":ident,"natureza":"foto","url":"https://upload.wikimedia.org/wikipedia/commons/3/37/foto.jpg",
        "pagina":"https://commons.wikimedia.org/wiki/File:foto.jpg",
        "wh":[640,720],"licenca":"CC BY 4.0","credito":"Autor original · CC BY 4.0",
        "sha256_origem":hashlib.sha256(dados).hexdigest(),
        "prova":{"midia_corresponde":True,"apenas_piloto_experimental":True}
    }]},dados


def contrato(tema="geografia",ident="foto_comprovada"):
    return {"id":tema,"cenas":[
        {"id":"objeto","midia":{"tipo":"foto","asset_id":ident}},
        {"id":"processo","midia":{"tipo":"video","asset_id":"nao_inferir"}}
    ]}


@pytest.mark.parametrize("tema",["taiwan_industria","venezuela_geografia","suez_engenharia","historia_moderna"])
def test_qualquer_tema_estagia_mesmos_bytes_sem_promover_licenca(tmp_path,monkeypatch,tema):
    monkeypatch.chdir(tmp_path)
    base,bruto=catalogo()
    chamados=[]
    def baixar(url):
        chamados.append(url)
        return bruto
    r=E.preparar(contrato(tema),base, __import__('pathlib').Path("stage_acervo/fotos"),baixar=baixar)
    assert r["relatorio"]["recuperadas"]==1
    assert not r["relatorio"]["autorizacao_publicar"]
    assert not r["relatorio"]["autorizacao_editorial"]
    caminho=r["catalogo"]["itens"][0]["arquivo_local"]
    assert __import__('pathlib').Path(caminho).read_bytes()==bruto
    assert len(chamados)==1
    assert r["catalogo"]["itens"][0]["prova"]["apenas_piloto_experimental"] is True
    assert "arquivo_local" not in base["itens"][0]
    # rodar segunda vez: reuso do cache SHA sem download
    de_novo=E.preparar(contrato(tema),base,__import__('pathlib').Path("stage_acervo/fotos"),
                      baixar=lambda url: (_ for _ in ()).throw(AssertionError("re-download")))
    assert de_novo["relatorio"]["recuperadas"]==1
    assert de_novo["relatorio"]["originais"]["foto_comprovada"]["origem"]=="cache SHA"


def test_nao_confia_em_imagem_adulterada(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    base,bruto=catalogo()
    r=E.preparar(contrato(),base,__import__('pathlib').Path("stage/fotos"),baixar=lambda u:bruto[:-15]+b"ALTERADA")
    assert r["relatorio"]["recuperadas"]==0
    assert "SHA-256" in r["relatorio"]["falhas"][0]["erro"]
    assert "arquivo_local" not in r["catalogo"]["itens"][0]


def test_nao_recupera_licenca_falsa_ou_host_externo(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    base,bruto=catalogo()
    base["itens"][0]["url"]="https://site.invalido/arquivo.jpg"
    r=E.preparar(contrato(),base,__import__('pathlib').Path("stage/fotos"),
                 baixar=lambda u:bruto)
    assert r["relatorio"]["falhas"]
    assert r["relatorio"]["recuperadas"]==0
    base["itens"][0]["url"]="https://upload.wikimedia.org/wikipedia/commons/3/37/foto.jpg"
    base["itens"][0]["prova"]["midia_corresponde"]=False
    r=E.preparar(contrato(),base,__import__('pathlib').Path("stage/fotos"),
                 baixar=lambda u:bruto)
    assert r["relatorio"]["falhas"]
    assert not r["relatorio"]["autorizacao_publicar"]


def test_nao_baixa_video_fingindo_ser_foto(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    r=E.preparar({"cenas":[{"midia":{"tipo":"video","asset_id":"video1"}}]},
                 {"itens":[]},__import__('pathlib').Path("stage/fotos"),
                 baixar=lambda u:(_ for _ in ()).throw(AssertionError("não baixar")))
    assert r["relatorio"]["solicitadas"]==0
    assert r["relatorio"]["recuperadas"]==0


def test_foto_nao_catalogada_continua_bloqueada(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    r=E.preparar(contrato(ident="foto_que_nao_existe"),{"itens":[]},
                 __import__('pathlib').Path("stage/fotos"))
    assert r["relatorio"]["falhas"][0]["asset_id"]=="foto_que_nao_existe"
