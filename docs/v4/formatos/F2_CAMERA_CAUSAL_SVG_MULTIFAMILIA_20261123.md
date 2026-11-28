# ATLAS F2 — câmera causal SVG consumindo SceneGraph (23/11/2026)

**Estado:** implementação e prova técnica aprovadas; **ARTE NÃO HOMOLOGADA**. Branch experimental `atlas-direcao-visual-20261118`. Sem Claude ou IA externa, sem postagem.

## De metadado à câmera REAL

A F1 gerava `plano_causal.eventos[].camera.alvos`, mas renderizadores ignoravam esse dado. A F2 criou `src/v4/formatos/camera_causal_svg.py` que:
1. Compila a ficha de `grafo_causal.py`, verifica atores, relações, mudanças de estado e ordem física.
2. Procura **todas as bboxes de atores** em `camera_causal_geometrias.json` de cada família; sem geometria declarada, BLOQUEIA.
3. Calcula o centro comum dos atores no foco causal, interpola-o entre etapas e aplica uma única transformação SVG à cena física completa.
4. Calcula limites de pan/zoom para manter o bounding box integral da máquina na zona útil. Nunca permite scale menor que 1, elemento cortado, NaN, momento inválido ou ator não declarado.
5. Deixa textos editoriais, rodapé, física da biela, pistão e válvulas intactos. **Zoom de câmera não é ajuste de equação física.**

`src/v4/formatos/temporizacao_causal.py` trata a **velocidade de exposição do mecanismo** por limiares físicos (saída de `compressor_pv_core.limites_fases`): cada fase do compressor recebe ao menos 1,15s nos oito segundos. Distribuição exata observada: 1,5393; 2,4624; 2,3672; 1,6311s. A física não foi alterada; o relógio do vídeo evolui a diferentes velocidades conforme a fase.

## Reuso entre famílias

| Família | Base 540×960 | Zoom máximo | Atores de foco | Fonte física |
|---|---|---|---|---|
| Compressor completo com reservatório horizontal | lift 100px | 1,08× | motor, filtro, válvulas, pistão, conduto, tanque | `compressor_pv_core` |
| Otto 4 tempos | lift 28px | 1,025× | admissão/escape, pistão, ignição, volante e câmara | `reference_first` medido, revisado |

A lógica da câmera não faz `if tema == compressor` nem guarda instantes arbitrários por título. Os atores e o grafo são específicos da família (necessariamente); a política de câmera é comum.

## Evidência / limites

[Run 45106787906](https://github.com/Heitor2404/coringa-news/actions/runs/45106787906): **SUCCESS, 50 testes**, dois MP4 reais 8s 24fps 540×960 sem som; artifact privado **14787692527**, expiração 28/11/2026 03h35 UTC; contém folhas de contato, comparativos e relatórios. Hash dos vídeos:
- Compressor `c1a719ca17d41f114a76e404419e3be4d66d642d4030a8bcc806419c7c50c260`
- Otto `4a0f244bb8244e709db78e856501a9fdad3b178471f42f8c522bfd5642bbe404`

QA de pixels e verificação geométrica ≠ semântica, fidelidade de máquina, eficácia no celular ou aceitação estética. Visualmente o ganho de ocupação é modesto, especialmente no Otto, onde a largura da máquina impede zoom maior sem cortes. Não tentar fazer parecer cinematográfico à força.

**Não integrado à renderização ATLAS final**: `FilmeEditorial.tsx` antigo e seus componentes EUV/eclusa minúsculos continuam vetados como referências de arte. A F2 é aplicada a SVG Python de prova privada. O motor ainda não pesquisa e reconstrói qualquer mecanismo automaticamente. A próxima etapa deve usar o grafo como direção em um renderer novo/modernizado sob estilo benchmark sem sacrificar fidelidade e sem vídeos genéricos.
