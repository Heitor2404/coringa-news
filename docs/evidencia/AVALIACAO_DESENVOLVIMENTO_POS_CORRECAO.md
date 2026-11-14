# Avaliação desenvolvimento — após as correções da etapa 3

Grupo: **desenvolvimento** · 24 casos · acerto 24/24 · falsa prova **0** · recall de prova 7/7 · eventos 5/5

| Domínio | Casos | Acerto | Falsa prova | Prova reconhecida |
|---|---|---|---|---|
| naval | 12 | 12 | 0 | 2/2 |
| geologia | 12 | 12 | 0 | 5/5 |

- Invariante — sem visão independente nunca há PROVA: ok
- Invariante — tirar categoria ou data nunca cria PROVA: ok
- Dependência da visão (catálogo E casamento mentindo com confiança alta): 2 falsa(s) prova(s): nav-10, geo-03
- Só o casamento erra (catálogo correto): 0 falsa(s) prova(s): nenhuma

## Casos

| Caso | Tipo | Acontecimento | Imagem | Esperado | Obtido | Adversária | Legado | Sem categoria | Motivo |
|---|---|---|---|---|---|---|---|---|---|
| nav-01 | 1 | i6 | a6_commons | PROVA | **PROVA** | CONTEXTO | RELACIONADA | RELACIONADA | leitura visual cega confirma "estado_final"; categoria do acontecimento: "2021 Suez Canal obstruction" |
| nav-02 | 10 | i6 | a9_openverse | RELACIONADA | **RELACIONADA** | RELACIONADA | CONTEXTO | RELACIONADA | leitura visual cega confirma "acao"; vínculo do registro fraco: entidade citada na descrição/título: "Ever Given" |
| nav-03 | 1 | i0 | a8_iss | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria do acontecimento: "2021 Suez Canal obstruction" |
| nav-04 | 2 | i0 | a2_aster | CONTEXTO | **CONTEXTO** | CONTEXTO | RELACIONADA | CONTEXTO | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria da entidade: "Suez Canal" |
| nav-05 | 3 | i14 | a1_roterda | CONTEXTO | **CONTEXTO** | RELACIONADA | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria da entidade: "IMO 9811000" |
| nav-06 | 3 | i14 | a6_commons | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "estado_inicial" (exigido: acao ou estado_final); categoria do acontecimento: "2021 Suez Canal obstruction" |
| nav-07 | 9 | i2 | a10_outro_navio | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | imagem de fase "antes" (criacao_declarada: 2011) para fala que exige "acao"; leitura visual cega confirma "acao" |
| nav-08 | 2 | i2 | a12_2020 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria da entidade: "IMO 9811000" |
| nav-09 | 5 | i7 | a0_diagrama | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | catálogo diz "diagrama": casamento não confirmado; categoria da entidade: "Suez Canal" |
| nav-10 | 6 | i7 | a5_arabe | INCOMPATIVEL | **INCOMPATIVEL** | PROVA | INCOMPATIVEL | INCOMPATIVEL | texto em escrita arabe é o conteúdo da imagem: o público não lê |
| nav-11 | 4 | i0 | a11_igreja | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "nao_mostra" (exigido: acao ou estado_final); categoria da entidade: "Suez Canal" |
| nav-12 | 7 | i0 | a14_placa | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria do acontecimento: "2021 Suez Canal obstruction" |
| geo-01 | 1 | e7 | a25_rosenquist | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria do acontecimento: "1980 eruption of Mount St. Helens" |
| geo-02 | 1 | e6 | a25_rosenquist | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "estado_final"; categoria do acontecimento: "1980 eruption of Mount St. Helens" |
| geo-03 | 3 | e9 | a25_rosenquist | CONTEXTO | **CONTEXTO** | PROVA | RELACIONADA | CONTEXTO | leitura visual: "estado_inicial" (exigido: acao ou estado_final); categoria do acontecimento: "1980 eruption of Mount St. Helens" |
| geo-04 | 1 | e1 | a15_depois | RELACIONADA | **RELACIONADA** | RELACIONADA | CONTEXTO | RELACIONADA | leitura visual cega confirma "estado_final"; vínculo do registro fraco: categoria da entidade: "Mount St. Helens" |
| geo-05 | 2 | e7 | a13_antes | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "estado_inicial" (exigido: acao ou estado_final); categoria do acontecimento: "1980 eruption of Mount St. Helens" |
| geo-06 | 2 | e7 | a5_1982 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria da entidade: "Mount St. Helens" |
| geo-07 | 1 | e2 | a5_1982 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "entidade"; categoria da entidade: "Mount St. Helens" |
| geo-08 | 7 | e12 | a0_memorial | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | INCOMPATIVEL | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria do acontecimento: "Memorials of the 1980 eruption of Mount St. Helens" |
| geo-09 | 5 | e7 | a23_animacao | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | catálogo diz "reconstituicao_3d": casamento não confirmado; categoria do acontecimento: "1980 eruption of Mount St. Helens" |
| geo-10 | 4 | e9 | a16_nuvens | INCOMPATIVEL | **INCOMPATIVEL** | RELACIONADA | INCOMPATIVEL | INCOMPATIVEL | imagem genérica sem vínculo de registro |
| geo-11 | 1 | e5 | a12_johnston | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "entidade"; categoria da entidade: "David A. Johnston" |
| geo-12 | 1 | e1 | a18_post | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria do acontecimento: "1980 eruption of Mount St. Helens" |

## Decisão por acontecimento

| Domínio | Acontecimento | Esperado | Obtido | Imagem | Fundamento |
|---|---|---|---|---|---|
| naval | i14 | bloqueio | **bloqueio** | — | nenhuma imagem do navio liberado (bloqueio legítimo do piloto) |
| naval | i6 | foto_prova | **foto_prova** | a6_commons | prova real disponível |
| geologia | e7 | foto_prova | **foto_prova** | a25_rosenquist | era bloqueio falso no piloto |
| geologia | e9 | bloqueio | **bloqueio** | — | nenhuma imagem da explosão ultrapassando |
| geologia | e12 | bloqueio | **bloqueio** | — | memorial não prova destruição |

