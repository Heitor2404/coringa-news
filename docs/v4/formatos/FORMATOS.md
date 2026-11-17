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


## Direção de arte final (17/11) — composições, rasters e validação nos quadros

**Composições** (`formatos.json → composicoes`): cada beat escolhe uma. Ela fixa o palco, o QUADRO livre onde a câmera
enquadra o território do beat (`roi` = oeste, sul, leste, norte) e os slots das camadas. Câmera = `plano.camera_roi`
(foco + âncora em tela; pan proporcional à escala na transição; deriva lenta no beat), igual em `Palco.tsx`.

| composição | uso |
|---|---|
| atlas.protagonista | o mapa é a informação; só etiqueta curta fora do território |
| atlas.manchete | gancho/fecho: título em cima, território embaixo |
| atlas.painel | território em cima, número/perfil embaixo (ligados pelos nomes) |
| atlas.lateral | território alto + coluna de dados |
| atlas.documento | prova fotográfica grande sobre o mapa esmaecido |
| atlas.tecnica | estrutura abstrata em tela cheia |
| dossie.capa / documento / ficha / calendario / relacao | pasta; documento real + marcações na região exata; ficha com prova presa e carimbo; mês real com o dia; régua proporcional |

**Rasters** (`motor4/formatos/dados/raster/`, procedência em `ATRIBUICAO.md` e `.json`): NE2 (domínio público) no
largo; Sentinel-2 cloudless **2016** (CC BY 4.0) no canal/eclusas, coletados por `formatos-coleta.yml` (sem IA).

**Regras novas** (plano): F-COMPOSICAO, F-COBRE-TERRITORIO, F-MAPA-BAIXA-RESOLUCAO, F-RECONSTRUCAO. **No quadro
renderizado** (`python -m src.v4.formatos quadros`, `scripts/formatos_validar.py`, `motor4/remotion/medir.mjs`):
R-COLISAO, R-COBRE-TERRITORIO, R-ZONA-IDENTIDADE, R-ROTULO-COBERTO, R-TRANSBORDA, R-TEXTO-PEQUENO (≥ 26 px; crédito
≥ 18 px), R-TEXTO-CORTADO, R-CENA-VAZIA — a própria página registra a geometria real depois que o mapa e as fontes ficam
prontos. **No MP4**: ritmo medido (`ritmo.py`, mesma métrica das referências) com portão ≤ 3 s parado.

**Mídia**: a biblioteca guarda o sha256 DA ORIGEM; `ativos` confere antes de usar; o preflight confere o arquivo do
render contra o registrado (ERR-066). Reconstruções editoriais são sempre rotuladas.

### Prévia única da direção de arte — execução 44122592315 (17/11)

| | ATLAS (79,05 s) | DOSSIÊ (24,4 s) |
|---|---|---|
| Estado do motor | AGUARDANDO_APROVACAO_HUMANA | AGUARDANDO_APROVACAO_HUMANA |
| Preflight / quadros renderizados | verde / 6 quadros, 0 problemas | verde / 6 quadros, 0 problemas |
| Áudio no MP4 | −14,8 LUFS · −1,0 dBTP | −14,9 LUFS · −1,2 dBTP |
| Maior trecho parado (ritmo medido) | 2 s (antes 4 s) | 2 s (antes 4 s) |
| Segundos parados | 4/79 (antes 33/79) | 2/24 (antes 13/24) |
| Custo de IA | 0 (narrações cifradas) | 0 |

Referências: A = 2 s / 3 de 68 s parados; B = 1 s / 12 de 176 s. Antes desta, três disparos pararam antes de
renderizar (429 do Wikimedia por User-Agent fora da política, ERR-071; caminho relativo na medição e mesa cara demais,
ERR-072); nenhum gastou IA. Prévias, folhas, styleframes, leitura em celular e antes/depois foram ao Telegram privado.


## ATLAS — gramática de edição da referência (17/11, tarde)

Fonte: engenharia reversa do Heitor (`src/v4/formatos/atlas_parametros.json`, conteúdo literal) + conferência própria
da câmera por SIFT na cópia 512×910 (`atlas_camera_verificada.json`: confere a tabela do relatório e estende para o
vídeo inteiro). Só o que a cópia permite medir; nenhuma fonte, traço ou easing "original" foi inventado.

| Gramática | Implementação | Validação |
|---|---|---|
| mapa persistente desde o 1º quadro | composição `atlas.abertura` (sem cartão de foto cobrindo o mapa) | F-COMPOSICAO |
| câmera medida | `movimento`: aproxima (log2 1,0242 ≈ +0,034 zoom/s), fixo (0) quando o dado muda, recua (log2 0,9544) no fecho, terminando no enquadramento | teste de câmera; F-COBRE-TERRITORIO no fim do recuo |
| objetos ancorados | `atlas.geoPin` (lugar / foto real) projetado pela MESMA câmera do palco | F-PINO-FORA, colisão a cada 0,25 s; R-PINO-DESCOLADO (≤ 3 px do `map.project`) no quadro |
| hierarquia que acende | `editorial.hierarchy` em blocos com profundidade + salto entre níveis, composição `atlas.escada` | quadros renderizados |
| dado com contexto | `statCard` estilo `dial` (meio-círculo proporcional) | F-TEXTO-NAO-CABE do mostrador |
| planta técnica | palco `tecnico` com o território real, grade 170 px (ref. ~169 px) | ERR-073 |
| legenda | ATLAS: topo 1392 (centro ≈ 1430–1470; ref. 1496, limitada pela área segura 1480) | zona `legenda` do formato |
| créditos cartográficos | `motor4/formatos/dados/atribuicoes.json` (manifesto); o palco mostra só as camadas visíveis; faixa própria 1300–1388 | preflight: manifesto, uso comercial, proibidos (Esri/Google/Mapbox/S2 2018+), fonte factual ≠ atribuição; R-CREDITOS-TRANSBORDA |

Esri World Imagery aparece na referência, mas atribuição não é licença: não é usado. Base = Natural Earth II (largo) e
EOxCloudless 2016 (CC BY 4.0) no detalhe. Fontes factuais do ATLAS ficam em `narracao.fatos` (Linda Hall, Britannica,
UF Libraries) e nunca se misturam com os créditos do mapa. DOSSIÊ congelado (código preservado; `so-atlas` no disparo).

## ATLAS — consolidação do motor e padrão visual (17/11, noite)
Base aprovada: prévia 44155276352. Correções no MOTOR (não no episódio):
- **Áreas seguras** (`plataformas.json` + `layout.py`): perfis TikTok / Reels / Shorts (aproximações configuráveis, com fontes);
  a união decide slots, quadro do território e as faixas inferiores próprias (conteúdo → legenda → créditos). Slots das
  composições ATLAS são intenções `{y, h, w_max}` resolvidas pelo perfil.
- **Legenda** (`legenda_sync.py`): `realinhar` (pausas reais como âncoras, sem IA) no `narrar`; `conferir` no preflight e
  como portão `legenda_ok` do MP4; agrupamento com mínimo de 0,35 s idêntico em Python e `Camada.tsx`.
- **Cartões** (`Primitivas.Cartao/Fonte`, tokens `canal.cartao`): sistema único; pílula encolhe 40 → 30 px.
- **Planta técnica** (`canal.palco.tecnico` → `mecanismos.js` via `p.tema`): reutilizável por qualquer mecanismo V2.
- **Pinos**: papel protagonista/secundário (`canal.pino`), `desloc: "auto"`, escala automática ≥ 75 %, rótulo de texto com
  lado automático; F-PINO-FORA usa a área segura.
- **Gancho** (F-GANCHO), **CTA** (`inserir_cta`, só se couber), **ritmo sem câmera** (`ritmo.medir_completo`).
- **Conexões** entre pontos (`rotas[].arco`, círculo máximo) e geometria do mundo (`scripts/formatos_mundo.py`, Natural Earth
  via world-atlas já instalado) — sem dado OSM, sem nova instalação.
- **Fiscal**: amostragem ampliada, máscaras de plataforma (folhas `plataforma_*.jpg`), alinhamento/inclinação de cartões,
  legenda na faixa, atribuição obrigatória presente, pinos parte × parte; `fiscal_4camadas.md`.
- **Reuso sem render completo**: `scripts/formatos_reuso.py <plano> <saida>` (tempos e voz SINTÉTICOS → ativos → preflight
  → quadros com todas as regras). Planos em `planos/reuso/` (chips China × EUA; história 1880–1914).
