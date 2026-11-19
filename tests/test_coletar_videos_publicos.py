"""Coleta realista sem rede: qualquer tema, licença pendente e sem promoção."""
import copy
import json
from pathlib import Path

import pytest
from src.v4.formatos import coletar_videos_publicos as C

ROOT=Path(__file__).resolve().parents[1]
RECEITA=ROOT/"docs/v4/formatos/CANDIDATOS_VIDEO_INSTITUCIONAL_20261119.json"


def fonte():
    return json.loads(RECEITA.read_text(encoding="utf8"))["itens"][0]


@pytest.mark.parametrize("tema",["taiwan_industria","venezuela_geografia","historia_tecnologia","suez_engenharia"])
def test_candidato_dvids_e_reutilizavel_sem_mudar_codigo(tmp_path,tema):
    f=fonte()
    f["tema"]=tema
    dados=b"FAKE_MP4_TEST_ONLY"*7200
    def baixar(item,dest):
        dest.write_bytes(dados)
    def inspecionar(p):
        return {"largura":1280,"altura":720,"duracao_s":104.0,"codec":"h264"}
    def quadros(p,dest,dur):
        dest.write_bytes(b"contato_falso_teste")
        return {"amostras":12,"tempos_s":list(range(12)),
                "estado":"QUADROS_EXTRAIDOS_SEM_INTERPRETACAO_DA_ACAO"}
    pasta=tmp_path/"fontes"
    r=C.executar({"versao":1,"itens":[f]},pasta,
                 tmp_path/"biblioteca.sqlite3",tmp_path/"armazenamento_v3",
                 baixar=baixar,inspecionar=inspecionar,quadros=quadros)
    assert r["baixados"]==1
    assert r["aprovados_editorialmente"]==0 and r["liberados_publicacao"]==0
    assert r["gastos_ia_usd"]==0
    v=r["fontes"][0]
    assert v["status"]=="CANDIDATO_BAIXADO_NAO_HOMOLOGADO"
    assert v["uso_comercial"]!="sim"
    assert not v["acao_fisica_comprovada"] and not v["publicado"]
    assert v["id_v3"].startswith("cm-")
    assert (pasta/"relatorio.json").is_file()
    assert (pasta/"manifesto_v3.jsonl").is_file()
    from src.v3.biblioteca import Biblioteca
    bib=Biblioteca(db=tmp_path/"biblioteca.sqlite3",armazem=tmp_path/"armazenamento_v3")
    try:
        assert bib.obter(v["id_v3"])["uso_comercial"]!="sim"
        assert bib.verificar()["ok"]==1
    finally:
        bib.fechar()


@pytest.mark.parametrize("campo,valor",[
    ("provedor","site_aleatorio"),("id","../dest"),
    ("video_id","999abc"),("download_id","../../senha"),
    ("pagina","https://falso.example/video/1029228/roubo"),
    ("pagina","http://www.dvidshub.net/video/1029228/microelectronics"),
    ("pagina","https://www.dvidshub.net/video/000001/outro"),
    ("autorizar_publicacao",True),
    ("situacao_direitos","PUBLIC_DOMAIN_LIBERADO_SEM_REVISAO"),
    ("credito",""),
])
def test_bloqueia_origem_invalida_e_aprovacao_falsa(campo,valor):
    f=fonte()
    f[campo]=valor
    with pytest.raises(ValueError):
        C.validar_fonte(f)


def test_download_recusado_nunca_vira_prova_ou_video_independente(tmp_path):
    def nao_baixa(f,p):
        raise PermissionError("HTTP 403: site exige conta para baixar")
    r=C.executar({"versao":1,"itens":[fonte()]},tmp_path/"prova",
                 tmp_path/"biblioteca.sqlite3",tmp_path/"armazem",baixar=nao_baixa)
    assert r["baixados"]==0
    assert r["fontes"][0]["status"]=="SEM_VIDEO_VERIFICADO"
    assert r["fontes"][0]["tipo_erro"]=="PermissionError"
    assert not r["fontes"][0]["acao_fisica_comprovada"]


def test_arquivo_truncado_nao_e_homologado(tmp_path):
    def truncado(f,p):p.write_bytes(b"truncado")
    r=C.executar({"versao":1,"itens":[fonte()]},tmp_path/"p",
                 tmp_path/"db.sqlite3",tmp_path/"armazem",baixar=truncado)
    assert r["baixados"]==0
    assert not (tmp_path/"p"/(fonte()["id"]+".mp4")).exists()


def test_receitas_invalidas_rejeitadas_antes_de_rede(tmp_path):
    f=fonte()
    with pytest.raises(ValueError):
        C.executar({"versao":1,"itens":[f,f]},tmp_path/"p",tmp_path/"db",tmp_path/"a")
    with pytest.raises(ValueError):
        C.executar({"versao":2,"itens":[f]},tmp_path/"p",tmp_path/"db",tmp_path/"a")


def test_duas_fontes_mesmos_bytes_nao_contam_como_provas_independentes(tmp_path):
    receita=json.loads(RECEITA.read_text(encoding="utf8"))
    def baixar(f,p):p.write_bytes(b"FAKE_MP4_SAME_SOURCE"*6000)
    def info(p):return {"largura":1280,"altura":720,"duracao_s":20}
    def contato(p,d,dur):
        d.write_bytes(b"preview")
        return {"amostras":12,"tempos_s":[]}
    r=C.executar(receita,tmp_path/"p",tmp_path/"db",tmp_path/"armazem",
                 baixar=baixar,inspecionar=info,quadros=contato)
    assert r["baixados"]==2 and r["aprovados_editorialmente"]==0
    assert len({x["id_v3"] for x in r["fontes"]})==1  # V3 deduplicou SHA
    assert not any(x["acao_fisica_comprovada"] for x in r["fontes"])


def nist():
    p=ROOT/"docs/v4/formatos/CANDIDATOS_VIDEO_NIST_NANOFAB_20261119.json"
    return json.loads(p.read_text(encoding="utf8"))["itens"][0]


def test_nist_kaltura_usa_mesma_biblioteca_e_nao_aprova(tmp_path):
    fonte=nist()
    C.validar_fonte(fonte)
    def baixar(f,d):
        assert f["entry_id"]=="0_emhevqw5"
        d.write_bytes(b"VIDEO TESTE NAO REAL"*7000)
    def metadados(p):
        return {"largura":1280,"altura":720,"duracao_s":145.0}
    def frames(p,d,dur):
        d.write_bytes(b"folha")
        return {"amostras":12,"tempos_s":[10,20]}
    r=C.executar({"versao":1,"itens":[fonte]},tmp_path/"candidatos",
                 tmp_path/"bib.sqlite3",tmp_path/"armazem",
                 baixar=baixar,inspecionar=metadados,quadros=frames)
    assert r["baixados"]==1 and r["aprovados_editorialmente"]==0
    assert r["fontes"][0]["uso_comercial"]=="indefinido"
    assert r["fontes"][0]["acao_fisica_comprovada"] is False


@pytest.mark.parametrize("campo,valor",[
    ("entry_id","../malicioso"),("partner_id","123456"),
    ("pagina","https://www.nist.gov.evil.example/video/a"),
    ("pagina","https://www.nist.gov/arquivo/nao-video"),
    ("situacao_direitos","LIBERADO"),
    ("autorizar_publicacao",True),
])
def test_nist_recusa_fonte_nao_oficial(campo,valor):
    f=nist()
    f[campo]=valor
    with pytest.raises(ValueError):
        C.validar_fonte(f)


def test_nist_url_kaltura_é_derivada_do_id_oficial(tmp_path,monkeypatch):
    f=nist()
    comandos=[]
    def executar(cmd,**kwargs):
        comandos.append(cmd)
        (tmp_path/"arquivo.mp4").write_bytes(b"mp4")
        return None
    monkeypatch.setattr(C.subprocess,"run",executar)
    C.baixar_nist(f,tmp_path/"arquivo.mp4")
    assert comandos and comandos[0][-1]=="kaltura:684682:0_emhevqw5"
    assert "60M" in comandos[0]
