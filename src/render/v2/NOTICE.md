# Avisos de terceiros — sistema visual V2

- **MapLibre GL JS** 5.x — BSD-3-Clause — https://github.com/maplibre/maplibre-gl-js (carregado de node_modules)
- **Natural Earth** v5.1.2 — domínio público — https://www.naturalearthdata.com (camadas baixadas por
  scripts/v2_natural_earth.py; atribuição exibida nos mapas: "Natural Earth · MapLibre")
- **D3** 7.x — ISC — https://d3js.org
- **Source Serif 4**, **Montserrat**, **JetBrains Mono** (@fontsource) — SIL Open Font License 1.1
- **Manim Community** (opcional, src/v2/manim_cenas.py) — MIT — https://www.manim.community

As composições em src/render/v2/comp são código próprio do Coringa Explica (não copiam componentes de terceiros).

## Padrões do catálogo HyperFrames reescritos em `comp/doc.js` (V3)

HyperFrames (HeyGen), Apache-2.0, https://github.com/heygen-com/hyperframes, commit `478313ba0e674d51c3b307afa862de8dd87afcf9`
(16/11/2026). Nenhum arquivo foi copiado: as ideias abaixo foram reimplementadas para o tempo do palco V2 (seek
determinístico, sem CDN, sem CSS global, sem timeline própria do componente).

| Componente de origem | Uso no Coringa |
|---|---|
| `hw-callout-circle` | círculo desenhado à mão em dois traços (`doc.plano`, anotação `circulo`) |
| `yt-feather-highlight` | foco com máscara esfumada (`doc.plano`, anotação `foco`) |
| `grain-overlay` | granulação de tratamento (ruído fixo deslocado por quadro, determinístico) |
| `vignette` | vinheta radial de tratamento |

## V3.1 — transições reescritas em `nucleo.js`

HyperFrames commit `8e8eeb2` (16/11/2026), Apache-2.0. Ideia reimplementada, nenhum arquivo copiado:

| Componente de origem | Uso no Coringa |
|---|---|
| `whip-pan-cut` | transição `whip`: a cena que sai e a que entra deslizam juntas, com desfoque de movimento no meio (deslocamento geográfico/temporal) |
| `iris-reveal` | transição `iris`: revelação circular a partir do centro de interesse (revelação final) |
| `before-after-wipe` | não portado: `comparacao.antes_depois` (fotos.js) já faz a varredura com divisória |
