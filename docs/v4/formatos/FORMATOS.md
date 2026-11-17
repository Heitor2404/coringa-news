# Formatos padronizados — ATLAS e DOSSIÊ

Fábrica de vídeos editoriais: **dois formatos aprovados**, uma identidade por canal (configuração, não fork) e uma
biblioteca curta de primitivas com posições fixas. O diretor preenche composições; não inventa estilo. Referências e
medidas: `ENGENHARIA_REVERSA_REFERENCIAS.md`.

## Arquitetura (reaproveita o V4)

```
plano (beats → camadas em slots, tempos ancorados na fala)        src/v4/formatos/planos/*.json
  └─ validar (sem IA): slots, colisão (camadas e zonas da marca/legenda), texto que cabe, progressão ≤ 4 s,
     mídia duplicada/repetida, modalidades, rota com geometria                 src/v4/formatos/plano.py
narrar → ativos (biblioteca comprovada) → PREFLIGHT 100 % → render                src/v4/formatos/produzir.py
  render: Remotion `Formato` (palco persistente + primitivas)  motor4/remotion/src/formatos/
          + clipe aprovado do palco V2 (mecanismo.eclusa, modo V4) em furo com corte limpo
          + camada global (marca + legenda por palavra)  Camada.tsx
          + som (voz, trilha com sidechain, master −14 LUFS, pico corrigido no MP4)  som.py / compositor.py
  portões no MP4 final: janela de 4 s preta/congelada (zona de conteúdo), áudio −14 ±1 LUFS e pico ≤ −1 dBTP
diretor de formato (IA, opcional): preenche o esquema, valida, UMA correção     src/v4/formatos/diretor.py
CLI: python -m src.v4.formatos {validar|narrar|ativos|preflight|render|telegram} <plano> <saida>
Quadros de layout sem MP4: scripts/formatos_quadros.py
```

Identidade: `src/v4/formatos/canais/coringa.json` (cores, fontes, tempos de entrada/saída, cores do palco). Outro canal =
outro arquivo. Slots e zonas: `src/v4/formatos/formatos.json` (marca y 282–334 e legenda 1240–1455 ficam livres).

## Primitivas (12) — implementado × validado

| Primitiva | Onde | Testes (sem IA) | Usada nos pilotos | Estado |
|---|---|---|---|---|
| atlas.mapStage | `Palco.tsx` PalcoMapa (MapLibre + Natural Earth, graticulado, atribuição) | quadros locais | ATLAS | implementado; render integrado pendente |
| atlas.highlightRegion | `destaques` (país/lago, entra/sai) | quadros locais | ATLAS | idem |
| atlas.routeAndLocator | `rotas` (geometria OSM medida) + `rotulos` com área segura/colisão | geometria versionada; quadros | ATLAS | sem barra de escala nem globo localizador |
| editorial.statCard | cartão / pílula, contagem real | texto que cabe | ATLAS, DOSSIÊ | idem |
| editorial.peopleCard | retrato em círculo + nome | tipagem | — | **não exercitado** (sem retrato licenciado na biblioteca) |
| editorial.hierarchy | escada ou perfil (alturas), níveis acendem | texto que cabe | ATLAS | idem |
| editorial.timeline | marcos na ordem da fala, dentro da caixa | quadros | DOSSIÊ | idem |
| dossie.documentCard | documento/registro com cabeçalho, data, crédito; zoom só ≥ 1,5× | crédito visível no preflight | ATLAS, DOSSIÊ | zoom não exercitado |
| dossie.evidenceHighlight | carimbo / sublinhado / círculo mirado na parte do documento | geometria espelhada em Python | DOSSIÊ | sublinhado não exercitado |
| editorial.comparison | barras com unidade comum | tipagem | — | **não exercitado** |
| editorial.flowConnections | nós e setas com fluxo | texto que cabe | ATLAS | idem |
| editorial.titleOrPayoff | ≤ 3 linhas, palavra a palavra | texto que cabe, máx. linhas | ATLAS, DOSSIÊ | idem |

## Pilotos desta rodada

- **ATLAS** `atlas_panama.json` (79 s): narração e fatos da execução 44049021691 (cifrada), mapa como palco com rota
  real, 26 m, perfil 3+3 degraus, mecanismo da eclusa (clipe aprovado), mapa técnico para o caminho da água, volume e
  tempo, água doce até o mar, retorno ao mapa inicial. Piloto **supervisionado** (fixa o padrão).
- **DOSSIÊ** `dossie_panama_demo.json` (≈ 23 s): texto escrito só com f9, f10 e a procedência das fotos; uma chamada de TTS.

## Limitações conhecidas

- O cálculo de colisão é geométrico sobre caixas fixas (componentes desenham dentro delas); não há leitura do DOM do
  Remotion após o render. A verificação visual é por quadros parados e pela folha do MP4.
- Limite de progressão (4 s) é alarme de trabalho; as referências ficam em 1–2 s. Calibrar só com o seu veredito.
- ATLAS sem imagem de satélite (sem tiles de terceiros): estilo próprio com Natural Earth/OSM.

## Execução integrada 44084129999 (17/11) — prévias privadas no Telegram

| | ATLAS (79,0 s) | DOSSIÊ (24,4 s) |
|---|---|---|
| Estado do motor | AGUARDANDO_APROVACAO_HUMANA | BLOQUEADO (janela 12–16 s sem mudança) |
| Áudio no MP4 | −14,8 LUFS · −1,1 dBTP | −14,9 LUFS · −1,2 dBTP |
| Janelas pretas/congeladas | 0 | 1 |
| Custo de IA | 0 (narração cifrada reutilizada) | 1 chamada de TTS (cota grátis) |
| Defeito encontrado depois | **mídia trocada** em 0–6 s e 55–59 s (ERR-066) | — |

Corrigido sem nova execução: ERR-066 (nome próprio + impressão digital por mídia) e ERR-067 (progressão ≤ 3 s; planos
ajustados com a narração real). A narração do DOSSIÊ ficou cifrada no repositório: uma nova execução custa 0 chamada de IA.
Primeira execução (44083616015) parou antes de renderizar: segredo ausente no passo de narração (ERR-065).
