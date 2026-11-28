# ATLAS — correção das safe zones e nova apresentação 3D (21/11/2026)

**Estado: LAB privado, sem publicação e sem aprovação artística.**

## Diagnóstico

O erro da versão anterior foi usar a interseção mais conservadora das margens de segurança de **texto de anúncios** como limite obrigatório da **animação toda**, produzindo um mecanismo miniaturizado e uma tela vazia. O usuário rejeitou tanto tamanho quanto direção visual.

## Pesquisa de plataformas

- Meta: orientação para logos e texto em anúncios Reels/Stories, não mandato para recortar máquina e cenário de todo Reel orgânico. As proporções 14% superior/35% inferior/6% lateral são referência histórica para anúncios, não geometria oficial universal de cada aparelho. https://www.facebook.com/business/help/980593475366490
- TikTok Ads junho 2026: zona varia com dimensão, legenda e opções interativas; preview não é necessariamente igual à experiência real. https://ads.tiktok.com/resources/help/article/tiktok-auction-in-feed-ads
- YouTube Shorts: editor sinaliza se texto/stickers estão próximos demais da borda. https://support.google.com/youtube/answer/16215842

## Contrato novo

Arquivo: `motor4/remotion/src/formatos/editorial-safe-roles-v2.json`.

**visual_full_bleed**: pode ocupar 1080×1920 inteiro e passar por trás da UI. **visual_primary_action**: centro do mecanismo preferencialmente x260–740 e y600–1190, com corpo periférico podendo ultrapassar. **essential_text**: reserva [92,288,765,1225]. **watermark**: pode ficar fora da faixa protegida. Overlay per-platform é aproximação, nunca garantia. Não tratar 'ad safe' como escala física.

## Código e prova real

- `motor4/remotion/src/formatos/CinematicCutaway3D.tsx`: direção nova, modelo real 3D paramétrico de pistão, biela, volante, cabeçote, corpo e entradas/saídas. Mesma `SliderCrankRig.ts`, duas configurações em JSON, sem codificação por episódio.
- Novas composições **privadas**: `Prova3D-Pistao` e `Prova3D-Compressor` no `Root.tsx`. Não alteram produção.
- 3D passou em testes e quatro stills renderizados nos runs 44948033100, 44948322718, 44948514332, 44948740878. Último é direção azul-ciano clara, amplica máquina, cabeçote sem corte, biela à frente do volante, narrativa só no topo e barra de progresso embaixo.
- Artefato do run 44948740878: 14724801611, expiração 25/11/2026, quadros `motor_inicio.png`, `motor_transmissao.png`, `compressor_admissao.png`, `compressor_pressao.png` e contato.
- Workflow separado `.github/workflows/qa-cinematic-3d-videos.yml` para dois MP4s 8,4s, 540x960, WebGL em software. Run criado: 44948783359. Confirmar conclusão e inspecionar MOVIMENTO antes de alegar vídeo aprovado.

## Limites

Não há reconstrução automática do vídeo da internet; o sistema 3D é uma nova expressão original da física parametrizada, não conversão automática de modelo externo. É apenas uma família mecânica. Termodinâmica de gás e válvulas são ilustração didática. A revisão estética humana permanece pendente. Sem Claude, Telegram, publicação, main, NTC ou DOSSIÊ.

## Resultado de vídeo 3D integral (confirmado 21/11/2026)

- [GitHub Actions 44948783359](https://github.com/Heitor2404/coringa-news/actions/runs/44948783359): SUCCESS. Passaram compilação TypeScript, testes de configuração e as duas renderizações reais em WebGL/Three.js por CPU.
- Artifact privado 14725310354 (atlas-cinematic-3d-2videos-privados), expira em 26/11/2026 20:59:30 UTC. Dois filmes 8,4 segundos, 30 fps, 540×960, MP4/H.264, sem voz, sem Telegram e sem publicação.
- MOTOR_3D_PRIVADO.mp4 SHA-256 55aefcff3bb9fd71ce6981b981f52596f8d1151c8d4862804ad04e358140f979; delta RGB de movimento 19,08.
- COMPRESSOR_3D_PRIVADO.mp4 SHA-256 b272bd9eb21cea32a7b89ebcfbc8fc0a9e82ffe666b598ad883a9c94044ae056; delta RGB de movimento 17,26.
- Contato de 10 tempos reais contato_3d_10quadros.jpg, cinco por tema. Inspecionado visualmente: pistão e biela articulados, grande escala do conjunto, legenda no topo e válvulas/portas simplificadas. O movimento físico aparece, não cinco imagens estáticas.
- Valor do delta RGB é medição mecânica grosseira, não prova de retenção, qualidade editorial ou interpretação factual perfeita.
- Comparativo real entre frame do antigo desenho e frame do novo 3D em /mnt/data/comparativo_real_antes_depois_3d_20261121.jpg produzido no turno, verificar path em futuras conversas.
- Pendente avaliação ESTÉTICA do usuário: a arte ainda se parece com um protótipo didático 3D, não afirmar vídeo publicável. O modelo NÃO recria animações da internet automaticamente.
