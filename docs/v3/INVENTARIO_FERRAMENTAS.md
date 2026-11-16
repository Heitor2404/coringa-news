# V3.1 — Inventário de ferramentas gratuitas (16/11/2026)

Não reavaliar o que está aqui sem motivo novo. A V3 (docs/evidencia/REESTRUTURACAO_AUDIOVISUAL_V3.md §1–3) já auditou
Remotion, video-use, ffmpeg-skill, ai-design-skills e o catálogo HyperFrames; esta tabela atualiza e fecha os itens.
"Benefício comprovado" só quando medido num vídeo real ou num teste que falharia sem a ferramenta.

| Ferramenta | Já existia? | Gratuita / licença | Dependências | Implementada? | Benefício comprovado |
|---|---|---|---|---|---|
| HyperFrames — componentes (count-up, chart-story, headline-slam, logo-brand-close, vox-annotate) | sim (template antigo, `hf.js`) | Apache-2.0 | GSAP 3.14.2 | sim, motor antigo | uso em produção (motor antigo) |
| HyperFrames — padrões em `doc.js` (hw-callout-circle, yt-feather-highlight, grain, vignette) | sim (V3) | Apache-2.0 | nenhuma | sim, V3 | V3: tempo parado 73%→33% (Pompeia) com a direção que usa esses padrões |
| HyperFrames — `whip-pan-cut`, `iris-reveal` → transições `whip` e `iris` | **não** | Apache-2.0 (reescrito, atribuição em `src/render/v2/NOTICE.md`) | nenhuma | **sim** (`nucleo.js`) | ensaio local: renderiza e o fiscal detecta a troca; ganho estético aguarda avaliação humana |
| HyperFrames — `before-after-wipe` | equivalente já existia (`comparacao.antes_depois`) | Apache-2.0 | — | não portado | duplicaria uma capacidade existente |
| Skills oficiais HyperFrames (hyperframes, cli, registry, media-use, reverse-any-video, style-sampling, remotion-to-hyperframes, figma, slideshow) | não | Apache-2.0; `media-use` e partes de `reverse-any-video` usam HeyGen (pago) | CLI/bun do HyperFrames | **não instaladas** | o render do Coringa é o palco próprio; as skills servem ao CLI HyperFrames. A parte gratuita útil (extração de quadros, comparação, análise de referência) já é coberta por FFmpeg + PySceneDetect + `folha_contato` |
| ffmpeg-skill (kajisho5, commit f1c97cb) | não | MIT | Python stdlib + FFmpeg 6.1+ | **sim**, `.claude/skills/ffmpeg-skill` (só desenvolvimento) | `probe`, `loudness`, `scenes` rodaram no ensaio local; a produção não depende dela |
| PySceneDetect 0.7.3 | não | BSD-3 | opencv-python-headless | **sim**, `src/v3/fiscal_editorial.py` (cortes reais × planejados) | detecta corte seco e transição; calibração com os MP4s da validação em `docs/v3/ENTREGA_V3_1.md` |
| video-use (browser-use) | não | MIT | ElevenLabs Scribe (pago) para transcrever | **não instalado** | só metodologia: autoavaliação do render (folha de contato + fiscal), nunca recortes de fala (o Coringa não edita gravação bruta) |
| snapcn.dev | não | **não verificável**: o site está fora da rede deste ambiente (2ª tentativa, 16/11) e a busca não achou licença publicada | Remotion | **rejeitado** | licença não verificada = não entra (regra do brief). Remotion: grátis para até 3 pessoas (licença Remotion), mas segundo runtime sem ganho de qualidade (V3 §2) |
| ai-design-skills (elayadesign, commit 456d9e0) | não | MIT | — | **rejeitado** | só `figma-designer` e `landing-page-design`: nada de vídeo/motion |
| Remotion (protótipo) | sim (`prototipos/remotion`) | licença Remotion (grátis até 3 pessoas) | React | protótipo isolado, mantido | sem ganho visual sobre o palco (mesmo Chromium) |
| SQLite (stdlib) | — | domínio público | nenhuma | **sim**, biblioteca global | dedup + reuso de regiões testados (`tests/test_v3_biblioteca.py`) |
| faster-whisper, Gemini TTS/visão, Claude Code | sim | cota gratuita / assinatura | — | em uso | alinhamento de fala, visão com cache por sha, diretor |

## Vídeos de referência do brief

Os nove links do YouTube não abrem a partir deste ambiente (YouTube fora da rede permitida). **Não assisti.** As técnicas
do brief (homogeneização, hierarquia visual, câmera com intenção, motion programático, documentário, animação explicativa,
edição pela voz, som, ciclo de revisão) entraram como regras verificáveis:

| Técnica | Onde virou código/regra |
|---|---|
| Homogeneização | `doc.plano` tratamento de cor comum (`tratamento`), granulação e vinheta |
| Hierarquia visual | anotações ancoradas em regiões da visão; `E-ATENCAO` e `E-SLIDESHOW` no fiscal |
| Câmera com intenção | movimentos válidos, imperceptível corrigido (ERR-010) |
| Motion programático | receitas + composições paramétricas pelo contrato, nada escrito por vídeo |
| Documentário | selo honesto (ERR-003), REGISTRO só com ano compatível, foto real primeiro |
| Explicação de mecanismo | `R-MECANISMO-ANIMADO`, ERR-006 bloqueia mecanismo crítico em cartão |
| Edição pela voz | tempos da narração alinhada; anotação `na_palavra`; divisão de trecho `comeca_na_palavra` |
| Som | `escolher_musica` (biblioteca existente em `assets/musica/`), −14 LUFS, pico ≤ −1 dBTP (T-LOUDNESS) |
| Ciclo de revisão | prévia por quadros antes do MP4, 1 correção dirigida por problema, folha de contato |
