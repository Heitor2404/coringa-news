# E7 — geometria estrutural licenciada → solver 2D genérico → MP4 privado

**Data:** 23/11/2026. **Branch:** `atlas-direcao-visual-20261118`. **Status:** prova técnica aprovada, visual NÃO homologado e produção NÃO integrada.

## Motivação e descoberta

Após E3–E6, a busca textual conseguia citar relações, mas NÃO fornecer corpos, pivôs, posições, dimensões e restrições completos para um `MechanismSpec`. E7 abre **uma segunda rota de dados**: mecanismos existentes como geometria **estruturada**, sem atribuir a uma IA a criação automática das dimensões.

Referência externa identificada: [jackhale98/linkage_design](https://github.com/jackhale98/linkage_design), versão congelada no commit **`c1ae13b040213b55ece567418bc14e4d2c8d1b0f`**, licença **MIT** conferida. Possui arquivo CSV versionado `LinkageDesign,1` com `[points]`, `[lines]`, `[constraints]`, `[bodies]`, `[joints]`, `[driver]`, entre outras seções. Arquivos são **exemplos geométricos produzidos por terceiros**, não dados medidos de uma máquina industrial específica, nem resultado de pesquisa→spec por texto puro. O script de importação inclui cópia da licença MIT e atribuição no artifact privado.

Manifesto congelado `benchmarks/e7_open_geometry_sources_v1.json`: os cinco CSVs foram identificados previamente e têm SHA Git blob, URL baseada em commit fixo e licença. Sem troca automática por novas versões ou URLs arbitrárias. O manifesto de 12 alvos de generalização existente **não foi alterado**.

## Código implementado

- `src/v4/formatos/importador_geometria_e7.py`:
  - Busca HTTPS em host fixo `raw.githubusercontent.com`, revisão exata e paths restritos; confere SHA Git blob de CSV e licença; não executa o conteúdo externo.
  - Lê CSV em seções, valida pontos e linhas, unidades `mm/cm/m/in`, distâncias, ângulos, vertical/horizontal, `point_on_line`, midpoint, corpos e âncoras. Rejeita geometria que não satisfaz as restrições declaradas.
  - Traduz `revolute`→`pin` e `pin_in_slot`→`slot` do **mesmo solver E1**, convertendo posições mundiais de origem em âncoras locais de cada corpo. Não há roteamento por título do mecanismo. `[pairs]` de alta ordem não são reinterpretados ficticiamente como `pin`.
  - Distingue rasgo finito em corpo móvel de **linha construtiva de guia** (sem batentes físicos declarados): para rasgos finitos, todos os frames passam por verificação independente de que o pino está dentro do segmento, e não apenas na reta infinita.
  - Reusa `S.trajectory`, rejeitando má convergência, singularidade e saltos. Não importa forças, inércia ou valida CAD industrial.
- `src/v4/formatos/solver_restricoes_e1.py`: admite `slotted_link` **somente como forma gráfica genérica**, sem novo núcleo físico.
- `src/v4/formatos/renderer_corpos_e1.py`: removeu a antiga escala mínima artificial de **1 metro** da câmera, que miniaturizava máquinas de 300 mm. Enquadramento agora usa limites reais de toda a trajetória com folga proporcional; pinos têm tamanho fixo em pixels. Primitiva reutilizável `slotted_link` desenha **canal visível**, e o pino deslizante é desenhado em todos os modelos com juntas `slot`. Nenhum compositor com `if` para retorno rápido.
- `tests/test_importador_geometria_e7.py`: adversariais de alteração de SHA/licença, dados incorretos, tipo de junta não suportado, rasgo físico finito, título renomeado, escala e área segura, mais regressão E1/E2.
- `.github/workflows/qa-importacao-geometria-e7.yml`: execução sem modelos pagos, busca LIVE dos arquivos congelados, prova de geometria, MP4 do mesmo renderer, FFprobe/sha, quadro de contato e teste independente da assimetria de tempo de ida/volta.

## Verificação final

[GitHub Actions **45241614038**](https://github.com/Heitor2404/coringa-news/actions/runs/45241614038): **SUCCESS — 38 testes aprovados**, todos os passos de busca, importação, render e QA verdes. Artifact `lab-e7-source-geometry-mit-private-mechanism`, ID **14852920080**, expira **28/11/2026 18:45:39 UTC**. ZIP extraído; quadros reais visualizados e vídeo identificado por SHA.

| Fonte estruturada | Resultado da conversão |
|---|---|
| `quick-return.csv` | **PASS**, geometria de origem, 181 estados, juntas e rasgo finito |
| `four-bar.csv` | **PASS**, 181 estados |
| `slider-crank.csv` | **PASS**, 181 estados |
| `scotch-yoke.csv` | **BLOCKED_E7-FONTE-VELOCIDADE**: velocidade da fonte 600 rpm supera limite do importador, NÃO é uma reprovação da cinemática intrínseca |
| `gears.csv` | **BLOCKED_E7-FONTE-CONTATO_COMPOSTO_NAO_SUPORTADO**: exige engrenamento superior/composto, ainda não disponível no importador |

**Retorno rápido:** sua estrutura foi derivada do CSV da fonte, com 3 juntas (2 pinos + 1 rasgo), 2 corpos móveis, 6 restrições geométricas originais e acionamento a 30 rpm. Geometria aceita pelo solver comum sem template próprio. Os extremos do balancim foram detectados nos índices 174 e 306 de uma volta de 360 amostras; a relação dos tempos de percurso mais longo/mais curto foi **1,7272727273×**, comprovando assimetria cinemática. A verificação confirma também que o pino não excedeu os extremos do rasgo finito na trajetória amostrada.

**MP4 real privado:** `QUICK_RETURN_E7_PRIVATE.mp4` (540×960, 18fps, sem áudio), SHA256 **`ec9ed94c88d2e48d49145a67e25b15dfdfab6c3517a07c299dc42ce205303693`**. `QA_E7_VIDEO.json`, `QUICK_RETURN_E7_CONTATO.jpg`, quatro quadros e licença MIT estão no artifact.

**Inspeção visual REAL:** a máquina agora ocupa bem mais da área útil que na primeira versão E7, sem recorte de peças; pino e rasgo são visíveis. Porém o conjunto continua como **ilustração técnica simplificada**: barra longa com canal, manivela linear, pouco contexto de montagem, nenhuma aparência industrial, nenhuma direção de câmera narrativa. **VISUAL REPROVADO para publicação** (o código de QA diz `visual_approved=false`). A correção não constitui aprovação do ATLAS nem do estilo final desejado.

## O que efetivamente mudou no projeto

Este experimento importa uma geometria completa **que já estava descrita por terceiros em formato de engenharia estruturado**, monta um `MechanismSpec` e resolve/renderiza pelo solver/compositor compartilhados. É uma ponte reusável, **não** prova de que o motor encontre sozinho arquivos para qualquer tema, compreenda CAD, deduza geometria de vídeo, explique uma peça sem dimensões ou represente dinâmica/contato de máquinas reais. A fonte técnica está licenciada MIT, com atribuição mantida; não se inferiu licença para outras ilustrações externas.

O retorno rápido (`whitworth`) é **mais um alvo** do benchmark congelado resolvido a partir de dados externos estruturados. **Placar provisório de topologias demonstradas: 4/12**, contando quatro barras, Scotch yoke e pinhão-cremalheira anteriores com specs manuais, e retorno rápido com **spec importada de CSV externo**. Esse resultado **não equivale a 4/12 autônomos**. Os outros oito alvos permanecem não demonstrados; nenhum holdout mecânico foi solucionado e zero artes aprovadas. Scotch yoke já havia passado com spec manual em E1, mas **a importação E7 desse arquivo específico foi bloqueada** — resultados distintos.

## Próxima etapa E8 recomendada

1. Generalizar ingestão de formatos abertos de CAD/desenhos dimensionados, mantendo direitos, unidades, procedência de cada restrição e rejeição por insuficiência. Não usar engenharia de máquinas de terceiros como um conjunto de templates por título.
2. Abordar velocidades externas acima do limite de amostragem do protótipo com **resampling de tempo declarativo** e teste de preservação de trajetória, sem mascarar velocidades reais ou forçar um resultado fisicamente incorreto.
3. Validar um mecanismo **não utilizado para desenhar o adaptador**, com geometria importada, oráculo independente e observação real de animação.
4. Separar direção de arte geral: formas mais inteligíveis, foco em peças que interagem, narrativa visual, câmera estável, aproveitamento da área dos Reels, sem importar o antigo visual rejeitado.

**Proteção:** branch experimental apenas. `main`, NTC, DOSSIÊ, Telegram, pipeline documental de produção e publicação não alterados. Nenhuma API paga invocada pelo código E7.
