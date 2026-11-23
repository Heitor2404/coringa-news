# E8 — catálogo multi-repositório de geometria mecânica e avaliação inédita do importador

**Data:** 23/11/2026. **Branch isolada:** `atlas-direcao-visual-20261118`.
**Veredito cinemático parcial:** fonte aberta verificada; o adaptador CSV passou em novas topologias; não existe descoberta aberta de projeto, importador universal CAD ou direção visual homologada.

## Fonte, licença e problema

O E7 automatizou a montagem de `MechanismSpec` a partir de arquivos **CSV estruturados e com geometria pré-definida por terceiros** em apenas um repositório. A pergunta E8 foi: conseguimos **verificar duas origens independentes** e rodar novas geometrias não usadas no E7 sem acrescentar um solver, uma família de animação ou um compositor por máquina?

Foram pesquisados repositórios de mecanismos abertos. Registro `benchmarks/e8_multi_repo_catalog_v1.json` conserva dois projetos, ambos identificados por SHA de commit, blob de licença e blob do conteúdo:

1. `jackhale98/linkage_design`, commit `c1ae13b040213b55ece567418bc14e4d2c8d1b0f`, licença MIT (`LICENSE` blob `c9582739f2438eacbc6984f8002e3289e3b1f9db`). Arquivos CSV `LinkageDesign,1` com corpos, pontos, juntas e dimensões.
2. `MasoudMiM/sketch-mechanisms`, commit `46d41163a23a112e599bda808b2ef8a66981a8fc`, licença MIT (`LICENSE` blob `1fb6be5dcab13512aa3f0370888d5ef7f17ba7c1`). `README.md` documenta presets por tipo com comprimentos relativos e `reference.json` contém **amostras numéricas de trajetórias**, úteis como referências independentes, mas **não possuem os anchors, pivôs e corpos explicitamente instanciados necessários para converter automaticamente a `MechanismSpec` genérica**. Fonte alternativa licenciada **CONFIRMADA**, importação dessa origem **NÃO COMPROVADA**. Não criar manualmente um template por palavra `type:` e alegar autonomia.

Esta etapa implementa **catálogo fechado de dois repositórios encontrados por pesquisa**, NÃO um crawler universal que recebe tema e pesquisa todas as fontes existentes.

## Código e proteção

- `src/v4/formatos/triagem_fontes_geometria_e8.py`: verifica URL GitHub RAW HTTPS (host fixo), hashes de blobs, commit, texto efetivo da licença MIT e conteúdo de arquivos. Distingue `STRUCTURED_PLANAR_SOURCE` de `PARAMETRIC_PRESET_NO_EXPLICIT_JOINT_ANCHORS` e `INDEPENDENT_KINEMATIC_ORACLE_ONLY`. Snippets, nomes de arquivos, credenciais e metadados não podem gerar `MechanismSpec` nem importar arte por si só. A triagem não executa código de terceiros.
- **Bug de segurança REAL E8:** primeiro CI detectou que uma entrada de caminho começando com `..` passava na expressão regular e atingia uma tentativa de fetch. Corrigido: componentes do caminho não podem começar com ponto. A regressão exige rejeição **ANTES** do acesso externo. Não retirar essa proteção.
- `benchmarks/e8_unseen_linkage_sources_v1.json`: congela seis arquivos CSV do mesmo upstream MIT que **não estavam no benchmark de E7**: `shaper`, `hoekens`, `watt`, `pump-jack`, `knuckle-press`, `hydraulic-boom`. Hashes SHA de blob registram os bytes exatos. **Este não é o holdout do benchmark de 12**, nem desenvolvimento de CAD arbitrário.
- `src/v4/formatos/importador_geometria_e7.py` ganhou validação **GENÉRICA de paralelismo e perpendicularidade entre linhas declaradas na fonte**: produto vetorial/dot normalizados, aceita anti-paralelo, recusa pontos de origem incompatíveis e linhas degeneradas. Sem `if` por nome de máquina.
- `tests/test_triagem_fontes_geometria_e8.py` e `tests/test_importador_geometria_e7.py`: adversariais de caminho traversal, hash, licença, origem simulada não contado como live, formatos sem geometria, `parallel/perpendicular` falsificados, fonte com restrições quebradas.
- `.github/workflows/qa-fontes-abertas-e8.yml`: regressões E1/E2/E7/E8, segundo repositório consultado de fato, reimportação LIVE dos seis CSV inéditos, render privado usando o mesmo `renderer_corpos_e1.py` e avaliação de video/hashes.

## Resultados auditados e evolução

**Primeiro CI após correção de traversal:** [GitHub Actions 45269592545](https://github.com/Heitor2404/coringa-news/actions/runs/45269592545), **SUCCESS, 51 testes**, segundo repo MIT validado, 4 amostras de fontes avaliadas. Só **1/4 arquivo de amostra multi-repo** possuía geometria passível de tradução direta; os dois arquivos do projeto alternativo eram referências numéricas/presets, NÃO `MechanismSpec` completas.

**Seis arquivos congelados — primeira tentativa ANTES de acrescentar a regra genérica `parallel`:**
- `shaper.csv` — PASS, mesma física/compositor E1.
- `knuckle-press.csv` — PASS, mesma física/compositor E1.
- `hoekens.csv`, `watt.csv`, `pump-jack.csv`, `hydraulic-boom.csv` — BLOCKED inicialmente em `RESTRICAO_NAO_SUPORTADA`. Causa real observada: relação `parallel` no CSV.

**Reteste E8b APÓS implementar o recurso genérico:** [GitHub Actions 45270102478](https://github.com/Heitor2404/coringa-news/actions/runs/45270102478) **SUCCESS, 51 testes** (antes de acrescentar o teste direto da nova primitiva). Agora:
- `shaper.csv` — PASS, 4 corpos, 7 juntas, 181 poses.
- `hoekens.csv` — PASS, mecanismo de trajetória aproximadamente reta, 181 poses.
- `pump-jack.csv` — PASS, 181 poses.
- `knuckle-press.csv` — PASS, 5 corpos e 8 juntas, 181 poses.
- `watt.csv` — `BLOCKED_E7-FONTE-DRIVER_NAO_SUPORTADO`: fonte exige varredura angular parcial com retorno; o importador recusa em vez de impor uma volta inteira.
- `hydraulic-boom.csv` — `BLOCKED_E7-FONTE-QUANTIDADE_CORPOS`: esse modelo possui atuação linear e tipo de representação não coberto pelo importador/solver atual; a recusa **não é falha de física hidráulica demonstrada**.

**Resultado atualizado:** **4/6 fontes CSV inéditas para o importador foram convertidas e solucionadas**, duas tiveram recusa explicitamente identificada. O aumento **2→4** foi obtido DEPOIS de inspecionar as fontes de avaliação. É melhoria legítima no código genérico, mas **NÃO é um aumento medido em holdout cego**. A amostra é pequena e vem do MESMO repo/autor da E7; segundo repo independente ainda não é traduzido.

**Regressão E7:** [Actions 45270170727](https://github.com/Heitor2404/coringa-news/actions/runs/45270170727) **SUCCESS, 39 testes**, agora com casos positivos/negativos de `parallel/perpendicular` e falsificação de desenhos. E7 permanece 3/5 nos arquivos originais, pois `scotch-yoke` é bloqueado pelo limite de velocidade e `gears` por contato composto; nenhum bloqueio foi maquiado.

## Direção visual e benchmark

O motor produziu o vídeo `E8_UNSEEN_GENERIC_PRIVATE.mp4` de `shaper` pelo mesmo renderer: **540×960, 18 fps, 2 segundos, mudo, privado, câmera fixa**. Teste do vídeo revelou movimento visível e a cópia dos modelos veio de coordenadas CSV da fonte, não mídia de terceiros. **Quadro real inspecionado: ilustração técnica ainda muito simplificada**, sem uma máquina-ferramenta reconhecível no nível que o usuário quer, apesar do mecanismo cinemático correto; `visual_approved=false`.

Os novos CSVs não representam automaticamente novos dos **12 mecanismos** do benchmark congelado; não aumentar o score só por haver mais arquivos. O placar de laboratório permanece **4/12 candidatos demonstrados** até a E7, **0 holdouts mecânicos**, **0 spec oriunda de prosa livre**, **0 estilo homologado**, **0 publicação**.

## Próxima etapa

- Fazer novos testes **em outra fonte que já descreva explicitamente corpos/juntas/âncoras**, sem encaixar presets por título, e separar taxa de descoberta de taxa de importação de topologias.
- Driver parcial/retorno e atuador linear exigem evolução genérica com contrato de cinemática e limites independentes; não contornar velocidade ou geometria real para obter vídeo.
- Reforçar representação visual comum com corpos industriais discerníveis, indicadores de ação e composição/movimento motivados pelos mecanismos, mantendo câmera estável, sem modelos visuais descartados.
- Exigir QA independente dos vídeos, além de testes de resíduos matemáticos.

**Tudo permanece na branch experimental; `main`, NTC, DOSSIÊ, Telegram, produção e postagem NÃO alterados.**
