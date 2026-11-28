"""Teste do amostrador de GIF de referencia com bytes simulados."""
import io
from PIL import Image

from src.v4.formatos.amostrar_referencia import amostrar_gif


def gif_bytes():
    out=io.BytesIO()
    frames=[Image.new("RGB",(96,64),(i*65,100,140)) for i in range(4)]
    frames[0].save(out,format="GIF",save_all=True,append_images=frames[1:],
                   duration=200,loop=0)
    return out.getvalue()


class Response:
    def __init__(self, buf):
        self.buf=buf
    def raise_for_status(self):
        pass
    def iter_content(self, chunk_size):
        yield self.buf

def cand():
    return {"id":"commons-test","midia":"animacao_gif",
            "pagina":"https://commons.wikimedia.org/wiki/File:Example.gif",
            "origem_media":"https://upload.wikimedia.org/wikipedia/commons/Example.gif"}

def test_extrai_quadros_reais_e_marca_revisao_pendente(tmp_path):
    r=amostrar_gif(cand(),tmp_path,get=lambda *a,**k: Response(gif_bytes()))
    assert r["numero_quadros"] == 4
    assert len(r["amostras"]) >= 4
    assert len(r["sha256"]) == 64
    assert r["veredito_visual"] == "PENDENTE"
    assert (tmp_path/"contato_referencia.jpg").exists()
    assert (tmp_path/"inspecao.json").exists()
    assert (tmp_path/"original.gif").exists()

def test_nao_aceita_url_arbitraria(tmp_path):
    c=cand()
    c["origem_media"]="https://example.com/file.gif"
    try:
        amostrar_gif(c,tmp_path,get=lambda *a,**k: Response(gif_bytes()))
        assert False
    except ValueError as exc:
        assert "F-REFERENCIA-ORIGEM" in str(exc)

def test_resposta_invalida_e_rejeitada(tmp_path):
    try:
        amostrar_gif(cand(),tmp_path,get=lambda *a,**k: Response(b"not a gif"))
        assert False
    except ValueError as exc:
        assert "F-REFERENCIA-CONTEUDO" in str(exc)
