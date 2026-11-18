# ATLAS — piloto 2: GUERRA DOS CHIPS (brief factual/editorial)
**18/11/2026 · Branch experimental `atlas-piloto-chips-20261118` · SEM render ou publicação neste documento.**

## Objetivo do teste

Demonstrar que o ATLAS consegue explicar uma disputa geopolítica/econômica usando a **mesma identidade audiovisual** aprovada no Panamá — mapa como palco principal, fotos reais verificadas, card editorial, pin e conexão animada. Não são permitidos motion graphics novos só para este tema nem estética de notícia/tecnologia inventada. A eclusa não participa deste piloto.

## Hipótese narrativa

> **Por que uma ilha tem tanta importância numa disputa entre as maiores potências do mundo?**

Responder, em ordem:
1. **Taiwan** — geografia de uma concentração industrial estratégica: fabricar chips avançados tem importância geopolítica.
2. **Holanda** — ASML e equipamentos de litografia EUV: partes da cadeia dependem de fornecedores muito especializados.
3. **Estados Unidos** — presença relevante no design/tecnologias e controles de exportação sobre certos itens.
4. **China** — o interesse em ampliar capacidade e reduzir dependência; distinguir restrição de exportação de proibição universal.
5. **Conclusão** — a cadeia não está localizada em um único país; o poder está nos elos de produção, ferramentas, conhecimento e regras.

**Evitar:** analogia de corrida armamentista simplista, afirmação de bloqueio total e permanente, vídeo sem fotos, cards que ocupem todo o mapa, mapa que represente uma relação industrial como trajeto logístico físico confirmado.

## Pesquisa primária revisada em 18/11/2026

| ID | Afirmação adequada | Fonte primária | Recorte e ressalva |
|---|---|---|---|
| chip-tsmc | A TSMC informa que, em 2025, processos de 7 nm ou mais avançados representaram **74% da receita da própria TSMC com wafers**. | [TSMC 2025 Annual Report](https://investor.tsmc.com/static/annualReports/2025/english/index.html) | **NÃO** é 74% dos chips mundiais. Sem métrica para `90% dos chips do planeta` no roteiro atual. |
| chip-asml | A ASML se descreve como a única fabricante atual de sistemas comerciais de litografia EUV. | [ASML 2025 Annual Report, Strategic Report](https://ourbrand.asml.com/m/8ab959d4926657b/original/asml-2025-annual-report-strategic-report-section.pdf) | EUV é um sistema específico; não dizer que ASML fabrica `todas as máquinas de chips`. |
| chip-bis-2022 | O BIS introduziu controles sobre certos chips de computação avançada e equipamentos para fabricar semicondutores voltados à China em **7/10/2022**, com prazos diferentes por tipo de restrição. | [BIS 2022 announcement](https://media.bis.gov/press-release/commerce-implements-new-export-controls-advanced-computing-semiconductor-manufacturing-items-peoples) | Data e categorias são fatos históricos; não concluir que qualquer produto ou transação seja proibido. |
| chip-bis-2026-jan | O BIS anunciou em **13/01/2026** análise de pedidos de licença caso a caso para certos semicondutores, incluindo Nvidia H200 e AMD MI325X, condicionada a requisitos. | [BIS Jan 13 2026](https://www.bis.gov/press-release/department-commerce-revises-license-review-policy-semiconductors-exported-china) | NÃO generalizar para todas as restrições, nem tratar como liberdade irrestrita. Reavaliar perto da produção. |
| chip-bis-2026-nov | O BIS publicou em **16/11/2026** regra sobre acesso remoto a capacidade computacional americana avançada. | [BIS Nov 16 2026](https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology) | Tema de atualidade, sujeito a alteração. Pode entrar somente com data e contexto; não é obrigatoriamente gancho. |

**Correção do fixture legado:** `src/v4/formatos/planos/reuso/atlas_chips.json` usa tempos **sintéticos**, afirma `Taiwan fabrica mais de noventa por cento` sem delimitar mercado/fonte e narra restrições a partir de 2022 sem contexto atual. Considerá-lo **fixture de geometria e componentes**, não versão factual pronta. Ele não foi modificado neste passo para preservar o teste de regressão. Futuro plano narrado terá fatos editados e âncoras temporais recalculadas com a voz.

## A biblioteca de acervo relacionada

Em `atlas-biblioteca-20261118` existe `midias_candidatas_chips.json`: TSMC Fab 18 (Taiwan), ASML sede (Holanda), SMIC fábrica (China), wafer (genérico), NASA sala limpa (genérico), contêineres ASML em Tainan. **Ainda todas candidatas**, sem atribuição final e liberação editorial. Não usar fotos com legendas falseadas: sede ASML NÃO é máquina EUV; contêineres em Taiwan NÃO provam equipamento dentro; NASA NÃO é interior da TSMC.

O vídeo IBM `How EUV lithography works.webm` está no Commons com **License review needed**, portanto não entrar no motor até revisão jurídica/autoridade sobre a licença. Imagens oficiais da ASML podem ter direitos reservados. Se faltar foto livre da máquina, usar mapa e card factual sem simular uma foto como se fosse real.

## Storyboard planejado — APENAS composições ATLAS já existentes

| Bloco | Tempo relativo* | Palco/gramática | Prova visual exigida |
|---|---|---|---|
| 1. Gancho | breve | `atlas.abertura` | Foco real em Taiwan no mapa; pergunta curta; nenhuma imagem fictícia |
| 2. Taiwan | curto | `atlas.protagonista` + pino/foto | TSMC em Tainan; distinguir sede/filial, localização correta |
| 3. Cadeia global | médio | `atlas.protagonista` + rotas de **dependência**, não transporte real | EUA ↔ Holanda ↔ Taiwan, etiquetas mínimas; câmera abrange relações |
| 4. ASML e EUV | curto | `atlas.painel` | Dado com fonte, foto da sede devidamente identificada ou sem foto; **não** mostrar máquina errada |
| 5. Restrições e China | médio | `atlas.protagonista` + `editorial.timeline` autorizado no catálogo | Mapa da China/EUA, datas 2022/2026 atribuídas, distinção jurídica |
| 6. Síntese | curto | `atlas.escada` ou `atlas.manchete` | Projeto / equipamento / fabricação em ordem, sobre mapa; evitar encaixar tudo ao mesmo tempo |

*Não fixar segundos sem a narração real. Contrato do ATLAS exige sincronia de voz, safe areas, papel/cores, créditos, áudio e ritmo.

## Portões antes de rodar nova renderização

1. Checar cada fato e frase contra a fonte com escopo temporal; fiscal **bloqueia** extrapolação.
2. Atribuir cenas a composições e pins já aprovados (mesma estética do Panamá).
3. Conferir se rotas denotam **relações** e não movimentos físicos fictícios.
4. Fotografias somente depois de baixar, hash, validação de conteúdo/licença e crédito; não relaxar o motor.
5. Narração real e tempos reais antes de aprovar plano publicável; teste de reuso pode usar tempos sintéticos **somente como teste**.
6. Prévia privada, inspeção do MP4, sem publicação/merge na produção.

**O verdadeiro teste é conseguir um vídeo completo e profissional de um assunto distinto sem mudar a gramática do ATLAS.**

## Resultado técnico do primeiro teste de reuso (GitHub Actions 44370810497)

- `86` testes Python aprovaram; preflight `23/23`, sem falhas; `27` quadros renderizados, **zero erros bloqueadores**.
- Apareceram `81` avisos `A-CREDITO-RODAPE` (27 quadros × TikTok/Reels/Shorts): **os créditos localizados no rodapé podem ficar atrás das interfaces**. Isso **não** é prova de que a legenda se sobrepõe ao crédito; é uma advertência de interface.
- Nesta fixture específica só entram bases **Natural Earth**, cujo manifesto (`motor4/formatos/dados/atribuicoes.json`) declara **domínio público/atribuição não obrigatória**, então os 81 avisos são de **visibilidade editorial de crédito de cortesia**, não 81 violações confirmadas de licença. Situação muda com OSM, EOxCloudless ou fotos CC BY/CC BY-SA.
- Preservar a posição baixa já aprovada **até inspecionar os quadros nas interfaces reais**, e prever atribuição obrigatória devidamente acessível no vídeo ou na descrição conforme licença/plataforma. Não mascarar o problema com um falso `100% aprovado`.
- Teste feito com **voz sintetizada de teste**, não narração do vídeo final; os fatos do plano legado não estão aprovados editorialmente.
- Revisão de workflow posterior (`6d11ae5e`): os artefatos passam a preservar **somente folhas e relatórios**, evitando ocupar cerca de 150MB com cada quadro e cada máscara duplicados.


## Fotografia real no teste experimental (18/11 — após auditoria visual)

O segundo teste cartográfico estava tecnicamente verde (34 quadros, zero bloqueadores em `44379818856`), mas a auditoria direta da folha `styleframes.jpg` revelou **ausência de evidências fotográficas** e excesso de composições mapa + card. Para corrigir usando o **catálogo visual existente**, o plano em `atlas_chips_factual_2026.json` passou a conter:

1. **TSMC Fab 18, Tainan** — `commons:TSMC_Fab_18_May_2025.jpg`, retrato real ancorado nas coordenadas da fábrica em Taiwan; autor `4300streetcar`, CC BY 4.0, [página do Commons](https://commons.wikimedia.org/wiki/File:TSMC_Fab_18_May_2025.jpg). *Mostra exterior do complexo, não a capacidade ou percentual de fabricação.* Exibir no início da explicação sobre TSMC, sem cobrir o card dos dados.
2. **Wafer de silício em close** — `commons:Silicon_wafer_close_view.jpg`, foto real ilustrativa, autor `Le hollandais volant`, CC BY 4.0, [página do Commons](https://commons.wikimedia.org/wiki/File:Silicon_wafer_close_view.jpg). *Não implica origem, fabricante, modelo ou processo de fabricação de um chip específico.* Exibir dentro de `atlas.tecnica` + `dossie.documentCard`, **estilo registro, inclinação 0**, durante a palavra `wafers`, com indicação explícita de foto ilustrativa e créditos.

**A integridade do binário é verificada pelo SHA256 da miniatura aprovada de 960 px**, registrada em `src/v4/biblioteca_comprovada.json` **somente nesta branch**; os hashes foram coletados na execução do Commons `44380034537`, que verificou também as licenças. A miniatura foi escolhida deliberadamente para um uso pequeno em quadro, não como filmagem full-HD. Os originais de 21+ MB não são necessários para o retrato circular; se futuramente usar a foto grande, será preciso baixar e auditar o binário ORIGINAL separadamente.

Imagens candidatas que **não** entraram no teste: sede ASML (não é scanner EUV), placa noturna SMIC, sala limpa antiga NASA, contêineres ASML em Taiwan (não comprovam conteúdo). Não encaixar mídia só para aumentar a contagem de fotos.

Aprovação: **prévia privada experimental apenas**. O usuário ainda não aprovou o novo MP4 e não houve liberação para publicação. Créditos precisam ser conferidos dentro das plataformas; CC BY 4.0 requer licença, autor, fonte e indicação de adaptação/re-enquadramento (no vídeo e/ou descrição conforme exigências). O controle de origem falha fechado se o conteúdo mudar.

### Próxima validação

Workflow `.github/workflows/atlas-chips-reuso.yml` exige que ambas as imagens sejam **realmente baixadas e usadas**, com `origem_conferida=True`, licença CC BY 4.0 e dimensões coerentes. A conferência de quadros deve identificar possíveis conflitos entre o mapa, foto circular da fábrica, foto editorial do wafer, legendas e fontes. Não substituir inspeção humana por CI verde.
