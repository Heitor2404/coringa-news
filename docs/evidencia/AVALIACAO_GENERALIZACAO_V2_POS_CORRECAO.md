# Avaliação generalizacao_v2 — após as correções da etapa 3

Grupo: **generalizacao_v2** · 17 casos · acerto 17/17 · falsa prova **0** · recall de prova 3/3 · eventos 3/3

| Domínio | Casos | Acerto | Falsa prova | Prova reconhecida |
|---|---|---|---|---|
| dirigivel_hindenburg | 6 | 6 | 0 | 1/1 |
| nuclear_chernobyl | 6 | 6 | 0 | 1/1 |
| botanica_germinacao | 5 | 5 | 0 | 1/1 |

- Invariante — sem visão independente nunca há PROVA: ok
- Invariante — tirar categoria ou data nunca cria PROVA: ok
- Dependência da visão (catálogo E casamento mentindo com confiança alta): 1 falsa(s) prova(s): g-gm-03
- Só o casamento erra (catálogo correto): 0 falsa(s) prova(s): nenhuma

## Casos

| Caso | Tipo | Acontecimento | Imagem | Esperado | Obtido | Adversária | Legado | Sem categoria | Motivo |
|---|---|---|---|---|---|---|---|---|---|
| g-hb-01 | 1 | hb_fogo | fogo | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria do acontecimento: "Hindenburg disaster" |
| g-hb-02 | 10 | hb_fogo | upload_txt | RELACIONADA | **RELACIONADA** | RELACIONADA | CONTEXTO | RELACIONADA | leitura visual cega confirma "acao"; vínculo do registro fraco: acontecimento citado na descrição/título: "Hindenburg disaster"; categoria da entidade: "LZ 129  |
| g-hb-03 | 2 | hb_fogo | voo_1936 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | INCOMPATIVEL | leitura visual: "estado_inicial" (exigido: acao ou estado_final); categoria da entidade: "LZ 129 Hindenburg" |
| g-hb-04 | 9 | hb_fogo | r101 | INCOMPATIVEL | **INCOMPATIVEL** | INCOMPATIVEL | INCOMPATIVEL | CONTEXTO | parece o acontecimento, mas o registro curado classifica a imagem em outro assunto: R101, Airship accidents in France |
| g-hb-05 | 4 | hb_fogo | zeppelin_nt | INCOMPATIVEL | **INCOMPATIVEL** | RELACIONADA | INCOMPATIVEL | INCOMPATIVEL | sem vínculo de registro: semelhança não basta para contexto; leitura visual: "outro_estado" (exigido: acao ou estado_final) |
| g-hb-06 | 7 | hb_fogo | memorial | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | INCOMPATIVEL | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria do acontecimento: "Hindenburg disaster" |
| g-ch-01 | 1 | ch_explosao | aerea_1986 | PROVA | **PROVA** | CONTEXTO | RELACIONADA | RELACIONADA | leitura visual cega confirma "estado_final"; categoria do acontecimento: "Chernobyl disaster" |
| g-ch-02 | 7 | ch_explosao | nsc_2017 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | INCOMPATIVEL | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria da entidade: "Chernobyl Nuclear Power Plant" |
| g-ch-03 | 7 | ch_explosao | pripyat_2010 | INCOMPATIVEL | **INCOMPATIVEL** | INCOMPATIVEL | INCOMPATIVEL | INCOMPATIVEL | leitura visual: "consequencia" (exigido: acao ou estado_final) |
| g-ch-04 | 2 | ch_explosao | usina_1985 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | INCOMPATIVEL | leitura visual: "estado_inicial" (exigido: acao ou estado_final); categoria da entidade: "Chernobyl Nuclear Power Plant" |
| g-ch-05 | 9 | ch_explosao | fukushima | INCOMPATIVEL | **INCOMPATIVEL** | INCOMPATIVEL | INCOMPATIVEL | CONTEXTO | parece o acontecimento, mas o registro curado classifica a imagem em outro assunto: Fukushima Daiichi nuclear disaster |
| g-ch-06 | 6 | ch_explosao | jornal_ru | INCOMPATIVEL | **INCOMPATIVEL** | CONTEXTO | INCOMPATIVEL | INCOMPATIVEL | texto em escrita cirilica é o conteúdo da imagem: o público não lê |
| g-gm-01 | 1 | gm_broto | broto_cat | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria da entidade: "Phaseolus vulgaris (seedlings)" |
| g-gm-02 | 10 | gm_broto | broto_livre | RELACIONADA | **RELACIONADA** | RELACIONADA | INCOMPATIVEL | RELACIONADA | leitura visual cega confirma "acao"; nenhum registro liga a imagem a ESTE acontecimento (pode ser outro caso parecido) |
| g-gm-03 | 3 | gm_broto | vagem | CONTEXTO | **CONTEXTO** | PROVA | RELACIONADA | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria da entidade: "Phaseolus vulgaris (fruits)" |
| g-gm-04 | 9 | gm_broto | milho | INCOMPATIVEL | **INCOMPATIVEL** | INCOMPATIVEL | INCOMPATIVEL | RELACIONADA | parece o acontecimento, mas o registro curado classifica a imagem em outro assunto: Zea mays (seedlings) |
| g-gm-05 | 5 | gm_broto | desenho | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | INCOMPATIVEL | catálogo diz "diagrama": casamento não confirmado; categoria da entidade: "Phaseolus vulgaris" |

## Decisão por acontecimento

| Domínio | Acontecimento | Esperado | Obtido | Imagem | Fundamento |
|---|---|---|---|---|---|
| dirigivel_hindenburg | hb#fraco | revisao | **revisao** | upload_txt | só a foto com data de envio: revisão |
| nuclear_chernobyl | ch#outro | bloqueio | **bloqueio** | — | só contexto e outro acidente |
| botanica_germinacao | gm#prova | foto_prova | **foto_prova** | broto_cat | atemporal com espécie curada |

