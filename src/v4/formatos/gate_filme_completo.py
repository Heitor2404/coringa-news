"""Gate pré-voz para filmes documentais: FATO -> PROVA REAL -> MÍDIA CURADA.

Reusa ponte_biblioteca.catalogo e ponte_mapa_atlas.validar_comprovante.
Não baixa mídia, não chama TTS, não inventa licenças, não dá aprovação humana.
Valida qualquer storyboard desta estrutura; Taiwan é somente um caso de regressão.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

TIPOS = {"foto", "video", "atlas_map", "comparison", "mechanism"}
ACAO = {"MOSTRAR", "DEMONSTRAR", "LOCALIZAR", "CONECTAR", "REVELAR", "COMPARAR"}
PROIBIDAS = {"BLOQUEADO", "REPROVADO", "PENDENTE_REVISAO", "LICENSE_REVIEW_NEEDED"}


def avaliar(manifesto:dict, catalogo:dict|None=None) -> dict:
    erros:list[dict]=[]
    def falha(codigo:str, cena:str, motivo:str)->None:
        erros.append({"codigo":codigo,"cena":cena,"motivo":motivo})
    if manifesto.get("versao")!=1 or manifesto.get("formato")!="filme_editorial":
        falha("E-FORMATO","-","exige manifesto documental versão 1")
    if (manifesto.get("tipo")!="PRE_PRODUCAO_PRIVADA" or
            (manifesto.get("politica") or {}).get("publicar") is not False):
        falha("E-PUBLICACAO","-","somente preparo privado, nunca licença de publicar")
    janela=manifesto.get("janela_duracao_s") or []
    dur=manifesto.get("duracao_planejada_s")
    if not (len(janela)==2 and isinstance(dur,(int,float)) and
            all(isinstance(n,(int,float)) for n in janela) and
            janela[0]<=dur<=janela[1] and math.isfinite(dur)):
        falha("E-TEMPO","-","duração fora da janela editorial")
    regras=manifesto.get("rubrica_editorial") or {}
    if not (isinstance(regras.get("min_videos_reais_independentes"),int) and
            isinstance(regras.get("max_fracao_fotos_estaticas"),(int,float)) and
            0<=regras["max_fracao_fotos_estaticas"]<=1 and
            1<=regras.get("max_foto_individual_s",0)<=8):
        falha("E-RUBRICA","-","requisitos visuais devem ser declarados em cada episódio")
    cenas=manifesto.get("cenas") or []
    if not cenas:
        falha("E-CENAS","-","sem plano de cena")
    conhecidos={x.get("id"):x for x in (catalogo or {}).get("itens") or []}
    media_movel=set();fotos_s=0.;mapas=0;prev=0.;visto=set()
    for c in cenas:
        cid=c.get("id") or "?"
        start,end=c.get("inicio"),c.get("fim")
        if not (isinstance(start,(int,float)) and isinstance(end,(int,float))
                and math.isfinite(start) and math.isfinite(end)
                and end>start and abs(start-prev)<.06):
            falha("E-CORTE",cid,"cenas devem cobrir integralmente o vídeo sem lacunas/overlaps")
            continue
        prev=float(end);span=end-start
        if c.get("acao") not in ACAO or not isinstance(c.get("promessa"),str) or len(c["promessa"])<15:
            falha("E-FATO",cid,"cada cena precisa de intenção e aprendizado verificável")
        m=c.get("midia") or {}
        tipo=m.get("tipo")
        if tipo not in TIPOS:
            falha("E-TIPO",cid,"tipo de mídia desconhecido")
            continue
        if c.get("acao")=="DEMONSTRAR" and tipo not in ("video","mechanism"):
            falha("E-ACAO-SEM-VIDEO",cid,"não confundir foto de máquina com ação observável")
        if c.get("acao")=="LOCALIZAR" and tipo!="atlas_map":
            falha("E-MAPA-NAO-ATLAS",cid,"mapas devem sair do ATLAS original")
        if m.get("identidade") not in ("literal","representativa","explicativa"):
            falha("E-IDENTIDADE",cid,"identidade real ou ilustrativa obrigatória")
        if tipo in ("foto","video"):
            asset=m.get("asset_id")
            it=conhecidos.get(asset)
            if not asset or not it:
                falha("E-MIDIA-SEM-CURADORIA",cid,
                      f"{asset or 'SEM ASSET'}: não está no acervo comprovado V4/V3")
                continue
            if asset in visto:
                falha("E-FONTE-REPETIDA",cid,"mesma mídia não vira prova nova por zoom ou recorte")
            visto.add(asset)
            prova=it.get("prova") or {}
            sha=it.get("sha256_origem")
            if not (isinstance(sha,str) and len(sha)==64 and
                    prova.get("midia_corresponde") is True and
                    it.get("licenca") and it.get("credito")):
                falha("E-PROCEDENCIA",cid,"sem SHA/licença/crédito e revisão do objeto")
            if any(x in str(c.get("estado") or "").upper() for x in PROIBIDAS):
                falha("E-LICENCA-PENDENTE",cid,"status do arquivo impede uso")
            if tipo=="video" and it.get("natureza")!="video":
                falha("E-VIDEO-FALSO",cid,"mídia declarada vídeo não é vídeo no catálogo")
            if tipo=="foto" and it.get("natureza")=="video":
                falha("E-FOTO-FALSA",cid,"usar metadados compatíveis com a origem")
            if m.get("identidade")=="literal" and prova.get("apenas_piloto_experimental") is True:
                # Imagem real da fábrica passa em roteiro experimental;
                # uso final depende de inspeção humana separada.
                pass
            if tipo=="foto":
                fotos_s+=span
                if span>regras.get("max_foto_individual_s",3.8)+.001:
                    falha("E-FOTO-PARADA",cid,f"foto por {span:.2f}s sem acontecimento")
            else:
                if it.get("uso_comercial") not in ("sim",True):
                    falha("E-VIDEO-SEM-USO-COMERCIAL",cid,"uso comercial do original não confirmado")
                if prova.get("acao_ou_relacao_visivel") is not True:
                    falha("E-VIDEO-SEM-ACAO-COMPROVADA",cid,
                          "vídeo precisa de revisão de quadros que MOSTRE o processo narrado")
                else:
                    media_movel.add(sha)
        elif tipo=="atlas_map":
            if m.get("identidade")!="explicativa":
                falha("E-MAPA-COMO-REGISTRO",cid,"mapa nunca é prova filmada da fábrica")
            from src.v4.formatos.ponte_mapa_atlas import validar_comprovante
            problemas=validar_comprovante({
                "local_source":m.get("clipe"),"atlas_proof":m.get("prova"),
                "expected_sha256":m.get("sha256")
            })
            if problemas:
                falha("E-MAPA-SEM-COMPROVANTE",cid,"; ".join(problemas))
            else:
                mapas+=1
        else:
            # Comparações e mecanismos precisam de origem, objetivo e evidência
            # conferida no mesmo catálogo; nunca aprovar card por si só.
            assets=m.get("asset_ids") or []
            if (len(assets)<2 and tipo=="comparison") or not all(
                  a in conhecidos for a in assets):
                falha("E-FLUXO-SEM-PROVA",cid,
                      "relação/resultado visual não comprovado por duas fontes distintas")
        if c.get("acao")=="REVELAR" and not m.get("resultado_verificavel"):
            falha("E-PAYOFF-SEM-CONSEQUENCIA",cid,
                  "payoff precisa consequência verificada, não apenas slogan")
    if isinstance(dur,(int,float)) and abs(prev-dur)>.06:
        falha("E-DURACAO-CENAS","-",f"última cena termina em {prev}, duração prometida {dur}")
    if isinstance(dur,(int,float)) and dur>0 and regras.get("max_fracao_fotos_estaticas") is not None:
        ratio=fotos_s/dur
        if ratio>regras["max_fracao_fotos_estaticas"]+.001:
            falha("E-SLIDESHOW","-",f"{ratio:.1%} do filme em fotos estáticas; rever direção")
    if len(media_movel)<regras.get("min_videos_reais_independentes",0):
        falha("E-VIDEO-INSUFICIENTE","-",
              f"{len(media_movel)} vídeos reais de ação conferida; mínimo deste episódio: "
              f"{regras.get('min_videos_reais_independentes',0)}")
    if regras.get("mapa_evidencia_real_obrigatorio") and mapas<1:
        falha("E-CARTOGRAFIA-NAO-INTEGRADA","-","mapa ATLAS não está com MP4 e comprovante no mesmo runner")
    voz=manifesto.get("base_narracao") or {}
    if (voz.get("motor")!="gemini" or voz.get("voz")!="Charon"
        or voz.get("fallback")!="bloquear"):
        falha("E-VOZ-CONFIG","-","somente o preset Charon; Edge proibido")
    pronto_visual=not erros
    # A produção sonora é SEGUNDA FASE. Metadados de timestamps não são WAV.
    return {
        "status":"PRONTO_PARA_TTS" if pronto_visual else "BLOQUEADO_EDITORIAL_SEM_PROVA",
        "pronto_para_tts":pronto_visual,
        "pronto_para_render":pronto_visual and bool(voz.get("arquivo_wav")),
        "previsao_s":dur,
        "total_cenas":len(cenas),"videos_independentes_conferidos":len(media_movel),
        "mapas_atlas_comprovados":mapas,"fotos_s":round(fotos_s,3),
        "inspecao_humana":"PENDENTE","publicado":False,
        "bloqueios":erros,
    }


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("manifesto",type=Path)
    p.add_argument("saida",type=Path)
    a=p.parse_args(argv)
    from src.v4.formatos.ponte_biblioteca import catalogo
    data=json.loads(a.manifesto.read_text(encoding="utf-8"))
    r=avaliar(data,catalogo())
    a.saida.parent.mkdir(parents=True,exist_ok=True)
    a.saida.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":r["status"],"bloqueios":len(r["bloqueios"]),
                      "mapas":r["mapas_atlas_comprovados"],
                      "videos":r["videos_independentes_conferidos"],
                      "publicado":False},ensure_ascii=False))
    return 0 if r["pronto_para_tts"] else 1


if __name__=="__main__":
    raise SystemExit(main())
