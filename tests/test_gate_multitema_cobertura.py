"""Regressão do MESMO portão por acontecimento em temas distintos.

Os testes são SINTÉTICOS: conferir_bytes=False NÃO é usado na produção.
Não aprovam visualmente nenhuma cena e não são autorização para publicar.
"""
from src.v4.formatos import gate_filme_completo as G


def filme(tema, cenas, **rubrica):
    return {
        "versao": 1, "formato": "filme_editorial",
        "tipo": "PRE_PRODUCAO_PRIVADA", "id": tema,
        "politica": {"publicar": False},
        # Ausente de propósito: um filme NOVO deve adotar modo narrativo.
        "duracao_planejada_s": cenas[-1]["fim"],
        "rubrica_editorial": {
            "min_videos_reais_independentes": rubrica.get("videos", 0),
            "max_fracao_fotos_estaticas": rubrica.get("fotos", 1),
            "max_foto_individual_s": 7,
            "mapa_evidencia_real_obrigatorio": rubrica.get("mapa", False)
        },
        "base_narracao": {
            "motor": "gemini", "voz": "Charon",
            "fallback": "bloquear", "arquivo_wav": None,
        },
        "cenas": cenas,
    }


def cena(id, t0, t1, acao, promessa, midia):
    return {"id": id, "inicio": t0, "fim": t1,
            "acao": acao, "promessa": promessa, "midia": midia}


def foto(id):
    return {"id": id, "natureza": "foto",
            "sha256_origem": "a" * 64, "licenca": "CC BY 4.0",
            "credito": "Arquivo primário", "uso_comercial": "sim",
            "prova": {"midia_corresponde": True}}


def avaliar(p, itens=None):
    return G.avaliar(p, {"itens": itens or []}, conferir_bytes=False)


def test_venezuela_nao_exige_video_ou_mapa_quando_foto_comprova_objeto():
    p=filme("relevo_venezuela",[
        cena("roraima",0,4,"MOSTRAR","Reconhecer a montanha real na paisagem",
             {"tipo":"foto","identidade":"literal","asset_id":"roraima_original"})
    ])
    r=avaliar(p,[foto("roraima_original")])
    assert r["modo_duracao"]=="narrativa"
    assert r["pronto_para_tts"] is True  # somente em teste de catálogo fictício
    assert r["pronto_para_render"] is False
    assert r["inspecao_humana"]=="PENDENTE"
    assert r["cobertura_acontecimentos"][0]["status_tecnico"]=="SEM_BLOQUEIO_LOCAL_REVISAO_HUMANA_PENDENTE"
    assert r["cenas_com_bloqueios_locais"]==0


def test_suez_acontecimento_que_exige_mecanismo_nao_vira_cartao():
    p=filme("eclusas_suez",[
        cena("processo",0,18,"DEMONSTRAR",
             "Mostrar como duas comportas controlam um fluxo de água",
             {"tipo":"foto","identidade":"explicativa","asset_id":"imagem_maquina"})
    ])
    r=avaliar(p,[foto("imagem_maquina")])
    assert "E-ACAO-SEM-VIDEO" in set(r["cobertura_acontecimentos"][0]["bloqueios"])
    assert r["cobertura_acontecimentos"][0]["status_tecnico"]=="BLOQUEADO"
    assert not r["pronto_para_tts"]


def test_historia_de_conflito_com_mapa_sem_prova_cartografica_nao_passa(monkeypatch):
    from src.v4.formatos import ponte_mapa_atlas
    monkeypatch.setattr(ponte_mapa_atlas,"validar_comprovante",
                        lambda _: ["sem raster e MP4 original"])
    p=filme("geografia_conflito",[
        cena("territorio",0,3,"LOCALIZAR",
             "Situar o conflito no território correspondente",
             {"tipo":"atlas_map","identidade":"explicativa",
              "clipe":"inexistente.mp4","prova":"inexistente.json",
              "sha256":"b"*64})
    ],mapa=True)
    r=avaliar(p)
    assert "E-MAPA-SEM-COMPROVANTE" in r["cobertura_acontecimentos"][0]["bloqueios"]
    assert "E-CARTOGRAFIA-NAO-INTEGRADA" in r["bloqueios_globais"]
    assert r["mapas_atlas_comprovados"]==0
    assert not r["pronto_para_tts"]


def test_documentario_sem_teto_narrativo_mantem_bloqueios_de_qualidade():
    # Narrativa longa com 3 acontecimentos. Não existe teto editorial;
    # a falta de demonstração concreta deve continuar bloqueando.
    p=filme("industria_chips",[
        cena("onde",0,2,"MOSTRAR","Visualizar fábrica com origem comprovada",
             {"tipo":"foto","identidade":"literal","asset_id":"roraima_original"}),
        cena("como",2,180,"DEMONSTRAR",
             "Entender etapa física com movimento verdadeiro",
             {"tipo":"video","identidade":"representativa","asset_id":"nao_curado"}),
        cena("consequencia",180,220,"REVELAR",
             "Entender consequência material documentada",
             {"tipo":"video","identidade":"representativa","asset_id":"nao_curado2"}),
    ])
    r=avaliar(p,[foto("roraima_original")])
    assert r["modo_duracao"]=="narrativa"
    assert r["previsao_s"]==220
    assert r["diagnostico_plataformas"]["destinos"]["youtube_shorts"]["estado"]=="EXIGE_OUTRO_FORMATO_OU_VERSAO"
    assert "E-TEMPO" not in {x["codigo"] for x in r["bloqueios"]}
    assert r["cenas_com_bloqueios_locais"]==2
    assert not r["pronto_para_tts"]


def test_repeticao_de_prova_persiste_em_qualquer_tema():
    p=filme("tema_livre",[
        cena("a",0,2.8,"MOSTRAR","Mostrar a primeira evidência visível",
             {"tipo":"foto","identidade":"literal","asset_id":"foto_unica"}),
        cena("b",2.8,5.6,"MOSTRAR","Mostrar uma segunda informação distinta",
             {"tipo":"foto","identidade":"literal","asset_id":"foto_unica"}),
    ])
    r=avaliar(p,[foto("foto_unica")])
    assert "E-FONTE-REPETIDA" in r["cobertura_acontecimentos"][1]["bloqueios"]
    assert not r["pronto_para_tts"]
