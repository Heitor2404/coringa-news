# E5 — evidências de conexão explícita: corpus real revisado, teste por página e falsos positivos

**Data:** 23/11/2026 · **Branch isolada:** `atlas-direcao-visual-20261118`
**Status:** experimento de classificação **PASSOU no limiar predefinido**, NÃO gerou juntas físicas executáveis, NÃO integrou produção, NÃO aprovou estética.

## Pergunta e limites da prova

E4 já encontrava artigos novos, mas F17 devolvia 0 arestas tipadas nas frases E4. E5 pergunta algo **MAIS SIMPLES que construir a máquina**: uma frase de texto recuperado afirma explicitamente uma ligação física de componentes identificáveis?

E5 **não** declara quais coordenadas locais são pivôs, quais peças instanciadas são as extremidades reais, quais ângulos/raios existem, nem converte automaticamente `connects` em `pin`. O evento é marcado `unspecified_physical_connection`, com menções de componentes e `sentence_id` para auditoria humana. `joint_kind_verified=false`, `safe_for_solver=false`, `render_allowed=false` e `publish=false` sempre. F17 continua existindo, sem modificações; comparação abaixo é uma **referência de cobertura em classificação binária**, NÃO prova de superioridade em juntas fisicamente tipadas.

## Fontes e método

**Primeira coleta live (Actions 45220383061):** consultas previamente decididas por assunto `Scotch yoke`, `connecting rod`, `crankpin`, sem URLs de artigos fornecidas. E4 buscou cada artigo pela API pública MediaWiki e recuperou texto por `pageid`, `revid` e SHA. Artifact de coleta `14841515280`, expira **28/11/2026 16:47:23 UTC**. Os trechos foram revisados antes de implementar E5.

**Gold congelado:** `benchmarks/e5_gold_relacoes_v1.json`, 6 artigos únicos e **116 frases** (4 fontes do E4/E5 no conjunto de desenvolvimento, 2 no conjunto de teste). Rótulo humano no nível de frase: “há uma declaração explícita de conexão/engate/encaixe de componentes nomeáveis”, ou “não há”. Exemplos genéricos de arranjos, definições de tipos de link, negadores e pronomes sem antecedente inequívoco são negativos. Nenhum texto integral dos artigos é versionado: só IDs, revisão, SHA do texto, seleção determinística e IDs positivos. A coleta anterior original fica no artifact, não serve como prova de URL independentemente reexecutada.

**IMPORTANTE SOBRE INDEPENDÊNCIA:** as anotações e o extrator foram elaborados pela mesma sessão, embora os rótulos/splits tenham sido **salvos antes de escrever o extrator** e as páginas do teste não tenham sido usadas na execução de desenvolvimento. Isto **NÃO é teste duplo-cego nem revisão independente**, portanto há risco de viés de seleção/anotação. Não extrapolar a taxa de acerto a máquinas não vistas.

Páginas e verificações de revisão:
- Desenvolvimento: Four-bar linkage `pageid=1442361, revid=1380680795` (12 frases), Quick return mechanism `49162954, 1386479381` (12), Scotch yoke `1949491, 1386480718` (18), Connecting rod `622034, 1385154929` (40). **82 frases, 9 rótulos positivos.**
- Teste por página: Six-bar linkage `33346874, 1380705291` (12) e Crankpin `3002380, 1376334632` (22). **34 frases, 4 positivos.**

A CI baixou **novamente os seis artigos reais**, exigindo **mesmos `pageid`, `revid`, SHA256 e total/ordem de frases**. Se a fonte mudar, o experimento não pode simplesmente dar verde com novos trechos ou um cache local: **bloqueia** por `SOURCE_REVISION_DRIFT`. Search snippets NÃO contam como texto de fonte.

## Implementação

- `src/v4/formatos/extrator_relacoes_e5.py`: detector determinístico conservador de verbos `connect/attach/engage/couple/hinge/pin` com **pelo menos duas menções de componentes mecânicos**. Recusa definição genérica, estrutura sem peças nomeáveis, negações, perguntas, conexões hipotéticas e o substantivo `connecting rod` confundido com verbo. Não possui ramificação por título do artigo, família específica ou ID.
- `tests/test_extrator_relacoes_e5.py`: frases adversariais, confundimento `pin` como substantivo, negação, citação simulada, parâmetros e métricas sem precisão definida, integridade da revisão e duplicação de artigos.
- `.github/workflows/qa-extrator-relacoes-e5.yml`: testes E5, E4 e F17, consulta REAL de seis artigos, comparação fonte→texto→rótulo, métrica por divisão e gate pré-configurado de precisão no teste **≥0,80** e recall **≥0,50**. Fonte deriva sempre de artigo recuperado, não de trecho criado no teste.

## Resultado efetivamente observado

**GitHub Actions [45222048740](https://github.com/Heitor2404/coringa-news/actions/runs/45222048740) — SUCCESS, 55 testes PASS.**
**Artifact** `lab-e5-frozen-corpus-connection-precision-recall`, ID **14840352298**, expira **28/11/2026 16:56:31 UTC**; contém `E5_CORPUS_REAL_METRICAS.json`. ZIP baixado, relatório examinado e candidatos por `sentence_id` conferidos.

| Fonte/teste | TP | FP | FN | TN | Precisão | Recuperação |
|---|---:|---:|---:|---:|---:|---:|
| Desenvolvimento E5 (82 frases) | 9 | 0 | 0 | 73 | 100% | 100% |
| Teste por página E5 (34 frases) | 4 | **1** | 0 | 29 | **80%** | **100%** |
| F17 em dev (comparação binária) | 0 | 0 | 9 | 73 | indefinida | 0% |
| F17 em teste (comparação binária) | 0 | 0 | 4 | 30 | indefinida | 0% |

**False positive preservado e auditado:** `Crankpin` `pageid=3002380, sentença s19`. Texto usa `They were connected to the driving rods...`, e menciona roda ao final. O detector viu verbo + duas menções, mas o sujeito é **pronome sem referência resolvida na mesma frase**. Gold marcou corretamente negativo no critério de ligação explicitamente identificada. Não mudar esse rótulo e não alterar E5 v1 para mascarar o erro descoberto no conjunto de teste. Próxima versão deve resolver correferência ou recusar pronomes, **avaliada em páginas novas independentes**, não apenas esta mesma amostra.

**Gold hash:** `5af7d8c0a6dedaa406a410279a184d531dcdc9a3b888be773d3d15497e5ebb69`.

## Interpretação para o motor

**Avanço real:** E5 detectou 13 frases com ligações explícitas no conjunto de 116 sem depender da redação estreita da F17; 1 ocorrência extra no teste era falso positivo. As frases reconhecidas ganharam identificador de origem e lista de termos, mas **não** estão prontas para converter em `pin`, `slider` ou `slot`. Importar esses candidatos diretamente na trajetória poderia produzir máquinas fisicamente erradas.

**Não realizado:** descoberta da máquina a partir de tema sem consulta sugerida; compreensão geral de engenharia; ligação de múltiplas frases; resolução de pronomes; geometria, dimensões ou eixos; resolução dinâmica/contato real; modelo 3D; desenho industrial fidedigno; teste em fontes pagas ou CAD; qualquer render novo ou publicação. Total no benchmark congelado de 12 **continua 3 alvos com specs MANUAIS**, sem tentativa de holdout físico novo. E5 não altera esse score.

## Próximo experimento E6 recomendado

1. Criar um **resolvedor de identidade/antecedente** que separe `connecting rod` genérico, `rod` em diferentes contextos e `They` de peças realmente nomeadas. Bloquear se a evidência não identificar duas partes com confiança rastreável. Não codificar a exceção literal do Crankpin s19.
2. Produzir provas de **endpoint tipado** `pin/slider/slot` e dados dimensionais para specs, cada uma com fonte por campo, e medir rejeição de casos ambíguos.
3. Congelar novos artigos **não usados para desenvolver a heurística** e exigir revisão independente do gold; medir falso positivo além da recuperação.
4. Só após suporte completo de topologia/geometria, testar `MechanismSpec` e render **privado** no solver comum. Evitar uma animação específica por máquina.

**Isolamento:** branch experimental somente; `main`, NTC, DOSSIÊ, Telegram e canais produtivos sem modificações. Sem APIs pagas de IA usadas no E5; consumo GitHub Actions não monetizado no relatório.
