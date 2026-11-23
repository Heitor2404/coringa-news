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
