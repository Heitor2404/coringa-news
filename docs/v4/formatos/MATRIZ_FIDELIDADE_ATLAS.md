# ATLAS — matriz de fidelidade à referência A (17/11, noite)

Os testes verdes NÃO aprovam nada. A entrega fica bloqueada até a avaliação do Heitor.
Evidências: trechos de 7 s lado a lado (referência | Coringa) e o trio de quadros (referência | Panamá aprovado | motor
corrigido). Ficam só na conversa privada; a referência nunca entra no repositório.
Medidas: SIFT na zona de conteúdo (`src/v4/formatos/movimento.py`) e ebur128 + janelas de 400 ms (`som_medir.py`).
Os vídeos estão comprimidos, então as medidas comparam ordem de grandeza, não easing exato.

Situação: **C** = conforme · **P** = parcialmente conforme · **N** = não conforme.

## Mapas e cor

| Item | Referência (medida/observação) | Coringa (medida/observação) | Situação |
|---|---|---|---|
| Base regional | Imagem de satélite (Esri; proibida para nós) | Satélite EOxCloudless 2016 (CC BY 4.0), definição até zoom 11–14 | C |
| Base continental | Imagem de satélite verde-escura | Relevo NE2 (domínio público), ne2_mundo, ne2_pacifico e ne2_asia_leste, até ±85° | P: mais claro e pastel que satélite; nenhuma base continental de satélite licenciada está disponível sem serviço pago |
| Base obrigatória | Sempre há imagem | F-MAPA-SEM-BASE e F-MAPA-BORDA-DA-BASE (antes a checagem era pulada sem rasters) | C (regra no motor) |
| Mapa-múndi em 9:16 | Nunca vai além do continente | No zoom mínimo aparecem a Antártida e o Ártico | P: recomendo limitar a escala mínima ao continente (pendente) |
| Mapa técnico | Azul-marinho (#0F2338), grade fina, contorno do território | Fundo #070B14/#0E1828, grade de 170 px, território real | C |
| Destaque de país | Preenchimento vermelho opaco | Preenchimento amarelo translúcido + contorno com brilho (identidade Coringa) | P: decisão de identidade, a confirmar |
| Tratamento de cor | Satélite saturado, contraste médio | Satélite com contraste +0,12 e saturação +0,1 (agora no manifesto do raster, não no episódio) | P |

## Traços e marcadores

| Item | Referência | Coringa | Situação |
|---|---|---|---|
| Traços e rotas | Sem rota no trecho A; províncias contornadas | Rota medida de 9 px e conexões de 7 px (token), desenho progressivo | P: sem equivalente direto na A |
| Marcadores e retratos | Retrato circular com etiqueta abaixo, sobre o lugar | Foto circular protagonista/secundária ancorada, etiqueta abaixo, desvio ≤ 3 px do mapa | C |

## Câmera e transições

| Item | Referência | Coringa | Situação |
|---|---|---|---|
| Aproximação | +2 a +4 %/s contínuo (1–8 s: 1,040 · 1,032 · 1,019 · 1,019 · 1,020 · 1,020 · 1,022) | t1: 1,024 · 1,015 · 1,016 · 1,001 · 1,015 · 1,013. Antes parava aos 3,5 s; corrigido (deriva desde o quadro 0, começa mais aberta) | C |
| Afastamento do fecho | Suavizado: 0,979 → 0,922 → 0,978 | t5: 0,962 → 0,931 → 0,959 (antes 0,954 constante) | C |
| Mapa → técnico | Recuo 0,94/s, depois câmera parada | t4: aproximação e depois o clipe da eclusa (câmera própria, fixa) | P |
| Transições | Voo curto entre escalas | Transição calculada pelo motor: 0,8 s + 0,22 s por nível de zoom (máx. 1,8 s); o episódio não escolhe mais | P: easing não verificável no MP4 |

## Proporções, tipografia, legendas e cartões

| Item | Referência | Coringa | Situação |
|---|---|---|---|
| Proporções e posições | Pergunta no topo, território no centro, cartão central | Mesmas faixas, resolvidas pela área segura de TikTok, Reels e Shorts | C |
| Legenda | Frase, 1–3 palavras, cerca de 52–56 px, branca com sombra, grupo inteiro de uma vez, y ≈ 1457–1534 | Frase (caixa normal), 1–3 palavras, 56 px, branca, sem karaokê, faixa y 1232–1382 | P: fica cerca de 95 px mais alta para não ficar sob a interface do TikTok. A caixa de frase é heurística (o TTS só entrega maiúsculas); pode errar maiúsculas raras |
| Títulos | Título grande no topo | Corpo por token do slot (pergunta 84/104, manchete 76) | C |
| Entrada de cartão | ≈ 0,53 s (cartão de 12 s) | ≈ 0,37 s (token de entrada 0,45 com easing) | P: proposta de token 0,55 |
| Cartões | Papel claro, número grande, sem fundo vermelho | Sistema único em papel, centralizado, sem inclinação, fonte factual no rodapé | C |

## Ritmo e demonstração técnica

| Item | Referência | Coringa | Situação |
|---|---|---|---|
| Ritmo das revelações | 1–2 s entre informações | Portão ≤ 3 s sem câmera; Panamá 1,28 eventos/s | P: o portão está acima do ritmo da referência |
| Demonstração técnica | Diagrama escuro sobre o território | Diagrama só em beat com `funcao` mecanismo/estrutura (F-TECNICO-SEM-MECANISMO); planta da eclusa no tema do canal | C |

## Acabamento sonoro

| Item | Referência | Coringa | Situação |
|---|---|---|---|
| Loudness | −14,1 LUFS · LRA 1,9 · pico verdadeiro −2,5 dBTP medido no MP4 exportado (você informou −2,01) | Master do canal (voz comprimida, ganho linear, limitador de pico verdadeiro) no Panamá, depois do AAC: −14,2 LUFS · LRA 2,5 · −1,9/−2,1 dBTP | C |
| Distribuição do nível | p10 −28,5 dB · p90 −14,5 dB (14,0 dB entre eles) | p10 −23,6 · p90 −12,2 (11,3 dB) | P: a diferença vem da dinâmica da voz, não da trilha (baixar a trilha de −24 para −28 dB não mudou o p10). Os volumes individuais da referência não se recuperam da mixagem |
| Efeitos | Discretos | Ancorados em acontecimentos (troca de escala, cartão, rota, mecanismo), de −22 a −26 dB, espaçados ≥ 0,9 s | P: avaliação de ouvido é sua |

## O que mudou na arquitetura (a causa dos mapas chapados)

- Não há mais mapa geográfico sem base licenciada que cubra a tela inteira. O teto de zoom é a definição da base.
- O diagrama técnico só aparece em beat de mecanismo/estrutura.
- O arquivo do episódio não pode trazer identidade: tamanho, raio, largura, ajuste de cor, transição e zoom_max são proibidos (F-ESTILO-NO-EPISODIO). Tudo isso vem de tokens e presets do canal.
- O diretor recebe essas regras no prompt e o validador as recusa.
