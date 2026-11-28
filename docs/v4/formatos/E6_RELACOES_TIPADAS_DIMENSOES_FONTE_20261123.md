# E6 — Relações mecânicas tipadas em fontes novas, medidas literais e bloqueio de composição sem geometria

**Data:** 23/11/2026. **Branch isolada:** `atlas-direcao-visual-20261118`.
**Resultado:** E6 passou nos testes do experimento **TEXTUAL**, sem gerar `MechanismSpec` ou simulação inédita. **Não promover para produção.**

## O que foi feito e por quê

Depois da E5, um extrator identificava conexões físicas em frases públicas, mas sem resolver quais peças participavam e sem distinguir `slot`, `slider` ou `rack_pinion`. Além disso, a E5 marcou indevidamente uma frase cujo sujeito era apenas `They`. A E6 é **mais conservadora**, separando classificação textual estreita de comprovação da geometria real.

1. **Coleta live em fontes NOVAS:** `.github/workflows/lab-e6-coleta-corpus.yml`, [Actions 45236864266](https://github.com/Heitor2404/coringa-news/actions/runs/45236864266), SUCCESS. Cinco consultas humanas por assunto; descoberta de URLs de artigos e recuperação real via MediaWiki `pageid`, `revid` e SHA; artifact **14849132292**, expira 28/11/2026 18:18:10 UTC. Sem snippets como provas, sem mídia de terceiros.
2. **Gold separado antes de codificar o detector:** `benchmarks/e6_gold_juntas_v1.json`. **129 frases**, cinco artigos, com classes escritas manualmente antes da implementação e `split` POR ARTIGO. O conjunto de desenvolvimento reúne Geneva drive (15), Cam follower (11), Slider-crank linkage (40), **66 frases, 3 positivas**. O teste separado reúne Universal joint (40) e Rack and pinion (23), **63 frases, 2 positivas**. Gold v1 tem SHA256 **`f5d35d4ba5b2308d5249712d43955ec36677fb6c5564c07d1ef2e5ac0cc6c9b9`**. **Os mesmos desenvolvedores rotularam e implementaram**: NÃO é avaliação independente/cego nem prova representativa de todas as máquinas.
3. **Módulo novo:** `src/v4/formatos/extracao_juntas_e6.py`. Só reconhece afirmações textuais pontuais e explicitamente verificáveis para três classes `pin_in_slot`, `sliding_in_guide`, `rack_engages_pinion`, associando `sentence_id`, SHA da frase e revisão da página. Evita classificar frases genéricas de junta, falta de relação explícita, negações, perguntas, hipóteses e pronomes que aparecem como sujeito não resolvido. **Todos os resultados** conservam `safe_for_solver=false`, `body_instances_bound=false`, `render_allowed=false`, `publish=false` — os nomes de classes só propõem qual tipo de restrição poderia ser estudado.
4. **Unidades numéricas sem autorização de design:** a E6 extraiu `rod length 6\"` e `crank radius 2\"` de uma frase de **exemplo** do artigo slider-crank, normalizando para **0,1524 m** e **0,0508 m**. Essas medidas não pertencem a uma máquina identificada e NÃO autorizam preencher a spec, escolher pivôs ou projetar peças.
5. **Testes e execução:** `tests/test_extracao_juntas_e6.py` e `.github/workflows/qa-extracao-juntas-e6.yml`; regressões E5/E4/F17 e E2 permanecem incluídas, com verificação live da revisão e SHA. Falhas da fonte bloqueiam a validação (nunca retestam uma versão atualizada como se fosse o gold).

## Validação efetiva

[GitHub Actions **45238025158**](https://github.com/Heitor2404/coringa-news/actions/runs/45238025158) **SUCCESS — 96 testes aprovados** (incluindo regressões). Artifact `lab-e6-typed-evidence-five-sources-no-spec`, ID **14849822403**, expira **28/11/2026 18:24:47 UTC**. ZIP com `E6_TYPED_TEXT_EVAL.json` baixado, candidatos e conversões numéricas inspecionados.

| Corpus | Frases | TP | FP | FN | TN | Precisão | Recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Desenvolvimento — 3 artigos | 66 | 3 | 0 | 0 | 63 | 100% | 100% |
| Teste separado — 2 artigos | 63 | 2 | 0 | 0 | 61 | 100% | 100% |

**Exemplos positivos com prova específica de texto:** Geneva drive `s2` e `s14` classificados como `pin_in_slot`; Slider-crank linkage `s3` classificado `sliding_in_guide`; Rack and pinion `s1` e `s4` classificados `rack_engages_pinion`. Artigos Universal joint e Cam follower produziram **0 relações** nessas três classes restritas.

**Interpretação crítica:** apenas CINCO frases positivas em 129, DUAS positivas no teste separado, rótulos criados pela própria equipe e repertório de só três expressões de engenharia. **100% neste pequeno benchmark não é 100% de capacidade real**. Falsos negativos para outro vocabulário, outros tipos de mecanismos e fontes técnicas complexas não foram medidos; o sistema ainda não resolve correferência real entre parágrafos (ele apenas rejeita alguns pronomes). A E5 original e seu falso positivo ficam preservados, NÃO foram alterados.

## Falha arquitetural ainda aberta: texto tipado ≠ junta simulável

- `pin_in_slot` em **Geneva drive** se refere a **entrada e saída intermitente** do pino no rasgo. O `slot` contínuo usado pelo E1/E2 **não resolve por si só** o contato que liga/desliga durante a volta, impactos ou fases de travamento. Logo, mesmo o tipo proposto exige investigar contatos condicionais e ângulos permitidos.
- `sliding_in_guide` não prova direção do eixo, offset, curso, seed ou as demais juntas do mecanismo.
- `rack_engages_pinion` não comprova raio primitivo, dentes, perfil de contato, montagem e fase. E2 resolve **rolamento ideal parametrizado manualmente**, não engrenamento físico real.
- Dois comprimentos de exemplo são evidências de **valores descritos no artigo**, não de um projeto específico. Não há dados confiáveis para um `MechanismSpec` completa.
- A fonte Wikipedia não contém automaticamente licença para reutilizar ilustrações ou identidade visual de equipamento industrial; nenhuma imagem foi copiada.

**NÃO houve** nenhuma spec criada a partir de fonte, nenhum novo vídeo, 3D, peça industrial fiel, aprovação artística, motor publicado ou teste de holdout mecânico. O benchmark congelado dos 12 continua **3 topologias resolvidas com dados manuais em E1/E2, 9 não tentadas**, e **0 fonte→spec completa**.

## Próxima etapa que realmente importa — E7

Exigir **instâncias de corpo e pontos geométricos fundamentados**: corpo A e B, tipo de relação, eixo/pivô, tolerância e parâmetros em fonte identificada com revisão/licença, com recusa explícita do que não se sabe. Preparar um processo de busca mais amplo em especificações técnicas **licenciadas e desenhos dimensionados**, em vez de depender só de textos gerais. Criar benchmark independente anotado por pessoa externa e realizar um teste não preparado do início (tema→pesquisa→spec→solver→MP4 privado), sem construir uma exceção por nome de máquina.

Para mecanismos com contato intermitente (Geneva), o solver deve identificar e sinalizar essa lacuna **em vez de usar a junta permanente**. Custo de chamadas a modelos neste código E6 = 0; custo de CI e horas humanas não contabilizados.

**Isolamento:** modificações apenas na branch experimental. `main`, NTC, DOSSIÊ, Telegram, pipeline produtivo e postagem intactos. Aparência dos renders E1/E2 segue NÃO HOMOLOGADA.
