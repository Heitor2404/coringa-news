"""Amostra visual privada do ATLAS: ~10 s em 4 cortes do plano completo, SEM renderizar 79 s.

Cada corte preserva a linha do tempo absoluta do storyboard: cena, mapa, legenda e voz reais.
Exibe gancho, cartao, palco tecnico e CTA. A animacao V2 (eclusa 31-41s)
NAO integra esta amostra, pois precisaria de render proprio. Nao e um episodio.
Execucao: python scripts/atlas_previa_curta.py render|enviar saida_formatos/atlas
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from src.v4.backends import js
from src.v4.formatos import plano as P
from src.v4.util import RAIZ, rodar

FPS = 30
# (id, inicio absoluto, fim absoluto) — intervalos FORA do clipe V2 aprovado.
JANELAS = [
    ("gancho_mapa", 0.0, 2.40),
    ("cartao_26m", 18.80, 21.40),
    ("palco_tecnico", 41.20, 43.80),
    ("cta_final", 76.30, 78.95),
]


def _ler(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def render(saida: Path) -> Path:
    pf = _ler(saida / "preflight.json")
    if not pf.get("pronto"):
        raise RuntimeError("preflight vermelho: proibido renderizar ate amostra curta")
    quad = _ler(saida / "quadros" / "relatorio.json")
    if not quad.get("ok"):
        raise RuntimeError("styleframes com erros: proibido renderizar amostra curta")

    pl = _ler(saida / "plano_resolvido.json")
    meta = _ler(saida / "narracao.json")
    imgs = _ler(saida / "ativos.json")
    can = P.canal(pl.get("canal", "coringa"))
    geo = _ler(RAIZ / pl["geo"]) if pl.get("geo") else None
    if pl.get("formato") != "atlas":
        raise RuntimeError("amostra restrita ao ATLAS")
    visual = P.props(pl, P.tokens_canal(can), geo, imgs)
    camada = P.props_camada(pl, meta)
    props = {"duracao": pl["duracao"], "visual": visual, "legenda": camada}

    trab = saida / "_amostra"
    trab.mkdir(parents=True, exist_ok=True)
    partes = []
    registro = []
    t0 = time.monotonic()
    for nome, inicio, fim in JANELAS:
        if not (0 <= inicio < fim <= pl["duracao"]):
            raise RuntimeError(f"janela invalida {nome}: {inicio}-{fim}")
        for c in pl.get("clipes") or []:
            if inicio < c["t1"] and c["t0"] < fim:
                raise RuntimeError(f"janela {nome} invade clipe V2; jamais renderizar mapa no lugar do mecanismo")

        f0, f1 = round(inicio * FPS), round(fim * FPS) - 1
        n = f1 - f0 + 1
        if n <= 0 or n > 90:
            raise RuntimeError(f"amostra fora do limite de 3s: {nome}")
        video = trab / f"{nome}_video.mp4"
        mux = trab / f"{nome}.mp4"
        inicio_render = time.monotonic()
        js.remotion("AtlasAmostra", props, video, trab / nome, quadros=(f0, f1))
        rodar(["ffmpeg", "-v", "error", "-y", "-i", str(video),
               "-ss", f"{inicio:.3f}", "-t", f"{n / FPS:.3f}", "-i", str(saida / "voz.wav"),
               "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
               "-af", "aresample=async=1:first_pts=0", "-shortest", "-movflags", "+faststart",
               str(mux)], timeout=180, log=trab / f"{nome}_mux.log")
        partes.append(mux)
        registro.append({"nome": nome, "inicio_original_s": inicio, "fim_original_s": fim,
                         "frames_renderizados": n, "tempo_execucao_s": round(time.monotonic() - inicio_render, 2)})
        print(f"ATLAS_AMOSTRA {nome}: {n} frames, {registro[-1]['tempo_execucao_s']}s", flush=True)

    lista = trab / "partes.txt"
    lista.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in partes))
    final = saida / "atlas_identidade_v1_amostra_curta.mp4"
    rodar(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
           "-c", "copy", "-movflags", "+faststart", str(final)], timeout=180)
    registro_json = {
        "tipo": "MONTAGEM DE TESTE — cortes temporais; nao representa o episodio final nem a continuidade do roteiro",
        "referencia_visual": "docs/v4/formatos/GUIA_VISUAL_ATLAS_V1.md",
        "janelas": registro, "total_frames": sum(r["frames_renderizados"] for r in registro),
        "duracao_aproximada_s": sum(r["frames_renderizados"] for r in registro) / FPS,
        "tempo_total_render_s": round(time.monotonic() - t0, 2),
        "componente_mecanismo_v2": "NAO TESTADO nesta amostra — exige trecho especifico",
        "publicado": False, "aprovacao_estetica": False
    }
    (saida / "atlas_amostra_relatorio.json").write_text(json.dumps(registro_json, ensure_ascii=False, indent=2))
    print(json.dumps(registro_json, ensure_ascii=False), flush=True)
    return final


def enviar(saida: Path) -> None:
    """Apenas Telegram privado autorizado; se qualquer portao falhou, envia erro sem fingir aprovacao."""
    from src.v3 import previa_telegram
    chat, _ = previa_telegram.chat_autorizado()
    mp4 = saida / "atlas_identidade_v1_amostra_curta.mp4"
    relatorio = saida / "atlas_amostra_relatorio.json"
    preflight = saida / "preflight.json"
    quadros = saida / "quadros" / "relatorio.json"
    if not mp4.exists():
        motivos = []
        if preflight.exists():
            p = _ler(preflight)
            motivos.extend(i.get("item") or "erro" for i in p.get("itens", []) if not i.get("ok"))
        if quadros.exists():
            q = _ler(quadros)
            motivos.extend(f"{e['regra']} {e.get('texto','')}" for e in q.get("problemas", []) if not e.get("aviso"))
        msg = ("ATLAS V1 — PREVIA CURTA BLOQUEADA. Nenhum video gerado nem publicado. "
               "Falhas: " + ("; ".join(motivos[:8]) if motivos else "consultar logs do Actions")[:3100])
        previa_telegram._api("sendMessage", {"chat_id": chat, "text": msg})
        return

    if not relatorio.exists():
        raise RuntimeError("video sem relatorio de janelas; bloqueio de envio")
    r = _ler(relatorio)
    titulo = ("ATLAS V1 — AMOSTRA PRIVADA (~10 s): gancho / cartao / fundo tecnico / CTA. "
              "CORTES entre trechos distintos, voz correspondente a cada trecho. "
              "Nao e episodio completo. Mecanismo V2 fora desta amostra. "
              "Aguardando aprovacao estetica; nada publicado.")
    previa_telegram._api("sendVideo", {"chat_id": chat, "caption": titulo, "supports_streaming": "true"},
                         ("video", previa_telegram._caber(mp4)))
    for path, descricao in [
        (saida / "quadros" / "styleframes.jpg", "ATLAS V1 — quadros visuais (privado)"),
        (saida / "quadros" / "celular.jpg", "ATLAS V1 — leitura em celular (privado)"),
        (relatorio, "ATLAS V1 — origem dos intervalos de teste (privado)")]:
        if path.exists():
            previa_telegram._api("sendDocument", {"chat_id": chat, "caption": descricao}, ("document", path))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in {"render", "enviar"}:
        raise SystemExit("uso: python scripts/atlas_previa_curta.py render|enviar <dir_saida>")
    if sys.argv[1] == "render":
        render(Path(sys.argv[2]))
    else:
        enviar(Path(sys.argv[2]))
