"""Prototipo REFERENCE FIRST: midia real -> prova de eventos -> grafo causal.

NAO faz copia pixel a pixel nem declara reconstruct 2D/3D antes de haver
renderer capaz + ativo autorizado + QA humano. Prova de Gemini e provisoria.
A mesma cinemática pistao-biela-eixo NÃO significa o mesmo processo:
compressor de ar e motor de combustao têm evidencias obrigatorias diferentes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.v4.formatos import referencia_temporal as F

PROCESSOS = {
    "compressor_alternativo": {
        "familia": "slider_crank",
        "atores": ("pistao", "biela", "virabrequim", "cilindro",
                   "valvula_admissao", "valvula_descarga"),
        "ligacoes": (("pistao", "biela"), ("biela", "virabrequim")),
        "eventos": (
            ("admissao_ar", ("pistao_desce", "valvula_admissao_abre", "ar_entra")),
            ("compressao_ar", ("pistao_sobe", "valvulas_fechadas", "volume_diminui")),
            ("descarga_ar", ("pistao_sobe", "valvula_descarga_abre", "ar_sai")),
        ),
        "nao_equivale_a": ("motor_otto_4t",),
        "capacidades_visuais": (
            "cilindro_com_volume_variavel", "valvulas_entrada_e_saida_visiveis",
            "fluxo_admissao_visivel", "fluxo_descarga_visivel",
            "ciclo_sincronizado_com_pistao"),
    },
    "motor_otto_4t": {
        "familia": "slider_crank",
        "atores": ("pistao", "biela", "virabrequim", "cilindro",
                   "valvula_admissao", "valvula_escape", "ignicao"),
        "ligacoes": (("pistao", "biela"), ("biela", "virabrequim")),
        "eventos": (
            ("admissao_mistura", ("pistao_desce", "valvula_admissao_abre", "mistura_entra")),
            ("compressao_mistura", ("pistao_sobe", "valvulas_fechadas", "volume_diminui")),
            ("ignicao_expansao", ("ignicao_acontece", "pistao_desce", "gases_expandem")),
            ("escape_gases", ("pistao_sobe", "valvula_escape_abre", "gases_saem")),
        ),
        "nao_equivale_a": ("compressor_alternativo",),
        "capacidades_visuais": (
            "quatro_tempos_dois_giros", "valvulas_admissao_e_escape",
            "mistura_entrada_visivel", "ignicao_visivel",
            "expansao_visivel", "escape_visivel"),
    },
}

# Auditoria do renderer de laboratorio EXISTENTE, não promessa de capacidade.
# Tem um rig comum e portas desenhadas, MAS não passou por demonstração
# comprovada de ar entrando/saindo nem quatro tempos com ignição.
RENDERERS_LAB_NAO_APROVADOS = {
    "CinematicCutaway3D": {
        "capacidades": frozenset(("pistao_articulado", "biela_articulada",
                                 "volante_giratorio", "dutos_simplificados")),
        "estado": "EXPERIMENTAL_NAO_RECONSTRUCAO_POR_REFERENCIA",
    },
    "CompressorPV2D": {
        # A física P-V agora representa as válvulas, o volume, entrada e saída
        # VISUALMENTE, mas NÃO foi reconstruída a partir de referência
        # animada de compressor. Continua BLOQUEADA para uso automático.
        "capacidades": frozenset((
            "cilindro_com_volume_variavel",
            "valvulas_entrada_e_saida_visiveis",
            "fluxo_admissao_visivel",
            "fluxo_descarga_visivel",
            "ciclo_sincronizado_com_pistao",
        )),
        "estado": "PROVA_FISICA_NAO_RECONSTRUCAO_POR_REFERENCIA",
    },
    "CompressorConjunto2D": {
        # Conjunto completo (motor elétrico, correia, bomba e tanque).
        # Exibe estados P-V, mas a identidade ainda depende de
        # configuração declarada; não há IA visual independente.
        "capacidades": frozenset((
            "cilindro_com_volume_variavel",
            "valvulas_entrada_e_saida_visiveis",
            "fluxo_admissao_visivel",
            "fluxo_descarga_visivel",
            "ciclo_sincronizado_com_pistao",
        )),
        "estado": "PROVA_2D_CONJUNTO_COMPLETO_NAO_RECONSTRUCAO_AUTOMATICA",
    },
}


def verificar_renderizador(processo: str, renderer: str, *,
                          capacidades_override=None) -> dict:
    """Bloqueia o uso do slider-crank generico como compressor ou motor."""
    if processo not in PROCESSOS:
        return {"aprovado": False, "faltantes": [],
                "bloqueios": ["F-PROCESSO-DESCONHECIDO"]}
    known = RENDERERS_LAB_NAO_APROVADOS.get(renderer)
    if known is None and capacidades_override is None:
        return {"aprovado": False, "faltantes": list(PROCESSOS[processo]["capacidades_visuais"]),
                "bloqueios": ["F-RENDERER-NAO-CADASTRADO"]}
    advertised = set(capacidades_override if capacidades_override is not None
                     else known["capacidades"])
    required = set(PROCESSOS[processo]["capacidades_visuais"])
    missing = sorted(required - advertised)
    return {"aprovado": False,
            "faltantes": missing,
            "bloqueios": (["F-RENDERER-NAO-DEMONSTRA-PROCESSO"] if missing
                          else ["F-RENDERER-EXPERIMENTAL_NAO_APROVADO"] if known
                          else ["F-RENDERER-NAO-AUDITADO"])}


def prancha_temporal(imagens: list[bytes]) -> bytes:
    """Compacta 10-20 frames visuais em UMA imagem numerada para VLM.

    O modelo recebe a sequência inteira mas somente uma chamada de mídia;
    se perder sinais de válvula, o contrato de processo BLOQUEIA.
    """
    import io
    from PIL import Image, ImageDraw
    if not 10 <= len(imagens) <= 20:
        raise ValueError("F-PRANCHA-FRAMES")
    cols = 3
    rows = (len(imagens) + cols - 1) // cols
    tw, th = 310, 422
    out = Image.new("RGB", (cols * tw, rows * th), "#EEF6FA")
    draw = ImageDraw.Draw(out)
    for i, raw in enumerate(imagens):
        with Image.open(io.BytesIO(raw)) as src:
            img = src.convert("RGB")
            img.thumbnail((tw - 16, th - 42), Image.Resampling.LANCZOS)
        x, y = (i % cols) * tw + 8, (i // cols) * th + 34
        out.paste(img, (x + (tw - 16 - img.width) // 2, y))
        draw.text((x + 9, y - 25), f"QUADRO {i:02d}", fill="#103950")
    b = io.BytesIO()
    out.save(b, "JPEG", quality=90)
    return b.getvalue()


def prompt_visao(processo: str, frames: int) -> str:
    if processo not in PROCESSOS:
        raise ValueError("F-PROCESSO-DESCONHECIDO")
    spec = PROCESSOS[processo]
    return (
        f"Voce recebe UMA PRANCHA com {frames} quadros CRONOLOGICOS numerados QUADRO 00.. em linhas de 3. "
        f"Objetivo: verificar SE ela mostra '{processo}'. "
        "Nao infira processos pelo titulo, texto, wikipedia ou conhecimento previo. "
        "Compressor RECIPROCANTE nao é motor de combustao: compressor tem "
        "admissao de AR, compressao com valvulas fechadas e descarga "
        "por valvula de saida. Motor Otto 4T tem admissao, compressao, "
        "IGNICAO com expansao e escape em DOIS giros. "
        "Pistao subindo/descendo e volante girando SOZINHOS nao provam nenhum dos dois. "
        "Apenas declare valvula/fluxo/ignicao se estiver VISIVEL nos quadros. "
        "Quando eventos se passam entre os frames e nao podem ser vistos "
        "em estados antes/depois, responda eventos=[] e processo='indeterminado'. "
        "Indices 0..N-1 correspondem a ordem das imagens; NAO cite instantes inventados. "
        "Retorne APENAS JSON estrito com {processo: compressor_alternativo|"
        "motor_otto_4t|slider_crank_generico|indeterminado, "
        "atores: [...], ligacoes:[{a:'pistao',b:'biela'}, ...], "
        "eventos:[{tipo:'...',antes:0,depois:1, "
        "sinais:['...'],visivel:true,descricao:'mudanca VISUAL CONCRETA'}],"
        " problemas:[...]}. "
        f" Atores candidatos, NAO obrigatorios: {json.dumps(spec['atores'], ensure_ascii=False)}."
        f" Eventos e sinais exigidos: {json.dumps(spec['eventos'], ensure_ascii=False)}."
        " NUNCA invente sinais para completar essa lista."
    )


def _check_events(obs: dict, spec: dict, frames: list[dict]) -> tuple[list[dict], list[str]]:
    rejected = []
    events = obs.get("eventos")
    if not isinstance(events, list):
        return [], ["F-EVENTOS-NAO-LISTA"]
    required = spec["eventos"]
    if len(events) != len(required):
        return [], ["F-ETAPAS-NAO-MOSTRADAS"]
    approved = []
    prev_end = -1
    for pos, ((name, required_signals), event) in enumerate(zip(required, events)):
        if not isinstance(event, dict) or event.get("tipo") != name:
            rejected.append("F-EVENTO-ORDEM-OU-TIPO")
            break
        before, after = event.get("antes"), event.get("depois")
        if (not isinstance(before, int) or isinstance(before, bool)
                or not isinstance(after, int) or isinstance(after, bool)
                or before < prev_end or not 0 <= before < after < len(frames)):
            rejected.append("F-ETAPA-SEM-PAR-TEMPORAL-VALIDO")
            break
        signs = event.get("sinais")
        desc = event.get("descricao")
        if (event.get("visivel") is not True or not isinstance(signs, list)
                or set(required_signals) - set(str(x) for x in signs)
                or not isinstance(desc, str) or len(desc.strip()) < 30):
            rejected.append("F-EVENTO-SEM-SINAIS-CONCRETOS")
            break
        if frames[before]["sha256"] == frames[after]["sha256"]:
            rejected.append("F-QUADROS-IDENTICOS-NA-ETAPA")
            break
        approved.append({
            "tipo": name,
            "antes": before, "depois": after,
            "sinais": list(required_signals),
            "descricao_observada": desc.strip()[:350],
            "sha_antes": frames[before]["sha256"],
            "sha_depois": frames[after]["sha256"],
            "tempo_antes_s": frames[before]["segundo"],
            "tempo_depois_s": frames[after]["segundo"],
            "confiabilidade": "MODELO_NAO_REVISADO",
        })
        prev_end = after
    return (approved if not rejected else []), rejected


def analisar(manifest: dict, resposta_visao: object, processo: str) -> dict:
    """Contrato SEMÂNTICO; sem dar a um JSON da IA status de verdade factual."""
    if processo not in PROCESSOS:
        raise ValueError("F-PROCESSO-DESCONHECIDO")
    result = {
        "schema": "reference-first-scene-ir-v1",
        "processo_requerido": processo,
        "referencia_id": manifest.get("referencia_id"),
        "origem_sha256": manifest.get("arquivo_sha256"),
        "estado": "BLOQUEADO",
        "publicar": False, "renderer": None,
        "validacao_visual_humana": "PENDENTE",
        "validacao_fisica": "PENDENTE", "licenca_para_reutilizacao": "PENDENTE",
        "grafo": None, "bloqueios": [],
    }
    if (manifest.get("schema") != "reference-first-temporal-v1"
            or not isinstance(manifest.get("amostras"), list)
            or len(manifest["amostras"]) < 10):
        result["bloqueios"] = ["F-REFERENCIA-TEMPORAL-NAO-VERIFICADA"]
        return result
    if not isinstance(resposta_visao, dict):
        result["bloqueios"] = ["F-VISAO-SEM-RESPOSTA-ESTRUTURADA"]
        return result
    observed_process = resposta_visao.get("processo")
    if observed_process != processo:
        result["bloqueios"] = ["F-OUTRO-PROCESSO-OU-INDETERMINADO"]
        result["processo_observado_pelo_modelo"] = observed_process
        return result
    spec = PROCESSOS[processo]
    actors = resposta_visao.get("atores")
    if not isinstance(actors, list) or not set(spec["atores"]).issubset(
            set(x for x in actors if isinstance(x, str))):
        result["bloqueios"] = ["F-ATORES-FUNCIONAIS-NAO-VISTOS"]
        return result
    edges = resposta_visao.get("ligacoes")
    if not isinstance(edges, list) or any(not isinstance(e, dict) for e in edges):
        result["bloqueios"] = ["F-CONEXOES-NAO-VERIFICADAS"]
        return result
    got = {frozenset((e.get("a"), e.get("b"))) for e in edges
           if isinstance(e.get("a"), str) and isinstance(e.get("b"), str)}
    needed = {frozenset(pair) for pair in spec["ligacoes"]}
    if not needed.issubset(got):
        result["bloqueios"] = ["F-JUNTAS-PINOS-NAO-OBSERVADAS"]
        return result
    events, errors = _check_events(resposta_visao, spec, manifest["amostras"])
    if errors:
        result["bloqueios"] = errors
        return result
    # Fonte e modelo podem descrever partes de um evento sem fornecer
    # geometria/pose/rigging. IR nao finge que recuperou meshes ou poses 3D.
    result["grafo"] = {
        "familia_fisica": spec["familia"],
        "tipo_processo": processo,
        "atores": list(spec["atores"]),
        "relacoes": [{"a": a, "b": b, "tipo": "articulacao"}
                     for a, b in spec["ligacoes"]],
        "eventos_com_prova": events,
        "restricoes_de_render": list(spec["capacidades_visuais"]),
        "malhas_3d_recuperadas": False,
        "rig_2d_recuperado": False,
        "observacao": "HIPOTESE_DO_MODELO_NAO_CERTIFICADA",
    }
    result["estado"] = "GRAFO_PROVISORIO_SEM_RENDER"
    result["bloqueios"] = [
        "F-VLM-NAO-E-VERIFICACAO-INDEPENDENTE",
        "F-RENDERER-RECONSTRUTIVO-AINDA-NAO-IMPLEMENTADO",
        "F-REVISAO-LICENCA-E-QUALIDADE-PENDENTES",
    ]
    return result


def executar(pasta_quadros: Path, processo: str, destino: Path,
             *, chamar_visao=None, usar_gemini: bool = False) -> dict:
    try:
        manifest, images = F.carregar(pasta_quadros)
    except Exception as exc:
        output = {"estado": "BLOQUEADO", "processo_requerido": processo,
                  "renderer": None, "publicar": False,
                  "bloqueios": ["F-ARQUIVO-SEM-QUADROS-REAIS: " + str(exc)[:150]]}
    else:
        # Default e OFF, mesmo quando secrets estiverem presentes.
        # Sem autorizacao de uso, Gemini NAO sera chamado.
        if chamar_visao is None and usar_gemini:
            if not (os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2")):
                answer = None
            else:
                from src.gemini import json_visao
                try:
                    compacta = prancha_temporal(images)
                    answer = json_visao(
                        prompt_visao(processo, len(images)),
                        [compacta], leve=True)
                except Exception:
                    answer = None
        elif chamar_visao is None:
            answer = None
        else:
            try:
                answer = chamar_visao(prompt_visao(processo, len(images)),
                                     [prancha_temporal(images)])
            except Exception:
                answer = None
        output = analisar(manifest, answer, processo)
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "scene_ir.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf8")
    return output


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="REFERENCE-FIRST privado, sem Claude")
    sub = p.add_subparsers(dest="cmd", required=True)
    sample = sub.add_parser("amostrar")
    sample.add_argument("arquivo")
    sample.add_argument("saida")
    sample.add_argument("--referencia-id", required=True)
    sample.add_argument("--pagina")
    sample.add_argument("--licenca-declarada")
    inspect = sub.add_parser("inspecionar")
    inspect.add_argument("quadros_dir")
    inspect.add_argument("processo", choices=list(PROCESSOS))
    inspect.add_argument("saida")
    inspect.add_argument("--usar-gemini", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "amostrar":
        result = F.amostrar(Path(a.arquivo), Path(a.saida), a.referencia_id,
                            pagina=a.pagina, licenca_declarada=a.licenca_declarada)
        print(json.dumps({"estado": result["estado"], "frames": len(result["amostras"]),
                          "movimento": result["intervalos_em_movimento"]}))
        return 0
    result = executar(Path(a.quadros_dir), a.processo, Path(a.saida),
                      usar_gemini=a.usar_gemini)
    print(json.dumps({"estado": result["estado"],
                      "bloqueios": result["bloqueios"]}, ensure_ascii=False))
    return 1  # NENHUM renderer novo / publicacao sera autorizado por esta CLI.


if __name__ == "__main__":
    raise SystemExit(main())
