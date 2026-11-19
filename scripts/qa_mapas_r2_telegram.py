"""Entrega o MP4 de mapas já renderizado ao Telegram PRIVADO autorizado.

Não publica em redes. Falha fechada caso QA, áudio ou mídia faltem.
Usa apenas TELEGRAM_CHAT_ID fixado em secrets e `chat_autorizado`.
"""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from src.v3 import previa_telegram

def entregar(pasta: Path) -> dict:
    pasta=Path(pasta)
    video=pasta/"mapas_narrados_r2.mp4"
    contato=pasta/"contato_editorial.jpg"
    relatorio=pasta/"qa_montagem.json"
    plano_path=pasta/"plano_sincronizado.json"
    problemas=[]
    try:
        qa=json.loads(relatorio.read_text(encoding="utf8"))
        plano=json.loads(plano_path.read_text(encoding="utf8"))
    except (OSError,ValueError) as e:
        qa,plano={},{}
        problemas.append("QA ou plano sincronizado ausente/inválido")
    if qa.get("status_tecnico")!="PRONTO_PARA_REVISAO" or qa.get("problemas_tecnicos"):
        problemas.append("QA técnico não autoriza prévia")
    if (qa.get("publicavel") is not False or qa.get("aprovacao_humana")!="PENDENTE"
        or qa.get("tem_audio") is not True):
        problemas.append("status PRIVADO/NÃO APROVADO ou áudio não comprovado")
    shots=plano.get("shots") or []
    if len(shots)!=3 or any(s.get("type")!="map" for s in shots):
        problemas.append("não são os três mapas esperados")
    if (plano.get("sincronia_voz") or {}).get("tempo_audio")!=1:
        problemas.append("voz não está comprovadamente em velocidade natural")
    if not video.is_file() or video.stat().st_size<100_000:
        problemas.append("MP4 ausente ou vazio")
    if not contato.is_file() or contato.stat().st_size<6_000:
        problemas.append("folha de quadros ausente ou vazia")
    if video.is_file() and video.stat().st_size>=100_000:
        r=subprocess.run(["ffprobe","-v","error","-show_entries",
                          "stream=codec_type:format=duration","-of","json",
                          str(video)],capture_output=True,text=True,timeout=30)
        if r.returncode:
            problemas.append("ffprobe falhou")
        else:
            info=json.loads(r.stdout)
            has_audio=any(s.get("codec_type")=="audio" for s in info.get("streams",[]))
            has_video=any(s.get("codec_type")=="video" for s in info.get("streams",[]))
            length=float((info.get("format") or {}).get("duration") or 0)
            if not (has_audio and has_video and 10.3<=length<=10.7):
                problemas.append("vídeo/áudio/duração divergentes da prévia de 10,47s")
    # Não sequer envia aviso para destino arbitrário: a verificação é obrigatória.
    chat,tipos=previa_telegram.chat_autorizado()
    if problemas:
        previa_telegram._api("sendMessage",{"chat_id":chat,"text":
            "CORINGA · PRÉVIA DE MAPAS BLOQUEADA (NÃO ENVIADA)\n"+
            "\n".join("- "+m for m in problemas)+"\nNÃO PUBLICADO."})
        raise RuntimeError("; ".join(problemas))
    titulo=("CORINGA EXPLICA · PRÉVIA PRIVADA 10,47s\n"
            "Taiwan (país em destaque) · Venezuela (pins) · Suez (rota)\n"
            "Barra global e voz de TESTE em tempo natural.\n"
            "AGUARDANDO SUA AVALIAÇÃO · NÃO PUBLICADO.")
    a=previa_telegram._api("sendVideo",{
        "chat_id":chat,"caption":titulo,"supports_streaming":"true"
    },("video",previa_telegram._caber(video)))
    if not a or not a.get("message_id"):
        raise RuntimeError("Telegram não confirmou message_id do MP4")
    b=previa_telegram._api("sendPhoto",{
        "chat_id":chat,"caption":"Folha de quadros · 3 mapas, sem aprovação editorial."
    },("photo",contato))
    if not b or not b.get("message_id"):
        raise RuntimeError("Telegram não confirmou message_id do JPEG")
    c=previa_telegram._api("sendMessage",{
        "chat_id":chat,
        "text":("Esta é a correção dos mapas e da barra global, NÃO um vídeo final. "
                "Verifique destaque de país, distância entre pins, rota geográfica e timbre de voz. "
                "Ainda não publicável.")
    })
    if not c or not c.get("message_id"):
        raise RuntimeError("Telegram não confirmou a mensagem de contexto")
    return {"enviado":True,"destino":tipos["tipo"]+" privado autorizado",
            "video_message_id":a["message_id"],
            "photo_message_id":b["message_id"],
            "context_message_id":c["message_id"],
            "arquivo":video.name,"publicado":False,"aprovacao_humana":"PENDENTE"}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("pasta",type=Path)
    args=ap.parse_args()
    print(json.dumps(entregar(args.pasta),ensure_ascii=False))
