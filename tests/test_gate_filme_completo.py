"""Testa que um documentário não é aprovado só por ter mapa e duas fotos."""
import copy
import json
from pathlib import Path

from src.v4.formatos import gate_filme_completo as G

ROOT=Path(__file__).resolve().parents[1]
BRIEF=ROOT/"docs/v4/formatos/CONTRATO_PILOTO_TAIWAN_INTEGRAL_20261119.json"


def brief():
    return json.loads(BRIEF.read_text(encoding="utf-8"))


def item(id,natureza):
    return {"id":id,"natureza":natureza,
      "sha256_origem":(id.encode().hex()+"a"*64)[:64],
      "licenca":"CC BY 4.0","credito":"Fonte documental · licença conferida",
      "uso_comercial":"sim",
      "prova":{"midia_corresponde":True,"acao_ou_relacao_visivel":True}}


def catalogo():
    return {"itens":[
      item("commons:TSMC_Fab_18_May_2025.jpg","foto"),
      item("commons:Silicon_wafer_close_view.jpg","foto")
    ]}


def codes(r):
    return {i["codigo"] for i in r["bloqueios"]}


def _avaliar_sintetico(manifesto, itens):
    # Estes testes criam mídia fictícia, SEM arquivo original.
    # O motor real e o CLI nunca dispensam a checagem byte a byte.
    return G.avaliar(manifesto, itens, conferir_bytes=False)


def test_fluxo_real_bloqueia_metadados_sem_arquivo():
    resultado=G.avaliar(brief(), catalogo())
    assert "E-BYTES-NAO-COMPROVADOS" in codes(resultado)
    assert not resultado["pronto_para_tts"]


def test_fluxo_real_rejeita_arquivo_com_hash_adulterado(tmp_path, monkeypatch):
    import hashlib
    cat=catalogo()
    original=cat["itens"][0]
    original["arquivo_local"]="fab18.jpg"
    original["sha256_origem"]=hashlib.sha256(b"arquivo diferente").hexdigest()
    (tmp_path/"fab18.jpg").write_bytes(b"arquivo corrompido")
    monkeypatch.chdir(tmp_path)
    resultado=G.avaliar(brief(), cat)
    assert any(x["codigo"]=="E-BYTES-NAO-COMPROVADOS" and
               x["cena"]=="01_fab18" and "SHA-256" in x["motivo"]
               for x in resultado["bloqueios"])
    assert not resultado["pronto_para_tts"]



def test_taiwan_nao_finge_que_acervo_tem_video_suficiente():
    r=_avaliar_sintetico(brief(),catalogo())
    assert r["status"]=="BLOQUEADO_EDITORIAL_SEM_PROVA"
    assert not r["pronto_para_tts"] and not r["pronto_para_render"]
    assert r["publicado"] is False and r["inspecao_humana"]=="PENDENTE"
    assert {"E-CARTOGRAFIA-NAO-INTEGRADA",
            "E-MIDIA-SEM-CURADORIA","E-COMPARACAO-INCOMPLETA",
            "E-PAYOFF-SEM-CONSEQUENCIA"} <= codes(r)
    assert "W-DIVERSIDADE-VIDEO" in {x["codigo"] for x in r["avisos_editoriais"]}


def test_pendencia_licenca_nao_se_resolve_por_string_do_roteiro():
    p=brief()
    p["cenas"][5]["estado"]="BLOQUEADO_LICENCA_SEM_REVISAO"
    r=_avaliar_sintetico(p,catalogo())
    assert not r["pronto_para_tts"]


def test_tempo_e_narracao_de_base_sao_os_do_roteiro_antigo_sem_fingir_wav():
    p=brief()
    assert abs(p["duracao_planejada_s"]-27.445)<.001
    assert p["base_narracao"]["voz"]=="Charon"
    assert p["base_narracao"]["arquivo_wav"] is None
    assert p["base_narracao"]["status"]=="SEM_AUDIO_REUTILIZAVEL_VERIFICADO"
    assert len(p["cenas"])==8
    assert _avaliar_sintetico(p,catalogo())["pronto_para_render"] is False


def _completo(monkeypatch):
    p=brief()
    original=catalogo()["itens"]
    novos=[
        item("chip_real_em_movimento","video"),
        item("uc_davis_real","foto"),
        item("semiconductor_fab_real","video"),
        item("consequencia_real","video"),
    ]
    p["cenas"][2]["midia"]["asset_id"]="chip_real_em_movimento"
    p["cenas"][4]["midia"]["asset_id"]="uc_davis_real"
    p["cenas"][5]["midia"]["asset_id"]="semiconductor_fab_real"
    p["cenas"][5]["midia"]["substituicao"]={
        "acontecimento":"Processo industrial de Taiwan",
        "evento_da_midia":"Laboratorio externo",
        "uso":"demonstracao",
        "cena_especifica":True,"origem_verificada":True,
        "licenca_verificada":True,
        "representacao":{
            "tipo":"processo_equivalente",
            "processo_narrado":"deposicao_metalica_em_wafer",
            "processo_midia":"deposicao_metalica_em_wafer",
            "compatibilidade_tecnica_verificada":True,
            "evidencia_inspecao":"inspecao humana dos quadros reais 1s a 3s",
            "fala_atribui_registro":False,
            "origem_no_credito":"Laboratorio externo · representacao",
        }
    }
    novos[2]["prova"]["processo_verificado"]="deposicao_metalica_em_wafer"
    p["cenas"][6]["midia"]={
        "tipo":"comparison","identidade":"explicativa",
        "asset_ids":["commons:TSMC_Fab_18_May_2025.jpg",
                     "commons:Silicon_wafer_close_view.jpg"],
        "fonte_factual":"https://www.asml.com/",
        "relacao_visualmente_verificada":True,
    }
    p["cenas"][7]["midia"]["asset_id"]="consequencia_real"
    p["cenas"][7]["midia"]["resultado_verificavel"]=True
    p["cenas"][2]["estado"]="ORIGEM_CATALOGADA"
    p["cenas"][4]["estado"]="ORIGEM_CATALOGADA"
    p["cenas"][5]["estado"]="ORIGEM_CATALOGADA"
    p["cenas"][6]["estado"]="RELACAO_VERIFICADA"
    p["cenas"][7]["estado"]="ORIGEM_CATALOGADA"
    monkeypatch.setattr("src.v4.formatos.ponte_mapa_atlas.validar_comprovante",lambda x:[])
    return p,{"itens":original+novos}


def test_mesmo_motor_pode_aceitar_cenas_novas_quando_realmente_curadas(monkeypatch):
    p,cat=_completo(monkeypatch)
    r=_avaliar_sintetico(p,cat)
    assert r["pronto_para_tts"],r["bloqueios"]
    assert not r["pronto_para_render"]  # ainda não produziu áudio
    assert r["mapas_atlas_comprovados"]==1
    assert r["videos_independentes_conferidos"]==3
    assert r["publicado"] is False


def test_two_photos_cannot_be_called_two_new_videos(monkeypatch):
    p,cat=_completo(monkeypatch)
    cat["itens"][-1]["natureza"]="foto"
    r=_avaliar_sintetico(p,cat)
    assert not r["pronto_para_tts"]
    assert "E-VIDEO-FALSO" in codes(r)


def test_meta_de_clipes_e_aviso_nao_bloqueio_global(monkeypatch):
    p,cat=_completo(monkeypatch)
    p["rubrica_editorial"]["min_videos_reais_independentes"]=5
    r=_avaliar_sintetico(p,cat)
    assert "W-DIVERSIDADE-VIDEO" in {x["codigo"] for x in r["avisos_editoriais"]}
    assert r["pronto_para_tts"]
    assert "E-VIDEO-INSUFICIENTE" not in codes(r)


def test_percentual_de_fotos_gera_alerta_sem_cortar_factualmente(monkeypatch):
    p,cat=_completo(monkeypatch)
    p["rubrica_editorial"]["max_fracao_fotos_estaticas"]=.22
    r=_avaliar_sintetico(p,cat)
    assert "W-SLIDESHOW" in {x["codigo"] for x in r["avisos_editoriais"]}
    assert r["pronto_para_tts"]
    assert "E-SLIDESHOW" not in codes(r)


def test_gemini_charon_sem_edge(monkeypatch):
    p,cat=_completo(monkeypatch)
    p["base_narracao"]["motor"]="edge"
    p["base_narracao"]["voz"]="Antonio"
    assert "E-VOZ-CONFIG" in codes(_avaliar_sintetico(p,cat))


def test_repeticao_de_foto_nao_e_nova_prova(monkeypatch):
    p,cat=_completo(monkeypatch)
    p["cenas"][4]["midia"]["asset_id"]=p["cenas"][3]["midia"]["asset_id"]
    assert "E-FONTE-REPETIDA" in codes(_avaliar_sintetico(p,cat))


def test_relacao_sem_fonte_nao_vira_prova_por_ter_duas_imagens(monkeypatch):
    p,cat=_completo(monkeypatch)
    p["cenas"][6]["midia"].pop("fonte_factual")
    assert "E-RELACAO-NAO-DEMONSTRADA" in codes(_avaliar_sintetico(p,cat))


def test_trama_sem_payoff_concreto_bloqueia_ultimo_plano(monkeypatch):
    p,cat=_completo(monkeypatch)
    p["cenas"][7]["midia"].pop("resultado_verificavel")
    assert "E-PAYOFF-SEM-CONSEQUENCIA" in codes(_avaliar_sintetico(p,cat))


def test_filme_integral_permite_demonstracao_tecnica_equivalente_curada(monkeypatch):
    p,cat=_completo(monkeypatch)
    r=_avaliar_sintetico(p,cat)
    assert "E-REPRESENTACAO-NAO-EQUIVALENTE" not in codes(r)
    assert "E-PROCESSO-SEM-INSPECAO-NO-ACERVO" not in codes(r)
    assert r["pronto_para_tts"]
    assert r["inspecao_humana"]=="PENDENTE"


def test_filme_integral_reprova_e_beam_disfarçado_de_euv(monkeypatch):
    p,cat=_completo(monkeypatch)
    p["cenas"][5]["midia"]["substituicao"]["representacao"]["processo_narrado"]="litografia_euv"
    r=_avaliar_sintetico(p,cat)
    assert "E-REPRESENTACAO-NAO-EQUIVALENTE" in codes(r)
    assert not r["pronto_para_tts"]


def test_filme_integral_reprova_substituicao_inventada_so_no_roteiro(monkeypatch):
    p,cat=_completo(monkeypatch)
    cat["itens"][4]["prova"].pop("processo_verificado")
    r=_avaliar_sintetico(p,cat)
    assert "E-PROCESSO-SEM-INSPECAO-NO-ACERVO" in codes(r)
    assert not r["pronto_para_tts"]


def test_filme_integral_nao_aceita_mudar_identidade_para_literal(monkeypatch):
    p,cat=_completo(monkeypatch)
    p["cenas"][5]["midia"]["identidade"]="literal"
    r=_avaliar_sintetico(p,cat)
    assert "E-REGISTRO-CONTRADITORIO" in codes(r)
    assert not r["pronto_para_tts"]
