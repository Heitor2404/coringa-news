# E7 — Importação genérica de geometria mecânica licenciada, com prova de solver e vídeo privado

**Data:** 23/11/2026 · **Branch:** `atlas-direcao-visual-20261118`
**Status:** primeiro conversor **automático de fonte geométrica estruturada → MechanismSpec do solver comum**, com sucesso em 3/5 fontes. **NÃO** é compreensão autônoma de máquina a partir de texto/vídeo, não é CAD industrial, não é publicação.

## Descoberta e decisão arquitetural

E4 descobria textos; E5/E6 distinguiam conexões sem montar uma geometria. Em vez de inventar coordenadas a partir de frases curtas, a E7 buscou uma fonte em formato estruturado de geometria: **[Linkage Design](https://github.com/jackhale98/linkage_design)**, repositório aberto **MIT**, que disponibiliza exemplos com:
- `[points]` — coordenadas com `length_unit=mm`;
- `[lines]` — geometria das barras e ranhuras;
- `[bodies]` — associação das linhas a corpos rígidos;
- `[joints]` — tipo e extremos por ponto ou ranhura, inclusive `pin_in_slot`;
- `[constraints]` — comprimentos, ângulos e colinearidade independentes;
- `[driver]` — corpo/linha acionada, RPM, sentido e varredura.

A interface é **por dados**, e não por nome de mecanismo: nenhum `if` procura `quick-return`, `slider-crank` ou `four-bar` para escolher fórmula/compositor. Ao contrário de E1/E2, as distâncias, ângulos iniciais, pontos e juntas **não foram preenchidos manualmente por nós**: foram convertidos de CSV preexistente criado por outra equipe. Os *shapes* SVG, como largura ilustrativa de barras, são uma apresentação criada automaticamente e não dimensões reais fornecidas no arquivo.

**Referência externa congelada:** `jackhale98/linkage_design` commit `c1ae13b040213b55ece567418bc14e4d2c8d1b0f`. Licença MIT verificada por Git blob SHA-1 `c9582739f2438eacbc6984f8002e3289e3b1f9db`; o arquivo original e reconhecimento autoral são mantidos no artifact. Os arquivos de exemplo foram consultados por `raw.githubusercontent.com`, usando exclusivamente revisão, caminho e hashes listados no `benchmarks/e7_open_geometry_sources_v1.json`; rejeita origem móvel/redirecionada e hash divergente. **Não** copiamos imagens, vídeos nem código de renderização de terceiros.

## Código entregue

- `src/v4/formatos/importador_geometria_e7.py` — leitor CSV por seções com validação de unidade, pontos, linhas, posições iniciais, dimensões e restrições fonte; converte `revolute→pin` e `pin_in_slot→slot` do solver E1 **sem declarar suporte a outro tipo**. Identifica corretamente `ground`, a linha-guia construtiva (infinita) e o rasgo de peça (finito). Verifica em **todos os quadros** se o pino permanece dentro de um rasgo físico com comprimento efetivo, em vez de simplesmente satisfazer a equação de linha infinita. Converte RPM em rad/s. Bloqueia grau de liberdade singular, contato composto não suportado e velocidade incompatível com o solver.
- `src/v4/formatos/solver_restricoes_e1.py` e `renderer_corpos_e1.py` — somente extensão de **primitiva de desenho** `slotted_link`, sem motor físico novo. A câmera deixou de forçar mínimo artificial de 1 m, que deixava os mecanismos reais em milímetros minúsculos; agora enquadra **a amplitude completa da trajetória**, com margem relativa, sem cortes. Marcadores de junta usam **raio em pixels**, não valor físico fixo de 45 mm. O rasgo tem canal visual ilustrativo e o pino é marcado sobre o movimento, sem alegar tolerância industrial ou desenho CAD. Mesmos componentes para todos os mecanismos.
- `tests/test_importador_geometria_e7.py` — verificações de contrato fonte, licença, revisão, redirecionamentos, dimensões conflitantes, pivôs sem corpo, rasgo finito, manipulação de CSV, duplicidade e câmera sem corte.
- `.github/workflows/qa-importacao-geometria-e7.yml` — baixa fonte/licença no GitHub Actions, executa regressões E1/E2, converte cinco exemplos, gera MP4 privado com renderer comum e confere física, timings, codec, frames, hash e folha de contato.

## Resultado REAL medido

**Run final** [GitHub Actions **45241614038**](https://github.com/Heitor2404/coringa-news/actions/runs/45241614038), **SUCCESS, 38 testes PASS** na suíte E7+E1+E2 selecionada. Regressões independentes do renderizador comum: E1 [45241485909](https://github.com/Heitor2404/coringa-news/actions/runs/45241485909) **SUCCESS** e E2 [45241485413](https://github.com/Heitor2404/coringa-news/actions/runs/45241485413) **SUCCESS**.

**Artifact privado:** `lab-e7-source-geometry-mit-private-mechanism`, ID **14852920080**, expira **28/11/2026 18:45:39 UTC**. Foi baixado e inspecionado. Arquivos incluem os JSONs de QA, `quick_return_E7_SPEC.json`, `four_bar_E7_SPEC.json`, `slider_crank_E7_SPEC.json`, vídeo do mecanismo de retorno rápido, quatro frames, quadro de contato, licença MIT e atribuição.

| Origem CSV | Status | Motivo |
|---|---|---|
| `quick-return.csv` | **PASS** | 2 corpos, 3 juntas, geometria original, full-rank, pino em rasgo finito |
| `four-bar.csv` | **PASS** | Geometria de barras e quatro pivôs convertida sem caso especial |
| `slider-crank.csv` | **PASS** | Biela e pino em guia convertidos pela mesma estrutura |
| `scotch-yoke.csv` | **BLOCKED** | RPM 600 acima dos limites explícitos de acionador do laboratório; não foi testada trajetória nessa velocidade |
| `gears.csv` | **BLOCKED** | Pares compostos de engrenagem + rack não equivalem ao pequeno contrato E1/E2 suportado |

**MP4 real final:** `QUICK_RETURN_E7_PRIVATE.mp4`, **2 s, 540×960, 18 fps, sem áudio, privado**, SHA256 `ec9ed94c88d2e48d49145a67e25b15dfdfab6c3517a07c299dc42ce205303693`. Compilado a partir da `MechanismSpec` E7 usando exclusivamente `renderer_corpos_e1.py`.
- Geometria do CSV com **6 constraints numéricas checadas**, **3 juntas**, **181 quadros físicos amostrados**, resíduo máximo ≈**4,16×10⁻¹⁷ m** e Jacobiano de posto completo, pino dentro da fenda em toda a trajetória.
- Avaliação do movimento de saída em **361 amostras**: ida/volta com razão temporal **1,7273**, confirmando característica de retorno rápido. Isso sustenta o contrato cinemático do desafio `whitworth` da lista congelada de 12 sem reutilizar vídeo pré-gravado ou solver especial. É um **piloto candidato a nível 3**, ainda sem revisão técnica externa nem visual independente.
- Primeira imagem real rejeitada visualmente: barra pequena porque câmera aplicava `span>=1 m`; revisão genérica removeu esse erro e a última folha de contato mostra alavanca ampliada, pino e canal do rasgo legíveis, sem câmera itinerante ou peças cortadas.
- **Estética ainda NÃO HOMOLOGADA**: é um diagrama cinemático abstrato, não uma representação convincente de máquina industrial pronta para reels. Não incluir como vídeo de publicação.

## Contagem honesta de capacidade

**Antes:** 3 dos 12 desafios congelados numericamente demonstrados com parâmetros escritos manualmente (quatro barras, Scotch yoke e pinhão-cremalheira), zero fonte→spec automática.

**Agora:** 3 arquivos de origem externa estruturada convertidos e animados matematicamente por um mesmo solver; desses, **quick-return** é um quarto desafio distinto candidato ao nível 3 (`whitworth`). O reuso do `four-bar` e `slider-crank` NÃO são novos mecanismos do benchmark, e a conversão de `scotch-yoke` deste CSV específico está bloqueada. Pontuação provisória: **4 desafios com demonstração cinemática no laboratório** (3 antes e 1 novo), mas somente **1 deles recém demonstrado de fonte estrutural externa**, ainda SEM análise visual independente. Formalizar essa atribuição com auditoria externa em vez de declarar 4/12 como taxa universal.

**O que NÃO foi feito:** procurar automaticamente entre múltiplos repositórios por um tema genérico; extrair do nada a montagem a partir de prosa/foto/vídeo; identificar dimensões sem uma fonte estruturada; converter CNC/STEP nativo/FreeCAD; solver com forças, contato intermitente ou montagem 3D; validar industrialmente a largura do rasgo; comprovar licença de imagens adicionais; postar. Os exemplos CSV foram **modelados previamente por terceiros**, e o motor apenas converteu o formato documentado, com procedência e recusa.

## Próxima fase E8

1. Acrescentar **descoberta por tema→fontes de geometria verificadas** (não somente CSVs de um repositório fixo), respeitando licença e hashes antes de importar; medir taxa de fontes insuficientes/ruins, não aceitar download genérico de código executável.
2. Fazer auditoria independente do **Whitworth** e dos desenhos em movimento, incluindo travessia de peças, proporção, câmera e contato de rasgo; exigir revisão por máquina que **não foi** usada para calibrar o importador, sem editar o benchmark congelado.
3. Aumentar capacidade do solver **por tipos reutilizáveis de contato**, não por nome: suporte verificado a contato de came, engrenagens compostas, contato intermitente com bloqueio/retomada, ou recusa explícita quando sem física.
4. Evoluir o compositor geral para corpos com espessura, pivôs, bases e detalhes industriais proporcionais às evidências; preservar dados físicos separados de decoração e a legibilidade de 9:16.

**Continuidade:** registrar seção 135. **Isolamento:** `main`, NTC, DOSSIÊ, Telegram e produção do canal não alterados nesta fase.
