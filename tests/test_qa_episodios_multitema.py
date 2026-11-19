"""Regressão OFFLINE dos três projetos narrados, sem custos de mídia/API."""
import json
import hashlib
from pathlib import Path

from scripts import qa_episodios_multitema as E
from src.v4.formatos import filme_editorial, contrato_visual_comum as C

ROOT=Path(__file__).resolve().parents[1]
MANIFESTO=ROOT/"docs/v4/formatos/qa_episodios_multitema_3.json"


def get():
    return json.loads(MANIFESTO.read_text(encoding="utf8"))


def plano(ep,tempo=3.7):
    fontes=[]
    for c in ep["cenas"]:
        fontes.append({"id":c["id"],"local_source":(
            c.get("local_video") or c.get("local_photo") or
            f"tests/midia/qa_multitema/{ep['id']}/{c['id']}.jpg"
        ),"media_type":"video" if c.get("local_video") else "photo",
         "expected_sha256":hashlib.sha256((c.get("local_photo") or c.get("local_video") or c["id"]).encode()).hexdigest(),"license":c["licenca"],
         "credit":c["autor"],"page":c["fonte"]})
    return E.compilar_um(ep,fontes,tempo)


def test_tres_temas_reais_nao_sao_tres_cenas_do_panama():
    m=get()
    assert m["schema"]==1
    assert len(m["episodios"])==3
    assert len({ep["dominio"] for ep in m["episodios"]})==3
    assert len({ep["id"] for ep in m["episodios"]})==3
    assert all(len(ep["cenas"])==4 for ep in m["episodios"])
    assert {ep["dominio"] for ep in m["episodios"]}=={"industria","geografia","historia"}


def test_tres_roteiros_que_renderizaram_sao_bloqueados_pela_mesma_regra_nova():
    m=get()
    encontrados={}
    for ep in m["episodios"]:
        p=plano(ep,m["duracao_cena"])
        q=filme_editorial.avaliar(p)
        encontrados[ep["id"]] = {x["codigo"] for x in q["bloqueios"]}
        assert not q["pronto"], (ep["id"],q["bloqueios"])
        assert "F-SEM-PROGRESSAO-INFORMACIONAL" in encontrados[ep["id"]]
        c=C.auditar(p)
        assert c["estrutura_declarada_ok"],(ep["id"],c["falhas"])
        assert c["prova_visual"]=="NAO_INSPECIONADA"
        assert c["aprovacao_humana"]=="PENDENTE"
        assert p["tipo"]=="PROVA_VISUAL_PRIVADA"
        assert len(p["shots"])==4
        assert abs(p["duracao"]-14.8)<.01
    assert "F-FONTE-VISUAL-REPETIDA" in encontrados["venezuela_paisagens"]
    assert "F-FONTE-VISUAL-REPETIDA" in encontrados["ever_given_suez"]
    assert "F-FONTE-VISUAL-REPETIDA" not in encontrados["taiwan_chips"]


def test_nenhuma_midia_representativa_alega_ser_do_proprio_acontecimento():
    m=get()
    for ep in m["episodios"]:
        p=plano(ep)
        for c,s in zip(ep["cenas"],p["shots"]):
            assert (s["evidence"]=="literal") == bool(c["original"])
            assert ("literal_identity" in s) == bool(c["original"])
            assert s["subject"]==c["prova"][:140]
            assert "Guerra do Iraque" not in c["voz"]


def test_fontes_locais_e_acervo_reutilizado_antes_de_download():
    m=get()
    for ep in m["episodios"]:
        for c in ep["cenas"]:
            assert c.get("local_photo") or c.get("local_video")
            assert c["licenca"] in E.LICENCAS
            assert c["fonte"].startswith("https://")
            assert c.get("prova") and c.get("voz")
            assert c["local_photo"].startswith((
                "tests/midia/", "tests/piloto_ever_given/img/", "motor4/formatos/dados/raster/"))


def test_narracoes_nao_podem_ser_vendidas_como_aprovacao_final():
    m=get()
    assert "VOZ" in m["modo"] or "NARRAD" in m["modo"]
    for ep in m["episodios"]:
        p=plano(ep)
        assert p["auditoria_privada"]["narracao_teste"].endswith("proibido publicar")
        assert len(p["auditoria_privada"]["roteiro_por_cena"])==4


def test_regra_multitema_detecta_substituicao_enganosa_em_qualquer_plano():
    from src.v4.formatos.qa_video_fontes import decidir_uso
    d=decidir_uso(acontecimento="Incêndio Hindenburg 1937",
                 evento_da_midia="Incêndio de outro dirigível",
                 uso="registro",cena_especifica=True,rotulo="",
                 origem_verificada=True,licenca_verificada=True)
    assert not d["permitido"] and not d["prova_do_fato"]
