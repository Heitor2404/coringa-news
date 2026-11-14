# Validação com dados reais (coleta única no CI)

- **cenário**: registro montado no gabarito + visão rotulada · **registro real**: metadados coletados + visão rotulada · **real**: metadados coletados + resposta do Gemini cego (sem resposta do casamento → "incerto", nunca PROVA)

| Conjunto | Caso | Imagem | Esperado | Cenário | Registro real | Real (Gemini) | Gemini: natureza / confere / confiança |
|---|---|---|---|---|---|---|---|
| desenvolvimento | nav-01 | a6_commons | PROVA | PROVA | PROVA | RELACIONADA | satelite_ou_aerea / incerto / baixa |
| desenvolvimento | nav-02 | a9_openverse | RELACIONADA | RELACIONADA | sem registro | — | satelite_ou_aerea / incerto / baixa |
| desenvolvimento | nav-03 | a8_iss | PROVA | PROVA | PROVA | RELACIONADA | satelite_ou_aerea / incerto / baixa |
| desenvolvimento | nav-04 | a2_aster | CONTEXTO | CONTEXTO | CONTEXTO | RELACIONADA | satelite_ou_aerea / incerto / baixa |
| desenvolvimento | nav-05 | a1_roterda | CONTEXTO | CONTEXTO | sem registro | — | foto / incerto / baixa |
| desenvolvimento | nav-06 | a6_commons | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | satelite_ou_aerea / incerto / baixa |
| desenvolvimento | nav-07 | a10_outro_navio | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| desenvolvimento | nav-08 | a12_2020 | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| desenvolvimento | nav-09 | a0_diagrama | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | diagrama / incerto / baixa |
| desenvolvimento | nav-10 | a5_arabe | INCOMPATIVEL | INCOMPATIVEL | INCOMPATIVEL | INCOMPATIVEL | diagrama / incerto / baixa |
| desenvolvimento | nav-11 | a11_igreja | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa | (recuperado)
| desenvolvimento | nav-12 | a14_placa | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa | (recuperado)
| desenvolvimento | geo-01 | a25_rosenquist | PROVA | PROVA | sem registro | — | — |
| desenvolvimento | geo-02 | a25_rosenquist | PROVA | PROVA | sem registro | — | — |
| desenvolvimento | geo-03 | a25_rosenquist | CONTEXTO | CONTEXTO | sem registro | — | — |
| desenvolvimento | geo-08 | a0_memorial | CONTEXTO | CONTEXTO | sem registro | — | — |
| desenvolvimento | geo-09 | a23_animacao | CONTEXTO | CONTEXTO | CONTEXTO | — | — | (recuperado)
| desenvolvimento | geo-12 | a18_post | PROVA | PROVA | PROVA | — | — | (recuperado)
| reservado | ap-01 | as11_40_5903 | PROVA | PROVA | PROVA | RELACIONADA | foto / incerto / baixa | (recuperado)
| reservado | ap-02 | as11_40_5903 | CONTEXTO | CONTEXTO | CONTEXTO | RELACIONADA | foto / incerto / baixa | (recuperado)
| reservado | ap-03 | dvids_5903 | CONTEXTO | CONTEXTO | sem registro | — | — |
| reservado | ap-04 | s69_39525 | PROVA | PROVA | RELACIONADA | CONTEXTO | foto / incerto / baixa |
| reservado | ap-05 | s69_39525 | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| reservado | ap-06 | nhq2019 | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| reservado | ap-07 | as11_36_5355 | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| reservado | ap-08 | insignia | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | ilustracao_digital / incerto / baixa | (recuperado)
| reservado | ap-09 | lua_cheia | INCOMPATIVEL | INCOMPATIVEL | sem registro | — | — |
| reservado | bw-01 | b1110_018 | PROVA | PROVA | CONTEXTO | — | — | (recuperado)
| reservado | bw-02 | b1104_006 | INCOMPATIVEL | INCOMPATIVEL | INCOMPATIVEL | — | — | (recuperado)
| reservado | bw-03 | b1222_034 | CONTEXTO | CONTEXTO | CONTEXTO | — | — | (recuperado)
| reservado | bw-04 | b1118_018 | PROVA | PROVA | PROVA | — | — | (recuperado)
| reservado | bw-05 | b1109_030 | CONTEXTO | CONTEXTO | INCOMPATIVEL | INCOMPATIVEL | foto / incerto / baixa |
| reservado | tn-01 | loc_46682 | PROVA | PROVA | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| reservado | tn-02 | uw_290_52 | PROVA | PROVA | sem registro | — | — |
| reservado | tn-03 | commons_upload | RELACIONADA | RELACIONADA | RELACIONADA | CONTEXTO | foto / incerto / baixa |
| reservado | tn-04 | uw_290_33 | CONTEXTO | CONTEXTO | sem registro | — | — |
| reservado | tn-06 | fragmento | CONTEXTO | CONTEXTO | sem registro | — | — |
| reservado | mt-01 | jd_92417 | RELACIONADA | RELACIONADA | RELACIONADA | CONTEXTO | foto / incerto / baixa |
| reservado | mt-03 | jd_63251 | RELACIONADA | RELACIONADA | RELACIONADA | CONTEXTO | foto / incerto / baixa |
| reservado | mt-04 | jd_92418 | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| reservado | mt-06 | merian | CONTEXTO | INCOMPATIVEL | INCOMPATIVEL | INCOMPATIVEL | pintura / incerto / baixa |
| reservado | kt-01 | fema_15008 | PROVA | PROVA | PROVA | PROVA | satelite_ou_aerea / estado_final / alta |
| reservado | kt-02 | fema_14891 | PROVA | PROVA | PROVA | — | — | (recuperado)
| reservado | kt-03 | fema_17284 | PROVA | PROVA | PROVA | — | — | (recuperado)
| reservado | al-01 | goll_1876 | CONTEXTO | CONTEXTO | CONTEXTO | — | — | (recuperado)
| reservado | al-02 | von_corven | CONTEXTO | CONTEXTO | CONTEXTO | — | — | (recuperado)

- Falsas provas com dados reais: 0 []
- Provas esperadas não alcançadas com o registro real: 6 ['geo-01', 'geo-02', 'ap-04', 'bw-01', 'tn-01', 'tn-02']
- Sem registro real (ausência de evidência coletada): 11 ['nav-02', 'nav-05', 'geo-01', 'geo-02', 'geo-03', 'geo-08', 'ap-03', 'ap-09', 'tn-02', 'tn-04', 'tn-06']
- Natureza: catálogo real × rótulo do gabarito divergem em 3: ['nav-12 (rótulo cartaz, catálogo foto)', 'ap-08 (rótulo ilustracao, catálogo ilustracao_digital)', 'mt-06 (rótulo desenho, catálogo pintura)']
- Casamento real: só clima_katrina respondeu (coleta 43631002615); os 5 da recuperação 43634303551 deram 503 de novo.

## Recuperação 43634303551 (única, sem repetição)

- **Commons:** 16 entradas tinham falhado por 429.
  - 14 registros recuperados com consultas em lote e pausa; 2 buscas sem resultado (Rosenquist, memorial de Johnston Ridge).
  - 8 imagens baixadas. Outros 6 downloads levaram 429 de novo em upload.wikimedia e foram encerrados.
- **Gemini (6 chamadas novas, o limite):**
  - o catálogo das 4 imagens recuperadas dos domínios com casamento respondeu;
  - os 5 casamentos deram **503 de novo**: 0 respostas.

### Erros reais encontrados (regra NÃO alterada, conforme a ordem)

1. **bw-01 (rejeição indevida):** a foto de Checkpoint Charlie, de 10/11/1989, cai para CONTEXTO.
   - O gênero é lido de TODAS as categorias, e uma delas descreve um objeto dentro da cena ("You-are-entering-the-American-Sector **sign** at Checkpoint Charlie").
   - Além disso, a categoria real do acontecimento ("Fall and demolition of the Berlin Wall…") não contém o nome de referência "Fall of the Berlin Wall".
2. **nav-12 (risco de falsa prova, não materializado):** a placa do supermercado está na categoria do acontecimento.
   - Não há categoria de gênero, e o catálogo real a chamou de "foto", não de "cartaz".
   - Se o casamento disser "estado_final", nada a barra; com "ação", o catálogo (nada acontecendo) a barra.
3. **ap-04 (rejeição indevida):** a NASA devolve "APOLLO XI" sem palavras-chave.
4. **tn-01 (rejeição indevida):** o arquivo HABS traz a data da documentação ("after 1968"); a data da foto está no título.
5. **ap-01 / ap-02:** sem casamento, a foto certa fica RELACIONADA (revisão), nunca PROVA. Para a fala da decolagem, a foto da Lua também fica RELACIONADA (revisão) em vez de CONTEXTO, porque a fase não pode ser julgada sem a leitura do estado.

## Teste mínimo com modelo alternativo — execução 43635010212 (única, encerrada)

- **Diagnóstico sem geração** (`models.list` e `models.get`):
  - `gemini-3.8-flash` existe e está visível para a chave (versão 3.0, entrada de 1M tokens).
  - Os erros anteriores foram **503 UNAVAILABLE "high demand"**, do lado do Google. Não é cota da chave (seria 429) nem modelo inexistente (seria 404).
- **Escolha do alternativo:** `gemini-3.6-flash`, o próximo modelo principal na ordem do próprio projeto (`gemini.PRINCIPAIS`).
  - Uma chamada de casamento cego: 4 imagens já guardadas do Ever Given (a6, a10, a12, a1) × acontecimentos i6 (evidência direta, gabarito nav-01 = PROVA) e i2 (imagem enganosa a10, gabarito nav-07 = CONTEXTO).
- **Resultado: 503 UNAVAILABLE "high demand" de novo** (10 s). Sem resposta, não há precisão a medir. O teste foi encerrado, sem nova tentativa.
- **Impedimento registrado:** nesta janela, os modelos principais do plano grátis (3.8 e 3.6 flash) recusaram as chamadas de visão longas por sobrecarga.
  - Os modelos lite (3.5-flash-lite) responderam a todos os 7 catálogos.
  - Modelos visíveis que não testei: 3.7-flash e 3.5-flash.
- **Respostas brutas:** `tests/evidencia/coleta_real/teste_modelo_43635010212/`.

## Casamento com gemini-3.5-flash-lite — execução 43635338190 (uma chamada, sem nova tentativa)

- **Funcionou:** 3,5 s; 5.065 tokens de entrada e 771 de saída (plano grátis). 4 imagens × i6 (positivo) e i2 (negativo).
- **Identificação:**
  - i6 → **só a a6** ("navio encalhado de través", `acao`, confiança alta). As outras três vieram como `outro_estado`. Correto.
  - i2 → a a6 veio como `nao_mostra`; a10 (homônimo de 2011 navegando), a12 e a1 vieram como `entidade`. Não confundiu nada com prova.
- **Avaliação pela regra (inalterada), com registros reais e catálogo real:**
  - **nav-07 (a10 × i2): CONTEXTO = gabarito.**
  - **nav-08 (a12 × i2): CONTEXTO = gabarito.**
  - **nav-01 (a6 × i6): CONTEXTO ≠ gabarito (PROVA). É rejeição indevida.**
    - O casamento disse `acao` para o navio preso.
    - O catálogo, em outra chamada, disse "nada acontecendo".
    - A trava de discordância catálogo × casamento derrubou a confirmação.
    - O gabarito rotula a cena como `estado_final`.
  - **Falsas provas: 0.**
- **Achado:** o modelo lite chama de "ação" um estado resultante (navio já preso) e de "entidade" uma ação real (navio navegando). A fronteira ação × estado final é o ponto fraco. Com a regra atual isso gera rejeição, não falsa prova.
