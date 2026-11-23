# E8 — duas fontes MIT verificadas, seis exemplos geométricos inéditos, quatro vídeos privados

**Data:** 23/11/2026. **Branch:** `atlas-direcao-visual-20261118`.
**Estado:** QA numérico e de transporte APROVADO; estética e compreensão autônoma de mecanismos NÃO APROVADAS.

## Pergunta e escopo

A E7 aceitou três CSVs de um mesmo fornecedor de geometria mecânica. Era necessário testar (1) se esse adaptador conseguia aceitar geometrias que **não tinham sido usadas durante sua implementação** e (2) se o catálogo de fontes conseguia distinguir um segundo projeto aberto de uma verdadeira fonte de corpos/juntas, evitando inventar geometria a partir de presets.

**Não confundir:** E8 implementa um **catálogo limitado a dois repositórios revisados manualmente**, NÃO busca irrestrita de todo o GitHub. As seis entradas inéditas de teste são **do mesmo primeiro repositório**, não da segunda fonte. Toda verificação tem hash Git blob e commit imutável, e nenhum artefato foi publicado automaticamente.

## Entregas reais

- `benchmarks/e8_unseen_linkage_sources_v1.json`: seis arquivos CSV previamente não presentes no conjunto E7, com nomes, SHA de blobs e commit MIT fixos; não altera os 12 desafios congelados.
- `benchmarks/e8_multi_repo_catalog_v1.json`: duas fontes independentes revisadas e pinadas: `jackhale98/linkage_design`, commit `c1ae13b040213b55ece567418bc14e4d2c8d1b0f`, e `MasoudMiM/sketch-mechanisms`, commit `46d41163a23a112e599bda808b2ef8a66981a8fc`. Ambas com licença MIT e Git blob da licença previamente fixado.
- `src/v4/formatos/triagem_fontes_geometria_e8.py`: lê catálogo restrito, recusa URL/commit/path perigosos, baixa conteúdo de `raw.githubusercontent.com` fixado por commit, valida licença e hash exato do arquivo; classifica candidatos como geometria estruturada importável, preset de parâmetros sem juntas explícitas, referência independente de posições ou formato não reconhecido. Nunca confunde um README com corpo/junta resolvido.
- `tests/test_triagem_fontes_geometria_e8.py`: adversariais de hashes alterados, falsa licença, fonte simulada se passando por HTTPS, caminhos inseguros, CSV incompleto e crédito indevido de capacidades.
- `.github/workflows/qa-fontes-abertas-e8.yml`: valida regressões E1/E2/E7, consulta os dois repositórios MIT, testa os seis novos CSVs com o **mesmo importador e solver**, gera quatro MP4 privados do compositor comum, inspeciona todos por FFprobe/hash e extrai frames e comparativos.
- Houve uma segunda rotina temporária de CI com testes sobrepostos (`qa-e8-fontes-e-geometria.yml`). Ela foi removida nesta retomada para evitar duplicação de processamento. Permanecerá a principal, `qa-fontes-abertas-e8.yml`, que testa e renderiza **todos** os mecanismos aceitos.

## Validação efetivamente comprovada

**GitHub Actions [45270545501](https://github.com/Heitor2404/coringa-news/actions/runs/45270545501) — SUCCESS, 52 testes PASS**, todos os passos inclusive renderização das quatro máquinas e QA dos vídeos. Uma execução E8 anterior também passou com 51 testes ([45270102478](https://github.com/Heitor2404/coringa-news/actions/runs/45270102478)); a execução de 52 é a referência desta entrega. Uma segunda execução duplicada ([45270718532](https://github.com/Heitor2404/coringa-news/actions/runs/45270718532)) passou, mas sua rotina não será mantida.

**Artifact privado** `lab-e8-independent-mit-sources-unseen-private`, ID **14865665877**, expira **28/11/2026 21:33:22 UTC**. ZIP baixado e extraído em inspeção local; 40 arquivos incluindo relatório, origem/licença, fontes, seis auditorias, quatro MP4, quadros e folha de contato. `E8_ALL_VIDEOS_QA.json` e a folha `E8_ACCEPTED_MECHANISMS_CONTACT.jpg` foram inspecionados efetivamente.

### Resultado das seis geometrias novas, mesmo adaptador E7

| CSV externo | Estado E8 | Corpos móveis | Juntas |
|---|---|---:|---:|
| `shaper.csv` | **PASS** | 4 | 7 |
| `hoekens.csv` | **PASS** | 3 | 4 |
| `pump-jack.csv` | **PASS** | 3 | 4 |
| `knuckle-press.csv` | **PASS** | 5 | 8 |
| `watt.csv` | **BLOCKED_E7-FONTE-DRIVER_NAO_SUPORTADO** | — | — |
| `hydraulic-boom.csv` | **BLOCKED_E7-FONTE-QUANTIDADE_CORPOS** | — | — |

Todos os quatro aceitos usaram 181 poses por mecanismo no QA, rank completo e resíduo máximo na escala **10⁻¹⁷ m**, sem `if` por título. Os bloqueios não foram mascarados: Watt requer sweep/retorno do acionador que o importador não modela; Hydraulic boom usa atuação linear e estrutura fora do contrato atual de corpos. Não anunciar reprovação da física dessas máquinas: foi **incompatibilidade de contrato**.

### Resultado das duas fontes independentes

- `jackhale98/linkage_design`: dois exemplos selecionados para triagem contêm **geometria explicitamente estruturada** (`points/lines/bodies/joints/driver`), aceitos como candidatos do adaptador comum.
- `MasoudMiM/sketch-mechanisms`: o `README.md` descreve **presets nomeados por mecanismo**, mas não entrega o grafo completo de corpos/juntas; `reference.json` contém coordenadas de amostras de soluções numéricas, úteis como oráculo, mas insuficientes para montar corpo e pontos de junta. **ZERO `MechanismSpec` convertidas diretamente dessa segunda fonte.** Ela NÃO comprova compatibilidade entre formatos heterogêneos.

### Vídeos verdadeiros do motor E8

Todos **540×960, 18fps, sem áudio, câmera fixa, privados**, gerados pelo mesmo `renderer_corpos_e1.py`, sem vídeos ou desenhos copiados dos fornecedores. Cada MP4 passou por hash e teste de diferença real entre quadros.

| Máquina | Nome no artifact | SHA256 |
|---|---|---|
| Shaper | `E8_UNSEEN_GENERIC_PRIVATE.mp4` | `3b748fc2f1ee5481a44726ece95073577113e887fdd9ffa18809893685a6a0b9` |
| Hoekens | `E8_GENERIC_hoekens.mp4` | `37bf3910c59a925f66246b2d4beeace78b6115f337cfdb4d7a3b5661023e0185` |
| Pump jack | `E8_GENERIC_pump_jack.mp4` | `c4a3c382ca846fe190ea701132763b9553ed0ea43a1c6681cb62719655de58e3` |
| Knuckle press | `E8_GENERIC_knuckle_press.mp4` | `63d0cd083366cd5804818b6fb604a0aceeedbc3ac1792bcdab6ce0cdee44f64e` |

**Avaliação visual direta da folha real:** mecanismos distinguíveis como conjuntos de barras articuladas, mas **não parecem máquinas industriais**. Amplas áreas vazias permanecem no painel claro; não há volante, base de máquina, componentes funcionais, superfícies de contato com volumetria ou contexto narrativo. Os quatro desenhos juntos mostram ganho físico, não direção cinematográfica suficiente. **VISUAL NÃO HOMOLOGADO PARA O CORINGA**; proibir uso como produto final.

## Escore e cuidados

- **4/6 CSVs inéditos do MESMO repo** convertidos e resolvidos: evidência forte de que o adaptador E7 não foi codificado só para os cinco títulos anteriores.
- **2/2 repositórios MIT conferidos**, mas somente **1 repo** forneceu `MechanismSpec` completas via o esquema atual.
- **Nenhum** novo alvo distinto do benchmark congelado de 12 confirmado nesta etapa. O Shaper é outro retorno rápido, mecanismo já demonstrado em E7, e os demais não são diretamente os alvos congelados. Placar provisório anterior de **4 topologias de 12** permanece, sem subir artificialmente.
- **0 specs obtidas de prosa livre**, **0 URLs descobertas sem revisão humana**, **0 CAD nativo importado**, **0 holdouts do benchmark de mecanismos** testados, **0 projetos industriais validados**, **0 visuais aprovados**.
- Custos de modelos pagos no código E8 = **zero**; consumo de CI/tempo humano não quantificado.
- `main`, NTC, DOSSIÊ, Telegram e publicação NÃO alterados. Sem confundir licença MIT dos arquivos de origem com direitos irrestritos sobre outras imagens do GitHub.

## Próxima E9 recomendada

Enfrentar separadamente **(a) dados e física** e **(b) visual funcional**. Na física, testar um segundo formato com **corpos e juntas realmente explícitos**, não um README com presets por título; estender a interface de driver para sweep e atuadores lineares por contrato genérico, com provas de limites e velocidades físicas, se houver evidência. Na direção visual, explorar um sistema **geral de montagem/aparência de peças** a partir de geometria e referências licenciadas, e não só barras coloridas. Separar aprovação de legibilidade, fidelidade de mecanismo, enquadramento, retenção e estética, sem escrever um compositor por máquina.
