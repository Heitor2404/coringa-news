---
name: coringa-edicao
description: Use ao mexer em render, montagem, transições, composições JS do palco V2/V3, áudio/loudness ou operações FFmpeg do Coringa.
---
# Edição e render do Coringa

- Palco: `src/render/v2/` (nucleo.js = cenas, legenda, transições; comp/*.js = composições; doc.js = planos documentais).
  Tudo determinístico por `seek(t)` — nada de CDN, timeline própria ou `Math.random` sem semente.
- Transições: corte por padrão; dissolve (tempo/mesmo lugar) e preto (capítulo) só com motivo. zoom, mascara, deslize,
  flash, whip, iris existem, mas não são variedade gratuita; zoom de transição sobre câmera em movimento vira corte.
  Padrões HyperFrames reimplementados (atribuição em `src/render/v2/NOTICE.md`).
- Câmera do `doc.plano` (Plano Mestre §4): layout `cobrir` (foto cobre o quadro em todo o caminho) × `integral`
  (documento/mapa inteiro; sobra só abaixo da linha da legenda, sobre mesa escura). `fixo` = sem transformação.
  Escala em log + centro em linha reta, seno in-out. A conta tem espelho em `src/v3/geometria.py` (mesma matemática):
  mudou um, muda o outro — `tests/test_v3_geometria.py::test_palco_real_igual_ao_espelho_e_sem_borda` compara os dois.
- Prova de movimento: `geometria.auditar_dados(dados)` (quadro a quadro: borda, encolhimento, salto, pan/zoom rápido,
  aceleração, para-e-anda, resolução) e `geometria.auditar_palco(pg, dados)` (palco real). A prévia já roda os dois.
- Render: `src/render/render.py::renderizar` (quadros → FFmpeg, masterização −14 LUFS, pico ≤ −1 dBTP).
- Antes do MP4: prévia por quadros (`pipeline.previa_quadros`). Defeito visível em quadro não justifica render completo.
- FFmpeg ad hoc (inspeção, cortes, galerias, loudness): skill `ffmpeg-skill` (kajisho5/ffmpeg-skill, MIT) — só desenvolvimento;
  a produção não depende de Claude Code para rodar FFmpeg.
- Mudou composição/transição → regenerar referência visual só se a mudança for intencional e registrada.

Testes: `python -m pytest -q tests/test_v2.py tests/test_v3_fiscal.py`.
