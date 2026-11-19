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


def test_gancho_importancia_global_avanca_sem_repetir_mapa():
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    b = next(x for x in pl["beats"] if x["id"] == "g-02-contexto-taiwan")
    info = next(L for L in b["camadas"] if L["id"] == "alcance-global")
    assert info["componente"] == "editorial.statCard"
    assert info["slot"] == "selo"
    assert info["p"]["valor"] == "IMPACTO GLOBAL"
    assert info["t0"] == "@importa"
    tempo = P.resolver_tempos(pl, _palavras(pl["narracao"]["texto"]))
    assert all(x["regra"] != "F-SEM-PROGRESSAO" for x in P.validar(tempo) if x["gravidade"] == "erro")


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
