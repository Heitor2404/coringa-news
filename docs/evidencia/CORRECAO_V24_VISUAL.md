# V2.4 — Correção visual prioritária após o MP4 43730252500 (nota 2/10)

Ramo experimental `piloto-v24-lagartixa`. Sem merge, sem alteração da main, do NTC, da produção ou da identidade visual.

## Causa raiz confirmada
`capacidades._pelo_contrato` passava os `dados` do contrato **crus** para a composição. Frases inteiras
("deslocamento temporário da nuvem eletrônica em uma molécula") viravam nós/etapas de `diagrama.explicativo` e
`processo.etapas` com ícone genérico; `forcas.vetores` recebia `["forças de Van der Waals"]` (sem ângulo → seta sem
objeto). Nenhuma composição mostrava objeto, estado inicial, mudança e resultado.

## O que mudou (genérico — nada específico da lagartixa)
| Fase | Mudança | Onde |
|---|---|---|
| 1 | Composição nova `mecanismo.estados`: objetos genéricos (superfície, corpo, cerdas, ramos, partículas, seta), 2–4 estados que interpolam, relações (atração/repulsão/contato/empurra) que aparecem com a intensidade, faixa INÍCIO → RESULTADO, selo "ESQUEMA · FORA DE ESCALA" (nunca parece foto/micrografia) | `src/render/v2/comp/ciencia.js` |
| 1 | `processo.etapas`/`diagrama.explicativo` aceitam strings sem quebrar; `forcas.vetores` tira o sentido do nome (peso ↓, empuxo ↑…) e **não desenha** força sem sentido conhecido | idem |
| 1 | Mecanismo **crítico** não é representado por cartão de frases (nó/etapa > 24 caracteres): `contrato.comp_aceita` no preparo, no seletor e no fiscal (S8) | `contrato.py`, `preparo.py`, `capacidades.py`, `fiscal_v2.py` |
| 2 | **Prévia visual antes da narração** (`src/v2/previa.py`): renderiza no palco real cada composição crítica (início/meio/fim), bloqueia erro de render, texto fora/sobreposto, área vazia e início = fim; grava `folha.jpg` + `previa.json` | `main.py` |
| 3 | Fiscal: D15 (mesma foto > 4 s seguidos), D16 (mesma foto em cenas consecutivas), S9 (cena crítica com esquema/reconstrução pendente), S8 (mecanismo só escrito); `ESTATICO_MAX` 5 → 4 s | `fiscal_v2.py`, `montagem.py` |
| 4 | Roteiro revisado por edição auditada do checkpoint (sha256 das falas removidas; fatos novos só com fonte): ver `.github/piloto/edicao.json` | `checkpoint.editar` (ops `substituir_eventos`, `acrescentar_fatos`, `regenerar`) |
| 5 | Áudio medido **no MP4 final** (depois do AAC) e corrigido até −14 ± 0,5 LUFS e ≤ −1,2 dBTP (histórico em `*.audio.json`) | `render.final_medido` |
| 5 | Kicker nunca corta palavra; revelação: detalhe só do conteúdo final validado, quebra em 2 linhas se não couber, e fica sobre o **resultado do último esquema** (só formas, sem texto concorrendo); encerramento na tipografia de título; falas repetidas de planos da mesma ideia entram uma vez | `montagem.py`, `editorial.js` |
| 5 | Ilustração identificada (e2) = **revisão humana S7**, nunca prova e nunca S5 | `fiscal_v2._adequada` |

## Roteiro (edição auditada sobre o checkpoint 43730252500)
Sai: e3 (desenho a0), dipolo instantâneo, "nome do fenômeno", repulsão/distância de contato (não visualizáveis em 60 s) e
metade do trecho da NASA (~10 s → ~6 s). Entra, cada um com esquema demonstrativo:
cerdas na lamela → espátulas → atração ao encostar → Van der Waals só de perto → soltar descolando da ponta → soma segura
o peso. A conclusão volta para a lagartixa (revelação sobre o esquema "somadas, seguram o peso").

Fontes acrescentadas (com o trecho na pesquisa): Autumn et al., PNAS 2002 (nota da UC Berkeley: até 500 mil cerdas por pata,
centenas a mil espátulas por cerda, soma até ~1000× o peso); Huber et al., PNAS 2005 (hierarquia lamela → cerda → espátula);
Scientific American e Higham & Russell, J. Exp. Biol. 2025 (dedos descolam a partir da ponta; > ~30° desfaz a adesão);
NASA, 4 fev. 2025 (Suni Williams e o Astrobee com braços de almofadas inspiradas em lagartixas).
Nota de rigor: a analogia "como fita adesiva" foi **evitada** (Autumn et al. 2006 rejeitam que os dedos descolem como fita).

## Cobertura visual (simulação offline do mesmo checkpoint + edição, mesmo renderizador; tempos de fala estimados)
| # | Fala (resumo) | Composição | Representa |
|---|---|---|---|
| 0 | Ubatuba, caça no teto sem cola | abertura.pergunta (foto a16) | gancho |
| 1 | Faixas = lamelas | banner.discreto ILUSTRAÇÃO (a3, 3,6 s) | ilustração identificada → revisão S7 |
| 2 | Lamela coberta de cerdas | mecanismo.estados | dedo → lamela ampliada → cerdas |
| 3 | Ponta abre em espátulas | mecanismo.estados | 1 cerda → ponta se abre → centenas de pontas |
| 4 | Encostadas, moléculas se atraem | mecanismo.estados | longe/sem atração → encosta → atração (+/−) |
| 5 | Van der Waals só de perto | mecanismo.estados | colada forte → um pouco longe fraca → longe ≈ 0 |
| 6 | Soltar descolando da ponta | mecanismo.estados | presa → ponta se ergue → descola aos poucos |
| 7 | Somadas, até 1000× o peso | mecanismo.estados | 1 atração fraca → somam → seguram o peso |
| 8–9 | NASA 2025, braços que grudam | foto.documental a9 → a13 (fotos diferentes, < 4 s cada) | registro real |
| 10 | Revelação | revelacao.surpresa sobre o resultado do esquema 7 | resposta |
| 11 | Encerramento | encerramento.editorial | marca + fontes |

Prévia: 6/6 composições críticas OK (início ≠ fim, sem texto fora/sobreposto, sem erro).
Fiscal da simulação: **0 bloqueio**, 1 revisão (S7 da ilustração e2, por desenho), A1 −14,5 LUFS / −1,6 dBTP.
Genericidade: os mesmos testes renderizam esquemas da ponte de Tacoma, do Ever Given e do dique do Katrina (`tests/test_v24_previa.py`).

## Testes
`pytest tests/`: 725 passaram; as 7 falhas são as mesmas da linha de base anterior a esta correção (polvo/lote/fase3/v21
rota e fiscal antigo). Expectativas antigas ajustadas só onde a regra mudou por pedido explícito (mecanismo crítico em
cartão de frases agora bloqueia; D15/D16 são regras novas): `test_v24_contratos`, `test_v24_selecao`,
`test_v24_fluxo_integrado`, `test_piloto_correcao` — cada ajuste comentado no próprio teste. Referências visuais
regeneradas só para `mecanismo.estados` (nova) e `encerramento.editorial` (tipografia unificada).

## Execução real 43740293581 (retomada única de 43730252500)
- Pré-validação, preparo e **prévia: 6/6 esquemas OK**, sem chamada de IA de contrato; 50,3 s; áudio final −14,6 LUFS / −1,4 dBTP (A1 resolvido).
- **FALHA_OPERACIONAL**: o checkpoint 43730252500 guardado no cache estava **sem as imagens do acervo**. Causa: a limpeza
  pós-vídeo (`main.py`) apagava a pasta das imagens do acervo — que, numa retomada, é `<checkpoint>/arquivos`. Sem
  fotos, e2 e e9 viraram texto (o fiscal bloqueou corretamente com S5) e, com `arq` vazio, `Path(None)` derrubou a execução
  depois do MP4. Os planos novos e9/e10 também não tinham id de imagem. Corrigido (`_limpar_acervo`, id de imagem
  automático) com testes.
- Incidente: o commit de entrega limpou `retomar.txt` sem `[skip ci]` e disparou uma execução nova (43740825165);
  cancelada na preparação do ambiente, antes do pipeline (sem chamada de modelo, sem vídeo).
- Edição para a nova retomada (se autorizada): `base_run` 43728184399 (último checkpoint com as imagens); edição e2/e13
  já auditada + a desta correção; resultado conferido idêntico (falas, resumo, suspense, fatos) ao roteiro editado de 43730252500.
