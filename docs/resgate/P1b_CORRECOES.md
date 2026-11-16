# P1b — correções da auditoria de 16/11 (sobre e8cc5dc)

**Branch:** `piloto-v24-lagartixa` · **Escopo:** só os trechos reprovados e a falha crítica de P0. Sem MP4 completo,
sem NTC, `main`, produção, merge, publicação ou Telegram. Provedores pagos continuam desabilitados.

## P0 — custo pago não pode ser omitido (`src/caixa.py`)

- Provedor que cobra (`pago`/`confirmar`) só é chamado com: teto ratificado + pior caso > 0 + **medidor** que lê a
  cobrança real da resposta. Sem medidor → negado antes de chamar. Hoje nenhum provedor que cobra tem medidor: Cloudflare
  e imagem do Gemini ficam negados mesmo com ratificação.
- Medidor que não lê (None, NaN, negativo, erro), falha da chamada ou `depois()` sem cobrança → registra o **pior caso**
  e trava os pagos do vídeo. Reserva aberta por execução que morreu → vira gasto no pior caso na próxima abertura.
  Provedor declarado grátis cuja resposta mostre cobrança → registra e bloqueia o provedor.
- **Entre runners:** armazém `git` — ramo `caixa-livro`, um arquivo cifrado (Fernet, chave do `CHECKPOINT_KEY`) por
  vídeo; cada mudança é um commit com push **sem força** (compare-and-swap: push recusado → relê e decide de novo).
  Exclusão entre runners por arrendamento gravado no livro. `v3-validacao.yml` usa `CAIXA_ARMAZEM=git`.
- Testes (`tests/test_v3_p0_travas.py`, 38): caminho real de `imagens._uma`→`_klein`, `gemini._tentar`, `voz._rest_tts`
  e `claude.pedir` com HTTP/CLI simulados; omissão/medidor quebrado/falha → pior caso; varredura de todas as chamadas
  `caixa.operar` em `src/`; **reexecução independente** com repositório remoto e dois clones em processos separados:
  o segundo runner vê o gasto do primeiro e é negado no teto; runner morto no meio → arrendamento segura e a reserva
  vira gasto; dois runners simultâneos → só um abre; livro remoto cifrado. Repetido 5× sem instabilidade.
- Limite: compare-and-swap e arrendamento foram testados contra um repositório local, não contra o GitHub real
  (nenhuma execução do V3 foi disparada). O alerta (0,60) e o teto (0,80) seguem como limite de segurança provisório.

## Visual — só os trechos reprovados (mesma voz, mesma narração)

| Trecho | Antes (P1) | Agora (P1b) |
|---|---|---|
| 12–15 s placa | foto de 1274×960 da parede, placa pequena e macia | placa frontal de 4052×2533 (Acabashi, CC BY-SA 4.0) na largura da tela, legível, acima da legenda; avanço lento até o parágrafo; sem contorno. Ponto da Pudding Lane no fim do mapa e centro da placa na mesma altura de tela (≈ y 780) |
| 38–44 s mapa | mapa inteiro em faixa pequena, metade de baixo escura | `cobrir`: mapa na altura toda; a câmera acompanha o avanço de leste para oeste (centro → muralha → oeste/Smithfield); nomes ~1,6× maiores. Marcador de Smithfield não cobre mais o nome |
| 47–49 s Golden Boy | foto de 480×640 (pequena ou macia) | foto de 3672×4041 (CC BY 2.0), do menino à inscrição de 1666, cobrindo o quadro |
| 49–58 s Monumento | foto cortava a urna e o chão | foto de 3840×5775 (donald judge, CC BY 2.0) com chão e urna; da base ao monumento inteiro em "ergueram"; linha de medida dos 61,5 m AO LADO do monumento, do chão ao topo da urna, com a câmera parada; sem rótulo (a legenda diz o número no mesmo instante) |

Mídia buscada por categoria do Commons pelo workflow de resgate (3 execuções de ~1 min, só download; catálogo completo
com tamanho e licença guardado no resultado cifrado). Auditoria de câmera e palco real: sem borda, sem encolhimento,
sem divergência; nenhuma degradação nova nesses planos.

## O que continua fraco

- **Placa:** sem cortar o texto, uma placa horizontal não cobre o quadro vertical; fica uma faixa escura sob a legenda
  (≈ 40% da tela no começo do plano, menos no fim).
- **Mapa:** "quase toda a cidade" não aparece inteira ao mesmo tempo (a câmera percorre); o fim do plano do mapa
  (7–12 s) ainda tem barra escura embaixo.
- **Monumento:** a linha de medida passa por trás da legenda; fica um aviso de zoom no limite em 22,6 s (fora destes trechos).

## Testes e custo

- Suíte inteira: **948 passam, 12 falham, 13 pulados** — as mesmas 12 falhas do `2beb111`.
- Cobrança efetiva: US$ 0. Actions: 3 execuções curtas do workflow de resgate (cota grátis). Nenhuma API paga.
- Chave pública desta sessão adicionada em `.github/piloto/chave_publica_sessao_p1b.asc` (a privada anterior se perdeu
  no reinício do ambiente; a nova fica só fora do Git).
