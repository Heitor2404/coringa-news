"""Entrega estritamente PRIVADA dos três estudos narrados, após gates técnicos.

Três provas em assuntos diferentes não são vídeos autorizados a publicar.
Sem segredo ou chat privado, nenhuma mídia sai do runner.
"""
import argparse
import json
from pathlib import Path
from src.v3 import previa_telegram

IDS=("taiwan_chips","hubble_nasa","hindenburg_1937")
TITULOS=("Taiwan e chips","NASA e Hubble","Hindenburg 1937")

def entregar(pasta:Path):
    chat,info=previa_telegram.chat_autorizado()
    paths=[]
    problemas=[]
    for id_,titulo in zip(IDS,TITULOS):
        d=Path(pasta)/id_
        video=d/"episodio_narrado.mp4"
        qa=d/"qa_montagem.json"
        if not video.is_file() or video.stat().st_size < 90000 or not qa.is_file():
            problemas.append(f"{id_}: sem MP4 ou QA")
            continue
        rel=json.loads(qa.read_text(encoding="utf-8"))
        if (rel.get("status_tecnico")!="PRONTO_PARA_REVISAO" or
            rel.get("publicavel") is not False or
            rel.get("aprovacao_humana")!="PENDENTE" or
            rel.get("tem_audio") is not True or
            len(rel.get("amostras_editoriais") or [])!=4):
            problemas.append(f"{id_}: revisão técnica bloqueada")
            continue
        paths.append((titulo,video,d/"contato_editorial.jpg"))
    if problemas or len(paths)!=3:
        previa_telegram._api("sendMessage",{"chat_id":chat,"text":
            "QA MULTITEMA BLOQUEADA — NENHUM VÍDEO ENVIADO.\n"+
            "\n".join(problemas)+"\nConferir relatório no GitHub Actions."})
        raise RuntimeError("multitema não enviado: "+repr(problemas))
    for titulo,video,contato in paths:
        previa_telegram._api("sendVideo",{
            "chat_id":chat,
            "caption":(f"TESTE EDITORIAL PRIVADO — {titulo}\n"
                       "Vídeo de ~15s com narração Edge de TESTE, não a voz definitiva.\n"
                       "NÃO PUBLICADO · NÃO APROVADO · AGUARDANDO SUA AVALIAÇÃO.\n"
                       "Fontes reais; imagem representativa identificada quando necessário."),
            "supports_streaming":"true"
        },("video",previa_telegram._caber(video)))
        if contato.is_file():
            previa_telegram._api("sendPhoto",{
                "chat_id":chat,
                "caption":f"QA por cena — {titulo}; quatro cenas, quatro capturas por cena."},
                ("photo",contato))
    previa_telegram._api("sendMessage",{"chat_id":chat,"text":
        "3 amostras narradas entregues: Taiwan/chips, Hubble/NASA e Hindenburg.\n"
        "Isto é um teste de generalização, NÃO uma autorização para publicar.\n"
        "Avaliar cena por cena: fonte correta, fala correspondente, ritmo, recorte, texto e progressão."})
    return {"enviados":len(paths),"destino":f"{info['tipo']} privado autorizado",
            "publicados":0,"aprovados_por_humano":0}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("saida",type=Path)
    a=p.parse_args()
    print(json.dumps(entregar(a.saida),ensure_ascii=False))
