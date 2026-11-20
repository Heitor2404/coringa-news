# Diretor híbrido — fotografia autêntica e mecanismo autoral no FilmeEditorial
20/11/2026 • branch experimental \`atlas-direcao-visual-20261118\`

## Por que
Até a etapa anterior, \`diretor_roteiro\` localizava uma **fotografia CANDIDATA** no acervo V4, mas nenhum teste avançava com segurança até os **bytes originais**. O único preview renderizado partia de uma cena só de mecanismos. Resultado: o motor ainda não produzia prova híbrida de registro real + explicação visual.

## Composição reaproveitada
\`src/v4/formatos/diretor_hibrido.py\` NÃO é outro compositor:
1. Lê \`roteiro.cenas\` com \`acontecimento\` V2, \`duracao_s\` e texto. A entrada não informa \`asset\`, \`mechanism\`, \`shots\` nem \`cues\`.
2. Chama \`diretor_roteiro.analisar\` para escolher forma por acontecimento V2/V3; **não** usa regex da narração para inventar física.
3. Para explicações físicas usa o \`diretor_roteiro.expandir_preview\` + \`diretor_processos\` + catálogo de ações já existente, preservando a máquina de estados e as áreas seguras.
4. Para registros contextuais de \`lugar\`, \`ambiente\` ou \`pessoa\`, só aceita **uma única foto candidata** do acervo verificável que tenha: correspondência visual prévia, licença permitida com confirmação da API/humana, crédito, página Commons e SHA-256 travado, com download restrito a Wikimedia HTTPS por \`montagem_privada_real.baixar_imagem\`.
5. Reusa \`filme_editorial.avaliar/preparar\` para verificar **bytes reais**, SHA, dimensões, referências, direitos, fonte e identidade editorial, gerar props e renderizar tudo no **mesmo** \`FilmeEditorial.tsx\`. SHA divergente falha sem render.
6. Fotografia continua com \`evidence='representative'\` e \`direcao_evento.intencao='explicar_contexto'\`, **nunca** prova da ação física descrita no trecho seguinte. O processo EUV é desenho \`evidence='explainer'\`, não filmagem da TSMC.
7. Preserva \`proveniencia_hibrida.json\` com \`ORIGINAIS_SHA_VERIFICADOS\`, sem aprovar a identidade do evento, a edição, o fato, a voz ou publicação.

## O piloto é só validação da técnica
Entrada: contrato de roteiro V2 para exterior TSMC Fab 18 e mecanismo EUV (dois primeiros beats de \`QA_ROTEIRO_V2_TAIWAN_20261120.json\`). O terceiro beat, terremoto sem mídia específica, **não** entra: se mantido, todo filme híbrido continua bloqueado. Não confundir "foto real em um piloto" com "episódio publicável".

Com o catálogo de 20/11 a foto exata da Fab 18:
- \`commons:TSMC_Fab_18_May_2025.jpg\`
- Autor: 4300streetcar; licença declarada \`CC BY 4.0\`; página no Commons
- URL do thumbnail \(960×640\) travada no SHA da biblioteca \`3cfbaf153fd3f4d1e3a26f16ba9058baa37f9c63d7fee0c42d7c18cd57330ca0\`
- A foto mostra **exterior**, não o interior, e não prova que a etapa EUV ocorre naquele edifício.

O mecanismo EUV é uma ilustração técnica cuja fonte explicativa é ASML. O storyboard dirige os beats, mas não assume locação, equipamento específico nem desempenho fabril.

## Bloqueios essenciais
- \`H-MIDIA-SEM-PROVENIENCIA\`: metadados/licença/prova visual incompletos.
- \`H-CANDIDATO-AMBIGUO\`: mais de uma mídia com identidade compatível; requer curadoria, não escolha aleatória.
- \`H-REGISTRO-ESPECIFICO\`: não usar foto genérica para comprovar eventos históricos ou ações.
- \`H-FOTO-REPETIDA\`: a mesma fotografia não vira vários acontecimentos por zoom.
- \`R-SEM-MECANISMO\`: ação física sem renderer real; não produzir animação de palavras.
- \`R-SEM-REGISTRO\`: evento específico sem prova; não continuar o episódio só para completar tempo.
- Verificação real de SHA no \`filme_editorial.preparar\`; um bit alterado bloqueia a origem. O status "CANDIDATO" não sobe a "ORIGINAIS_SHA_VERIFICADOS" sem bytes.

## Generalização: o que já vale, o que não vale
O algoritmo não contém regra por tema ou marca; **qualquer** foto contextual que cumpra o contrato, e qualquer mecanismo já cadastrado, pode usar a mesma montagem. Testes negativos exigem travas e isolamento entre domínios.

Mas ainda **não** suporta uma história híbrida geral com mapa, documentos complexos, vídeos reais de ações, comparações e pessoas quando falta mídia homologada. Tampouco cria novos mecanismos ou extrai fatos de texto livre. A biblioteca atual tem pouquíssimos originais com prova de licença suficiente. A seleção automática de vídeos reais exige inspeção da ação quadro a quadro, identidade, ROI, janela e licença. Repetir o processo com três temas e revisões humanas ainda é necessário.

## Próximas etapas que agregam valor
- Reidratação de vídeo real e provas de ROI/ação pela biblioteca V3/ponte V4, SEM assumir que outro laboratório é TSMC.
- Montagem híbrida de três ou mais formatos: registro contextual → mapa ATLAS autenticado → mecanismo contextualizado → consequência documentada, com transições SEMÂNTICAS e sem cortes decorativos.
- Dar ao módulo V2 informação da pesquisa para declarar ações com fonte factual real; não tentar substituir semântica com regex.
- Medir repetição de mídia, legibilidade, continuidade, ritmo e variedade em *filmes completos*, não em demos de 10s.

**Segurança e processo:** apenas \`PROVA_VISUAL_PRIVADA\`, \`publicar=false\`; sem Gemini/Claude, TTS, Telegram, Meta/YouTube e sem tocar main/NTC/DOSSIÊ. A publicação exige aprovação humana, direitos, narração, fontes específicas e inspeção visual; nenhum relatório de testes equivale a isso.
