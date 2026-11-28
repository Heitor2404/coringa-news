"""Fiscal transversal de PROGRESSÃO em cenas de foto/vídeo.

Não confunde zoom/pan com novidade. Reutilização de uma origem fotográfica,
mesmo após outro crop, é a mesma evidência. NÃO atesta que uma ação foi vista.
A mesma regra vale para qualquer assunto; não contém nomes de países/temas.
"""
from __future__ import annotations

from collections import defaultdict


def verificar(shots: list[dict], media: dict,
              *, max_sem_novidade_s: float = 2.8) -> list[dict]:
    erros = []
    visto = {}
    for shot in shots:
        ident = str(shot.get("id") or "?")
        typ = shot.get("type")
        duration = float(shot.get("end",0))-float(shot.get("start",0))
        cues=shot.get("cues") or []
        # Fotos não executam a ação alegada apenas por trocar pixels.
        # Quando o último acontecimento/callout ocorre muito cedo, o resto
        # fica parado informacionalmente; panning NÃO conta como nova prova.
        if typ=="photo" and duration>max_sem_novidade_s:
            instantes=[float(q["at"]) for q in cues
                       if isinstance(q.get("at"),(float,int))]
            ultimo=max(instantes,default=0)
            tempo_morto=round(duration-ultimo,2)
            if tempo_morto>max_sem_novidade_s:
                erros.append({
                    "codigo":"F-SEM-PROGRESSAO-INFORMACIONAL",
                    "cena":ident,
                    "motivo":f"{tempo_morto}s de foto após o último marco; zoom/pan não comprova novidade",
                    "gap_s":tempo_morto,
                })
        # A identidade vem da página do original e do hash, não do ID do
        # recorte JPEG; duas imagens derivadas da mesma fonte são REPETIÇÃO.
        for field in ("asset","assetB"):
            asset_id=shot.get(field)
            if not asset_id:
                continue
            item=media.get(asset_id) or {}
            keys=[]
            page=(item.get("page") or "").strip()
            sha=(item.get("expected_sha256") or "").strip()
            if page:
                keys.append(("pagina",page))
            if len(sha)==64:
                keys.append(("hash",sha))
            key_antes=next((visto[x] for x in keys if x in visto),None)
            if key_antes and typ=="photo":
                erros.append({
                    "codigo":"F-FONTE-VISUAL-REPETIDA",
                    "cena":ident,
                    "motivo":(f"mesma fonte de {key_antes} reutilizada como novo plano; "
                              "mudança de crop/zoom não cria outra evidência"),
                    "fonte_anterior":key_antes
                })
            for key in keys:
                visto.setdefault(key,ident)
    return erros
