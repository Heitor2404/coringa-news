"""Enquadramento horizontal→vertical com área essencial visível.

ROI é declaração do curador, NÃO prova automática de ação. Testes estruturais
multitema e teste de integração props→Remotion sem gastar Gemini/ffmpeg.
"""
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from src.v4.formatos import filme_editorial as F

ROOT=Path(__file__).resolve().parents[1]
PROVA=ROOT/"docs/v4/formatos/filme_taiwan_prova.json"


def plano(tema="laboratorio"):
    p=json.loads(PROVA.read_text(encoding="utf8"))
    p["titulo"]=tema
    sha="a"*64
    shot=p["shots"][0]
    shot.update(type="video",asset="video-acervo",source_in_seconds=0.0,
                video_framing={
                    "modo":"roi_observada", "sha256_origem":sha,
                    "inspecao":"Dois quadros originais foram inspecionados para localizar o operador",
                    "pontos":[
                        {"at":0.0,"fonte_s":0.0,
                         "area_essencial":[.45,.32,.68,.88]},
                        {"at":1.4,"fonte_s":1.4,
                         "area_essencial":[.47,.32,.70,.88]},
                    ]
                })
    p["media"]["video-acervo"]={
        "url":"https://upload.wikimedia.org/wikipedia/commons/c/c0/documentario.mp4",
        "page":"https://commons.wikimedia.org/wiki/File:documentario.mp4",
        "credit":"Acervo documental sob revisão humana",
        "license":"Public domain",
        "media_type":"video","expected_sha256":sha,
        "width":1360,"height":720,
    }
    return p


def codigos(r):
    return {x["codigo"] for x in r["bloqueios"]}


@pytest.mark.parametrize("tema",[
    "industria_de_semicondutores", "navio_eclusa",
    "historia_de_infraestrutura", "laboratorio_de_fisica",
])
def test_enquadramento_dirigido_serve_a_qualquer_tema(tema):
    p=plano(tema)
    r=F.avaliar(p)
    assert r["pronto"],r["bloqueios"]
    pontos=F.planejar_enquadramento_video(
        p["shots"][0],p["media"]["video-acervo"],(1360,720))
    assert len(pontos)==2
    assert pontos[0]["at"]==0
    assert all(0<=v<=1 for ponto in pontos for v in ponto["position"])
    assert pontos[0]["position"][0]!=pontos[1]["position"][0]
    assert all(abs(ponto["position"][1]-.5)<.0001 for ponto in pontos)


def test_nist_1360_por_720_janela_horizontal_preserva_operador_na_direita():
    p=plano("ensaio_geometrico_com_medidas_do_frame_nist_78s")
    pos=F.planejar_enquadramento_video(
        p["shots"][0],p["media"]["video-acervo"],(1360,720))[0]["position"][0]
    fracao_visivel=(1080/1920)/(1360/720)
    esquerda=pos*(1-fracao_visivel)
    direita=esquerda+fracao_visivel
    assert esquerda+.03*fracao_visivel<=.45
    assert direita-.03*fracao_visivel>=.68
    assert fracao_visivel<.30  # cover corta mais de 70% da largura


def test_sujeito_maquina_com_80pct_da_largura_e_irrecortavel():
    p=plano()
    p["shots"][0]["video_framing"]["pontos"][0]["area_essencial"]=[.1,.1,.9,.9]
    r=F.avaliar(p)
    assert "F-ROI-NAO-CABE" in codigos(r)
    assert not r["pronto"]


def test_recusa_sha_de_outro_video_e_arquivo_sem_achado_de_quadro():
    p=plano()
    p["media"]["video-acervo"]["expected_sha256"]="b"*64
    assert "F-ROI-SHA" in codigos(F.avaliar(p))
    p=plano()
    p["shots"][0]["video_framing"]["inspecao"]="ok"
    assert "F-ROI-INSPECAO" in codigos(F.avaliar(p))


def test_recusa_tempo_ou_bbox_de_outro_frame():
    p=plano()
    p["shots"][0]["video_framing"]["pontos"][1]["fonte_s"]=45
    assert "F-ROI-FONTE" in codigos(F.avaliar(p))
    p=plano()
    p["shots"][0]["video_framing"]["pontos"][1]["area_essencial"]=[-.1,0,.1,.2]
    assert "F-ROI-AREA" in codigos(F.avaliar(p))


def test_recusa_zoom_extra_que_desfaz_sujeito_protegido():
    p=plano()
    p["shots"][0]["video_zoom"]=1.3
    assert "F-ROI-ZOOM" in codigos(F.avaliar(p))


def test_video_final_horizontal_nao_pode_usar_recorte_central_cego():
    p=plano()
    p["tipo"]="FILME_FINAL"
    del p["shots"][0]["video_framing"]
    r=F.avaliar(p)
    assert "F-ROI-SEM-DIRECAO" in codigos(r)
    assert not r["pronto"]


def test_preparar_exporta_posicoes_no_mesmo_compositor(tmp_path,monkeypatch):
    # Integração com o fixture de vídeo horizontal REAL do repositório.
    origem=ROOT/"tests/midia/video_horizontal_navio.mp4"
    assert origem.is_file()
    p=plano("teste_integracao_qualquer_filme")
    sha=hashlib.sha256(origem.read_bytes()).hexdigest()
    m=p["media"]["video-acervo"]
    m.update(local_source="tests/midia/video_horizontal_navio.mp4",
             expected_sha256=sha,width=1280,height=720)
    p["shots"][0]["video_framing"]["sha256_origem"]=sha
    # Bbox continua cabendo na fonte 1280x720.
    def sonda(cmd,*args,**kwargs):
        if cmd[0]=="ffprobe":
            return SimpleNamespace(stdout=json.dumps({
                "streams":[{"width":1280,"height":720}],
                "format":{"duration":"6.006"}
            }))
        raise AssertionError("comando inesperado: "+str(cmd))
    monkeypatch.setattr(F.subprocess,"run",sonda)
    imagem=Image.new("RGB",(820,820),(40,70,90))
    buff=io.BytesIO()
    imagem.save(buff,format="JPEG")
    r=F.preparar(p,tmp_path/"saida",tmp_path/"public",
                  downloader=lambda _:buff.getvalue())
    assert r["pronto"]
    props=json.loads((tmp_path/"saida"/"props.json").read_text(encoding="utf8"))
    shot=props["shots"][0]
    assert len(shot["framing_positions"])==2
    assert all(0<=x<=1 for v in shot["framing_positions"] for x in v["position"])
    assert (tmp_path/"public"/shot["asset"]).is_file()


def test_preparar_recusa_dimensoes_inventadas(tmp_path,monkeypatch):
    origem=ROOT/"tests/midia/video_horizontal_navio.mp4"
    p=plano()
    sha=hashlib.sha256(origem.read_bytes()).hexdigest()
    p["media"]["video-acervo"].update(
        local_source="tests/midia/video_horizontal_navio.mp4",expected_sha256=sha,
        width=1360,height=720
    )
    p["shots"][0]["video_framing"]["sha256_origem"]=sha
    def fake(cmd,*args,**kwargs):
        if cmd[0]=="ffprobe":
            return SimpleNamespace(stdout=json.dumps({
                "streams":[{"width":1280,"height":720}],
                "format":{"duration":"6.006"}
            }))
        raise AssertionError("comando inesperado")
    monkeypatch.setattr(F.subprocess,"run",fake)
    im=Image.new("RGB",(820,820),"black")
    b=io.BytesIO();im.save(b,format="JPEG")
    with pytest.raises(ValueError,match="dimensões reais diferem"):
        F.preparar(p,tmp_path/"saida",tmp_path/"public",downloader=lambda _:b.getvalue())



def test_video_longo_com_roi_dirigido_e_progressao_real():
    """Duas decisões diferentes coexistem: ação mantém o plano; ROI mantém o sujeito."""
    p=plano("engenharia_sem_cortes_artificiais")
    shot=p["shots"][0]
    delta=10.0-shot["end"]
    shot["end"]=10.0
    for s in p["shots"][1:]:
        s["start"]=round(s["start"]+delta,3)
        s["end"]=round(s["end"]+delta,3)
    p["duracao"]=round(p["duracao"]+delta,3)
    p["media"]["video-acervo"]["duration_s"]=12.0
    sha=p["media"]["video-acervo"]["expected_sha256"]
    shot["video_framing"]["pontos"]=[
        {"at":0.0,"fonte_s":0.0,"area_essencial":[.45,.32,.68,.88]},
        {"at":4.0,"fonte_s":4.0,"area_essencial":[.47,.32,.70,.88]},
        {"at":8.0,"fonte_s":8.0,"area_essencial":[.46,.32,.69,.88]},
    ]
    shot["progressao_visual"]={
        "tipo":"acao_observada", "sha256_origem":sha,
        "inspecao":"Marcos anotados em quadros originais: ações distintas sob revisão humana",
        "eventos":[
            {"at":.8,"fonte_s":.8,"acao_visivel":"operador inicia interação com painel"},
            {"at":3.2,"fonte_s":3.2,"acao_visivel":"braço posiciona suporte na máquina"},
            {"at":6.4,"fonte_s":6.4,"acao_visivel":"porta de câmara se desloca visivelmente"},
            {"at":9.0,"fonte_s":9.0,"acao_visivel":"equipamento muda de configuração"},
        ]
    }
    r=F.avaliar(p)
    assert r["pronto"],r["bloqueios"]
    assert len(F.planejar_enquadramento_video(shot,p["media"]["video-acervo"],(1360,720)))==3
    # Teste estrutural sintético: isso NÃO atesta que a filmagem real
    # contém as ações escritas acima, nem libera uso comercial.
    assert r["visual_approval"]=="NAO_FOI_AVALIADO"


@pytest.mark.parametrize("width,expected",[
    (.20,None),(.39,'4:5'),(.49,'1:1'),(.85,'integral'),
])
def test_adaptive_relationship_selects_largest_compatible_viewport(width,expected):
    # Synthetic geometry regression, never represented as observed footage.
    p=plano()
    shot=p["shots"][0]
    m=p["media"]["video-acervo"]
    m.update(width=1280,height=720)
    shot["video_framing"]={
        "modo":"relacao_observada","sha256_origem":m["expected_sha256"],
        "inspecao":"Fixture geométrica sintética para testar seleção de enquadramento",
        "pontos":[{"at":at,"fonte_s":at,"elementos":[
            {"nome":"A","bbox":[.5-width/2,.20,.5-width/2+.03,.80]},
            {"nome":"B","bbox":[.5+width/2-.03,.20,.5+width/2,.80]}]}
            for at in (0.,1.4)]}
    r=F.resolver_relacao_video(shot,m,(1280,720),adaptativo=True)
    if expected=='integral':
        assert r['layout']=='cena_integral'
        assert not r['framing_positions']
    else:
        assert r['layout']=='recorte_relacional_seguro'
        assert r.get('documentary_viewport')==expected
        assert len(r['framing_positions'])==2
    assert r['elementos_protegidos']==['A','B']


def test_adaptive_relationship_does_not_weaken_sha_binding():
    p=plano()
    shot=p["shots"][0]
    shot["video_framing"].update(modo="relacao_observada",sha256_origem="b"*64)
    with pytest.raises(ValueError,match="F-RELACAO-SHA"):
        F.resolver_relacao_video(shot,p["media"]["video-acervo"],(1360,720),adaptativo=True)
