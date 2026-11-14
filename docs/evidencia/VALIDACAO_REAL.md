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
| desenvolvimento | nav-11 | a11_igreja | CONTEXTO | CONTEXTO | sem registro | — | — |
| desenvolvimento | nav-12 | a14_placa | CONTEXTO | CONTEXTO | sem registro | — | — |
| desenvolvimento | geo-01 | a25_rosenquist | PROVA | PROVA | sem registro | — | — |
| desenvolvimento | geo-02 | a25_rosenquist | PROVA | PROVA | sem registro | — | — |
| desenvolvimento | geo-03 | a25_rosenquist | CONTEXTO | CONTEXTO | sem registro | — | — |
| desenvolvimento | geo-08 | a0_memorial | CONTEXTO | CONTEXTO | sem registro | — | — |
| desenvolvimento | geo-09 | a23_animacao | CONTEXTO | CONTEXTO | sem registro | — | — |
| desenvolvimento | geo-12 | a18_post | PROVA | PROVA | sem registro | — | — |
| reservado | ap-01 | as11_40_5903 | PROVA | PROVA | sem registro | — | — |
| reservado | ap-02 | as11_40_5903 | CONTEXTO | CONTEXTO | sem registro | — | — |
| reservado | ap-03 | dvids_5903 | CONTEXTO | CONTEXTO | sem registro | — | — |
| reservado | ap-04 | s69_39525 | PROVA | PROVA | RELACIONADA | CONTEXTO | foto / incerto / baixa |
| reservado | ap-05 | s69_39525 | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| reservado | ap-06 | nhq2019 | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| reservado | ap-07 | as11_36_5355 | CONTEXTO | CONTEXTO | CONTEXTO | CONTEXTO | foto / incerto / baixa |
| reservado | ap-08 | insignia | CONTEXTO | CONTEXTO | sem registro | — | — |
| reservado | ap-09 | lua_cheia | INCOMPATIVEL | INCOMPATIVEL | sem registro | — | — |
| reservado | bw-01 | b1110_018 | PROVA | PROVA | sem registro | — | — |
| reservado | bw-02 | b1104_006 | INCOMPATIVEL | INCOMPATIVEL | sem registro | — | — |
| reservado | bw-03 | b1222_034 | CONTEXTO | CONTEXTO | sem registro | — | — |
| reservado | bw-04 | b1118_018 | PROVA | PROVA | sem registro | — | — |
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
| reservado | kt-02 | fema_14891 | PROVA | PROVA | sem registro | — | — |
| reservado | kt-03 | fema_17284 | PROVA | PROVA | sem registro | — | — |
| reservado | al-01 | goll_1876 | CONTEXTO | CONTEXTO | sem registro | — | — |
| reservado | al-02 | von_corven | CONTEXTO | CONTEXTO | sem registro | — | — |

- Falsas provas com dados reais: 0 []
- Provas esperadas não alcançadas com o registro real: 11 ['geo-01', 'geo-02', 'geo-12', 'ap-01', 'ap-04', 'bw-01', 'bw-04', 'tn-01', 'tn-02', 'kt-02', 'kt-03']
