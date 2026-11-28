# ATLAS F3 — realce físico de relações, sem câmera móvel

**23/11/2026, laboratório experimental, sem Claude e sem publicação.**

## O que realmente muda

A F2B corrigiu a câmera que flutuava ao trocar de fase. O SceneGraph continuava sabendo quais atores precisavam ser mostrados, mas o renderizador apenas movia os mecanismos existentes. A F3 transforma uma parcela dessa informação em **ênfase visual** diretamente sobre peças e trajetos físicos reconhecidos, **sem mover o enquadramento** e sem novos cards.

O operador genérico `realce_causal_svg.renderizar(familia,acao,fracao,dinamicos,fisica_confirma)` depende de:
1. evento e relação exatos no `grafo_causal`;
2. atores com bboxes já fornecidas pela família;
3. trajeto físico vetorial cadastrado em `realce_causal_trajetos.json`, ou contorno móvel fornecido pelo renderer;
4. comprovação de abertura da válvula no simulador quando há fluxo.

Sem uma dessas provas, **bloqueia** em vez de inventar seta, canal ou relação.

## Teste comparativo de duas famílias

| Família | Estados com destaque | Como aparece | Movimento de câmera |
|---|---|---|---|
| Compressor de oficina (motor, correia, bomba, tanque) | Reexpansão, admissão, compressão, descarga | contorno do pistão e fino traçado ciano/laranja seguindo entrada/descarga | **Nenhum** |
| Motor Otto 4 tempos | admissão, compressão, escape | trajetos no duto e contorno móvel do pistão | **Nenhum** |

O Otto não duplica a faísca existente na ignição; a capacidade sem geometria adicional retorna sem overlay, sem fallback decorativo.

Todos os realces estão atrás de uma flag isolada `--realce-causal` (default desligado). O motor continua 2D curado, e o SceneGraph **não** sabe reconstruir peças por texto livre ou referência externa.

## Evidência e avaliação

[GitHub Actions 45109206250](https://github.com/Heitor2404/coringa-news/actions/runs/45109206250): SUCCESS, **51 testes**, dois MP4s privados 8s 24fps 540×960, sem áudio. Artifact **14787784904**, até **28/11/2026 04:01 UTC**, com `QUADROS_8_FASES_ANTES_DEPOIS.jpg`, relatórios e vídeos.

Visão humana: linhas de entrada/descarga do compressor ficam mais perceptíveis na comparação aproximada, e a câmera permanece travada. Ainda é uma melhoria **discreta**, não linguagem gráfica universal, não foi aprovado para postagem e não há comprovação automática de compreensão/estética.

**Próximo:** terceira família física em estilo plenamente compatível com a referência do compressor completo, usando o mesmo operador de causalidade. Não recuperar o visual de esquema minúsculo já rejeitado.
