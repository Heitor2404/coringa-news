# ESTADO CANÔNICO DO MOTOR DOCUMENTAL — Coringa Explica
Atualização: 25/11/2026. Branch experimental `atlas-direcao-visual-20261118`. Este registro complementa, não substitui, o histórico. Ler primeiro em qualquer retomada; conferir HEAD, código e Actions. Não inferir inexistência a partir de ausência de menção no chat/arquivo recente. Nunca rebaixar capacidade comprovada para não implementada sem apontar regressão concreta com SHA/run e escopo. A validação integral e a qualidade editorial são dimensões distintas da existência de integração.

## REGRA PERMANENTE — crítica técnica independente e proteção da qualidade editorial

Determinação expressa do proprietário em 25/11/2026: o ChatGPT (ou qualquer agente de desenvolvimento) deve avaliar criticamente TODAS as propostas, inclusive as do proprietário e as próprias. Não concordar por conveniência, não implementar uma ideia equivocada, inviável ou prejudicial sem expor o problema. Distinguir fatos comprovados, limitações geométricas/técnicas, hipóteses e preferências estéticas; explicar discordâncias com evidência, oferecer alternativas executáveis e indicar trade-offs. Se a ideia for boa apenas em condições específicas, explicitar as condições. A decisão editorial final é do proprietário; a responsabilidade do agente é não mascarar falhas, não trocar qualidade por velocidade e não declarar sucesso artístico com CI verde. Preservar versões visualmente superiores como referências comparativas, não como homologação irrestrita; antes de alterar estética, comparar quadros e filmes reais nas mesmas condições, com provas de texto, enquadramento, evidência, áudio e áreas seguras. Esta regra complementa os ciclos completos de execução, não exige aprovação a cada correção técnica reversível.

## PROCEDIMENTO PERMANENTE — ciclos completos de execução e validação

Determinação expressa do proprietário em 25/11/2026: evitar obrigá-lo a enviar “prossiga” a cada microetapa ou enquanto um workflow está em execução. Em cada sessão ativa, conduzir blocos completos: consultar estado e código reais, corrigir de forma agrupada, testar, iniciar o CI necessário, consultar até o resultado terminal quando o tempo da sessão permitir, diagnosticar falhas, corrigir e revalidar, inspecionar as evidências audiovisuais reais e atualizar continuidade/estado canônico. Não disparar render duplicado nem alterar precipitadamente um caminho cujo teste ainda está em curso. Consolidar feedback em resultados úteis e comprovados, ou impedimentos materiais que realmente exijam decisão do proprietário. Se o limite da sessão impedir acompanhar até a conclusão, informar o run e a etapa exata, não prometer monitoramento em segundo plano; na próxima retomada consultar o resultado desse run primeiro, sem repetir trabalho. Não inventar aprovação, inspeção ou sucesso. Nenhuma publicação automática, nenhuma ampliação de orçamento, nenhuma alteração da main. A prioridade é qualidade editorial verificável e primeiro vídeo postável, não contagem de commits.

## Estado vigente da auditoria corretiva de 25/11

A fase continua aberta. O bloco E282 em `6083a0005197` terminou. O [replay dos checkpoints](https://github.com/Heitor2404/coringa-news/actions/runs/45642199999) e o fluxo progressivo recuperaram nove análises cada, sem visão nova. O [controle multitemático](https://github.com/Heitor2404/coringa-news/actions/runs/45642200671) passou. O [recibo privado da E281.2](https://github.com/Heitor2404/coringa-cofre/blob/revisao-privada/revisoes/e2812-45639629861-1/prova.json) permanece em 1/2, com 3,8 s disponíveis. As referências abaixo a execuções em andamento descrevem o momento histórico indicado.

O commit `65e0f17cd4db8d6a68e15eaf2249002bf7545858` passou no [controle multitemático](https://github.com/Heitor2404/coringa-news/actions/runs/45644894008). O integral progressivo pode usar a reserva de foto automaticamente. Janelas inválidas sobrevivem ao checkpoint como diagnóstico, movimento alegado entre quadros idênticos é recusado e as marcas de fim de palavra chegam ao agrupador. Inspeção local de três vídeos existentes confirmou amostras decodificáveis. Permanecem pendentes a seleção de ação inédita com revisão formal e os três filmes completos. A matriz e o parecer desta missão ficam em `AUDITORIA_FINAL_FASE_CORRETIVA.md`.

## ENCERRAMENTO CONTROLADO — 25/11 16:11

Missão Claude encerrada pelo proprietário; o ChatGPT reassume e incorporará seletivamente após auditoria. Fase corretiva **não concluída**. Branch `claude-consolidacao-corretiva-20261125` preservada (nada integrado); `main` e `atlas-direcao-visual-20261118` inalteradas. Lista das alterações que afetam direção audiovisual, compositor e identidade visual: topo de [AUDITORIA_FINAL_FASE_CORRETIVA.md](AUDITORIA_FINAL_FASE_CORRETIVA.md). Último CI isolado 45681330128 SUCCESS; última execução ATLAS 45678665168 FAILURE documentada (geografia PENDENTE; retry posterior não validado). Saldo da autorização E284-visao-8: 1 lógica.

## Estado vigente — consolidação final Claude E284, 25/11 (prevalece sobre os blocos abaixo)

Detalhes, matriz e parecer: [AUDITORIA_FINAL_FASE_CORRETIVA.md](AUDITORIA_FINAL_FASE_CORRETIVA.md). Partida `5157189c`; Work e primeira rodada preservados (contrato do replay: as mesmas 9 revisões do código `257ce75d`, CI 45677151177).

| Item | Implementação | Validação técnica | Validação prática / autonomia |
|---|---|---|---|
| Varredura temporal limitada (fluxo + âncoras hierárquicas) e eventos no mesmo plano | `c5fe736e` | `test_varredura_limites_e284.py` | prévia real Apollo 496 s (run 45665284919) |
| Contrato exato do reuso + estados de prova inequívocos | `c5fe736e`, `b5023860`, `f6212921` | CI 45677151177 COMPLETA | replay e normal 9/9; detectou regressão real 9→0 (corrigida) |
| Autorização persistente E284-visao-8 | `a1b13244` | `test_orcamento_visao_e284.py` | 5 execuções; 7/8 lógicas, 9/16 operações, USD 0 |
| Filmagem de ação | `095b64cb`, `2de411b0` | testes | **reprovada** (run 45666408862); finalidade esgotada |
| Geleiras 18/18, documentário narrado | `1f03dee3`…`c0e4acd4` | `test_ritmo_fala_e284.py`, `test_legenda_inicio_fala_e284.py` | 63,9 s, sincronia medida aprovada, Telegram (run 45678546446) |
| ATLAS caminho real + geografia automática | `a9fbc813`, `08b71bc9` | `test_geografia_verificada_e284.py`, `test_atlas_automatico_e284.py` | Corinto (run 45665672046), Telegram |
| Borda S2 | `abd207e5`, `979c36cd` | `test_oceano_s2_e284.py` | causa no dado EOX; corrigida (run 45675321568) |

**Fase corretiva aberta**: faltam a prova real de filmagem de ação e dois documentários de temas novos (orçamento) e a escala útil de fotos com legenda (código).

## Estado vigente — consolidação Claude, 25/11 (branch `claude-consolidacao-corretiva-20261125`)

Prevalece sobre os blocos transitórios abaixo. Partida `257ce75d` (Work preservado integralmente). Detalhes, matriz e parecer em [AUDITORIA_FINAL_FASE_CORRETIVA.md](AUDITORIA_FINAL_FASE_CORRETIVA.md).

| Item | Implementação | Validação técnica | Validação prática / autonomia |
|---|---|---|---|
| Config Remotion na remotion root (`motor4/remotion.config.js`), Chrome local sem download (causa da falha de Corinto) | `4c7d59bd` | local + CI [45654737439](https://github.com/Heitor2404/coringa-news/actions/runs/45654737439) `REMOTION_CONFIG_RAIZ_OK` | renders locais de `FilmeEditorial` sem download; render ATLAS real não refeito (sem rede para tiles nesta sessão) |
| Varredura temporal local de filmagens (cortes, câmera × referente, transições, marcas de metadados, nova rodada no mesmo arquivo só com plano promissor) | `6ec76d07`, `e2c8ac03`, `3cb5509d` | `tests/test_varredura_temporal_e283.py`; CI 45654737439 replay e fluxo normal 9/9 reusos, visão 0 | sem visão real após a correção (orçamento esgotado); E281.2 continua 1/2 |
| Legenda medida fora da filmagem integral horizontal | `b954c3c6` | `tests/test_legenda_fora_da_evidencia_e283.py` | quadros locais inspecionados; escala 16:9 integral continua ~32% da tela (ganho exige ROI declarada) |

Regressões de referência no HEAD: 222 e 206 aprovados (local e CI). Nenhuma chamada paga, nenhum reinício de orçamento, nenhuma publicação. Bloqueios: três documentários ≥60 s e prova de ação com visão real (orçamento); borda S2 não reproduzida (raster bruto inacessível nesta sessão). **Fase corretiva aberta.**

## Estado vigente — retomada ChatGPT E285 (§338)
A branch Claude 9b2f7df é arquivo histórico, não estado integrado. Geleiras 63,9s (45678546446) **REPROVADA editorialmente**: 18 fotos, fundo borrado, escala e créditos inadequados; prova técnica de voz/render apenas, roteiro assistido. Prioridade imediata vídeo postável >=60s com direitos e avaliação real, sem publicação. E285 importa subset técnico e testes; não importa alterações de ritmo, roteiro, compositor, geografia/S2 nem workflows pagos. Saldo visão E284 1 somente geleiras; não reiniciar. Validação E285 pendente. Ver §338.

## Capacidades cuja integração/reutilização já foi comprovada
| Capacidade | Prova prática histórica | Código existente | Pendência delimitada |
|---|---|---|---|
| ATLAS nativo → FilmeEditorial | [Taiwan 44588617776](https://github.com/Heitor2404/coringa-news/actions/runs/44588617776); [E261.4 45551945864](https://github.com/Heitor2404/coringa-news/actions/runs/45551945864); [E261.8 45553006784](https://github.com/Heitor2404/coringa-news/actions/runs/45553006784) | src/v4/formatos/ponte_mapa_atlas.py; scripts/qa_misto_atlas_e261.py | geografia pesquisada/verificada automaticamente; borda S2; composição com legenda; não reintegrar |
| ATLAS multiescala | [E236 45516297789](https://github.com/Heitor2404/coringa-news/actions/runs/45516297789), Grand Canyon/Gibraltar; 5,5 s cada | scripts/qa_atlas_multiscale.py | validar outros objetivos geográficos quando exigidos; não afirmar DEM/3D homologados |
| Montagem multimodal narrada | [E233 45509206301](https://github.com/Heitor2404/coringa-news/actions/runs/45509206301), 79,8 s, 24 cenas, Telegram entregue; falha apenas backup cofre | src/v4/formatos/ponte_cobertura_filme.py; src/v4/formatos/filme_editorial.py | autonomia e qualidade consistente no fluxo atual, não criar compositor |
| Animações integradas em prova privada | [E28 45321450413](https://github.com/Heitor2404/coringa-news/actions/runs/45321450413); [E29 45321559459](https://github.com/Heitor2404/coringa-news/actions/runs/45321559459); [E44 45388294172](https://github.com/Heitor2404/coringa-news/actions/runs/45388294172) | src/v4/formatos/diretor_visual_e202.py; src/v4/formatos/cobertura_documental.py | seleção/execução automática de complemento E217/E261.5, arte e narração; não reativar legado reprovado |
| Filmagens por janelas e reuso | [E258.1 45544941326](https://github.com/Heitor2404/coringa-news/actions/runs/45544941326); [E259 45545856108](https://github.com/Heitor2404/coringa-news/actions/runs/45545856108) | scripts/qa_revisao_documental_e247.py; src/v4/formatos/amostragem_documental.py | aquisição pertinente, ação e tomadas longas, ROI; amostras não provam ação contínua |
| Memória V3/cofre e replay | [E260.1 45548964290](https://github.com/Heitor2404/coringa-news/actions/runs/45548964290); [E265 45615720734](https://github.com/Heitor2404/coringa-news/actions/runs/45615720734), 15/15; [E273 45624516177](https://github.com/Heitor2404/coringa-news/actions/runs/45624516177), 3 pistas pendentes | src/v4/formatos/reuso_documental.py; scripts/recuperar_checkpoints_documentais.py | preservar escopo/hash e validade; não repetir replay comprovado sem regressão |
| Duração mínima revisada | [E260.3 45550782541](https://github.com/Heitor2404/coringa-news/actions/runs/45550782541); [E261.7 45552638190](https://github.com/Heitor2404/coringa-news/actions/runs/45552638190) | src/v4/formatos/tempo_natural.py; scripts/qa_documentario_integral_e254.py | montagem com voz real e tomadas longas; não retornar a duração rígida |
| Pré-triagem foto Commons | [E274 45627022872](https://github.com/Heitor2404/coringa-news/actions/runs/45627022872), 6/6, 6 HTTP, 1.260.368 bytes, 29 testes | src/v4/pretriagem_documental.py; scripts/qa_pretriagem_e269.py | seleção semântica e fluxo autônomo; não confundir miniatura com cobertura |
| Composição documental | [E271.1 45623113472](https://github.com/Heitor2404/coringa-news/actions/runs/45623113472) | src/v4/formatos/filme_editorial.py | tamanho/áreas mortas/créditos/legendas, sem homologação estética |

## Backlog corretivo único (não reconstruir capacidades acima)
1. Pesquisa e aquisição: diversidade real de fontes/consultas, rendimento, recibos e variantes; distinguir falha operacional de ausência de mídia.
2. Seleção: integrar pré-triagem à fila existente, inspeção semântica por escopo, selecionar ações/timestamps e preservar contexto; manter aprovação privada separada dos direitos.
3. Acabamento: evidência protagonista, ROI sem crop cego, créditos, títulos, legendas reais e transições; investigar a fonte da borda cartográfica antes de novo render idêntico.
4. Aproveitamento de capacidades: fechar passagem de necessidades geográficas e lacunas explicativas para ATLAS/solver já existentes; complementar somente quando pertinente e com prova.
5. Validar ponta a ponta em documentários privados >=60s de temas contrastantes, com evidência visual, revisão efetiva de resultados, sem homologar por CI verde.
6. Após o fechamento corretivo, autocorreção audiovisual autônoma (§285) é prioridade estratégica expressa do usuário.

## Regras de continuidade
- Usar histórico permanente, inclusive [versão com §§1–285](https://github.com/Heitor2404/coringa-news/blob/005d8543c30b/docs/CONTINUIDADE_PROXIMO_CHAT.md), [§291](https://github.com/Heitor2404/coringa-news/blob/4ded6709e23b/docs/CONTINUIDADE_PROXIMO_CHAT.md), [§294–301](https://github.com/Heitor2404/coringa-news/blob/3f376eabb7b3/docs/CONTINUIDADE_PROXIMO_CHAT.md), [§312](https://github.com/Heitor2404/coringa-news/blob/f2cd06ec5e0309b510bc477ebd917fe130a3a56e/docs/CONTINUIDADE_PROXIMO_CHAT.md). O arquivo corrente foi segmentado por tamanho; não descartar as provas antigas.
- Antes de nova implementação: confrontar registro, código e run; só reabrir integração se regressão específica comprovada. Após mudança: atualizar registro e continuidade com estado implementado/testado/prático separadamente, SHA/run, defeitos e próximo bloco.
- Trabalhar em blocos relacionados, sem pedir “prossiga” entre microetapas. Feedback consolidado com o que foi comprovado e o que não foi. Não prometer conclusão em segundo plano.
- Não alterar main/publicar/reiniciar orçamento de 20 chamadas do episódio das geleiras sem autorização; Claude somente para avanço substancial. Sem novos gates arbitrários. Preservar regressões e direitos.

## Último bloco em validação — E275/E275.1
- Diversidade de descoberta: orçamento de consultas independente do limite de retenção, intercala lotes ranqueados e registra descartes operacionais. Pré-triagem prioriza consultas distintas sem eliminar alternativas. Código integrado no caminho progressivo; aguardando regressões e prova prática.
- Handoff de prévias: opção privada `--pretriagem-pendente` reutiliza a fila de lacunas do E247, sem nova pesquisa, visão ou promoção de cobertura. Ainda não decide qual original adquirir autonomamente; validar antes de ativar como padrão.
- E274: seis folhas inspecionadas, aquedutos com alternativas pouco diversas; Saturno dois candidatos quase iguais. Eficiência de transporte aprovada, diversidade/semântica ainda pendentes.

### Resultado confirmado do bloco
E275, commit 5677893ee08b3f7cca05ba5207c8a54d01730006, [run 45628133696](https://github.com/Heitor2404/coringa-news/actions/runs/45628133696) SUCCESS: 117 testes, verificação do registro canônico aprovada. E275.1, commit a30f943c33a5c7a0e4c1b162ba984db854ca069a, [run 45628307070](https://github.com/Heitor2404/coringa-news/actions/runs/45628307070) iniciado, resultado ainda pendente nesta consulta. Não repetir E275; confirmar E275.1 e inspecionar as folhas se geradas. Não confundir integração opt-in de prévias com seleção autônoma. Faltam validação prática atual, seleção/filmagens, acabamento e autonomia das capacidades existentes, conforme backlog. Nenhuma nova chamada Gemini/Claude/TTS, nenhuma publicação, main preservada.

### E276 — bloco de variantes
E275.1 [run 45628307070](https://github.com/Heitor2404/coringa-news/actions/runs/45628307070) SUCCESS, 32 testes; quatro prévias no fluxo real, 12 HTTP, 2.868.484 bytes, oito erros, zero visão/cobertura. Quatro folhas vistas; melhor pista de aqueduto e alternativas distintas de Saturno, uma de cor artificial não homologada. E276 corrige a resolução pedida apenas no modo opt-in sem visão e ordena variantes declaradas de vídeo sem excluir alternativas; implementação presente, validação pendente. Não alterar status de ATLAS, animações, montagem ou memória.

### E277 — reaproveitamento temporal
Corrigida ordem de amostragem cache-only para alcançar janelas com revisão privada já armazenada fora do lote técnico padrão. A identidade continua dependente da regeneração dos pixels e do ID exato. Implementado no caminho E247/E257, teste novo e regressão real em execução; não confundir com melhoria semântica ou ação contínua. E276 em validação no [run 45628962634](https://github.com/Heitor2404/coringa-news/actions/runs/45628962634).

E277 [run 45629080558](https://github.com/Heitor2404/coringa-news/actions/runs/45629080558) e regressão geral [45629080686](https://github.com/Heitor2404/coringa-news/actions/runs/45629080686) em execução, assim como E276. Consultar resultados antes de repetir qualquer trabalho (§318).

### E276/E277 confirmadas — próximo E278
E276 45628962634 SUCCESS (35 testes, 6/6 prévias, 6 HTTP, 1.372.670 bytes, zero erros). E277 45629080558 SUCCESS (140 testes, 9 revisões reaproveitadas no replay e no fluxo normal); regressão geral 45629080686 SUCCESS (195+11 testes). Não repetir. E276 duas folhas suspeitas vistas: retrato humano na consulta Saturno e gravura sem aqueduto evidente na consulta de Segóvia. Próximo E278: pertinência visual antes da diversidade, preservar identidade/ação/contexto, seleção de prévias vinculada à aquisição e revisão de filmagens existente; não promover miniatura a cobertura, nem reabrir integrações. Ver §319. Fase corretiva aberta.

### E278 — pertinência e aquisição orientada por observações
Implementado ranking contextual soft antes da fração de correspondência, fallback sujeito isolado adiado, diversidade de prévias dentro de faixas de pertinência. Contrato genérico de escolhas observadas ligado ao E272; seis folhas E276 revisadas, duas pistas priorizadas, duas inadequadas, uma alternativa e uma contextual condicional. Prova conjunta sem visão/voz em execução; não considerar seleção autônoma comprovada. Após CI, conferir folhas novas e originais, diagnosticar sem nova integração paralela. Ver §320.

### E278.1 — observação por lote, integração experimental
E278 f420aeb: [prova](https://github.com/Heitor2404/coringa-news/actions/runs/45631143175), [regressão](https://github.com/Heitor2404/coringa-news/actions/runs/45631143043) em execução na consulta. Opção --revisar-previas usa o saldo existente de ask, gera observações vinculadas para aquisição E272; sem saldo, pendente. Testes controlados, nenhuma visão real nova. Não considerar autonomia de seleção homologada até prova com pixels e orçamento autorizado. Ver §321.

### Estado verificado do bloco E278
[{"id":45631143175,"status":"in_progress","conclusion":null},{"id":45631143043,"status":"completed","conclusion":"success"},{"id":45631359513,"status":"in_progress","conclusion":null}]. E278.1 [run 45631359513](https://github.com/Heitor2404/coringa-news/actions/runs/45631359513). Regressão geral aprovada; testes e nova pesquisa E278 aprovados por etapa, aquisição/folhas ainda não confirmadas. Retomar pelo §322, sem duplicar execução nem reconstruir capacidades existentes.

### E278/E278.1 — resultados confirmados (§323)
[45631143175](https://github.com/Heitor2404/coringa-news/actions/runs/45631143175) SUCCESS: 38 testes, 6 prévias pertinentes em inspeção assistida (6 HTTP, 906.046 bytes, zero erros), sem os dois falsos positivos E276. Concentração em uma consulta por tema permanece. Aquisição a partir de observações E276: 2/2 arquivos, 3.392.321 bytes, um derivado declarado 1920x853 e um master 3600x2700, folhas inspecionadas, revisão formal/direitos pendentes. [45631359513](https://github.com/Heitor2404/coringa-news/actions/runs/45631359513) SUCCESS: 125 testes do bloco, observador real ainda não executado. [45631143043](https://github.com/Heitor2404/coringa-news/actions/runs/45631143043) SUCCESS: 195+11 testes. Não repetir o bloco. Próximo: provar observação/seleção autônoma com orçamento permitido, aquisição e revisão integral encadeadas, filmagens de ação e composição; sem reabrir integrações comprovadas.

### E279 — encadeamento no E247
Modo opt-in --encadear-previas reserva saldo existente, observa miniaturas e passa candidato vinculado à revisão formal existente na mesma execução; não promove prévia, preserva movimento/ATLAS. Implementado, regressões E279/E279.1 aprovadas; visão real e qualidade final não homologadas. §324.

### E279.1 — aquisição de resolução normal após prévia
Compartilhado resolvedor E272/E279, preview reduzido nas necessidades reservadas e reconsulta de variantes somente para a escolha. Teste do E247.main com dados controlados, duas chamadas simuladas dentro do teto; validação técnica SUCCESS, 128 testes. Não declarar autonomia real. §325.

E279 [45632218472](https://github.com/Heitor2404/coringa-news/actions/runs/45632218472) SUCCESS, 127 testes. E279.1 [45632385794](https://github.com/Heitor2404/coringa-news/actions/runs/45632385794): SUCCESS, 128 testes. Ver §326 antes de continuar. Nenhuma nova IA real.

### E279.1 e E280 confirmadas (§327–329)
E279.1 [45632385794](https://github.com/Heitor2404/coringa-news/actions/runs/45632385794) SUCCESS, 128 testes. Encadeamento controlado comprovado; visão real não homologada. E280: preferência de janela formal pertinente com ROI declarada legível, sem veto adicional; fundo tonal desfocado e créditos maiores em fotos integrais no compositor existente. Prova comparativa privada com cenas E271.1, zero IA/voz. Não confundir ambiência com evidência nem fragmento mudo com filme narrado completo. E280 finalizada com sucesso; seis quadros vistos, melhora de créditos e ambiência mas não de escala útil. Acabamento narrado ainda pendente.

**Runs E280 confirmados:** 45634734946, 45634735022, 45634734897 e 45634735294 SUCCESS. Seis quadros inspecionados; não repetir. Acabamento narrado permanece pendente.

### E281 — prova real conjunta (§329)
E280 45634734946 SUCCESS, 43 testes e 19,2s; demais três runs SUCCESS. E281 corrige interface de bytes JPEG e reserva rede no orçamento existente. Prova real privada em novos temas, até 4 chamadas lógicas/4 operações caixa, USD 0, sem reiniciar geleiras, sem Claude/TTS. Não considerar autonomia, filme integral ou direitos aprovados antes de evidência. Fragmento condicional à cobertura, não substitui >=60s.

E281 commit d1b9d76, [run 45636170163](https://github.com/Heitor2404/coringa-news/actions/runs/45636170163): FAILURE, 78 testes passaram e 1 falhou antes de visão real. Não duplicar execução real nem ampliar cota. Conferir prova.json, observações, cobertura, folhas e eventual MP4. Não confundir sucesso do workflow com aprovação semântica.

### E281.1 — correção da validação (§331)
E281 45636170163 FAILURE, 78 aprovados/1 falha, nenhuma visão real: assinatura JPEG no teste tinha escape duplicado. Corrigido com bytes.fromhex('ffd8'), mantendo a asserção e o teto anterior. Nova execução E281.1 SUCCESS, 79 testes; ver §332 para resultado prático. Não alterar estados de capacidades comprovadas.

### E281.1 comprovada em fotografia; E281.2 concluída, cobertura parcial (§332–333)
[45638969866](https://github.com/Heitor2404/coringa-news/actions/runs/45638969866) SUCCESS, 79 testes, duas respostas reais de visão, seleção autônoma do Coliseu e revisão formal privada comprovadas em uma necessidade. Foguete não revisado: ffprobe ausente, não falha semântica. E281.2 instala/verifica dependências e restaura checkpoint específico com replay sem visão/rede, só então usa saldo de duas chamadas/duas operações; teto USD 0. Não repetir aprovação da foto, não afrouxar direitos Archive. Sem MP4 na E281.1; aguardar prova de movimento. Autonomia generalizada e filme integral seguem pendentes.

### E282 — prevenção de reincidências (§333)
E281.2 [45639629861](https://github.com/Heitor2404/coringa-news/actions/runs/45639629861) SUCCESS 79 testes; foto recuperada; vídeo baixado e decodificado; 2 chamadas reais restantes, 3 janelas sem ação solicitada e 3 inválidas D-REV-OBSERVACAO. Cobertura 1/2, sem MP4/Telegram. Saldo de visão E281 esgotado; não repetir. E282 preflight compartilhado antes de rede, favorece candidatos novos antes de repetir vídeo remoto na segunda fase, conserva resposta inválida sem aprovar; testes de falhas e regressão acumulada sem IA. Regressões E282 confirmadas nos runs 45642199999 e 45642200671. O estado mais recente prevalece. Fechamento exige prova proporcional ao escopo e regressão concreta, não apenas CI verde; sem criar bloqueios editoriais arbitrários.

### E286 — composição em revisão (§339)
Remoção do fundo borrado e melhoria da escala por proporção real; crédito discreto, legenda centralizada. Prova privada de layout multiformato sem IA, não filme narrado nem homologação; conferir quadros. E285 multitema 45683486826 SUCCESS, contrato de reuso 45683486814 pendente nesta consulta. 

E286.1 (§340): contrato de área segura histórico exigia blur reprovado; corrigido para preservar imagem integral e impedir retorno. Nova prova pendente. Candidato prioritário Havaí (curadoria assistida histórica, não autonomia inédita).

### E285.1 / E287 (§341)
E285 validou código/reuso 9 por identidade, 222/206/35 testes, mas homologação incompleta por resumo e memória de mudanças não integradas; corrigidos registros, novo CI pendente. E286.1 área segura SUCCESS; layout real pendente. Piloto Havaí assistido E219: histórico 79,8s vídeo/mapa, entrega privada confirmada, arquivo 403; E287 prepara originais sem IA, cobertura e cofre pendentes. Direção recebe fala de capítulos quando disponível. Não declarar autonomia inédita nem aprovação de publicação.

E287.1 (§342): layout E286.1 renderizado e inspecionado, melhoria vertical e crédito, horizontal e legendas embutidas ainda não aprovados. Preflight E287 falhou por dependência npm ausente, corrigida; novo run pendente.

E288 (§343): alternativa privada de crop foto baseada em bbox explícita e vinculada, fallback integral, checa interferência de textos; prova real pendente, sem ativação automática geral. Havaí preflight 45685353176 em curso.

E289 (§344): E285.1 SUCCESS, E287.1 SUCCESS, 12 originais USGS e 84 janelas técnicas preservadas; prova de acervo inspecionada. Candidato Havaí assistido com voz Charon limitada a 2 operações gratuitas em livro próprio, zero visão, restore por SHA, render e inspeção pendentes. Não publicar automaticamente.

E288 concluído tecnicamente (§345): 51 testes, 3 fotos/9,6s; n6 ganho de área, n3/n5 permanecem inadequadas no aproveitamento vertical. Opt-in privado, não homologado. E285.1 homologação técnica COMPLETA. E289 run 45686246801 em execução na consulta; candidato narrado ainda não avaliado.

E289.1 (§346): run E289 restaurou acervo e ATLAS mas voz HTTP400 por systemInstruction; saldo voz 1/2. Corrigido contrato REST conhecido, preservação de voz bruta e recibo, teste de saldo persistente. Nova execução pendente, sem vídeo aprovado.

E289.2 (§347): recuperação explícita de gravação bruta por SHA, roteiro e voz; nenhuma nova síntese/fallback no replay. Testes novos pendentes; E289.1 em curso na consulta, não iniciar render paralelo.

E289.3 (§348): voz real 83,04s preservada, TTS 2/2 esgotado; falha 21/216 palavras fora da fala. Recuperação medida e comparação de realinhamento local sem alterar critérios de aceitação, zero IA; render pendente. 

### E289.3 concluída tecnicamente (§349)
Run 45690032145 SUCCESS: 31 testes, 83,07s, 24 cenas vídeo/ATLAS, sincronização medida 21→0 palavras fora da fala, atraso 0,00s, voz/acervo reutilizados, Telegram entregue privadamente. Revisão editorial e voz PENDING; prévia 540x960, piloto assistido. Procedimento permanente de ciclos completos destacado no início. Sem publicação.

### E289.3 REPROVADA editorialmente (§350)
Proprietário reprovou hierarquia tipográfica e escala das filmagens horizontais; referência comparativa de 79,85s preferida, não homologada. Inspeção de nove quadros confirma deficiências. Prioridade: prova privada de composição adaptativa, recorte dirigido apenas quando mantém evidência/contexto, fallback integral com fundo autoral discreto e informação pertinente; sem blur, sem stretch, sem crop cego. Proteger identidade por comparação real e bounds de texto, manter sync e acervo. Regra permanente de crítica técnica independente registrada no início. Não publicar E289.3; não ampliar cotas. Nenhuma mudança de código nesta sessão.

### E290 — tipografia e enquadramento, antes da escolha de fundo (§351)
Implementado no mesmo FilmeEditorial privado: medidas DOM reais e diagnóstico de overflow, créditos maiores (24–30px) e legenda 36–52px, seção até duas linhas, faixas separadas, 16:9 integral sem sobreposição geométrica e sem redução de largura; integrais altas preservam escala anterior, crops existentes não alterados; ROI foto alinhada a cabeçalho, overlay imersivo ainda exige avaliação semântica. Fundo atual, ATLAS, CAD e narração preservados. Commits até c28d37c. [Run E290 45697727693](https://github.com/Heitor2404/coringa-news/actions/runs/45697727693) em execução (setup na consulta), oito quadros reais 1080x1920 com textos sintéticos; não declarar prova de filme/sincronia nem aprovação estética. Compositor/ROI 45697629798 SUCCESS, multitema 45697629853 SUCCESS, negativa 45697629887 SUCCESS. Próximo: confirmar run/medidas/quadros e corrigir falhas antes de selecionar aproximadamente quatro estilos de fundo no chat com o proprietário; não fixar quota de modos/estilos, não reiniciar cotas ou render integral. Sem nova IA/TTS/publicação/main. E289.3 continua reprovada editorialmente, fase corretiva aberta.

Atualização E290: [45697644312](https://github.com/Heitor2404/coringa-news/actions/runs/45697644312) SUCCESS, contrato de áreas seguras e recusa de animações legadas confirmado. 45697629851, 45697629794 e 45697629774 SUCCESS. Run 45697727693 ainda em execução na etapa `Regressoes e compilacao do compositor`, sem PNGs/medidas confirmados nesta consulta. Retomar pelo mesmo run, sem disparar duplicata; não iniciar seleção de fundos antes da inspeção e eventuais correções. Nenhum novo gasto/publicação.

## 352. E290.1 — correção do crédito longo detectado pela prova visual

E290 run 45697727693 FAILURE na prova DOM, 56 testes e tsc SUCCESS, oito quadros 1080x1920 efetivamente renderizados e 24 medições, 22 aprovadas; duas falhas são o mesmo crédito NASA nos offsets 1 e 2. Cofre e290-45697727693-1, commit 57256ae3a1213323bebae86f5d96baefae89ebe5, medidas consultadas: texto integral 24px, altura real de caixa 116px contra 102px; sem truncar ou reduzir piso. Quatro quadros JPG do offset 2 abertos (navio, NASA, Roraima, Salto Ángel): horizontal navio com texto fora da evidência e hierarquia melhor, mas área inferior vazia permanece; NASA traz legenda inglesa embutida no original, não usar como referência estética positiva; caixas escuras se estendem além de texto em retratos, e cachoeira fica parcialmente encoberta, portanto não homologar imersivo. E290.1 redistribui as mesmas faixas dentro da área segura: legenda 1020..1110, crédito 1118..1240 (122px), palco panorâmico 405..1015 (610px, suficiente para 607,5px de 16:9 inteiro a 1080 de largura); fontes mais altas mantêm a escala anterior de 730px. Proteção ROI de foto acompanha faixa de legenda y1020. Caixa de texto passa a largura fit-content limitada ao slot, mede glyph bounds em cada tentativa de tamanho, sem baixar pisos; seção com padding menor e interlinha 1.0. Mesmas oito provas, com crédito completo original e seção extensa adicional; asserts de pisos, semântica de fonte e perímetro mantidos. Sem IA, TTS, novo fundo, publicação ou alteração main. Nova validação pendente; não declarar solução até inspecionar resultados, não disparar duplicata. Ainda faltam avaliação de ROI de imersivo/recortes e estética autoral, conforme §351.
