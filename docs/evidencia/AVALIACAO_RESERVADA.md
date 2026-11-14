# Avaliação final — casos reservados (avaliados uma única vez)

Grupo: **reservado** · 53 casos · acerto 45/53 · falsa prova **0** · recall de prova 9/10 · eventos 10/12

| Domínio | Casos | Acerto | Falsa prova | Prova reconhecida |
|---|---|---|---|---|
| espaco_apollo11 | 9 | 9 | 0 | 2/2 |
| historia_muro_berlim | 8 | 8 | 0 | 2/2 |
| engenharia_tacoma | 8 | 6 | 0 | 2/2 |
| biologia_metamorfose | 8 | 6 | 0 | 0/1 |
| clima_katrina | 8 | 7 | 0 | 3/3 |
| negativo_penicilina | 4 | 3 | 0 | 0/0 |
| negativo_alexandria | 4 | 3 | 0 | 0/0 |
| negativo_esporte | 4 | 3 | 0 | 0/0 |

- Invariante — sem visão independente nunca há PROVA: ok
- Invariante — tirar categoria ou data nunca cria PROVA: ok
- Dependência da visão (IA mentindo com confiança alta): 3 falsa(s) prova(s): ap-08, bw-05, tn-04

## Casos

| Caso | Tipo | Acontecimento | Imagem | Esperado | Obtido | Adversária | Legado | Sem categoria | Motivo |
|---|---|---|---|---|---|---|---|---|---|
| ap-01 | 1 | ap_pouso | as11_40_5903 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria do acontecimento: "Apollo 11 Hasselblad film magazine 40" |
| ap-02 | 2 | ap_lancamento | as11_40_5903 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria do acontecimento: "Apollo 11 Hasselblad film magazine 40" |
| ap-03 | 9 | ap_pouso | dvids_5903 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | imagem de fase "depois" (criacao_declarada: 2009-12-11) para fala que exige "acao"; leitura visual cega confirma "acao" |
| ap-04 | 1 | ap_lancamento | s69_39525 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria do acontecimento: "Apollo 11" |
| ap-05 | 2 | ap_pouso | s69_39525 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria do acontecimento: "Apollo 11" |
| ap-06 | 7 | ap_pouso | nhq2019 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria do acontecimento: "Apollo 11" |
| ap-07 | 3 | ap_pouso | as11_36_5355 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "nao_mostra" (exigido: acao ou estado_final); categoria do acontecimento: "Apollo 11" |
| ap-08 | 5 | ap_pouso | insignia | CONTEXTO | **CONTEXTO** | PROVA | CONTEXTO | CONTEXTO | leitura visual: elemento de outra classe; categoria do acontecimento: "Apollo 11" |
| ap-09 | 4 | ap_pouso | lua_cheia | INCOMPATIVEL | **INCOMPATIVEL** | CONTEXTO | INCOMPATIVEL | INCOMPATIVEL | imagem genérica sem vínculo de registro |
| bw-01 | 1 | bw_abertura | b1110_018 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria do acontecimento: "Fall of the Berlin Wall" |
| bw-02 | 4 | bw_abertura | b1104_006 | INCOMPATIVEL | **INCOMPATIVEL** | CONTEXTO | INCOMPATIVEL | INCOMPATIVEL | leitura visual: "nao_mostra" (exigido: acao ou estado_final) |
| bw-03 | 9 | bw_abertura | b1222_034 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | imagem de fase "depois" (criacao_declarada: 1989-12-22) para fala que exige "acao"; leitura visual cega confirma "acao" |
| bw-04 | 1 | bw_abertura | b1118_018 | PROVA | **PROVA** | CONTEXTO | CONTEXTO | RELACIONADA | leitura visual cega confirma "estado_final"; categoria da entidade: "Berlin Wall" |
| bw-05 | 3 | bw_abertura | b1109_030 | CONTEXTO | **CONTEXTO** | PROVA | RELACIONADA | INCOMPATIVEL | leitura visual: "nao_mostra" (exigido: acao ou estado_final); categoria do acontecimento: "Fall of the Berlin Wall" |
| bw-06 | 7 | bw_abertura | memorial_bernauer | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria da entidade: "Berlin Wall Memorial" |
| bw-07 | 5 | bw_abertura | east_side | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria da entidade: "Berlin Wall" |
| bw-08 | 2 | bw_abertura | mauerbau | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "estado_inicial" (exigido: acao ou estado_final); categoria da entidade: "Construction of the Berlin Wall" |
| tn-01 | 1 | tn_queda | loc_46682 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; acontecimento citado na descrição/título: "Tacoma Narrows Bridge collapse" |
| tn-02 | 1 | tn_queda | uw_290_52 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "estado_final"; categoria da entidade: "Tacoma Narrows Bridge (Tacoma, Wash.)" |
| tn-03 | 10 | tn_queda | commons_upload | RELACIONADA | **CONTEXTO** ✘ | CONTEXTO | CONTEXTO | CONTEXTO | imagem de fase "depois" (criacao_declarada: Uploaddate 2010-01-17) para fala que exige "acao"; leitura visual cega confirma "acao" |
| tn-04 | 3 | tn_queda | uw_290_33 | CONTEXTO | **CONTEXTO** | PROVA | RELACIONADA | CONTEXTO | leitura visual: "estado_inicial" (exigido: acao ou estado_final); acontecimento citado na descrição/título: "Tacoma Narrows Bridge collapse" |
| tn-05 | 2 | tn_queda | abertura_1940 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "estado_inicial" (exigido: acao ou estado_final); categoria da entidade: "Tacoma Narrows Bridge (1940)" |
| tn-06 | 7 | tn_queda | fragmento | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria da entidade: "Tacoma Narrows Bridge (1940)" |
| tn-07 | 2 | tn_queda | pontes_atuais | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria da entidade: "Tacoma Narrows Bridge (1950)" |
| tn-08 | 4 | tn_queda | golden_gate | INCOMPATIVEL | **CONTEXTO** ✘ | CONTEXTO | INCOMPATIVEL | CONTEXTO | leitura visual: "estado_inicial" (exigido: acao ou estado_final) |
| mt-01 | 10 | mt_crisalida | jd_92417 | RELACIONADA | **RELACIONADA** | RELACIONADA | CONTEXTO | RELACIONADA | leitura visual cega confirma "estado_final"; vínculo do registro fraco: entidade citada na descrição/título: "Danaus plexippus" |
| mt-02 | 1 | mt_crisalida | commons_pupa | PROVA | **RELACIONADA** ✘ | RELACIONADA | CONTEXTO | RELACIONADA | leitura visual cega confirma "estado_final"; vínculo do registro fraco: categoria da entidade: "Danaus plexippus (pupae)" |
| mt-03 | 1 | mt_crisalida | jd_63251 | RELACIONADA | **RELACIONADA** | RELACIONADA | CONTEXTO | RELACIONADA | leitura visual cega confirma "acao"; vínculo do registro fraco: entidade citada na descrição/título: "Danaus plexippus" |
| mt-04 | 3 | mt_crisalida | jd_92418 | CONTEXTO | **CONTEXTO** | RELACIONADA | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); entidade citada na descrição/título: "Danaus plexippus" |
| mt-05 | 3 | mt_crisalida | adulto | CONTEXTO | **CONTEXTO** | RELACIONADA | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria da entidade: "Danaus plexippus (adults)" |
| mt-06 | 5 | mt_crisalida | merian | CONTEXTO | **CONTEXTO** | CONTEXTO | INCOMPATIVEL | CONTEXTO | ilustracao: arte/IA/reconstituição nunca prova; leitura visual cega confirma "acao" |
| mt-07 | 9 | mt_crisalida | machaon | INCOMPATIVEL | **RELACIONADA** ✘ | RELACIONADA | INCOMPATIVEL | RELACIONADA | leitura visual cega confirma "estado_final"; nenhum registro liga a imagem a ESTE acontecimento (pode ser outro caso parecido) |
| mt-08 | 5 | mt_crisalida | ciclo | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | diagrama: explica, não registra o acontecimento; leitura visual cega confirma "acao" |
| kt-01 | 1 | kt_inundacao | fema_15008 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "estado_final"; categoria do acontecimento: "Effects of Hurricane Katrina in New Orleans" |
| kt-02 | 1 | kt_inundacao | fema_14891 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "acao"; categoria do acontecimento: "Effects of Hurricane Katrina in New Orleans" |
| kt-03 | 1 | kt_inundacao | fema_17284 | PROVA | **PROVA** | PROVA | RELACIONADA | RELACIONADA | leitura visual cega confirma "estado_final"; categoria do acontecimento: "Effects of Hurricane Katrina in New Orleans" |
| kt-04 | 2 | kt_inundacao | goes_28ago | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria do acontecimento: "Hurricane Katrina" |
| kt-05 | 2 | kt_inundacao | skyline | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final); categoria da entidade: "Skylines of New Orleans" |
| kt-06 | 7 | kt_inundacao | memorial | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria do acontecimento: "Hurricane Katrina" |
| kt-07 | 5 | kt_inundacao | trajetoria | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | mapa: explica, não registra o acontecimento; leitura visual cega confirma "acao" |
| kt-08 | 9 | kt_inundacao | harvey | INCOMPATIVEL | **CONTEXTO** ✘ | CONTEXTO | INCOMPATIVEL | CONTEXTO | imagem de fase "depois" (criacao_declarada: 2017-08-29) para fala que exige "estado_final"; leitura visual cega confirma "estado_final" |
| pn-01 | 3 | pn_mofo | fleming_1945 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "nao_mostra" (exigido: acao ou estado_final); categoria da entidade: "Alexander Fleming" |
| pn-02 | 10 | pn_mofo | placa_moderna | RELACIONADA | **CONTEXTO** ✘ | CONTEXTO | INCOMPATIVEL | CONTEXTO | imagem de fase "depois" (criacao_declarada: 2016) para fala que exige "acao"; leitura visual cega confirma "acao" |
| pn-03 | 2 | pn_mofo | producao_1943 | CONTEXTO | **CONTEXTO** | CONTEXTO | INCOMPATIVEL | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final) |
| pn-04 | 7 | pn_mofo | placa_azul | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | INCOMPATIVEL | leitura visual: "consequencia" (exigido: acao ou estado_final); categoria da entidade: "Alexander Fleming" |
| al-01 | 5 | al_destruicao | goll_1876 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | ilustracao: arte/IA/reconstituição nunca prova; leitura visual cega confirma "acao" |
| al-02 | 5 | al_destruicao | von_corven | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "estado_inicial" (exigido: acao ou estado_final); categoria da entidade: "Library of Alexandria" |
| al-03 | 9 | al_destruicao | bibliotheca | INCOMPATIVEL | **CONTEXTO** ✘ | RELACIONADA | INCOMPATIVEL | CONTEXTO | leitura visual: "outro_estado" (exigido: acao ou estado_final) |
| al-04 | 7 | al_destruicao | serapeum | CONTEXTO | **CONTEXTO** | RELACIONADA | INCOMPATIVEL | CONTEXTO | leitura visual: "consequencia" (exigido: acao ou estado_final); mostra consequência, não o acontecimento |
| es-01 | 3 | es_salto | beamon_2014 | CONTEXTO | **CONTEXTO** | CONTEXTO | CONTEXTO | CONTEXTO | leitura visual: "entidade" (exigido: acao); categoria da entidade: "Bob Beamon" |
| es-02 | 9 | es_salto | salto_2012 | INCOMPATIVEL | **CONTEXTO** ✘ | CONTEXTO | INCOMPATIVEL | CONTEXTO | imagem de fase "depois" (criacao_declarada: 2012-08-04) para fala que exige "acao"; leitura visual cega confirma "acao" |
| es-03 | 4 | es_salto | estadio | INCOMPATIVEL | **INCOMPATIVEL** | CONTEXTO | INCOMPATIVEL | INCOMPATIVEL | leitura visual: "nao_mostra" (exigido: acao) |
| es-04 | 5 | es_salto | selo | CONTEXTO | **CONTEXTO** | RELACIONADA | INCOMPATIVEL | CONTEXTO | ilustracao: arte/IA/reconstituição nunca prova; leitura visual cega confirma "acao" |

## Decisão por acontecimento

| Domínio | Acontecimento | Esperado | Obtido | Imagem | Fundamento |
|---|---|---|---|---|---|
| espaco_apollo11 | ap_pouso#com_prova | foto_prova | **foto_prova** | as11_40_5903 | há prova real |
| espaco_apollo11 | ap_pouso#sem_prova | bloqueio | **bloqueio** | — | a única cópia da foto certa tem registro contraditório; o resto é contexto |
| espaco_apollo11 | ap_pouso#vazio | bloqueio | **bloqueio** | — | sem nenhuma evidência (caso 8) |
| historia_muro_berlim | bw_abertura#sem_prova | bloqueio | **bloqueio** | — | nenhuma imagem da abertura de 9–10/11 |
| engenharia_tacoma | tn_queda#fraco | revisao | **bloqueio** ✘ | — | a única foto do colapso tem vínculo fraco: revisão humana, não bloqueio |
| biologia_metamorfose | mt_crisalida#fraco | revisao | **revisao** | jd_92417 | foto certa com vínculo fraco: revisão |
| clima_katrina | kt_inundacao#sem_prova | bloqueio | **bloqueio** | — | nenhuma imagem da inundação de Nova Orleans (a do Harvey é outro acontecimento) |
| negativo_penicilina | pn_mofo#sem_foto | bloqueio | **bloqueio** | — | só retrato e imagens posteriores |
| negativo_penicilina | pn_mofo#demo | revisao | **bloqueio** ✘ | — | demonstração moderna: humano decide (nunca prova) |
| negativo_alexandria | al_destruicao#arte | bloqueio | **bloqueio** | — | só arte e imagens posteriores |
| negativo_esporte | es_salto#sem_foto | bloqueio | **bloqueio** | — | nenhuma foto livre do salto |
| negativo_esporte | es_salto#parecida | bloqueio | **bloqueio** | — | salto parecido de outro atleta não serve |

