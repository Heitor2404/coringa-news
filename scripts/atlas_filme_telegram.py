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


def entregar(saida: Path, titulo: str = "Panamá — eclusa causal 7,8 s") -> dict:
    pasta = Path(saida)
    filme = pasta / "prova_causal_8s.mp4"
    contato = pasta / "contato_causal_8s.jpg"
    qa_file = pasta / "qa_causal.json"

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
    if abs(float(qa.get("duracao") or 0) - 7.8) > 0.1:
        motivos.append("duração da prévia divergente de 7,8 s")
    if not filme.is_file() or filme.stat().st_size < 50_000:
        motivos.append("MP4 ausente ou vazio")
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
        "7,8 segundos · SEM NARRAÇÃO\n"
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
             "caption": "Panamá 7,8 s — folha de quadros da prova causal (privado)"},
            ("photo", contato),
        )
        anexos += 1
    previa_telegram._api(
        "sendMessage",
        {"chat_id": chat, "text":
         "ATLAS — PANAMÁ: prévia de 7,8 s entregue apenas para revisão visual.\n"
         "É uma demonstração SILENCIOSA, não um episódio final. "
         "Avalie se o portão real → esquema → água/navio subindo funciona visualmente. "
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
    args = p.parse_args(argv)
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        raise RuntimeError("Telegram privado não configurado; não enviar a outro destino")
    resultado = entregar(args.saida, args.titulo)
    print(json.dumps(resultado, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
