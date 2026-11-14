# Coringa Explica — correção cirúrgica do piloto Ever Given (V2.3)

Ramo `visual-v2-3-correcao-piloto`, a partir de `visual-v2-2-correcao-final`. Sem merge, sem NTC, sem chamada paga,
nenhum vídeo de produção gerado. Tudo foi medido sobre o material ORIGINAL do piloto (execução 43540333049),
preservado em `tests/piloto_ever_given/` (roteiro, acervo, cenas com os tempos da voz, fiscal, imagens, áudio).

## Causas-raiz

| # | Defeito no piloto | Causa-raiz | Onde |
|---|---|---|---|
| 1 | 13 de 19 cenas caíram em foto; 26 bloqueios só depois de 11 min | ninguém validava o contrato antes da narração; os dados vinham em texto livre | não existia etapa |
| 2 | "369 navios" bloqueado por "número sem fonte" | o leitor da pesquisa só lia 9 de 25 linhas (`(Wikipedia (inglês))` tem parênteses aninhados) e a cena de número não recebia a fonte | integração |
| 3 | "faturamento recorde" com fonte fora da lista | a lista de fontes ia ao motor cortada nas 3 primeiras | `main.py` |
| 4 | vento empurrando tratado como rota; atravessado exigindo diagrama; cobrança como citação; contagens como etapas | tabela de tipos sem reclassificação; nenhum tipo aceitava foto real | contrato/seletor |
| 5 | diagrama em árabe em "ventos fortes o empurraram" | o casamento do acervo trocou a foto que o roteirista pediu (a9, satélite) pelo diagrama (a5) | casamento → sem conferência |
| 6 | tela preta ~6 s | crítico sem composição e sem imagem virava `foto.documental` vazia | `montagem.py` |
| 7 | "NÚMERO BLOQUEADO · F3" dentro do vídeo | número reprovado virava banner com o motivo interno | `montagem.py` |
| 8 | sincronia perdida | a palavra de sincronia estava no 2º plano da fala dividida; cada plano era resolvido sozinho | `piloto.py` |
| 9 | créditos com ids inconsistentes | arquivos numerados pelo download, ids pelo filtro; o diagnóstico não guardava o vínculo; o post creditava a escolha, não o que aparecia | `acervo`/`main.py` |
| 10 | −18,5 LUFS | ganho preso ao teto do limitador numa mistura com ~21 dB entre pico e média | `masterizar` |
| 11 | fiscal: frase isolada, foto real reprovada, mesma causa contada várias vezes, tela preta e texto técnico aprovados | S1/S2/S5 por plano; nenhum código para tela vazia/texto técnico | `fiscal_v2.py` |
| 12 | fiscal antigo 10/10 "pode postar" | o resumo não subordinava a nota antiga ao V2.2 | `main.py` |
| 13 | (achado no replay) foto de satélite virava faixa de 69 px | o detector de cartão de scanner tomava areia lisa por margem | `acervo_v2.py` |

## Fiscal antes × depois (mesmo material)

| | Piloto original, fiscal antigo | Piloto original, fiscal corrigido | Piloto com as correções |
|---|---|---|---|
| Bloqueios | 26 (S5 12, S1 9, S2 4, D9 1) | 12 causas distintas (S5 8, D13 1, D14 1, D9 1, A1 1) | **1** (S5 e9) |
| Tela preta (D13) | não detectada | bloqueada | não ocorre |
| "NÚMERO BLOQUEADO" (D14) | não detectado | bloqueado | não ocorre |
| Loudness | aviso | bloqueio (A1) | — (o replay não renderiza) |
| Revisão humana | — | — | S7: "levava vinte mil" (capacidade como carga) |

O bloqueio que fica é legítimo: e9, "catorze rebocadores… o libertaram", declara o estado final "flutuando
livremente" e nenhuma imagem do acervo mostra o navio liberado (todas mostram o navio preso). O preparo barra antes da
narração com: dados para `comparacao.antes_depois` (img_antes, img_depois) ou `processo.etapas`, ou foto/vídeo real
que mostre "flutuando livremente".

## Revisão factual (só as afirmações problemáticas)

| Afirmação no roteiro | O que as fontes dizem | Veredito |
|---|---|---|
| "levava vinte mil contêineres" | Capacidade 20.124 TEU; carga reportada ≈ 18.300 contêineres (Reuters; Wikipedia: 18.300 TEU) | **Errado**: capacidade apresentada como carga. O preparo agora manda para revisão humana (S7). |
| "foi movido 80% na direção certa" | Autoridade do Canal: manobras restauraram 80% da **direção** (alinhamento) do navio, com a popa a 102 m da margem | **Impreciso**: é alinhamento, não distância percorrida. |
| "ventos fortes o empurraram" | Atribuição inicial a ventos/tempestade de areia; em 27/03 o chefe da Autoridade disse que o vento não foi a causa principal e que pode ter havido erro técnico ou humano | **Incompleto**: falta a ressalva (a pesquisa tinha a linha; o roteiro não usou). |
| "quinze rebocadores, duas dragas e seiscentos trabalhadores" | Boskalis: 11 rebocadores de porto + 2 oceânicos e ~30.000 m³ de areia dragada; Svitzer: 13 rebocadores e duas dragas; duas dragas da Autoridade (Mashhour e 10th of Ramadan); uma nota de operadores citou "cerca de 15 rebocadores" na madrugada de 29/03 | Dragas confere; 15 rebocadores só em fonte secundária (13 nas primárias); **600 trabalhadores não encontrado** em fonte primária. |
| "catorze rebocadores… às 15h05" | 15h05 confirmado pela Boskalis; total primário de 13 rebocadores | Horário confere; número diverge (13). |
| "cobrou 916 milhões… caiu para 600 milhões e, em julho, liberado" | US$ 916 mi (com US$ 300 mi de "reputação"), reduzido para ~US$ 600 mi em maio, depois para US$ 550 mi; liberado em 7/07 com termos não divulgados | Confere, mas omite a 2ª redução (550). |
| "faturamento recorde" | Autoridade do Canal (2/01/2022): US$ 6,3 bi em 2021, maior da história, +12,8% sobre 2020; 20.694 navios | **Confere**; a fonte do roteiro (iG Economia) é secundária; a primária é o comunicado da Autoridade. |
| "369 navios esperavam" | Chefe da Autoridade (Reuters, 29/03): ao menos 369 navios na fila; depois 422 | **Confere** (a fonte estava na pesquisa; o problema era de integração). |

Fontes: Boskalis (comunicado de 29/03/2021, via gCaptain/Riviera/Professional Mariner); Suez Canal Authority
(comunicados via Reuters, AP, AFP, The Maritime Executive, Arab News); Svitzer (via AJOT/The Maritime Standard);
Reuters via MarineLink e Insurance Journal; S&P Global; Ahram Online.

## Pendências

| Item | Estado |
|---|---|
| Causa exata do −18,5 LUFS | parcial: a masterização agora garante a meta numa mistura de crista alta e o fiscal bloqueia fora da meta; o componente que gerou o pico não foi identificado porque o pacote não tinha a narração separada (o piloto agora guarda narração e mistura) |
| e9 (navio liberado) | bloqueado de propósito: falta imagem do estado final |
| Fatos 80%, vento, 600 trabalhadores, 14/15 rebocadores | o motor não reescreve o roteiro; a correção vem do roteirista no próximo piloto |
| Fiscal sem o preparo | sem o relatório do preparo, o fiscal não sabe se uma foto mostra o fato (bloqueia, como deve) |
| Aprovação visual | do Heitor |
