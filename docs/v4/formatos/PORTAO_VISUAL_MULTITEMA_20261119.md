# Contrato visual transversal — fase 1 (19/11/2026)

**Objetivo:** encerrar o ciclo de microcorreções em vídeos específicos (Panamá) e construir um portão que reconheça o mesmo defeito, independentemente do tema e do compositor.

**Branch experimental:** \`atlas-direcao-visual-20261118\`. Não alterar \`main\`, \`motor-integral-v4\`, NTC, DOSSIÊ nem publicar.

## Implementação feita (código em execução, não apenas projeto)

- \`src/v4/formatos/contrato_visual_comum.py\`: adapta contratos ATLAS e \`filme_editorial\` a um vocabulário único de intenção, referente, aprendizado, suporte e etapas esperadas. Verifica se o roteiro declara o objeto e a prova e se as ações esperadas estão programadas em ordem. **Não transforma metadata ou mudança de pixels em comprovação de narrativa.**
- A mesma rubrica \`criterios\`/\`julgar_inspecao\` é usada por \`src/v4/formatos/revisao_visual.py\` (ATLAS, já existente) e \`src/v4/formatos/revisao_filme_editorial.py\` (novo). O último extrai amostras da mídia real por etapa, envia duas imagens por inspeção a uma interface de visão injetável e falha fechada quando imagem/modelo indisponível.
- \`src/v4/formatos/triagem_editorial.py\` e \`src/v4/formatos/filme_editorial.py\` agora reportam \`contrato_comum\` e incorporam suas falhas estruturais no gate especializado. Nenhum gate anterior foi rebaixado.
- Contratos com \`estados_esperados\` (FILME) ou \`direcao_visual.etapas_esperadas\` (ATLAS) recebem cobertura estrutural de ação em ordem. Sem expectativas explícitas => **NÃO MENSURADO**, nunca 100% inventado. O Panamá de 19s recebeu somente a lista de sete estados esperados no JSON **sem alterar ou renderizar o episódio**.
- \`tests/test_contrato_visual_multitema.py\`: regressões positivas e negativas com Panamá, Taiwan FILME, Taiwan ATLAS legado e gabarito Hindenburg. Os testes de resposta VLM são *dublês programados*: avaliam comportamento do portão, **não** qualidade real das imagens.
- Workflow \`.github/workflows/qa-contrato-visual-multitema.yml\` executa análise offline, sem render, sem TTS, sem Gemini e sem Telegram. Artifact \`qa-contrato-visual-compartilhado-tres-temas\` com relatório independente.

## Resultado reproduzível: GitHub Actions 44542614237

**SUCCESS — 37 testes passaram em 0,79s.** Verificação cruzada:

| Caso | Estrutura | Ações esperadas/programadas | Veredito visual | Aprovação humana |
|---|---|---|---|---|
| Panamá, FILME 19s | válido (2 compromissos, 2 suportes declarados) | 1/1 | NÃO INSPECIONADO nesta rodada | PENDENTE |
| Taiwan, FILME | válido (6 compromissos, 6 suportes declarados) | 0/0 — não declarado | NÃO INSPECIONADO | PENDENTE |
| Taiwan, ATLAS legado | BLOQUEADO (0/6 suportes declarados resolvidos pelo contrato; falta direção) | 0/0 | NÃO INSPECIONADO | PENDENTE |
| Hindenburg | 6 cenários **hipotéticos** de correspondência entre acontecimento e imagem; não são vídeo real | N/A | NÃO INSPECIONADO | PENDENTE |

Dois runs anteriores \`44542442950\` e \`44542467192\` falharam na configuração do YAML (dois-pontos não escapados em nome de etapa); corrigido. O run final \`44542614237\` executou testes e gerou o artifact esperado.

## Interpretação obrigatória

- **Nenhuma pontuação dos três temas comprova melhoria estética.** Um teste verde aqui prova que os *mesmos portões* funcionam em formatos e dados diferentes, e que não foi concedida aprovação humana fictícia.
- A regressão Hindenburg testa recusa de prova falsa/incompatível e classificação de registro hipotético; não valida imagens reais nem vídeo do desastre.
- A passagem de roteiro → compositor ainda depende de curadoria/roteiro; a presença de \`acao\` no JSON não prova que o objeto efetivamente executou essa ação na imagem. Só a inspeção do MP4, preferencialmente multimodal e depois humana, pode verificar isso.
- O revisor FILME foi preparado e testado **sem consumo de IA** por injeção de respostas; não foi executada revisão real de 7 ações via modelo nesta rodada.

## Próximo gate que realmente mede generalização

1. Obter **três MP4s reais** em domínios diferentes (engenharia, indústria, acontecimento histórico), mantendo versões anteriores como baseline de cada tema. Não escolher cenas por estarem bonitas.
2. Para cada acontecimento/beat: registrar objeto, ação esperada, mídia real, tempo do vídeo, e dois ou mais quadros em que o objeto deveria mudar.
3. Rodar **exatamente o mesmo** contrato e o revisor real, sem exceções por tema. O fiscal deve distinguir:
   - ação visível vs legenda prometendo ação;
   - foto literal vs representativa e origem/licença;
   - enquadramento seguro com objeto protagonista;
   - progressão causal e conclusão de cada beat;
   - reprovação clara quando não há prova.
4. Medir falsos positivos/falsos negativos contra **avaliações humanas por beat** (não score de pixels ou número de testes). Registrar tempo/custo total da revisão.
5. Só promover uma correção à arquitetura compartilhada se melhorar pelo menos dois domínios não relacionados sem piorar o terceiro; manter CI com ambos antes/depois. Corrigir excepcionalmente um tema no seu adaptador, nunca com regra global disfarçada.

**Decisão:** parar novas V6/V7 Panamá; próxima rodada é avaliação visual *real* cruzada, com vídeos variados e fontes verificadas, não uma nova animação exclusiva.
