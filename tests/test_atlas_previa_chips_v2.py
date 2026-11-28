"""Ponte editorial: o primeiro roteiro chips V2 deve resolver tempos e layouts OFFLINE.
Nao confunde teste sintetico de tempo com audio aprovado; Gemini só no workflow privado.
"""
import json
import re
from pathlib import Path

from src.v4.formatos import plano as P

RAIZ = Path(__file__).resolve().parents[1]
ARQ = RAIZ / "src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json"


def _palavras(texto):
    texto = re.findall(r"[\wÀ-ÿº]+", texto)
    return [{"w": x.upper(), "s": round(i / 2.55, 3), "e": round((i + 1) / 2.55, 3)}
            for i, x in enumerate(texto)]


def test_tempo_sintetico_e_contracto_chips_v2():
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    assert pl["abertura_tipo"] == "prova_real"
    assert pl["beats"][0]["composicao"] == "atlas.prova"
    assert pl["narracao"]["texto"].lower().count("noventa") == 0
    pal = _palavras(pl["narracao"]["texto"])
    resolvido = P.resolver_tempos(pl, pal)
    assert 20 <= resolvido["duracao"] <= 30
    assert resolvido["beats"][0]["camadas"][0]["p"]["rotulo_t"] < 3
    wafer = next(L for beat in resolvido["beats"] for L in beat["camadas"] if L["id"] == "wafer-real")
    assert wafer["p"]["rotulo"] == "WAFER DE SILÍCIO · FOTO ILUSTRATIVA"
    assert isinstance(wafer["p"]["rotulo2"], str) and "CIRCUITOS" in wafer["p"]["rotulo2"]
    assert wafer["p"]["rotulo_t"] < wafer["p"]["rotulo2_t"] < wafer["t1"]
    assert wafer["p"]["rotulo2_t"] in P.eventos(resolvido)
    assert all(isinstance(L["t0"], (int, float)) for b in resolvido["beats"] for L in b["camadas"])
    erros = [v for v in P.validar(resolvido) if v["gravidade"] == "erro"]
    if erros:
        print("ATLAS_V2_VALIDATION_ERRORS=" + json.dumps(erros, ensure_ascii=False))
    assert not erros, json.dumps(erros, ensure_ascii=False)


def test_fotos_chips_vem_do_catalogo_com_hash_real():
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    refs = [x["p"]["asset"] for b in pl["beats"] for x in b["camadas"]
            if x["componente"] == "atlas.provaVisual"]
    bib = json.loads((RAIZ / "src/v4/biblioteca_comprovada.json").read_text(encoding="utf-8"))
    by_id = {x["id"]: x for x in bib["itens"]}
    assert len(refs) == 2 and len(set(refs)) == 2
    for x in refs:
        reg = by_id[x]
        assert reg["licenca"] == "CC BY 4.0"
        assert len(reg["sha256_origem"]) == 64
        assert reg["prova"]["midia_corresponde"] is True
        assert reg["prova"]["confirmacao_humana"] is None
    assert "não mostra produção interna" in by_id[refs[0]]["mostra"]
    assert "sem identificação" in by_id[refs[1]]["mostra"]


def test_fim_e_cta_respeitam_duracao_real_da_narracao():
    """Regressão da execução 44437665279: CTA 31.24s e payoff 31.29s
    excederam o WAV real 30.773s apesar do CI sintético verde.
    """
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    palavras = _palavras(pl["narracao"]["texto"])
    # Última palavra realinhada pode terminar quase no final do WAV.
    # O antigo "@fim" somava 0,6s e fechava o plano além do áudio.
    palavras[-1]["e"] = 30.69
    duracao_wav = 30.773
    resolvido = P.resolver_tempos(pl, palavras, duracao_audio=duracao_wav)
    assert resolvido["duracao"] == duracao_wav
    fim = next(L for b in resolvido["beats"] for L in b["camadas"] if L["id"] == "payoff-funcao")
    assert fim["t1"] == duracao_wav
    for b in resolvido["beats"]:
        for L in b["camadas"]:
            assert L["t1"] <= duracao_wav + .001, (b["id"], L["id"], L["t1"])
    assert all(v["regra"] != "F-TEMPO" for v in P.validar(resolvido) if v["gravidade"] == "erro")


def test_gancho_pergunta_avanca_sem_card_cobrindo_o_mapa():
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    b = next(x for x in pl["beats"] if x["id"] == "g-02-contexto-taiwan")
    assert len(b["camadas"]) == 1
    linhas = b["camadas"][0]["p"]["linhas"]
    assert next(l for l in linhas if l["texto"] == "TAIWAN?")["t"] == "@importa"
    tempo = P.resolver_tempos(pl, _palavras(pl["narracao"]["texto"]))
    erros = [x["regra"] for x in P.validar(tempo) if x["gravidade"] == "erro"]
    assert "F-SEM-PROGRESSAO" not in erros
    assert "F-COBRE-TERRITORIO" not in erros


def test_telegram_recebe_bloqueio_sem_video(monkeypatch, tmp_path):
    """Não esconder falha de preflight quando resultado.json não existe."""
    from src.v4.formatos import produzir
    from src.v3 import previa_telegram

    pasta = tmp_path / "bloqueado"
    pasta.mkdir()
    (pasta / "preflight.json").write_text(json.dumps({
        "pronto": False, "itens": [
            {"item": "plano: F-TEMPO payoff", "ok": False, "detalhe": "fora da duração da voz"}
        ]
    }), encoding="utf-8")
    enviados = []
    monkeypatch.setattr(previa_telegram, "chat_autorizado", lambda: ("123", {"tipo": "private", "membros": 2}))
    monkeypatch.setattr(previa_telegram, "_api", lambda nome, data: enviados.append((nome, data)))
    resposta = produzir.telegram(pasta, "Piloto Chips V2")
    assert resposta == {"enviado": True, "sem_mp4": True}
    assert enviados and enviados[0][0] == "sendMessage"
    assert "BLOQUEADO" in enviados[0][1]["text"]
    assert "F-TEMPO" in enviados[0][1]["text"]
    workflow = (RAIZ / ".github/workflows/atlas-chips-v2-privado.yml").read_text(encoding="utf-8")
    bloco = workflow.split("Entregar APENAS no Telegram privado como DIAGNÓSTICO", 1)[1]
    assert '[ -s "$SAIDA/resultado.json" ]' not in bloco.split("Portão editorial", 1)[0]


def test_gancho_com_tempo_real_gemini_nao_congela_tres_segundos():
    """Reproduz o bloqueio 44447705090 usando tempos reais capturados do TTS,
    não uma média artificial de 2,55 palavras por segundo. Mantém portão 3s.
    """
    fixture = json.loads((RAIZ / "tests/dados/atlas_chips_v2_tts_real_run_44447705090.json").read_text(encoding="utf-8"))
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    resolvido = P.resolver_tempos(pl, fixture["palavras"], duracao_audio=fixture["duracao_audio"])
    foto = next(L for beat in resolvido["beats"] for L in beat["camadas"] if L["id"] == "fab18-real-dominante")
    assert foto["p"]["rotulo_t"] == .63
    assert foto["p"]["rotulo2_t"] == 2.65
    assert foto["p"]["rotulo2"] == "FAB 18 · TAIWAN"
    assert foto["t1"] > foto["p"]["rotulo2_t"]
    erros = [v for v in P.validar(resolvido) if v["gravidade"] == "erro"]
    assert not any(v["regra"] == "F-SEM-PROGRESSAO" for v in erros), erros
    assert not any(v["regra"] == "F-TEMPO" for v in erros), erros
    # Evitar a falsa correção "subir limite" (em vez de introduzir prova factual).
    assert P.REGRAS["progressao_max_s"] == 3


def test_telegram_exibe_erros_reais_dos_quadros(monkeypatch, tmp_path):
    """Regressao run 44449171248: preflight verde, render bloqueado por texto a 24 px."""
    from src.v4.formatos import produzir
    from src.v3 import previa_telegram

    pasta = tmp_path / "bloqueado_quadros"
    (pasta / "quadros").mkdir(parents=True)
    (pasta / "preflight.json").write_text(json.dumps({
        "pronto": True, "itens": [{"item": "geometria", "ok": True, "detalhe": "OK"}]
    }), encoding="utf-8")
    (pasta / "quadros" / "relatorio.json").write_text(json.dumps({
        "quadros": [{"t": 1.5}],
        "problemas": [
            {"t": 1.5, "regra": "R-TEXTO-PEQUENO",
             "texto": "'FAB 18 · TSMC' a 24 px (mín. 26)", "aviso": False},
            {"t": 1.5, "regra": "A-CREDITO-RODAPE",
             "texto": "crédito na área de interface", "aviso": True}
        ]
    }), encoding="utf-8")
    enviados = []
    monkeypatch.setattr(previa_telegram, "chat_autorizado",
                        lambda: ("123", {"tipo": "private", "membros": 2}))
    monkeypatch.setattr(previa_telegram, "_api",
                        lambda nome, data: enviados.append((nome, data)))
    resultado = produzir.telegram(pasta, "Chips V2")
    assert resultado == {"enviado": True, "sem_mp4": True}
    mensagem = enviados[0][1]["text"]
    assert "preflight: 1/1 itens OK" in mensagem
    assert "etapa: quadros (1 analisados; 1 erros)" in mensagem
    assert "R-TEXTO-PEQUENO" in mensagem and "FAB 18" in mensagem
    assert "A-CREDITO-RODAPE" not in mensagem


def test_rotulo_prova_visual_atlas_atende_legibilidade_minima():
    """Regra do componente reutilizavel, nao hardcode do episodio Chips."""
    src = (RAIZ / "motor4/remotion/src/formatos/Primitivas.tsx").read_text(encoding="utf-8")
    prova = src.split("// atlas.provaVisual", 1)[1].split("// editorial.cta", 1)[0]
    assert "fontSize: 30" in prova
    assert "fontSize: 24" not in prova
    assert "maxWidth: b.w - 44" in prova


def test_gancho_real_nao_encurta_quando_gemini_fala_rapido():
    """Run 44450584008: POR aos 2.418s fazia a foto terminar aos 2.298s."""
    fixture = json.loads((RAIZ / "tests/dados/atlas_chips_v2_tts_real_run_44450584008.json").read_text(encoding="utf-8"))
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    r = P.resolver_tempos(pl, fixture["palavras"], duracao_audio=fixture["duracao_audio"])
    foto = next(L for L in r["beats"][0]["camadas"] if L["componente"] == "atlas.provaVisual")
    mapa = r["beats"][1]
    pergunta = mapa["camadas"][0]
    assert foto["t0"] == 0
    assert foto["t1"] == 2.5, foto
    assert mapa["t"] == foto["t1"]
    assert pergunta["t0"] >= mapa["t"]
    assert pergunta["p"]["linhas"][0]["t"] >= pergunta["t0"]
    cam = next(k for k in r["palco"] if k["composicao"] == mapa["composicao"]
               and abs(k["t"] - mapa["t"]) < .002)
    assert pergunta["t0"] + .35 >= cam["t"] + cam["dur_camera"]
    assert P.REGRAS["progressao_max_s"] == 3
    erros = [v for v in P.validar(r) if v["gravidade"] == "erro"]
    assert not erros, json.dumps(erros, ensure_ascii=False)


def test_piso_temporal_nao_atrasa_gancho_com_narracao_mais_lenta():
    """Run 44447705090: POR depois de 3.5s; mapa segue palavra sem corte aos 2.5s."""
    fixture = json.loads((RAIZ / "tests/dados/atlas_chips_v2_tts_real_run_44447705090.json").read_text(encoding="utf-8"))
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    r = P.resolver_tempos(pl, fixture["palavras"], duracao_audio=fixture["duracao_audio"])
    foto = r["beats"][0]["camadas"][0]
    mapa = r["beats"][1]
    assert foto["t1"] > 3.0
    assert foto["t1"] == mapa["t"]
    assert P.REGRAS["progressao_max_s"] == 3
    erros = [v for v in P.validar(r) if v["gravidade"] == "erro"]
    assert not erros, json.dumps(erros, ensure_ascii=False)
