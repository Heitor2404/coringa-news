# Correção estrutural da direção audiovisual (16/11/2026)

Ramo `piloto-v24-lagartixa`, partindo de `4b2aa20`. Sem nova versão de Londres, sem merge, sem publicação, sem NTC/main/
produção. **Nada aqui é aprovação artística**: o fiscal mede decisões, e só o Heitor aprova.

## 1. Diagnóstico (por que o motor decidia mal)

| Defeito visto em Londres | Causa raiz | Onde |
|---|---|---|
| gancho começa cheio e encolhe (1,00 → 0,46) | receita R-GANCHO-IMPACTO mandava `detalhe → contexto` + revelar | `src/v3/receitas.json` |
| gravuras e mapa recuam até virar faixa | R-REVELACAO-FINAL (`objeto → geral`), R-LOCALIZA-RECUA e `camera('localizar')` recuavam sempre | `receitas.json`, `src/v2/diretor.py` |
| receita "testada" tratada como padrão | o prompt mostrava receitas não aprovadas como guia | `src/v3/receitas.py` |
| cartão sobre fundo escuro | qualquer enquadramento mais largo que 9:16 caía no layout `integral` | `src/v2/diretor.py` (bloco de layout) |
| até o "geral" virava cartão | o 'geral' era calculado em 1080×1540, mais largo que o quadro | `diretor.enquadramento` |
| tudo virava foto com zoom | forma visual não existia; `doc.plano` era a saída padrão; mídia sem natureza (mapa/documento/gravura) | `pipeline.py`, `plano_av.py` |
| fiscal aprovava decisão ruim | não media ocupação, legibilidade de mapa nem queda de presença | `src/v3/fiscal_editorial.py` |

## 2. O que mudou

- **Forma antes da câmera** — `src/v3/linguagem.py`: registro, mapa, esquema, documento, comparação, tipografia por
  acontecimento; ação essencial (mecanismo, processo, transformação, movimento…) não aceita foto com zoom. Regras das
  quatro referências unificadas em `docs/v3/LINGUAGEM_CORINGA.md`.
- **Composição** — `src/v3/decisao.py`: vertical que preserva o importante → outra mídia do acervo → editorial (visão
  geral + detalhe, só para documento mais largo que o painel) → revisão/bloqueio. Cartão automático removido.
- **Câmera** — fixa por padrão; recuo só com `revela` (região fora antes, dentro depois, objeto principal mantido);
  movimento imperceptível vira fixo; gancho com recuo sem `revela` é recusado pelo validador.
- **Fiscal de decisão** — `fiscal_editorial.decisoes`: imagem pequena, queda de ocupação, gancho que perde impacto,
  objeto fora, mapa ilegível, anotação prejudicada, crítico sem representação, ação sem esquema. Limites calibrados
  em 13 vereditos humanos (`tests/dados/londres_decisoes_humanas.json`): aprovados 1,00; reprovados 0,31–0,65.
  Julgamento semântico continua como revisão obrigatória.

## 3. Testes de regressão

Escritos antes da correção: no motor `4b2aa20`, **19 falham** (`docs/v3/evidencia/regressao_motor_4b2aa20.txt`) —
abertura com recuo, gravura em cartão, mapa ilegível/vazio, documento horizontal sem editorial, fiscal × veredito
humano. Agora passam (`tests/test_v3_decisao_visual.py`, `test_v3_linguagem.py`, `test_v3_microcena.py`). Nenhuma
exceção para Londres no motor (sem nomes de arquivo nem coordenadas). Suíte inteira: só as 12 falhas de ambiente já
conhecidas.

## 4. Microcenas (execução 43930812668, uma tentativa cada)

Recorte por regra (`src/v3/microcena.py`): um acontecimento do tipo pedido, ~5–8 s, de roteiros já pesquisados; o
diretor automático real decidiu tudo. Prévias enviadas ao Telegram privado autorizado (não é publicação).

| Microcena | Decisão do diretor | Fiscal | Leitura honesta |
|---|---|---|---|
| História (Titanic, abertura) | 2 fotos, registro, cobrir, câmera fixa | 0 bloqueios, 1 revisão: objeto 55% fora no plano 1 | sem recuo nem cartão; quadro cheio. O 2º plano corta o navio — o fiscal pegou |
| Geografia (Panamá) | mapa → editorial | **bloqueado**: selo × crédito (ERR-008) | não houve rota/propagação; revelou ERR-041 (corrigido depois, sem nova execução) |
| Biologia (lagartixa) | foto + `mecanismo.estados` (esquema) | 0 bloqueios, revisões E-PARADO/E-VAZIO | a forma certa foi escolhida, mas o esquema é pequeno e ocupa pouco do quadro |
| Ciência (céu azul) | `processo.etapas` (esquema) | 0 bloqueios, revisões E-PARADO/E-VAZIO | forma certa, demonstração fraca: quadro quase vazio, não mostra o espalhamento |

A revisão multimodal falhou em todos os planos (ERR-040: enviava o caminho em vez da imagem) — corrigida com teste.

## 5. Custo

Cobrança efetiva **US$ 0,00**. Crédito de assinatura (Claude Code, `sonnet`) consumido: 0,078 + 0,157 + 0,131 + 0,125 =
**US$ 0,49** nas quatro. Gemini na cota grátis (22 chamadas). Nenhum provedor pago ativado; teto 0,80 / alerta 0,60
mantidos. Nenhuma geração por IA de imagem ou vídeo.

## 6. Limitações (não resolvidas)

- Limites do fiscal calibrados em só 13 exemplos de um único vídeo.
- Natureza da mídia por palavras-chave no título/descrição — pode errar.
- Componentes de esquema (`mecanismo.estados`, `processo.etapas`) desenham pequeno: a forma é decidida, a
  demonstração ainda é fraca. O fiscal acusa como revisão (E-VAZIO), não bloqueia.
- Nenhuma microcena provou mapa com rota/propagação.
- No editorial, rótulo de ponto fora da janela de detalhe aponta para a borda.
- Troca por `alternativas` mantém anotações pensadas para a mídia anterior.
- ERR-040 e ERR-041 corrigidos sem nova execução real (uma tentativa por caso); refazer Panamá depende de autorização.
- `ArmazemGit` do caixa ainda não validado entre execuções reais.
