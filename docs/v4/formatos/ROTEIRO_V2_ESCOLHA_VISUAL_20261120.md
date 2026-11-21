# Direção do roteiro V2 até a escolha de provas e mecanismos — 20/11/2026

## Por que esta etapa existe
O motor já tinha \`diretor_processos.expandir\`, mas ele exigia eventos semânticos estruturados manualmente antes de chegar ao render. Analisamos módulos EXISTENTES, em vez de inventar um segundo classificador de palavras:
- \`src/v2/contrato.py\`: contrato de acontecimentos do roteirista (tipo, sujeito, ação, estado inicial/final, mostrar, dados e fonte)
- \`src/v3/linguagem.py\`: forma visual apropriada para o tipo (registro, mapa, esquema, documento, comparação, tipografia)
- \`src/v4/formatos/catalogo_mecanismos.py\`: capacidades físicas realmente implementadas
- \`src/v4/formatos/ponte_biblioteca.py\`: biblioteca visual com procedência/visão/licenças (sujeita a bytes e direitos reais)
- \`src/v4/formatos/filme_editorial.py\`: preflight e composição com veto de publicação.

**A V2 já provou que expressões regulares não entendem paráfrases** (6/16 frases no conjunto de reserva viraram fotos indevidamente, segundo comentário no contrato); portanto este código **NÃO** adivinha acontecimentos com palavras-chave do roteiro. Ele consume os contratos V2 já emitidos pelo roteirista. Isso não é compreensão automática de texto livre.

## Mudança no MOTOR
Novo \`src/v4/formatos/diretor_roteiro.py\`:
1. Recebe \`roteiro.cenas\` com \`fala\`, \`duracao_s\` de voz/direção e \`acontecimento\` V2, sem \`asset\`, \`mechanism\` ou \`shots\`.
2. Classifica forma via V3 e compara ações estruturadas com o catálogo V4. Exemplo: \`source→reticle→projection→wafer\` seleciona \`optical_projection\`; \`metal→oxygen→oxidize→rust\` não tem física implementada, então é BLOQUEADO.
3. Pesquisa mídia da biblioteca para eventos de registro por identidade do SUJEITO. Uma correspondência é somente **CANDIDATO**; exige SHA/arquivo original, licença, correspondência factual específica e revisão humana. Uma foto do exterior da fábrica não vira registro de seu interior nem de terremoto.
4. Encaminha ao \`diretor_processos\` e ao MESMO \`filme_editorial.avaliar/preparar\` quando **todas** as cenas de uma prova técnica são mecanismos existentes. Caso haja foto/mapa/vídeo sem prova ou processo não cadastrado, retorna relatório \`R-*\` e **bloqueia render** da história, sem preencher lacunas com cards.
5. Só funciona em \`PROVA_VISUAL_PRIVADA\`, \`publicar=false\`; sem Claude, Gemini, TTS, Telegram ou URLs baixadas.

## Testes concretos, sem pré-selecionar recurso
\`QA_ROTEIRO_V2_TAIWAN_20261120.json\`: três trechos narrativos do eixo semicondutores, mas **não** escolhe fotos ou renderizadores:
- Fab 18: V3 sugere registro; V4 encontra \`commons:TSMC_Fab_18_May_2025.jpg\` como candidato, porém **não pode montar** sem os bytes e a autenticação editorial da cena
- mecanismo EUV: V3 esquema; V4 reconhece \`optical_projection\`; disponível para prévia técnica, não para publicar
- terremoto de 2024: registro específico indisponível; BLOQUEIA (não usar vídeo de outro desastre).

\`QA_ROTEIRO_V2_OXIDACAO_20261120.json\`: transformação física da oxidação do ferro, assunto independente; V3 exige esquema, mas V4 ainda não tem renderer físico; BLOQUEIA. Não tomar mecanismo de litografia ou de eclusa emprestado.

\`QA_ROTEIRO_V2_EUV_20261120.json\`: isolado técnico com contrato V2, sem name de renderer e sem keyframes. Pode seguir por \`diretor_roteiro → diretor_processos → filme_editorial → Remotion\` numa prévia privada de ~6,9 segundos.

## O que NÃO está pronto
- Extrair ações físicas verificáveis a partir de *qualquer* texto livre sem um contrato V2 ou provedor semântico. A etapa declarativa da V2 continua necessária; o mecanismo não afirma entender sozinho roteiros arbitrários.
- Selecionar vídeo de origem literal por semelhança de texto. Identidade, licença, tempo, ROI e observação de ações requerem inspeção e bytes originais; caso contrário, candidato sem render.
- Produzir uma animação inédita para qualquer processo. Catálogo é finito, e um caso sem capacidade permanece bloqueado.
- Certificar fatos, direitos ou qualidade visual a partir de contratos. A inspeção do MP4 permanece humana.
- Fazer um episódio final ou publicar. O eixo editorial permanece \`Guerra dos Chips EUA × China\`, sem trocar a pauta pelo teste.

## Próximo gargalo produtivo
Ingestão e verificação de **mídia real para eventos** (bytes SHA, identidade exata e direitos), com composição do filme híbrido — e uma camada semântica de roteiro com fonte confiável que produza/valide o contrato V2. Essa camada pode ser assistida por IA quando houver disponibilidade, mas **nenhuma implementação deve fingir** que regex é substituto dela.

Branch experimental \`atlas-direcao-visual-20261118\`. Manter \`main\`, NTC, DOSSIÊ sem alterações.
