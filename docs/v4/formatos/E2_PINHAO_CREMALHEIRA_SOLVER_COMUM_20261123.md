# E2 — terceira topologia pelo solver comum 2D: pinhão e cremalheira

**Data:** 23/11/2026 · **Branch isolada:** `atlas-direcao-visual-20261118`
**Status:** validação cinemática **APROVADA**; direção de arte **NÃO APROVADA**; nenhuma integração na produção.

## Hipótese e implementação

Após E1 (oráculo de biela + quatro barras + Scotch yoke), o desafio E2 foi
`pinhao_cremalheira`, alvo já presente em
`benchmarks/generalizacao_mecanismos_v1.json` congelado ANTES do solver.
Não criar um compositor nem um solver exclusivo por nome de máquina.

- `src/v4/formatos/solver_restricoes_e1.py` recebeu **uma nova junta reutilizável**
  `rack_pinion` (1 equação), parametrizada por:
  `a,b,pa,pb,axis_b,pitch_radius_m,pitch_side,phase_m`. Idealiza
  rolamento da circunferência primitiva sobre a linha da cremalheira:
  projeção ao longo do eixo + lado × raio × (ângulo do pinhão − ângulo da
  cremalheira) − fase = 0. O solver continua usando o MESMO
  `scipy.optimize.least_squares`, matriz jacobiana, rank e continuação
  de solução E1. Independente de 540×960.
- Prova adicional de **tangência geométrica da linha primitiva** rejeita
  uma especificação que possua equação de rolamento satisfatória mas
  distância transversal incoerente. Não equivale a contato dente-a-dente
  nem forças/atrito, impactos, involuta industrial ou análise CAD.
- `src/v4/formatos/renderer_corpos_e1.py` estendeu **formas reutilizáveis**
  `gear` e `rack` a partir de `shapes` e ampliou/elevou o palco
  compartilhado. Os dentes SVG são **ilustrativos**, não cálculo involuto;
  nenhuma ramificação escolhe renderer com base em nome de mecanismo.
- `benchmarks/specs_genericas_e2/pinhao_cremalheira_e2.json` fornece
  configuração **MANUAL**, raio primitivo **0,4 m**, 20 dentes
  esquemáticos, cremalheira prismática e rotação de −π/2 a +π/2 em 6s.
  A especificação não foi construída por leitura de fontes.
- `tests/test_solver_generico_e2.py` valida relação de movimento,
  tangência, fechamento, variantes de raio/sentido/fase, rejeições
  de parâmetros, corpo com nome trocado, rank e limites visuais.
  Testes E1 anteriores continuam executados como regressão.
- `.github/workflows/qa-solver-generico-e2.yml` executa as regressões,
  produz MP4 privado do MESMO compositor, verifica o arquivo por FFprobe,
  compara frames em pixels e registra QA e folha de contato.

## Bug real descoberto e corrigido

**Primeira execução:** [Actions 45208053694](https://github.com/Heitor2404/coringa-news/actions/runs/45208053694) —
**FAIL** no QA de movimento visual, apesar de testes físicos aprovados e
MP4 renderizado. A cremalheira aparecia **parada na imagem**, embora o
solver movesse sua pose. No renderizador genérico, um laço desenhando
dentes atribuía coordenadas locais às variáveis `x,y` que deveriam
conter a pose global do corpo; isso sobrescrevia o `transform` SVG.

**Correção:** renomeadas as coordenadas locais para `tooth_x,tooth_y`;
regressão compara as coordenadas `data-pose` do SVG com a pose
calculada pelo solver; QA de vídeo passou também a exigir movimento
lateral rastreável da área amarela da cremalheira, e não apenas
qualquer mudança de pixels (como o giro da roda).

## Resultado efetivamente verificado

**Execução final** [GitHub Actions 45209167047](https://github.com/Heitor2404/coringa-news/actions/runs/45209167047) —
**SUCCESS, 37 testes passaram**, incluindo regressão E1/F7 e adversariais E2.
**Artifact** `lab-e2-pinhao-cremalheira-generico-privado`, ID
**14834632743**, expira **28/11/2026 15:48:57 UTC**. ZIP obtido, hashes
verificados, quadro comparativo aberto e examinado.

**Vídeo** `PINHAO_CREMALHEIRA_E2.mp4`, **6 s, 540×960, 18 fps,
sem áudio, privado**, SHA256:
`4a2393ce53b41698c0800db6b7dd765c2ffc2593051fb18957c103118fcc6d56`.

**Medições em 121 poses:**
- Erro máximo de rolamento ideal: **5,55×10⁻¹⁷ m**.
- Resíduo máximo de restrições: **4,44×10⁻¹⁶ m**.
- Curso horizontal da cremalheira: **1,2566370614359172 m**, correspondente a `π×0,4` para meia-volta.
- Deslocamento rastreado da cremalheira na imagem (entre dois frames amostrados): **96,92 px**; diferença RGB máxima do palco: **1,847**.
- Rank das restrições completo; mecanismo renderizado por `renderer_corpos_e1.py` com câmera fixa.

## Julgamento crítico e score correto

O **resultado mecânico E2 passou**, mas a inspeção dos quatro quadros mostra
uma ilustração didática básica: pinhão e cremalheira distinguíveis, porém
**pequenos dentro de um grande quadro claro** e sem contextualização
industrial, volumes ou detalhes de máquina real. **Estética NÃO HOMOLOGADA
para o Coringa**. O novo renderer não está preparado para publicar
documentários. Não usar o resultado como direção visual final.

E0: o compilador F15 anterior recusou 12/12 *probes* de grafo manual,
um teste de admissão e não da capacidade física de todo o código legado.
E1: 2 topologias novas testadas com specs manuais.
E2: 1 nova topologia de transmissão com spec manual.
**Cumulativo: 3 alvos diferentes do benchmark resolvidos numericamente e
renderizados pelo núcleo genérico; os outros 9 não foram tentados; ZERO
holdouts, ZERO specs provenientes de pesquisa automática, ZERO aprovação
visual e ZERO integrações em produção.** Não anunciar taxa universal de
acerto 3/12 ou autoengenharia; nível 3 segue candidato provisório.

## Próximo experimento proposto — E3

1. Incorporar proposta de `MechanismSpec` fundamentada em relações
   técnicas (F16/F17), com procedência e confiança **por junta**, mantendo
   propostas incompletas BLOQUEADAS, e medir intervenção humana.
2. Usar topologia já suportada do E1/E2 como controle, mas **sem depender de
   regra especial para título/fonte**. Registrar taxa de specs aceitas e
   reprovadas e custos reais; depois passar a um holdout permitido pelo
   benchmark sem editar o conjunto congelado.
3. Separar um passe de **direção visual geral** (composição, câmera, detalhes
   e relação imagem-física) da validação numérica. Não voltar ao antigo
   renderizador miniaturizado rejeitado.

**Isolamento:** `main`, NTC, DOSSIÊ, Telegram, motor documental de
produção e postagem preservados. Nunca promover sem prova e revisão humana.
