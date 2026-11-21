"""Garimpo de animacoes: 2D/video + 3D, roteamento sem inventar conteudo."""
from pathlib import Path

from src.v4.formatos import referencias_mecanismos as R


def brief(actions=None, phases=None):
    return {
        "id": "teste-prova",
        "pergunta": "Como acontece a transferencia de energia entre partes?",
        "consultas_en": ["mechanism operation animation"],
        "acoes_necessarias": actions or ["source","reticle","projection","wafer"],
        "fases_necessarias": phases or ["origem","transformacao","resultado"],
    }


class Response:
    def raise_for_status(self):
        pass
    def json(self):
        return {"results": [{
            "uid": "a1b2c3d4e5f6g7h8",
            "name": "3D optical machine",
            "viewerUrl": "https://sketchfab.com/models/a1b2c3d4e5f6g7h8",
            "downloadable": True,
            "license": {"slug": "by"},
        }]}


def search3d(url, **kwargs):
    assert url == "https://api.sketchfab.com/v3/search"
    assert kwargs["params"]["type"] == "models"
    return Response()


def searchvideo(args):
    assert args["tipo"] == "video"
    return [{
        "titulo":"A visual example",
        "url":"https://commons.wikimedia.org/wiki/File:Example.webm",
        "pagina":"https://commons.wikimedia.org/wiki/File:Example.webm",
        "credito":"Example (CC BY 4.0), Commons",
        "video":{"url":"https://upload.wikimedia.org/example.webm"},
    }]


def observed(ref):
    actions=["source","reticle","projection","wafer"]
    hashes=[format(i+1, "064x") for i in range(5)]
    return [{
        "referencia_id": ref,
        "metodo": "inspecao_ia_quadros",
        "estado":"EVENTOS_VISUAIS_PROVISORIOS",
        "categoria":"RELEVANTE",
        "origem_sha256":"f"*64,
        "quadros": [0.5, 1.4, 3.1, 4.0, 5.0],
        "quadros_sha256":hashes,
        "atores_visiveis": ["source","reticle","optics","wafer"],
        "acoes_visiveis": actions,
        "evidencias":[{"acao":a,"antes":i,"depois":i+1,
                      "hash_antes":hashes[i],"hash_depois":hashes[i+1],
                      "evidencia":"O elemento se desloca entre os dois quadros de forma observavel."}
                     for i,a in enumerate(actions)],
        "fases_visiveis": ["origem","transformacao","resultado"],
    }]


def test_pesquisa_dois_meios_sem_afirmar_aprovacao():
    d=R.descobrir(brief(),buscar=searchvideo,get=search3d)
    assert len(d["candidatos"]) == 2
    assert {x["midia"] for x in d["candidatos"]} == {"video","modelo_3d"}
    assert all(x["status"]=="CANDIDATO_SEM_INSPECAO" for x in d["candidatos"])
    assert not d["publicar"] and d["renderer_aprovado"] is None
    assert d["observacao_visual"] == "NAO_EXECUTADA"


def test_so_titulo_e_formato_nao_escolhem_renderer():
    d=R.descobrir(brief(),buscar=searchvideo,get=search3d)
    p=R.planejar(brief(),d,[])
    assert p["renderer"] is None
    assert p["estado"] == "REFERENCIA_SEM_INSPECAO"
    assert "F-REFERENCIA-NAO-INSPECIONADA" in p["bloqueios"]


def test_observacao_de_quadros_prepara_renderer_existente():
    b=brief()
    d=R.descobrir(b,buscar=searchvideo,get=search3d)
    ref=d["candidatos"][0]["id"]
    p=R.planejar(b,d,observed(ref))
    assert p["renderer"] == "optical_projection"
    assert p["estado"] == "RENDERER_EXISTENTE_PLANO_PRELIMINAR"
    assert p["plano"]["revisao_fisica"] == "PENDENTE"
    assert p["plano"]["render_testado"] is False
    assert p["publicar"] is False


def test_mecanismo_desconhecido_e_bloqueado_sem_remendo_por_tema():
    b=brief(["ignite","piston_move","crank_rotate"],["entrada","mecanismo","saida"])
    d=R.descobrir(b,buscar=searchvideo,get=search3d)
    obs=observed(d["candidatos"][0]["id"])
    obs[0]["acoes_visiveis"]=b["acoes_necessarias"]
    obs[0]["evidencias"]=obs[0]["evidencias"][:3]
    for evidencia, acao in zip(obs[0]["evidencias"],b["acoes_necessarias"]):
        evidencia["acao"]=acao
    obs[0]["fases_visiveis"]=b["fases_necessarias"]
    obs[0]["atores_visiveis"]=["piston","crank"]
    p=R.planejar(b,d,obs)
    assert p["estado"] == "CAPACIDADE_OU_EVIDENCIA_INSUFICIENTE"
    assert p["renderer"] is None and not p["publicar"]


def test_recusa_observacao_sem_quadros_ou_sem_correspondencia():
    b=brief()
    d=R.descobrir(b,buscar=searchvideo,get=search3d)
    obs=observed(d["candidatos"][0]["id"])
    obs[0]["quadros"]=[1.0]
    assert R.planejar(b,d,obs)["renderer"] is None
    obs[0]["quadros"]=[1.0, 2.0]
    obs[0]["acoes_visiveis"]=["projection","source","wafer","reticle"]
    assert R.planejar(b,d,obs)["renderer"] is None


def test_erro_em_fornecedor_nao_inventa_candidatos():
    def broken(*a, **kw):
        raise ConnectionError("offline")
    d=R.descobrir(brief(),buscar=broken,get=broken)
    assert d["candidatos"] == []
    # Pode haver mais de uma consulta por provedor; contabilizar falhas,
    # nao assumir numero fixo de pedidos de rede.
    assert len(d["erros"]) >= 2
    assert all("ConnectionError" in e for e in d["erros"])
    assert R.planejar(brief(),d,[])["estado"] == "SEM_REFERENCIAS"


def test_sem_consulta_real_nao_prossegue():
    b=brief(); b["consultas_en"]=[]
    try:
        R.descobrir(b,buscar=searchvideo,get=search3d)
        assert False
    except ValueError:
        pass


def test_recurso_3d_nao_e_pretendido_renderizado():
    b=brief()
    d=R.descobrir(b,buscar=lambda _: [],get=search3d)
    assert d["candidatos"][0]["modelo_editavel"] == "NAO_VERIFICADO"
    assert d["candidatos"][0]["download_autorizado"] == "NAO_VERIFICADO"
    assert R.planejar(b,d,[])["renderer"] is None

class CommonsResponse:
    def raise_for_status(self):
        pass
    def json(self):
        return {"query":{"pages":[
            {"title":"File:Piston motion.gif","imageinfo":[{
                "url":"https://upload.wikimedia.org/wikipedia/commons/p/p1/Piston_motion.gif",
                "mime":"image/gif",
                "descriptionurl":"https://commons.wikimedia.org/wiki/File:Piston_motion.gif",
                "extmetadata":{"LicenseShortName":{"value":"CC BY-SA 4.0"}}
            }]},
            {"title":"File:Static diagram.png","imageinfo":[{
                "url":"https://upload.wikimedia.org/wikipedia/commons/static.png",
                "mime":"image/png"}]}
        ]}}

def test_descoberta_commons_inclui_gif_mas_nao_afirma_movimento_inspecionado():
    def fake_commons(url, **kwargs):
        assert "commons.wikimedia.org" in url
        assert kwargs["params"]["gsrnamespace"] == 6
        return CommonsResponse()
    found, errors=R.buscar_commons_animacoes(
        ["four stroke piston engine cutaway animation"],get=fake_commons)
    assert not errors
    assert len(found)==1
    assert found[0]["midia"]=="animacao_gif"
    assert found[0]["titulo"].endswith("Piston motion.gif")
    assert found[0]["licenca_verificada"] is False
    assert found[0]["movimento_observado"] is False
    assert R.termos_essenciais(["four stroke piston engine cutaway animation"])[0]=="piston"

def test_nao_confunde_lista_de_acoes_com_acontecimento_observado():
    b=brief()
    d=R.descobrir(b,buscar=searchvideo,get=search3d)
    o=observed(d["candidatos"][0]["id"])
    o[0].pop("evidencias")
    assert R.planejar(b,d,o)["renderer"] is None


def test_hash_de_frame_divergente_bloqueia_a_selecao():
    b=brief()
    d=R.descobrir(b,buscar=searchvideo,get=search3d)
    o=observed(d["candidatos"][0]["id"])
    o[0]["evidencias"][0]["hash_depois"]="a"*64
    assert R.planejar(b,d,o)["renderer"] is None
