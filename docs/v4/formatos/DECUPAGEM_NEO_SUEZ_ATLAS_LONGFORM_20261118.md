# Estudo REAL do vídeo neo / Canal de Suez — tradução para ATLAS LONG
**18/11/2026 | STATUS: DOCUMENTAÇÃO, SEM CÓDIGO, SEM HOMOLOGAÇÃO OU PUBLICAÇÃO**

## Evidência e limites
MP4 `videoplayback.mp4`, enviado pelo usuário; vídeo original identificado pelo usuário como neo, *How One Ship Caused a Global Traffic Jam*: https://www.youtube.com/watch?v=8RxmRw1kCrc. Arquivo de **489,732 s**, 640×320 (2:1), 25 fps, H264, AAC estéreo 44,1k. **12.242 quadros decodificados**, amostragem visual a cada 2 s (245 capturas), análise quantitativa de transição a cada 0,2 s. Inspeção visual de folhas de contato de todo o vídeo; NÃO alegar exame humano de cada um dos 12.242 quadros nem perfeição da transcrição do áudio. **38 picos fortes de variação visual**, que **não** equivalem a exatamente 38 cortes. Áudio medido com FFmpeg: **−17,66 LUFS integrada**, **−0,59 dBTP pico verdadeiro**, **5,80 LU LRA**. Não houve escuta subjetiva confiável; não fazer afirmações sobre timbre ou mix por inferência.

## Decupagem visual/editorial por trecho
| Intervalo | Proposta narrativa demonstrada pelo neo | Mídia / operação |
|---|---|---|
| 0:00–0:21 | O trajeto do Ever Given passa por um gargalo global | mapa escuro com linhas vermelha/branca progressivas, rótulos discretos |
| 0:22–0:50 | O navio trava uma passagem estreita | mapamúndi → aproximação ao satélite local do Suez; eixo de obstrução em vermelho |
| 0:50–1:05 | A obstrução é real | filmagem do navio e visão local do canal |
| 1:06–1:41 | Por que é tão difícil retirar o navio? | reconstrução 3D neutra do convés, escala humana, tamanhos e comparação de barcos; **um cenário persiste mas progride** |
| 1:42–2:28 | O resgate exige equipamentos, trabalho e coordenação | escavadeiras, rebocadores, diagrama transversal e sala de controle |
| 2:28–3:00 | Por que não contornar a África? | mapa regional/mundial: percurso via canal vs rota ao redor da África |
| 3:00–3:10 | Como é navegar o canal? | filmagem real, pequena pausa atmosférica |
| 3:10–3:23 | Congestionamento se acumula | satélite + densidade de navios em vermelho |
| 3:24–3:56 | A geografia constrange o tráfego | travelling seguindo o canal e lagos reais; marcos geográficos |
| 3:56–4:05 | Retorno ao concreto | filmagem das margens e equipamentos |
| 4:05–4:25 | Qual o efeito econômico imediato? | reconstrução de navio + bloqueio + comparação de rota |
| 4:25–4:47 | Navios e empresas enfrentam escolha | imagens documentais em grayscale com navios em vermelho, destaque por objeto, não cards |
| 4:47–5:05 | Retorna à causa física | reconstrução no canal como nova etapa causal |
| 5:05–5:35 | O custo alcança mercadorias e logística | armazém, porto, contêineres destacados seletivamente em vermelho |
| 5:35–5:49 | Distribuição/desequilíbrio do estoque | mapa América do Norte + contêineres vermelhos multiplicados; passa do objeto físico para representação |
| 5:49–6:00 | Efeito ligado à causa | satélite do navio atravessado novamente |
| 6:00–6:40 | Como foi finalmente liberado? | filmagens reais de rebocadores e navegação; consequência visível |
| 6:40–7:16 | E depois de liberar? | navio, infraestrutura portuária, trem, imagens reais; novo problema de cadeia logística |
| 7:16–7:50 | Conclusão | retorna à embarcação em imagens reais e depois reconstrói em 3D com câmera que recua |
| 7:50–8:10 | Encerramento | créditos/outro |

**As marcações são de seções editoriais aproximadas, não dos pontos exatos de cada corte.** A descrição temporal suplementar foi consultada em https://videohighlight.com/v/8RxmRw1kCrc?aiFormatted=false&language=en&mediaType=youtube&summaryId=BG_Pa4kBYn5DH8ztQrAc&summaryType=default e é síntese de terceiros; as observações visuais vieram do MP4.

## Sete aprendizados objetivos (e limites)
1. **Geografia tem função.** Mapa abstrato = relações mundiais; satélite = geografia real; pontos = tráfego; percurso = diferença entre alternativas. **neo usa câmera zenital bastante**. Portanto não impor 3D oblíquo em todo mapa: o problema do piloto Chips é mapa repetido, não somente ângulo da câmera.
2. **Mesma cena pode durar dezenas de segundos com PROGRESSÃO.** 3D ~1:06–1:41 explica escala e equipamentos; satélite ~3:24–3:56 percorre infraestrutura. Um corte a cada 2 s ou card a cada 3 s **não** é a receita.
3. **Continuidades de objeto:** navio → bloqueio → resgate → comércio → volta ao navio. Mesmo recurso retorna quando carrega informação nova, não para reciclar quadro.
4. **Cor como seleção semântica:** vermelho em navio/contêineres/rotas. Adaptar a técnica para as **cores já aprovadas Coringa**: amarelo `#FFD21F` para foco, vermelho `#E5483A` para bloqueio/risco, ciano para tecnologia; não copiar paleta neo nem banhar tudo em vermelho.
5. **Evidência física > cartão explicativo.** Escavadeiras, navios, armazéns, portos e trens mostram ações e consequências. No Chips, fotografia da fábrica pequena e linhas Holanda→Taiwan não explicavam fabricação, EUV ou dependência industrial.
6. **Mudança de escala = mudança de pergunta.** mundo → canal → navio → humanos → mundo. O texto e a câmera têm alvos referenciáveis, não movimentos decorativos.
7. **Explicação em cadeia:** acidente → resgate difícil → importância do canal → choque comercial → consequências depois da liberação. A estrutura **causa/pergunta/resposta/nova consequência** sustenta 8 min.

### Limites da imitação
- Não importar imagens, áudio, modelo 3D, screenshots ou stock (inclusive Getty, citada pelo neo) para vídeos Coringa sem licença.
- O neo usa After Effects, GeoLayers, Illustrator/Premiere e Blender, segundo FAQ oficial https://neoproductions.com/faq. Isso descreve ferramentas dele, não obrigação de comprá-las; nosso renderer pode chegar a princípios semelhantes com componentes próprios.
- O 3D monocromático pode parecer mais esquemático que premium. Não copiar 3D cinza por padrão.
- Parte do episódio usa planos longos que seriam inadequados para Shorts sem outras decisões editoriais.
- Não concluir preferências de voz com análise de LUFS. Locução aprovada do Coringa deve ser **travada por preset**, sem fallback Edge silencioso.

## Adaptação em dois perfis de saída
**ATLAS SHORT / vertical:** preservar `GUIA_VISUAL_ATLAS_V1.md`, áreas seguras por rede, legenda até 3 palavras/grupo com até uma amarela, créditos, CTA e ritmo de Short; não sobrecarregar a cada frase com card.

**ATLAS LONG / horizontal (proposta, ainda NÃO implementada):** novo preset de **1920×1080, 30 fps** com slots, câmera e créditos próprios; **não esticar `1080×1920`**, nem copiar margem da cópia neo 2:1. Narração estruturada em capítulos/atos, possíveis 8–12+ minutos, legendas fechadas/arquivo SRT quando apropriado e dados na imagem só quando relevantes. O mesmo diretor semântico e acervo validado abastecem os dois perfis.

## Mudanças arquiteturais propostas, em ordem
**P0 — trabalho editorial/portões, baixo custo**
- Antes do beat, ficha `referente_visual → ação_observável → prova_licenciada → aprendizado`; sem mídia/mecanismo necessário, estado `CAPACIDADE_INDISPONÍVEL`, nunca preencher lacuna com outro mapa ou card.
- Separar `progresso_em_plano` de `mudança_de_tela`. Regra atual `progressao_max_s=3` não deve ser aplicada sem adaptação à linguagem longform. O fiscal deve proteger contra imobilidade vazia, não punir explicação que evolui.
- Diferenciar workflow `success`, fiscal `BLOQUEADO` e aprovação humana; travar narrador.
**P1 — capacidades visuais genéricas**
- Prova visual real dominante (foto/vídeo grande), com rastreio de licença e fonte.
- Sequência **mapa abstrato → satélite real → objeto / processo → volta a mapa** mantendo referente.
- Contrato de focalização por evento e states para mecanismos 2.5D/3D; primeiro somente o que se reutiliza. No catálogo atual ATLAS só `mecanismo.eclusa` é aprovado.
- Destaque por máscara quando técnico/editorialmente seguro, mapa densidade com dados reais, passagem de objeto a representação cartográfica.
- Investigar visão oblíqua como **opção**, não estilo obrigatório.
**P2 — adaptação longform e homologação**
- Prototipar um capítulo de 90–120 s para testar **abertura, explicação, mudança de escala e consequência** em 16:9 com voz aprovada.
- Testar custo de render, armazenamento e licença do novo formato antes de episódio inteiro. O teto de custo de Shorts não é transferível automaticamente.
- Manter **NTC, DOSSIÊ e `motor-integral-v4` intocados** até revisão humana.

## Checklist que um diretor deve satisfazer para cada minuto
1. Qual é a **pergunta nova** deste trecho?
2. Que **objeto, pessoa, processo ou relação geográfica** a câmera mostra?
3. O que **muda dentro do plano** (fato novo, não mera deriva)?
4. É **prova real** ou **reconstrução rotulada**? Origem e licença estão corretas?
5. Há uma **virada causal** que motive continuar?
6. Mapa/cartão/foto é realmente a **modalidade mais esclarecedora**?
7. A narração está na **voz aprovada** e a relação fala→quadro está compreensível?
8. O minuto termina com uma **revelação, dificuldade ou próximo passo**?

## Próximo experimento
**Não renderizar 8–10 min ainda.** Escolher um capítulo teste em 16:9 (90–120 s) com uma pergunta causal fechada e prova física, demonstrando três mudanças de escala; separar código de formato e legado. Depois validar roteiro, fatos, voz, acervo, composições, mp4 e percepção humana. Se for incapaz de produzir uma boa cena de 2 minutos, ampliá-la para 8 só multiplica os problemas.

**Fontes:** vídeo oficial https://www.youtube.com/watch?v=8RxmRw1kCrc ; FAQ https://neoproductions.com/faq ; neo sobre séries https://neoproductions.com/ ; a síntese secundária com marcação temporal acima; contratos internos de ATLAS V1/V2.
