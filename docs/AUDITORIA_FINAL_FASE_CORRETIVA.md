# Auditoria final da fase corretiva — consolidação Claude (25/11/2026)

Branch exclusiva: `claude-consolidacao-corretiva-20261125`. Commit de partida: `257ce75db196840cc4d74132f301e7179a842d67`.
Nenhuma alteração em `main` ou `atlas-direcao-visual-20261118` (ambas conferidas por `git ls-remote` no fim da sessão:
`atlas-direcao-visual-20261118` = `257ce75d…`, sem commits posteriores do Work; `main` = `8d550693…`). Nenhum merge,
rebase, force push ou reescrita de histórico. Nenhuma chamada paga do motor (visão, Claude, TTS): teto USD 0 mantido.

Este documento separa o que foi **comprovado** do que apenas foi **implementado**. Onde não há evidência, está escrito.

---

## A. Estado inicial

- HEAD `257ce75d` = dois commits do ChatGPT Work sobre E282 (`65e0f17c`, `257ce75d`).
- Linha de base reproduzida localmente antes de qualquer alteração: regressão acumulada **222 passed**, controle
  multitemático **206 passed** (mesmos conjuntos de `qa-corretiva-e260.yml` e `qa-filme-taiwan-portao.yml`).
- Problemas abertos herdados: (1) incompatibilidade de navegador do Remotion na prova de Corinto, correção do Work não
  enviada; (2) E281.2 com cobertura 1/2 — filmagem do foguete não aprovada após duas chamadas no mesmo clipe de 496 s;
  (3) escala útil da evidência não resolvida pela E280; (4) três documentários completos ≥60 s não produzidos;
  (5) borda curva de textura Sentinel-2 documentada; (6) passagem autônoma de necessidades geográficas ao ATLAS.

## B. Causas-raiz (reproduzidas)

| # | Defeito | Reprodução | Causa-raiz |
|---|---|---|---|
| 1 | Remotion baixa Chrome Headless Shell mesmo com Chrome instalado e `REMOTION_CHROME` definido | `cd motor4 && REMOTION_CHROME=/usr/bin/google-chrome npx remotion compositions remotion/src/index.ts --log=verbose` → `No config file loaded.` → `Downloading Chrome Headless Shell` → `ENOTFOUND` | O CLI só lê `remotion.config.*` da "remotion root" (pasta do `package.json` mais próximo = `motor4/`, `RenderInternals.findRemotionRoot`). O arquivo estava em `motor4/remotion/` e **nunca foi aplicado**: `REMOTION_CHROME`, `gl=swangle`, JPEG 92 e concorrência eram ignorados em todos os renders que não passavam flags explícitas (vários workflows confiavam em `REMOTION_CHROME`). |
| 2 | Janelas de filmagens longas não alcançam a ação; insistência no mesmo arquivo | Vídeo sintético (`tests/test_varredura_temporal_e283.py`): ação do referente só em 46–54 s; a grade antiga escolhe três janelas por terços sem tocar o plano da ação | `explorar()` gerava grade uniforme (≤12 janelas de 3,8 s), `selecionar()` impunha uma janela por terço e ranqueava por diferença bruta de pixels — cortes e panorâmicas pareciam ação. `revisao_adicional_possivel` era verdadeiro sempre que restasse janela não vista, mesmo parada ou só de câmera. É o padrão da E281.2 (134/268/358 s e 89/313/447 s no clipe Apollo de 496 s). |
| 3 | Regressão introduzida e corrigida nesta sessão: reuso de checkpoint 9 → 2 | CI isolado [run 45653082312](https://github.com/Heitor2404/coringa-news/actions/runs/45653082312), passo de replay | Janelas de checkpoint ausentes da nova grade eram reinseridas com o início **arredondado** (chave de 4 casas); `revisao_id` faz hash do início exato → ID diferente → análise privada não encontrada. |
| 4 | Legenda medida cobre a filmagem integral horizontal | Render local de `FilmeEditorial` media-first com vídeo 16:9 `cena_integral` e legendas (quadro 45) | `DOC_MEDIA.integral` ia até y 1150 enquanto a faixa de legenda documental ocupa y 1040–1150. |

## C. Correções realizadas

| Commit | Arquivos | Alteração | Justificativa |
|---|---|---|---|
| `4c7d59bd` | `motor4/remotion.config.js` (movido de `motor4/remotion/remotion.config.ts`), `motor4/remotion/remotion.config.ts` (shim), `tests/test_remotion_config_raiz.py` | Config na remotion root, em JS (config `.ts` exige `tsconfig.json` na raiz, que `motor4/` não tem); navegador `REMOTION_CHROME` > `CORINGA_CHROME` > Chrome/Chromium do sistema; sem nenhum, comportamento padrão | Corrige o mecanismo (local da config), não o sintoma (não adiciona `--browser-executable` em cada chamada). Restaura também `swangle`/JPEG 92 que eram silenciosamente ignorados. |
| `6ec76d07`, `e2c8ac03` | `src/v4/formatos/amostragem_documental.py`, `scripts/qa_revisao_documental_e247.py`, `tests/test_varredura_temporal_e283.py` | `varrer()`: uma passada FFmpeg em baixa resolução (≤720 quadros, ≤4 fps, 160 px) sobre o arquivo inteiro; Farneback + afim RANSAC separam movimento da câmera do residual do referente; cortes por diferença após compensar a câmera; fusões (<0,8 s) agrupadas como transições. Janelas dentro de planos, melhor movimento residual por plano, cobertura temporal preservada; diversidade por plano, não por terços. `marcas_temporais()`: timestamps declarados em título/descrição relevantes à necessidade viram pistas. `ha_janelas_promissoras()`: nova rodada no mesmo arquivo só com plano não visto e promissor, marca de metadado ou análise privada gratuita. | Generalizável (nenhuma regra por tema). Tudo local e gratuito. Sem varredura (arquivo ausente, sem ffmpeg/OpenCV) o comportamento histórico é preservado. Pistas nunca são prova: `prova_semantica: False`, `cobertura_semantica_integral: False`. |
| `3cb5509d` | idem | `inicios_exatos`: E247 passa o float armazenado; reinserção usa o início exato | Corrige a regressão #3 na causa. |
| `b954c3c6` | `motor4/remotion/src/formatos/FilmeEditorial.tsx`, `tests/test_legenda_fora_da_evidencia_e283.py` | Com legendas, vídeo integral usa a caixa das fotos integrais (y 405–1030, largura 1080) | Evidência sem texto sobreposto; mesma identidade das fotos integrais. |
| `2b952579`, `e500446b` | `.github/workflows/qa-consolidacao-claude-20261125.yml` | Workflow exclusivo da branch: regressões 222/206/novas, verificação da config Remotion no runner, replay e fluxo normal sem IA com checkpoints privados (somente leitura), diagnóstico por códigos | Os workflows existentes filtram `atlas-direcao-visual-20261118`; não foram alterados. Permissão `contents: read`, `CAIXA_MAX_CHAMADAS=0`, `CAIXA_TETO_USD=0`, `USAR_CLAUDE=0`, sem upload para o cofre. |
| (este commit) | `docs/memoria/erros.json` (ERR-085…088), `docs/ESTADO_CANONICO_MOTOR.md`, `docs/CONTINUIDADE_PROXIMO_CHAT.md`, este arquivo | Registro | `python -m src.v3.memoria conferir` → íntegra. |

## D. Preservação do trabalho do Work

Todas as correções de `65e0f17c` e `257ce75d` permanecem intactas e cobertas pelas suítes 222/206 e pelo replay:
recusa de movimento entre quadros idênticos (`test_identical_observed_pixels_cannot_support_reported_motion` passa com
a nova amostragem), preservação de observações inválidas (`consolidar_janelas` inalterado), marcas reais de fim de
palavra e agrupamento por pausas (`legenda_sync.py` não tocado), encadeamento de prévias, pesquisa/provedores,
MediaWiki, reuso de mosaicos ATLAS, proteção de orçamento esgotado e de arquivos residuais (não tocados).
Única interação: `scripts/qa_revisao_documental_e247.py` — acrescentados metadados textuais ao dicionário de mídia (não
entram em nenhum `revisao_id`), troca da condição de `revisao_adicional_possivel` por `ha_janelas_promissoras` e o
repasse de `inicios_exatos`. A correção de Corinto do Work não existia no GitHub; foi refeita a partir da causa.

## E. Regressões

| Execução | Resultado |
|---|---|
| Local, partida `257ce75d` | 222 passed; 206 passed |
| Local, HEAD | 222 passed; 206 passed; novas 13 passed (`test_remotion_config_raiz.py` 4, `test_varredura_temporal_e283.py` 8, `test_legenda_fora_da_evidencia_e283.py` 1); testes que tocam E247/amostragem (e257, e258, e269, e283) 64 passed; `test_area_segura_plataformas.py` + `test_filme_editorial.py` passam |
| CI [45653082312](https://github.com/Heitor2404/coringa-news/actions/runs/45653082312) (`2b952579`) | FAILURE — 222/206/12 aprovados, config Remotion OK no runner, **replay 2 reusos** (regressão #3, detectada pelo próprio CI) |
| CI [45654737439](https://github.com/Heitor2404/coringa-news/actions/runs/45654737439) (`3cb5509d`) | **SUCCESS** — `REMOTION_CONFIG_RAIZ_OK`, 222 passed, 206 passed, 13 passed; `E259 PACOTES 2`; replay e fluxo normal: visão 0, **9 reusos cada**, estados `['CANDIDATO_PRIVADO_REVISADO','LACUNA_PENDENTE']` idênticos ao run do Work 45646284798; varredura local ativa nos dois vídeos; janelas de checkpoint reinseridas com início exato |

Nenhum teste removido ou enfraquecido. Um teste foi ajustado durante o desenvolvimento antes do primeiro commit (textura
sintética de 8 px → 24 px em `test_varredura_temporal_e283.py`): ruído branco subamostrado não representa filmagem real e
fazia o fluxo óptico falhar numa panorâmica; a finalidade (separar câmera de referente) foi mantida.

## F. Resultados audiovisuais

**Nenhum documentário completo ≥60 s foi produzido nesta sessão.** Motivos precisos em H. Provas práticas realizadas:

- Render local real do `FilmeEditorial` (Remotion + Chrome do sistema, sem download) com três clipes/fotos reais do
  repositório (`tests/midia/*`, Canal do Panamá e NASA): quadros antes/depois inspecionados visualmente; a legenda deixou
  de cobrir o convés do navio. A narração usada foi um WAV de silêncio apenas para habilitar a faixa de legenda no
  compositor — **não é prova de sincronia nem filme narrado**. Artefatos locais, não versionados.
- Varredura em clipes reais do repositório: fusão do timelapse do Panamá detectada como transição (2,6–3,4 s), dois
  planos; custo medido em arquivo de 496 s 720p: **17,4 s de CPU local**, 720 quadros.
- Nenhuma folha nova inspecionada, nenhuma entrega Telegram, nenhuma publicação.

## G. Eficiência

- Chamadas de IA do motor: **0**. Custo: **USD 0**. Downloads de mídia: **0** (rede da sessão bloqueada a provedores;
  CI só leu checkpoints privados já existentes).
- Reuso comprovado no CI: 9 análises privadas reaproveitadas no replay e 9 no fluxo normal.
- Economia esperada (não medida com IA real): a varredura substitui janelas cegas; em arquivos longos, a segunda chamada
  no mesmo clipe só ocorre se houver plano promissor não observado — exatamente o desperdício da E281.2 (2 chamadas,
  6 janelas, 0 aprovação). Para clipes ≤ 30 s, a varredura custa < 1 s.
- Render: a config passa a aplicar `concurrency 1`/`swangle`/JPEG 92 também nos workflows que só exportavam
  `REMOTION_CHROME`; flags explícitas na linha de comando continuam prevalecendo.

## H. Limitações restantes

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

## I. Matriz final de capacidades

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

## J. Instruções para auditoria

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

## K. Parecer de encerramento

**A fase corretiva NÃO pode ser encerrada.** As causas-raiz reproduzíveis sem recurso pago foram corrigidas, com
regressão permanente e validação no CI (incluindo replay real de checkpoints privados). Falta a evidência prática
exigida pela própria missão: seleção de filmagem de ação com visão real após a correção e três documentários narrados
≥60 s em temas contrastantes. Ambos dependem de autorização explícita de orçamento de visão (H.1).

## L. Relatório de integração futura

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
