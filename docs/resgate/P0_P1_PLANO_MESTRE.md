# P0 + P1 do Plano Mestre V1 — travas, câmera e montagem (Londres 1666)

**Data:** 16/11/2026 · **Branch:** `piloto-v24-lagartixa` · **Partiu de:** `2beb111` (HEAD confirmado, igual a `origin`)
**Escopo:** só P0 (segurança/custo) e P1 (câmera/montagem). Nada de G/B/C, nada de NTC, `main`, merge, publicação ou Telegram.
**Estado:** correção técnica comprovada por teste e por prévia; **qualidade artística NÃO declarada** — depende do Heitor.

## 1. Diferenças entre o Plano Mestre e o HEAD (antes de mexer)

| Plano Mestre diz | O que o código mostrou |
|---|---|
| V3 com 0 bloqueios não tem gate humano | Pior: `_fazer_curiosidade` gravava `APROVADO_FISCAL` e chamava `telegram()` (só não enviava porque `v3-validacao.yml` não passa as chaves do Telegram). Não existe postagem automática em rede social no código. |
| `orcamento_video` não protege dinheiro | Confirmado (modo monitorar, "não bloqueia"). Provedores hoje: Claude por OAuth (assinatura), Gemini/Groq com chaves grátis, Pollinations grátis, Cloudflare Workers AI (plano da conta desconhecido). |
| `doc.plano` usa `(H−380)/c.h` e fundo desfocado; `fixo` faz 3% de zoom | Confirmado, e a escala podia ficar abaixo da que cobre o quadro **no meio** do movimento. |
| Prompt "documentário" e "Varie transições"; E-ATENCAO > 3 s | Confirmado; o prompt do V2 (`PROMPT_DIRETOR`) também pedia variar transição; 8 das 14 receitas tinham dissolve/whip/iris como padrão. |
| Limite rígido antigo de 80 s | Em `main._aplicar_porteiro` (caminho antigo/V2; o V3 não passa por ele). Também `roteiro.LIMITE_PALAVRAS = 160` (≈ 55–60 s), que conflita com o mínimo de 65 s. **Não alterado** (fora de P0/P1). |
| 815/12/13 na suíte | Reconfirmado no mesmo diretório: no `2beb111`, os 12 testes listados no §4 falham. |

## 2. O que foi corrigido (P0)

**Publicação** — `src/v3/estado_final.py` + `main.py` (só o ramo V3):
`BLOQUEADO` · `AGUARDANDO_APROVACAO_HUMANA` (máximo automático) · `APROVADO_HUMANO` (exige `humano:<nome>:<data>`) ·
`PUBLICAVEL` (exige aprovação **e** autorização separada; nenhum código chega lá nesta etapa). Revisão multimodal ausente
ou sem visão = pendência. Dois portões: o fluxo e o próprio `telegram()` recusam tudo que não é `PUBLICAVEL`.

**Dinheiro** — `src/caixa.py` (novo; ligado em `claude.py`, `gemini.py`, `voz.py`, `imagens.py`; aberto só com `MOTOR_VISUAL=v3`):
- três métricas separadas: cobrança efetiva, crédito de assinatura, cota grátis;
- faturamento declarado por provedor; desconhecido → negado; "pode cobrar" (Cloudflare, imagem do Gemini) → negado até
  `CAIXA_RATIFICADO=humano:<nome>:<data>`;
- preflight: cobrado + reservado + pior caso + futuros ≤ teto (0,80 **provisório, não ratificado**); custo desconhecido → negado;
- limites: 4 tentativas pagas por etapa, 200 chamadas, 90 min; falha também conta; total persistido entre retries/jobs;
- segunda execução do mesmo vídeo não abre o caixa (trava de arquivo);
- negação vira estado `BLOQUEADO_ORCAMENTO` (não degrada a edição).

## 3. O que foi corrigido (P1)

| Defeito | Correção | Arquivos |
|---|---|---|
| Foto encolhia e mostrava cópia desfocada | Layout explícito: `cobrir` (escala ≥ cobertura em todo o caminho; fundo nunca aparece) × `integral` (documento/mapa inteiro sobre mesa escura; sobra só abaixo da linha da legenda). Escolha automática **registrada** (`LAYOUT-INTEGRAL`, `ENQUADRAMENTO-CORTADO`, `RESOLUCAO-BAIXA`). | `doc.js`, `geometria.py`, `diretor.py` |
| `fixo` com zoom | Uma chave, nenhuma transformação. | `diretor.py` |
| Detalhe da placa sob a legenda (antes e na 1ª tentativa) | `integral` aceita barra escura só abaixo da legenda e prefere composição limpa quando o assunto anda < 250 px. | `doc.js`, `geometria.py` |
| Arranque/freada bruscos | Seno in-out (pico 1,57× a média; o cúbico dava 3×). | `doc.js`, `geometria.py` |
| Percurso torto (no zoom do Monumento o quadro descia e voltava) | Centro interpolado em linha reta + limite por quadro. | `doc.js`, `geometria.py` |
| Movimento acelerado "porque a palavra mudou" | Duração mínima pela distância (zoom ≤ ~45%/s, pan ≤ 700 px/s no pico) e pausa mínima de 0,5 s entre movimentos; o que não cabe vira revisão (`MOVIMENTO-SEM-TEMPO`). | `diretor.py`, `geometria.py` |
| Zoom de transição + zoom de câmera | Vira corte, registrado. | `diretor.py` |
| Incentivo a variedade gratuita | Prompt multitemático; transição "corte" por padrão e só com motivo; `layout` no contrato; receitas com corte por padrão (a motivada ficou anotada); fiscal não pune plano fixo (nota estética só > 6 s) e acusa imagem parada onde se pediu movimento. | `pipeline.py`, `diretor.py`, `receitas.json`, `fiscal_editorial.py` |
| Fiscal de 4 quadros não via movimento | `geometria.auditar_dados` (espelho, quadro a quadro: borda, encolhimento, salto, pan/zoom rápido, aceleração, para-e-anda, resolução) + `auditar_palco` (Chromium real, `window.geometria`, compara com o espelho). Roda na prévia; borda/encolhimento/divergência = replanejamento, persistindo = bloqueio. | `geometria.py`, `nucleo.js`, `pipeline.py`, `supervisionado.py` |

**Storyboard supervisionado de Londres:** um só ajuste, no Monumento (49–57 s): antes subia ao topo e voltava (zoom 49%/s,
salto de 42 px num quadro); agora é um movimento só, da base à coluna inteira em "Monumento". Mesmas mídias e mesma voz.

## 4. Testes (execução real)

- Novos: `tests/test_v3_p0_travas.py` (19), `tests/test_v3_geometria.py` (94, incluindo 80 trajetórias aleatórias e o
  palco real × espelho), `tests/test_v3_fiscal.py::test_plano_fixo_nao_e_punido_e_movimento_parado_e`.
- Prova de que o teste do palco pega o defeito: com o encolhimento reintroduzido no JS, ele falha com `G-BORDA` e `G-ESPELHO`.
- `tests/test_v3_*.py`: 178 passam.
- Suíte inteira: **928 passam, 13 falham, 13 pulados**. As 12 falhas abaixo **também falham no `2beb111`** (rodadas no mesmo
  diretório com as mudanças guardadas):
  `test_etapa1_confiabilidade::test_gancho_do_polvo…`, `test_fase1_m1_m2_lote::test_critica_e_ganchos…` (×2),
  `test_fase3_acontecimentos::test_casar_volta…`, `test_polvo::test_casamento_registra…`, `test_v21` (×3),
  `test_v22_contrato::test_criterios_c1_a_c5`, `test_v22_inedito` (×2), `test_v25_matriz::test_dev_todos_passam`.
  A 13ª, `test_v2::test_regressao_visual_contra_referencias`, falhou por causa desta mudança: a referência do `doc.plano`
  registrava o defeito (imagem em faixa, preto embaixo). Referência regenerada com `python -m src.v2.regressao --atualizar --so doc.plano`
  e comparação guardada em `docs/resgate/p1_referencia_doc_plano_antes_depois.jpg`. Com isso: **12 falhas, as mesmas de antes**.
- Testes antigos com expectativa alterada de propósito (comportamento mudou por decisão do Plano Mestre):
  `test_v3_diretor::test_movimento_imperceptivel_e_corrigido` (fixo agora é fixo), `test_v3_resgate::test_camera_anotacao…`
  (duração mínima pela distância), `test_v3_resgate::test_anotacao_essencial…` (procura a degradação pelo código, não pela posição).
- Memória: ERR-027 a ERR-032 em `docs/memoria/erros.json`; `python -m src.v3.memoria conferir` íntegro.

## 5. Antes × depois (mesmos arquivos, mesma voz)

Três vídeos lado a lado (antes `2beb111` | depois): **7–19 s**, **33–47,5 s** (mapa), **46,5–58 s** (Golden Boy + Monumento).
- 7–19 s: o mapa deixa de flutuar sobre a cópia desfocada; o detalhe da placa sobe para cima da legenda; a xilogravura cobre o quadro.
- 33–47 s: mesma progressão; sem cópia desfocada embaixo. O mapa continua ocupando só a metade de cima em 38–44 s (ver §7).
- 47–58 s: Golden Boy deixou de ser ampliado 3× (macio) e virou foto inteira e nítida, pequena, sobre fundo escuro; o
  Monumento faz um movimento só. O topo com a urna em chamas deixou de aparecer.
- Auditoria de câmera da versão nova (Londres inteiro): 0 borda, 0 encolhimento, 0 divergência palco × espelho; restam
  2 avisos de zoom no limite (45%/s) em 22,6 s e 38,5 s.
- **MP4 completo não foi renderizado** nesta etapa: o Plano Mestre pede o completo só depois da validação dos trechos.

## 6. Custos

- Cobrança efetiva: **US$ 0**. Nenhuma API paga foi chamada; nenhuma narração nova (áudio reaproveitado do resgate).
- Créditos: esta sessão do Claude Code (assinatura). Cotas: nenhuma chamada ao Gemini/Groq; Actions: 0 execuções.
- Teto de US$ 0,80/alerta 0,60 implementado como **configuração provisória**; nenhum provedor que cobra é chamado até a ratificação.

## 7. O que continua ruim, não validado ou só simulado

- **Mapa 38–44 s:** em `integral`, o mapa ocupa só a metade de cima; embaixo fica a barra escura da legenda. É intencional
  (não é sobra acidental), mas visualmente fraco. Decisão de direção: cobrir com recorte, ou outro enquadramento.
- **Golden Boy (47–49 s):** nítido mas pequeno (cartão sobre fundo escuro). Precisa de mídia melhor.
- **Placa (12–15 s) e mapa:** abaixo da legenda há barra escura em alguns trechos. Funciona como faixa de legenda, mas não foi aprovado por você.
- Limites de velocidade (45%/s, 700 px/s), pausa de 0,5 s e margem de 250 px são **valores iniciais meus**, não estética aprovada.
- A abertura (0–7 s, pintura de 1675) entrou em `integral` automaticamente (o enquadramento final era largo); não foi revisada nesta etapa.
- A trava financeira foi testada com provedores simulados; nenhuma cobrança real passou por ela. O faturamento de Gemini/Groq
  é declarado como "cota grátis" por configuração — se alguma conta ganhar faturamento, é preciso mudar a declaração.
- Revisão multimodal com visão ainda não rodou aqui (sem chave); fica como pendência no estado final.
- `roteiro.LIMITE_PALAVRAS` (≈ 55–60 s) e o porteiro de 80 s não foram tocados (P2).

## 8. Próxima etapa (depende da sua aprovação)

1. Você assiste aos três antes/depois e diz por timestamp o que aprova e o que não.
2. Com o OK: MP4 completo de Londres com a câmera nova (sem nova narração, custo zero).
3. Ratificar (ou mudar) o teto de US$ 0,80/0,60 antes de qualquer provedor pago.
4. Só depois: P2 e os testes G/B/C com o diretor automático.
