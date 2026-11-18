"""Amostra visual privada do ATLAS: ~13 s em 5 cortes do plano completo, SEM renderizar 79 s.

Cada corte preserva a linha do tempo absoluta do storyboard: cena, mapa, legenda e voz reais.
Exibe gancho, cartão, subida da eclusa, palco técnico e CTA.
Execucao: python scripts/atlas_previa_curta.py render|enviar saida_formatos/atlas
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

# Executavel por caminho: python scripts/atlas_previa_curta.py, sem depender de PYTHONPATH no runner.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.v4.backends import js
from src.v4.formatos import plano as P, produzir
from src.v4.util import RAIZ, rodar

FPS = 30
# (id, inicio absoluto, fim absoluto).
JANELAS = [
    ("gancho_mapa", 0.0, 2.40),
    ("cartao_26m", 18.80, 21.40),
    ("eclusa_subindo", 36.70, 39.50),
    ("palco_tecnico", 41.20, 43.80),
    ("cta_final", 76.30, 78.95),
]


def _ler(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def montar(partes, voz, registro, destino):
    # Remotion e a eclusa V2 podem ter time bases e parâmetros H.264 diferentes.
    # Decodificar e montar uma única trilha CFR e uma única trilha AAC.
    entradas = []
    filtros = []
    for i, (video, janela) in enumerate(zip(partes, registro, strict=True)):
        entradas += ["-i", video]
        n = janela["frames_renderizados"]
        inicio = janela["inicio_original_s"]
        filtros.append(f"[{i}:v]trim=end_frame={n},setsar=1,format=yuv420p,"
                       f"settb=1/{FPS},setpts=N[v{i}]")
        filtros.append(f"[{len(partes)}:a]atrim=start={inicio}:duration={n / FPS:.9f},"
                       f"asetpts=PTS-STARTPTS,aresample=48000[a{i}]")
    pares = "".join(f"[v{i}][a{i}]" for i in range(len(partes)))
    filtros.append(f"{pares}concat=n={len(partes)}:v=1:a=1[v][a]")
    rodar(["ffmpeg", "-v", "error", "-y", *entradas, "-i", voz,
           "-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS),
           "-video_track_timescale", "90000", "-c:a", "aac", "-b:a", "160k",
           "-movflags", "+faststart", destino], timeout=300)


def quadros_reproduzidos(video):
    # Decodificar no ritmo de reprodução também revela buracos nos timestamps.
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-xerror", "-i", str(video),
                                   "-an", "-vf", f"fps={FPS},scale=96:170", "-pix_fmt", "rgb24",
                                   "-f", "rawvideo", "-"])
    return np.frombuffer(raw, np.uint8).reshape(-1, 170, 96, 3).astype(np.int16)


def conferir_montagem(mp4, partes, registro, base_eclusa, primeiro_quadro):
    final = quadros_reproduzidos(mp4)
    esperado = sum(j["frames_renderizados"] for j in registro)
    if len(final) != esperado:
        raise RuntimeError(f"MP4 final: {len(final)} quadros reproduzidos, esperados {esperado}")
    pos = 0
    for video, janela in zip(partes, registro, strict=True):
        n = janela["frames_renderizados"]
        origem = quadros_reproduzidos(video)
        trecho = final[pos:pos + n]
        if len(origem) != n or np.abs(trecho - origem).mean(axis=(1, 2, 3)).max() > 4:
            raise RuntimeError(f"MP4 diverge do corte {janela['nome']}")
        if janela["nome"] == "eclusa_subindo":
            # Área do mecanismo, sem o selo e as legendas da camada global.
            mecanismo = trecho[:, 50:104]
            original = quadros_reproduzidos(base_eclusa)[primeiro_quadro:primeiro_quadro+n, 50:104]
            if len(original) != n or np.abs(mecanismo - original).mean(axis=(1, 2, 3)).max() > 5:
                raise RuntimeError("MP4 não reproduz a animação V2 da eclusa")
            if np.abs(mecanismo[-1] - mecanismo[0]).mean() < 2:
                raise RuntimeError("subida da eclusa congelada no MP4")
        pos += n
    print(f"ATLAS_MP4_CONFERIDO {len(final)} quadros; {len(partes)} cortes e movimento da eclusa", flush=True)


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
        clipes = [c for c in pl.get("clipes", []) if inicio < c["t1"] and c["t0"] < fim]
        eclusa = nome == "eclusa_subindo"
        if eclusa:
            if len(clipes) != 1 or clipes[0]["componente"] != "mecanismo.eclusa":
                raise RuntimeError("janela sem a eclusa do plano")
            clipe = clipes[0]
            if not clipe["t0"] <= inicio < fim <= clipe["t1"]:
                raise RuntimeError("janela cruza o limite da eclusa")
        elif clipes:
            raise RuntimeError(f"janela {nome} invade clipe V2")

        f0, f1 = round(inicio * FPS), round(fim * FPS) - 1
        n = f1 - f0 + 1
        if n <= 0 or n > 90:
            raise RuntimeError(f"amostra fora do limite de 3s: {nome}")
        video = trab / f"{nome}_video.mp4"
        inicio_render = time.monotonic()
        if eclusa:
            # A base V2 é independente da voz e da legenda; o workflow restaura
            # somente este MP4 quando o plano, tema e renderizador coincidem.
            cache_key = os.environ.get("ATLAS_ECLUSA_KEY")
            base = trab / f"eclusa_v2_{cache_key or 'local'}.mp4"
            if not cache_key or not base.exists():
                tmp = trab / "eclusa_v2.tmp.mp4"
                produzir._clipe(clipe, can, (trab / "v2").resolve(), tmp.resolve())
                tmp.replace(base)
            alpha = trab / "eclusa_legenda.webm"
            js.remotion("Camada", camada, alpha, trab / "camada", alfa=True, quadros=(f0, f1))
            primeiro_quadro = f0 - round(clipe["t0"] * FPS)
            offset = primeiro_quadro / FPS
            rodar(["ffmpeg", "-v", "error", "-y", "-ss", f"{offset:.6f}", "-i", base,
                   "-c:v", "libvpx", "-i", alpha, "-filter_complex",
                   "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p", "-frames:v", str(n),
                   "-an", "-c:v", "libx264", "-crf", "16", video])
        else:
            js.remotion("AtlasAmostra", props, video, trab / nome, quadros=(f0, f1))
        partes.append(video)
        registro.append({"nome": nome, "inicio_original_s": inicio, "fim_original_s": fim,
                         "frames_renderizados": n, "tempo_execucao_s": round(time.monotonic() - inicio_render, 2)})
        print(f"ATLAS_AMOSTRA {nome}: {n} frames, {registro[-1]['tempo_execucao_s']}s", flush=True)

    candidato = trab / "montagem.mp4"
    montar(partes, saida / "voz.wav", registro, candidato)
    from src.v3.previa_telegram import _caber
    entrega = _caber(candidato)
    conferir_montagem(entrega, partes, registro, base, primeiro_quadro)
    final = saida / "atlas_identidade_v1_amostra_curta.mp4"
    entrega.replace(final)
    registro_json = {
        "tipo": "MONTAGEM DE TESTE — cortes temporais; nao representa o episodio final nem a continuidade do roteiro",
        "referencia_visual": "docs/v4/formatos/GUIA_VISUAL_ATLAS_V1.md",
        "janelas": registro, "total_frames": sum(r["frames_renderizados"] for r in registro),
        "duracao_aproximada_s": sum(r["frames_renderizados"] for r in registro) / FPS,
        "tempo_total_render_s": round(time.monotonic() - t0, 2),
        "componente_mecanismo_v2": "mecanismo.eclusa — subida com legenda e voz",
        "quadros_finais_conferidos": True, "publicado": False, "aprovacao_estetica": False
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
    if not r.get("quadros_finais_conferidos"):
        raise RuntimeError("MP4 sem conferência dos quadros finais")
    titulo = ("ATLAS V1 — AMOSTRA PRIVADA (~13 s): gancho / cartao / eclusa / fundo tecnico / CTA. "
              "CORTES entre trechos distintos, voz correspondente a cada trecho. "
              "Nao e episodio completo. "
              "Aguardando aprovacao estetica; nada publicado.")
    previa_telegram._api("sendVideo", {"chat_id": chat, "caption": titulo, "supports_streaming": "true"},
                         ("video", mp4))
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
