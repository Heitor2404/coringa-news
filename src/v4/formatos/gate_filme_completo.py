"""Gate pré-voz para filmes documentais: FATO -> PROVA REAL -> MÍDIA CURADA.

Reusa ponte_biblioteca.catalogo e ponte_mapa_atlas.validar_comprovante.
Não baixa mídia, não chama TTS, não inventa licenças, não dá aprovação humana.
Valida qualquer storyboard desta estrutura; Taiwan é somente um caso de regressão.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

TIPOS = {"foto", "video", "atlas_map", "comparison", "mechanism"}
ACAO = {"MOSTRAR", "DEMONSTRAR", "LOCALIZAR", "CONECTAR", "REVELAR", "COMPARAR"}
PROIBIDAS = {"BLOQUEADO", "REPROVADO", "PENDENTE_REVISAO", "LICENSE_REVIEW_NEEDED"}


def avaliar(manifesto:dict, catalogo:dict|None=None, *, conferir_bytes:bool=True) -> dict:
    erros:list[dict]=[]
    def falha(codigo:str, cena:str, motivo:str)->None:
        erros.append({"codigo":codigo,"cena":cena,"motivo":motivo})
    if manifesto.get("versao")!=1 or manifesto.get("formato")!="filme_editorial":
        falha("E-FORMATO","-","exige manifesto documental versão 1")
    if (manifesto.get("tipo")!="PRE_PRODUCAO_PRIVADA" or
            (manifesto.get("politica") or {}).get("publicar") is not False):
        falha("E-PUBLICACAO","-","somente preparo privado, nunca licença de publicar")
    dur=manifesto.get("duracao_planejada_s")
    politica_duracao=manifesto.get("politica_duracao") or {}
    if not isinstance(politica_duracao,dict):
        falha("E-POLITICA-DURACAO","-","política de duração precisa ser um objeto")
        politica_duracao={}
    # Contratos novos usam o padrão narrativo global. A janela fixa só
    # permanece em contratos antigos que DECLARAM janela_duracao_s, para
    # preservar testes legados sem contaminar os próximos episódios.
    modo_duracao=politica_duracao.get(
        "modo", "janela_legada" if "janela_duracao_s" in manifesto else "narrativa"
    )
    dur_valida=(isinstance(dur,(int,float)) and not isinstance(dur,bool)
                and math.isfinite(dur) and dur>0)
    if modo_duracao=="narrativa":
        # Sem teto de duração global; cenas e narração real precisam cobrir
        # a história inteira. Metas comerciais pertencem à distribuição.
        if not dur_valida:
            falha("E-TEMPO","-","duração narrativa inválida")
    elif modo_duracao=="janela_legada":
        # Compatibilidade dos pilotos antigos, não política dos filmes novos.
        janela=manifesto.get("janela_duracao_s") or []
        if not (dur_valida and len(janela)==2 and
                all(isinstance(n,(int,float)) and not isinstance(n,bool) and math.isfinite(n)
                    for n in janela) and janela[0]<=dur<=janela[1]):
            falha("E-TEMPO","-","duração fora da janela editorial legada")
    else:
        falha("E-POLITICA-DURACAO","-","modo de duração desconhecido")
    from src.v4.formatos.tempo_natural import avaliar_destinos
    diagnostico_duracao=(avaliar_destinos(dur) if dur_valida else None)
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

    def verificar_bytes(item: dict) -> tuple[bool, str]:
        """Verificação obrigatória nos fluxos reais, contra SHA declarado no catálogo."""
        rel=item.get("arquivo_local") or item.get("local_source")
        sha=item.get("sha256_origem")
        if not isinstance(rel,str) or not rel:
            return False, "arquivo original ainda não foi recuperado no runner"
        p=Path(rel)
        if p.is_absolute() or ".." in p.parts:
            return False, "caminho da mídia deve ser relativo ao diretório de trabalho"
        raiz=Path.cwd().resolve()
        arquivo=(raiz/p).resolve()
        if not arquivo.is_relative_to(raiz) or not arquivo.is_file():
            return False, "arquivo original não existe ou saiu do workspace"
        if not isinstance(sha,str) or len(sha)!=64:
            return False, "hash SHA-256 do catálogo inválido"
        h=hashlib.sha256()
        with arquivo.open("rb") as fd:
            for bloco in iter(lambda:fd.read(1024*1024), b""):
                h.update(bloco)
        if h.hexdigest()!=sha:
            return False, "bytes reais diferem do SHA-256 curado"
        return True, ""

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
        # REGISTRO e REPRESENTACAO usam o mesmo acervo; nunca o mesmo valor de prova.
        # Requer contrato explícito apenas quando uma ação é DEMONSTRADA
        # por mídia de outro laboratório/local/evento.
        substituicao = m.get("substituicao")
        if c.get("acao") == "DEMONSTRAR" and m.get("identidade") == "representativa":
            if not isinstance(substituicao,dict):
                falha("E-REPRESENTACAO-SEM-CONTRATO",cid,
                      "demonstração ilustrativa exige processo, origem, compatibilidade e inspeção")
            else:
                from src.v4.formatos.qa_video_fontes import decidir_uso
                uso = decidir_uso(
                    acontecimento=str(substituicao.get("acontecimento") or ""),
                    evento_da_midia=str(substituicao.get("evento_da_midia") or ""),
                    uso=str(substituicao.get("uso") or ""),
                    cena_especifica=substituicao.get("cena_especifica") is not False,
                    rotulo=str(substituicao.get("rotulo") or ""),
                    origem_verificada=substituicao.get("origem_verificada") is True,
                    licenca_verificada=substituicao.get("licenca_verificada") is True,
                    representacao=substituicao.get("representacao"),
                )
                if not uso["permitido"] or uso.get("categoria")!="ILUSTRACAO_TECNICA":
                    falha("E-REPRESENTACAO-NAO-EQUIVALENTE",cid,
                          "processo ilustrativo não comprovado: "+uso["codigo"])
        elif substituicao is not None and m.get("identidade") == "literal":
            falha("E-REGISTRO-CONTRADITORIO",cid,
                  "mídia literal não aceita substituição de outra origem")
        if c.get("acao")=="REVELAR" and not m.get("resultado_verificavel"):
            falha("E-PAYOFF-SEM-CONSEQUENCIA",cid,
                  "payoff precisa consequência verificada, não apenas slogan")
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
            bytes_ok, causa = verificar_bytes(it) if conferir_bytes else (True, "")
            if not bytes_ok:
                falha("E-BYTES-NAO-COMPROVADOS",cid,causa)
            prova=it.get("prova") or {}
            if (c.get("acao")=="DEMONSTRAR" and m.get("identidade")=="representativa"
                    and isinstance(substituicao,dict)):
                rep = substituicao.get("representacao") or {}
                processo = str(rep.get("processo_midia") or "").strip().casefold()
                provado = str(prova.get("processo_verificado") or "").strip().casefold()
                if not processo or not provado or provado != processo:
                    falha("E-PROCESSO-SEM-INSPECAO-NO-ACERVO",cid,
                          "declaração do roteiro não substitui inspeção do processo no catálogo curado")
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
                elif bytes_ok:
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
            if (len(set(assets))<2 and tipo=="comparison") or not all(
                  a in conhecidos for a in assets):
                falha("E-FLUXO-SEM-PROVA",cid,
                      "relação/resultado visual não comprovado por duas fontes distintas")
            if not m.get("fonte_factual") or not m.get("relacao_visualmente_verificada"):
                falha("E-RELACAO-NAO-DEMONSTRADA",cid,
                      "múltiplas imagens e títulos não provam relação causal, exige fonte e inspeção visual")
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
    # Um nome de arquivo não basta, exigir o WAV REAL e seu SHA declarado.
    wav=voz.get("arquivo_wav")
    audio_autenticado=False
    if pronto_visual and isinstance(wav,str) and wav and not Path(wav).is_absolute() and ".." not in Path(wav).parts:
        fonte=Path(wav)
        if fonte.is_file() and isinstance(voz.get("sha256_wav"),str) and len(voz["sha256_wav"])==64:
            h=hashlib.sha256()
            with fonte.open("rb") as f:
                for chunk in iter(lambda:f.read(65536),b""):
                    h.update(chunk)
            audio_autenticado=h.hexdigest()==voz["sha256_wav"] and bool(voz.get("texto_sha256"))
    # Mesmo contrato que bloqueia o filme vira livro-caixa de acontecimentos:
    # uma linha por cena, sem gerar outra definição de storyboard ou inventar
    # inspeção visual. Um quadro sem bloqueio técnico AINDA requer revisão.
    bloqueios_por_cena={}
    for erro in erros:
        bloqueios_por_cena.setdefault(erro["cena"], []).append(erro["codigo"])
    cobertura_acontecimentos=[
        {"id":c.get("id") or "?", "acao":c.get("acao"),
         "tipo_visual":(c.get("midia") or {}).get("tipo"),
         "bloqueios":bloqueios_por_cena.get(c.get("id") or "?", []),
         "status_tecnico":(
             "BLOQUEADO" if bloqueios_por_cena.get(c.get("id") or "?") else
             "SEM_BLOQUEIO_LOCAL_REVISAO_HUMANA_PENDENTE"
         )}
        for c in cenas
    ]
    return {
        "cobertura_acontecimentos":cobertura_acontecimentos,
        "cenas_com_bloqueios_locais":sum(x["status_tecnico"]=="BLOQUEADO" for x in cobertura_acontecimentos),
        "bloqueios_globais":bloqueios_por_cena.get("-", []),
        "status":"PRONTO_PARA_TTS" if pronto_visual else "BLOQUEADO_EDITORIAL_SEM_PROVA",
        "pronto_para_tts":pronto_visual,
        "pronto_para_render":pronto_visual and audio_autenticado,
        "previsao_s":dur,
        "modo_duracao":modo_duracao,
        "diagnostico_plataformas":diagnostico_duracao,
        "total_cenas":len(cenas),"videos_independentes_conferidos":len(media_movel),
        "mapas_atlas_comprovados":mapas,"fotos_s":round(fotos_s,3),
        "inspecao_humana":"PENDENTE","publicado":False,
        "bloqueios":erros,
    }


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("manifesto",type=Path)
    p.add_argument("saida",type=Path)
    p.add_argument("--catalogo",type=Path,default=None,
                   help="overlay efêmero do catálogo com arquivos locais já atestados")
    a=p.parse_args(argv)
    from src.v4.formatos.ponte_biblioteca import catalogo
    data=json.loads(a.manifesto.read_text(encoding="utf-8"))
    curado=(json.loads(a.catalogo.read_text(encoding="utf8"))
            if a.catalogo is not None else catalogo())
    r=avaliar(data,curado)
    a.saida.parent.mkdir(parents=True,exist_ok=True)
    a.saida.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":r["status"],"bloqueios":len(r["bloqueios"]),
                      "mapas":r["mapas_atlas_comprovados"],
                      "videos":r["videos_independentes_conferidos"],
                      "publicado":False},ensure_ascii=False))
    return 0 if r["pronto_para_tts"] else 1


if __name__=="__main__":
    raise SystemExit(main())
