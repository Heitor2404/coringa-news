"""Envia prova visual curta ao Telegram PRIVADO autorizado; nunca publica em redes.

Usado tanto após o render experimental quanto para recuperar um artefato
já concluído. A origem é sempre um arquivo local produzido/baixado pelo workflow,
não uma URL arbitrária. Falhas de QA viram mensagem BLOQUEADO sem vídeo.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.v3 import previa_telegram


def entregar(saida: Path, titulo: str = "Panamá — eclusa causal 7,8 s", *,
            video: str = "prova_causal_8s.mp4", contato_nome: str = "contato_causal_8s.jpg",
            qa_nome: str = "qa_causal.json", duracao: float = 7.8) -> dict:
    pasta = Path(saida)
    filme = pasta / video
    contato = pasta / contato_nome
    qa_file = pasta / qa_nome

    # Destino único, com verificação de privacidade já usada pelos outros canais.
    chat, info = previa_telegram.chat_autorizado()

    motivos = []
    try:
        qa = json.loads(qa_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        qa = {}
        motivos.append("relatório QA ausente ou inválido")

    if qa.get("status") != "AGUARDANDO_REVISAO_HUMANA":
        motivos.append("estado editorial não permite envio de prévia")
    if qa.get("nao_publicado") is not True or qa.get("sem_tts") is not True:
        motivos.append("escopo privado/silencioso não comprovado")
    if abs(float(qa.get("duracao") or 0) - duracao) > 0.1:
        motivos.append(f"duração da prévia divergente de {duracao:g} s")
    if not filme.is_file() or filme.stat().st_size < 50_000:
        motivos.append("MP4 ausente ou vazio")
    # E212: old artifacts cannot bypass the renderer policy by being resent.
    from src.v4.formatos import politica_animacao
    try:
        politica_animacao.validar_entrega_privada(pasta / "props.json", filme, qa)
    except (ValueError, OSError, TypeError) as exc:
        motivos.append("política de animação: " + str(exc)[:250])
    if motivos:
        txt = ("ATLAS — PANAMÁ: PRÉVIA PRIVADA BLOQUEADA\n"
               "NÃO PUBLICADO · nenhum vídeo enviado\n"
               + "\n".join("- " + m for m in motivos[:6])
               + "\nConferir execução no GitHub Actions.")
        previa_telegram._api("sendMessage", {"chat_id": chat, "text": txt[:3900]})
        raise RuntimeError("Prévia bloqueada: " + "; ".join(motivos))

    caption = (
        "CORINGA EXPLICA · PRÉVIA PRIVADA\n"
        f"{titulo}\n"
        f"{duracao:g} segundos · SEM NARRAÇÃO\n"
        "STATUS: AGUARDANDO APROVAÇÃO HUMANA\n"
        "NÃO PUBLICADO — prova visual experimental."
    )
    previa_telegram._api(
        "sendVideo",
        {"chat_id": chat, "caption": caption, "supports_streaming": "true"},
        ("video", previa_telegram._caber(filme)),
    )
    anexos = 0
    if contato.is_file() and contato.stat().st_size > 10_000:
        previa_telegram._api(
            "sendPhoto",
            {"chat_id": chat,
             "caption": f"Panamá {duracao:g} s — folha de quadros da prova causal (privado)"},
            ("photo", contato),
        )
        anexos += 1
    previa_telegram._api(
        "sendMessage",
        {"chat_id": chat, "text":
         f"ATLAS — PANAMÁ: prévia de {duracao:g} s entregue apenas para revisão visual.\n"
         "É uma demonstração SILENCIOSA, não um episódio final. "
         "Avalie se a cena realmente demonstra entrada, fecho, enchimento, equalização e saída. "
         "Mesmo com CI verde, estética continua pendente. Publicação proibida."},
    )
    return {
        "enviado": True,
        "destino": f"{info['tipo']} privado autorizado",
        "arquivo": filme.name,
        "anexos": anexos,
        "publicado": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("saida", type=Path)
    p.add_argument("--titulo", default="Panamá — eclusa causal 7,8 s")
    p.add_argument("--video", default="prova_causal_8s.mp4")
    p.add_argument("--contato", default="contato_causal_8s.jpg")
    p.add_argument("--qa", default="qa_causal.json")
    p.add_argument("--duracao", type=float, default=7.8)
    args = p.parse_args(argv)
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        raise RuntimeError("Telegram privado não configurado; não enviar a outro destino")
    resultado = entregar(args.saida, args.titulo, video=args.video,
                        contato_nome=args.contato, qa_nome=args.qa, duracao=args.duracao)
    print(json.dumps(resultado, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
