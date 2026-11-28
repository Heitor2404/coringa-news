# Experimento E0/E1 — baseline 12 + solver genérico 2D em laboratório

**Data:** 23/11/2026 · Branch: `atlas-direcao-visual-20261118` · **Estado inicial:** código enviado, validação CI pendente (não declarar acerto antes do resultado).

## Mudança de arquitetura que está sendo testada

Não acrescentar novos `if family==...` ao solver. `solver_restricoes_e1.py` recebe uma especificação de corpos rígidos planos em **metros**, poses iniciais, juntas `pin` (2 equações), `slider` (2), `slot` (1) e um acionador angular (1). As mesmas equações e a mesma biblioteca SciPy resolvem um sistema de restrições não lineares em cada instante. Verifica máximo resíduo, rank do jacobiano e continuidade de ramo. É cinemática, não dinâmica nem CAD/contato complexo.

Um único `renderer_corpos_e1.py` recebe as poses calculadas e desenha barras/discos em SVG, convertendo metros em pixels **somente na câmera global fixa** do vídeo. Títulos e acabamento são didáticos e *não aprovados* para os canais.

**Três especificações declarativas, sem física por nome:**
1. `benchmarks/specs_genericas_e1/oraculo_biela_e1.json`: manivela de 0,35 m e biela de 1,2 m, pino + slider; a referência independente é `cinematica_biela_manivela.calcular` F7 com escala 100 px/m e translação apenas nos testes.
2. `benchmarks/specs_genericas_e1/quatro_barras_e1.json`: quatro juntas rotativas, elo de entrada 0,7 m, acoplador 2,0 m, balancim 1,65 m e distância de 2,2 m entre pivôs fixos. Verificar fechamento em 360° e oscilação de saída.
3. `benchmarks/specs_genericas_e1/scotch_yoke_e1.json`: manivela de 0,65 m, cursor prismático e pino em rasgo; trajetória de x deve coincidir com seno de 0,65 m de amplitude.

## Benchmark congelado

`benchmarks/generalizacao_mecanismos_v1.json` foi escrito ANTES deste solver. Não editá-lo para facilitar pontuação. `benchmarks/probes_f15_v1.json` traz 12 pequenos grafos **codificados manualmente**, não extraídos por IA ou de fontes reais; `benchmarks/rodar_baseline_f15_e0.py` passa todos pelo `F15.identify` original e registra explicitamente aceitação/recusa. O baseline só mede **admissão estrutural**, e `score_ge_3=0` significa *nenhuma trajetória/renderização conferida pelo sistema antigo neste ensaio*, não que sua geração geral seja intrinsecamente impossível.

## Critérios de aprovação da experiência E1

- 121 poses de cada mecanismo com resíduo inferior a 1e-8 m, jacobiano de rank pleno e sem salto de ramo grande.
- Biela do solver genérico coincidir com oráculo F7, não com uma fórmula escrita apenas para passar.
- Quatro barras fechar juntas ao longo de uma volta e apresentar oscilação contínua do balancim.
- Scotch yoke seguir movimento senoidal pela geometria do pino/rasgo.
- Todos os três renderizados pelo MESMO código, sem nomes de mecanismos no solver.
- Nenhum vídeo ou arte aprovada para publicação; não há contato de came, catraca ou corrente, 3D, ingestão automática, direitos de imagens externos, nem QA real de aplicativos.

**Workflow:** `.github/workflows/qa-solver-generico-e1.yml`. Produz baseline JSON, métricas e três vídeos MP4 540×960/18 fps/6s, com folha de 12 quadros. Os dois novos desafios só podem ganhar **pontuação provisória** após testes cinemáticos e renderizador comum. Não declarar 8/12, nem autonomia de construir MechanismSpec a partir de pesquisa.

**Segurança:** `main`, NTC, DOSSIÊ, Telegram, motor documental de produção e postagem INTACTOS.

## Resultado REAL, após validação (23/11 ~12h19 BRT)

**Run FINAL:** https://github.com/Heitor2404/coringa-news/actions/runs/45203474875 — **SUCCESS, 24 testes aprovados**, testes do solver e regressões F7; renderização efetiva de três arquivos MP4, QA via FFprobe, hashes conferidos, folha de 12 quadros inspecionada localmente. Primeira run `45203277422` cancelada após ajuste apenas documental; não contabilizar como falha física.

**Artifact GitHub:** `lab-e1-baseline12-solver-3-mecanismos-privado`, ID **14832389273**, expira **28/11/2026 ~15h19 UTC**. ZIP `E1_GENERIC_SOLVER_3_VIDEOS.zip` baixado (969 KiB) e extraído para auditoria, contendo `BASELINE_F15_12.json`, `QA_SOLVER_E1.json`, três MP4, 12 PNG e `COMPARATIVO_SOLVER_E1_3_MECANISMOS_12_QUADROS.jpg`.

**Baseline observado, com as 12 entradas congeladas:**
- `benchmarks/rodar_baseline_f15_e0.py` executou `compilador_topologia_f15.identify` nos 12 grafos simplificados de `benchmarks/probes_f15_v1.json` (origem de grafo **MANUAL**, não IA). **12/12 BLOQUEADOS**, zero admitidos e nenhuma renderização feita pelo motor antigo nesse ensaio; lista e motivos individuais em `BASELINE_F15_12.json`. Isto é **teste de admissão de topologia**, não prova de incapacidade matemática absoluta de representar os mecanismos caso fossem codificados novos núcleos.
- Principais motivos: `TOPOLOGIA_NAO_SUPORTADA`, `ARESTA_INVALIDA`, `NO_DUPLICADO_OU_DESCONHECIDO`. Nenhum desafio holdout foi tentado no novo solver.

**Solver E1 validado por experimentos físicos:**
- `ORACULO_BIELA_E1.mp4` — **SHA256 `019c9d293d1647a7b1b8947e2b27675e35bff5343f4b4787176889836293eafb`**, 6s, 540×960, 18fps, mudo, privado. 121 poses em metros, resíduo máximo **8,88e−16 m**, erro máximo contra fórmula F7 independente **1,11e−15 m**.
- `QUATRO_BARRAS_E1.mp4` — **SHA256 `e4efcd426c60dce821cafec65f2091976e93fa9c1d6ec9147b5aa6b21c8d5d97`**, mesmas specs. Quatro juntas rotativas fechadas, volta completa da manivela, balancim oscilando **0,9046379 rad**, residual **6,66e−16 m**, poses contínuas sem salto de ramo.
- `SCOTCH_YOKE_E1.mp4` — **SHA256 `c4a30c6df2014ce7d4d15e294253e44a3eb4e148822b917e4cd9649dabc7919c`**, mesmas specs. Junta `slot` (pino em rasgo) + `slider`; deslizamento senoidal de amplitude **0,65 m**, erro contra seno **5,55e−16 m**, residual **8,88e−16 m**.
- Os três usam exatamente `src/v4/formatos/solver_restricoes_e1.py` + `src/v4/formatos/renderer_corpos_e1.py`. Não há `if` por família; apenas corpos, poses, juntas e formas fornecidos por três JSONs declarativos. Câmara fixa calculada do conjunto de poses, unidades físicas separadas da resolução de vídeo.

**Avaliação visual humana da folha de 12 quadros:** mecanismos reconhecíveis por desenho de elos, pivôs e barras, mas deliberadamente esquemáticos, sem carcaça fiel, detalhes de fabricante, realismo 3D, materiais industriais ou composição aprovada para Coringa. No Scotch yoke, a ranhura é representada por barras de guia estilizadas; essa aparência ainda exige redesign de estética, não impacta o fechamento cinemático medido. Nas quatro barras os elos fecham no vértice oscilante. **Não publicar**.

**Interpretação correta do score:** 0/12 admissões no F15 antigo e **2 candidatos provisórios a nível 3 de 2 desafios inéditos tentados no E1** (quatro barras + Scotch yoke); **os outros 10 não foram testados pelo novo solver**, 0 aprovações visuais, 0 especificações geradas autonomamente a partir de fontes. Não chamar o resultado de "2/12 de reconhecimento de máquinas" porque as especificações são manuais. A validação matemática foi forte para as três topologias, mas não existe ainda benchmark de contatos, fontes industriais ou avaliação de qualidade profissional.

**Limitações adicionais:** o solver usa SciPy least_squares de restrições cinemáticas, não integrador dinâmico/contato. Hoje suporta pino, prismática, pino-em-rasgo e acionador angular. Não suporta atrito, impactos, colisões de contato, cames, engrenagens planetárias, corrente, sem-fim, corpos 3D ou otimização automática de configurações iniciais. Os JSONs precisam de `seed` inicial coerente informado pelo projetista; graus de liberdade e jacobiano são conferidos, mas descobrir ramo correto e especificação a partir de linguagem/imagem continua PENDENTE.

**Próximas tarefas de alta prioridade:** reforçar validador com exemplos de mecanismos sobre-restritos e variações dimensionais não triviais, testar uma terceira topologia nova SEM mudar solver/renderer e introduzir regra de design visual compartilhada, depois experimentar `MechanismSpec` construído a partir de fonte de texto com evidência por junta; medir custo e taxa de falha. Não ajustar o benchmark congelado para facilitar êxito. `main`, NTC, DOSSIÊ, Telegram e produção intocados.
