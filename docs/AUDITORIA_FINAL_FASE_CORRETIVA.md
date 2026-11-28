# ENCERRAMENTO CONTROLADO — 25/11/2026 16:11 (instrução do proprietário)

Missão encerrada a pedido do proprietário; o desenvolvimento volta ao ChatGPT, que auditará e incorporará seletivamente.
Nada novo foi implementado, renderizado ou consumido após a instrução. **A fase corretiva NÃO está concluída.**

- HEAD preservado na branch exclusiva: o commit deste encerramento (sobre `c92facb5`). Árvore limpa, tudo no GitHub.
- `main` = `8d550693…` e `atlas-direcao-visual-20261118` = `257ce75d…` inalteradas (conferido por `git ls-remote`).
- Workflows: nenhum em execução. Último CI isolado `45681330128` (c92facb5) **SUCCESS**. Última execução ATLAS
  `45678665168` **FAILURE** documentada (geografia PENDENTE por fonte sem resposta; retry adicionado depois, **não validado
  em execução**). Este commit de encerramento usa `[skip ci]` para não disparar execuções.
- Recursos: autorização E284-visao-8 com 7/8 chamadas lógicas e 9/16 operações consumidas, 20.182 tokens, USD 0; saldo
  1 lógica (finalidade geleiras). Gemini TTS (cota gratuita): 7 sínteses. Orçamentos antigos seguem esgotados.

## Alterações que afetam a direção audiovisual, o compositor e a identidade visual

| Área | Alteração | Commit | Arquivo |
|---|---|---|---|
| **Compositor** | Vídeo horizontal integral com legenda usa a caixa das fotos integrais (y 405–1030), legenda fora da evidência | `b954c3c6` (E283) | `motor4/remotion/src/formatos/FilmeEditorial.tsx` |
| **Compositor / render** | Config do Remotion passa a ser carregada (`motor4/remotion.config.js`): aplica `gl=swangle`, JPEG 92, concorrência 1 e Chrome local em TODOS os renders sem flags explícitas — muda a qualidade de imagem intermediária de renders antigos que dependiam do padrão | `4c7d59bd` (E283) | `motor4/remotion.config.js` |
| **Compositor (ATLAS)** | Crédito em tela pode incluir Blue Marble quando o raster S2 tem oceano batimétrico (cortesia, só se couber) | `979c36cd` | `motor4/remotion/src/formatos/Palco.tsx`, `src/v4/formatos/plano.py` |
| **Identidade visual do mapa** | Mosaicos S2 novos do ATLAS multiescala: mar aberto da base Blue Marble com batimetria + máscara Natural Earth 10 m e faixa costeira S2 de 1,5 km (aparência do oceano muda) | `abd207e5` | `scripts/formatos_raster.py`, `scripts/qa_atlas_multiscale.py` |
| **Fiscal editorial** | Tolerância de 1e-6 s nos limites de duração de plano (quadros inteiros) | `abd207e5` | `src/v4/formatos/filme_editorial.py` |
| **Direção — ritmo/montagem** | Cortes de imagem até 1,2 s da fronteira da fala (J/L-cut); ritmo uniforme da voz até 8%; pausas da TTS encurtadas a 0,35 s só se necessário; recusa com `FALA_EXCEDE_EVIDENCIA_REPLANEJAR` | `1f03dee3`, `d158dc54`, `9f5bc5a0` | `scripts/qa_documentario_integral_e254.py` |
| **Legendas** | Início da palavra alinhado à fala medida (≤0,4 s); render exige sincronia medida aprovada | `c0e4acd4` | `src/v4/formatos/legenda_sync.py`, `scripts/qa_documentario_integral_e254.py` |
| **Direção — seleção de filmagens** | Varredura temporal local, janelas por evento, insistência controlada, adiamento de ângulo com ≥3 negativas, fila prioriza candidatos novos | `6ec76d07`, `e2c8ac03`, `3cb5509d`, `c5fe736e`, `095b64cb`, `2de411b0` | `src/v4/formatos/amostragem_documental.py`, `scripts/qa_revisao_documental_e247.py`, `src/v4/formatos/revisao_documental.py` |
| **Direção — multimodal/ATLAS** | Necessidade `territorio` recebe mapa ATLAS automático com geografia verificada por Wikidata+OSM; a ponte aceita essa origem além da curadoria | `a9fbc813`, `08b71bc9`, `c92facb5` | `src/v4/formatos/{geografia_verificada,atlas_automatico,ponte_cobertura_filme}.py`, `scripts/qa_documentario_integral_e254.py` |
| **Roteiro (assistido)** | Falas das geleiras encurtadas pelo desenvolvedor, só no caso `benchmarks/e284/geleiras.json` | `ec2ef217` | benchmark (não é código do motor) |

Sem efeito audiovisual (infraestrutura/validação): orçamento persistente e teto de tentativas (`src/v4/orcamento_visao.py`,
`src/gemini.py`), contrato do replay e estados de prova, descoberta de checkpoints, workflows exclusivos, scripts de
prévia/diagnóstico/entrega E284, memória `ERR-085…097`.

Regressões identificadas durante o trabalho (todas corrigidas e cobertas por teste): reuso 9→2 por início arredondado
(`3cb5509d`); reuso 9→0 por descoberta de checkpoints por recência após rearquivamentos (`f6212921`).

# Auditoria final da fase corretiva — consolidação Claude (25/11/2026, segunda rodada E284)

Branch: `claude-consolidacao-corretiva-20261125`. Partida desta rodada: `5157189c` (aceito pela auditoria). Partida da
branch: `257ce75d` (Work). `main` (`8d550693`) e `atlas-direcao-visual-20261118` (`257ce75d`) não foram alteradas;
nenhum merge, rebase ou force push. Teto financeiro do motor: USD 0 em todas as execuções.

Classificação usada: **comprovado** = execução real com artefato inspecionado; **técnico** = teste/CI; **bloqueado** =
limitação real registrada. Intervenções humanas/do desenvolvedor são marcadas **assistido**.

## A. Os quatro riscos da auditoria independente

| Risco | Reprodução | Solução (commit) | Evidência |
|---|---|---|---|
| 3.1 limite real da varredura | `fps=max(.5,…)` excedia 720 quadros acima de ~24 min; `subprocess.run` guardava todo o vídeo bruto | `c5fe736e`: duração real por pacotes (sem decodificar) e demux; modo contínuo em fluxo (um quadro por vez, memória constante, teto rígido); acima de cap/duração <1 fps, âncoras hierárquicas (van der Corput) sobre o arquivo inteiro com orçamento de tempo — qualquer prefixo cobre o arquivo; pares no ritmo da fonte (fonte de 2 fps gerava pares duplicados); proporções extremas; arquivo ilegível → `INDISPONIVEL` e grade histórica | `tests/test_varredura_limites_e284.py`: 26 min ≤720 quadros e lacuna máx. <10 s; metadados menores e maiores que o real; 400×16, 16×400; arquivo corrompido. Real: clipe Apollo 496 s 720 quadros, maior lacuna 1,03 s |
| 3.2 eventos no mesmo plano | plano único de 180 s com dois acontecimentos e uma transformação lenta era abandonado após o 1º | `c5fe736e`: segmentação em eventos (início de atividade, deriva gradual de aparência), câmera acompanhando referente; janelas, diversidade e insistência por evento; deriva lenta conta como sinal | testes de plano único (eventos A e B alcançáveis; sem sinal novo → candidato externo) |
| 3.3 regressão frouxa do reuso | `>=6` aceitava perder 3 de 9 | `c5fe736e`/`b5023860`: contrato congelado `benchmarks/e284/contrato_replay_e260.json` (multiconjunto das 9 revisões, estados, seleção, zero visão, zero HTTP; fluxo normal permite só buscas de metadados) + prova `igual_ao_work` executando o código `257ce75d` sobre a mesma coleção; colisão de chaves arredondadas restaura cada início exato | CI 45669210737/45671033045/45672773260: replay 9 = contrato, normal 9, Work 9 = Claude, `DIFERENCAS []`. O contrato **detectou** depois uma regressão real (9 → 0, CI 45675321541), ver B.7 |
| 3.4 workflow aprovava sem prova | `continue-on-error` nos checkpoints | `c5fe736e`/`f6212921`: `scripts/estado_prova.sh` registra APROVADA/REPROVADA/BLOQUEADA (exit 77); `scripts/resumo_provas.py` marca NAO_EXECUTADA e só homologa com todas aprovadas; prova de checkpoints exige pacotes (`scripts/exigir_pacotes.py`) | `tests/test_contrato_validacao_e284.py`; sumários dos runs com tabela de estados |

Outros workflows auditados (não executam nesta branch, não alterados): `qa-documentario-integral-e254.yml` segue se o
cofre falhar (aviso) e só verifica artefato após render; `qa-filme-taiwan-portao.yml` usa `continue-on-error` em
download de artefato expirado (estado explícito "BLOQUEADO"); vários (`qa-lacunas-e264`, `qa-replay-integral-e265`,
`qa-selecao-real-e281`, `reparar_manifesto_documental.py`) procuram uma tag fixa em `listar_releases(60)` — ficarão
cegos quando a tag sair da janela (mesma causa de B.7). Recomenda-se adotar `estado_prova.sh`/`resumo_provas.py` ao integrar.

## B. Demais correções materiais (todas reproduzidas em execução real)

1. **Autorização persistente de visão** (`a1b13244`, `src/v4/orcamento_visao.py`): livro no cofre (`orcamento/E284-visao-8.json`, CAS pelo sha), criado uma vez, reserva antes da chamada, liquidação pelas operações efetivas (tentativas, retries, inválidas), reserva órfã no pior caso, limites não ampliáveis, limite por finalidade; `gemini._tentar` com `CORINGA_VISAO_MAX_TENTATIVAS`.
2. **Mesmos bytes por outra fonte / ângulo inadequado** (`095b64cb`, `2de411b0`): na prova da ação as 2 chamadas foram para o clipe Apollo (1ª perdida por 503 ×2, contabilizada; 2ª o mesmo arquivo voltou pelo Commons). Arquivo com ≥3 negativas revisadas para a necessidade é adiado sem chamada até a última fase e ordenado após candidatos novos.
3. **Geografia verificada automaticamente** (`a9fbc813`, `08b71bc9`): `geografia_verificada.py` (Wikidata P625 + OSM concordantes, senão PENDENTE) consolida mecanismos já existentes; a ponte aceita essa origem; `atlas_automatico.py` encadeia aquisição/render ATLAS existentes para necessidades `territorio` no fluxo integral. A curadoria manual continua válida; coordenadas de modelo nunca.
4. **Borda curva Sentinel-2** (`abd207e5`, `979c36cd`): causa no **dado bruto** EOX — o s2cloudless 2016 só imageia uma faixa costeira de oceano (com costuras de passagem) e o EOX compõe outro oceano escuro além dela (grade de tiles brutos do Kilauea; MAE bruto×mosaico ≈2,7 e render fiel). Alternativa: S2 em terra + faixa costeira de 1,5 km (máscara Natural Earth 10 m, domínio público, suavizada) e mar aberto da base Blue Marble com batimetria já usada nos zooms menores; crédito Blue Marble acrescentado. Run 45675321568: borda eliminada, oceano contínuo entre níveis (inspecionado).
5. **Fala × evidência** (`1f03dee3`, `d158dc54`, `9f5bc5a0`): voz maior que a capacidade verificada bloqueava com `E254-TEMPO-CAPITULO`; a duração da TTS varia entre execuções (63,8 s e 69,8 s para o mesmo texto). Ordem: cortes de imagem até 1,2 s da fronteira da fala (J/L-cut, nunca além da capacidade revisada); ritmo uniforme até 8% (tons preservados, todos os tempos escalados); só então pausas longas encurtadas para 0,35 s (fala intacta, tempos remapeados); acima disso `FALA_EXCEDE_EVIDENCIA_REPLANEJAR` com o fator.
6. **Fiscal editorial e quadros inteiros** (`abd207e5`): `fim−início` de quadros/30 deu 3.8000000000000043 > 3,8 e reprovou foto na capacidade exata.
7. **Descoberta de checkpoints por recência** (`f6212921`): as reexecuções arquivaram de novo os mesmos 19 pacotes; a janela de 60 releases e o orçamento de manifestos empurraram a coleção E258 para fora (E259 PACOTES 0; o contrato acusou 9 → 0). Releases cujos pacotes já foram catalogados não consomem manifesto; varredura até 300 releases; prova exige pacotes.
8. **Legenda antecipada** (`c0e4acd4`): documentário narrado com sincronia medida `ok=false` (9/165 palavras iniciando na pausa antes da fala). Início alinhado ao começo real da fala medido no áudio (≤0,4 s, antes do fim da palavra); render passa a exigir sincronia aprovada.
9. **Roteiro das geleiras** (`ec2ef217`, **assistido**): falas encurtadas pelo desenvolvedor (mesmos fatos, sem fatos novos) porque o capítulo final pedia fator 1,35. A seleção de mídia permaneceu autônoma.

## C. Regressões

| Execução | Resultado |
|---|---|
| Local HEAD | 222 passed; 206 passed; novas desta branch (E283+E284) passam; `memoria conferir` íntegra |
| CI isolado 45669210737, 45671033045, 45672773260 | SUCCESS: config Remotion, 222, 206, novas, memória, checkpoints, replay = contrato (9), normal (9), igual ao Work |
| CI isolado 45675321541 | FAILURE correto: E259 PACOTES 0 → replay 0 (B.7) |
| CI isolado 45677151177 (f6212921) | SUCCESS, homologação COMPLETA: 222, 206, novas, memória, PACOTES 2, replay 9 = contrato, normal 9, Work = Claude |
| Testes alterados | `tests/test_atlas_multiscale_e237.py`: mock de aquisição aceita `**kw` (novo parâmetro `oceano`); finalidade (adquirir uma vez por nível) preservada |

## D. Validações audiovisuais

| Prova | Run / commit | Duração | Modalidades | Narração | Seleção | Entrega |
|---|---|---|---|---|---|---|
| Prévia local Apollo (sem visão) | 45665284919 / a1b13244 | — | folha de 6 janelas | não | varredura local | cofre `revisoes/e284-acao-previa-45665284919-1` |
| Filmagem de ação (foguete) | 45666408862 / 095b64cb | — | — | — | autônoma; **reprovada** (n2 LACUNA) | cofre `revisoes/e284-acao-visao-45666408862-1` |
| Corinto ATLAS (real, sem download de navegador) | 45665672046 / a9fbc813 | 5,5 s | mapa multiescala | não | geografia autônoma (Wikidata Q182873 + OSM, 1,2 km) | Telegram ✓; cofre `e284-atlas-corinto-45665672046-1` |
| Kilauea antes/depois da correção S2 | 45671033072 → 45675321568 → 45678665168 | 5,5 s | mapa | não | caso curado E261.4 | cofre `e284-atlas-corinto-45671033072-1`, `-45675321568-1`, `-45678665168-1` |
| Corinto, 5ª execução | 45678665168 | — | — | — | geografia **PENDENTE** (uma fonte sem resposta no runner; nenhum mapa sem verificação) → retry limitado acrescentado no commit final | — |
| Geleiras — documentário integral | 45675321595 / abd207e5 | 65,2 s | 18 fotografias | sim (Gemini TTS) | autônoma (3 novas + 15 de checkpoint); roteiro assistido | Telegram ✓; cofre `e284-geleiras-visao-45675321595-1`; **sincronia medida reprovada** → corrigida em B.8 |
| **Geleiras — versão final** | 45678546446 / c0e4acd4 | **63,9 s** | 18 fotografias | sim (Gemini TTS, ritmo 1,025; um corte de imagem 1,17 s após a fala) | autônoma; roteiro assistido | **Telegram ✓**; cofre `e284-geleiras-visao-45678546446-1` + release `review-e284-geleiras-visao-45678546446-1`; **sincronia medida ok** (atraso 0,0 s, 4/165 palavras fora da fala ≤3%, sem fala sem legenda) |

Crédito Blue Marble: declarado nos props; na tela é cortesia (domínio público) e só entra se couber nas duas linhas da faixa, regra existente — no Kilauea não coube; o recibo do raster registra as duas fontes.

Avaliação inspecionada (folha de contato e quadros): n16 fiorde, n17 Matterhorn e n18 Lake Pukaki pertinentes; créditos
legíveis; a composição ainda é **de fotos pequenas**: fotos integrais ocupam a faixa y≈405–1030 e retratos (Matterhorn,
cachoeira) ficam estreitos, com a metade inferior da tela em ambiência desfocada. Isso decorre do perfil seguro
conservador (texto até y≈1260) somado à ausência de recorte por ROI em fotos; não foi resolvido nesta rodada (H).
O tema é **regressão integral** de um episódio já trabalhado, não prova de generalização inédita.

## E. Orçamento

| Item | Valor |
|---|---|
| Autorização | E284-visao-8: 8 lógicas / 16 operações; ação ≤2, geleiras ≤6 |
| Consumido | 7 lógicas (ação 2, geleiras 5), 9 operações externas (2 retries por 503), 20.182 tokens, USD 0 |
| Saldo | 1 lógica (geleiras), 7 operações; finalidade de ação esgotada |
| Orçamentos antigos | geleiras 20 e E281 4 continuam esgotados; não reiniciados |
| Voz | Gemini TTS, cota gratuita, 1 chamada por tentativa de montagem (7 tentativas) |

## F. Matriz vigente de capacidades

| Capacidade | Implementação | Validação técnica | Validação prática | Autonomia comprovada |
|---|---|---|---|---|
| Seleção de fotografia | sim | sim | sim (Coliseu E281.1; n16–n18) | **sim** (18/18 geleiras, 3 inéditas nesta rodada) |
| Varredura temporal de filmagens | sim | sim | prévia real (Apollo 496 s, janelas de atividade) | parcial |
| Seleção de filmagem de ação | sim | sim | **reprovada** (2 chamadas no mesmo ângulo; causas corrigidas) | **não** — bloqueado por orçamento |
| Reuso de análises/checkpoints | sim | contrato exato (9) | replay real | sim |
| Limites de recursos persistentes | sim | sim | sim (saldo entre 5 execuções) | sim |
| ATLAS no caminho real de render | sim | sim | sim (Corinto, Kilauea) | geografia automática **sim** (Corinto) |
| Borda S2 | causa identificada | sim | sim (Kilauea) | — |
| Narração + legendas sincronizadas | sim | sim | **63,9 s narrado com sincronia medida aprovada** (run 45678546446) | sim |
| Animações complementares | sem alteração | suítes 222/206 | histórico (E28/E29/E44) | não exercitadas nesta rodada |
| Direção multimodal | sem alteração (prompt + rotas) | suítes | episódio das geleiras é monomodal (só fotos, por desenho do caso) | não demonstrada nesta rodada |
| Três documentários ≥60 s contrastantes | — | — | **1** (regressão integral) | bloqueado por orçamento |

## G. Pendências reais

1. **Filmagem de ação com visão real** — orçamento (finalidade esgotada). Menor recurso: 2 chamadas; com as correções B.2 as alternativas do Archive (encontradas na mesma execução) viriam antes do clipe Apollo.
2. **Dois documentários de temas novos** (ciência/tecnologia e história/geografia com ATLAS) — orçamento: cada tema novo de ~6 necessidades exige ~6–10 chamadas de visão (uma por candidato revisado, com margem para rejeições).
3. **Escala útil de fotos/retratos com legenda** — código: recorte por ROI declarada em fotos (bbox da evidência direta já existe) e caixa por proporção; não implementado.
4. **Workflows antigos com tag fixa em `listar_releases(60)`** — código/integração (A).
5. **Animações e multimodal** — não exercitados com mídia nova nesta rodada; nenhuma incompatibilidade demonstrada nas suítes.

## H. Parecer final

**A fase corretiva ainda não pode ser encerrada integralmente.** Estão comprovados: os quatro riscos da auditoria, a
preservação do Work e da primeira rodada, o reuso exato, limites persistentes, seleção autônoma de fotografias, ATLAS no
caminho real com geografia verificada automaticamente, a causa e correção da borda S2 e um documentário narrado de
63,9 s com sincronia medida aprovada. Faltam, por limitação de orçamento e não de código conhecido: a prova real da filmagem de ação e dois documentários
de temas novos; e, por código, a escala útil de fotos com legenda. Recomendação: autorizar ~2 chamadas para a ação e
~12–16 para dois temas novos, e encerrar a fase se essas provas passarem.

## I. Integração posterior

- HEAD final: último commit da branch (este documento é atualizado no commit final). Commits desta rodada: `c5fe736e` … HEAD (`git log 5157189c..HEAD`).
- Arquivos principais: `src/v4/formatos/amostragem_documental.py`, `scripts/qa_revisao_documental_e247.py`, `src/v4/orcamento_visao.py`, `src/gemini.py`, `src/v4/formatos/{geografia_verificada,atlas_automatico,ponte_cobertura_filme,revisao_documental,filme_editorial,legenda_sync,plano}.py`, `scripts/{qa_documentario_integral_e254,formatos_raster,qa_atlas_multiscale,recuperar_checkpoints_documentais,contrato_reuso_replay,comparar_reuso_work,estado_prova.sh,resumo_provas,exigir_pacotes,qa_previa_filmagem_e284,qa_fragmento_acao_e284,qa_filme_e284,entregar_prova_e284,diagnostico_s2_e284}.py`, `motor4/remotion/src/formatos/{FilmeEditorial,Palco}.tsx`, testes `tests/test_*e284*.py`, `benchmarks/e284/*`.
- Conflitos potenciais: E247, amostragem, `qa_documentario_integral_e254.py`, `ponte_cobertura_filme.py`, `FilmeEditorial.tsx`, `Palco.tsx`, docs de continuidade.
- Workflows exclusivos a remover/adaptar: `qa-consolidacao-claude-20261125.yml`, `qa-provas-reais-e284.yml`, `qa-atlas-corinto-e284.yml` e os gatilhos `.github/e284/*.json`. Levar `estado_prova.sh`/`resumo_provas.py` e o contrato congelado para `qa-corretiva-e260.yml`.
- Preservar: `motor4/remotion.config.js` na raiz de `motor4/`; o livro `orcamento/E284-visao-8.json` no cofre (não recriar).
- Procedimento: `git checkout atlas-direcao-visual-20261118 && git merge --no-ff claude-consolidacao-corretiva-20261125`; remover workflows exclusivos em commit separado; rodar `qa-corretiva-e260` com o contrato. Não executado.

## Histórico — primeira rodada Claude (E283), mantida sem alteração

Branch exclusiva: `claude-consolidacao-corretiva-20261125`. Commit de partida: `257ce75db196840cc4d74132f301e7179a842d67`.
Nenhuma alteração em `main` ou `atlas-direcao-visual-20261118` (ambas conferidas por `git ls-remote` no fim da sessão:
`atlas-direcao-visual-20261118` = `257ce75d…`, sem commits posteriores do Work; `main` = `8d550693…`). Nenhum merge,
rebase, force push ou reescrita de histórico. Nenhuma chamada paga do motor (visão, Claude, TTS): teto USD 0 mantido.

Este documento separa o que foi **comprovado** do que apenas foi **implementado**. Onde não há evidência, está escrito.

---

### A. Estado inicial

- HEAD `257ce75d` = dois commits do ChatGPT Work sobre E282 (`65e0f17c`, `257ce75d`).
- Linha de base reproduzida localmente antes de qualquer alteração: regressão acumulada **222 passed**, controle
  multitemático **206 passed** (mesmos conjuntos de `qa-corretiva-e260.yml` e `qa-filme-taiwan-portao.yml`).
- Problemas abertos herdados: (1) incompatibilidade de navegador do Remotion na prova de Corinto, correção do Work não
  enviada; (2) E281.2 com cobertura 1/2 — filmagem do foguete não aprovada após duas chamadas no mesmo clipe de 496 s;
  (3) escala útil da evidência não resolvida pela E280; (4) três documentários completos ≥60 s não produzidos;
  (5) borda curva de textura Sentinel-2 documentada; (6) passagem autônoma de necessidades geográficas ao ATLAS.

### B. Causas-raiz (reproduzidas)

| # | Defeito | Reprodução | Causa-raiz |
|---|---|---|---|
| 1 | Remotion baixa Chrome Headless Shell mesmo com Chrome instalado e `REMOTION_CHROME` definido | `cd motor4 && REMOTION_CHROME=/usr/bin/google-chrome npx remotion compositions remotion/src/index.ts --log=verbose` → `No config file loaded.` → `Downloading Chrome Headless Shell` → `ENOTFOUND` | O CLI só lê `remotion.config.*` da "remotion root" (pasta do `package.json` mais próximo = `motor4/`, `RenderInternals.findRemotionRoot`). O arquivo estava em `motor4/remotion/` e **nunca foi aplicado**: `REMOTION_CHROME`, `gl=swangle`, JPEG 92 e concorrência eram ignorados em todos os renders que não passavam flags explícitas (vários workflows confiavam em `REMOTION_CHROME`). |
| 2 | Janelas de filmagens longas não alcançam a ação; insistência no mesmo arquivo | Vídeo sintético (`tests/test_varredura_temporal_e283.py`): ação do referente só em 46–54 s; a grade antiga escolhe três janelas por terços sem tocar o plano da ação | `explorar()` gerava grade uniforme (≤12 janelas de 3,8 s), `selecionar()` impunha uma janela por terço e ranqueava por diferença bruta de pixels — cortes e panorâmicas pareciam ação. `revisao_adicional_possivel` era verdadeiro sempre que restasse janela não vista, mesmo parada ou só de câmera. É o padrão da E281.2 (134/268/358 s e 89/313/447 s no clipe Apollo de 496 s). |
| 3 | Regressão introduzida e corrigida nesta sessão: reuso de checkpoint 9 → 2 | CI isolado [run 45653082312](https://github.com/Heitor2404/coringa-news/actions/runs/45653082312), passo de replay | Janelas de checkpoint ausentes da nova grade eram reinseridas com o início **arredondado** (chave de 4 casas); `revisao_id` faz hash do início exato → ID diferente → análise privada não encontrada. |
| 4 | Legenda medida cobre a filmagem integral horizontal | Render local de `FilmeEditorial` media-first com vídeo 16:9 `cena_integral` e legendas (quadro 45) | `DOC_MEDIA.integral` ia até y 1150 enquanto a faixa de legenda documental ocupa y 1040–1150. |

### C. Correções realizadas

| Commit | Arquivos | Alteração | Justificativa |
|---|---|---|---|
| `4c7d59bd` | `motor4/remotion.config.js` (movido de `motor4/remotion/remotion.config.ts`), `motor4/remotion/remotion.config.ts` (shim), `tests/test_remotion_config_raiz.py` | Config na remotion root, em JS (config `.ts` exige `tsconfig.json` na raiz, que `motor4/` não tem); navegador `REMOTION_CHROME` > `CORINGA_CHROME` > Chrome/Chromium do sistema; sem nenhum, comportamento padrão | Corrige o mecanismo (local da config), não o sintoma (não adiciona `--browser-executable` em cada chamada). Restaura também `swangle`/JPEG 92 que eram silenciosamente ignorados. |
| `6ec76d07`, `e2c8ac03` | `src/v4/formatos/amostragem_documental.py`, `scripts/qa_revisao_documental_e247.py`, `tests/test_varredura_temporal_e283.py` | `varrer()`: uma passada FFmpeg em baixa resolução (≤720 quadros, ≤4 fps, 160 px) sobre o arquivo inteiro; Farneback + afim RANSAC separam movimento da câmera do residual do referente; cortes por diferença após compensar a câmera; fusões (<0,8 s) agrupadas como transições. Janelas dentro de planos, melhor movimento residual por plano, cobertura temporal preservada; diversidade por plano, não por terços. `marcas_temporais()`: timestamps declarados em título/descrição relevantes à necessidade viram pistas. `ha_janelas_promissoras()`: nova rodada no mesmo arquivo só com plano não visto e promissor, marca de metadado ou análise privada gratuita. | Generalizável (nenhuma regra por tema). Tudo local e gratuito. Sem varredura (arquivo ausente, sem ffmpeg/OpenCV) o comportamento histórico é preservado. Pistas nunca são prova: `prova_semantica: False`, `cobertura_semantica_integral: False`. |
| `3cb5509d` | idem | `inicios_exatos`: E247 passa o float armazenado; reinserção usa o início exato | Corrige a regressão #3 na causa. |
| `b954c3c6` | `motor4/remotion/src/formatos/FilmeEditorial.tsx`, `tests/test_legenda_fora_da_evidencia_e283.py` | Com legendas, vídeo integral usa a caixa das fotos integrais (y 405–1030, largura 1080) | Evidência sem texto sobreposto; mesma identidade das fotos integrais. |
| `2b952579`, `e500446b` | `.github/workflows/qa-consolidacao-claude-20261125.yml` | Workflow exclusivo da branch: regressões 222/206/novas, verificação da config Remotion no runner, replay e fluxo normal sem IA com checkpoints privados (somente leitura), diagnóstico por códigos | Os workflows existentes filtram `atlas-direcao-visual-20261118`; não foram alterados. Permissão `contents: read`, `CAIXA_MAX_CHAMADAS=0`, `CAIXA_TETO_USD=0`, `USAR_CLAUDE=0`, sem upload para o cofre. |
| (este commit) | `docs/memoria/erros.json` (ERR-085…088), `docs/ESTADO_CANONICO_MOTOR.md`, `docs/CONTINUIDADE_PROXIMO_CHAT.md`, este arquivo | Registro | `python -m src.v3.memoria conferir` → íntegra. |

### D. Preservação do trabalho do Work

Todas as correções de `65e0f17c` e `257ce75d` permanecem intactas e cobertas pelas suítes 222/206 e pelo replay:
recusa de movimento entre quadros idênticos (`test_identical_observed_pixels_cannot_support_reported_motion` passa com
a nova amostragem), preservação de observações inválidas (`consolidar_janelas` inalterado), marcas reais de fim de
palavra e agrupamento por pausas (`legenda_sync.py` não tocado), encadeamento de prévias, pesquisa/provedores,
MediaWiki, reuso de mosaicos ATLAS, proteção de orçamento esgotado e de arquivos residuais (não tocados).
Única interação: `scripts/qa_revisao_documental_e247.py` — acrescentados metadados textuais ao dicionário de mídia (não
entram em nenhum `revisao_id`), troca da condição de `revisao_adicional_possivel` por `ha_janelas_promissoras` e o
repasse de `inicios_exatos`. A correção de Corinto do Work não existia no GitHub; foi refeita a partir da causa.

### E. Regressões

| Execução | Resultado |
|---|---|
| Local, partida `257ce75d` | 222 passed; 206 passed |
| Local, HEAD | 222 passed; 206 passed; novas 13 passed (`test_remotion_config_raiz.py` 4, `test_varredura_temporal_e283.py` 8, `test_legenda_fora_da_evidencia_e283.py` 1); testes que tocam E247/amostragem (e257, e258, e269, e283) 64 passed; `test_area_segura_plataformas.py` + `test_filme_editorial.py` passam |
| CI [45653082312](https://github.com/Heitor2404/coringa-news/actions/runs/45653082312) (`2b952579`) | FAILURE — 222/206/12 aprovados, config Remotion OK no runner, **replay 2 reusos** (regressão #3, detectada pelo próprio CI) |
| CI [45654737439](https://github.com/Heitor2404/coringa-news/actions/runs/45654737439) (`3cb5509d`) | **SUCCESS** — `REMOTION_CONFIG_RAIZ_OK`, 222 passed, 206 passed, 13 passed; `E259 PACOTES 2`; replay e fluxo normal: visão 0, **9 reusos cada**, estados `['CANDIDATO_PRIVADO_REVISADO','LACUNA_PENDENTE']` idênticos ao run do Work 45646284798; varredura local ativa nos dois vídeos; janelas de checkpoint reinseridas com início exato |

Nenhum teste removido ou enfraquecido. Um teste foi ajustado durante o desenvolvimento antes do primeiro commit (textura
sintética de 8 px → 24 px em `test_varredura_temporal_e283.py`): ruído branco subamostrado não representa filmagem real e
fazia o fluxo óptico falhar numa panorâmica; a finalidade (separar câmera de referente) foi mantida.

### F. Resultados audiovisuais

**Nenhum documentário completo ≥60 s foi produzido nesta sessão.** Motivos precisos em H. Provas práticas realizadas:

- Render local real do `FilmeEditorial` (Remotion + Chrome do sistema, sem download) com três clipes/fotos reais do
  repositório (`tests/midia/*`, Canal do Panamá e NASA): quadros antes/depois inspecionados visualmente; a legenda deixou
  de cobrir o convés do navio. A narração usada foi um WAV de silêncio apenas para habilitar a faixa de legenda no
  compositor — **não é prova de sincronia nem filme narrado**. Artefatos locais, não versionados.
- Varredura em clipes reais do repositório: fusão do timelapse do Panamá detectada como transição (2,6–3,4 s), dois
  planos; custo medido em arquivo de 496 s 720p: **17,4 s de CPU local**, 720 quadros.
- Nenhuma folha nova inspecionada, nenhuma entrega Telegram, nenhuma publicação.

### G. Eficiência

- Chamadas de IA do motor: **0**. Custo: **USD 0**. Downloads de mídia: **0** (rede da sessão bloqueada a provedores;
  CI só leu checkpoints privados já existentes).
- Reuso comprovado no CI: 9 análises privadas reaproveitadas no replay e 9 no fluxo normal.
- Economia esperada (não medida com IA real): a varredura substitui janelas cegas; em arquivos longos, a segunda chamada
  no mesmo clipe só ocorre se houver plano promissor não observado — exatamente o desperdício da E281.2 (2 chamadas,
  6 janelas, 0 aprovação). Para clipes ≤ 30 s, a varredura custa < 1 s.
- Render: a config passa a aplicar `concurrency 1`/`swangle`/JPEG 92 também nos workflows que só exportavam
  `REMOTION_CHROME`; flags explícitas na linha de comando continuam prevalecendo.

### H. Limitações restantes

1. **Três documentários completos ≥60 s — BLOQUEADO por orçamento.** Os saldos de visão (geleiras 20/20, E281 4/4)
   estão esgotados e não foram reiniciados. A cobertura existente é 15/18 (57 s) nas geleiras e 1/2 na E281; não há
   cobertura suficiente para ≥60 s sem novas revisões. Menor recurso adicional: autorização de **2 chamadas lógicas de
   visão** (Gemini flash-lite, mesmo provedor/contrato) para repetir só a necessidade de movimento da E281 com a
   varredura nova (prova direta da correção #2), e **3–6 chamadas** para as lacunas n16–n18 das geleiras; narração
   pelo motor de voz já usado (sem custo novo) somente após cobertura ≥60 s.
2. Sessão de desenvolvimento sem rede para provedores de mídia (Commons/Archive/EOX/Remotion CDN bloqueados por
   allowlist): impediu inspecionar o raster bruto Sentinel-2. **Borda curva S2: não reproduzida.** Descartado nesta
   sessão: o palco usa `image source` com cantos em Mercator para tiles EPSG:3857 (interpolação linear correta, sem
   curvatura) e o `acabamento()` gera alfa retangular. A hipótese restante é o próprio dado EOX 2016 ou a rampa entre
   níveis; exige baixar os tiles brutos da região afetada no Actions — não mascarar.
3. **Escala útil**: com o perfil seguro multiplataforma (texto só até y≈1260), uma fonte 16:9 integral ocupa 1080×608
   (~32% da tela). Ganho real exige recorte por ROI declarada pela revisão (`relacao_observada` → 4:5/1:1, já
   implementado no modo adaptativo). Não foi criado recorte sem ROI: violaria a integridade documental.
4. **Direção multimodal e geografia autônoma**: sem alteração. A decisão de modalidade vem do prompt do diretor
   (`diretor_visual_e202.planejar_documental`) e a passagem ao ATLAS exige `CURADORIA_GEOGRAFICA_VERIFICADA`; a
   pesquisa/verificação automática de geografia continua pendente e não pode ser validada sem IA/rede.
5. Animações complementares: nenhuma alteração; contratos E217/E40 preservados (suítes passam).
6. A varredura é heurística: movimento seguido pela câmera (travelling acompanhando o referente) aparece como câmera
   dominante — é só penalidade de ranking, a janela continua elegível. Não detecta semântica.

### I. Matriz final de capacidades

| Capacidade | Classificação | Evidência |
|---|---|---|
| ATLAS nativo → FilmeEditorial | Validada na prática (histórico) | runs 44588617776, 45551945864, 45553006784 |
| Config Remotion / navegador local | **Validada tecnicamente** (local + CI) | `4c7d59bd`; CI 45654737439 `REMOTION_CONFIG_RAIZ_OK` |
| Reutilização de mosaicos ATLAS (Work) | Validada tecnicamente | `test_atlas_base_regional_e235.py` |
| Borda S2 | Bloqueada (sem acesso ao raster) | H.2 |
| Aproximação multiescala | Validada na prática (histórico) | E236 45516297789 |
| Seleção autônoma de fotografia | Autonomia comprovada (1 necessidade, E281.1) | 45638969866 |
| Varredura temporal local de filmagens | **Validada tecnicamente** | `test_varredura_temporal_e283.py`; CI 45654737439 |
| Seleção autônoma de filmagem de ação | Parcialmente validada / bloqueada por orçamento | E281.2 1/2; correção sem prova com visão real |
| Reuso de checkpoints/análises | Validada tecnicamente (replay real) | CI 45654737439: 9/9 |
| Orçamento esgotado sem reativação | Validada tecnicamente | suíte 222 + replay `visao 0` |
| Legendas sincronizadas (Work) | Validada tecnicamente | suítes; sem filme narrado novo |
| Legenda fora da evidência integral | Validada tecnicamente | render local + teste |
| Montagem multimodal narrada | Validada na prática (histórico E233) | 45509206301 |
| Animações complementares | Implementada / validada tecnicamente (histórico) | suítes E213/E217/política |
| Geografia pesquisada/verificada automaticamente | Implementada parcialmente / não validada | H.4 |
| Três documentários ≥60 s contrastantes | **Não realizado — bloqueado** | H.1 |

### J. Instruções para auditoria

```bash
git fetch origin claude-consolidacao-corretiva-20261125 && git checkout claude-consolidacao-corretiva-20261125
git log --oneline 257ce75d..HEAD
pip install -r requirements.txt beautifulsoup4 pytest pyyaml && npm ci --prefix motor4
# Causa 1 — partida (esperado: "No config file loaded" e tentativa de download) versus HEAD ("Applied configuration"):
git worktree add /tmp/partida 257ce75d && ln -s "$PWD/motor4/node_modules" /tmp/partida/motor4/node_modules
(cd /tmp/partida/motor4 && REMOTION_CHROME=/usr/bin/google-chrome npx --no-install remotion compositions remotion/src/index.ts --log=verbose 2>&1 | grep -E "config|Downloading")
(cd motor4 && npx --no-install remotion compositions remotion/src/index.ts --log=verbose 2>&1 | grep -E "Applied configuration|Downloading")
git worktree remove --force /tmp/partida
# Suítes de referência e novas (mesmos conjuntos do workflow isolado):
python -m pytest -q tests/test_remotion_config_raiz.py tests/test_varredura_temporal_e283.py tests/test_legenda_fora_da_evidencia_e283.py
python -m src.v3.memoria conferir
```
CI: [45654737439](https://github.com/Heitor2404/coringa-news/actions/runs/45654737439) (logs públicos mostram
apenas códigos). Workflow: `.github/workflows/qa-consolidacao-claude-20261125.yml`. Nenhum artefato privado novo.

### K. Parecer de encerramento

**A fase corretiva NÃO pode ser encerrada.** As causas-raiz reproduzíveis sem recurso pago foram corrigidas, com
regressão permanente e validação no CI (incluindo replay real de checkpoints privados). Falta a evidência prática
exigida pela própria missão: seleção de filmagem de ação com visão real após a correção e três documentários narrados
≥60 s em temas contrastantes. Ambos dependem de autorização explícita de orçamento de visão (H.1).

### L. Relatório de integração futura

- Commit de partida: `257ce75db196840cc4d74132f301e7179a842d67`. HEAD final: ver `git log -1` da branch (este commit de
  documentação é o último).
- Arquivos modificados: `motor4/remotion.config.js` (novo, movido), `motor4/remotion/remotion.config.ts`,
  `motor4/remotion/src/formatos/FilmeEditorial.tsx`, `src/v4/formatos/amostragem_documental.py`,
  `scripts/qa_revisao_documental_e247.py`, `tests/test_remotion_config_raiz.py`, `tests/test_varredura_temporal_e283.py`,
  `tests/test_legenda_fora_da_evidencia_e283.py`, `docs/memoria/erros.json`, `docs/ESTADO_CANONICO_MOTOR.md`,
  `docs/CONTINUIDADE_PROXIMO_CHAT.md`, `docs/AUDITORIA_FINAL_FASE_CORRETIVA.md`,
  `.github/workflows/qa-consolidacao-claude-20261125.yml`.
- Conflitos potenciais: `scripts/qa_revisao_documental_e247.py` e `amostragem_documental.py` se o Work voltar a alterar
  a amostragem; `FilmeEditorial.tsx` (bloco integral media-first); os dois docs de continuidade (anexos ao fim).
- Workflow exclusivo de validação: **retirar** `qa-consolidacao-claude-20261125.yml` antes da integração (ou trocar o
  filtro de branch). Incluir `tests/test_remotion_config_raiz.py`, `tests/test_varredura_temporal_e283.py` e
  `tests/test_legenda_fora_da_evidencia_e283.py` no workflow acumulado `qa-corretiva-e260.yml` ao integrar.
- Preservar: `motor4/remotion.config.js` na raiz de `motor4/` (mover de volta reintroduz o defeito).
- Procedimento recomendado após aprovação: `git checkout atlas-direcao-visual-20261118 && git merge --no-ff
  claude-consolidacao-corretiva-20261125`, remover o workflow exclusivo num commit separado, rodar `qa-corretiva-e260`
  e `qa-filme-taiwan-portao`. Não foi executado.