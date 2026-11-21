"""Testes offline do revisor: nao usar Gemini, so respostas simuladas."""
import io

from PIL import Image, ImageDraw

from src.v4.formatos import inspecionar_referencia as I
from src.v4.formatos import referencias_mecanismos as R
from src.v4.formatos.amostrar_referencia import amostrar_gif


def brief(acoes=None):
    return {
        "id":"test-1",
        "pergunta":"Como o feixe atraves da maquina chega ao alvo?",
        "consultas_en":["optical projection mechanism animation"],
        "acoes_necessarias":acoes or ["source","reticle","projection","wafer"],
        "fases_necessarias":["origem","transformacao","resultado"]
    }


def candidate():
    return {"id":"ref-1","midia":"animacao_gif",
            "pagina":"https://commons.wikimedia.org/wiki/File:Optics.gif",
            "origem_media":"https://upload.wikimedia.org/wikipedia/commons/Optics.gif"}


class Resp:
    def raise_for_status(self): pass
    def iter_content(self,chunk_size):
        out=io.BytesIO()
        frames=[]
        for i in range(5):
            im=Image.new("RGB",(120,120),"white")
            dr=ImageDraw.Draw(im)
            dr.rectangle((i*18,40,i*18+24,80),fill=(30,60,120))
            frames.append(im)
        frames[0].save(out,format="GIF",save_all=True,
                       append_images=frames[1:],duration=250,loop=0)
        yield out.getvalue()


def setup(tmp_path):
    amostrar_gif(candidate(),tmp_path,get=lambda *_a,**_kw: Resp())
    return candidate()


def visual(_prompt, images):
    assert len(images)==5
    return {
        "categoria":"RELEVANTE",
        "atores_visiveis":["source","reticle","optics","wafer"],
        "fases_visiveis":["origem","transformacao","resultado"],
        "eventos":[{
            "acao":acao,"antes":i,"depois":i+1,"alvo":"elemento optico",
            "evidencia":"Componente muda de posicao entre os dois quadros, observado.",
            "visivel":True,
        } for i,acao in enumerate(brief()["acoes_necessarias"])],
        "problemas":[],"justificativa":"Mecanismo hipotetico para validar contrato"
    }


def test_retorna_eventos_vinculados_a_hash_sem_aprovar_publicacao(tmp_path):
    c=setup(tmp_path)
    result=I.inspecionar(brief(),c,tmp_path,visual)
    assert result["estado"]=="EVENTOS_VISUAIS_PROVISORIOS"
    assert len(result["observacao"]["evidencias"])==4
    assert len(result["observacao"]["origem_sha256"])==64
    assert result["revisao_humana"]=="PENDENTE"
    assert result["publicar"] is False
    p=R.planejar(brief(),{"candidatos":[c]},[result["observacao"]])
    assert p["renderer"]=="optical_projection"
    assert not p["publicar"] and not p["plano"]["render_testado"]


def test_recusa_rotacao_de_coracao_como_fluxo_sanguineo(tmp_path):
    c=setup(tmp_path)
    def wrong(p,i):
        result=visual(p,i)
        result["categoria"]="IRRELEVANTE"
        return result
    x=I.inspecionar(brief(),c,tmp_path,wrong)
    assert x["observacao"] is None
    assert "F-REFERENCIA-IRRELEVANTE-OU-INCERTA" in x["bloqueios"]


def test_ausencia_de_movimento_evidenciado_bloqueia(tmp_path):
    c=setup(tmp_path)
    def fake(p,i):
        x=visual(p,i)
        for event in x["eventos"]:
            event["antes"]=event["depois"]
        return x
    x=I.inspecionar(brief(),c,tmp_path,fake)
    assert x["observacao"] is None
    assert "F-SEM-MOVIMENTO-VISIVEL" in x["bloqueios"]


def test_hash_original_alterado_impede_chamada_ia(tmp_path):
    c=setup(tmp_path)
    original=tmp_path/"original.gif"
    original.write_bytes(original.read_bytes()+b"x")
    r=I.inspecionar(brief(),c,tmp_path,lambda *_: (_ for _ in ()).throw(AssertionError("not called")))
    assert r["observacao"] is None
    assert "F-REFERENCIA-SHA" in r["bloqueios"][0]


def test_metadados_de_outra_referencia_bloqueiam(tmp_path):
    c=setup(tmp_path);c["id"]="other"
    r=I.inspecionar(brief(),c,tmp_path,visual)
    assert r["observacao"] is None
    assert "F-REFERENCIA-ID" in r["bloqueios"][0]


def test_cota_indisponivel_impede_aceite(tmp_path):
    c=setup(tmp_path)
    def quota(*_): raise RuntimeError("sem cota")
    r=I.inspecionar(brief(),c,tmp_path,quota)
    assert r["observacao"] is None
    assert r["bloqueios"][0].startswith("F-VISAO-FALHOU")


def test_parcial_nao_finge_que_cobre_todas_as_fases(tmp_path):
    c=setup(tmp_path)
    def half(p,i):
        x=visual(p,i)
        x["categoria"]="PARCIAL"
        x["eventos"]=x["eventos"][:2]
        return x
    r=I.inspecionar(brief(),c,tmp_path,half)
    assert r["estado"]=="OBSERVACAO_PARCIAL"
    assert len(r["observacao"]["acoes_visiveis"])==2
    p=R.planejar(brief(),{"candidatos":[c]},[r["observacao"]])
    assert p["renderer"] is None


def test_nova_familia_sem_renderer_nao_reutiliza_optica(tmp_path):
    c=setup(tmp_path)
    nomes=["ignite","piston_move","crank_rotate","exhaust"]
    b=brief(nomes)
    def other(_p,imgs):
        x=visual("x",imgs)
        for name,event in zip(nomes,x["eventos"]):
            event["acao"]=name
        return x
    r=I.inspecionar(b,c,tmp_path,other)
    assert r["estado"]=="EVENTOS_VISUAIS_PROVISORIOS"
    plan=R.planejar(b,{"candidatos":[c]},[r["observacao"]])
    assert plan["renderer"] is None
    assert plan["estado"]=="CAPACIDADE_OU_EVIDENCIA_INSUFICIENTE"


def test_grava_inspecao_e_planejamento_sem_modificar_producao(tmp_path):
    c=setup(tmp_path)
    output=tmp_path/"reports"
    plan=I.executar(brief(),{"candidatos":[c]},tmp_path,output,visual)
    assert plan["planejamento"]["renderer"]=="optical_projection"
    assert (output/"inspecao_semantica.json").exists()
    assert (output/"planejamento_inspecionado.json").exists()
