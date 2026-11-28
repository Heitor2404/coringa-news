"""Reference-first tests. Frames/answers are SYNTHETIC: no semantic accuracy claim.
An actual GIF needs to be inspected by a multimodal service and a human.
"""
import io
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.v4.formatos import referencia_temporal as F
from src.v4.formatos import reference_first as RF


def fake_gif(path, changes=True, n=16):
    frames = []
    for k in range(n):
        im = Image.new("RGB", (220, 220), (236, 244, 244))
        d = ImageDraw.Draw(im)
        height = 42 + 7 * (k if k <= 8 else 16 - k) if changes else 84
        d.rectangle((73, height, 144, height + 57), fill="#527D94")
        d.ellipse((88, 168, 125, 205), fill="#B47F3F")
        if k % 4 == 0:
            d.polygon([(20, 25), (49, 25), (49, 42)], fill="#3ABFDA")
        frames.append(im)
    frames[0].save(path, "GIF", save_all=True, append_images=frames[1:],
                   duration=100, loop=0, optimize=False)


def source(tmp_path):
    original = tmp_path / "source.gif"
    fake_gif(original)
    m = F.amostrar(original, tmp_path / "frames", "lab-referencia-01",
                   pagina="https://commons.wikimedia.org/wiki/File:Sample.gif",
                   licenca_declarada="DECLARADA_PD_NAO_VALIDADA")
    return original, tmp_path / "frames", m


def answer(process):
    s = RF.PROCESSOS[process]
    events = []
    for i, (name, signals) in enumerate(s["eventos"]):
        events.append({
            "tipo": name, "antes": 2 * i, "depois": 2 * i + 2,
            "sinais": list(signals),
            "visivel": True,
            "descricao": f"De {i} a {i+1}, movimentos de pecas sao observados "
                         "entre os dois quadros, com alteracao de estado.",
        })
    return {
        "processo": process,
        "atores": list(s["atores"]),
        "ligacoes": [{"a": a, "b": b} for a, b in s["ligacoes"]],
        "eventos": events,
    }


def test_amostrador_gif_real_12_quadros_individuais_com_sha(tmp_path):
    original, folder, m = source(tmp_path)
    assert len(m["amostras"]) == 12
    assert m["intervalos_em_movimento"] >= 3
    assert m["publicar"] is False
    got, imgs = F.carregar(folder)
    assert got["arquivo_sha256"] == m["arquivo_sha256"]
    assert len(imgs) == 12
    assert all(img.startswith(b"\xff\xd8") for img in imgs)


def test_gif_sem_movimento_rejeitado(tmp_path):
    original = tmp_path / "static.gif"
    # A animação pode ter quadros DIFERENTES em metadados mas iguais visualmente.
    fake_gif(original, changes=False)
    # Frame de indicador muda em 25% dos quadros. Para teste de estático
    # criado separadamente totalmente igual sem indicador.
    frames=[Image.new("RGB",(160,160),"white") for _ in range(16)]
    frames[0].save(original,"GIF",save_all=True,append_images=frames[1:],
                   duration=100,loop=0,optimize=False)
    with pytest.raises(ValueError, match="CICLO-CURTO|MOVIMENTO"):
        F.amostrar(original, tmp_path / "f", "ref-parada-01")


def test_origem_ou_frames_modificados_bloqueiam(tmp_path):
    original, folder, _ = source(tmp_path)
    p = folder / "quadro_04.jpg"
    p.write_bytes(p.read_bytes() + b"alterado")
    with pytest.raises(ValueError, match="MODIFICADO"):
        F.carregar(folder)
    _, folder, _ = source(tmp_path)
    original.write_bytes(original.read_bytes() + b"alterado")
    with pytest.raises(ValueError, match="SHA-ORIGINAL"):
        F.carregar(folder)


def test_somente_pistao_generico_nao_e_compressor(tmp_path):
    _, _, m = source(tmp_path)
    a=answer("compressor_alternativo")
    a["processo"]="slider_crank_generico"
    r=RF.analisar(m,a,"compressor_alternativo")
    assert r["estado"]=="BLOQUEADO"
    assert "F-OUTRO-PROCESSO-OU-INDETERMINADO" in r["bloqueios"]
    assert r["grafo"] is None


def test_motor_4_tempos_nao_e_compressor(tmp_path):
    _, _, m = source(tmp_path)
    a=answer("motor_otto_4t")
    r=RF.analisar(m,a,"compressor_alternativo")
    assert r["grafo"] is None
    assert r["processo_observado_pelo_modelo"]=="motor_otto_4t"


def test_compressor_sem_valvulas_bloqueia_mesmo_que_tem_pistao(tmp_path):
    _, _, m = source(tmp_path)
    a=answer("compressor_alternativo")
    a["atores"]=["pistao","biela","virabrequim","cilindro"]
    r=RF.analisar(m,a,"compressor_alternativo")
    assert "F-ATORES-FUNCIONAIS-NAO-VISTOS" in r["bloqueios"]
    assert r["grafo"] is None


def test_compressor_sem_fluxo_de_saida_bloqueia(tmp_path):
    _, _, m = source(tmp_path)
    a=answer("compressor_alternativo")
    a["eventos"][-1]["sinais"].remove("ar_sai")
    r=RF.analisar(m,a,"compressor_alternativo")
    assert "F-EVENTO-SEM-SINAIS-CONCRETOS" in r["bloqueios"]


def test_compressor_etapa_sem_prova_de_frames_bloqueia(tmp_path):
    _, _, m = source(tmp_path)
    a=answer("compressor_alternativo")
    a["eventos"][1]["antes"]=a["eventos"][1]["depois"]
    r=RF.analisar(m,a,"compressor_alternativo")
    assert "F-ETAPA-SEM-PAR-TEMPORAL-VALIDO" in r["bloqueios"]


def test_motor_sem_ignicao_nao_e_quatro_tempos(tmp_path):
    _, _, m=source(tmp_path)
    a=answer("motor_otto_4t")
    a["eventos"][2]["sinais"].remove("ignicao_acontece")
    r=RF.analisar(m,a,"motor_otto_4t")
    assert r["grafo"] is None
    assert "F-EVENTO-SEM-SINAIS-CONCRETOS" in r["bloqueios"]


def test_observacao_completa_so_cria_grafo_PROVISORIO(tmp_path):
    _, _, m = source(tmp_path)
    for process in ("motor_otto_4t", "compressor_alternativo"):
        result=RF.analisar(m,answer(process),process)
        assert result["estado"]=="GRAFO_PROVISORIO_SEM_RENDER"
        assert result["grafo"]["tipo_processo"]==process
        assert result["grafo"]["familia_fisica"]=="slider_crank"
        assert result["grafo"]["malhas_3d_recuperadas"] is False
        assert result["grafo"]["rig_2d_recuperado"] is False
        assert result["renderer"] is None
        assert result["publicar"] is False
        assert "F-RENDERER-RECONSTRUTIVO-AINDA-NAO-IMPLEMENTADO" in result["bloqueios"]


def test_renderer_antigo_nao_pode_passar_por_compressor_completo():
    r=RF.verificar_renderizador("compressor_alternativo","CinematicCutaway3D")
    assert not r["aprovado"]
    assert "valvulas_entrada_e_saida_visiveis" in r["faltantes"]
    assert "fluxo_descarga_visivel" in r["faltantes"]


def test_renderer_antigo_nao_pode_passar_por_motor_4tempos():
    r=RF.verificar_renderizador("motor_otto_4t","CinematicCutaway3D")
    assert not r["aprovado"]
    assert "ignicao_visivel" in r["faltantes"]
    assert "quatro_tempos_dois_giros" in r["faltantes"]


def test_nao_escolhe_renderer_inexistente_automaticamente():
    r=RF.verificar_renderizador("compressor_alternativo","NaoExiste")
    assert not r["aprovado"]
    assert "F-RENDERER-NAO-CADASTRADO" in r["bloqueios"]


def test_sem_credencial_visao_ou_sem_midia_produz_bloqueio(tmp_path):
    _, folder, _=source(tmp_path)
    done=RF.executar(folder,"compressor_alternativo",tmp_path/"out",
                      chamar_visao=lambda *_: None)
    assert done["grafo"] is None
    assert done["renderer"] is None and done["publicar"] is False
    assert (tmp_path/"out/scene_ir.json").exists()
    fail=RF.executar(tmp_path/"nonexistent","motor_otto_4t",tmp_path/"fail",
                      chamar_visao=lambda *_: answer("motor_otto_4t"))
    assert fail["estado"]=="BLOQUEADO"
    assert "F-ARQUIVO-SEM-QUADROS-REAIS" in fail["bloqueios"][0]


def test_modelo_apenas_declara_eventos_nao_torna_video_publicavel(tmp_path):
    _, folder, _ = source(tmp_path)
    report=RF.executar(folder,"compressor_alternativo",tmp_path/"out",
                       chamar_visao=lambda *_: answer("compressor_alternativo"))
    assert report["estado"] == "GRAFO_PROVISORIO_SEM_RENDER"
    assert report["validacao_visual_humana"]=="PENDENTE"
    assert report["licenca_para_reutilizacao"]=="PENDENTE"
    assert report["renderer"] is None


def test_pedido_analisado_com_frame_adulterado_nao_chama_gemini(tmp_path):
    _, folder, _ = source(tmp_path)
    p=folder/"quadro_02.jpg"
    p.write_bytes(b"invalid")
    def must_not_call(*_):
        raise AssertionError("Nao devia chamar VLM")
    result=RF.executar(folder,"compressor_alternativo",tmp_path/"blocked",
                       chamar_visao=must_not_call)
    assert result["estado"]=="BLOQUEADO"
    assert result["renderer"] is None
    assert "F-ARQUIVO-SEM-QUADROS-REAIS" in result["bloqueios"][0]


def test_meta_vazia_e_resposta_inventada_nao_se_tornam_prova():
    m={"referencia_id":"ref","amostras":[]}
    r=RF.analisar(m,answer("compressor_alternativo"),"compressor_alternativo")
    assert "F-REFERENCIA-TEMPORAL-NAO-VERIFICADA" in r["bloqueios"]

def test_nem_override_externo_habilita_renderer_sem_auditoria():
    feats=RF.PROCESSOS["compressor_alternativo"]["capacidades_visuais"]
    result=RF.verificar_renderizador(
        "compressor_alternativo","PluginNaoAuditado",
        capacidades_override=list(feats))
    assert not result["aprovado"]
    assert "F-RENDERER-NAO-AUDITADO" in result["bloqueios"]

def test_prancha_de_doze_quadros_vira_uma_imagem_numerada(tmp_path):
    from PIL import Image
    import io
    _, folder, _=source(tmp_path)
    _, images=F.carregar(folder)
    prancha=RF.prancha_temporal(images)
    with Image.open(io.BytesIO(prancha)) as im:
        assert im.format=="JPEG"
        assert im.size==(930,1688)
    assert len(prancha)>20000


def test_execucao_padrao_nao_chama_gemini_nem_com_chave(tmp_path,monkeypatch):
    _, folder, _=source(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "falsa-credencial")
    result=RF.executar(folder,"motor_otto_4t",tmp_path/"safe_off")
    assert result["estado"]=="BLOQUEADO"
    assert result["renderer"] is None and not result["publicar"]
    assert "F-VISAO-SEM-RESPOSTA-ESTRUTURADA" in result["bloqueios"]


def test_one_call_prancha_para_callback_injetado(tmp_path):
    _, folder, _=source(tmp_path)
    calls=[]
    def simulated(prompt,images):
        calls.append((prompt,images))
        return answer("motor_otto_4t")
    result=RF.executar(folder,"motor_otto_4t",tmp_path/"out",chamar_visao=simulated)
    assert len(calls)==1 and len(calls[0][1])==1
    assert calls[0][1][0][:2]==bytes([0xff,0xd8])
    assert result["estado"]=="GRAFO_PROVISORIO_SEM_RENDER"

def test_compressor_pv_demonstra_ciclo_mas_ainda_bloqueia_sem_referencia_real():
    result = RF.verificar_renderizador("compressor_alternativo", "CompressorPV2D")
    assert result["aprovado"] is False
    assert result["faltantes"] == []
    assert "F-RENDERER-EXPERIMENTAL_NAO_APROVADO" in result["bloqueios"]
    # O motor antigo continua sem as capacidades físicas da compressão.
    old = RF.verificar_renderizador("compressor_alternativo", "CinematicCutaway3D")
    assert old["faltantes"]
    assert old["aprovado"] is False


def test_nova_montagem_visual_nao_promove_renderer_por_pouco_qa():
    result = RF.verificar_renderizador(
        "compressor_alternativo", "CompressorConjunto2D")
    assert not result["aprovado"]
    assert result["faltantes"] == []
    assert "F-RENDERER-EXPERIMENTAL_NAO_APROVADO" in result["bloqueios"]
