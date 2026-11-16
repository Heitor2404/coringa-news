---
name: coringa-edicao
description: Use ao mexer em render, montagem, transições, composições JS do palco V2/V3, áudio/loudness ou operações FFmpeg do Coringa.
---
# Edição e render do Coringa

- Palco: `src/render/v2/` (nucleo.js = cenas, legenda, transições; comp/*.js = composições; doc.js = planos documentais).
  Tudo determinístico por `seek(t)` — nada de CDN, timeline própria ou `Math.random` sem semente.
- Transições: corte, dissolve, zoom, mascara, deslize, flash, preto, **whip** (deslocamento), **iris** (revelação).
  A mesma transição 4× seguidas é achado estético. Padrões HyperFrames reimplementados (atribuição em `src/render/v2/NOTICE.md`).
- Render: `src/render/render.py::renderizar` (quadros → FFmpeg, masterização −14 LUFS, pico ≤ −1 dBTP).
- Antes do MP4: prévia por quadros (`pipeline.previa_quadros`). Defeito visível em quadro não justifica render completo.
- FFmpeg ad hoc (inspeção, cortes, galerias, loudness): skill `ffmpeg-skill` (kajisho5/ffmpeg-skill, MIT) — só desenvolvimento;
  a produção não depende de Claude Code para rodar FFmpeg.
- Mudou composição/transição → regenerar referência visual só se a mudança for intencional e registrada.

Testes: `python -m pytest -q tests/test_v2.py tests/test_v3_fiscal.py`.
