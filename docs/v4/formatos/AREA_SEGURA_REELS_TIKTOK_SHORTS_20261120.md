# Área segura multiplataforma — Coringa / FilmeEditorial (20/11/2026)

**Objetivo**: produzir vídeos documentais verticais que não dependam de marca, título, explicação, legenda, créditos, números e atores essenciais que possam ficar sob os controles de **Reels, TikTok ou Shorts**. O master permanece 1080×1920 e 9:16; o fundo não precisa ficar contido. Perfil experimental **MULTIPLATAFORMA_CONSERVADOR_V1**.

## Não são dimensões oficiais exatas de todos os aplicativos

Os layouts das interfaces de vídeos orgânicos variam por app, versão, posição dos botões, idioma, descrição, legenda e publicação como anúncio. Limites de anúncios são **apenas referências**. É obrigatório revisar render em celular e, para publicação, no preview do aplicativo correspondente. O retorno do teste é **segurança geométrica estimada**, jamais garantia de legibilidade na UI real.

## Fonte única, sem duplicar a arquitetura anterior

O projeto **já possuía** \`src/v4/formatos/plataformas.json\`, \`src/v4/formatos/layout.py\` e \`motor4/remotion/src/Camada.tsx\` (legenda real e créditos). Não criar outro motor de margens sem integrá-los.

- Os nomes em \`plataformas.json.ativos\` permanecem como perfis legados para reproduzir pilotos ATLAS; **não equivalem a homologação para publicação**.
- Os novos \`ativos_seguros\` são TikTok, Instagram Reels e YouTube Shorts com margens conservadoras. O preflight \`qa_area_segura.py\` consulta exatamente esses perfis via \`layout.py\`; não mantém três cópias de números por plataforma.
- \`motor4/remotion/src/formatos/safe-zones-vertical.json\` define somente a **interseção editorial comum e seus slots**; este arquivo aponta para a fonte existente para conferência de alterações.
- A área editorial comum conservadora em 1080×1920 é **[x=150, y=300, right=770, bottom=1240]**; a faixa horizontal direita e a parte inferior ficam livres de informação indispensável. **Fundo e barra de andamento são decorativos e podem ultrapassar os limites**.

## Dois modos mutuamente exclusivos (sem duplicar textos)

1. **Prévia sem narração**: logo/identidade, seção, palco visual, cue, headline, assunto e fonte em *slots* distintos, nunca truncando a informação crucial em silêncio. Palco de vídeo quadrado ou horizontal usa \`object-fit:contain\`, não corta equipamento para preencher 9:16. Os mecanismos podem ser re-enquadrados no palco, mas a leitura dos símbolos e os rótulos internos exige inspeção do MP4.
2. **Versão com legenda real**: a área do título/cue/assunto editorial é cedida à \`Camada\` com legendas sincronizadas; fonte fica em faixa separada. O compositor possui \`subtitle_mode\` para ocultar esses overlays quando o filme com voz usar a faixa. **A QA atual não possui narração; o uso correto desse parâmetro no pipeline de publicação ainda deve ser testado em conjunto com voz real.**

## Validação e limites

- \`src/v4/formatos/qa_area_segura.py\` valida configuração, slots, per-platform intersect, textos longos, presença de ROI/estados do vídeo, e bloqueia **mapas ATLAS com rótulos embutidos e gráficos raster** sem homologação. Uma cena com texto pré-renderizado não fica segura somente porque o compositor centralizou sua caixa.
- \`src/v4/formatos/filme_editorial.py\` exige \`safe_area_profile\` em filme final. Pilotos privados sem o perfil continuam possíveis para comparação histórica, mas não são candidatos a publicação.
- \`FilmeEditorial.tsx\` usa as posições do único contrato, mantém barras de progresso fora da leitura (decorativas) e permite overlay QA \`safe_zone_debug\` **somente quando solicitado**.
- A folha de inspeção compara as máscaras de cada uma das 3 interfaces diretamente de \`layout.mascaras\`, mais interseção comum; vermelho representa área de risco e verde a de leitura comum.
- O fiscal não pode provar que uma pessoa/ator em vídeo externo está dentro do enquadramento apenas com a caixa do título. Checagens de ROI e inspeção humana continuam necessárias.

## Critérios para fechar

1. Rodar \`tests/test_area_segura_plataformas.py\` e regressões de diretor/mecanismos **e** compilação TypeScript.
2. Renderizar duas animações independentes EUV/eclusa e revisar os quadros e a folha de quatro máscaras: legibilidade de marcas/números/textos, nenhum corte do acontecimento, fonte perceptível e tipografia interna sem duplicação.
3. Renderizar ao menos uma prova de mídia real com os mesmos layouts.
4. Testar legendas de narração sincronizadas em 2–4 linhas e créditos sem colisão, antes de permitir a versão final de publicação.
5. Em mapas/capturas com textos rasterizados, migrar o texto para a camada editorial segura ou comprovar empiricamente os quadros. **Não liberar com bypass de CI.**

**Status**: camada de segurança integrada ao motor experimental, QA geométrica automatizada. A qualidade estética e publicação ainda dependem da inspeção dos vídeos e de direitos/fatos verificáveis.
