# Relatório geométrico — Ninguém Te Contou (depois da Fase 2, 12/11/2026)

Gerado por `python -m tests.ntc_geometria`. Medido no Chrome do Playwright sobre o motor real (`canais/ntc/vetor/fabula.html`), grade de 18 px com `elementsFromPoint` (forma pintada), amostras a cada 0.067 s em cena com movimento e a cada 0.5 s nas paradas, mais início/desenvolvimento/ação/final e cada corte de câmera. Tempo de cada cena estimado pela narração (3 palavras/s).

**comprovado** = a medida mostra o erro sem depender de gosto. **possível** = a medida acusa, mas pode ser intencional (profundidade, encostar de leve) — precisa de olho.

## Antes × depois da Fase 2 (mesmos 4 casos, mesmas regras do medidor)

| caso | comprovados antes | comprovados depois | possíveis antes | possíveis depois |
|---|---|---|---|---|
| baratas | 11 | 0 | 27 | 19 |
| ceu_e_voadores | 30 | 0 | 40 | 25 |
| fogo_e_destruicao | 4 | 0 | 15 | 9 |
| espaco_e_movimento | 11 | 0 | 21 | 13 |
| **total** | **56** | **0** | **103** | **66** |

Comprovados antes, por tipo: fora_da_tela 23, ceu_sobre_estrutura 10, astro_duplicado 9, ceu_abaixo_horizonte 9, texto_cobre_rosto 3, cai_e_para_no_ar 2.

O que sobra são só **possíveis** (precisam de olho; não são erro certo): objetos amontoados (monte de folhas, ratos juntos), bicho voando na frente de figurante, gota/nota parada no ar (o motor permite), pássaro/fogo cortado na borda, lua/sol no espaço perto do planeta do fundo.

**Total: 0 comprovados, 66 possíveis.**

## Caso `baratas` — 15 cenas, 950 instantes medidos, 0 comprovados, 19 possíveis

| nível | cena | cenário | quando (s na cena) | plano | elemento | problema | região invadida | medida |
|---|---|---|---|---|---|---|---|---|
| possível | 4 | rua | 1.27–1.4 (3 amostras) | geral | barata (obj3, some) | fora_da_tela | borda do quadro | caixa na tela [825, 1689, 1106, 1842] |
| possível | 5 | rua | 2.7 | geral | Val | fora_da_tela | borda do quadro | caixa na tela [-75, 853, 745, 1764] |
| possível | 6 | floresta | 0.87–2.47 (26 amostras) | geral | folhas (obj5, cresce) × folhas (obj4, aparece) | objetos_amontoados | folhas (obj4, aparece) | 100% do menor coberto |
| possível | 6 | floresta | 0.93–2.46 (25 amostras) | geral | folhas (obj5, cresce) × folhas (obj3, aparece) | objetos_amontoados | folhas (obj3, aparece) | 100% do menor coberto |
| possível | 6 | floresta | 2.2–2.46 (5 amostras) | geral | folhas (obj5, cresce) | fora_da_tela | borda do quadro | caixa na tela [-12, 1680, 304, 1845] |
| possível | 7 | floresta | 0.86–4.61 (62 amostras) | geral | folhas (obj9, cresce) × folhas (obj5, aparece) | objetos_amontoados | folhas (obj5, aparece) | 100% do menor coberto |
| possível | 7 | floresta | 1.67–2.27 (11 amostras) | geral | folhas (obj9, cresce) | fora_da_tela | borda de baixo | caixa na tela [602, 1798, 861, 1939] |
| possível | 7 | floresta | 1.81–2.27 (9 amostras) | geral | folhas (obj8, cresce) | fora_da_tela | borda do quadro | caixa na tela [-26, 1776, 269, 1918] |
| possível | 9 | rua | 1.13–2.33 (20 amostras) | geral | rato (obj3, foge) × rato (obj0, foge) | objetos_amontoados | rato (obj0, foge) | 81% do menor coberto |
| possível | 9 | rua | 1.13–1.27 (4 amostras) | geral | rato (obj3, foge) × lixo (obj2, cai) | objetos_amontoados | lixo (obj2, cai) | 83% do menor coberto |
| possível | 9 | rua | 1.73–2.47 (11 amostras) | geral | lixo (obj1, cai) × rato (obj0, foge) | objetos_amontoados | rato (obj0, foge) | 60% do menor coberto |
| possível | 9 | rua | 1.8–3.28 (24 amostras) | geral | lixo (obj1, cai) | fora_da_tela | borda de baixo | caixa na tela [39, 1718, 325, 1936] |
| possível | 9 | rua | 1.8–2.53 (11 amostras) | geral | rato (obj3, foge) × lixo (obj1, cai) | objetos_amontoados | lixo (obj1, cai) | 79% do menor coberto |
| possível | 10 | cozinha | 0.4–1.14 (11 amostras) | geral | rato (obj0, pula) | fora_da_tela | borda do quadro | caixa na tela [-32, 869, 371, 1045] |
| possível | 12 | horta | 2 | geral | passaro (obj1, aparece) | fora_da_tela | borda do quadro | caixa na tela [-8, 613, 262, 759] |
| possível | 13 | cozinha | 0.53–2.53 (18 amostras) | geral | rato (obj1, corre) × rato (obj0, corre) | objetos_amontoados | rato (obj0, corre) | 71% do menor coberto |
| possível | 13 | cozinha | 1.13–1.53 (7 amostras) | geral | rato (obj0, corre) | cobre_val | corpo da Val | 9% do corpo (pode ser profundidade) |
| possível | 13 | cozinha | 1.4–1.53 (3 amostras) | geral | rato (obj1, corre) | cobre_val | corpo da Val | 8% do corpo (pode ser profundidade) |
| possível | 13 | cozinha | 1.6–2.03 (3 amostras) | geral | balao | texto_cobre_rosto | cabeça da Val | 13% da cabeça coberta |

## Caso `ceu_e_voadores` — 10 cenas, 764 instantes medidos, 0 comprovados, 25 possíveis

| nível | cena | cenário | quando (s na cena) | plano | elemento | problema | região invadida | medida |
|---|---|---|---|---|---|---|---|---|
| possível | 0 | rua | 0.6–0.67 (2 amostras) | geral | nuvem (obj2, aparece) × sol (obj0, aparece) | objetos_amontoados | sol (obj0, aparece) | 37% do menor coberto |
| possível | 0 | rua | 2.53–2.8 (5 amostras) | geral | nuvem (obj2, aparece) | fora_da_tela | borda do quadro | caixa na tela [356, -7, 795, 229] |
| possível | 0 | rua | 2.86–5.62 (44 amostras) | objeto | nuvem (obj2, aparece) × nuvem (obj1, aparece) | objetos_amontoados | nuvem (obj1, aparece) | 91% do menor coberto |
| possível | 1 | rua | 0.61–0.74 (3 amostras) | geral | dinheiro (obj2, cai) | cobre_rosto | cabeça da Val | 18% da cabeça atrás do objeto |
| possível | 1 | rua | 2.13–2.14 (2 amostras) | geral | Val | fora_da_tela | borda do quadro | caixa na tela [-68, 840, 752, 1764] |
| possível | 2 | rua | 2.13–2.47 (6 amostras) | geral | passaro (obj1, aparece) × passaro (obj0, aparece) | objetos_amontoados | passaro (obj0, aparece) | 58% do menor coberto |
| possível | 3 | sitio | 0.8–1.0 (4 amostras) | geral | passaro (obj3, aparece) × passaro (obj1, aparece) | objetos_amontoados | passaro (obj1, aparece) | 66% do menor coberto |
| possível | 3 | sitio | 0.87–1.53 (12 amostras) | geral | passaro (obj3, aparece) × nuvem (obj2, aparece) | objetos_amontoados | nuvem (obj2, aparece) | 62% do menor coberto |
| possível | 3 | sitio | 2.07–2.33 (5 amostras) | geral | passaro (obj0, aparece) | fora_da_tela | borda do quadro | caixa na tela [591, -43, 864, 105] |
| possível | 4 | fazenda | 2.2–2.21 (2 amostras) | rosto | balao | texto_cobre_rosto | cabeça da Val | 6% da cabeça coberta |
| possível | 5 | praia | 0.4–5.28 (77 amostras) | geral | passaro (obj2, aparece) | voador_na_frente_de_pessoa | povo1 | 100% do bicho voando sobre o figurante |
| possível | 5 | praia | 0.53–1.07 (9 amostras) | geral | passaro (obj3, aparece) | voador_na_frente_de_pessoa | povo3 | 100% do bicho voando sobre o figurante |
| possível | 5 | praia | 0.93–1.67 (10 amostras) | geral | passaro (obj2, aparece) | fora_da_tela | borda do quadro | caixa na tela [-16, 1191, 170, 1291] |
| possível | 5 | praia | 1.27–5.28 (36 amostras) | geral | passaro (obj3, aparece) | voador_na_frente_de_pessoa | povo0 | 28% do bicho voando sobre o figurante |
| possível | 5 | praia | 2.4–5.28 (11 amostras) | meio | passaro (obj2, aparece) | voador_na_frente_de_pessoa | povo2 | 25% do bicho voando sobre o figurante |
| possível | 6 | horta | 0.5–5.29 (17 amostras) | geral | gota (obj0, aparece) | parado_no_ar | chão começa em y=1340 | gota parado no ar em y=1180 (o motor permite; ver se faz sentido) |
| possível | 6 | horta | 1.0–5.29 (16 amostras) | geral | gota (obj1, aparece) | parado_no_ar | chão começa em y=1340 | gota parado no ar em y=1217 (o motor permite; ver se faz sentido) |
| possível | 6 | horta | 1.0–5.29 (16 amostras) | geral | gota (obj2, aparece) | parado_no_ar | chão começa em y=1340 | gota parado no ar em y=1254 (o motor permite; ver se faz sentido) |
| possível | 7 | cozinha | 1.93–2.53 (11 amostras) | geral | mosca (obj1, aparece) | fora_da_tela | borda do quadro | caixa na tela [1030, 1179, 1098, 1248] |
| possível | 7 | cozinha | 2.66–2.8 (3 amostras) | geral | mosca (obj0, aparece) | fora_da_tela | borda do quadro | caixa na tela [-11, 1072, 43, 1132] |
| possível | 8 | sala | 0.5–5.29 (17 amostras) | geral | dinheiro (obj0, aparece) | parado_no_ar | chão começa em y=1340 | dinheiro parado no ar em y=1180 (o motor permite; ver se faz sentido) |
| possível | 8 | sala | 1.0–5.29 (16 amostras) | geral | dinheiro (obj1, aparece) | parado_no_ar | chão começa em y=1340 | dinheiro parado no ar em y=1215 (o motor permite; ver se faz sentido) |
| possível | 8 | sala | 1.0–5.29 (16 amostras) | geral | dinheiro (obj3, aparece) | parado_no_ar | chão começa em y=1340 | dinheiro parado no ar em y=1294 (o motor permite; ver se faz sentido) |
| possível | 8 | sala | 1.0–5.29 (16 amostras) | geral | dinheiro (obj2, aparece) | parado_no_ar | chão começa em y=1340 | dinheiro parado no ar em y=1260 (o motor permite; ver se faz sentido) |
| possível | 8 | sala | 1.63–5.29 (13 amostras) | rosto | dinheiro (obj1, aparece) | cobre_val | corpo da Val | 6% do corpo (pode ser profundidade) |

## Caso `fogo_e_destruicao` — 9 cenas, 609 instantes medidos, 0 comprovados, 9 possíveis

| nível | cena | cenário | quando (s na cena) | plano | elemento | problema | região invadida | medida |
|---|---|---|---|---|---|---|---|---|
| possível | 2 | rua | 0.87–4.62 (61 amostras) | geral | lixo (obj1, cai) × fogo (obj0, aparece) | objetos_amontoados | fogo (obj0, aparece) | 100% do menor coberto |
| possível | 2 | rua | 1.79–2.33 (9 amostras) | geral | lixo (obj1, cai) | fora_da_tela | borda de baixo | caixa na tela [42, 1717, 327, 1935] |
| possível | 3 | lab | 0.47–4.95 (71 amostras) | geral | vela (obj1, aparece) × fogo (obj0, aparece) | objetos_amontoados | fogo (obj0, aparece) | 100% do menor coberto |
| possível | 3 | lab | 2.53–2.53 (2 amostras) | geral | Val | fora_da_tela | borda do quadro | caixa na tela [-73, 839, 753, 1764] |
| possível | 6 | rua_destruida | 0.2–1.6 (24 amostras) | geral | fogo (obj4, aparece) | fora_da_tela | borda do quadro | caixa na tela [-154, 1553, 123, 1955] |
| possível | 6 | rua_destruida | 0.26–1.6 (23 amostras) | geral | fogo (obj5, aparece) | fora_da_tela | borda do quadro | caixa na tela [1007, 1620, 1242, 1978] |
| possível | 6 | rua_destruida | 0.33 | geral | fogo (obj1, aparece) | fora_da_tela | borda do quadro | caixa na tela [854, 883, 1129, 1322] |
| possível | 6 | rua_destruida | 0.33–4.28 (15 amostras) | rosto | fogo (obj2, aparece) × fogo (obj0, aparece) | objetos_amontoados | fogo (obj0, aparece) | 38% do menor coberto |
| possível | 8 | rua_destruida | 4.8–6.93 (13 amostras) | geral | Val | fora_da_tela | borda do quadro | caixa na tela [469, 884, 1160, 1783] |

## Caso `espaco_e_movimento` — 9 cenas, 610 instantes medidos, 0 comprovados, 13 possíveis

| nível | cena | cenário | quando (s na cena) | plano | elemento | problema | região invadida | medida |
|---|---|---|---|---|---|---|---|---|
| possível | 0 | espaco | 0.5–4.95 (13 amostras) | geral | lua (obj0, cresce) | astro_duplicado | cen91 (terra do cenário) [310, 700, 770, 1160] | o cenário já desenha terra; objeto lua em [200, 154, 320, 275] |
| possível | 0 | espaco | 0.5–4.95 (13 amostras) | geral | sol (obj1, aparece) | astro_duplicado | cen91 (terra do cenário) [310, 700, 770, 1160] | o cenário já desenha terra; objeto sol em [797, 698, 983, 883] |
| possível | 1 | espaco | 0.5–4.95 (13 amostras) | geral | lua (obj0, cresce) | astro_duplicado | cen91 (terra do cenário) [310, 700, 770, 1160] | o cenário já desenha terra; objeto lua em [200, 199, 320, 320] |
| possível | 3 | cozinha | 0.53–2.33 (18 amostras) | geral | rato (obj2, foge) × rato (obj1, foge) | objetos_amontoados | rato (obj1, foge) | 71% do menor coberto |
| possível | 3 | cozinha | 0.93–1.2 (6 amostras) | geral | rato (obj1, foge) | cobre_val | corpo da Val | 9% do corpo (pode ser profundidade) |
| possível | 3 | cozinha | 1.07–1.33 (5 amostras) | geral | rato (obj2, foge) | cobre_val | corpo da Val | 8% do corpo (pode ser profundidade) |
| possível | 4 | rua | 0.47–4.96 (71 amostras) | geral | lua (obj0, cresce) | astro_duplicado | cen1 (sol do cenário) [660, 60, 1040, 440] | o cenário já desenha sol; objeto lua em [238, 280, 282, 323] |
| possível | 4 | rua | 0.47–4.96 (71 amostras) | geral | lua (obj0, cresce) | astro_duplicado | cen2 (sol do cenário) [780, 180, 920, 320] | o cenário já desenha sol; objeto lua em [238, 280, 282, 323] |
| possível | 5 | praia | 0.47–4.29 (63 amostras) | geral | lua (obj0, aparece) | astro_duplicado | cen1 (sol do cenário) [660, 60, 1040, 440] | o cenário já desenha sol; objeto lua em [206, 212, 314, 320] |
| possível | 5 | praia | 0.47–4.29 (63 amostras) | geral | lua (obj0, aparece) | astro_duplicado | cen2 (sol do cenário) [780, 180, 920, 320] | o cenário já desenha sol; objeto lua em [206, 212, 314, 320] |
| possível | 5 | praia | 0.53–0.6 (2 amostras) | geral | dinheiro (obj1, cai) | cobre_rosto | cabeça da Val | 6% da cabeça atrás do objeto |
| possível | 7 | horta | 0.54–4.62 (49 amostras) | meio | folhas (obj8, aparece) × folhas (obj6, cresce) | objetos_amontoados | folhas (obj6, cresce) | 100% do menor coberto |
| possível | 7 | horta | 1.54–2.34 (13 amostras) | geral | folhas (obj9, cresce) | fora_da_tela | borda de baixo | caixa na tela [738, 1792, 1015, 1946] |
