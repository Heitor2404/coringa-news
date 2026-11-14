# Coringa Explica — V2.2 (correções finais da V2.1)

Ramo `visual-v2-2-correcao-final`, criado a partir de `visual-v2-1-refinamento` (b88fbb2). Sem merge. NTC intocado.
Nenhuma chamada paga: o roteiro do assunto inédito é FIXTURE (etapa paga do roteirista) e a voz é humana, livre (CC0).

> Teste automático não é aprovação visual. Tudo abaixo é medição; a aprovação estética é do Heitor.

## P0-1 — Centralização geométrica

Causa: a legenda e os textos "centralizados" usavam margens assimétricas (72/150, 90/150, 60/140), o que deslocava
o centro para 500–510 px. Correção: eixo simétrico `--eixo-esq/--eixo-dir = 150 px` (centro x = 540), classe `.eixo`
com `transform-origin: 50% 50%` (a animação de escala não desloca o centro), intenção declarada no próprio elemento
(`data-centro="1"` = centralizado; `data-alinhamento="local"` = rótulo preso a um objeto, assimetria intencional).

| Composição | Elemento | Centro antes (px) | Centro depois (px) | Desvio medido depois |
|---|---|---|---|---|
| todas | legenda (1 e 2 linhas, destaque, animada) | 510 | 540 | 0 px (DOM e pixels) |
| titulo.capitulo | título / subtítulo | 510 / 510 | 540 / 540 | 0 / 0 |
| revelacao.surpresa | pergunta / resposta / detalhe | 501 / 500 / 510 | 540 / 540 / 540 | 0 / 0 / 0 |
| forcas.vetores | resultado | 501 | 540 | 0 |
| evento.impacto | contador | 540 | 540 | 0 |

Assimetria intencional (documentada com `data-alinhamento="local"`): rótulos de comparacao.grandezas (sob cada
barra), intervalos da linha do tempo, anotação do gráfico, rótulo da órbita, rótulos de mapa, lower thirds, créditos.

Galeria antes/depois com o acervo real dos dois lados: `saida/v22/ev_pares/` (18 pares). Depois: 23 textos
declarados, desvio máximo 0 px.

Testes (`tests/test_v22_centro.py`, 5): extremos por linha no DOM; pixels a 1080×1920 e na prévia 540×960 (quadro
extraído por ffmpeg); título + subtítulo + legenda; todas as 33 composições com o texto declarado ou com intenção;
escala animada da revelação. Confirmado que falham com o CSS antigo. Evidência: `saida/v22/centro_pares/*.jpg`
(antes/depois nos mesmos instantes, grade em x = 540, centros desenhados).

## P0-2 — CI vermelho

Duas causas reais, ambas de quebra de linha que "cabia por poucos pixels" e quebrava diferente no Chromium do CI:
fontes do encerramento (folga de ~16 px) e legenda do mapa. Correção: quebra determinística (unidades inteiras e
folga de 40 px nas fontes; legenda equilibrada com larguras medidas, folga de 24 px e `<br>` explícito). As referências
regeneradas (titulo.capitulo, revelacao.surpresa, encerramento.editorial, mapa.territorio, foto.historica) mudaram
por causa visual intencional (centralização, quebra, foto original de 1913), com justificativa no commit. A tolerância
da regressão não foi alterada. A regressão agora imprime o quadro produzido em base64 quando falha.

## P0-3 — Contrato de acontecimentos

`src/v2/contrato.py`: id, tipo, sujeito, objeto, ação, estado inicial/final, o que mostrar, dados, capacidade, fonte,
importância, obrigatória e sincronia (palavra da narração que dispara um elemento). O bloco do contrato é anexado ao
pedido real do roteirista (`roteiro.escrever_explica`) sem tocar no texto do cofre; o formato antigo continua válido.
O seletor consulta o contrato ANTES dos padrões de texto; números do contrato passam por `fatos.validar`; a montagem
desenha a composição declarada com os dados declarados e registra substituição, dados faltantes e `origem`.

## P0-4 — Fiscal semântico

S5 compara declarado × selecionado × capacidade × dados × renderizado e bloqueia substituição genérica de acontecimento
crítico. S6 manda para revisão humana a cena sem contrato que os padrões não reconheceram. `aprovacao_automatica` é
separada de `aprovado_tecnicamente`.

Avaliação de ponta a ponta (`python -m src.v2.avaliacao_contrato`), paráfrases em 8 categorias:

| Critério | Resultado |
|---|---|
| C1 contrato com dados → composição capaz | 16/16 |
| C2 contrato crítico sem dados → bloqueio (S1+S5) | 16/16 |
| C3 tipo desconhecido crítico → bloqueio | 2/2 |
| C4 formato antigo → nunca aprovação automática silenciosa | 16/16 (12 revisão S6, 3 bloqueio, 1 composição capaz) |
| C5 reserva só por padrões | 10/16 (≥ 10) |

Seletor só por padrões (`python -m src.v2.avaliacao_selecao`): positivos 24/24, negativos 8/8, reserva 10/16.
Erros da reserva, todos: r1 (Roma 753 a.C.–476), r5 (sangue leva oxigênio), r6 (baleia-azul = 3 ônibus),
r7 (ferro enferruja), r13 (fibra óptica), r16 (furacão do Atlântico à Flórida) → caem em foto e, sem contrato,
o S6 impede aprovação automática. Com contrato, C1 cobre essas categorias.

Demonstração (C3/C4): acontecimento crítico não reconhecido → `aprovacao_automatica = False`.

## P1-5 — Foto de 1913

Trocada pelo original autêntico da Library of Congress (LCCN 2007663276, via Commons, domínio público): mesma
fotografia da auditoria, 2239×697 px, ~6,6× mais altura útil. `acervo_v2.adequacao_historica` decide pela resolução e
proporção reais: inteira / varredura / insuficiente (ampliação ≤ 1,5×, protagonista ≥ 300 px). D12 bloqueia foto de
arquivo que vira faixa fina — agora também a foto de FUNDO (foto.documental), achado no render inédito: a panorâmica
de Caracas (2400×463) aparecia como faixa de 185 px e passava; agora ganha janela alta com varredura.
Testes com fotos reais: panorâmica (2), horizontal, vertical, quadrada, documento, baixa resolução (bloqueia).

## P1-6 — video.documental com filmagem real

U.S. Navy e NASA (domínio público) e time-lapse CC BY 3.0: deitado, vertical, corte temporal, transição, legenda e
banner. Quadro do palco conferido contra o quadro extraído do original no mesmo instante. Áudio original: removido
(padrão) ou mixado (`audio_original > 0`, alinhado ao trecho, fades, abaixa sob a narração) — medido em render.

## P1-7 — Rótulos de mar

Candidatos amostrados na tela do enquadramento final e dentro do polígono do mar; caixa inteira testada contra terra
em todo quadro (câmera andando). Achado no render inédito: "Canal de Iucatã" sobre a costa venezuelana — peças com o
anel invertido no Natural Earth (Canal do Iucatão, Estreito de Gibraltar) eram o globo inteiro para o d3 esférico.
Corrigido peça a peça. Teste em 7 regiões: sobre água (verificação Python independente) E no mar que o rótulo nomeia
(`geo.mares_em`, teste plano). O código antigo falha em Golfo do Panamá, Golfo Pérsico, Itália, Veracruz e Venezuela.

## P1-8 — Mídia real no CI

`tests/midia/` (licença por arquivo, ao lado):

| Arquivo | Licença | Autor | Origem |
|---|---|---|---|
| foto_panoramica_1913 | Domínio público | Library of Congress | Commons (LCCN 2007663276) |
| foto_panoramica_caracas | CC BY-SA 3.0 | Paolo Costa Baldi | Commons |
| foto_horizontal_roraima | CC BY-SA 4.0 | Ney Teixeira de Freitas Guimarães Filho | Commons |
| foto_vertical / quadrada_salto_angel | CC BY-SA 4.0 | Berrucomons | Commons |
| documento_mapa_1635 | Domínio público | Willem Blaeu | Commons |
| video_horizontal_navio | Domínio público | U.S. Navy | Commons |
| video_horizontal_timelapse | CC BY 3.0 | Morrison Mast | Commons |
| video_vertical_nasa | Domínio público | NASA SVS | Commons |
| voz_venezuela | CC0 | Wilfredor | Commons |

Baixadas pelo workflow `midia-teste-v22` (o Actions tem internet; esta máquina não). Testes separados para mídia
presente, ausente (SEM ACERVO), baixa resolução e vídeo real.

## P1-9 — Assunto inédito (Venezuela) pelo fluxo real

`python -m src.v2.inedito`: interpretação (contrato) → seleção → validação → acervo local → montagem → sincronia
(alinhamento palavra a palavra da voz humana) → render 1080×1920 → fiscal → exportação. Só o roteiro é fixture.
Composições escolhidas pelo contrato: mapa.territorio, mapa.localizacao, foto.documental (Caracas), numero.animado,
mapa.territorio com vizinhos que acendem quando a voz diz Colômbia, Brasil, Guiana; encerramento.

O primeiro render revelou 4 defeitos que nenhum teste pegava (corrigidos, cada um com teste novo):
rótulo de mar no mar errado; panorâmica como faixa; mascote encostando no resumo; blocos de legenda sobrepostos.
E um de desempenho: a preparação do mapa levava 95 s e estourava o limite de 60 s → 20 s com pré-filtro exato.

## P1-10 / P1-11 — Áudio e render 1080×1920

Render do assunto inédito (`saida/v22/inedito/venezuela_1080x1920.mp4`, fora do repositório), máquina de 2 CPUs:

| Medida | Valor |
|---|---|
| Formato | 1080×1920, 30 fps, H.264 + AAC, 53,0 s |
| Tamanho | 10,3 MB |
| Loudness integrado / pico | −14,3 LUFS / −2,3 dBTP (alvo −14 LUFS) |
| Tempo total | 1 539 s (25,7 min), dos quais 278 s de medição geométrica; render ≈ 29× o tempo real |
| Memória (maior processo filho) | 505 MB |
| Preparação da página (READY) | 95,7 s → 20,1 s após o pré-filtro do mapa |
| Alinhamento | ≥ 80% das palavras do texto casadas com o reconhecimento (faster-whisper small) |
| Fiscal | sem bloqueio; avisos D11 (planos de 10,6–17 s, narração natural lenta) e D4 (legenda sobre o mapa na cena 4) |

Narração: voz humana real recortada em trechos contíguos (nunca repete áudio), legendas em blocos de até 4 palavras
nos instantes da voz, vizinhos do mapa acendem na palavra, música sintetizada local mixada sob a voz.

## P1-12 — Eclusa

Com `degraus > 1`, o quadro avisa "ESQUEMA: 1 CÂMARA PARA OS 26 m / NO CANAL: N CÂMARAS EM SEQUÊNCIA" e mostra a
escada em que o navio sobe os degraus. 82 km, US$ 5,3 mi (lance excepcional de leilão) e água como média aproximada
mantidos.

## P2-13 — Variedade documental

Sem cotas: a variedade vem do contrato (o roteirista declara o que mostrar) — no assunto inédito, 5 composições
distintas em 6 cenas, nenhuma imagem repetida, destaque de vizinhos amarrado às palavras.

## Pendências

| Item | Estado |
|---|---|
| Clipe real a 60 fps | parcial — o download por intervalo falhou duas vezes (arquivo de 261 bytes); vídeos testados são 24–30 fps |
| Legenda queimada em vídeo de arquivo (o da NASA tem legenda em inglês) | achado registrado; não há detector |
| Etapa do roteirista | fixture (é chamada paga) |
| Voz de produção | a voz real usada é humana e livre; a voz de produção do canal não foi testada (exigiria chamada paga) |
| Planos longos (D11) no inédito | aviso: a narração natural lê devagar (número ~10 s); decisão editorial |
| Aprovação visual e estética | precisa do Heitor |
