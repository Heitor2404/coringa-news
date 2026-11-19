# Auditoria de acervos, substituição e 3 vídeos de fonte — 19/11/2026

## Resposta à pergunta do usuário

O motor global \`src/acervo.py\` já consulta **Wikipédia, Wikimedia Commons, NASA, LOC, Europeana, Smithsonian, museus, Openverse, iNaturalist, GBIF, Wikidata** e candidatos de vídeo por **Commons, NASA, Internet Archive e Pixabay** conforme disponibilidade. Os módulos executam buscas e possuem tratamento para falha de fonte; **não se pode afirmar que todas as APIs estejam saudáveis ou que toda prévia usa todos os acervos.**

- \`src/acervo.py::coletar\` exige pelo menos \`MIN_UTEIS\` mídias ou pula o tema, e \`complementar\` refaz a busca por frases faltantes.
- \`src/v4/acervo_v4.py::escolher\` exige confirmação do objeto e lugar pela visão; sem evidência retorna \`INCERTO\`/sem mídia.
- \`src/v4/formatos/ponte_biblioteca.py::catalogo\` explicitamente **não insere outro vídeo parecido** caso falte registro.
- \`src/v2/evidencia.py\` já distingue \`PROVA\`, \`RELACIONADA\`, \`CONTEXTO\`, \`INCOMPATIVEL\`. A classificação real deve se apoiar em metadados + inspeção, não na semelhança da palavra-chave.

**Decisão sobre substituição:** B-roll de outra guerra NÃO pode aparecer como registro de combate específico. Contexto genérico de outra guerra pode ser **considerado**, mas exige que a narração não atribua aquela ação ao episódio narrado e que haja legenda explícita com a identidade VERDADEIRA do evento filmado e licença/origem conferidas. Mesmo assim, nunca vira \`PROVA\`.

## O que foi implementado

- \`src/v4/formatos/qa_video_fontes.py\`: valida identidade declarada, risco de troca de acontecimento, licença/origem declarada, obtém integridade SHA-256, metadados ffprobe, amostras temporais e folha de contato de vídeos reais. **Variação de pixels não é prova de ação.** Verificador \`decidir_uso\` é genérico, sem if/else específico para guerra/país.
- \`src/v4/formatos/contrato_visual_comum.py\`: integração opt-in de \`substituicao\` no contrato de ATLAS e FILME; um storyboard que tente usar guerra diferente como \`registro\` é bloqueado antes de publicar. Não faz downloads automáticos de material parecido nem modifica a seleção de mídias dos motores produtivos.
- \`tests/test_qa_video_fontes.py\` cobre: guerra Síria como registro do Iraque bloqueada; outra guerra na cena específica bloqueada mesmo rotulada; contexto genérico possível somente com origem real exposta; metadados incompletos bloqueados; a imagem candidata não vira prova por ter URL, etiquetas ou pixels diferentes; mesma regra aplicada aos preflights do ATLAS e FILME.

## Execução de três fontes audiovisuais reais

- Workflow \`.github/workflows/qa-3-videos-reais.yml\`, disparo \`.github/qualidade/fontes_3_videos.txt\`.
- Manifesto \`docs/v4/formatos/qa_fontes_tres_videos.json\` contém:
  1. **Engenharia** — \`tests/midia/video_horizontal_navio.mp4\`, fixture licenciada no repo, **6,006s 1280×720**, fonte vídeo U.S. Navy \`Continuing Promise transits the Panama Canal\` (Commons). Pode registrar navio navegando, **não** automaticamente demonstrar enchimento de eclusa.
  2. **Ciência** — \`tests/midia/video_vertical_nasa.mp4\`, fixture licenciada no repo, **6,006s 720×1280**, fonte \`Hubble Women Making History: Beverly Johnson\` NASA/Commons. Não prova fabricação de chips; arquivo contém legendas e vídeo vertical estilizado.
  3. **História** — \`qa_fontes/hindenburg_1937.webm\`, baixado SOMENTE no runner do Commons, fonte Prelinger Archives/Eugene W. Castle \`Hindenburg Explodes (audio extracted)\`, arquivo **SHA-1 verificado** contra metadado de origem \`e7cc658e36f1d801d51a43cadfe4ae4f19e599e1\`. FFprobe vê **326,593s 352×480 codificado**, arquivo histórico de qualidade insuficiente para crop vertical amplo. O material tem letreiros, aviões/dirigível e destruição, não só a explosão em cada instante.
- Run **44545548727 SUCCESS**, artifact id **14539414167** \`qa-3-videos-reais-fonte-e-contato\` (JPEG + JSON, sem republicar vídeos). Variação de pixels entre amostras positiva nas três fontes, mas ação narrada = \`NAO_INSPECIONADA\`; status humano = \`PENDENTE\`; \`publicado=false\`.
- A folha \`contato_3_dominios.jpg\` foi recuperada e examinada: row1 ship/open water; row2 quadro vertical NASA com legendas embutidas; row3 Hindenburg com letreiros e cenas de fogo. Não usar esta amostragem como evidência de qualidade de episódio final.
- Regressão adicional em **44546274486**, com política integrada ATLAS/FILME; conferir status final do run antes de declará-lo verde.

## Próximas necessidades reais

1. Integrar **classificação de uso** ao caminho de escolha/produção com evidência de origem do candidato e rótulo realmente mostrado na tela, sem fallback invisível. Hoje é gate de contrato para storyboard que declara substituição, **não um garimpeiro de mídia semelhante funcionando automaticamente**.
2. Avaliar **MP4s finais de três temas diferentes** contra narração real e anotação humana; este teste de fontes não mede montagem, ritmo, câmera, correspondência ação × fala nem taxa real de falsos positivos/negativos do modelo.
3. Só promover uma regra para produção quando a mesma melhoria reduzir problemas em dois ou mais temas sem criar erros em outro. Não rodar novas V6/V7 de Panamá por inércia.

**Não mexeu em main, NTC, DOSSIÊ ou produtor diário; nenhuma mídia foi publicada.**
