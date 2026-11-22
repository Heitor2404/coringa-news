"""Fonte GIF licenciada: private preview, nunca geometria 3D reconstruida."""
import hashlib
import json
import shutil
import subprocess

import pytest
from PIL import Image, ImageDraw

from src.v4.formatos import render_referencia_licenciada as M


def source(tmp_path):
    path=tmp_path/"animation.gif"
    frames=[]
    for k in range(16):
        im=Image.new("RGB",(180,180),"white")
        d=ImageDraw.Draw(im)
        d.rectangle((42,10+k*5,138,58+k*5),fill="#2278A9")
        frames.append(im)
    frames[0].save(path,"GIF",save_all=True,append_images=frames[1:],
                   duration=100,loop=0,optimize=False)
    return path


def plan(gif):
    return {
        "schema":"licensed-reference-private-v1", "publicar":False,
        "origem_sha256":hashlib.sha256(gif.read_bytes()).hexdigest(),
        "pagina":"https://commons.wikimedia.org/wiki/File:Example.gif",
        "autores":"Autor de exemplo","licenca":"CC BY-SA 3.0",
        "licenca_url":"https://creativecommons.org/licenses/by-sa/3.0/",
        "licenca_verificada_manual":True,
        "titulo":"TESTE DE REFERENCIA",
        "subtitulo":"GERADO COM GIF DE TESTE",
        "etapas":[
            {"frame":0,"titulo":"MOVIMENTO INICIAL",
             "detalhe":"Primeiro quadro do teste ilustrativo."},
            {"frame":5,"titulo":"MOVIMENTO MEIO",
             "detalhe":"O componente desloca no teste."},
            {"frame":11,"titulo":"MOVIMENTO FINAL",
             "detalhe":"A peça chega ao final do deslocamento."},
        ]
    }


def test_valida_licenca_e_atuacao_por_etapas(tmp_path):
    gif=source(tmp_path)
    n,duration=M.validar(gif,plan(gif))
    assert n==16 and abs(duration-1.6)<.02


def test_nao_aceita_licenca_nc_ou_sem_conferencia(tmp_path):
    gif=source(tmp_path)
    p=plan(gif)
    p["licenca"]="CC BY-NC 4.0"
    with pytest.raises(ValueError,match="LICENCA"):
        M.validar(gif,p)
    p=plan(gif)
    p["licenca_verificada_manual"]=False
    with pytest.raises(ValueError,match="LICENCA"):
        M.validar(gif,p)


def test_hash_de_referencia_bloqueia_substituicao(tmp_path):
    gif=source(tmp_path)
    p=plan(gif)
    gif.write_bytes(gif.read_bytes()+b"data")
    with pytest.raises(ValueError,match="SHA"):
        M.validar(gif,p)


def test_rejeita_etapas_fora_de_ordem_ou_publicacao(tmp_path):
    gif=source(tmp_path)
    p=plan(gif)
    p["etapas"][0]["frame"]=4
    with pytest.raises(ValueError,match="DESORDENADAS"):
        M.validar(gif,p)
    p=plan(gif)
    p["publicar"]=True
    with pytest.raises(ValueError,match="PUBLICACAO"):
        M.validar(gif,p)


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
                    reason="FFmpeg indisponivel")
def test_render_real_privado_de_gif_teste_com_credito_e_audio_ausente(tmp_path):
    gif=source(tmp_path)
    path=tmp_path/"preview.mp4"
    report=M.renderizar(gif,plan(gif),path,fps=24,velocidade=1)
    assert path.is_file() and path.stat().st_size>10000
    meta=json.loads(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries",
         "stream=codec_type,width,height:format=duration",
         "-of","json",str(path)]))
    video=next(x for x in meta["streams"] if x["codec_type"]=="video")
    assert (video["width"],video["height"])==(540,960)
    assert not any(x["codec_type"]=="audio" for x in meta["streams"])
    credit=json.loads(path.with_name("preview_creditos.json").read_text("utf8"))
    assert credit["licenca"]=="CC BY-SA 3.0"
    assert not credit["publicar"]
    assert report["renderer"]=="GIF_LICENCIADO_NAO_2D_RECONSTRUIDO"
