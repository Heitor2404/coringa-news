# Coringa Explica — Correção estrutural do Motor V2 (V2.5) · relatório consolidado

Branch `piloto-v24-lagartixa` · base `567caca` · commits `e182ea8` (estrutural) e `7b21bdc` (correções vindas dos pilotos reais).
Nada foi feito em `main`, produção ou NTC. Não houve merge, publicação nem envio ao Telegram. Nenhum serviço pago foi adicionado.

## Resumo honesto

| Categoria | Resultado real | Veredito |
|---|---|---|
| Ciência (gelo flutua) | `BLOQUEADO_MATERIAL` antes do roteiro: 2 imagens específicas de 3 exigidas (porteiro de viabilidade que já existia) | **NO-GO** — sem MP4 |
| História (Pompeia) | **MP4 gerado** (62,6 s), fiscal V2.2 **reprovou** (D16) e o vídeo tinha defeitos visíveis que o fiscal não pegou (ver abaixo) | **NO-GO** para o MP4 real; correções feitas e conferidas offline |
| Engenharia (eclusas do Panamá) | `BLOQUEADO_PREPARO` antes da narração: o plano vinculante achou 2 cenas sem representação executável (e4 tipo desconhecido; e5 processo sem etapas) | **NO-GO** — recusa correta, sem MP4 |

Nenhum dos 3 pilotos reais terminou com MP4 aprovado. Não houve retentativa. O problema estrutural de fundo ainda existe: o
roteirista (IA) entrega acontecimentos sem dados para a tela, e o ajuste por IA ficou indisponível no Panamá — o limite
semanal do Claude já tinha estourado e as cotas diárias do Gemini acabaram no meio do piloto (impedimento operacional, não de código).

## Causas estruturais corrigidas

1. **Plano visual vinculante** (`src/v2/plano_exec.py`, novo). Monta o plano por acontecimento antes da narração (fato + fonte,
   sujeito/ação/local/época/resultado, recurso, tipo de representação, dados obrigatórios, status REPRESENTÁVEL /
   REPRESENTÁVEL_COM_REVISÃO / INVIÁVEL, justificativa, limites). Faz um único ajuste; depois retira no máximo 2 acontecimentos,
   e só se a estrutura não quebra (gancho, revelação e fechamento ficam, anáfora é respeitada, ≥ 4 narrativos). Se não der, recusa
   antes da narração. O plano fica no checkpoint e no status.
2. **Estados do pipeline** (`src/v2/estados.py`, novo): PESQUISA_VALIDADA → ACERVO_VERIFICADO → PLANO_VISUAL_EXECUTÁVEL →
   ROTEIRO_VALIDADO → PRÉVIA_APROVADA → NARRAÇÃO → RENDER → FISCAL, cada um com hash das entradas, resultado, causa, artefatos e custo.
3. **Documentário histórico** (`preparo.py`). Um fato com fonte e sem foto do instante vira CONTEXTO identificado
   ("… · não é o instante"), nunca prova. Fato sem fonte → bloqueio "retirar ou qualificar". Renderização ou recriação não vale
   como registro. O fiscal exige o selo CONTEXTO na tela. Foto de objeto avulso não serve de contexto para outro fato (Pompeia: a estatueta de um gato).
4. **Cobertura estruturada** (`cobertura.py`). Correspondência por sujeito, ação, estado, tempo, lugar, dados, relação e função
   documental. Identidade, data e dados são condições necessárias. Todo número na tela precisa estar na fala ou na pesquisa; o
   leitor entende números por extenso, aproximações e escala ("2,5 bi"). Composição trocada é renderizada e validada de novo.
5. **Falsos positivos m6/g3/g4.** São negativos reais agora: o dado declarado inválido bloqueia mesmo em cena de apoio, e números
   sem apoio na tela bloqueiam. O rastreio exige que números e nomes próprios estejam na mesma linha da fonte.
6. **Contratos** (`contrato.py`): `params_tela` é a mesma tela para prévia, cobertura e montagem. Os formatos do roteirista são
   normalizados sem inventar nada. Movimento não usa mais `mecanismo.nivel`. Número sem unidade recebe a unidade escrita no texto
   que o sustenta.
7. **Render/montagem**: a cena oculta esconde também os filhos que reverteram `visibility` — o ano da linha do tempo aparecia
   como fantasma no vídeo inteiro de Pompeia. O fiscal agora mede a visibilidade do próprio elemento. Planos seguidos com a mesma foto
   viram um plano só (D16), e a nota de destaque usa o selo NOTA, não CONTEXTO.

Arquivos: `main.py`, `src/roteiro.py`, `src/v2/{plano_exec,estados}.py` (novos), `src/v2/{preparo,cobertura,contrato,capacidades,
fiscal_v2,montagem,prevalidacao,previa,ensaio,matriz}.py`, `src/render/v2/{nucleo.js,estilo.css,comp/tempo.js}`,
`tests/test_v25_estrutural.py` (novo, 22 testes), `tests/test_piloto_correcao.py`, `tests/test_v24_fluxo_integrado.py`.

## Testes (resultado completo, incluindo falhas)

- Suíte completa: **767 passaram, 5 falharam, 4 pulados**. As 5 falhas já existiam antes deste escopo (dependem de prompts guardados
  no cofre privado ou do caso polvo): `test_etapa1_confiabilidade::test_gancho_do_polvo…`, `test_fase1_m1_m2_lote::test_critica_e_ganchos…` (×2),
  `test_fase3_acontecimentos::test_casar_volta_a_aceitar…`, `test_polvo::test_casamento_registra…`.
- O teste de render novo **falha no código antigo** (os anos 79 e 1748 ficam visíveis em outra cena) e passa no novo.
- Matriz congelada: **45/49**. As 4 divergências são todas conservadoras (nenhuma aprovação indevida):
  n2 (nome de mapa → revisão), e5 e m4 (ilustração sem base na pesquisa → revisão), x3 (série **sem unidade** "2.5" não confere
  com "2,5 bilhões" → bloqueio). Mudança de gabarito: só g3/g4/m6, que viraram negativos reais. A pesquisa de teste da ONU ganhou os
  pontos de 1970 e 1990, porque a série mostrava valores que a pesquisa não tinha. Fica registrado aqui como mudança de entrada, não de esperado.
- Expectativa ajustada: `test_fiscal_depois_so_bloqueia…` — o D16 sumiu porque os planos foram unidos; o D15 (foto parada) continua sendo exigido.

## Vídeos simulados completos (mídia local, voz simulada, sem IA)

| Caso | Resultado | Plano visual |
|---|---|---|
| Lagartixa | MP4, fiscal sem bloqueio, 2 revisões | 12 acontecimentos · 10 representáveis · 2 com revisão |
| Titanic | MP4, fiscal sem bloqueio, 5 revisões | 10 · 4 representáveis · 6 com revisão · retirados e9 (série inventada) e e3 |
| Torre de Pisa | MP4, fiscal sem bloqueio, 2 revisões | 11 · 7 · 4 · retirado e8 |
| Céu azul | **recusado antes da narração** (precisaria de mais de 2 retiradas; sem IA para ajustar) | — |
| Pompeia (checkpoint real, depois) | MP4, fiscal sem bloqueio, 3 revisões; sem o ano fantasma; a estatueta foi trocada por ruínas com o selo CONTEXTO | 12 · 7 · 5 |
| Panamá (checkpoint real, depois) | MP4, fiscal sem bloqueio, 1 revisão — **vídeo fraco**: o mecanismo da eclusa (e5) saiu, e uma cena de "forças" ficou genérica | 5 · 4 · 1 · retirados e5, e4 |

## Antes / depois (casos reais)

- **Pompeia, antes (MP4 real)**: "1748" em sobreposição em quase todos os planos; a estatueta de Bastet como "contexto" de um morador
  fugindo; "33" e "6" sem unidade; D16 (legenda de lugar + mesma foto). **Depois (offline, mesmo checkpoint)**: sem fantasma,
  contexto de ruínas, "33 quilômetros", "6 metros", planos unidos, fiscal sem bloqueio.
- **Panamá**: o real foi recusado antes da narração (correto). Offline, sem IA, o plano retira e4/e5 e gera um vídeo curto e pobre.
  Ou seja, o plano evita o erro, mas não cria conteúdo bom sozinho.

### Plano visual por acontecimento — Pompeia (piloto real)

| ev | tipo | recurso | representação | status |
|---|---|---|---|---|
| e1 | numero | abertura.pergunta | editorial | REPRESENTÁVEL |
| e2 | numero | numero.animado | dado | REPRESENTÁVEL |
| e3 | evento_historico | a3 | contexto | COM_REVISÃO |
| e4 | evento_historico | a0 (estatueta — erro, corrigido depois) | contexto | COM_REVISÃO |
| e5 | processo | processo.etapas | esquema | REPRESENTÁVEL |
| e6 | numero | numero.animado | dado | COM_REVISÃO |
| e7 | transformacao | processo.etapas | esquema | REPRESENTÁVEL |
| e8 | evento_historico | a6 | contexto | COM_REVISÃO |
| e9 | sequencia_historica | linha_tempo.historica | cronologia | COM_REVISÃO |
| e10 | mecanismo | revelacao.surpresa | editorial | REPRESENTÁVEL |
| e11 | transformacao | processo.etapas | esquema | REPRESENTÁVEL |
| e12 | numero | numero.animado | dado | REPRESENTÁVEL |

Estados: PESQUISA ✔ · ACERVO ✔ · PLANO ✔ · ROTEIRO ✔ · PRÉVIA ✔ · NARRAÇÃO ✔ · RENDER ✔ · FISCAL ✘ (D16).

## Fiscal e custo

Custo em dinheiro nos três pilotos: **USD 0,00**. O Claude bateu o limite semanal ("resets 5am UTC") e tudo seguiu no Gemini gratuito,
que também esgotou a cota diária de dois modelos durante o Panamá.

## Limitações que continuam

- O roteirista ainda declara acontecimentos sem dados para a tela, e o "tipo desconhecido" aparece. O plano bloqueia, mas não conserta.
  O conserto depende do ajuste por IA, que pode estar indisponível.
- O porteiro de viabilidade antes do roteiro rejeita temas de ciência com poucas fotos "específicas" (gelo).
- O fiscal ainda deixa passar fotos paradas por muito tempo em parte dos casos (o ritmo de Pompeia teve 68 % de trechos parados).
- A cobertura deixa para revisão humana o que não dá para provar sem olhar (ação numa foto, nome num mapa).

## GO / NO-GO

- **Ciência: NO-GO** (bloqueado por material; os simulados lagartixa e céu azul mostram o motor correto, mas o real não terminou).
- **História: NO-GO** para publicação; o caminho (contexto identificado, linha do tempo) funcionou e os defeitos achados no real foram corrigidos e testados, mas falta um piloto real limpo.
- **Engenharia/natureza: NO-GO** (recusa correta antes da narração; o roteiro dessa categoria ainda vem sem esquemas executáveis).
